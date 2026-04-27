"""
Testes para services/export_service.py.
Verificam a API pública exportar_pdf() e funções auxiliares:
_fmt, _build_summary_table, _build_data_table.
"""
import sys
import unittest.mock as mock
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.report_row import CorDiferenca, ReportRow
from services.export_service import (
    _build_data_table,
    _build_summary_table,
    _fmt,
    exportar_pdf,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _row(
    data="2026-03-15",
    artigo="Artigo A",
    cor="PRETO",
    lote="L001",
    codigo="ART001",
    m2=100.0,
    peso_lote=120.0,
    kg_m2=1.20,
    kg_ft2=0.11,
    fator=1.25,
    peso_calc=124.50,
    pct=-3.62,
    cor_dif=CorDiferenca.VERDE,
) -> ReportRow:
    return ReportRow(
        data_recurtimento=data,
        artigo=artigo,
        cor=cor,
        lote_fabricacao=lote,
        codigo_artigo=codigo,
        m2=m2,
        peso_lote=peso_lote,
        kg_m2=kg_m2,
        kg_ft2=kg_ft2,
        fator_aplicado=fator,
        peso_calculado=peso_calc,
        pct_diferenca=pct,
        cor_diferenca=cor_dif,
    )


def _row_sem_calculo() -> ReportRow:
    return ReportRow(
        data_recurtimento="2026-03-15",
        artigo="Artigo Sem Fator",
        cor="MARROM",
        lote_fabricacao="L002",
        codigo_artigo="ART999",
        m2=50.0,
        peso_lote=None,
    )


def _resumo_padrao() -> dict:
    return {
        "total_linhas": 10,
        "media_pct_diferenca": -2.50,
        "total_verde": 5,
        "total_amarelo": 3,
        "total_vermelho": 2,
        "total_sem_calculo": 0,
    }


def _filtros_padrao() -> dict:
    return {
        "data_inicio": "2026-03-01",
        "data_fim": "2026-03-31",
        "lote": None,
        "artigo": None,
        "cor": None,
    }


# ---------------------------------------------------------------------------
# _fmt
# ---------------------------------------------------------------------------

class TestFmt:
    def test_none_retorna_traco(self):
        assert _fmt(None, "artigo") == "—"

    def test_numerico_com_duas_casas(self):
        assert _fmt(1.2567, "m2") == "1.26"

    def test_numerico_inteiro_com_duas_casas(self):
        assert _fmt(100.0, "m2") == "100.00"

    def test_texto_retorna_string(self):
        assert _fmt("PRETO", "cor") == "PRETO"

    def test_pct_diferenca_com_negativo(self):
        assert _fmt(-3.625, "pct_diferenca") == "-3.62"

    def test_numerico_invalido_retorna_string(self):
        assert _fmt("N/A", "m2") == "N/A"


# ---------------------------------------------------------------------------
# _build_summary_table
# ---------------------------------------------------------------------------

class TestBuildSummaryTable:
    def test_retorna_table(self):
        from reportlab.platypus import Table
        t = _build_summary_table(_resumo_padrao())
        assert isinstance(t, Table)

    def test_duas_linhas(self):
        t = _build_summary_table(_resumo_padrao())
        # Table armazena dados internamente como _cellvalues
        assert len(t._cellvalues) == 2

    def test_valores_no_resumo(self):
        resumo = _resumo_padrao()
        t = _build_summary_table(resumo)
        valores = t._cellvalues[1]
        assert "10" in valores           # total_linhas
        assert "-2.50%" in valores       # media_pct_diferenca
        assert "5" in valores            # verde
        assert "3" in valores            # amarelo
        assert "2" in valores            # vermelho

    def test_media_none_exibe_traco(self):
        resumo = _resumo_padrao()
        resumo["media_pct_diferenca"] = None
        t = _build_summary_table(resumo)
        valores = t._cellvalues[1]
        assert "—" in valores

    def test_zeros_nao_crasham(self):
        resumo = {
            "total_linhas": 0,
            "media_pct_diferenca": None,
            "total_verde": 0,
            "total_amarelo": 0,
            "total_vermelho": 0,
            "total_sem_calculo": 0,
        }
        t = _build_summary_table(resumo)
        assert t is not None


# ---------------------------------------------------------------------------
# _build_data_table
# ---------------------------------------------------------------------------

class TestBuildDataTable:
    def test_retorna_table(self):
        from reportlab.platypus import Table
        t = _build_data_table([_row()])
        assert isinstance(t, Table)

    def test_header_mais_linhas_de_dados(self):
        rows = [_row(), _row(artigo="B")]
        t = _build_data_table(rows)
        # 1 header + 2 linhas de dados
        assert len(t._cellvalues) == 3

    def test_lista_vazia_so_header(self):
        t = _build_data_table([])
        assert len(t._cellvalues) == 1

    def test_row_sem_calculo_exibe_traco(self):
        t = _build_data_table([_row_sem_calculo()])
        # Última coluna (% Dif.) deve ter "—"
        ultima_coluna = t._cellvalues[1][-1]
        assert ultima_coluna == "—"

    def test_12_colunas_no_header(self):
        t = _build_data_table([_row()])
        assert len(t._cellvalues[0]) == 12

    def test_valores_numericos_formatados(self):
        t = _build_data_table([_row(m2=200.0, pct=-7.55)])
        linha = t._cellvalues[1]
        assert "200.00" in linha
        assert "-7.55" in linha


# ---------------------------------------------------------------------------
# exportar_pdf
# ---------------------------------------------------------------------------

class TestExportarPdf:
    def _call(self, rows=None, filtros=None, resumo=None, estacao="RECURTIMENTO"):
        return exportar_pdf(
            rows=rows if rows is not None else [_row()],
            filtros=filtros or _filtros_padrao(),
            resumo=resumo or _resumo_padrao(),
            estacao=estacao,
        )

    def test_retorna_bytes(self):
        result = self._call()
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_header_pdf_valido(self):
        result = self._call()
        assert result[:4] == b"%PDF"

    def test_lista_vazia_de_rows(self):
        result = self._call(rows=[])
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"

    def test_resumo_todos_zeros(self):
        resumo = {
            "total_linhas": 0,
            "media_pct_diferenca": None,
            "total_verde": 0,
            "total_amarelo": 0,
            "total_vermelho": 0,
            "total_sem_calculo": 0,
        }
        result = self._call(rows=[], resumo=resumo)
        assert result[:4] == b"%PDF"

    def test_multiplas_linhas(self):
        rows = [
            _row(artigo="Alpha", cor_dif=CorDiferenca.VERDE),
            _row(artigo="Beta", pct=7.0, cor_dif=CorDiferenca.AMARELO),
            _row(artigo="Gamma", pct=15.0, cor_dif=CorDiferenca.VERMELHO),
            _row_sem_calculo(),
        ]
        result = self._call(rows=rows)
        assert result[:4] == b"%PDF"

    def test_linha_sem_calculo_nao_crasha(self):
        result = self._call(rows=[_row_sem_calculo()])
        assert isinstance(result, bytes)

    def test_filtros_ativos_nao_crasham(self):
        filtros = {
            "data_inicio": "2026-01-01",
            "data_fim": "2026-01-31",
            "lote": "L-XYZ",
            "artigo": "Artigo Teste",
            "cor": "PRETO",
        }
        result = self._call(filtros=filtros)
        assert result[:4] == b"%PDF"

    def test_estacao_custom(self):
        result = self._call(estacao="RECURTIMENTO-HML")
        assert result[:4] == b"%PDF"

    def test_sem_logo_nao_crasha(self):
        with mock.patch("services.export_service._LOGO_PATH") as mock_path:
            mock_path.exists.return_value = False
            result = self._call()
        assert result[:4] == b"%PDF"

    def test_logo_corrompido_nao_crasha(self):
        with mock.patch("services.export_service._LOGO_PATH") as mock_path:
            mock_path.exists.return_value = True
            with mock.patch("services.export_service.ImageReader", side_effect=Exception("Erro")):
                result = self._call()
        assert result[:4] == b"%PDF"

    def test_todas_cores_simultaneas(self):
        rows = [
            _row(pct=-2.0, cor_dif=CorDiferenca.VERDE),
            _row(pct=7.5, cor_dif=CorDiferenca.AMARELO),
            _row(pct=12.0, cor_dif=CorDiferenca.VERMELHO),
        ]
        result = self._call(rows=rows)
        assert result[:4] == b"%PDF"

    def test_grande_volume_nao_crasha(self):
        rows = [_row(artigo=f"Art {i}", m2=float(i + 1)) for i in range(200)]
        result = self._call(rows=rows)
        assert result[:4] == b"%PDF"
        assert len(result) > 1000
