"""
Testes para funções auxiliares de pages/02_cadastro.py.
Cobrem: validar_formulario() e construir_fator_artigo() — funções puras.
A lógica de persistência é coberta por test_factor_service.py.
"""
import sys
import importlib
import importlib.util
import unittest.mock as mock
from datetime import date
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="module")
def page():
    st_mock = mock.MagicMock()
    st_mock.cache_data = lambda *a, **kw: (lambda f: f)
    st_mock.cache_resource = lambda f: f
    sys.modules["streamlit"] = st_mock
    sys.modules["st_aggrid"] = mock.MagicMock()

    spec = importlib.util.spec_from_file_location(
        "cadastro_page",
        Path(__file__).parent.parent.parent / "pages" / "02_cadastro.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# validar_formulario
# ---------------------------------------------------------------------------

class TestValidarFormulario:

    def _v(self, page, **kwargs) -> dict[str, str]:
        defaults = dict(
            codigo_artigo="ART001",
            fator=1.25,
            data_inicio=date(2026, 1, 1),
            data_fim=None,
        )
        defaults.update(kwargs)
        # Removido descricao_artigo pois agora é read-only e não validado
        if "descricao_artigo" in defaults:
            del defaults["descricao_artigo"]
        return page.validar_formulario(**defaults)

    def test_formulario_valido_retorna_vazio(self, page):
        assert self._v(page) == {}

    def test_vigencia_aberta_e_valida(self, page):
        assert self._v(page, data_fim=None) == {}

    def test_vigencia_fechada_valida(self, page):
        assert self._v(page, data_fim=date(2026, 6, 30)) == {}

    # Artigo
    def test_codigo_artigo_vazio(self, page):
        erros = self._v(page, codigo_artigo="")
        assert "codigo_artigo" in erros
        assert "artigo" in erros["codigo_artigo"].lower()

    def test_codigo_artigo_espacos(self, page):
        erros = self._v(page, codigo_artigo="   ")
        assert "codigo_artigo" in erros
        assert "artigo" in erros["codigo_artigo"].lower()

    # Fator
    def test_fator_none(self, page):
        erros = self._v(page, fator=None)
        assert "fator" in erros
        assert "fator" in erros["fator"].lower()

    def test_fator_zero(self, page):
        erros = self._v(page, fator=0.0)
        assert "fator" in erros
        assert "maior que zero" in erros["fator"].lower()

    def test_fator_negativo(self, page):
        erros = self._v(page, fator=-1.0)
        assert "fator" in erros
        assert "maior que zero" in erros["fator"].lower()

    def test_fator_muito_pequeno_positivo_valido(self, page):
        assert self._v(page, fator=0.001) == {}

    # Data início
    def test_data_inicio_none(self, page):
        erros = self._v(page, data_inicio=None)
        assert "data_inicio" in erros
        assert "início" in erros["data_inicio"].lower()

    # Data fim vs data início
    def test_data_fim_igual_a_inicio(self, page):
        erros = self._v(
            page,
            data_inicio=date(2026, 6, 1),
            data_fim=date(2026, 6, 1),
        )
        assert "data_fim" in erros
        assert "posterior" in erros["data_fim"].lower()

    def test_data_fim_anterior_a_inicio(self, page):
        erros = self._v(
            page,
            data_inicio=date(2026, 6, 1),
            data_fim=date(2026, 1, 1),
        )
        assert "data_fim" in erros
        assert "posterior" in erros["data_fim"].lower()

    def test_data_fim_posterior_e_valida(self, page):
        assert self._v(
            page,
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 12, 31),
        ) == {}

    # Múltiplos erros simultâneos
    def test_acumula_multiplos_erros(self, page):
        erros = self._v(page, codigo_artigo="", fator=None, data_inicio=None)
        assert len(erros) >= 3
        assert "codigo_artigo" in erros
        assert "fator" in erros
        assert "data_inicio" in erros


# ---------------------------------------------------------------------------
# construir_fator_artigo
# ---------------------------------------------------------------------------

class TestConstruirFatorArtigo:

    def test_campos_obrigatorios(self, page):
        fa = page.construir_fator_artigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Teste",
            fator=1.25,
            data_inicio=date(2026, 1, 1),
            data_fim=None,
            observacao="",
        )
        assert fa.codigo_artigo == "ART001"
        assert fa.descricao_artigo == "Artigo Teste"
        assert fa.fator == pytest.approx(1.25)
        assert fa.data_inicio_vigencia == "2026-01-01"
        assert fa.data_fim_vigencia is None
        assert fa.observacao is None

    def test_vigencia_fechada(self, page):
        fa = page.construir_fator_artigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Teste",
            fator=1.25,
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 6, 30),
            observacao="",
        )
        assert fa.data_fim_vigencia == "2026-06-30"

    def test_observacao_preenchida(self, page):
        fa = page.construir_fator_artigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Teste",
            fator=1.25,
            data_inicio=date(2026, 1, 1),
            data_fim=None,
            observacao="Revisão de Março",
        )
        assert fa.observacao == "Revisão de Março"

    def test_observacao_apenas_espacos_vira_none(self, page):
        fa = page.construir_fator_artigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Teste",
            fator=1.25,
            data_inicio=date(2026, 1, 1),
            data_fim=None,
            observacao="   ",
        )
        assert fa.observacao is None

    def test_codigo_e_descricao_com_espacos_sao_limpos(self, page):
        fa = page.construir_fator_artigo(
            codigo_artigo="  ART001  ",
            descricao_artigo="  Artigo Teste  ",
            fator=1.25,
            data_inicio=date(2026, 1, 1),
            data_fim=None,
            observacao="",
        )
        assert fa.codigo_artigo == "ART001"
        assert fa.descricao_artigo == "Artigo Teste"

    def test_data_formatada_iso8601(self, page):
        fa = page.construir_fator_artigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Teste",
            fator=1.0,
            data_inicio=date(2026, 3, 5),
            data_fim=date(2026, 9, 15),
            observacao="",
        )
        assert fa.data_inicio_vigencia == "2026-03-05"
        assert fa.data_fim_vigencia == "2026-09-15"

    def test_status_padrao_ativo(self, page):
        fa = page.construir_fator_artigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Teste",
            fator=1.0,
            data_inicio=date(2026, 1, 1),
            data_fim=None,
            observacao="",
        )
        assert fa.status == "ativo"
