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
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ESTACAO, get_sqlite_conn, inject_global_css, render_env_banner, render_page_header
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
    "status_display":       "Status",
    "observacao":           "Observação",
    "motivo_cancelamento":  "Motivo Cancelamento",
    "created_at":           "Criado em",
    "cancelled_at":         "Cancelado em",
}

# ---------------------------------------------------------------------------
# Formatação e Helpers
# ---------------------------------------------------------------------------

def formatar_status(fator: FatorArtigo) -> str:
    """Retorna texto de status com indicador visual."""
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
            "status_display":       formatar_status(f),
            "observacao":           f.observacao or "",
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
# Modais de Ação (st.dialog) — Story 4.4 AC6
# ---------------------------------------------------------------------------

@st.dialog("Confirmar Inativação")
def modal_inativacao(fator: FatorArtigo, conn):
    st.warning(f"Você está prestes a inativar o fator ID {fator.id} para o artigo {fator.codigo_artigo}.")
    motivo = st.text_area("Motivo da inativação *", placeholder="Informe o motivo (obrigatório)", height=100)
    
    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancelar Inativação", use_container_width=True):
            st.rerun()
    with col_confirm:
        if st.button("Confirmar Inativação", type="primary", use_container_width=True):
            erros = validar_cancelamento(fator.id, motivo, fator)
            if erros:
                for e in erros:
                    st.error(e)
            else:
                try:
                    cancelar_fator(conn, fator.id, motivo.strip(), ESTACAO)
                    st.success("Fator inativado com sucesso!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Erro ao inativar: {exc}")


@st.dialog("Duplicar Fator")
def modal_duplicacao(fator: FatorArtigo, conn):
    st.info(f"Duplicando registro ID {fator.id} ({fator.codigo_artigo}).")
    st.markdown(f"**Artigo:** {fator.descricao_artigo}")
    st.markdown(f"**Fator:** {fator.fator:.4f}")
    
    st.divider()
    st.markdown("**Nova Vigência**")
    col_ini, col_fim = st.columns(2)
    with col_ini:
        data_inicio = st.date_input("Início *", value=None, format="DD/MM/YYYY")
    with col_fim:
        data_fim = st.date_input("Fim (Opcional)", value=None, format="DD/MM/YYYY")
        
    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancelar Duplicação", use_container_width=True):
            st.rerun()
    with col_confirm:
        if st.button("Confirmar Duplicação", type="primary", use_container_width=True):
            erros = validar_duplicacao(fator.id, data_inicio, data_fim, fator)
            if erros:
                for e in erros:
                    st.error(e)
            else:
                try:
                    new_id = duplicar_fator(
                        conn, 
                        fator.id, 
                        data_inicio.strftime("%Y-%m-%d"), 
                        ESTACAO,
                        data_fim.strftime("%Y-%m-%d") if data_fim else None
                    )
                    st.success(f"Fator duplicado! Novo ID: {new_id}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Erro ao duplicar: {exc}")


# ---------------------------------------------------------------------------
# Componentes de UI
# ---------------------------------------------------------------------------

def _render_filtros() -> dict:
    """Filtros horizontais (PRD Story 2.3 | Story 4.4 AC2)."""
    col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1])

    with col1:
        codigo = st.text_input("Código do artigo", placeholder="ex: ART001").strip() or None
    with col2:
        data_inicio = st.date_input("Início vigência", value=None, format="DD/MM/YYYY")
    with col3:
        data_fim = st.date_input("Fim vigência", value=None, format="DD/MM/YYYY")
    with col4:
        st.write("") # alinhamento
        apenas_vigentes = st.checkbox("Somente vigentes", value=False)
    with col5:
        st.write("") # alinhamento
        btn_aplicar = st.button("Aplicar", type="primary", use_container_width=True)

    # Botão Limpar (Story 4.4 AC7)
    if st.sidebar.button("Limpar Filtros", type="secondary", use_container_width=True):
        st.rerun()

    return {
        "codigo_artigo":      codigo,
        "apenas_vigentes":    apenas_vigentes,
        "data_inicio_filtro": data_inicio.strftime("%Y-%m-%d") if isinstance(data_inicio, date) else None,
        "data_fim_filtro":    data_fim.strftime("%Y-%m-%d") if isinstance(data_fim, date) else None,
    }


