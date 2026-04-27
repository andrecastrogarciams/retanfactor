# Runbook de Deploy — Retanfactor

Processo de deploy via Git + systemd. Todo deploy passa **obrigatoriamente** por homologação antes de produção (AC Story 3.3).

---

## Pré-requisitos

- Acesso SSH ao servidor com usuário `retanfactor` ou sudo
- Git configurado no servidor com acesso ao repositório
- Python venv em `/opt/retanfactor/venv`
- Arquivos `.env.producao` e `.env.homologacao` em `/opt/retanfactor/`
- Serviços systemd registrados: `retanfactor-prod` e `retanfactor-hml`
- Nginx configurado com `retanfactor.conf`

---

## 1. Deploy em Homologação

```bash
# 1. Acessar o servidor
ssh usuario@servidor-retanfactor

# 2. Entrar no diretório da aplicação
cd /opt/retanfactor

# 3. Baixar as atualizações
git fetch origin
git pull origin main

# 4. Atualizar dependências (se requirements.txt mudou)
venv/bin/pip install -r requirements.txt --quiet

# 5. Reiniciar o serviço de homologação
sudo systemctl restart retanfactor-hml

# 6. Verificar status
sudo systemctl status retanfactor-hml
```

### Smoke test em homologação

```bash
# Verificar se o serviço subiu
curl -s http://localhost:8502/healthz

# Verificar logs por erros imediatos
sudo journalctl -u retanfactor-hml -n 50 --no-pager

# Verificar log da aplicação
tail -50 /opt/retanfactor/logs/retanfactor.log
```

Validar manualmente no browser:
- [ ] Tela do relatório abre com banner de HOMOLOGAÇÃO visível
- [ ] Filtros funcionam e retornam dados (mesmo que Oracle de produção)
- [ ] Tela de cadastro abre sem erro
- [ ] Histórico de fatores carrega
- [ ] Botão "Exportar PDF" está **desabilitado** (ambiente homologação)
- [ ] Botão "Exportar Excel" funciona

---

## 2. Deploy em Produção

Executar **somente após smoke test em homologação aprovado**.

```bash
# 1. Reiniciar o serviço de produção
sudo systemctl restart retanfactor-prod

# 2. Verificar status
sudo systemctl status retanfactor-prod

# 3. Monitorar logs por 2-3 minutos
sudo journalctl -u retanfactor-prod -f
```

### Smoke test em produção

```bash
curl -s http://localhost:8501/healthz
tail -20 /opt/retanfactor/logs/retanfactor.log
```

Validar no browser (máquina autorizada):
- [ ] Tela abre **sem** banner de aviso (ambiente produção)
- [ ] Dados Oracle carregam normalmente
- [ ] Botão "Exportar PDF" está habilitado
- [ ] Cadastro de fator funciona

---

## 3. Tagear o Release no Git

Após deploy bem-sucedido em produção (AC Story 3.3):

```bash
# No repositório local ou CI
git tag -a v1.x.x -m "Release v1.x.x — <descrição resumida>"
git push origin v1.x.x
```

---

## 4. Contingência — Falha de Release

Não há rollback formal. Procedimento em caso de falha:

1. Identificar o commit estável anterior: `git log --oneline -10`
2. Reverter para o commit estável:
   ```bash
   git checkout <commit-hash>
   sudo systemctl restart retanfactor-prod
   ```
3. Corrigir o problema no código
4. Abrir novo PR → merge → refazer o processo do passo 1

---

## Estrutura de Arquivos no Servidor

```
/opt/retanfactor/
├── venv/                    # Python virtualenv
├── pages/                   # Páginas Streamlit
├── services/                # Serviços de negócio
├── repositories/            # Repositórios SQLite/Oracle
├── migrations/              # Migrations SQLite
├── data/
│   ├── fatores_producao.db  # SQLite produção
│   └── fatores_homologacao.db
├── logs/
│   └── retanfactor.log      # Log da aplicação (rotação diária, 30 dias)
├── docs/logo/               # Logo institucional
├── .env.producao            # Variáveis de ambiente produção (chmod 600)
├── .env.homologacao         # Variáveis de ambiente homologação (chmod 600)
└── requirements.txt
```

---

## Comandos Úteis

```bash
# Status dos serviços
sudo systemctl status retanfactor-prod retanfactor-hml

# Reiniciar ambos
sudo systemctl restart retanfactor-prod retanfactor-hml

# Ver logs em tempo real
sudo journalctl -u retanfactor-prod -f
sudo journalctl -u retanfactor-hml -f

# Verificar configuração Nginx
sudo nginx -t

# Recarregar Nginx sem downtime
sudo systemctl reload nginx
```
