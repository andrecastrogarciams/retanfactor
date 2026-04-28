"""
Configuração centralizada da aplicação.
Todas as variáveis sensíveis lidas de env — nunca hardcoded.
"""
import os
import sqlite3
from functools import lru_cache
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Identificação do ambiente
# ---------------------------------------------------------------------------

APP_ENV: str = os.environ.get("APP_ENV", "producao")  # homologacao | producao
ESTACAO: str = os.environ.get("ESTACAO", "RECURTIMENTO")

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DB_PATH: str = os.environ.get(
    "SQLITE_DB_PATH",
    str(BASE_DIR / "data" / f"fatores_{APP_ENV}.db"),
)
MIGRATIONS_DIR: Path = BASE_DIR / "migrations"
LOG_DIR: Path = BASE_DIR / "logs"
LOGO_PATH: Path = BASE_DIR / "assets" / "logo.png"

# ---------------------------------------------------------------------------
# Oracle
# ---------------------------------------------------------------------------

ORACLE_DSN: str = os.environ.get("ORACLE_DSN", "")
ORACLE_USER: str = os.environ.get("ORACLE_USER", "")
ORACLE_TIMEOUT_SECONDS: int = int(os.environ.get("ORACLE_TIMEOUT_SECONDS", "30"))

# ---------------------------------------------------------------------------
# Conexão SQLite — cacheada por sessão Streamlit
# ---------------------------------------------------------------------------

@st.cache_resource
def get_sqlite_conn() -> sqlite3.Connection:
    """
    Retorna conexão SQLite reutilizada pela sessão Streamlit.
    Aplica migrations na primeira chamada.
    """
    from repositories.sqlite_repo import apply_migrations, get_connection

    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(DB_PATH)
    apply_migrations(conn, MIGRATIONS_DIR)
    return conn


# ---------------------------------------------------------------------------
# Banner de ambiente (não produção)
# ---------------------------------------------------------------------------

def render_env_banner() -> None:
    """Exibe banner vermelho em ambientes que não são produção."""
    if APP_ENV != "producao":
        st.error(
            f"⚠️ AMBIENTE: **{APP_ENV.upper()}** — "
            "dados reais de Oracle. Exportação PDF desabilitada.",
            icon="🚧",
        )


# ---------------------------------------------------------------------------
# Design system — re-exportações para uso nas páginas
# ---------------------------------------------------------------------------

from assets.theme import inject_global_css, render_page_header  # noqa: E402, F401


# ---------------------------------------------------------------------------
# Logging — configurado uma única vez na inicialização (Story 3.3 AC1)
# ---------------------------------------------------------------------------

from logging_config import setup_logging  # noqa: E402

setup_logging(LOG_DIR)
