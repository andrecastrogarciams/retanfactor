"""
Testes unitários para factor_service.py.
Verifica orquestração de negócio: validações, log, invalidação de cache.
"""
import sys
import logging
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.factor import FatorArtigo
from repositories.sqlite_repo import apply_migrations, get_connection, get_fator_by_id
from services.factor_service import (
    buscar_fator,
    cancelar_fator,
    criar_fator,
    duplicar_fator,
    listar_fatores,
)
from services.report_service import ReportCache

MIGRATIONS_DIR = Path(__file__).parent.parent.parent / "migrations"
ESTACAO = "PC-RECURT-01"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def conn():
    c = get_connection(":memory:")
    apply_migrations(c, MIGRATIONS_DIR)
    yield c
    c.close()


@pytest.fixture
def fator_base(conn) -> int:
    f = FatorArtigo(
        codigo_artigo="ART001",
        descricao_artigo="Artigo Teste",
        fator=1.25,
        data_inicio_vigencia="2026-01-01",
        data_fim_vigencia="2026-06-30",
    )
    return criar_fator(conn, f, ESTACAO)


@pytest.fixture(autouse=True)
def cache_isolado(monkeypatch):
    """Substitui o cache global por instância isolada em cada teste."""
    local_cache = ReportCache(ttl_seconds=60)
    import services.factor_service as fs
    monkeypatch.setattr(fs, "get_cache", lambda: local_cache)
    return local_cache


# ---------------------------------------------------------------------------
# criar_fator
# ---------------------------------------------------------------------------

class TestCriarFator:
    def test_cria_e_retorna_id(self, conn):
        f = FatorArtigo(
            codigo_artigo="ART002",
            descricao_artigo="Artigo B",
            fator=1.5,
            data_inicio_vigencia="2026-01-01",
        )
        new_id = criar_fator(conn, f, ESTACAO)
        assert isinstance(new_id, int) and new_id > 0

    def test_persistido_no_banco(self, conn, fator_base):
        fator = buscar_fator(conn, fator_base)
        assert fator is not None
        assert fator.codigo_artigo == "ART001"
        assert fator.fator == pytest.approx(1.25)

    def test_invalida_cache_apos_criacao(self, conn, cache_isolado):
        cache_isolado.set("relatorio_key", [])
        f = FatorArtigo(
            codigo_artigo="ART003",
            descricao_artigo="Artigo C",
            fator=2.0,
            data_inicio_vigencia="2026-01-01",
        )
        criar_fator(conn, f, ESTACAO)
        assert cache_isolado.get("relatorio_key") is None

    def test_rejeita_sobreposicao(self, conn, fator_base):
        f = FatorArtigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Duplicado",
            fator=2.0,
            data_inicio_vigencia="2026-03-01",
            data_fim_vigencia="2026-09-30",
        )
        with pytest.raises(ValueError, match="Sobreposição"):
            criar_fator(conn, f, ESTACAO)

    def test_rejeita_codigo_artigo_vazio(self, conn):
        f = FatorArtigo(
            codigo_artigo="",
            descricao_artigo="Artigo X",
            fator=1.0,
            data_inicio_vigencia="2026-01-01",
        )
        with pytest.raises(ValueError, match="Código do artigo"):
            criar_fator(conn, f, ESTACAO)

    def test_rejeita_descricao_vazia(self, conn):
        f = FatorArtigo(
            codigo_artigo="ART010",
            descricao_artigo="",
            fator=1.0,
            data_inicio_vigencia="2026-01-01",
        )
        with pytest.raises(ValueError, match="Descrição"):
            criar_fator(conn, f, ESTACAO)

    def test_rejeita_fator_zero(self, conn):
        f = FatorArtigo(
            codigo_artigo="ART011",
            descricao_artigo="Artigo Y",
            fator=0,
            data_inicio_vigencia="2026-01-01",
        )
        with pytest.raises(ValueError, match="Fator deve ser maior"):
            criar_fator(conn, f, ESTACAO)

    def test_rejeita_fator_negativo(self, conn):
        f = FatorArtigo(
            codigo_artigo="ART012",
            descricao_artigo="Artigo Z",
            fator=-1.0,
            data_inicio_vigencia="2026-01-01",
        )
        with pytest.raises(ValueError, match="Fator deve ser maior"):
            criar_fator(conn, f, ESTACAO)

    def test_rejeita_data_inicio_ausente(self, conn):
        f = FatorArtigo(
            codigo_artigo="ART013",
            descricao_artigo="Artigo W",
            fator=1.0,
            data_inicio_vigencia="",
        )
        with pytest.raises(ValueError, match="início da vigência"):
            criar_fator(conn, f, ESTACAO)

    def test_registra_log_criacao(self, conn, caplog):
        f = FatorArtigo(
            codigo_artigo="ART020",
            descricao_artigo="Artigo Log",
            fator=1.75,
            data_inicio_vigencia="2026-01-01",
        )
        with caplog.at_level(logging.INFO, logger="services.factor_service"):
            criar_fator(conn, f, ESTACAO)

        assert "FATOR_CRIADO" in caplog.text
        assert "ART020" in caplog.text
        assert ESTACAO in caplog.text


