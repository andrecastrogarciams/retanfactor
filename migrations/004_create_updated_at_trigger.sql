-- SQLite não atualiza updated_at automaticamente; trigger garante integridade
CREATE TRIGGER IF NOT EXISTS trg_fator_artigo_updated_at
AFTER UPDATE ON fator_artigo
FOR EACH ROW
BEGIN
    UPDATE fator_artigo
    SET updated_at = datetime('now', 'localtime')
    WHERE id = OLD.id;
END;

INSERT OR IGNORE INTO schema_version (version, description)
VALUES ('004', 'Trigger para atualizacao automatica de updated_at');
