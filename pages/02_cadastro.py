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

PAGE_TITLE = "Cadastro de Fatores"
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
# Validação de formulário — função pura, testável
# ---------------------------------------------------------------------------

def validar_formulario(
    codigo_artigo: str,
    descricao_artigo: str,
    fator: Optional[float],
    data_inicio: Optional[date],
    data_fim: Optional[date],
) -> list[str]:
    """
    Valida os campos do formulário antes de acionar o serviço.
    Retorna lista de mensagens de erro (vazia = formulário válido).
    """
    erros = []

    if not codigo_artigo or not codigo_artigo.strip():
        erros.append("Selecione um artigo.")

    if not descricao_artigo or not descricao_artigo.strip():
        erros.append("Descrição do artigo não pode estar vazia.")

    if fator is None:
        erros.append("Informe o fator.")
    elif fator <= 0:
        erros.append("O fator deve ser maior que zero. (PRD Story 2.1 AC4)")

    if data_inicio is None:
        erros.append("Data de início da vigência é obrigatória.")

    if data_inicio and data_fim and data_fim <= data_inicio:
        erros.append("Data de fim da vigência deve ser posterior à data de início.")

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


# ---------------------------------------------------------------------------
# Renderização do formulário
# ---------------------------------------------------------------------------

def _render_seletor_artigo(artigos: list[dict]) -> tuple[str, str]:
    """
    Renderiza seletor de artigo.
    Se Oracle disponível: selectbox pesquisável com lista real.
    Se Oracle indisponível: campos de texto manuais com aviso.
    """
    if artigos:
        opcoes = {
            f"{a['codigo_artigo']} — {a['descricao_artigo']}": a
            for a in artigos
        }
        selecao = st.selectbox(
            "Artigo *",
            options=list(opcoes.keys()),
            index=None,
            placeholder="Selecione ou pesquise um artigo...",
            help="Lista carregada da view Oracle USU_VBI_ARTIGOS_SEMI_NOA",
        )
        if selecao:
            artigo = opcoes[selecao]
            return artigo["codigo_artigo"], artigo["descricao_artigo"]
        return "", ""
    else:
        st.warning(
            "⚠️ Lista de artigos Oracle indisponível. "
            "Preencha o código e a descrição manualmente.",
            icon="⚠️",
        )
        codigo = st.text_input("Código do artigo *", placeholder="ex: ART001")
        descricao = st.text_input("Descrição do artigo *", placeholder="ex: Napa Bovina")
        return codigo.strip(), descricao.strip()


def _limpar_formulario() -> None:
    """Limpa o estado do formulário após salvar com sucesso."""
    for key in [
        "form_fator", "form_data_inicio", "form_data_fim",
        "form_observacao", "form_artigo",
    ]:
        if key in st.session_state:
            del st.session_state[key]


# ---------------------------------------------------------------------------
# Página principal
# ---------------------------------------------------------------------------

def main() -> None:
    inject_global_css()
    render_page_header(PAGE_TITLE)
    render_env_banner()
    st.markdown(
        "Cadastre um novo fator de cálculo por código do artigo. "
        "A vigência define o período em que o fator será aplicado no relatório."
    )

    artigos = _carregar_artigos()

    st.divider()

    # ------------------------------------------------------------------
    # Formulário
    # ------------------------------------------------------------------
    with st.form("form_cadastro_fator", clear_on_submit=False):
        st.subheader("Dados do Fator")

        # Artigo (PRD Story 2.1 AC2-3)
        codigo_artigo, descricao_artigo = _render_seletor_artigo(artigos)

        st.divider()

        # Fator (PRD Story 2.1 AC4)
        col_fator, col_vazio = st.columns([1, 2])
        with col_fator:
            fator = st.number_input(
                "Fator *",
                min_value=0.0001,
                max_value=99.9999,
                value=None,
                step=0.0001,
                format="%.4f",
                placeholder="ex: 1.2500",
                help="Deve ser maior que zero. Usado na fórmula: m² × 10,764 × fator × 0,092903",
            )

        st.divider()

        # Vigência (PRD Story 2.1 AC1, AC5)
        st.markdown("**Vigência**")
        col_inicio, col_fim = st.columns(2)
        with col_inicio:
            data_inicio = st.date_input(
                "Data início *",
                value=None,
                format="DD/MM/YYYY",
                help="Obrigatório. Primeiro dia de validade do fator.",
            )
        with col_fim:
            data_fim = st.date_input(
                "Data fim",
                value=None,
                format="DD/MM/YYYY",
                help="Opcional. Deixe em branco para vigência em aberto.",
            )

        # Observação (PRD Story 2.1 AC1 — campo disponível)
        observacao = st.text_area(
            "Observação",
            value="",
            max_chars=500,
            placeholder="Informações adicionais sobre este fator (opcional).",
            height=80,
        )

        st.divider()

        # Botão de submissão
        submitted = st.form_submit_button(
            "💾 Salvar fator",
            type="primary",
            use_container_width=True,
        )

    # ------------------------------------------------------------------
    # Processamento após submissão
    # ------------------------------------------------------------------
    if not submitted:
        return

    # Converter date_input (pode retornar date ou None)
    data_inicio_val = data_inicio if isinstance(data_inicio, date) else None
    data_fim_val = data_fim if isinstance(data_fim, date) else None

    # Validação de formulário (PRD Story 2.2)
    erros = validar_formulario(
        codigo_artigo=codigo_artigo,
        descricao_artigo=descricao_artigo,
        fator=fator,
        data_inicio=data_inicio_val,
        data_fim=data_fim_val,
    )

    if erros:
        for erro in erros:
            st.error(f"❌ {erro}")
        return

    # Persistência (PRD Story 2.1 AC6-8)
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

        vigencia_txt = (
            f"{data_inicio_val.strftime('%d/%m/%Y')} → "
            + (data_fim_val.strftime("%d/%m/%Y") if data_fim_val else "em aberto")
        )
        st.success(
            f"✅ Fator cadastrado com sucesso!\n\n"
            f"**ID:** {new_id} | **Artigo:** {codigo_artigo} | "
            f"**Fator:** {fator:.4f} | **Vigência:** {vigencia_txt}",
        )
        st.info(
            "O relatório já reflete este fator. "
            "Consulte o **Histórico de Fatores** para visualizar o registro.",
            icon="ℹ️",
        )

    except ValueError as exc:
        # Sobreposição de vigência ou validação de negócio (PRD Story 2.2 AC3)
        st.error(f"❌ {exc}")
        logger.warning(
            "CADASTRO_REJEITADO | estacao=%s | artigo=%s | erro=%s",
            ESTACAO, codigo_artigo, str(exc),
        )

    except Exception as exc:
        st.error(
            f"❌ Erro inesperado ao salvar o fator. Tente novamente.\n\n`{exc}`"
        )
        logger.error(
            "ERRO_CADASTRO | estacao=%s | artigo=%s | erro=%s",
            ESTACAO, codigo_artigo, str(exc),
        )


if __name__ == "__main__":
    main()
