#!/bin/bash
# Script de Atualização RetanFactor

echo "🚀 Iniciando deploy..."

cd /var/www/retanfactor

# 1. Sincronizar com repositório (PRD Story 3.3 AC7)
git pull origin main

# 2. Atualizar dependências
./deploy/env/bin/pip install -r requirements.txt

# 3. Reiniciar serviço (Auto-Recuperação)
sudo systemctl restart retanfactor

echo "✅ Deploy concluído com sucesso!"