def _build_grid_options(df: pd.DataFrame) -> dict:
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configurações padrão
    gb.configure_default_column(resizable=True, sortable=True, filter=True)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    
    # Badge de Status (Story 4.4 AC4)
    cell_style_status = JsCode("""
    function(params) {
        if (params.value.includes('Ativo'))
            return { backgroundColor: '#d5e3ff', color: '#1f477b', 
                     borderRadius: '12px', padding: '2px 8px', 
                     display: 'inline-block', fontWeight: '500', marginTop: '4px' };
        return { backgroundColor: '#eeedf2', color: '#43474f', 
                 borderRadius: '12px', padding: '2px 8px', 
                 display: 'inline-block', fontWeight: '500', marginTop: '4px' };
    }
    """)
    
    # Colunas específicas usando os labels do DF (que veio de _COLUNAS_HISTORICO.values())
    gb.configure_column("ID", width=80)
    gb.configure_column("Cód. Artigo", width=120)
    gb.configure_column("Artigo", width=200)
    gb.configure_column("Fator", width=100, type=["numericColumn"], 
                        valueFormatter="x.toFixed(4)", cellStyle={'textAlign': 'right'})
    gb.configure_column("Início Vigência", width=120)
    gb.configure_column("Fim Vigência", width=120)
    gb.configure_column("Status", width=150, cellStyle=cell_style_status)
    gb.configure_column("Observação", width=250)

    # Seleção de linha para disparar as ações
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    
    grid_options = gb.build()
    grid_options["rowHeight"] = 36
    grid_options["headerHeight"] = 40
    
    return grid_options


def _render_tabela(fatores: list[FatorArtigo], conn) -> None:
    """Renderiza tabela AgGrid (Story 4.4 AC3-5)."""
    df = fatores_para_dataframe(fatores)

    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    grid_options = _build_grid_options(df)
    
    st.markdown(
        "<p style='font-size:12px;color:#737780;margin-bottom:8px;'>"
        "Selecione uma linha para duplicar ou inativar o fator.</p>", 
        unsafe_allow_html=True
    )

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        theme="streamlit",
        height=400,
        fit_columns_on_grid_load=True,
    )

    selected = grid_response.get("selected_rows")
    if selected is not None and len(selected) > 0:
        row = selected.iloc[0] if hasattr(selected, "iloc") else selected[0]
        fator_id = int(row["ID"])
        fator_obj = next((f for f in fatores if f.id == fator_id), None)
        
        if fator_obj:
            st.divider()
            col_info, col_act1, col_act2 = st.columns([3, 1, 1])
            with col_info:
                st.markdown(f"**Selecionado:** ID {fator_id} — {fator_obj.codigo_artigo}")
            
            with col_act1:
                if st.button("📋 Duplicar", use_container_width=True, disabled=fator_obj.status == 'cancelado'):
                    modal_duplicacao(fator_obj, conn)
            
            with col_act2:
                if st.button("🚫 Inativar", type="primary", use_container_width=True, disabled=fator_obj.status == 'cancelado'):
                    modal_inativacao(fator_obj, conn)


# ---------------------------------------------------------------------------
# Página principal
# ---------------------------------------------------------------------------

def main() -> None:
    inject_global_css()
    render_page_header(PAGE_TITLE)
    render_env_banner()

    filtros = _render_filtros()

    # Carregamento do histórico (PRD Story 2.3 AC7-8)
    try:
        conn = get_sqlite_conn()
        fatores = listar_fatores(conn, **filtros)
    except Exception as exc:
        logger.error("ERRO_SQLITE_HISTORICO | erro=%s", str(exc))
        st.error(f"❌ Falha ao carregar o histórico: {exc}")
        return

    # Métricas rápidas
    total = len(fatores)
    ativos = sum(1 for f in fatores if f.status == "ativo")
    
    st.markdown(
        f"""
        <div style="display:flex;gap:24px;margin-bottom:16px;">
          <div><span style="font-size:12px;color:#43474f;">TOTAL</span><br>
               <span style="font-size:20px;font-weight:700;">{total}</span></div>
          <div><span style="font-size:12px;color:#43474f;">ATIVOS</span><br>
               <span style="font-size:20px;font-weight:700;color:#1f477b;">{ativos}</span></div>
          <div><span style="font-size:12px;color:#43474f;">INATIVOS</span><br>
               <span style="font-size:20px;font-weight:700;color:#737780;">{total - ativos}</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Tabela principal
    _render_tabela(fatores, conn)


if __name__ == "__main__":
    main()
