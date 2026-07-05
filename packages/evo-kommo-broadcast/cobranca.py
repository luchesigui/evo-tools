#!/usr/bin/env python3
"""
Cobrança automática via WhatsApp/Kommo para alunos com pendências financeiras.

Fluxo:
1. Busca todos os membros ativos na API EVO
2. Verifica pendências financeiras de cada membro
3. Filtra membros cuja pendência mais antiga tem exatamente N dias de atraso
4. Para cada membro:
   a. Busca contato no Kommo pelo telefone
   b. Se encontrar: valida/adiciona campo "Evo ID"
   c. Se não encontrar: cria novo contato com Evo ID
   d. Dispara sales bot correspondente
5. Registra resultado no SQLite

Uso:
    python cobranca.py --janela 1
    python cobranca.py --janela 3
    python cobranca.py --janela 7
    python cobranca.py --janela 1 --dry-run --verbose
"""

import os
import sys
import logging
import argparse

from dotenv import load_dotenv

# Carrega .env deste pacote antes de importar módulos que lêem os vars
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Importa da EVO API (pacote irmão)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evo-renovacoes-pendencias"))
from evo_renovacoes import get_members_sample, analyze_pending_fees  # noqa: E402

from broadcast import KommoAPI, KommoChatsAPI  # noqa: E402
from kommo_contacts import find_or_create_contact, find_evo_id_field, trigger_sales_bot  # noqa: E402
from db import init_db, registrar_disparo, get_estatisticas  # noqa: E402

VALID_JANELAS = {1, 3, 7}

SALES_BOT_MAP = {
    1: "SALES_BOT_COBRANCA_1DIA",
    3: "SALES_BOT_COBRANCA_3DIAS",
    7: "SALES_BOT_COBRANCA_7DIAS",
}


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cobrança automática via Kommo para alunos com pendências financeiras"
    )
    parser.add_argument(
        "--janela",
        type=int,
        required=True,
        choices=list(VALID_JANELAS),
        help="Dias de atraso da pendência mais antiga (1, 3 ou 7)",
    )
    parser.add_argument("--membros", type=int, default=None, help="Limite de membros (padrão: todos)")
    parser.add_argument("--dry-run", action="store_true", help="Simular sem realizar ações no Kommo")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logs detalhados")
    parser.add_argument("--stats", action="store_true", help="Exibe estatísticas do banco e encerra")
    return parser.parse_args()


