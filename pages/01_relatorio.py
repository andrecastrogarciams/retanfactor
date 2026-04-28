"""
Página: Relatório Operacional de Recurtimento
Story 1.1 — Consultar relatório operacional
Story 1.2 — Visualizar dados em AgGrid com interações analíticas
Story 1.3 — Calcular peso, densidade e desvio (via report_service)
Story 1.4 — Exportar PDF e Excel
Story 3.2 — Cache temporário com atualização forçada
"""
import io
import logging
from datetime import date, datetime
from typing import Optional

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import APP_ENV, ESTACAO, get_sqlite_conn, inject_global_css, render_env_banner, render_page_header
from models.report_row import CorDiferenca, ReportRow
from services.report_service import calcular_resumo, get_relatorio

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de UI
# ---------------------------------------------------------------------------

PAGE_TITLE = "Relatório de Recurtimento"
PAGE_ICON = "📊"

# Cores AgGrid para % diferença (PRD seção 4.5)
_COR_VERDE = "#d4edda"
_COR_AMARELO = "#fff3cd"
_COR_VERMELHO = "#f8d7da"
_TEXTO_VERDE = "#155724"
_TEXTO_AMARELO = "#856404"
_TEXTO_VERMELHO = "#721c24"

# Ordem e rótulos das colunas (PRD Story 1.2 AC3)
_COLUNAS_ORDEM = [
    "data_recurtimento",
    "artigo",
    "cor",
    "lote_fabricacao",
    "codigo_artigo",
    "m2",
    "peso_lote",
    "kg_m2",
    "kg_ft2",
    "fator_aplicado",
    "peso_calculado",
    "pct_diferenca",
]

_COLUNAS_LABELS = {
    "data_recurtimento": "Data Recurtimento",
    "artigo":            "Artigo",
    "cor":               "Cor",
    "lote_fabricacao":   "Lote Fabricação",
    "codigo_artigo":     "Cód. Artigo",
    "m2":                "m²",
    "peso_lote":         "Peso do Lote",
    "kg_m2":             "kg/m²",
    "kg_ft2":            "kg/ft²",
    "fator_aplicado":    "Fator Aplicado",
    "peso_calculado":    "Peso Calculado",
    "pct_diferenca":     "% Diferença",
}

_COLUNAS_NUMERICAS = {
    "m2", "peso_lote", "kg_m2", "kg_ft2",
    "fator_aplicado", "peso_calculado", "pct_diferenca",
}


# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rows_to_dataframe(rows: list[ReportRow]) -> pd.DataFrame:
    """Converte lista de ReportRow para DataFrame na ordem padrão das colunas."""
    data = []
    for row in rows:
        data.append({col: getattr(row, col, None) for col in _COLUNAS_ORDEM})
    df = pd.DataFrame(data, columns=_COLUNAS_ORDEM)
    df.rename(columns=_COLUNAS_LABELS, inplace=True)
    return df


def _build_aggrid_options(df: pd.DataFrame) -> dict:
    """Configura GridOptions com estilos, paginação e interações."""
    gb = GridOptionsBuilder.from_dataframe(df)

    # Configurações globais
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True,
        editable=False,
        wrapHeaderText=True,
        autoHeaderHeight=True,
    )

    # Seleção de linhas — apenas visual (PRD Story 1.2 AC2)
    gb.configure_selection(selection_mode="multiple", use_checkbox=False)

    # Paginação (PRD Story 1.2 AC6)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)

    # Barra lateral de colunas (ocultar/mostrar/reordenar — PRD Story 1.2 AC4)
    gb.configure_side_bar(columns_panel=True, filters_panel=False)

    # Estilo condicional da coluna % Diferença (PRD Story 1.3 AC8)
    pct_col = _COLUNAS_LABELS["pct_diferenca"]
    pct_style = JsCode(f"""
        function(params) {{
            if (params.value === null || params.value === undefined || params.value === '') {{
                return {{}};
            }}
            var abs = Math.abs(params.value);
            if (abs <= 5.0) {{
                return {{'backgroundColor': '{_COR_VERDE}', 'color': '{_TEXTO_VERDE}',
                         'fontWeight': 'bold'}};
            }} else if (abs <= 10.0) {{
                return {{'backgroundColor': '{_COR_AMARELO}', 'color': '{_TEXTO_AMARELO}',
                         'fontWeight': 'bold'}};
            }} else {{
                return {{'backgroundColor': '{_COR_VERMELHO}', 'color': '{_TEXTO_VERMELHO}',
                         'fontWeight': 'bold'}};
            }}
        }}
    """)

    # Formatação numérica com 2 casas decimais
    num_fmt = JsCode("function(params) { return params.value != null ? params.value.toFixed(2) : ''; }")

    for col_key, col_label in _COLUNAS_LABELS.items():
        if col_key == "pct_diferenca":
            gb.configure_column(
                col_label,
                cellStyle=pct_style,
                valueFormatter=num_fmt,
                type=["numericColumn"],
                width=130,
            )
        elif col_key in _COLUNAS_NUMERICAS:
            gb.configure_column(
                col_label,
                valueFormatter=num_fmt,
                type=["numericColumn"],
                width=120,
            )
        elif col_key == "data_recurtimento":
            gb.configure_column(col_label, width=150)
        elif col_key in ("artigo", "lote_fabricacao"):
            gb.configure_column(col_label, width=180)
        else:
            gb.configure_column(col_label, width=110)

    grid_options = gb.build()

    # Habilitar reordenação de colunas via drag
    grid_options["suppressMovableColumns"] = False

    # Story 4.2: altura de linha 36px e header cinza #f1f3f5
    grid_options["rowHeight"] = 36
    grid_options["headerHeight"] = 40

    return grid_options


