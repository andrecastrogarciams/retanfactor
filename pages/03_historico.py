"""
Página: Histórico de Fatores
Story 2.3 — Consultar histórico de fatores
Story 2.4 — Duplicar e inativar fator
"""
import logging
from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ESTACAO, get_sqlite_conn, render_env_banner
from models.factor import FatorArtigo
from services.factor_service import (
    buscar_fator,
    cancelar_fator,
    duplicar_fator,
    listar_fatores,
)

logger = logging.getLogger(__name__)

PAGE_TITLE = "Histórico de Fatores"
PAGE_ICON = "📋"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

# Rótulos das colunas da tabela de histórico
_COLUNAS_HISTORICO = {
    "id":                   "ID",
    "codigo_artigo":        "Cód. Artigo",
    "descricao_artigo":     "Artigo",
    "fator":                "Fator",
    "data_inicio_vigencia": "Início Vigência",
    "data_fim_vigencia":    "Fim Vigência",
    "observacao":           "Observação",
    "status_display":       "Status",
    "motivo_cancelamento":  "Motivo Cancelamento",
    "created_at":           "Criado em",
    "cancelled_at":         "Cancelado em",
}

_COR_ATIVO = "#d4edda"
_COR_CANCELADO = "#f8d7da"


# ---------------------------------------------------------------------------
# Formatação — funções puras, testáveis
# ---------------------------------------------------------------------------

def formatar_status(fator: FatorArtigo) -> str:
    """
    Retorna texto de status com indicador visual.
    Cobre vigência aberta e cancelamento (PRD Story 2.3 AC6).
    """
    if fator.status == "cancelado":
        return "🔴 Cancelado"
    if fator.data_fim_vigencia is None:
        return "🟢 Ativo (aberto)"
    return "🟢 Ativo"


def formatar_vigencia(fator: FatorArtigo) -> str:
    """Formata período de vigência para exibição."""
    inicio = fator.data_inicio_vigencia or "—"
    fim = fator.data_fim_vigencia or "em aberto"
    return f"{inicio} → {fim}"


