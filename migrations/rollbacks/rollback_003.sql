DROP INDEX IF EXISTS idx_fa_vigencia_lookup;
DROP INDEX IF EXISTS idx_fa_historico;
DROP INDEX IF EXISTS idx_fa_status;
DELETE FROM schema_version WHERE version = '003';
