"""
Testes unitários para sqlite_repo.py.
Cada test usa banco SQLite em memória — sem dependência de arquivo externo.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from repositories.sqlite_repo import (
    apply_migrations,
    cancel_fator,
    duplicate_fator,
    get_fator_by_id,
    get_fator_vigente,
    get_connection,
    has_vigencia_overlap,
    insert_fator,
    list_fatores,
)
from models.factor import FatorArtigo

MIGRATIONS_DIR = Path(__file__).parent.parent.parent / "migrations"


@pytest.fixture
def conn():
    """Conexão SQLite em memória com migrations aplicadas."""
    c = get_connection(":memory:")
    apply_migrations(c, MIGRATIONS_DIR)
    yield c
    c.close()


@pytest.fixture
def fator_base(conn) -> int:
    """Insere um fator base e retorna o id."""
    f = FatorArtigo(
        codigo_artigo="ART001",
        descricao_artigo="Artigo Teste",
        fator=1.25,
        data_inicio_vigencia="2026-01-01",
        data_fim_vigencia="2026-06-30",
    )
    return insert_fator(conn, f)


# ---------------------------------------------------------------------------
# apply_migrations
# ---------------------------------------------------------------------------

class TestApplyMigrations:
    def test_cria_tabela_fator_artigo(self, conn):
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "fator_artigo" in tables
        assert "schema_version" in tables

    def test_cria_indices(self, conn):
        indexes = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='fator_artigo'"
            ).fetchall()
        }
        assert "idx_fa_vigencia_lookup" in indexes
        assert "idx_fa_historico" in indexes
        assert "idx_fa_status" in indexes

    def test_cria_trigger(self, conn):
        triggers = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            ).fetchall()
        }
        assert "trg_fator_artigo_updated_at" in triggers

    def test_idempotente(self, conn):
        apply_migrations(conn, MIGRATIONS_DIR)  # segunda chamada não deve falhar
        count = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
        assert count == 4  # exatamente 4 migrations registradas


# ---------------------------------------------------------------------------
# get_fator_vigente (Q1 — hottest path)
# ---------------------------------------------------------------------------

class TestGetFatorVigente:
    def test_retorna_fator_vigente(self, conn, fator_base):
        result = get_fator_vigente(conn, "ART001", "2026-03-15")
        assert result == pytest.approx(1.25)

    def test_retorna_none_sem_fator(self, conn):
        result = get_fator_vigente(conn, "ART999", "2026-03-15")
        assert result is None

    def test_retorna_none_fora_da_vigencia(self, conn, fator_base):
        result = get_fator_vigente(conn, "ART001", "2025-12-31")
        assert result is None

    def test_retorna_none_apos_vigencia(self, conn, fator_base):
        result = get_fator_vigente(conn, "ART001", "2026-07-01")
        assert result is None

    def test_vigencia_aberta_cobre_datas_futuras(self, conn):
        f = FatorArtigo(
            codigo_artigo="ART002",
            descricao_artigo="Artigo Vigencia Aberta",
            fator=2.0,
            data_inicio_vigencia="2026-01-01",
            data_fim_vigencia=None,
        )
        insert_fator(conn, f)
        assert get_fator_vigente(conn, "ART002", "2030-01-01") == pytest.approx(2.0)

    def test_ignora_fator_cancelado(self, conn, fator_base):
        cancel_fator(conn, fator_base, "Teste de cancelamento")
        result = get_fator_vigente(conn, "ART001", "2026-03-15")
        assert result is None

    def test_usa_mais_recente_quando_multiplos(self, conn, caplog):
        # Inserir dois fatores que se sobrepõem diretamente via SQL (bypassa validação)
        conn.execute(
            "INSERT INTO fator_artigo (codigo_artigo, descricao_artigo, fator, data_inicio_vigencia) "
            "VALUES ('ART003', 'Artigo X', 1.0, '2026-01-01')"
        )
        conn.execute(
            "INSERT INTO fator_artigo (codigo_artigo, descricao_artigo, fator, data_inicio_vigencia) "
            "VALUES ('ART003', 'Artigo X', 2.0, '2026-02-01')"
        )
        conn.commit()

        with caplog.at_level("WARNING"):
            result = get_fator_vigente(conn, "ART003", "2026-03-01")

        assert result == pytest.approx(2.0)
        assert "Múltiplos fatores vigentes" in caplog.text


# ---------------------------------------------------------------------------
# has_vigencia_overlap
# ---------------------------------------------------------------------------

class TestHasVigenciaOverlap:
    def test_detecta_sobreposicao_total(self, conn, fator_base):
        assert has_vigencia_overlap(conn, "ART001", "2026-01-01", "2026-06-30") is True

    def test_detecta_sobreposicao_parcial_inicio(self, conn, fator_base):
        assert has_vigencia_overlap(conn, "ART001", "2025-12-01", "2026-02-01") is True

    def test_detecta_sobreposicao_parcial_fim(self, conn, fator_base):
        assert has_vigencia_overlap(conn, "ART001", "2026-05-01", "2026-08-01") is True

    def test_sem_sobreposicao_antes(self, conn, fator_base):
        assert has_vigencia_overlap(conn, "ART001", "2025-01-01", "2025-12-31") is False

    def test_sem_sobreposicao_depois(self, conn, fator_base):
        assert has_vigencia_overlap(conn, "ART001", "2026-07-01", "2026-12-31") is False

    def test_vigencia_aberta_existente_sobrepoe_tudo(self, conn):
        f = FatorArtigo(
            codigo_artigo="ART004",
            descricao_artigo="Artigo D",
            fator=1.0,
            data_inicio_vigencia="2026-01-01",
            data_fim_vigencia=None,
        )
        insert_fator(conn, f)
        assert has_vigencia_overlap(conn, "ART004", "2030-01-01", "2030-12-31") is True

    def test_nova_vigencia_aberta_sobrepoe_existente(self, conn, fator_base):
        assert has_vigencia_overlap(conn, "ART001", "2026-06-01", None) is True

    def test_exclude_id_ignora_proprio_registro(self, conn, fator_base):
        assert has_vigencia_overlap(
            conn, "ART001", "2026-01-01", "2026-06-30", exclude_id=fator_base
        ) is False

    def test_nao_detecta_cancelado(self, conn, fator_base):
        cancel_fator(conn, fator_base, "Cancelado para teste")
        assert has_vigencia_overlap(conn, "ART001", "2026-01-01", "2026-06-30") is False


# ---------------------------------------------------------------------------
# insert_fator
# ---------------------------------------------------------------------------

class TestInsertFator:
    def test_insere_com_sucesso(self, conn):
        f = FatorArtigo(
            codigo_artigo="ART005",
            descricao_artigo="Artigo E",
            fator=1.5,
            data_inicio_vigencia="2026-01-01",
        )
        new_id = insert_fator(conn, f)
        assert isinstance(new_id, int)
        assert new_id > 0

    def test_bloqueia_sobreposicao(self, conn, fator_base):
        f = FatorArtigo(
            codigo_artigo="ART001",
            descricao_artigo="Artigo Duplicado",
            fator=2.0,
            data_inicio_vigencia="2026-03-01",
            data_fim_vigencia="2026-09-30",
        )
        with pytest.raises(ValueError, match="Sobreposição"):
            insert_fator(conn, f)

    def test_rejeita_fator_zero(self, conn):
        import sqlite3 as _sqlite3
        f = FatorArtigo(
            codigo_artigo="ART006",
            descricao_artigo="Artigo F",
            fator=0,
            data_inicio_vigencia="2026-01-01",
        )
        with pytest.raises(_sqlite3.IntegrityError):
            insert_fator(conn, f)

    def test_rejeita_fator_negativo(self, conn):
        import sqlite3 as _sqlite3
        f = FatorArtigo(
            codigo_artigo="ART007",
            descricao_artigo="Artigo G",
            fator=-1.0,
            data_inicio_vigencia="2026-01-01",
        )
        with pytest.raises(_sqlite3.IntegrityError):
            insert_fator(conn, f)

    def test_rejeita_data_fim_anterior_a_inicio(self, conn):
        import sqlite3 as _sqlite3
        f = FatorArtigo(
            codigo_artigo="ART008",
            descricao_artigo="Artigo H",
            fator=1.0,
            data_inicio_vigencia="2026-06-01",
            data_fim_vigencia="2026-01-01",
        )
        with pytest.raises((_sqlite3.IntegrityError, ValueError)):
            insert_fator(conn, f)


# ---------------------------------------------------------------------------
# cancel_fator
# ---------------------------------------------------------------------------

class TestCancelFator:
    def test_cancela_com_sucesso(self, conn, fator_base):
        cancel_fator(conn, fator_base, "Fator desatualizado")
        fator = get_fator_by_id(conn, fator_base)
        assert fator.status == "cancelado"
        assert fator.motivo_cancelamento == "Fator desatualizado"
        assert fator.cancelled_at is not None

    def test_rejeita_motivo_vazio(self, conn, fator_base):
        with pytest.raises(ValueError, match="obrigatório"):
            cancel_fator(conn, fator_base, "")

    def test_rejeita_motivo_espacos(self, conn, fator_base):
        with pytest.raises(ValueError, match="obrigatório"):
            cancel_fator(conn, fator_base, "   ")

    def test_rejeita_duplo_cancelamento(self, conn, fator_base):
        cancel_fator(conn, fator_base, "Primeiro cancelamento")
        with pytest.raises(ValueError, match="já está cancelado"):
            cancel_fator(conn, fator_base, "Segundo cancelamento")

    def test_rejeita_id_inexistente(self, conn):
        with pytest.raises(ValueError, match="não encontrado"):
            cancel_fator(conn, 9999, "Motivo qualquer")

    def test_cancelado_nao_aparece_em_vigentes(self, conn, fator_base):
        cancel_fator(conn, fator_base, "Cancelado")
        vigentes = list_fatores(conn, apenas_vigentes=True)
        assert not any(f.id == fator_base for f in vigentes)


# ---------------------------------------------------------------------------
# duplicate_fator
# ---------------------------------------------------------------------------

class TestDuplicateFator:
    def test_duplica_com_nova_vigencia(self, conn, fator_base):
        new_id = duplicate_fator(conn, fator_base, "2026-07-01", "2026-12-31")
        novo = get_fator_by_id(conn, new_id)
        original = get_fator_by_id(conn, fator_base)

        assert novo.codigo_artigo == original.codigo_artigo
        assert novo.descricao_artigo == original.descricao_artigo
        assert novo.fator == original.fator
        assert novo.observacao == original.observacao
        assert novo.data_inicio_vigencia == "2026-07-01"
        assert novo.data_fim_vigencia == "2026-12-31"
        assert novo.status == "ativo"

    def test_duplica_com_vigencia_aberta(self, conn, fator_base):
        new_id = duplicate_fator(conn, fator_base, "2026-07-01")
        novo = get_fator_by_id(conn, new_id)
        assert novo.data_fim_vigencia is None

    def test_duplicacao_respeita_validacao_sobreposicao(self, conn, fator_base):
        with pytest.raises(ValueError, match="Sobreposição"):
            duplicate_fator(conn, fator_base, "2026-03-01", "2026-09-30")

    def test_duplicacao_id_inexistente(self, conn):
        with pytest.raises(ValueError, match="não encontrado"):
            duplicate_fator(conn, 9999, "2026-07-01")


# ---------------------------------------------------------------------------
# list_fatores
# ---------------------------------------------------------------------------

class TestListFatores:
    def test_lista_todos(self, conn, fator_base):
        fatores = list_fatores(conn)
        assert len(fatores) >= 1

    def test_filtra_por_codigo(self, conn, fator_base):
        fatores = list_fatores(conn, codigo_artigo="ART001")
        assert all(f.codigo_artigo == "ART001" for f in fatores)

    def test_apenas_vigentes_exclui_cancelados(self, conn, fator_base):
        cancel_fator(conn, fator_base, "Cancelado para teste")
        vigentes = list_fatores(conn, apenas_vigentes=True)
        assert not any(f.id == fator_base for f in vigentes)

    def test_filtro_periodo_vigencia(self, conn, fator_base):
        fatores = list_fatores(
            conn,
            data_inicio_filtro="2026-01-01",
            data_fim_filtro="2026-06-30",
        )
        assert len(fatores) >= 1
