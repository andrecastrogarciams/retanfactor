"""
Página: Cadastro de Fatores
Story 2.1 — Cadastrar novo fator com vigência
Story 2.2 — Bloquear sobreposição de vigência
"""
import logging
from datetime import date, datetime
from typing import Optional

import streamlit as st

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ESTACAO, get_sqlite_conn, inject_global_css, render_env_banner, render_page_header
from models.factor import FatorArtigo
from services.factor_service import criar_fator

logger = logging.getLogger(__name__)

PAGE_TITLE = "Cadastro de Fator de Recurtimento"
PAGE_ICON = "📝"

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")


# ---------------------------------------------------------------------------
# Carregamento de artigos Oracle — cacheado por 5 minutos
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner="Carregando lista de artigos...")
def _carregar_artigos() -> list[dict]:
    """
    Busca lista de artigos da view Oracle USU_VBI_ARTIGOS_SEMI_NOA.
    Retorna lista vazia com aviso se Oracle estiver indisponível.
    (PRD Story 2.1 AC2)
    """
    try:
        from repositories.oracle_repo import fetch_artigos
        return fetch_artigos()
    except Exception as exc:
        logger.warning("AVISO_ORACLE_ARTIGOS | erro=%s", str(exc))
        return []


# ---------------------------------------------------------------------------
# Helpers de UI e Validação
# ---------------------------------------------------------------------------

def _render_erro_inline(campo: str):
    """Exibe mensagem de erro abaixo do campo se existir no session_state."""
    erros = st.session_state.get("form_errors", {})
    if campo in erros:
        st.markdown(
            f'<p style="color:#dc3545;font-size:12px;margin-top:-15px;margin-bottom:15px;">'
            f'⚠ {erros[campo]}</p>',
            unsafe_allow_html=True
        )


def validar_formulario(
    codigo_artigo: str,
    fator: Optional[float],
    data_inicio: Optional[date],
    data_fim: Optional[date],
) -> dict[str, str]:
    """
    Valida os campos do formulário e retorna dicionário de erros por campo.
    """
    erros = {}

    if not codigo_artigo or not codigo_artigo.strip():
        erros["codigo_artigo"] = "Selecione um artigo."

    if fator is None:
        erros["fator"] = "Informe o fator."
    elif fator <= 0:
        erros["fator"] = "O fator deve ser maior que zero."

    if data_inicio is None:
        erros["data_inicio"] = "Data de início é obrigatória."

    if data_inicio and data_fim and data_fim <= data_inicio:
        erros["data_fim"] = "Deve ser posterior à data de início."

    return erros


def construir_fator_artigo(
    codigo_artigo: str,
    descricao_artigo: str,
    fator: float,
    data_inicio: date,
    data_fim: Optional[date],
    observacao: str,
) -> FatorArtigo:
    """Constrói FatorArtigo a partir dos inputs do formulário."""
    return FatorArtigo(
        codigo_artigo=codigo_artigo.strip(),
        descricao_artigo=descricao_artigo.strip(),
        fator=fator,
        data_inicio_vigencia=data_inicio.strftime("%Y-%m-%d"),
        data_fim_vigencia=data_fim.strftime("%Y-%m-%d") if data_fim else None,
        observacao=observacao.strip() if observacao and observacao.strip() else None,
    )


def _render_seletor_artigo(artigos: list[dict]) -> tuple[str, str]:
    """
    Renderiza seletor de artigo (Story 4.3 AC3).
    """
    if artigos:
        opcoes = {
            f"{a['codigo_artigo']} — {a['descricao_artigo']}": a
            for a in artigos
        }
        selecao = st.selectbox(
            "Código do artigo",
            options=list(opcoes.keys()),
            index=None,
            placeholder="Selecione ou pesquise...",
            key="f_codigo_artigo_sel",
        )
        if selecao:
            artigo = opcoes[selecao]
            return artigo["codigo_artigo"], artigo["descricao_artigo"]
        return "", ""
    else:
        st.warning(
            "⚠️ Lista de artigos Oracle indisponível.",
            icon="⚠️",
        )
        codigo = st.text_input("Código do artigo", placeholder="ex: ART001", key="f_codigo_manual")
        descricao = st.text_input("Descrição do artigo", placeholder="ex: Napa Bovina", key="f_desc_manual")
        return codigo.strip(), descricao.strip()


