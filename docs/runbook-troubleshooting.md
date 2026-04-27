# Runbook de Troubleshooting — Retanfactor

Referência rápida para diagnóstico e resolução dos problemas mais comuns em produção.

---

## Verificação Geral de Saúde

```bash
# Status dos serviços
sudo systemctl status retanfactor-prod retanfactor-hml nginx

# Últimas 50 linhas do log da aplicação
tail -50 /opt/retanfactor/logs/retanfactor.log

# Logs do systemd (tempo real)
sudo journalctl -u retanfactor-prod -f --no-pager
```

---

## Problemas Comuns

### 1. Aplicação inacessível (502 Bad Gateway no Nginx)

**Causa provável:** Streamlit não está rodando.

```bash
# Verificar se o processo Streamlit está ativo
sudo systemctl status retanfactor-prod

# Verificar se a porta está sendo escutada
ss -tlnp | grep 8501

# Reiniciar o serviço
sudo systemctl restart retanfactor-prod

# Confirmar subida
sudo journalctl -u retanfactor-prod -n 30 --no-pager
```

---

### 2. Acesso bloqueado (403 Forbidden no Nginx)

**Causa provável:** IP da máquina não está na allowlist do Nginx.

```bash
# Ver log de bloqueios
tail -100 /var/log/nginx/retanfactor_prod_error.log | grep "access forbidden"

# Identificar o IP da máquina cliente
# (pedir ao usuário ou checar no access.log)
tail -20 /var/log/nginx/retanfactor_prod_access.log

# Adicionar IP à allowlist
sudo nano /etc/nginx/sites-available/retanfactor
# Adicionar: allow <IP>;  antes do deny all;

sudo nginx -t && sudo systemctl reload nginx
```

---

### 3. Erro Oracle — relatório não carrega

**Causa provável:** Oracle indisponível, credenciais expiradas ou DSN incorreto.

```bash
# Verificar erros Oracle no log
grep "ERRO_ORACLE" /opt/retanfactor/logs/retanfactor.log | tail -20

# Testar conectividade com o servidor Oracle
ping <host-oracle>
telnet <host-oracle> <porta-oracle>

# Verificar variáveis de ambiente carregadas
sudo systemctl show retanfactor-prod --property=Environment
```

**Ação:**
- Se Oracle está down: aguardar restabelecimento; a aplicação exibe mensagem de erro ao usuário.
- Se credenciais expiraram: atualizar `/opt/retanfactor/.env.producao` e reiniciar o serviço.
- Se DSN incorreto: corrigir `ORACLE_DSN` no `.env.producao` e reiniciar.

```bash
sudo systemctl restart retanfactor-prod
```

---

### 4. Erro ao salvar fator (SQLite)

**Causa provável:** Permissão de escrita negada ou banco corrompido.

```bash
# Verificar erros SQLite no log
grep "ERRO_SQLITE\|OperationalError" /opt/retanfactor/logs/retanfactor.log | tail -20

# Verificar permissões do arquivo
ls -la /opt/retanfactor/data/

# Corrigir permissões se necessário
sudo chown retanfactor:retanfactor /opt/retanfactor/data/fatores_producao.db
sudo chmod 664 /opt/retanfactor/data/fatores_producao.db

# Testar integridade do banco
sqlite3 /opt/retanfactor/data/fatores_producao.db "PRAGMA integrity_check;"
```

**Se banco corrompido:** Reconstrução manual a partir do histórico (sem backup formal no MVP).

---

### 5. PDF não é gerado

**Causa provável:** ReportLab não instalado ou erro interno no serviço de exportação.

```bash
# Verificar se reportlab está instalado
/opt/retanfactor/venv/bin/pip show reportlab

# Reinstalar se necessário
/opt/retanfactor/venv/bin/pip install reportlab>=4.0.0

# Reiniciar após instalar dependência
sudo systemctl restart retanfactor-prod
```

> Lembrar: PDF é desabilitado em homologação por padrão (ADR-005).

---

### 6. Serviço não inicia após deploy

**Causa provável:** Erro de sintaxe em código Python, dependência faltando ou variável de ambiente ausente.

```bash
# Ver causa do erro de inicialização
sudo journalctl -u retanfactor-prod -n 100 --no-pager

# Testar manualmente (substituir pelas variáveis reais)
cd /opt/retanfactor
source .env.producao
venv/bin/python -c "import config; print('OK')"

# Verificar dependências
venv/bin/pip install -r requirements.txt
```

---

### 7. Logs de aplicação não são gerados

**Causa provável:** Permissão negada no diretório de logs ou `LOG_DIR` inexistente.

```bash
# Verificar se o diretório existe e tem permissão
ls -la /opt/retanfactor/logs/

# Criar e corrigir permissões
mkdir -p /opt/retanfactor/logs
chown retanfactor:retanfactor /opt/retanfactor/logs
chmod 755 /opt/retanfactor/logs

sudo systemctl restart retanfactor-prod
```

---

## Rotação de Logs

A aplicação usa `TimedRotatingFileHandler` com rotação diária e retenção de 30 dias.
Arquivos rotacionados ficam em `/opt/retanfactor/logs/retanfactor.log.YYYY-MM-DD`.

```bash
# Listar arquivos de log
ls -lh /opt/retanfactor/logs/

# Buscar evento específico em todos os arquivos
grep "FATOR_CANCELADO" /opt/retanfactor/logs/retanfactor.log*

# Ver log de um dia específico
cat /opt/retanfactor/logs/retanfactor.log.2026-04-01
```

---

## Contatos e Escalação

| Situação | Responsável |
|----------|-------------|
| Oracle fora do ar | TI interna — suporte Oracle |
| Servidor inacessível | TI interna — infra local |
| Bug na aplicação | Desenvolvedor responsável |
| Allowlist de IP | TI interna — configuração Nginx |