def validate_env() -> dict:
    required = [
        "KOMMO_DOMAIN", "KOMMO_CLIENT_ID", "KOMMO_CLIENT_SECRET",
        "KOMMO_ACCESS_TOKEN", "KOMMO_REFRESH_TOKEN",
        "KOMMO_CHANNEL_ID", "KOMMO_CHANNEL_SECRET", "KOMMO_SCOPE_ID",
    ]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        print(f"ERRO: Variáveis de ambiente ausentes: {', '.join(missing)}")
        print("Copie .env.example para .env e preencha as credenciais.")
        sys.exit(1)
    return {v: os.getenv(v) for v in required}


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    init_db()

    if args.stats:
        rows = get_estatisticas(tipo="cobranca")
        if not rows:
            logger.info("Nenhum disparo de cobrança registrado.")
        for r in rows:
            logger.info(f"janela={r['janela_dias']}d | status={r['status']} | total={r['total']} | ultimo={r['ultimo_disparo']}")
        return

    env = validate_env()
    sales_bot_id = os.getenv(SALES_BOT_MAP[args.janela], "")

    if not sales_bot_id:
        logger.warning(f"Variável {SALES_BOT_MAP[args.janela]} não configurada. O bot não será disparado.")

    if args.dry_run:
        logger.info("=== MODO DRY RUN ATIVADO — nenhuma ação será realizada no Kommo ===")

    # 1. Busca membros EVO
    logger.info(f"[1/4] Buscando membros na API EVO (limite: {args.membros or 'todos'})...")
    members, _ = get_members_sample(limit=args.membros)

    # 2. Analisa pendências com exatamente N dias de atraso
    logger.info(f"\n[2/4] Identificando pendências com exatamente {args.janela} dia(s) de atraso...")
    devedores = analyze_pending_fees(members, target_dias_atraso=args.janela)
    logger.info(f"  {len(devedores)} aluno(s) com pendência de {args.janela} dia(s) encontrado(s).")

    if not devedores:
        logger.info("Nenhum aluno para processar. Encerrando.")
        return

    # 3. Inicializa Kommo API
    logger.info("\n[3/4] Inicializando Kommo API...")
    kommo_api = KommoAPI(
        domain=env["KOMMO_DOMAIN"],
        client_id=env["KOMMO_CLIENT_ID"],
        client_secret=env["KOMMO_CLIENT_SECRET"],
        access_token=env["KOMMO_ACCESS_TOKEN"],
        refresh_token=env["KOMMO_REFRESH_TOKEN"],
        dry_run=args.dry_run,
    )
    kommo_api.initialize()

    evo_field_id = find_evo_id_field(kommo_api)
    if not evo_field_id:
        logger.warning("Campo 'Evo ID' não encontrado no Kommo. Contatos serão criados/atualizados sem ele.")

    chats_api = KommoChatsAPI(
        channel_id=env["KOMMO_CHANNEL_ID"],
        channel_secret=env["KOMMO_CHANNEL_SECRET"],
        scope_id=env["KOMMO_SCOPE_ID"],
        account_id=str(kommo_api.account_id or ""),
        dry_run=args.dry_run,
    )

    # 4. Processa cada aluno
    logger.info(f"\n[4/4] Processando {len(devedores)} aluno(s)...")
    sucesso = erros = sem_telefone = 0

    for aluno in devedores:
        nome = aluno["nome"]
        telefone = aluno.get("telefone", "")
        evo_id = str(aluno["id_member"])

        logger.info(
            f"  → {nome} | atraso={aluno['dias_atraso']}d | "
            f"pendências={aluno['qtd_pendencias']} | "
            f"R$ {aluno['valor_total_pendente']:.2f} | tel={telefone or '-'}"
        )

        if not telefone:
            logger.warning(f"    Sem telefone para {nome}. Pulando.")
            sem_telefone += 1
            registrar_disparo(
                tipo="cobranca",
                janela_dias=args.janela,
                nome_aluno=nome,
                telefone="",
                evo_id=evo_id,
                kommo_contact_id=None,
                sales_bot_id=sales_bot_id,
                status="sem_telefone",
            )
            continue

        # Busca/cria contato no Kommo
        kommo_id, acao = find_or_create_contact(kommo_api, nome, telefone, evo_id, evo_field_id)

        if not kommo_id:
            erros += 1
            registrar_disparo(
                tipo="cobranca",
                janela_dias=args.janela,
                nome_aluno=nome,
                telefone=telefone,
                evo_id=evo_id,
                kommo_contact_id=None,
                sales_bot_id=sales_bot_id,
                status="erro",
                detalhes_erro=f"acao={acao}",
            )
            continue

        # Dispara sales bot
        from kommo_contacts import sanitize_phone
        phone_sanitized = sanitize_phone(telefone)
        bot_ok = trigger_sales_bot(chats_api, phone_sanitized, nome, sales_bot_id, dry_run=args.dry_run)

        status = "sucesso" if bot_ok else "erro"
        if bot_ok:
            sucesso += 1
            logger.info(f"    OK | kommo_id={kommo_id} | acao={acao} | bot={sales_bot_id}")
        else:
            erros += 1
            logger.warning(f"    Contato {acao} mas falha ao disparar bot")

        registrar_disparo(
            tipo="cobranca",
            janela_dias=args.janela,
            nome_aluno=nome,
            telefone=telefone,
            evo_id=evo_id,
            kommo_contact_id=kommo_id,
            sales_bot_id=sales_bot_id,
            status="dry_run" if args.dry_run else status,
        )

    logger.info("\n" + "=" * 60)
    logger.info(f"COBRANÇA {args.janela}D — RESUMO")
    logger.info("=" * 60)
    logger.info(f"  Total processado:  {len(devedores)}")
    logger.info(f"  Sucesso:           {sucesso}")
    logger.info(f"  Sem telefone:      {sem_telefone}")
    logger.info(f"  Erros:             {erros}")
    if args.dry_run:
        logger.info("  (Modo dry run — nenhuma ação foi realizada no Kommo)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
