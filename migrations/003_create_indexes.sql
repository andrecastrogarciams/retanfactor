-- Covering index para a query crítica Q1 (busca de fator vigente por artigo + data)
CREATE INDEX IF NOT EXISTS idx_fa_vigencia_lookup
    ON fator_artigo (codigo_artigo, status, data_inicio_vigencia, data_fim_vigencia);

-- Índice para tela de histórico (filtro por artigo, ordenado por criação)
CREATE INDEX IF NOT EXISTS idx_fa_historico
    ON fator_artigo (codigo_artigo, created_at DESC);

-- Índice para filtro "somente vigentes"
CREATE INDEX IF NOT EXISTS idx_fa_status
    ON fator_artigo (status);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES ('003', 'Indices de performance para consulta de vigencia e historico');
