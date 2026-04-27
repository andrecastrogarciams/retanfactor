"""
Testes unitários para report_service.py.
Oracle é substituído por função mock — sem dependência de banco externo.
SQLite usa banco em memória com migrations aplicadas.
"""
import sys
import time
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.report_row import CorDiferenca, OracleRow, ReportRow
from models.factor import FatorArtigo
from repositories.sqlite_repo import apply_migrations, get_connection, insert_fator
from services.report_service import (
    ReportCache,
    build_relatorio,
    calcular_kg_ft2,
    calcular_kg_m2,
    calcular_linha,
    calcular_peso_calculado,
    calcular_pct_diferenca,
    calcular_resumo,
    classificar_cor,
    get_relatorio,
)

MIGRATIONS_DIR = Path(__file__).parent.parent.parent / "migrations"

# Fórmula de referência para validações
_M2_TO_FT2 = 10.764


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sqlite_conn():
    c = get_connection(":memory:")
    apply_migrations(c, MIGRATIONS_DIR)
    yield c
    c.close()


@pytest.fixture
def sqlite_com_fator(sqlite_conn):
    insert_fator(
        sqlite_conn,
        FatorArtigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Teste",
            fator=1.25,
            data_inicio_vigencia="2026-01-01",
            data_fim_vigencia=None,
        ),
    )
    return sqlite_conn


def oracle_row(
    codigo="ART001",
    data="2026-03-15",
    m2=100.0,
    peso_lote=120.0,
    artigo="Artigo Teste",
    cor="PRETO",
    lote="L001",
) -> OracleRow:
    return OracleRow(
        data_recurtimento=data,
        artigo=artigo,
        cor=cor,
        lote_fabricacao=lote,
        codigo_artigo=codigo,
        m2=m2,
        peso_lote=peso_lote,
    )


def mock_oracle(rows: list[OracleRow]):
    def _fetch(**kwargs):
        return rows
    return _fetch


# ---------------------------------------------------------------------------
# calcular_kg_m2
# ---------------------------------------------------------------------------

class TestCalcularKgM2:
    def test_calculo_correto(self):
        assert calcular_kg_m2(120.0, 100.0) == pytest.approx(1.20)

    def test_arredonda_duas_casas(self):
        result = calcular_kg_m2(100.0, 3.0)
        assert result == pytest.approx(33.33)

    def test_m2_zero_retorna_none(self):
        assert calcular_kg_m2(120.0, 0.0) is None

    def test_m2_none_retorna_none(self):
        assert calcular_kg_m2(120.0, None) is None


# ---------------------------------------------------------------------------
# calcular_kg_ft2
# ---------------------------------------------------------------------------

class TestCalcularKgFt2:
    def test_calculo_correto(self):
        expected = round(120.0 / (100.0 * _M2_TO_FT2), 2)
        assert calcular_kg_ft2(120.0, 100.0) == pytest.approx(expected)

    def test_arredonda_duas_casas(self):
        result = calcular_kg_ft2(100.0, 3.0)
        expected = round(100.0 / (3.0 * _M2_TO_FT2), 2)
        assert result == pytest.approx(expected)

    def test_m2_zero_retorna_none(self):
        assert calcular_kg_ft2(120.0, 0.0) is None

    def test_m2_none_retorna_none(self):
        assert calcular_kg_ft2(120.0, None) is None


# ---------------------------------------------------------------------------
# calcular_peso_calculado
# ---------------------------------------------------------------------------

class TestCalcularPesoCalculado:
    def test_formula_correta(self):
        # peso_calculado = m² × 10.764 × fator × 0.092903
        expected = round(100.0 * 10.764 * 1.25 * 0.092903, 2)
        assert calcular_peso_calculado(100.0, 1.25) == pytest.approx(expected)

    def test_arredonda_duas_casas(self):
        result = calcular_peso_calculado(33.33, 1.0)
        assert isinstance(result, float)
        assert len(str(result).split(".")[-1]) <= 2

    def test_m2_zero_retorna_none(self):
        assert calcular_peso_calculado(0.0, 1.25) is None

    def test_fator_zero_retorna_none(self):
        assert calcular_peso_calculado(100.0, 0.0) is None

    def test_m2_none_retorna_none(self):
        assert calcular_peso_calculado(None, 1.25) is None

    def test_fator_none_retorna_none(self):
        assert calcular_peso_calculado(100.0, None) is None


