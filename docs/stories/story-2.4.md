# Story 2.4 — Duplicar e inativar fator

**Epic:** Epic 2 — Gestão de Fatores
**Status:** Done
**Estimativa:** M

## Descrição
Como usuário operacional, quero duplicar um fator e também inativar um fator existente, para facilitar nova vigência e controlar registros que não devem mais ser usados.

## Acceptance Criteria

1. Ao clicar em **Duplicar fator**, os campos **código do artigo, descrição, fator e observação** devem vir pré-preenchidos, enquanto **início e fim de vigência** devem permanecer em branco.
2. A duplicação deve reaproveitar os dados do registro original sem alterar o registro de origem.
3. Ao inativar/cancelar um fator, o usuário deve informar **motivo obrigatório**.
4. O motivo do cancelamento deve ser salvo no SQLite em campo próprio `motivo_cancelamento`.
5. A observação do cadastro inicial pode ser reaproveitada na duplicação, mas o motivo do cancelamento deve ser persistido como informação distinta.
6. O cancelamento/inativação deve remover o fator das consultas futuras imediatamente, sem reescrever historicamente os dados Oracle.
7. A ação de duplicação e a ação de cancelamento devem ser registradas em log com seus metadados obrigatórios.
8. Se o SQLite falhar durante duplicação ou cancelamento, a aplicação deve abortar a operação e informar o erro ao usuário.

## Escopo

**IN:**
- Formulário de duplicação na tela de histórico: selectbox de registros ativos, pré-visualização do registro selecionado, campos de nova vigência em branco
- Validação de duplicação: `validar_duplicacao()` — fator_id obrigatório, origem não pode ser cancelada, data_inicio obrigatória, data_fim posterior ao início
- Formulário de cancelamento na tela de histórico: selectbox de registros ativos, campo `motivo` obrigatório
- Validação de cancelamento: `validar_cancelamento()` — fator_id obrigatório, motivo não pode ser vazio/espaços, fator não pode já estar cancelado
- `duplicar_fator()` em `factor_service.py` — valida data_inicio, chama `duplicate_fator()` em `sqlite_repo.py`, invalida cache
- `cancelar_fator()` em `factor_service.py` — chama `cancel_fator()` em `sqlite_repo.py`, invalida cache
- `cancel_fator()` em `sqlite_repo.py` — transacional: UPDATE status → 'cancelado', preenche `motivo_cancelamento` e `cancelled_at`
- `duplicate_fator()` em `sqlite_repo.py` — lê registro original, cria cópia com nova vigência via `insert_fator()`
- `st.rerun()` após operação bem-sucedida para atualizar histórico
- Log de duplicação e cancelamento com metadados

**OUT:**
- Edição retroativa do motivo após cancelamento
- Reativação de fator cancelado
- Cancelamento em lote
- Exclusão física de registros

## Dependências
- Story 2.2 — duplicação passa pela mesma validação de sobreposição (AC8 de Story 2.2)
- Story 2.3 — ações realizadas a partir da tela de histórico

## Riscos
- Falha parcial no cancelamento (atualização iniciada mas não commitada) levaria a estado inconsistente; mitigado pelo uso de transação SQLite com rollback automático.
- Seleção de registro errado para cancelamento é irreversível no MVP — mitigado pela pré-visualização do registro selecionado no formulário de duplicação.

## Dev Notes

**Arquivos implementados:**
- `pages/03_historico.py` — `validar_duplicacao()`, `validar_cancelamento()`, `_render_form_duplicacao()`, `_render_form_cancelamento()`
- `services/factor_service.py` — `duplicar_fator()`, `cancelar_fator()`
- `repositories/sqlite_repo.py` — `cancel_fator()`, `duplicate_fator()`

**Padrão transacional:**
`cancel_fator()` usa `conn.execute()` dentro de `try/except` com rollback explícito — garante atomicidade e evita cancelamento parcial (AC8).

**Testes:**
- `tests/unit/test_historico_page.py` — 16 testes cobrindo `validar_duplicacao` e `validar_cancelamento` (casos: fator_id None, origem cancelada, data inválida, motivo vazio/espaços)
- `tests/unit/test_factor_service.py` — cobertura de `duplicar_fator()` e `cancelar_fator()`
- `tests/unit/test_sqlite_repo.py` — cobertura de `cancel_fator()` e `duplicate_fator()`

## Tasks

- [x] Implementar `cancel_fator()` em `sqlite_repo.py` — transacional com motivo obrigatório
- [x] Implementar `duplicate_fator()` em `sqlite_repo.py` — copia campos e delega para `insert_fator()`
- [x] Implementar `cancelar_fator()` e `duplicar_fator()` em `factor_service.py` com invalidação de cache e logs
- [x] Implementar `validar_duplicacao()` — validação pura do formulário de duplicação
- [x] Implementar `validar_cancelamento()` — validação pura do formulário de cancelamento
- [x] Implementar `_render_form_duplicacao()` — selectbox de ativos + pré-visualização + campos de nova vigência
- [x] Implementar `_render_form_cancelamento()` — selectbox de ativos + motivo obrigatório
- [x] Escrever e passar testes unitários das funções de validação

## Change Log
- 2026-04-27: Story criada por @pm — status Done, implementação entregue por @dev
