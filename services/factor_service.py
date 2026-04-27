"""
Serviço de negócio para gestão de fatores de artigo.

Responsabilidades:
- Orquestrar operações sobre sqlite_repo com log estruturado
- Invalidar cache do relatório após qualquer mutação
- Expor API limpa para as páginas UI (cadastro e histórico)
"""
import logging
import sqlite3
from typing import Optional

from models.factor import FatorArtigo
from repositories import sqlite_repo
from services.report_service import get_cache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------

def buscar_fator(conn: sqlite3.Connection, fator_id: int) -> Optional[FatorArtigo]:
    return sqlite_repo.get_fator_by_id(conn, fator_id)


def listar_fatores(
    conn: sqlite3.Connection,
    codigo_artigo: Optional[str] = None,
    apenas_vigentes: bool = False,
    data_inicio_filtro: Optional[str] = None,
    data_fim_filtro: Optional[str] = None,
) -> list[FatorArtigo]:
    return sqlite_repo.list_fatores(
        conn,
        codigo_artigo=codigo_artigo,
        apenas_vigentes=apenas_vigentes,
        data_inicio_filtro=data_inicio_filtro,
        data_fim_filtro=data_fim_filtro,
    )


# ---------------------------------------------------------------------------
# Mutações — todas invalidam o cache do relatório (PRD Story 3.2 AC3)
# ---------------------------------------------------------------------------

def criar_fator(
    conn: sqlite3.Connection,
    fator: FatorArtigo,
    estacao: str,
) -> int:
    """
    Persiste novo fator e invalida o cache do relatório.

    Levanta ValueError se houver sobreposição de vigência (PRD Story 2.2).
    Registra log com metadados obrigatórios (PRD Story 2.1 AC8).
    """
    _validar_fator(fator)

    new_id = sqlite_repo.insert_fator(conn, fator)
    get_cache().invalidate()

    logger.info(
        "FATOR_CRIADO | estacao=%s | codigo_artigo=%s | fator=%.4f "
        "| vigencia=%s→%s | id=%d",
        estacao,
        fator.codigo_artigo,
        fator.fator,
        fator.data_inicio_vigencia,
        fator.data_fim_vigencia or "aberto",
        new_id,
    )
    return new_id


def cancelar_fator(
    conn: sqlite3.Connection,
    fator_id: int,
    motivo: str,
    estacao: str,
) -> None:
    """
    Inativa fator e invalida o cache do relatório.

    Levanta ValueError se o registro não existir ou já estiver cancelado.
    Registra log com metadados obrigatórios (PRD Story 2.4 AC7).
    """
    fator = sqlite_repo.get_fator_by_id(conn, fator_id)
    if fator is None:
        raise ValueError(f"Fator id={fator_id} não encontrado.")

    sqlite_repo.cancel_fator(conn, fator_id, motivo)
    get_cache().invalidate()

    logger.info(
        "FATOR_CANCELADO | estacao=%s | codigo_artigo=%s | fator=%.4f "
        "| vigencia=%s→%s | motivo=%s | id=%d",
        estacao,
        fator.codigo_artigo,
        fator.fator,
        fator.data_inicio_vigencia,
        fator.data_fim_vigencia or "aberto",
        motivo,
        fator_id,
    )


def duplicar_fator(
    conn: sqlite3.Connection,
    fator_id: int,
    data_inicio_nova: str,
    estacao: str,
    data_fim_nova: Optional[str] = None,
) -> int:
    """
    Duplica fator com nova vigência e invalida o cache do relatório.

    Reutiliza código, descrição, fator e observação do registro original.
    Levanta ValueError se sobreposição detectada (PRD Story 2.2 AC8).
    Registra log com metadados obrigatórios (PRD Story 2.4 AC7).
    """
    if not data_inicio_nova:
        raise ValueError("Data de início da nova vigência é obrigatória.")

    new_id = sqlite_repo.duplicate_fator(conn, fator_id, data_inicio_nova, data_fim_nova)
    novo = sqlite_repo.get_fator_by_id(conn, new_id)
    get_cache().invalidate()

    logger.info(
        "FATOR_DUPLICADO | estacao=%s | origem_id=%d | novo_id=%d "
        "| codigo_artigo=%s | fator=%.4f | vigencia=%s→%s",
        estacao,
        fator_id,
        new_id,
        novo.codigo_artigo,
        novo.fator,
        data_inicio_nova,
        data_fim_nova or "aberto",
    )
    return new_id


# ---------------------------------------------------------------------------
# Validações de negócio (complementares às constraints do banco)
# ---------------------------------------------------------------------------

def _validar_fator(fator: FatorArtigo) -> None:
    erros = []

    if not fator.codigo_artigo or not fator.codigo_artigo.strip():
        erros.append("Código do artigo é obrigatório.")

    if not fator.descricao_artigo or not fator.descricao_artigo.strip():
        erros.append("Descrição do artigo é obrigatória.")

    if fator.fator is None or fator.fator <= 0:
        erros.append("Fator deve ser maior que zero.")

    if not fator.data_inicio_vigencia:
        erros.append("Data de início da vigência é obrigatória.")

    if erros:
        raise ValueError(" | ".join(erros))
