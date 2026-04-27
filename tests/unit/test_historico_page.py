"""
Testes para funções auxiliares de pages/03_historico.py.
Cobrem funções puras: formatar_status, formatar_vigencia,
fatores_para_dataframe, validar_duplicacao, validar_cancelamento.
"""
import sys
import importlib
import importlib.util
import unittest.mock as mock
from datetime import date
from typing import Optional

import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent)
                if False else  # noqa — workaround para type checker
                str(__import__("pathlib").Path(__file__).parent.parent.parent))

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.factor import FatorArtigo


@pytest.fixture(scope="module")
def page():
    st_mock = mock.MagicMock()
    st_mock.cache_data = lambda *a, **kw: (lambda f: f)
    st_mock.cache_resource = lambda f: f
    sys.modules["streamlit"] = st_mock
    sys.modules["st_aggrid"] = mock.MagicMock()

    spec = importlib.util.spec_from_file_location(
        "historico_page",
        Path(__file__).parent.parent.parent / "pages" / "03_historico.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fator(
    id=1,
    codigo="ART001",
    descricao="Artigo Teste",
    fator=1.25,
    inicio="2026-01-01",
    fim=None,
    status="ativo",
    motivo=None,
    created_at="2026-01-01 09:00:00",
    cancelled_at=None,
) -> FatorArtigo:
    return FatorArtigo(
        id=id,
        codigo_artigo=codigo,
        descricao_artigo=descricao,
        fator=fator,
        data_inicio_vigencia=inicio,
        data_fim_vigencia=fim,
        status=status,
        motivo_cancelamento=motivo,
        created_at=created_at,
        cancelled_at=cancelled_at,
    )


# ---------------------------------------------------------------------------
# formatar_status
# ---------------------------------------------------------------------------

class TestFormatarStatus:
    def test_ativo_aberto(self, page):
        f = _fator(fim=None)
        assert "Ativo" in page.formatar_status(f)
        assert "aberto" in page.formatar_status(f)

    def test_ativo_com_fim(self, page):
        f = _fator(fim="2026-12-31")
        resultado = page.formatar_status(f)
        assert "Ativo" in resultado
        assert "aberto" not in resultado

    def test_cancelado(self, page):
        f = _fator(status="cancelado", motivo="Revisado")
        assert "Cancelado" in page.formatar_status(f)

    def test_ativo_tem_indicador_verde(self, page):
        assert "🟢" in page.formatar_status(_fator())

    def test_cancelado_tem_indicador_vermelho(self, page):
        assert "🔴" in page.formatar_status(_fator(status="cancelado"))


# ---------------------------------------------------------------------------
# formatar_vigencia
# ---------------------------------------------------------------------------

class TestFormatarVigencia:
    def test_vigencia_fechada(self, page):
        f = _fator(inicio="2026-01-01", fim="2026-06-30")
        resultado = page.formatar_vigencia(f)
        assert "2026-01-01" in resultado
        assert "2026-06-30" in resultado

    def test_vigencia_aberta(self, page):
        f = _fator(inicio="2026-01-01", fim=None)
        resultado = page.formatar_vigencia(f)
        assert "2026-01-01" in resultado
        assert "em aberto" in resultado

    def test_formato_seta(self, page):
        f = _fator(inicio="2026-01-01", fim="2026-06-30")
        assert "→" in page.formatar_vigencia(f)


# ---------------------------------------------------------------------------
# fatores_para_dataframe
# ---------------------------------------------------------------------------