# ---------------------------------------------------------------------------
# calcular_pct_diferenca
# ---------------------------------------------------------------------------

class TestCalcularPctDiferenca:
    def test_sem_diferenca(self):
        assert calcular_pct_diferenca(100.0, 100.0) == pytest.approx(0.0)

    def test_diferenca_positiva(self):
        # (120 - 100) / 100 * 100 = 20%
        assert calcular_pct_diferenca(120.0, 100.0) == pytest.approx(20.0)

    def test_diferenca_negativa(self):
        # (80 - 100) / 100 * 100 = -20%
        assert calcular_pct_diferenca(80.0, 100.0) == pytest.approx(-20.0)

    def test_arredonda_duas_casas(self):
        result = calcular_pct_diferenca(100.0, 3.0)
        assert len(str(abs(result)).split(".")[-1]) <= 2

    def test_peso_calculado_zero_retorna_none(self):
        assert calcular_pct_diferenca(100.0, 0.0) is None

    def test_peso_calculado_none_retorna_none(self):
        assert calcular_pct_diferenca(100.0, None) is None


# ---------------------------------------------------------------------------
# classificar_cor
# ---------------------------------------------------------------------------

class TestClassificarCor:
    @pytest.mark.parametrize("pct", [0.0, 3.5, 5.0, -5.0, -3.5])
    def test_verde(self, pct):
        assert classificar_cor(pct) == CorDiferenca.VERDE

    @pytest.mark.parametrize("pct", [5.01, 7.5, 10.0, -5.01, -10.0])
    def test_amarelo(self, pct):
        assert classificar_cor(pct) == CorDiferenca.AMARELO

    @pytest.mark.parametrize("pct", [10.01, 25.0, -10.01, -50.0])
    def test_vermelho(self, pct):
        assert classificar_cor(pct) == CorDiferenca.VERMELHO

    def test_none_retorna_none(self):
        assert classificar_cor(None) is None

    def test_usa_valor_absoluto(self):
        assert classificar_cor(-4.0) == CorDiferenca.VERDE
        assert classificar_cor(4.0) == CorDiferenca.VERDE


# ---------------------------------------------------------------------------
# calcular_linha (integração das fórmulas)
# ---------------------------------------------------------------------------

class TestCalcularLinha:
    def test_calcula_todas_colunas(self):
        row = oracle_row(m2=100.0, peso_lote=120.0)
        fator = 1.25
        result = calcular_linha(row, fator)

        assert result.fator_aplicado == pytest.approx(1.25)
        assert result.kg_m2 == pytest.approx(1.20)
        assert result.kg_ft2 == pytest.approx(round(120.0 / (100.0 * _M2_TO_FT2), 2))
        assert result.peso_calculado == pytest.approx(round(100.0 * _M2_TO_FT2 * 1.25 * 0.092903, 2))
        assert result.pct_diferenca is not None
        assert result.cor_diferenca is not None

    def test_sem_fator_retorna_colunas_none(self):
        row = oracle_row(m2=100.0, peso_lote=120.0)
        result = calcular_linha(row, None)

        assert result.fator_aplicado is None
        assert result.kg_m2 is None
        assert result.kg_ft2 is None
        assert result.peso_calculado is None
        assert result.pct_diferenca is None
        assert result.cor_diferenca is None

    def test_m2_zero_retorna_colunas_none(self):
        row = oracle_row(m2=0.0, peso_lote=120.0)
        result = calcular_linha(row, 1.25)
        assert result.peso_calculado is None

    def test_peso_lote_zero_retorna_colunas_none(self):
        row = oracle_row(m2=100.0, peso_lote=0.0)
        result = calcular_linha(row, 1.25)
        assert result.peso_calculado is None

    def test_data_recurtimento_none_retorna_colunas_none(self):
        row = oracle_row(data=None, m2=100.0, peso_lote=120.0)
        result = calcular_linha(row, 1.25)
        assert result.peso_calculado is None

    def test_preserva_dados_oracle_originais(self):
        row = oracle_row(codigo="ART001", artigo="Artigo X", cor="MARROM", lote="L999")
        result = calcular_linha(row, None)

        assert result.codigo_artigo == "ART001"
        assert result.artigo == "Artigo X"
        assert result.cor == "MARROM"
        assert result.lote_fabricacao == "L999"

    def test_cor_diferenca_quando_dentro_da_faixa_verde(self):
        # Ajustar peso_lote para ficar dentro de 5%
        peso_calc = round(100.0 * _M2_TO_FT2 * 1.25 * 0.092903, 2)
        peso_lote = round(peso_calc * 1.03, 2)  # +3%
        row = oracle_row(m2=100.0, peso_lote=peso_lote)
        result = calcular_linha(row, 1.25)
        assert result.cor_diferenca == CorDiferenca.VERDE


