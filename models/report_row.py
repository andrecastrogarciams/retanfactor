from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CorDiferenca(str, Enum):
    VERDE = "verde"
    AMARELO = "amarelo"
    VERMELHO = "vermelho"


@dataclass
class OracleRow:
    """Linha bruta da view Oracle USU_VBI_OPREC_V2."""
    data_recurtimento: Optional[str]   # ISO-8601: 'YYYY-MM-DD'
    artigo: Optional[str]
    cor: Optional[str]
    lote_fabricacao: Optional[str]
    codigo_artigo: Optional[str]
    m2: Optional[float]
    peso_lote: Optional[float]


@dataclass
class ReportRow:
    """Linha do relatório com colunas derivadas calculadas."""
    # Colunas Oracle (origem)
    data_recurtimento: Optional[str]
    artigo: Optional[str]
    cor: Optional[str]
    lote_fabricacao: Optional[str]
    codigo_artigo: Optional[str]
    m2: Optional[float]
    peso_lote: Optional[float]

    # Colunas calculadas (None quando sem fator ou dados inválidos)
    kg_m2: Optional[float] = None
    kg_ft2: Optional[float] = None
    fator_aplicado: Optional[float] = None
    peso_calculado: Optional[float] = None
    pct_diferenca: Optional[float] = None
    cor_diferenca: Optional[CorDiferenca] = None
