#!/usr/bin/env python3
"""
Renovação automática via WhatsApp/Kommo para alunos com contratos próximos do vencimento.

Fluxo:
1. Busca todos os membros ativos na API EVO
2. Filtra membros com contrato encerrando exatamente em N dias
3. Para cada membro:
   a. Busca contato no Kommo pelo telefone
   b. Se encontrar: valida/adiciona campo "Evo ID"
   c. Se não encontrar: cria novo contato com Evo ID
   d. Dispara sales bot correspondente
4. Registra resultado no SQLite

Uso:
    python renovacao.py --janela 7    # contratos que vencem em 7 dias
    python renovacao.py --janela 3    # contratos que vencem em 3 dias
    python renovacao.py --janela 1    # contratos que vencem amanhã
    python renovacao.py --janela 7 --dry-run --verbose
"""

import os
import sys
import logging
import argparse

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evo-renovacoes-pendencias"))
from evo_renovacoes import get_members_sample, analyze_renovations  # noqa: E402

from broadcast import KommoAPI, KommoChatsAPI  # noqa: E402
from kommo_contacts import find_or_create_contact, find_evo_id_field, trigger_sales_bot, sanitize_phone  # noqa: E402
from db import init_db, registrar_disparo, get_estatisticas  # noqa: E402

VALID_JANELAS = {1, 3, 7}

SALES_BOT_MAP = {
    7: "SALES_BOT_RENOVACAO_7DIAS",
    3: "SALES_BOT_RENOVACAO_3DIAS",
    1: "SALES_BOT_RENOVACAO_1DIA",
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
        description="Renovação automática via Kommo para alunos com contrato próximo do vencimento"
    )
    parser.add_argument(
        "--janela",
        type=int,
        required=True,
        choices=list(VALID_JANELAS),
        help="Dias até o vencimento do contrato (1, 3 ou 7)",
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
        rows = get_estatisticas(tipo="renovacao")
        if not rows:
            logger.info("Nenhum disparo de renovação registrado.")
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

    # 2. Filtra contratos vencendo exatamente em N dias
    logger.info(f"\n[2/4] Filtrando contratos com vencimento em exatamente {args.janela} dia(s)...")
    renovacoes = analyze_renovations(members, days_before=args.janela, exact=True)
    logger.info(f"  {len(renovacoes)} aluno(s) com contrato vencendo em {args.janela} dia(s).")

    if not renovacoes:
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
        logger.warning("Campo 'Evo ID' não encontrado no Kommo. Contatos serão criados sem ele.")

    chats_api = KommoChatsAPI(
        channel_id=env["KOMMO_CHANNEL_ID"],
        channel_secret=env["KOMMO_CHANNEL_SECRET"],
        scope_id=env["KOMMO_SCOPE_ID"],
        account_id=str(kommo_api.account_id or ""),
        dry_run=args.dry_run,
    )

    # 4. Processa cada aluno
    logger.info(f"\n[4/4] Processando {len(renovacoes)} aluno(s)...")
    sucesso = erros = sem_telefone = 0

    for aluno in renovacoes:
        nome = aluno["nome"]
        telefone = aluno.get("telefone", "")
        evo_id = str(aluno["id_member"])

        logger.info(
            f"  → {nome} | vence={aluno['fim_contrato']} | "
            f"dias={aluno['dias_ate_vencimento']} | "
            f"plano={aluno['plano'][:30]} | tel={telefone or '-'}"
        )

        if not telefone:
            logger.warning(f"    Sem telefone para {nome}. Pulando.")
            sem_telefone += 1
            registrar_disparo(
                tipo="renovacao",
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
                tipo="renovacao",
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
            tipo="renovacao",
            janela_dias=args.janela,
            nome_aluno=nome,
            telefone=telefone,
            evo_id=evo_id,
            kommo_contact_id=kommo_id,
            sales_bot_id=sales_bot_id,
            status="dry_run" if args.dry_run else status,
        )

    logger.info("\n" + "=" * 60)
    logger.info(f"RENOVAÇÃO {args.janela}D — RESUMO")
    logger.info("=" * 60)
    logger.info(f"  Total processado:  {len(renovacoes)}")
    logger.info(f"  Sucesso:           {sucesso}")
    logger.info(f"  Sem telefone:      {sem_telefone}")
    logger.info(f"  Erros:             {erros}")
    if args.dry_run:
        logger.info("  (Modo dry run — nenhuma ação foi realizada no Kommo)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