# ---------------------------------------------------------------------------
# build_relatorio
# ---------------------------------------------------------------------------

class TestBuildRelatorio:
    def test_aplica_fator_vigente(self, sqlite_com_fator):
        rows = [oracle_row()]
        result = build_relatorio(rows, sqlite_com_fator)

        assert len(result) == 1
        assert result[0].fator_aplicado == pytest.approx(1.25)

    def test_sem_fator_no_banco(self, sqlite_conn):
        rows = [oracle_row(codigo="ARTIGO_SEM_FATOR")]
        result = build_relatorio(rows, sqlite_conn)

        assert result[0].peso_calculado is None

    def test_multiplas_linhas(self, sqlite_com_fator):
        rows = [
            oracle_row(codigo="ART001", lote="L001"),
            oracle_row(codigo="ART001", lote="L002"),
            oracle_row(codigo="ART999", lote="L003"),  # sem fator
        ]
        result = build_relatorio(rows, sqlite_com_fator)

        assert len(result) == 3
        assert result[0].fator_aplicado == pytest.approx(1.25)
        assert result[1].fator_aplicado == pytest.approx(1.25)
        assert result[2].fator_aplicado is None

    def test_linha_com_m2_none_no_oracle(self, sqlite_com_fator):
        row = OracleRow(
            data_recurtimento="2026-03-15",
            artigo="Artigo Teste",
            cor="PRETO",
            lote_fabricacao="L001",
            codigo_artigo="ART001",
            m2=None,
            peso_lote=120.0,
        )
        result = build_relatorio([row], sqlite_com_fator)
        assert result[0].peso_calculado is None


# ---------------------------------------------------------------------------
# get_relatorio (cache + injeção de mock Oracle)
# ---------------------------------------------------------------------------

class TestGetRelatorio:
    def test_retorna_linhas_calculadas(self, sqlite_com_fator):
        fetch_fn = mock_oracle([oracle_row()])
        result = get_relatorio(
            sqlite_com_fator,
            "2026-01-01", "2026-12-31",
            fetch_oracle_fn=fetch_fn,
        )
        assert len(result) == 1
        assert result[0].fator_aplicado == pytest.approx(1.25)

    def test_usa_cache_na_segunda_chamada(self, sqlite_com_fator):
        call_count = {"n": 0}
        local_cache = ReportCache(ttl_seconds=60)

        def counting_fetch(**kwargs):
            call_count["n"] += 1
            return [oracle_row()]

        get_relatorio(sqlite_com_fator, "2026-01-01", "2026-12-31",
                      fetch_oracle_fn=counting_fetch, cache=local_cache)
        get_relatorio(sqlite_com_fator, "2026-01-01", "2026-12-31",
                      fetch_oracle_fn=counting_fetch, cache=local_cache)

        assert call_count["n"] == 1  # Oracle chamado apenas uma vez

    def test_force_refresh_invalida_cache(self, sqlite_com_fator):
        call_count = {"n": 0}
        local_cache = ReportCache(ttl_seconds=60)

        def counting_fetch(**kwargs):
            call_count["n"] += 1
            return [oracle_row()]

        get_relatorio(sqlite_com_fator, "2026-01-01", "2026-12-31",
                      fetch_oracle_fn=counting_fetch, cache=local_cache)
        get_relatorio(sqlite_com_fator, "2026-01-01", "2026-12-31",
                      force_refresh=True, fetch_oracle_fn=counting_fetch, cache=local_cache)

        assert call_count["n"] == 2

    def test_filtros_diferentes_geram_cache_separado(self, sqlite_com_fator):
        call_count = {"n": 0}
        local_cache = ReportCache(ttl_seconds=60)

        def counting_fetch(**kwargs):
            call_count["n"] += 1
            return []

        get_relatorio(sqlite_com_fator, "2026-01-01", "2026-06-30",
                      fetch_oracle_fn=counting_fetch, cache=local_cache)
        get_relatorio(sqlite_com_fator, "2026-07-01", "2026-12-31",
                      fetch_oracle_fn=counting_fetch, cache=local_cache)

        assert call_count["n"] == 2

    def test_erro_oracle_propagado(self, sqlite_com_fator):
        local_cache = ReportCache(ttl_seconds=60)

        def failing_fetch(**kwargs):
            raise RuntimeError("Oracle indisponivel")

        with pytest.raises(RuntimeError, match="Oracle indisponivel"):
            get_relatorio(sqlite_com_fator, "2026-01-01", "2026-12-31",
                          fetch_oracle_fn=failing_fetch, cache=local_cache)


