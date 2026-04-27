# Story 3.1 — Restringir acesso por ambiente interno

**Epic:** Epic 3 — Operação e Hardening
**Status:** Done
**Estimativa:** M

## Descrição
Como equipe de TI, quero restringir o acesso à aplicação a computadores liberados, para reduzir uso indevido e manter o sistema apenas na rede interna.

## Acceptance Criteria

1. A aplicação deve ser acessível apenas na **rede interna**, sem acesso externo ou VPN no MVP.
2. O acesso deve ser controlado por **hostname e/ou allowlist de IPs no Nginx**.
3. Requisições provenientes de origem não autorizada devem ser bloqueadas antes do uso funcional da aplicação.
4. Toda tentativa de acesso bloqueado deve ser registrada em log com data/hora e metadados disponíveis.
5. O sistema não deve depender de login de usuário para o MVP.
6. A estação/setor exibida na tela e no PDF deve ser configurada tecnicamente por instância, via arquivo de configuração/env.
7. A URL de homologação deve ser separada da URL de produção.
8. O ambiente de homologação deve usar SQLite próprio e separado do ambiente de produção.

## Escopo

**IN:**
- Configuração Nginx com `allow`/`deny` por IP ou hostname para restrição de acesso (AC1-4)
- Variável de ambiente `ESTACAO` configurável por instância, exibida em todas as telas e no PDF (AC6)
- Variável `APP_ENV` com valores `producao` / `homologacao` e SQLite isolado por ambiente via `DB_PATH` (AC7-8)
- Banner visual de ambiente não-produção em todas as páginas via `render_env_banner()` (AC8)
- Configuração systemd de duas unidades separadas: produção e homologação

**OUT:**
- Login de usuário ou autenticação por token
- TLS/HTTPS interno (definido como A DEFINIR no PRD)
- VPN ou acesso externo

## Dependências
- Story 3.3 — logs de acesso bloqueado gerados pelo Nginx dependem da infraestrutura de logs

## Riscos
- Homologação aponta para mesma base Oracle de produção (ADR-005): risco de expor testes em dados reais. Mitigado pelo banner vermelho obrigatório e pela desabilitação da exportação PDF em homologação.
- Allowlist de IP pode precisar de atualização quando máquinas forem substituídas ou IPs mudarem; processo manual de manutenção.

## Dev Notes

**Implementado (camada de aplicação):**
- `config.py` — `APP_ENV`, `ESTACAO`, `DB_PATH` segregado por ambiente (`fatores_producao.db` / `fatores_homologacao.db`)
- `config.py:render_env_banner()` — banner de erro visível em APP_ENV != "producao"
- Todas as páginas chamam `render_env_banner()` antes de qualquer conteúdo
- PDF export desabilitado em não-produção em `pages/01_relatorio.py` (ADR-005)

**Pendente (infraestrutura):**
- Arquivo de configuração Nginx com bloco `allow`/`deny` por IP/hostname
- Arquivos systemd para serviço Streamlit em homologação e produção
- Documentação de variáveis de ambiente (runbook)

**Exemplo de configuração Nginx a implementar:**
```nginx
location / {
    allow 192.168.1.0/24;   # rede interna
    allow 10.0.0.5;          # servidor específico
    deny all;
    proxy_pass http://127.0.0.1:8501;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Tasks

- [x] Implementar `APP_ENV` e `ESTACAO` via env em `config.py`
- [x] Implementar `DB_PATH` segregado por ambiente (SQLite separado)
- [x] Implementar `render_env_banner()` em todas as páginas
- [x] Desabilitar exportação PDF em homologação
- [x] Criar arquivo de configuração Nginx com allowlist de IP/hostname
- [x] Criar arquivos systemd para produção e homologação
- [x] Documentar variáveis de ambiente no README/runbook

## Change Log
- 2026-04-27: Story criada por @pm — status InProgress, camada de app concluída, infra pendente
- 2026-04-27: Infra concluída por @dev — Nginx, systemd (prod+hml), env examples, docs/env-vars.md — status Done