# ---------------------------------------------------------------------------
# cancelar_fator
# ---------------------------------------------------------------------------

class TestCancelarFator:
    def test_cancela_com_sucesso(self, conn, fator_base):
        cancelar_fator(conn, fator_base, "Fator revisado", ESTACAO)
        fator = buscar_fator(conn, fator_base)
        assert fator.status == "cancelado"
        assert fator.motivo_cancelamento == "Fator revisado"
        assert fator.cancelled_at is not None

    def test_invalida_cache_apos_cancelamento(self, conn, fator_base, cache_isolado):
        cache_isolado.set("key", [])
        cancelar_fator(conn, fator_base, "Cancelando", ESTACAO)
        assert cache_isolado.get("key") is None

    def test_rejeita_id_inexistente(self, conn):
        with pytest.raises(ValueError, match="não encontrado"):
            cancelar_fator(conn, 9999, "Motivo", ESTACAO)

    def test_rejeita_duplo_cancelamento(self, conn, fator_base):
        cancelar_fator(conn, fator_base, "Primeiro", ESTACAO)
        with pytest.raises(ValueError):
            cancelar_fator(conn, fator_base, "Segundo", ESTACAO)

    def test_registra_log_cancelamento(self, conn, fator_base, caplog):
        with caplog.at_level(logging.INFO, logger="services.factor_service"):
            cancelar_fator(conn, fator_base, "Motivo de teste", ESTACAO)

        assert "FATOR_CANCELADO" in caplog.text
        assert "ART001" in caplog.text
        assert ESTACAO in caplog.text
        assert "Motivo de teste" in caplog.text

    def test_log_contem_vigencia(self, conn, fator_base, caplog):
        with caplog.at_level(logging.INFO, logger="services.factor_service"):
            cancelar_fator(conn, fator_base, "Revisão", ESTACAO)

        assert "2026-01-01" in caplog.text


# ---------------------------------------------------------------------------
# duplicar_fator
# ---------------------------------------------------------------------------

class TestDuplicarFator:
    def test_duplica_com_nova_vigencia(self, conn, fator_base):
        new_id = duplicar_fator(conn, fator_base, "2026-07-01", ESTACAO, "2026-12-31")
        novo = buscar_fator(conn, new_id)
        original = buscar_fator(conn, fator_base)

        assert novo.codigo_artigo == original.codigo_artigo
        assert novo.fator == pytest.approx(original.fator)
        assert novo.data_inicio_vigencia == "2026-07-01"
        assert novo.data_fim_vigencia == "2026-12-31"
        assert novo.status == "ativo"

    def test_duplica_com_vigencia_aberta(self, conn, fator_base):
        new_id = duplicar_fator(conn, fator_base, "2026-07-01", ESTACAO)
        novo = buscar_fator(conn, new_id)
        assert novo.data_fim_vigencia is None

    def test_invalida_cache_apos_duplicacao(self, conn, fator_base, cache_isolado):
        cache_isolado.set("key", [])
        duplicar_fator(conn, fator_base, "2026-07-01", ESTACAO)
        assert cache_isolado.get("key") is None

    def test_rejeita_sobreposicao_na_duplicacao(self, conn, fator_base):
        with pytest.raises(ValueError, match="Sobreposição"):
            duplicar_fator(conn, fator_base, "2026-03-01", ESTACAO, "2026-09-30")

    def test_rejeita_data_inicio_vazia(self, conn, fator_base):
        with pytest.raises(ValueError, match="obrigatória"):
            duplicar_fator(conn, fator_base, "", ESTACAO)

    def test_rejeita_id_inexistente(self, conn):
        with pytest.raises(ValueError, match="não encontrado"):
            duplicar_fator(conn, 9999, "2026-07-01", ESTACAO)

    def test_nao_altera_registro_original(self, conn, fator_base):
        duplicar_fator(conn, fator_base, "2026-07-01", ESTACAO)
        original = buscar_fator(conn, fator_base)
        assert original.status == "ativo"
        assert original.data_inicio_vigencia == "2026-01-01"

    def test_registra_log_duplicacao(self, conn, fator_base, caplog):
        with caplog.at_level(logging.INFO, logger="services.factor_service"):
            duplicar_fator(conn, fator_base, "2026-07-01", ESTACAO, "2026-12-31")

        assert "FATOR_DUPLICADO" in caplog.text
        assert "ART001" in caplog.text
        assert ESTACAO in caplog.text
        assert str(fator_base) in caplog.text

    def test_log_contem_ids_origem_e_novo(self, conn, fator_base, caplog):
        with caplog.at_level(logging.INFO, logger="services.factor_service"):
            new_id = duplicar_fator(conn, fator_base, "2026-07-01", ESTACAO)

        assert f"origem_id={fator_base}" in caplog.text
        assert f"novo_id={new_id}" in caplog.text