class TestFatoresParaDataframe:
    def test_lista_vazia_retorna_dataframe_vazio(self, page):
        df = page.fatores_para_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert len(df.columns) > 0

    def test_quantidade_de_linhas(self, page):
        fatores = [_fator(id=1), _fator(id=2, codigo="ART002")]
        df = page.fatores_para_dataframe(fatores)
        assert len(df) == 2

    def test_colunas_com_labels(self, page):
        df = page.fatores_para_dataframe([_fator()])
        assert "ID" in df.columns
        assert "Status" in df.columns
        assert "Fator" in df.columns

    def test_status_display_formatado(self, page):
        f_ativo = _fator(status="ativo")
        f_canc = _fator(id=2, status="cancelado")
        df = page.fatores_para_dataframe([f_ativo, f_canc])
        statuses = df["Status"].tolist()
        assert any("Ativo" in s for s in statuses)
        assert any("Cancelado" in s for s in statuses)

    def test_vigencia_aberta_exibida(self, page):
        f = _fator(fim=None)
        df = page.fatores_para_dataframe([f])
        fim_val = df["Fim Vigência"].iloc[0]
        assert fim_val == "em aberto"

    def test_vigencia_fechada_exibida(self, page):
        f = _fator(fim="2026-12-31")
        df = page.fatores_para_dataframe([f])
        assert df["Fim Vigência"].iloc[0] == "2026-12-31"

    def test_observacao_none_vira_string_vazia(self, page):
        f = _fator()
        f.observacao = None
        df = page.fatores_para_dataframe([f])
        assert df["Observação"].iloc[0] == ""

    def test_motivo_none_vira_string_vazia(self, page):
        f = _fator()
        df = page.fatores_para_dataframe([f])
        assert df["Motivo Cancelamento"].iloc[0] == ""


# ---------------------------------------------------------------------------
# validar_duplicacao
# ---------------------------------------------------------------------------

class TestValidarDuplicacao:
    def _v(self, page, **kwargs) -> list[str]:
        defaults = dict(
            fator_id=1,
            data_inicio_nova=date(2026, 7, 1),
            data_fim_nova=None,
            fator_origem=_fator(),
        )
        defaults.update(kwargs)
        return page.validar_duplicacao(**defaults)

    def test_valido(self, page):
        assert self._v(page) == []

    def test_valido_com_fim(self, page):
        assert self._v(page, data_fim_nova=date(2026, 12, 31)) == []

    def test_fator_id_none(self, page):
        erros = self._v(page, fator_id=None, fator_origem=None)
        assert len(erros) >= 1
        assert any("Selecione" in e for e in erros)

    def test_fator_origem_none(self, page):
        erros = self._v(page, fator_id=99, fator_origem=None)
        assert any("não encontrado" in e for e in erros)

    def test_origem_cancelada(self, page):
        f_canc = _fator(status="cancelado")
        erros = self._v(page, fator_origem=f_canc)
        assert any("cancelado" in e.lower() for e in erros)

    def test_data_inicio_none(self, page):
        erros = self._v(page, data_inicio_nova=None)
        assert any("obrigatória" in e or "início" in e for e in erros)

    def test_data_fim_igual_inicio(self, page):
        erros = self._v(
            page,
            data_inicio_nova=date(2026, 7, 1),
            data_fim_nova=date(2026, 7, 1),
        )
        assert any("posterior" in e for e in erros)

    def test_data_fim_anterior_inicio(self, page):
        erros = self._v(
            page,
            data_inicio_nova=date(2026, 7, 1),
            data_fim_nova=date(2026, 1, 1),
        )
        assert any("posterior" in e for e in erros)


# ---------------------------------------------------------------------------
# validar_cancelamento
# ---------------------------------------------------------------------------

class TestValidarCancelamento:
    def _v(self, page, **kwargs) -> list[str]:
        defaults = dict(
            fator_id=1,
            motivo="Fator revisado",
            fator_origem=_fator(),
        )
        defaults.update(kwargs)
        return page.validar_cancelamento(**defaults)

    def test_valido(self, page):
        assert self._v(page) == []

    def test_fator_id_none(self, page):
        erros = self._v(page, fator_id=None, fator_origem=None)
        assert any("Selecione" in e for e in erros)

    def test_fator_origem_none(self, page):
        erros = self._v(page, fator_id=99, fator_origem=None)
        assert any("não encontrado" in e for e in erros)

    def test_ja_cancelado(self, page):
        f_canc = _fator(status="cancelado")
        erros = self._v(page, fator_origem=f_canc)
        assert any("cancelado" in e.lower() for e in erros)

    def test_motivo_vazio(self, page):
        erros = self._v(page, motivo="")
        assert any("obrigatório" in e or "Motivo" in e for e in erros)

    def test_motivo_apenas_espacos(self, page):
        erros = self._v(page, motivo="   ")
        assert any("obrigatório" in e or "Motivo" in e for e in erros)

    def test_motivo_curto_valido(self, page):
        assert self._v(page, motivo="ok") == []

    def test_acumula_erros_multiplos(self, page):
        erros = self._v(page, fator_id=None, motivo="", fator_origem=None)
        assert len(erros) >= 1  # fator_id=None retorna cedo com 1 erro
