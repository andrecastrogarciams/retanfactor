"""
Serviço de relatório operacional de recurtimento.

Responsabilidades:
- Orquestrar busca Oracle + aplicação de fatores SQLite
- Calcular colunas derivadas (kg/m², kg/ft², peso calculado, % diferença)
- Classificar cor da % diferença
- Gerenciar cache com TTL e invalidação funcional
"""
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from models.report_row import CorDiferenca, OracleRow, ReportRow
from repositories.sqlite_repo import get_fator_vigente

logger = logging.getLogger(__name__)

# Constante de conversão m² → ft²
_M2_TO_FT2: float = 10.764

# TTL do cache em segundos (5 minutos — PRD Story 3.2 AC1)
_CACHE_TTL_SECONDS: int = 300


# ---------------------------------------------------------------------------
# Cálculos — funções puras, sem dependências externas
# ---------------------------------------------------------------------------

def calcular_kg_m2(peso_lote: float, m2: float) -> Optional[float]:
    """kg/m² = peso_lote / m²  (PRD Story 1.3 AC3)"""
    if not m2:
        return None
    return round(peso_lote / m2, 2)


def calcular_kg_ft2(peso_lote: float, m2: float) -> Optional[float]:
    """kg/ft² = peso_lote / (m² × 10.764)  (PRD Story 1.3 AC4)"""
    if not m2:
        return None
    return round(peso_lote / (m2 * _M2_TO_FT2), 2)


def calcular_peso_calculado(m2: float, fator: float) -> Optional[float]:
    """peso_calculado = m² × 10.764 × fator × 0.092903  (PRD Story 1.3 AC2)"""
    if not m2 or not fator:
        return None
    return round(m2 * _M2_TO_FT2 * fator * 0.092903, 2)


def calcular_pct_diferenca(peso_lote: float, peso_calculado: float) -> Optional[float]:
    """% diferença = (peso_real - peso_calculado) / peso_calculado × 100  (PRD Story 1.3 AC5)"""
    if not peso_calculado:
        return None
    return round((peso_lote - peso_calculado) / peso_calculado * 100, 2)


def classificar_cor(pct_diferenca: Optional[float]) -> Optional[CorDiferenca]:
    """
    Classifica a faixa de cor com base no valor absoluto da % diferença.
    (PRD Story 1.3 AC8 e seção 4.5)
    - verde:    |diferença| <= 5%
    - amarelo:  5.01% <= |diferença| <= 10%
    - vermelho: |diferença| > 10%
    """
    if pct_diferenca is None:
        return None
    abs_val = abs(pct_diferenca)
    if abs_val <= 5.0:
        return CorDiferenca.VERDE
    if abs_val <= 10.0:
        return CorDiferenca.AMARELO
    return CorDiferenca.VERMELHO


def calcular_linha(oracle_row: OracleRow, fator: Optional[float]) -> ReportRow:
    """
    Aplica todos os cálculos a uma linha Oracle.

    Retorna ReportRow com colunas calculadas preenchidas ou None
    quando os dados são inválidos (PRD Story 1.3 AC6).
    """
    row = ReportRow(
        data_recurtimento=oracle_row.data_recurtimento,
        artigo=oracle_row.artigo,
        cor=oracle_row.cor,
        lote_fabricacao=oracle_row.lote_fabricacao,
        codigo_artigo=oracle_row.codigo_artigo,
        m2=oracle_row.m2,
        peso_lote=oracle_row.peso_lote,
    )

    m2 = oracle_row.m2
    peso_lote = oracle_row.peso_lote

    dados_invalidos = (
        not m2
        or not peso_lote
        or not fator
        or not oracle_row.data_recurtimento
    )
    if dados_invalidos:
        return row  # colunas calculadas permanecem None

    row.fator_aplicado = fator
    row.kg_m2 = calcular_kg_m2(peso_lote, m2)
    row.kg_ft2 = calcular_kg_ft2(peso_lote, m2)
    row.peso_calculado = calcular_peso_calculado(m2, fator)
    row.pct_diferenca = calcular_pct_diferenca(peso_lote, row.peso_calculado)
    row.cor_diferenca = classificar_cor(row.pct_diferenca)
    return row


# ---------------------------------------------------------------------------
# Cache em memória
# ---------------------------------------------------------------------------

@dataclass
class _CacheEntry:
    rows: list[ReportRow]
    expires_at: float