# ---------------------------------------------------------------------------
# listar_fatores
# ---------------------------------------------------------------------------

class TestListarFatores:
    def test_lista_todos(self, conn, fator_base):
        resultado = listar_fatores(conn)
        assert len(resultado) >= 1

    def test_filtra_por_codigo(self, conn, fator_base):
        resultado = listar_fatores(conn, codigo_artigo="ART001")
        assert all(f.codigo_artigo == "ART001" for f in resultado)

    def test_apenas_vigentes(self, conn, fator_base):
        cancelar_fator(conn, fator_base, "Cancelado", ESTACAO)
        resultado = listar_fatores(conn, apenas_vigentes=True)
        assert not any(f.id == fator_base for f in resultado)

    def test_sem_filtros_inclui_cancelados(self, conn, fator_base):
        cancelar_fator(conn, fator_base, "Cancelado", ESTACAO)
        resultado = listar_fatores(conn)
        assert any(f.id == fator_base for f in resultado)

    def test_filtro_periodo(self, conn, fator_base):
        resultado = listar_fatores(
            conn,
            data_inicio_filtro="2026-01-01",
            data_fim_filtro="2026-06-30",
        )
        assert len(resultado) >= 1


# ---------------------------------------------------------------------------
# buscar_fator
# ---------------------------------------------------------------------------

class TestBuscarFator:
    def test_encontra_existente(self, conn, fator_base):
        fator = buscar_fator(conn, fator_base)
        assert fator is not None
        assert fator.id == fator_base

    def test_retorna_none_inexistente(self, conn):
        assert buscar_fator(conn, 9999) is None


# ---------------------------------------------------------------------------
# Fluxo completo: criar → duplicar → cancelar
# ---------------------------------------------------------------------------

class TestFluxoCompleto:
    def test_ciclo_de_vida_completo(self, conn, caplog):
        f = FatorArtigo(
            codigo_artigo="ART099",
            descricao_artigo="Artigo Ciclo",
            fator=1.10,
            data_inicio_vigencia="2026-01-01",
            data_fim_vigencia="2026-06-30",
        )

        with caplog.at_level(logging.INFO, logger="services.factor_service"):
            id_v1 = criar_fator(conn, f, ESTACAO)
            id_v2 = duplicar_fator(conn, id_v1, "2026-07-01", ESTACAO, "2026-12-31")
            cancelar_fator(conn, id_v1, "Substituído pela v2", ESTACAO)

        v1 = buscar_fator(conn, id_v1)
        v2 = buscar_fator(conn, id_v2)

        assert v1.status == "cancelado"
        assert v2.status == "ativo"
        assert v2.data_inicio_vigencia == "2026-07-01"

        assert "FATOR_CRIADO" in caplog.text
        assert "FATOR_DUPLICADO" in caplog.text
        assert "FATOR_CANCELADO" in caplog.text

    def test_sobreposicao_bloqueada_em_todas_as_operacoes(self, conn, fator_base):
        overlapping = FatorArtigo(
            codigo_artigo="ART001",
            descricao_artigo="ART001",
            fator=2.0,
            data_inicio_vigencia="2026-03-01",
        )
        with pytest.raises(ValueError, match="Sobreposição"):
            criar_fator(conn, overlapping, ESTACAO)

        with pytest.raises(ValueError, match="Sobreposição"):
            duplicar_fator(conn, fator_base, "2026-03-01", ESTACAO)