def _exportar_excel(df: pd.DataFrame) -> bytes:
    """
    Exporta DataFrame para Excel com valores numéricos como número.
    (PRD Story 1.4 AC6)
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatório")

        wb = writer.book
        ws = writer.sheets["Relatório"]

        # Formatar colunas numéricas como número com 2 casas
        from openpyxl.styles import numbers as xl_numbers
        num_cols = {_COLUNAS_LABELS[k] for k in _COLUNAS_NUMERICAS}
        for col_idx, col in enumerate(df.columns, start=1):
            if col in num_cols:
                for row_idx in range(2, ws.max_row + 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    if cell.value is not None:
                        try:
                            cell.value = float(cell.value)
                            cell.number_format = "0.00"
                        except (TypeError, ValueError):
                            pass

        # Ajustar largura das colunas
        for col_cells in ws.columns:
            max_len = max(
                len(str(c.value)) if c.value else 0 for c in col_cells
            )
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 30)

    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Filtros — painel horizontal (Story 4.2 AC1)
# ---------------------------------------------------------------------------

def _render_filtros() -> dict:
    """Renderiza filtros em linha horizontal e retorna os valores selecionados."""
    hoje = date.today()
    primeiro_dia_mes = hoje.replace(day=1)

    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

    with col1:
        data_inicio = st.date_input("Data início", value=primeiro_dia_mes, format="DD/MM/YYYY")
    with col2:
        data_fim = st.date_input("Data fim", value=hoje, format="DD/MM/YYYY")
    with col3:
        lote = st.text_input("Lote de fabricação", value="").strip() or None
    with col4:
        artigo = st.text_input("Artigo", value="").strip() or None
    with col5:
        cor = st.text_input("Cor", value="").strip() or None

    return {
        "data_inicio": data_inicio.strftime("%Y-%m-%d"),
        "data_fim":    data_fim.strftime("%Y-%m-%d"),
        "lote":        lote,
        "artigo":      artigo,
        "cor":         cor,
    }


# ---------------------------------------------------------------------------
# Renderização principal
# ---------------------------------------------------------------------------

def main() -> None:
    inject_global_css()
    render_page_header(PAGE_TITLE)
    render_env_banner()

    filtros = _render_filtros()

    # Botão de atualização forçada (PRD Story 3.2 AC2)
    col_btn, col_status = st.columns([1, 5])
    with col_btn:
        force_refresh = st.button("🔄 Atualizar dados", type="secondary")

    rows: Optional[list[ReportRow]] = None
    erro_oracle: Optional[str] = None

    # Consulta
    with st.spinner("Consultando Oracle..."):
        try:
            conn = get_sqlite_conn()
            rows = get_relatorio(
                sqlite_conn=conn,
                force_refresh=force_refresh,
                **filtros,
            )

            with col_status:
                ts = datetime.now().strftime("%H:%M:%S")
                if force_refresh:
                    # PRD Story 3.2 AC8 — informar visualmente recarregamento
                    st.success(f"Dados atualizados com sucesso às {ts}.", icon="✅")
                else:
                    st.info(f"Dados carregados às {ts}.", icon="ℹ️")

            logger.info(
                "ACESSO | estacao=%s | linhas=%d | filtros=%s",
                ESTACAO, len(rows), filtros,
            )

        except Exception as exc:
            # PRD Story 1.1 AC5 e AC8 — erro Oracle: mensagem clara + log
            erro_oracle = str(exc)
            logger.error(
                "ERRO_ORACLE | estacao=%s | erro=%s | filtros=%s",
                ESTACAO, erro_oracle, filtros,
            )

    # Bloco de erro Oracle — não exibir dados antigos (PRD Story 1.1 AC5)
    if erro_oracle:
        st.error(
            f"❌ Falha na consulta ao Oracle. "
            f"Verifique a conexão e tente novamente.\n\n`{erro_oracle}`"
        )
        st.stop()

    if rows is None:
        st.stop()

    # ---------------------------------------------------------------------------
    # Resumo — card estilizado (Story 4.2 AC4)
    # ---------------------------------------------------------------------------
    resumo = calcular_resumo(rows)

    media_pct = (
        f"{resumo['media_pct_diferenca']:.2f}%"
        if resumo["media_pct_diferenca"] is not None else "—"
    )

    _METRIC_STYLE = (
        "flex:1;min-width:120px;"
        "display:flex;flex-direction:column;gap:4px;"
    )
    _LABEL_STYLE = (
        "font-size:12px;font-weight:600;color:#43474f;"
        "text-transform:uppercase;letter-spacing:0.04em;"
    )
    _VALUE_STYLE = "font-size:24px;font-weight:700;color:#1a1c1f;"

    st.markdown(
        f"""
        <div style="border:1px solid #dee2e6;padding:20px;border-radius:4px;
                    background:#ffffff;display:flex;gap:24px;
                    flex-wrap:wrap;margin-bottom:16px;">
          <div style="{_METRIC_STYLE}">
            <span style="{_LABEL_STYLE}">Total de linhas</span>
            <span style="{_VALUE_STYLE}">{resumo['total_linhas']}</span>
          </div>
          <div style="{_METRIC_STYLE}">
            <span style="{_LABEL_STYLE}">Média % Diferença</span>
            <span style="{_VALUE_STYLE}">{media_pct}</span>
          </div>
          <div style="{_METRIC_STYLE}">
            <span style="{_LABEL_STYLE}">Verde ≤5%</span>
            <span style="{_VALUE_STYLE};color:#28a745;">{resumo['total_verde']}</span>
          </div>
          <div style="{_METRIC_STYLE}">
            <span style="{_LABEL_STYLE}">Amarelo 5–10%</span>
            <span style="{_VALUE_STYLE};color:#856404;">{resumo['total_amarelo']}</span>
          </div>
          <div style="{_METRIC_STYLE}">
            <span style="{_LABEL_STYLE}">Vermelho &gt;10%</span>
            <span style="{_VALUE_STYLE};color:#dc3545;">{resumo['total_vermelho']}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------------------
    # Tabela AgGrid (PRD Story 1.2)
    # ---------------------------------------------------------------------------
    if not rows:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    df = _rows_to_dataframe(rows)
    grid_options = _build_aggrid_options(df)

    try:
        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            allow_unsafe_jscode=True,
            theme="streamlit",
            height=500,
            fit_columns_on_grid_load=False,
            enable_enterprise_modules=False,
        )
        # PRD Story 1.2 AC7 — indicação de carregamento bem-sucedido já exibida acima
    except Exception as exc:
        # PRD Story 1.2 AC8 — falha de renderização
        logger.error("ERRO_AGGRID | estacao=%s | erro=%s", ESTACAO, str(exc))
        st.error(f"❌ Erro ao renderizar a tabela. Tente recarregar a página.\n\n`{exc}`")
        return

    st.divider()

    # ---------------------------------------------------------------------------
    # Exportações (PRD Story 1.4 | Story 4.2 AC5)
    # PDF = primário, Excel = secundário
    # ---------------------------------------------------------------------------
    st.markdown(
        "<p style='font-size:14px;font-weight:600;color:#1a1c1f;margin-bottom:4px;'>"
        "Exportar</p>"
        "<p style='font-size:12px;color:#43474f;margin-bottom:12px;'>"
        "A exportação usa as <b>linhas filtradas</b> e respeita a "
        "<b>visão atual das colunas</b>.</p>",
        unsafe_allow_html=True,
    )

    col_pdf, col_excel, _ = st.columns([1, 1, 4])

    # PDF primário (PRD Story 1.4 AC3-5 | Story 4.2 AC5)
    with col_pdf:
        pdf_desabilitado = APP_ENV != "producao"
        if pdf_desabilitado:
            st.button("📄 Exportar PDF", disabled=True,
                      help="PDF desabilitado em ambiente de homologação.")
        else:
            if st.button("📄 Exportar PDF", type="primary"):
                try:
                    from services.export_service import exportar_pdf
                    pdf_bytes = exportar_pdf(
                        rows=rows,
                        filtros=filtros,
                        resumo=resumo,
                        estacao=ESTACAO,
                    )
                    nome_pdf = (
                        f"relatorio_recurtimento_"
                        f"{filtros['data_inicio']}_a_{filtros['data_fim']}.pdf"
                    )
                    st.download_button(
                        label="⬇️ Baixar PDF",
                        data=pdf_bytes,
                        file_name=nome_pdf,
                        mime="application/pdf",
                    )
                except Exception as exc:
                    logger.error("ERRO_PDF | estacao=%s | erro=%s", ESTACAO, str(exc))
                    st.error(f"❌ Falha ao gerar o PDF.\n\n`{exc}`")

    # Excel secundário (PRD Story 1.4 AC6 | Story 4.2 AC5)
    with col_excel:
        try:
            excel_bytes = _exportar_excel(df)
            nome_arquivo = (
                f"relatorio_recurtimento_"
                f"{filtros['data_inicio']}_a_{filtros['data_fim']}.xlsx"
            )
            st.download_button(
                label="📥 Exportar Excel",
                data=excel_bytes,
                file_name=nome_arquivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
            )
        except Exception as exc:
            # PRD Story 1.4 AC7
            logger.error("ERRO_EXCEL | estacao=%s | erro=%s", ESTACAO, str(exc))
            st.error(f"❌ Falha ao gerar o arquivo Excel.\n\n`{exc}`")


if __name__ == "__main__":
    main()
