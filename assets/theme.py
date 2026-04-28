"""
Design system — Industrial Precision.
Funções reutilizáveis de injeção de CSS e renderização de header.
"""
from pathlib import Path

import streamlit as st

_CSS_PATH = Path(__file__).parent / "styles.css"
_LOGO_PATH = Path(__file__).parent.parent / "docs" / "logo" / "logo_viposa.png"


def inject_global_css() -> None:
    """Injeta o CSS do design system em todas as páginas."""
    css = _CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_page_header(title: str) -> None:
    """
    Renderiza header padrão: logo Viposa à esquerda, título à direita.
    Deve ser chamado após inject_global_css().
    """
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        if _LOGO_PATH.exists():
            st.image(str(_LOGO_PATH), width=120)
    with col_title:
        st.markdown(
            f"<h1 style='"
            f"font-family: Inter, sans-serif;"
            f"font-size: 24px;"
            f"font-weight: 600;"
            f"color: #1a1c1f;"
            f"margin: 0;"
            f"padding-top: 8px;"
            f"'>{title}</h1>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<hr style='border:none;border-top:1px solid #dee2e6;margin:8px 0 16px 0;'/>",
        unsafe_allow_html=True,
    )
