CREATE TABLE IF NOT EXISTS schema_version (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    version     TEXT    NOT NULL UNIQUE,
    description TEXT    NOT NULL,
    applied_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    checksum    TEXT
);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES ('001', 'Tabela de controle de migrations');