# ---------------------------------------------------------------------------
# ReportCache
# ---------------------------------------------------------------------------

class TestReportCache:
    def test_set_e_get(self):
        cache = ReportCache(ttl_seconds=60)
        rows = [calcular_linha(oracle_row(), 1.25)]
        cache.set("key1", rows)
        assert cache.get("key1") is rows

    def test_expirado_retorna_none(self):
        cache = ReportCache(ttl_seconds=0)
        cache.set("key1", [])
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_invalidate_limpa_tudo(self):
        cache = ReportCache(ttl_seconds=60)
        cache.set("key1", [])
        cache.set("key2", [])
        cache.invalidate()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_make_key_determinista(self):
        cache = ReportCache()
        k1 = cache.make_key(data_inicio="2026-01-01", lote="L001")
        k2 = cache.make_key(lote="L001", data_inicio="2026-01-01")
        assert k1 == k2


# ---------------------------------------------------------------------------
# calcular_resumo
# ---------------------------------------------------------------------------

class TestCalcularResumo:
    def _make_rows_with_pct(self, pcts: list[Optional[float]]) -> list[ReportRow]:
        rows = []
        for pct in pcts:
            r = oracle_row()
            result = ReportRow(
                data_recurtimento=r.data_recurtimento,
                artigo=r.artigo,
                cor=r.cor,
                lote_fabricacao=r.lote_fabricacao,
                codigo_artigo=r.codigo_artigo,
                m2=r.m2,
                peso_lote=r.peso_lote,
                pct_diferenca=pct,
                cor_diferenca=classificar_cor(pct),
            )
            rows.append(result)
        return rows

    def test_total_linhas(self):
        rows = self._make_rows_with_pct([1.0, 7.0, 15.0, None])
        resumo = calcular_resumo(rows)
        assert resumo["total_linhas"] == 4

    def test_contagem_por_cor(self):
        rows = self._make_rows_with_pct([1.0, 7.0, 15.0])
        resumo = calcular_resumo(rows)
        assert resumo["total_verde"] == 1
        assert resumo["total_amarelo"] == 1
        assert resumo["total_vermelho"] == 1

    def test_media_pct_diferenca(self):
        rows = self._make_rows_with_pct([10.0, 20.0])
        resumo = calcular_resumo(rows)
        assert resumo["media_pct_diferenca"] == pytest.approx(15.0)

    def test_sem_calculo_excluido_da_media(self):
        rows = self._make_rows_with_pct([10.0, None])
        resumo = calcular_resumo(rows)
        assert resumo["media_pct_diferenca"] == pytest.approx(10.0)
        assert resumo["total_sem_calculo"] == 1

    def test_todas_sem_calculo(self):
        rows = self._make_rows_with_pct([None, None])
        resumo = calcular_resumo(rows)
        assert resumo["media_pct_diferenca"] is None
        assert resumo["total_sem_calculo"] == 2
