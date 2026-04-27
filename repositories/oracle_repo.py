"""
Conexão com Oracle via python-oracledb (modo thin).
DSN e credenciais lidos de variáveis de ambiente — nunca hardcoded.
"""
import logging
import os
from typing import Generator

import oracledb

from models.report_row import OracleRow

logger = logging.getLogger(__name__)

SQL_RELATORIO = """
    SELECT
        TRUNC(data_recurtimento) AS data_recurtimento,
        artigo,
        cor,
        lote_fabricacao,
        codigo_artigo,
        m2,
        peso_lote
    FROM USU_VBI_OPREC_V2
    WHERE data_recurtimento BETWEEN :data_inicio AND :data_fim
      AND (:lote      IS NULL OR lote_fabricacao = :lote)
      AND (:artigo    IS NULL OR artigo = :artigo)
      AND (:cor       IS NULL OR cor = :cor)
    ORDER BY data_recurtimento, artigo, lote_fabricacao
"""

SQL_ARTIGOS = """
    SELECT codigo_artigo, descricao_artigo
    FROM USU_VBI_ARTIGOS_SEMI_NOA
    ORDER BY descricao_artigo
"""


def get_oracle_connection() -> oracledb.Connection:
    dsn = os.environ["ORACLE_DSN"]          # ex: host:port/service_name
    user = os.environ["ORACLE_USER"]
    password = os.environ["ORACLE_PASSWORD"]
    return oracledb.connect(user=user, password=password, dsn=dsn)


def fetch_relatorio(
    data_inicio: str,
    data_fim: str,
    lote: str | None = None,
    artigo: str | None = None,
    cor: str | None = None,
    timeout_seconds: int = 30,
) -> list[OracleRow]:
    """
    Busca linhas da view de relatório com os filtros informados.
    Levanta OracleError se a conexão falhar — o caller trata e exibe mensagem ao usuário.
    """
    conn = get_oracle_connection()
    conn.callTimeout = timeout_seconds * 1000

    cursor = conn.cursor()
    cursor.execute(
        SQL_RELATORIO,
        {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "lote": lote,
            "artigo": artigo,
            "cor": cor,
        },
    )

    rows = []
    for record in cursor:
        data_rec = record[0]
        rows.append(
            OracleRow(
                data_recurtimento=data_rec.strftime("%Y-%m-%d") if data_rec else None,
                artigo=record[1],
                cor=record[2],
                lote_fabricacao=record[3],
                codigo_artigo=record[4],
                m2=_to_float(record[5]),
                peso_lote=_to_float(record[6]),
            )
        )

    cursor.close()
    conn.close()
    logger.info("Oracle: %d linhas retornadas (%s → %s).", len(rows), data_inicio, data_fim)
    return rows


def fetch_artigos() -> list[dict]:
    """Retorna lista de artigos para o formulário de cadastro de fatores."""
    conn = get_oracle_connection()
    cursor = conn.cursor()
    cursor.execute(SQL_ARTIGOS)
    result = [
        {"codigo_artigo": row[0], "descricao_artigo": row[1]}
        for row in cursor
    ]
    cursor.close()
    conn.close()
    return result


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
