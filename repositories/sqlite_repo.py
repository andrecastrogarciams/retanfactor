import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from models.factor import FatorArtigo

logger = logging.getLogger(__name__)

_MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"
_SENTINEL_DATE = "9999-12-31"  # Representa vigência aberta nas comparações de sobreposição


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ---------------------------------------------------------------------------
# Migrations
# ---------------------------------------------------------------------------

def apply_migrations(conn: sqlite3.Connection, migrations_dir: Path = _MIGRATIONS_DIR) -> None:
    """Aplica migrations pendentes em ordem numérica. Idempotente."""
    _ensure_schema_version_table(conn)

    applied = {
        row["version"]
        for row in conn.execute("SELECT version FROM schema_version").fetchall()
    }

    migration_files = sorted(
        f for f in migrations_dir.glob("*.sql")
        if not f.parent.name == "rollbacks"
    )

    for migration_file in migration_files:
        version = migration_file.stem.split("_")[0]
        if version in applied:
            continue

        sql = migration_file.read_text(encoding="utf-8")
        logger.info("Aplicando migration %s: %s", version, migration_file.name)
        conn.executescript(sql)
        logger.info("Migration %s aplicada com sucesso.", version)


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            version     TEXT    NOT NULL UNIQUE,
            description TEXT    NOT NULL,
            applied_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            checksum    TEXT
        );
    """)


# ---------------------------------------------------------------------------
# Consulta de vigência — Q1 (hottest path)
# ---------------------------------------------------------------------------

def get_fator_vigente(
    conn: sqlite3.Connection,
    codigo_artigo: str,
    data_referencia: str,
) -> Optional[float]:
    """
    Retorna o fator vigente para um artigo em uma data específica.

    Se houver múltiplos registros válidos (inconsistência preexistente),
    usa o mais recente e registra ocorrência em log — conforme PRD Story 1.3 AC7.
    """
    rows = conn.execute(
        """
        SELECT fator, data_inicio_vigencia
        FROM   fator_artigo
        WHERE  codigo_artigo        = :codigo
          AND  status               = 'ativo'
          AND  data_inicio_vigencia <= :data
          AND  (data_fim_vigencia IS NULL OR data_fim_vigencia >= :data)
        ORDER BY data_inicio_vigencia DESC
        """,
        {"codigo": codigo_artigo, "data": data_referencia},
    ).fetchall()

    if not rows:
        return None

    if len(rows) > 1:
        logger.warning(
            "Múltiplos fatores vigentes para artigo '%s' na data '%s'. "
            "Usando o mais recente (data_inicio=%s). Verifique inconsistência no banco.",
            codigo_artigo,
            data_referencia,
            rows[0]["data_inicio_vigencia"],
        )

    return rows[0]["fator"]


# ---------------------------------------------------------------------------
# Validação de sobreposição
# ---------------------------------------------------------------------------

def has_vigencia_overlap(
    conn: sqlite3.Connection,
    codigo_artigo: str,
    data_inicio: str,
    data_fim: Optional[str],
    exclude_id: Optional[int] = None,
) -> bool:
    """
    Verifica se existe sobreposição de vigência para o mesmo código de artigo.
    Considera vigências abertas (data_fim=None) como '9999-12-31'.
    """
    data_fim_param = data_fim if data_fim else _SENTINEL_DATE

    query = """
        SELECT COUNT(*) AS total
        FROM   fator_artigo
        WHERE  codigo_artigo        = :codigo
          AND  status               = 'ativo'
          AND  data_inicio_vigencia <= :data_fim_nova
          AND  COALESCE(data_fim_vigencia, :sentinel) >= :data_inicio_nova
    """
    params: dict = {
        "codigo":          codigo_artigo,
        "data_inicio_nova": data_inicio,
        "data_fim_nova":    data_fim_param,
        "sentinel":         _SENTINEL_DATE,
    }

    if exclude_id is not None:
        query += " AND id != :exclude_id"
        params["exclude_id"] = exclude_id

    row = conn.execute(query, params).fetchone()
    return row["total"] > 0


# ---------------------------------------------------------------------------
# Inserção com validação de sobreposição
# ---------------------------------------------------------------------------

def insert_fator(conn: sqlite3.Connection, fator: FatorArtigo) -> int:
    """
    Insere um novo fator. Levanta ValueError se houver sobreposição de vigência.
    Executado dentro de transação para garantir atomicidade.
    """
    with transaction(conn):
        if has_vigencia_overlap(
            conn,
            fator.codigo_artigo,
            fator.data_inicio_vigencia,
            fator.data_fim_vigencia,
        ):
            raise ValueError(
                f"Sobreposição de vigência detectada para o artigo '{fator.codigo_artigo}' "
                f"no período {fator.data_inicio_vigencia} → {fator.data_fim_vigencia or 'aberto'}."
            )

        cursor = conn.execute(
            """
            INSERT INTO fator_artigo
                (codigo_artigo, descricao_artigo, fator,
                 data_inicio_vigencia, data_fim_vigencia, observacao)
            VALUES
                (:codigo_artigo, :descricao_artigo, :fator,
                 :data_inicio_vigencia, :data_fim_vigencia, :observacao)
            """,
            {
                "codigo_artigo":        fator.codigo_artigo,
                "descricao_artigo":     fator.descricao_artigo,
                "fator":                fator.fator,
                "data_inicio_vigencia": fator.data_inicio_vigencia,
                "data_fim_vigencia":    fator.data_fim_vigencia,
                "observacao":           fator.observacao,
            },
        )
        new_id = cursor.lastrowid
        logger.info(
            "Fator criado: id=%d artigo='%s' fator=%.4f vigencia=%s→%s",
            new_id,
            fator.codigo_artigo,
            fator.fator,
            fator.data_inicio_vigencia,
            fator.data_fim_vigencia or "aberto",
        )
        return new_id


# ---------------------------------------------------------------------------
# Inativação transacional
# ---------------------------------------------------------------------------

def cancel_fator(
    conn: sqlite3.Connection,
    fator_id: int,
    motivo: str,
) -> None:
    """
    Inativa um fator ativo. Levanta ValueError se o registro não existir ou
    já estiver cancelado (protege contra duplo cancelamento).
    """
    if not motivo or not motivo.strip():
        raise ValueError("Motivo de cancelamento é obrigatório.")

    with transaction(conn):
        cursor = conn.execute(
            """
            UPDATE fator_artigo
            SET    status              = 'cancelado',
                   motivo_cancelamento = :motivo,
                   cancelled_at        = datetime('now', 'localtime')
            WHERE  id     = :id
              AND  status = 'ativo'
            """,
            {"id": fator_id, "motivo": motivo.strip()},
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Fator id={fator_id} não encontrado ou já está cancelado."
            )

        logger.info("Fator id=%d cancelado. Motivo: %s", fator_id, motivo.strip())


# ---------------------------------------------------------------------------
# Consultas de histórico
# ---------------------------------------------------------------------------

def list_fatores(
    conn: sqlite3.Connection,
    codigo_artigo: Optional[str] = None,
    apenas_vigentes: bool = False,
    data_inicio_filtro: Optional[str] = None,
    data_fim_filtro: Optional[str] = None,
) -> list[FatorArtigo]:
    """Lista fatores com filtros opcionais. Usado na tela de histórico."""
    where_clauses = []
    params: dict = {}

    if codigo_artigo:
        where_clauses.append("codigo_artigo = :codigo")
        params["codigo"] = codigo_artigo

    if apenas_vigentes:
        where_clauses.append("status = 'ativo'")

    if data_inicio_filtro:
        where_clauses.append("data_inicio_vigencia >= :inicio_filtro")
        params["inicio_filtro"] = data_inicio_filtro

    if data_fim_filtro:
        where_clauses.append(
            "(data_fim_vigencia IS NULL OR data_fim_vigencia <= :fim_filtro)"
        )
        params["fim_filtro"] = data_fim_filtro

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = conn.execute(
        f"""
        SELECT *
        FROM   fator_artigo
        {where_sql}
        ORDER BY codigo_artigo, created_at DESC
        """,
        params,
    ).fetchall()

    return [_row_to_fator(row) for row in rows]


def get_fator_by_id(
    conn: sqlite3.Connection,
    fator_id: int,
) -> Optional[FatorArtigo]:
    row = conn.execute(
        "SELECT * FROM fator_artigo WHERE id = :id",
        {"id": fator_id},
    ).fetchone()
    return _row_to_fator(row) if row else None


def duplicate_fator(
    conn: sqlite3.Connection,
    fator_id: int,
    data_inicio_nova: str,
    data_fim_nova: Optional[str] = None,
) -> int:
    """
    Duplica um fator existente com nova vigência.
    Reutiliza código, descrição, fator e observação — conforme PRD Story 2.4 AC1.
    """
    origem = get_fator_by_id(conn, fator_id)
    if origem is None:
        raise ValueError(f"Fator id={fator_id} não encontrado.")

    novo_fator = FatorArtigo(
        codigo_artigo=origem.codigo_artigo,
        descricao_artigo=origem.descricao_artigo,
        fator=origem.fator,
        data_inicio_vigencia=data_inicio_nova,
        data_fim_vigencia=data_fim_nova,
        observacao=origem.observacao,
    )

    return insert_fator(conn, novo_fator)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _row_to_fator(row: sqlite3.Row) -> FatorArtigo:
    return FatorArtigo(
        id=row["id"],
        codigo_artigo=row["codigo_artigo"],
        descricao_artigo=row["descricao_artigo"],
        fator=row["fator"],
        data_inicio_vigencia=row["data_inicio_vigencia"],
        data_fim_vigencia=row["data_fim_vigencia"],
        observacao=row["observacao"],
        status=row["status"],
        motivo_cancelamento=row["motivo_cancelamento"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        cancelled_at=row["cancelled_at"],
    )
