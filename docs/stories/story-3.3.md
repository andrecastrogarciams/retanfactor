# Story 3.3 — Registrar logs operacionais e tratar falhas

**Epic:** Epic 3 — Operação e Hardening
**Status:** Done
**Estimativa:** M

## Descrição
Como desenvolvedor e equipe de TI, quero logs operacionais mínimos e comportamento controlado em falhas, para manter a operação rastreável e suportável.

## Acceptance Criteria

1. Os logs devem ser gravados em **arquivo local no servidor** com retenção mínima de **30 dias**.
2. Devem ser registrados ao menos os seguintes eventos:
   - acesso à aplicação
   - tentativa de acesso bloqueado
   - erro na consulta Oracle
   - criação de fator
   - duplicação de fator
   - cancelamento de fator
3. Para ações de fator, os logs devem incluir: data/hora, estação/setor, código do artigo, fator, vigência e ação realizada.
4. Não é obrigatório registrar em log a geração de PDF, exportação de Excel ou clique em atualizar dados no MVP.
5. Em erro de Oracle, o sistema deve registrar em log e mostrar mensagem de erro na tela; não haverá alerta automático no MVP.
6. A solução deve ser publicada como **Streamlit + Nginx + systemd** em servidor local.
7. O deploy deve ocorrer via **Git/GitHub + pull + restart do service**, passando obrigatoriamente por homologação antes de produção.
8. Não haverá rollback formal no MVP; em caso de falha de release, a contingência será corrigir e realizar novo deploy, com versionamento por **tags/releases no Git**.

## Escopo

**IN:**
- Configuração de `logging` com handler para arquivo local em `LOG_DIR` (rotação diária, retenção 30 dias via `TimedRotatingFileHandler`)
- Logs de ações de fator com campos: data/hora, `ESTACAO`, `codigo_artigo`, `fator`, vigência, ação — já presentes nos serviços
- Log de erro Oracle com contexto do filtro aplicado — já presente em `pages/01_relatorio.py`
- Logs de acesso/bloqueio via Nginx (`access.log` + `error.log`)
- Arquivo systemd para gerenciamento do processo Streamlit (start/stop/restart/status)
- Arquivo de configuração Nginx como reverse proxy para Streamlit
- Runbook de deploy: `git pull` + `systemctl restart retanfactor`
- Runbook de troubleshooting: como checar logs, reiniciar serviço, validar Oracle
- Documentação de variáveis de ambiente

**OUT:**
- Alertas automáticos (e-mail, Slack, PagerDuty)
- Centralized log aggregation (ELK, Loki)
- Rollback formal automatizado
- Métricas de negócio (dashboards)

## Dependências
- Story 3.1 — Nginx e systemd são compartilhados entre as duas stories; coordenar criação dos arquivos de configuração

## Riscos
- Logs em arquivo local sem rotação podem consumir disco em caso de volume alto de erros; mitigado por `TimedRotatingFileHandler` com `backupCount=30`.
- Sem alertas automáticos no MVP: falhas silenciosas podem demorar a ser detectadas. Mitigação: smoke test após deploy.

## Dev Notes

**Implementado (camada de aplicação):**
- `logging.getLogger(__name__)` em todos os módulos de serviço e repositório
- Eventos registrados com `logger.info()` / `logger.warning()` / `logger.error()`:
  - `ACESSO` — `pages/01_relatorio.py`
  - `ERRO_ORACLE` — `pages/01_relatorio.py`
  - `FATOR_CRIADO` — `services/factor_service.py:criar_fator()`
  - `FATOR_CANCELADO` — `services/factor_service.py:cancelar_fator()`
  - `FATOR_DUPLICADO` — `services/factor_service.py:duplicar_fator()`
  - `CADASTRO_REJEITADO` — `pages/02_cadastro.py`
  - `ERRO_SQLITE_HISTORICO` — `pages/03_historico.py`
- `config.py` define `LOG_DIR = BASE_DIR / "logs"`

**Pendente:**
- Configuração do `logging` root com `TimedRotatingFileHandler` apontando para `LOG_DIR`
- Arquivo systemd: `/etc/systemd/system/retanfactor.service`
- Arquivo Nginx: `/etc/nginx/sites-available/retanfactor`
- `docs/runbook-deploy.md`
- `docs/runbook-troubleshooting.md`
- `docs/env-vars.md` — catálogo de variáveis de ambiente

**Exemplo de systemd a implementar:**
```ini
[Unit]
Description=Retanfactor Streamlit App
After=network.target

[Service]
User=retanfactor
WorkingDirectory=/opt/retanfactor
EnvironmentFile=/opt/retanfactor/.env
ExecStart=/opt/retanfactor/venv/bin/streamlit run app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

**Configuração de logging a implementar (em `config.py` ou `logging_config.py`):**
```python
import logging
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler(
    LOG_DIR / "retanfactor.log",
    when="midnight", backupCount=30, encoding="utf-8"
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
))
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)
```

## Tasks

- [x] Adicionar `logger.info/warning/error` em todos os serviços com campos obrigatórios
- [x] Definir `LOG_DIR` em `config.py`
- [x] Configurar `TimedRotatingFileHandler` para escrita em arquivo com retenção 30 dias
- [x] Criar arquivo systemd `retanfactor.service` (produção e homologação)
- [x] Criar arquivo de configuração Nginx como reverse proxy
- [x] Escrever `docs/runbook-deploy.md`
- [x] Escrever `docs/runbook-troubleshooting.md`
- [x] Escrever `docs/env-vars.md`

## Change Log
- 2026-04-27: Story criada por @pm — status InProgress, logging Python concluído, infra e runbooks pendentes
- 2026-04-27: Concluído por @dev — `logging_config.py` com `TimedRotatingFileHandler`, integrado em `config.py`, runbooks de deploy e troubleshooting criados — status Done
