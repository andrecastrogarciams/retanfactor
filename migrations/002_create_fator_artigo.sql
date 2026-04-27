CREATE TABLE IF NOT EXISTS fator_artigo (
    id                    INTEGER  PRIMARY KEY AUTOINCREMENT,

    codigo_artigo         TEXT     NOT NULL,
    descricao_artigo      TEXT     NOT NULL,

    fator                 REAL     NOT NULL
                              CHECK (fator > 0),

    data_inicio_vigencia  TEXT     NOT NULL,
    data_fim_vigencia     TEXT,

    observacao            TEXT,
    status                TEXT     NOT NULL
                              DEFAULT 'ativo'
                              CHECK (status IN ('ativo', 'cancelado')),
    motivo_cancelamento   TEXT,

    created_at            TEXT     NOT NULL
                              DEFAULT (datetime('now', 'localtime')),
    updated_at            TEXT     NOT NULL
                              DEFAULT (datetime('now', 'localtime')),
    cancelled_at          TEXT,

    CHECK (
        data_fim_vigencia IS NULL
        OR data_fim_vigencia > data_inicio_vigencia
    ),

    CHECK (
        (status = 'ativo'     AND motivo_cancelamento IS NULL  AND cancelled_at IS NULL)
        OR
        (status = 'cancelado' AND motivo_cancelamento IS NOT NULL AND cancelled_at IS NOT NULL)
    )
);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES ('002', 'Tabela principal fator_artigo com constraints de integridade');
