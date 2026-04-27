# 📘 Manual de Operações Técnicas - RetanFactor (SmartLeather)

Este documento detalha o procedimento de instalação, segurança e manutenção do sistema RetanFactor em ambiente de produção (Linux).

## 🏗️ 1. Arquitetura e Stack
- **Interface:** Streamlit (Python 3.13+)
- **Banco Local:** SQLite (Fatores e Vigências)
- **Integração:** View Oracle (Modo Thin - sem necessidade de Instant Client)
- **Proxy:** Nginx
- **Gerenciamento:** systemd

---

## 🚀 2. Instalação Passo-a-Passo

### 2.1 Preparação
Clone o repositório no diretório de destino (padrão: `/var/www/retanfactor`):
```bash
cd /var/www
git clone https://github.com/andrecastrogarciams/retanfactor.git
cd retanfactor
```

### 2.2 Ambiente Python
Crie e prepare o Virtualenv:
```bash
python3 -m venv deploy/env
./deploy/env/bin/pip install -r requirements.txt
```

### 2.3 Configuração (.env)
O sistema exige as seguintes chaves preenchidas no `.env`:
- `ORACLE_DSN`: Host:Port/Service_Name
- `ORACLE_USER`: Usuário de leitura
- `ORACLE_PASSWORD`: Senha do usuário
- `APP_ENV`: "producao" (habilita PDF)
- `ESTACAO`: Nome para exibição no relatório

---

## 🛡️ 3. Segurança e Infraestrutura

### 3.1 Auto-Recuperação (systemd)
O sistema reinicia automaticamente em caso de falha ou reboot do servidor:
```bash
sudo ln -s /var/www/retanfactor/deploy/systemd/retanfactor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable retanfactor
sudo systemctl start retanfactor
```

### 3.2 Controle de Acesso (Nginx Allowlist)
A aplicação deve ser acessada apenas por computadores liberados.
1. Edite `deploy/nginx/retanfactor.conf`.
2. Adicione os IPs permitidos usando a diretiva `allow <IP>;`.
3. Aplique a configuração:
```bash
sudo ln -s /etc/nginx/sites-available/retanfactor.conf /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## 📋 4. Manutenção e Monitoramento

### 4.1 Logs Operacionais
Os logs estão localizados na pasta `./logs/`:
- `streamlit.log`: Erros da aplicação e acessos.
- `nginx_access.log`: Auditoria de origem de IP.

### 4.2 Atualização do Sistema
Sempre que houver mudanças no GitHub, execute o script de deploy automatizado:
```bash
bash deploy/deploy.sh
```

---
*Gerado automaticamente pelo agente @devops - Gage.*
