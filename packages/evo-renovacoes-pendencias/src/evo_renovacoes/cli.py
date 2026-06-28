#!/usr/bin/env python3
"""
CLI Entry Point para evo-renovacoes-pendencias.

Uso:
    python -m evo_renovacoes --dias 7
    python -m evo_renovacoes --dias 3 --json
    python -m evo_renovacoes --pendencias --dias 1
"""

import sys
import argparse
from datetime import datetime
from typing import Optional, List

from evo_renovacoes.core import (
    get_members_sample,
    analyze_renovations,
    analyze_pending_fees,
    check_pending_fees,
    print_report,
    print_pendencias_report,
    export_json,
    export_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evo-renovacoes",
        description="Panobianco - Relatorio de renovacoes e pendencias (API EVO)",
    )
    parser.add_argument(
        "--dias",
        type=int,
        default=5,
        choices=[1, 3, 7],
        help="Dias ate vencimento para filtro de renovacoes (1, 3 ou 7). Padrao: 5",
    )
    parser.add_argument(
        "--exato",
        action="store_true",
        help="Filtrar exatamente pelos dias especificados (nao janela)",
    )
    parser.add_argument(
        "--membros",
        type=int,
        default=None,
        help="Limite de membros a analisar (padrao: todos)",
    )
    parser.add_argument(
        "--sem-pendencia",
        action="store_true",
        help="Nao consulta pendencias (mais rapido)",
    )
    parser.add_argument(
        "--pendencias",
        action="store_true",
        help="Mostra todos os membros com pendencias financeiras",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exportar resultado em JSON",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Exportar resultado em CSV",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    print(
        f"\n[1/3] Buscando membros na API EVO (limite: {args.membros or 'todos'})..."
    )
    members, total = get_members_sample(limit=args.membros)

    if args.pendencias:
        print(f"\n[2/3] Analisando pendencias financeiras de todos os membros ativos...")
        data = analyze_pending_fees(members, target_dias_atraso=args.dias if args.exato else None)
        print(f"\n  Total com pendencias: {len(data)}")
        print_pendencias_report(data)

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        if args.json:
            export_json(data, f"evo_pendencias_{ts}.json")
        if args.csv:
            export_csv(data, f"evo_pendencias_{ts}.csv")
        if not args.json and not args.csv:
            export_json(data, f"evo_pendencias_{ts}.json")
        return 0

    print(f"\n[2/3] Analisando contratos com renovacao em {args.dias} dias{'  (exato)' if args.exato else ''}...")
    renewals = analyze_renovations(members, days_before=args.dias, exact=args.exato)
    print(f"  Alunos ativos com renovacao no periodo: {len(renewals)}")

    if not args.sem_pendencia and renewals:
        print(f"\n[3/3] Cruzando com pendencias financeiras...")
        renewals = check_pending_fees(renewals)
    else:
        for r in renewals:
            r.setdefault("tem_pendencia", None)
            r.setdefault("qtd_pendencias", 0)
            r.setdefault("valor_total_pendente", 0)

    print_report(renewals, args.dias)

    # Exportar se solicitado
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    if args.json:
        export_json(renewals, f"evo_renovacoes_{ts}.json")
    if args.csv:
        export_csv(renewals, f"evo_renovacoes_{ts}.csv")

    # Sempre salva JSON como registro
    if not args.json and not args.csv:
        export_json(renewals, f"evo_renovacoes_{ts}.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