def fatores_para_dataframe(fatores: list[FatorArtigo]) -> pd.DataFrame:
    """
    Converte lista de FatorArtigo em DataFrame formatado para exibição.
    Inclui coluna status_display com indicador visual (PRD Story 2.3 AC6).
    """
    if not fatores:
        return pd.DataFrame(columns=list(_COLUNAS_HISTORICO.values()))

    rows = []
    for f in fatores:
        rows.append({
            "id":                   f.id,
            "codigo_artigo":        f.codigo_artigo,
            "descricao_artigo":     f.descricao_artigo,
            "fator":                f.fator,
            "data_inicio_vigencia": f.data_inicio_vigencia,
            "data_fim_vigencia":    f.data_fim_vigencia or "em aberto",
            "observacao":           f.observacao or "",
            "status_display":       formatar_status(f),
            "motivo_cancelamento":  f.motivo_cancelamento or "",
            "created_at":           f.created_at or "",
            "cancelled_at":         f.cancelled_at or "",
        })

    df = pd.DataFrame(rows)
    df.rename(columns=_COLUNAS_HISTORICO, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Validação dos formulários de ação — funções puras, testáveis
# ---------------------------------------------------------------------------

def validar_duplicacao(
    fator_id: Optional[int],
    data_inicio_nova: Optional[date],
    data_fim_nova: Optional[date],
    fator_origem: Optional[FatorArtigo],
) -> list[str]:
    """Valida o formulário de duplicação antes de acionar o serviço."""
    erros = []

    if fator_id is None:
        erros.append("Selecione um registro para duplicar.")
        return erros

    if fator_origem is None:
        erros.append(f"Registro ID {fator_id} não encontrado.")
        return erros

    if fator_origem.status == "cancelado":
        erros.append("Não é possível duplicar um fator cancelado.")

    if data_inicio_nova is None:
        erros.append("Data de início da nova vigência é obrigatória.")

    if data_inicio_nova and data_fim_nova and data_fim_nova <= data_inicio_nova:
        erros.append("Data de fim deve ser posterior à data de início.")

    return erros


def validar_cancelamento(
    fator_id: Optional[int],
    motivo: str,
    fator_origem: Optional[FatorArtigo],
) -> list[str]:
    """Valida o formulário de cancelamento antes de acionar o serviço."""
    erros = []

    if fator_id is None:
        erros.append("Selecione um registro para cancelar.")
        return erros

    if fator_origem is None:
        erros.append(f"Registro ID {fator_id} não encontrado.")
        return erros

    if fator_origem.status == "cancelado":
        erros.append("Este fator já está cancelado.")

    if not motivo or not motivo.strip():
        erros.append("Motivo de cancelamento é obrigatório. (PRD Story 2.4 AC3)")

    return erros


# ---------------------------------------------------------------------------
# Componentes de UI
# ---------------------------------------------------------------------------

def _render_filtros() -> dict:
    """Filtros no sidebar (PRD Story 2.3 AC2-4)."""
    st.sidebar.header("Filtros")

    codigo = st.sidebar.text_input(
        "Código do artigo",
        placeholder="ex: ART001",
    ).strip() or None

    apenas_vigentes = st.sidebar.checkbox("Somente vigentes", value=False)

    st.sidebar.markdown("**Período de vigência**")
    data_inicio_filtro = st.sidebar.date_input(
        "Início a partir de",
        value=None,
        format="DD/MM/YYYY",
    )
    data_fim_filtro = st.sidebar.date_input(
        "Fim até",
        value=None,
        format="DD/MM/YYYY",
    )

    return {
        "codigo_artigo":      codigo,
        "apenas_vigentes":    apenas_vigentes,
        "data_inicio_filtro": data_inicio_filtro.strftime("%Y-%m-%d")
                              if isinstance(data_inicio_filtro, date) else None,
        "data_fim_filtro":    data_fim_filtro.strftime("%Y-%m-%d")
                              if isinstance(data_fim_filtro, date) else None,
    }


def _render_tabela(fatores: list[FatorArtigo]) -> None:
    """Renderiza tabela de histórico com destaque por status."""
    df = fatores_para_dataframe(fatores)

    if df.empty:
        st.info("Nenhum registro encontrado para os filtros selecionados.")
        return

    total = len(fatores)
    ativos = sum(1 for f in fatores if f.status == "ativo")
    cancelados = total - ativos

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de registros", total)
    col2.metric("🟢 Ativos", ativos)
    col3.metric("🔴 Cancelados", cancelados)

    st.divider()

    # Highlight por status
    def _highlight(row):
        if "Cancelado" in str(row.get("Status", "")):
            return [f"background-color: {_COR_CANCELADO}"] * len(row)
        return [f"background-color: {_COR_ATIVO}"] * len(row)

    st.dataframe(
        df.style.apply(_highlight, axis=1),
        use_container_width=True,
        hide_index=True,
        height=400,
    )


def _render_form_duplicacao(fatores: list[FatorArtigo], conn) -> None:
    """Formulário de duplicação (PRD Story 2.4 AC1-2)."""
    st.subheader("📋 Duplicar Fator")
    st.caption(
        "Reutiliza código, artigo, fator e observação. "
        "Informe a nova vigência."
    )

    ativos = [f for f in fatores if f.status == "ativo"]
    if not ativos:
        st.info("Não há fatores ativos para duplicar.")
        return

    opcoes_dup = {
        f"ID {f.id} — {f.codigo_artigo} | fator={f.fator:.4f} | "
        f"{f.data_inicio_vigencia}→{f.data_fim_vigencia or 'aberto'}": f.id
        for f in ativos
    }

    with st.form("form_duplicacao"):
        selecao = st.selectbox(
            "Registro a duplicar *",
            options=list(opcoes_dup.keys()),
            index=None,
            placeholder="Selecione...",
        )
        fator_id_dup = opcoes_dup[selecao] if selecao else None

        # Pré-visualização do registro selecionado (PRD Story 2.4 AC1)
        if fator_id_dup:
            origem = next((f for f in ativos if f.id == fator_id_dup), None)
            if origem:
                st.info(
                    f"**Artigo:** {origem.descricao_artigo} | "
                    f"**Fator:** {origem.fator:.4f} | "
                    f"**Observação:** {origem.observacao or '—'}",
                    icon="ℹ️",
                )

        st.markdown("**Nova vigência**")
        col_inicio, col_fim = st.columns(2)
        with col_inicio:
            data_inicio_dup = st.date_input(
                "Início *", value=None, format="DD/MM/YYYY", key="dup_inicio"
            )
        with col_fim:
            data_fim_dup = st.date_input(
                "Fim", value=None, format="DD/MM/YYYY", key="dup_fim",
                help="Deixe em branco para vigência em aberto."
            )

        submitted_dup = st.form_submit_button(
            "📋 Duplicar", type="primary", use_container_width=True
        )

    if not submitted_dup:
        return

    fator_origem = buscar_fator(conn, fator_id_dup) if fator_id_dup else None
    data_inicio_val = data_inicio_dup if isinstance(data_inicio_dup, date) else None
    data_fim_val = data_fim_dup if isinstance(data_fim_dup, date) else None

    erros = validar_duplicacao(fator_id_dup, data_inicio_val, data_fim_val, fator_origem)
    if erros:
        for e in erros:
            st.error(f"❌ {e}")
        return

    try:
        new_id = duplicar_fator(
            conn,
            fator_id=fator_id_dup,
            data_inicio_nova=data_inicio_val.strftime("%Y-%m-%d"),
            estacao=ESTACAO,
            data_fim_nova=data_fim_val.strftime("%Y-%m-%d") if data_fim_val else None,
        )
        st.success(
            f"✅ Fator duplicado com sucesso! Novo ID: **{new_id}**. "
            "Recarregue a página para ver o novo registro.",
        )
        st.rerun()
    except ValueError as exc:
        st.error(f"❌ {exc}")
    except Exception as exc:
        logger.error("ERRO_DUPLICACAO | estacao=%s | id=%s | erro=%s",
                     ESTACAO, fator_id_dup, str(exc))
        st.error(f"❌ Erro inesperado ao duplicar.\n\n`{exc}`")


def _render_form_cancelamento(fatores: list[FatorArtigo], conn) -> None:
    """Formulário de cancelamento/inativação (PRD Story 2.4 AC3-8)."""
    st.subheader("🚫 Inativar Fator")
    st.caption("O fator cancelado deixa de ser aplicado nos cálculos futuros.")

    ativos = [f for f in fatores if f.status == "ativo"]
    if not ativos:
        st.info("Não há fatores ativos para cancelar.")
        return

    opcoes_can = {
        f"ID {f.id} — {f.codigo_artigo} | fator={f.fator:.4f} | "
        f"{f.data_inicio_vigencia}→{f.data_fim_vigencia or 'aberto'}": f.id
        for f in ativos
    }

    with st.form("form_cancelamento"):
        selecao = st.selectbox(
            "Registro a inativar *",
            options=list(opcoes_can.keys()),
            index=None,
            placeholder="Selecione...",
        )
        fator_id_can = opcoes_can[selecao] if selecao else None

        motivo = st.text_area(
            "Motivo de cancelamento *",
            value="",
            max_chars=500,
            placeholder="Descreva o motivo da inativação...",
            height=80,
            help="Obrigatório. Será registrado permanentemente.",
        )

        submitted_can = st.form_submit_button(
            "🚫 Inativar", type="primary", use_container_width=True
        )

    if not submitted_can:
        return

    fator_origem = buscar_fator(conn, fator_id_can) if fator_id_can else None
    erros = validar_cancelamento(fator_id_can, motivo, fator_origem)
    if erros:
        for e in erros:
            st.error(f"❌ {e}")
        return

    try:
        cancelar_fator(conn, fator_id=fator_id_can, motivo=motivo, estacao=ESTACAO)
        st.success(
            f"✅ Fator ID **{fator_id_can}** inativado. "
            "O relatório já reflete esta alteração."
        )
        st.rerun()
    except ValueError as exc:
        st.error(f"❌ {exc}")
    except Exception as exc:
        logger.error("ERRO_CANCELAMENTO | estacao=%s | id=%s | erro=%s",
                     ESTACAO, fator_id_can, str(exc))
        st.error(f"❌ Erro inesperado ao inativar.\n\n`{exc}`")


# ---------------------------------------------------------------------------
# Página principal
# ---------------------------------------------------------------------------

def main() -> None:
    render_env_banner()
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.caption(f"Estação: **{ESTACAO}**")

    filtros = _render_filtros()

    # Carregamento do histórico (PRD Story 2.3 AC7-8)
    try:
        conn = get_sqlite_conn()
        fatores = listar_fatores(conn, **filtros)
    except Exception as exc:
        logger.error("ERRO_SQLITE_HISTORICO | estacao=%s | erro=%s", ESTACAO, str(exc))
        st.error(
            f"❌ Falha ao carregar o histórico de fatores. "
            f"Verifique o banco de dados.\n\n`{exc}`"
        )
        return

    # Tabela principal
    _render_tabela(fatores)

    st.divider()

    # Ações por registro
    col_dup, col_can = st.columns(2)

    with col_dup:
        _render_form_duplicacao(fatores, conn)

    with col_can:
        _render_form_cancelamento(fatores, conn)


if __name__ == "__main__":
    main()