def _limpar_formulario() -> None:
    """Limpa o estado do formulário e erros."""
    chaves = [
        "f_codigo_artigo_sel", "f_codigo_manual", "f_desc_manual",
        "f_fator", "f_data_inicio", "f_data_fim", "f_observacao",
        "form_errors"
    ]
    for key in chaves:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# ---------------------------------------------------------------------------
# Página principal
# ---------------------------------------------------------------------------

def main() -> None:
    inject_global_css()
    render_page_header(PAGE_TITLE)
    render_env_banner()

    artigos = _carregar_artigos()

    # Centralização do formulário (Story 4.3 AC2)
    _, col_form, _ = st.columns([1, 2, 1])

    with col_form:
        # st.form já possui o estilo de card via styles.css [data-testid="stForm"]
        with st.form("form_cadastro_fator", clear_on_submit=False):
            
            # Artigo (AC 3)
            codigo_artigo, descricao_artigo = _render_seletor_artigo(artigos)
            _render_erro_inline("codigo_artigo")

            # Descrição (AC 4 — read-only)
            st.text_input(
                "Descrição do artigo",
                value=descricao_artigo,
                disabled=True,
                help="Preenchimento automático baseado no código selecionado.",
            )

            # Fator (AC 3)
            fator = st.number_input(
                "Fator",
                min_value=0.001,
                max_value=99.999,
                value=None,
                step=0.001,
                format="%.3f",
                placeholder="ex: 1.250",
                key="f_fator",
            )
            _render_erro_inline("fator")

            # Vigência (AC 3)
            col_ini, col_fim = st.columns(2)
            with col_ini:
                data_inicio = st.date_input(
                    "Data início vigência",
                    value=None,
                    format="DD/MM/YYYY",
                    key="f_data_inicio",
                )
                _render_erro_inline("data_inicio")
            with col_fim:
                data_fim = st.date_input(
                    "Data fim vigência (Opcional)",
                    value=None,
                    format="DD/MM/YYYY",
                    key="f_data_fim",
                )
                _render_erro_inline("data_fim")

            # Observação (AC 3)
            observacao = st.text_area(
                "Observação",
                value="",
                max_chars=500,
                placeholder="Informações adicionais (opcional).",
                height=100,
                key="f_observacao",
            )

            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

            # Botões (AC 5 e 6)
            col_cancel, col_save = st.columns(2)
            with col_cancel:
                # O style secundário é aplicado via CSS global para botões não-primários
                btn_cancel = st.form_submit_button("Cancelar/Limpar", use_container_width=True)
            with col_save:
                btn_save = st.form_submit_button("💾 Salvar Fator", type="primary", use_container_width=True)

    # ------------------------------------------------------------------
    # Processamento
    # ------------------------------------------------------------------
    if btn_cancel:
        _limpar_formulario()

    if not btn_save:
        return

    # Converter date_input
    data_inicio_val = data_inicio if isinstance(data_inicio, date) else None
    data_fim_val = data_fim if isinstance(data_fim, date) else None

    # Validação (PRD Story 2.2 | Story 4.3 AC7)
    erros = validar_formulario(
        codigo_artigo=codigo_artigo,
        fator=fator,
        data_inicio=data_inicio_val,
        data_fim=data_fim_val,
    )

    if erros:
        st.session_state["form_errors"] = erros
        st.rerun()

    # Se chegou aqui, remove erros antigos
    if "form_errors" in st.session_state:
        del st.session_state["form_errors"]

    # Persistência
    novo_fator = construir_fator_artigo(
        codigo_artigo=codigo_artigo,
        descricao_artigo=descricao_artigo,
        fator=fator,
        data_inicio=data_inicio_val,
        data_fim=data_fim_val,
        observacao=observacao,
    )

    try:
        conn = get_sqlite_conn()
        new_id = criar_fator(conn, novo_fator, ESTACAO)

        st.success(f"✅ Fator cadastrado com sucesso! ID: {new_id}")
        st.balloons()
        # Não limpamos automaticamente para o usuário ver o sucesso, 
        # mas ele pode clicar em Cancelar/Limpar se quiser novo cadastro.

    except ValueError as exc:
        # Sobreposição de vigência
        st.session_state["form_errors"] = {"data_inicio": str(exc)}
        st.rerun()

    except Exception as exc:
        st.error(f"❌ Erro inesperado: {exc}")
        logger.error("ERRO_CADASTRO | erro=%s", str(exc))


if __name__ == "__main__":
    main()
