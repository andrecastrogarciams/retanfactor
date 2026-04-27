# Story 2.2 — Bloquear sobreposição de vigência

**Epic:** Epic 2 — Gestão de Fatores
**Status:** Done
**Estimativa:** M

## Descrição
Como usuário operacional, quero que o sistema impeça sobreposição de vigência para o mesmo código do artigo, para evitar ambiguidade no cálculo.

## Acceptance Criteria

1. O sistema deve validar, antes da gravação, se já existe vigência sobreposta para o mesmo código do artigo.
2. A regra de sobreposição deve considerar tanto registros com data fim definida quanto vigência em aberto.
3. Se houver tentativa de sobreposição, o sistema deve bloquear a gravação e exibir mensagem clara de erro ao usuário.
4. O registro inválido não deve ser persistido parcialmente no SQLite.
5. A tentativa de gravação rejeitada por sobreposição deve ser registrada em log técnico.
6. O bloqueio será considerado aceito quando toda tentativa de sobreposição for impedida consistentemente.
7. Em caso de falha no acesso ao SQLite durante a validação, o sistema deve cancelar a operação e exibir erro ao usuário.
8. A validação deve ser aplicada tanto no cadastro novo quanto na duplicação de fator.

## Escopo

**IN:**
- `has_vigencia_overlap()` em `sqlite_repo.py` — query com `COALESCE(data_fim_vigencia, '9999-12-31')` como sentinela
- Integração da validação em `insert_fator()` (transacional, sem persistência parcial)
- Integração na duplicação via `duplicate_fator()` que reutiliza `insert_fator()`
- Exceção `ValueError` com mensagem clara propagada até a UI
- Log técnico de rejeição

**OUT:**
- Edição retroativa de vigências existentes
- Resolução automática de conflitos
- Exclusão de registros em sobreposição

## Dependências
- Story 2.1 — a validação é parte do fluxo de criação de fator
- Story 2.4 — a mesma validação deve ser aplicada na duplicação (AC8)

## Riscos
- Inconsistências preexistentes no banco (importação manual) não são bloqueadas retroativamente; o sistema apenas bloqueia novas entradas sobrepostas.

## Dev Notes

**Implementação central:**
- `repositories/sqlite_repo.py:has_vigencia_overlap()` — usa sentinela `'9999-12-31'` via `COALESCE` para tratar vigência aberta no comparativo SQL
- `repositories/sqlite_repo.py:insert_fator()` — chama `has_vigencia_overlap()` dentro de transação; levanta `ValueError` em sobreposição detectada
- `repositories/sqlite_repo.py:duplicate_fator()` — delega para `insert_fator()`, herda a mesma validação

**Testes:**
- `tests/unit/test_sqlite_repo.py` — casos de sobreposição: fechada-fechada, fechada-aberta, aberta-aberta, sem sobreposição válida, exclusão de próprio ID

## Tasks

- [x] Implementar `has_vigencia_overlap()` com sentinela COALESCE
- [x] Integrar validação em `insert_fator()` com transação atômica
- [x] Garantir que `duplicate_fator()` herda a validação via `insert_fator()`
- [x] Escrever e passar testes de sobreposição (casos borda: aberta, fechada, autoexclusão)

## Change Log
- 2026-04-27: Story criada por @pm — status Done, implementação entregue por @dev
