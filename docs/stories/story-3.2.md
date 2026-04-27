# Story 3.2 — Aplicar cache temporário com atualização forçada

**Epic:** Epic 3 — Operação e Hardening
**Status:** Done
**Estimativa:** S

## Descrição
Como usuário operacional, quero que a aplicação use cache temporário e também permita atualização imediata, para equilibrar desempenho e atualidade dos dados.

## Acceptance Criteria

1. O relatório deve usar cache temporário com **TTL de 5 minutos**.
2. A tela do relatório deve exibir botão **Atualizar dados** para forçar nova consulta e invalidar o cache funcional da consulta.
3. Após salvar, duplicar ou inativar um fator, o relatório deve refletir imediatamente a nova regra aplicável, sem aguardar expiração natural do cache.
4. O cache não deve mascarar erro Oracle: se a consulta em tempo real falhar no refresh forçado, o sistema deve mostrar erro e não apresentar dado obsoleto como atual.
5. O uso de cache deve ser transparente ao usuário, sem exigir ação manual para o fluxo normal de consulta.
6. Se a invalidação do cache falhar, o sistema deve registrar o erro e informar que os dados podem não refletir a última alteração.
7. O comportamento do cache deve ser consistente entre homologação e produção.
8. A interface deve informar visualmente quando os dados forem recarregados com sucesso após atualização forçada.

## Escopo

**IN:**
- `ReportCache` em `services/report_service.py` — TTL 5 min, `get()`, `set()`, `invalidate()`, `make_key()`
- Parâmetro `force_refresh` em `get_relatorio()` — invalida cache antes da consulta quando `True`
- Botão "Atualizar dados" em `pages/01_relatorio.py` — passa `force_refresh=True`
- Feedback visual: mensagem de sucesso com timestamp após refresh forçado (AC8)
- Invalidação funcional chamada por `criar_fator()`, `cancelar_fator()` e `duplicar_fator()` (AC3)
- Parâmetro `cache` injetável em `get_relatorio()` para isolamento em testes (AC7 via teste)
- Erro Oracle propagado mesmo com cache preenchido (AC4)

**OUT:**
- Cache persistido em disco ou Redis
- Invalidação seletiva por artigo (invalida todo o cache na mutação)
- Configuração de TTL por usuário

## Dependências
- Story 1.1 — cache é parte do fluxo de consulta do relatório
- Story 2.1/2.4 — invalidação é disparada pelas ações de gestão de fatores

## Riscos
- Cache em memória por sessão Streamlit significa que múltiplas sessões simultâneas têm caches independentes; invalidação após salvar fator atinge apenas a sessão que executou a ação. Impacto baixo no MVP com poucos usuários simultâneos.

## Dev Notes

**Arquivos implementados:**
- `services/report_service.py` — `ReportCache`, `get_cache()`, `get_relatorio(force_refresh, cache=None)`
- `services/factor_service.py` — `criar_fator()`, `cancelar_fator()`, `duplicar_fator()` chamam `get_cache().invalidate()`
- `pages/01_relatorio.py` — botão "Atualizar dados", `force_refresh` passado para `get_relatorio()`, feedback visual com timestamp

**Padrão de injeção de cache para testes:**
```python
# Em testes: cache local isolado por teste
local_cache = ReportCache(ttl_seconds=60)
resultado = get_relatorio(..., cache=local_cache)
```

**Testes:**
- `tests/unit/test_report_service.py` — casos: cache HIT, cache MISS, force_refresh invalida cache, erro Oracle propagado mesmo em segundo chamada, TTL expira

## Tasks

- [x] Implementar `ReportCache` com TTL, `get()`, `set()`, `invalidate()`, `make_key()`
- [x] Adicionar parâmetro `cache` injetável em `get_relatorio()`
- [x] Adicionar parâmetro `force_refresh` em `get_relatorio()`
- [x] Adicionar botão "Atualizar dados" em `pages/01_relatorio.py`
- [x] Implementar feedback visual com timestamp após refresh forçado
- [x] Integrar `get_cache().invalidate()` em `criar_fator()`, `cancelar_fator()`, `duplicar_fator()`
- [x] Escrever e passar testes de cache (hit, miss, force_refresh, isolamento)

## Change Log
- 2026-04-27: Story criada por @pm — status Done, implementação entregue por @dev
