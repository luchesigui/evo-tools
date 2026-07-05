#!/usr/bin/env python3
"""
Módulo SQLite para registro de estatísticas de disparos.

Schema:
    disparos(
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp       TEXT NOT NULL,
        tipo            TEXT NOT NULL,          -- 'cobranca' ou 'renovacao'
        janela_dias     INTEGER NOT NULL,       -- 1, 3 ou 7
        nome_aluno      TEXT,
        telefone        TEXT,
        evo_id          TEXT,
        kommo_contact_id TEXT,
        sales_bot_id    TEXT,
        status          TEXT NOT NULL,          -- 'sucesso', 'erro', 'sem_telefone', 'dry_run'
        detalhes_erro   TEXT
    )
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any, List


DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "disparos.db")


def init_db(path: Optional[str] = None) -> None:
    """
    Inicializa o banco de dados e cria a tabela se não existir.

    Args:
        path: Caminho para o arquivo .db. Se None, usa DEFAULT_DB_PATH.
    """
    db_path = path or DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS disparos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tipo TEXT NOT NULL,
            janela_dias INTEGER NOT NULL,
            nome_aluno TEXT,
            telefone TEXT,
            evo_id TEXT,
            kommo_contact_id TEXT,
            sales_bot_id TEXT,
            status TEXT NOT NULL,
            detalhes_erro TEXT
        )
    """)
    conn.commit()
    conn.close()


def registrar_disparo(
    path: Optional[str] = None,
    **kwargs,
) -> int:
    """
    Registra um disparo no banco.

    kwargs esperados:
        tipo: str                -- 'cobranca' ou 'renovacao'
        janela_dias: int         -- 1, 3 ou 7
        nome_aluno: str
        telefone: str
        evo_id: str
        kommo_contact_id: Optional[str]
        sales_bot_id: Optional[str]
        status: str              -- 'sucesso', 'erro', 'sem_telefone', 'dry_run'
        detalhes_erro: Optional[str]

    Retorna o id do registro inserido.
    """
    db_path = path or DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        """
        INSERT INTO disparos
            (timestamp, tipo, janela_dias, nome_aluno, telefone, evo_id,
             kommo_contact_id, sales_bot_id, status, detalhes_erro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().isoformat(),
            kwargs.get("tipo", ""),
            kwargs.get("janela_dias", 0),
            kwargs.get("nome_aluno", ""),
            kwargs.get("telefone", ""),
            kwargs.get("evo_id", ""),
            kwargs.get("kommo_contact_id"),
            kwargs.get("sales_bot_id"),
            kwargs.get("status", ""),
            kwargs.get("detalhes_erro"),
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_estatisticas(
    path: Optional[str] = None,
    tipo: Optional[str] = None,
    janela_dias: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Retorna estatísticas dos disparos agrupadas por tipo, janela_dias e status.
    Filtra por tipo e/ou janela_dias se fornecidos.

    Args:
        path: Caminho para o arquivo .db. Se None, usa DEFAULT_DB_PATH.
        tipo: Filtro opcional por tipo ('cobranca' ou 'renovacao').
        janela_dias: Filtro opcional por janela (1, 3 ou 7).

    Returns:
        Lista de dicts com chaves: tipo, janela_dias, status, total, ultimo_disparo
    """
    db_path = path or DEFAULT_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conditions = []
    params: List[Any] = []
    if tipo:
        conditions.append("tipo = ?")
        params.append(tipo)
    if janela_dias is not None:
        conditions.append("janela_dias = ?")
        params.append(janela_dias)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = conn.execute(
        f"""
        SELECT
            tipo,
            janela_dias,
            status,
            COUNT(*) as total,
            MAX(timestamp) as ultimo_disparo
        FROM disparos
        {where}
        GROUP BY tipo, janela_dias, status
        ORDER BY tipo, janela_dias, status
        """,
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
