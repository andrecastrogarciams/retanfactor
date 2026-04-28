"""
Testes para assets/theme.py.
inject_global_css() e render_page_header() são funções que chamam st.markdown/st.image —
verificamos: leitura correta do CSS, presença de variáveis-chave e assinatura da API.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from assets.theme import _CSS_PATH, _LOGO_PATH, inject_global_css, render_page_header


# ---------------------------------------------------------------------------
# inject_global_css
# ---------------------------------------------------------------------------

class TestInjectGlobalCss:
    def test_css_file_exists(self):
        assert _CSS_PATH.exists(), f"styles.css não encontrado em {_CSS_PATH}"

    def test_css_contains_design_tokens(self):
        css = _CSS_PATH.read_text(encoding="utf-8")
        for token in (
            "--color-primary: #001e40",
            "--color-background: #f9f9fe",
            "--color-status-green: #28a745",
            "--color-status-yellow: #ffc107",
            "--color-status-red: #dc3545",
            "--radius-card: 4px",
            "Inter",
        ):
            assert token in css, f"Token ausente no CSS: {token}"

    def test_css_contains_button_styles(self):
        css = _CSS_PATH.read_text(encoding="utf-8")
        assert "background-color: var(--color-primary)" in css
        assert "border: 1px solid var(--color-primary)" in css

    def test_css_contains_aggrid_styles(self):
        css = _CSS_PATH.read_text(encoding="utf-8")
        assert ".ag-theme-streamlit .ag-header" in css
        assert "#f1f3f5" in css

    @patch("assets.theme.st")
    def test_inject_calls_st_markdown(self, mock_st):
        inject_global_css()
        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args
        assert "<style>" in args[0]
        assert kwargs.get("unsafe_allow_html") is True


# ---------------------------------------------------------------------------
# render_page_header
# ---------------------------------------------------------------------------

class TestRenderPageHeader:
    @patch("assets.theme.st")
    def test_renders_title_text(self, mock_st):
        mock_col = MagicMock()
        mock_col.__enter__ = lambda s: s
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = (mock_col, mock_col)

        render_page_header("Meu Título")

        all_markdown_calls = mock_st.markdown.call_args_list
        rendered_html = " ".join(str(c) for c in all_markdown_calls)
        assert "Meu Título" in rendered_html

    @patch("assets.theme.st")
    def test_renders_divider(self, mock_st):
        mock_col = MagicMock()
        mock_col.__enter__ = lambda s: s
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = (mock_col, mock_col)

        render_page_header("X")

        all_calls = " ".join(str(c) for c in mock_st.markdown.call_args_list)
        assert "<hr" in all_calls

    @patch("assets.theme.st")
    def test_uses_two_columns(self, mock_st):
        mock_col = MagicMock()
        mock_col.__enter__ = lambda s: s
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_st.columns.return_value = (mock_col, mock_col)

        render_page_header("Y")

        mock_st.columns.assert_called_once_with([1, 5])

    def test_logo_path_definition(self):
        assert _LOGO_PATH.name == "logo_viposa.png"
        assert "docs" in str(_LOGO_PATH)
        assert "logo" in str(_LOGO_PATH)