class ReportCache:
    """
    Cache simples em memória com TTL e invalidação explícita.
    Thread-safety não requerida — Streamlit é single-thread por sessão.
    """

    def __init__(self, ttl_seconds: int = _CACHE_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, _CacheEntry] = {}

    def get(self, key: str) -> Optional[list[ReportRow]]:
        entry = self._store.get(key)
        if entry and time.monotonic() < entry.expires_at:
            return entry.rows
        self._store.pop(key, None)
        return None

    def set(self, key: str, rows: list[ReportRow]) -> None:
        self._store[key] = _CacheEntry(
            rows=rows,
            expires_at=time.monotonic() + self._ttl,
        )

    def invalidate(self) -> None:
        """Invalida todo o cache — chamado após qualquer mudança de fator."""
        self._store.clear()
        logger.info("Cache do relatório invalidado.")

    def make_key(self, **kwargs) -> str:
        return "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))


# Instância global (substituível em testes)
_cache = ReportCache()


def get_cache() -> ReportCache:
    return _cache


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------

def build_relatorio(
    oracle_rows: list[OracleRow],
    sqlite_conn: sqlite3.Connection,
) -> list[ReportRow]:
    """
    Aplica fatores vigentes e calcula colunas derivadas para cada linha Oracle.
    Função pura em relação ao cache — usada internamente e nos testes.
    """
    result = []
    for oracle_row in oracle_rows:
        fator = None
        if oracle_row.codigo_artigo and oracle_row.data_recurtimento:
            fator = get_fator_vigente(
                sqlite_conn,
                oracle_row.codigo_artigo,
                oracle_row.data_recurtimento,
            )
        result.append(calcular_linha(oracle_row, fator))
    return result


def get_relatorio(
    sqlite_conn: sqlite3.Connection,
    data_inicio: str,
    data_fim: str,
    lote: Optional[str] = None,
    artigo: Optional[str] = None,
    cor: Optional[str] = None,
    force_refresh: bool = False,
    fetch_oracle_fn: Optional[Callable] = None,
    cache: Optional[ReportCache] = None,
) -> list[ReportRow]:
    """
    Retorna o relatório completo com colunas calculadas.

    - Usa cache com TTL 5 min (PRD Story 3.2 AC1)
    - `force_refresh=True` invalida o cache antes da consulta (Story 3.2 AC2)
    - `fetch_oracle_fn` e `cache` permitem injeção nos testes

    Levanta exceção Oracle propagada para a UI exibir mensagem de erro (Story 1.1 AC5).
    """
    if cache is None:
        cache = get_cache()

    if force_refresh:
        cache.invalidate()

    cache_key = cache.make_key(
        data_inicio=data_inicio,
        data_fim=data_fim,
        lote=lote or "",
        artigo=artigo or "",
        cor=cor or "",
    )

    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache HIT para chave '%s'.", cache_key)
        return cached

    logger.debug("Cache MISS. Consultando Oracle.")

    if fetch_oracle_fn is None:
        from repositories.oracle_repo import fetch_relatorio as fetch_oracle_fn

    oracle_rows = fetch_oracle_fn(
        data_inicio=data_inicio,
        data_fim=data_fim,
        lote=lote,
        artigo=artigo,
        cor=cor,
    )

    rows = build_relatorio(oracle_rows, sqlite_conn)
    cache.set(cache_key, rows)
    return rows


def calcular_resumo(rows: list[ReportRow]) -> dict:
    """
    Calcula totais para o cabeçalho do PDF (PRD Story 1.4 AC4):
    total de linhas, média de % diferença e contagem por faixa de cor.
    """
    com_calculo = [r for r in rows if r.pct_diferenca is not None]

    media_pct = None
    if com_calculo:
        media_pct = round(
            sum(r.pct_diferenca for r in com_calculo) / len(com_calculo), 2
        )

    return {
        "total_linhas": len(rows),
        "media_pct_diferenca": media_pct,
        "total_verde": sum(1 for r in rows if r.cor_diferenca == CorDiferenca.VERDE),
        "total_amarelo": sum(1 for r in rows if r.cor_diferenca == CorDiferenca.AMARELO),
        "total_vermelho": sum(1 for r in rows if r.cor_diferenca == CorDiferenca.VERMELHO),
        "total_sem_calculo": len(rows) - len(com_calculo),
    }
