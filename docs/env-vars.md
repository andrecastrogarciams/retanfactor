# Variáveis de Ambiente — Retanfactor

Todas as variáveis são lidas de arquivos `.env` carregados pelo systemd via `EnvironmentFile`.
Os arquivos de exemplo estão em `deploy/env/`.

---

## Variáveis de Aplicação

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `APP_ENV` | Não | `producao` | Identifica o ambiente. Valores: `producao`, `homologacao`. Controla banner de aviso, habilitação do PDF e nome do banco SQLite. |
| `ESTACAO` | Não | `RECURTIMENTO` | Nome da estação/setor exibido em todas as telas e no cabeçalho do PDF. Configurado por instância. |
| `SQLITE_DB_PATH` | Não | `data/fatores_{APP_ENV}.db` | Caminho absoluto do banco SQLite. Se vazio, usa o caminho padrão relativo ao projeto. |

---

## Variáveis Oracle

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `ORACLE_DSN` | Sim | `""` | Data Source Name no formato `host:port/service_name`. |
| `ORACLE_USER` | Sim | `""` | Usuário Oracle para conexão. |
| `ORACLE_PASSWORD` | Sim | `""` | Senha Oracle. Nunca versionar. |
| `ORACLE_TIMEOUT_SECONDS` | Não | `30` | Tempo máximo de espera da consulta Oracle em segundos. |

---

## Comportamento por APP_ENV

| Comportamento | `producao` | `homologacao` |
|---------------|-----------|---------------|
| Banner de aviso | Não exibido | Banner vermelho em todas as telas |
| Exportação PDF | Habilitada | **Desabilitada** (ADR-005) |
| Banco SQLite | `data/fatores_producao.db` | `data/fatores_homologacao.db` |
| Oracle | Produção | Produção (mesma base — atenção a testes) |
| Porta Streamlit | 8501 | 8502 |
| Nginx (porta externa) | 80 | 8080 |

---

## Segredos — Boas Práticas

- Nunca versionar arquivos `.env` com valores reais no Git.
- Os arquivos `deploy/env/*.example` são templates sem valores reais.
- No servidor, proteger os arquivos com permissão restrita:
  ```bash
  chmod 600 /opt/retanfactor/.env.producao
  chmod 600 /opt/retanfactor/.env.homologacao
  chown retanfactor:retanfactor /opt/retanfactor/.env.*
  ```
- Credenciais Oracle devem ser fornecidas somente via `EnvironmentFile` — nunca por argumento de linha de comando ou código-fonte.

---

## Verificação Rápida

Para confirmar que as variáveis foram carregadas corretamente pelo serviço:

```bash
# Ver variáveis do processo em execução
sudo systemctl show retanfactor-prod --property=Environment

# Ou inspecionar via journald
sudo journalctl -u retanfactor-prod | grep "ESTACAO\|APP_ENV"
```
