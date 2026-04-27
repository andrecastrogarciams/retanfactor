# Story 2.1 — Cadastrar novo fator com vigência

**Epic:** Epic 2 — Gestão de Fatores
**Status:** Done
**Estimativa:** M

## Descrição
Como usuário operacional, quero cadastrar um novo fator por código do artigo, para que os cálculos do relatório usem a regra vigente correta.

## Acceptance Criteria

1. O cadastro deve conter os campos: **código do artigo, descrição do artigo, fator, data início de vigência, data fim de vigência e observação**.
2. A lista de produtos para seleção deve vir da view Oracle `USU_VBI_ARTIGOS_SEMI_NOA`; se Oracle indisponível, campos de texto manual com aviso.
3. O vínculo funcional entre produto e fator deve ocorrer pelo **código do artigo**.
4. O campo `fator` não pode aceitar valor zero nem negativo.
5. A data fim de vigência pode ser vazia, significando vigência em aberto.
6. Ao salvar um fator válido, o registro deve ser persistido no SQLite em até **3 segundos** e deve aparecer imediatamente no histórico.
7. Após salvar um fator válido, ele deve passar a ser considerado imediatamente no relatório, sem aguardar expiração do cache.
8. A ação de criação deve ser registrada em log com data/hora, estação/setor, código do artigo, fator, vigência e ação realizada.

## Escopo

**IN:**
- Formulário de cadastro em `pages/02_cadastro.py`
- Validação de formulário: código, descrição, fator > 0, data início obrigatória, data fim posterior ao início
- Construção do objeto `FatorArtigo` e persistência via `services/factor_service.py` → `criar_fator()`
- Seletor de artigo Oracle com fallback para campos manuais
- Invalidação de cache do relatório após salvar
- Log de criação com metadados obrigatórios

**OUT:**
- Edição de fator existente (sem edição no MVP)
- Exclusão física de registros
- Autenticação/perfis de usuário

## Dependências
- Story 1.3 — fator deve estar disponível para cálculo imediato após salvar
- Story 3.2 — invalidação de cache após mudança de fator

## Riscos
- Oracle indisponível: fallback para entrada manual garante continuidade, mas código pode ser digitado incorretamente.
- Observação sem obrigatoriedade explícita travada no MVP (campo disponível, não obrigatório).

## Dev Notes

**Arquivos implementados:**
- `pages/02_cadastro.py` — UI do formulário, `validar_formulario()`, `construir_fator_artigo()`
- `services/factor_service.py` — `criar_fator()`, `_validar_fator()`
- `repositories/sqlite_repo.py` — `insert_fator()`, `has_vigencia_overlap()`

**Testes:**
- `tests/unit/test_cadastro_page.py` — 22 testes (validação + construção de fator)
- `tests/unit/test_factor_service.py` — cobertura de `criar_fator()`
- `tests/unit/test_sqlite_repo.py` — cobertura de `insert_fator()`

## Tasks

- [x] Implementar `validar_formulario()` — validação pura de campos
- [x] Implementar `construir_fator_artigo()` — builder puro do modelo
- [x] Implementar `_render_seletor_artigo()` — Oracle selectbox + fallback manual
- [x] Implementar `criar_fator()` em `factor_service.py`
- [x] Integrar invalidação de cache em `factor_service.criar_fator()`
- [x] Escrever e passar testes unitários

## Change Log
- 2026-04-27: Story criada por @pm — status Done, implementação entregue por @dev
