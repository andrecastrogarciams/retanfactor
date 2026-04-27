# Story 2.3 — Consultar histórico de fatores

**Epic:** Epic 2 — Gestão de Fatores
**Status:** Done
**Estimativa:** M

## Descrição
Como usuário operacional, quero consultar o histórico de fatores, para que eu possa entender o que está vigente e o que já foi cadastrado anteriormente.

## Acceptance Criteria

1. A tela de histórico deve permitir visualizar a lista de fatores já cadastrados.
2. O histórico deve permitir pesquisar por **código do artigo**.
3. O histórico deve permitir filtrar por **período de vigência**.
4. O histórico deve permitir visualizar **somente vigentes**.
5. Registros antigos, inativos e até duplicidades acidentais já existentes no banco devem continuar visíveis no histórico.
6. A tela deve indicar claramente o status do registro, incluindo vigência aberta e cancelamento, quando aplicável — com indicadores visuais distintos (🟢 ativo / 🔴 cancelado).
7. Se a leitura do SQLite falhar, a tela deve informar o erro ao usuário sem exibir dados incoerentes.
8. O carregamento do histórico deve respeitar o ambiente atual da aplicação, sem cruzar dados de homologação e produção.

## Escopo

**IN:**
- Tela `pages/03_historico.py` — tabela de histórico com métricas (total, ativos, cancelados)
- Filtros no sidebar: código do artigo, somente vigentes, período de início/fim
- Destaque visual de linha por status (verde para ativo, vermelho para cancelado)
- `formatar_status()` — indicador emoji + texto descritivo de vigência aberta
- `formatar_vigencia()` — exibição `"YYYY-MM-DD → YYYY-MM-DD"` ou `"em aberto"`
- `fatores_para_dataframe()` — conversão de lista `FatorArtigo` para DataFrame com rótulos em português
- `listar_fatores()` em `factor_service.py` com 4 filtros opcionais

**OUT:**
- Edição inline de registros na tabela
- Paginação avançada (tabela renderizada via `st.dataframe` com `height=400`)
- Exportação do histórico para Excel/PDF

## Dependências
- Story 2.1 — registros de cadastro devem aparecer aqui imediatamente após criação
- Story 2.4 — ações de duplicação e cancelamento são realizadas a partir desta tela

## Riscos
- Volume muito alto de registros pode degradar a renderização do `st.dataframe`; aceitável no MVP com volume esperado baixo.

## Dev Notes

**Arquivos implementados:**
- `pages/03_historico.py` — `formatar_status()`, `formatar_vigencia()`, `fatores_para_dataframe()`, `_render_filtros()`, `_render_tabela()`
- `services/factor_service.py` — `listar_fatores()`, `buscar_fator()`
- `repositories/sqlite_repo.py` — `list_fatores()` com filtros: `codigo_artigo`, `apenas_vigentes`, `data_inicio_filtro`, `data_fim_filtro`

**Testes:**
- `tests/unit/test_historico_page.py` — 32 testes cobrindo `formatar_status`, `formatar_vigencia`, `fatores_para_dataframe`

## Tasks

- [x] Implementar `list_fatores()` com 4 filtros opcionais em `sqlite_repo.py`
- [x] Implementar `listar_fatores()` e `buscar_fator()` em `factor_service.py`
- [x] Implementar funções puras `formatar_status()`, `formatar_vigencia()`, `fatores_para_dataframe()`
- [x] Implementar `_render_filtros()` — sidebar com código, checkbox, datas
- [x] Implementar `_render_tabela()` — métricas + dataframe com destaque por status
- [x] Escrever e passar testes unitários das funções puras

## Change Log
- 2026-04-27: Story criada por @pm — status Done, implementação entregue por @dev
