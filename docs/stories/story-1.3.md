# Story 1.3 — Calcular peso, densidade e desvio

**Epic:** Epic 1 — Relatório Operacional Base
**Goal:** Como usuário do recurtimento, quero que o sistema calcule automaticamente os valores derivados com base no fator vigente, para que eu não precise fazer conta manual no Excel.

## Acceptance Criteria
1. O sistema deve identificar o fator vigente pelo **código do artigo** e pela **data de recurtimento** da linha.
2. O peso calculado deve seguir a fórmula: `m² × 10,764 × fator × 0,092903`, com arredondamento para **2 casas decimais**.
3. O campo `kg/m²` deve ser calculado como `peso do lote / m²`, com arredondamento para **2 casas decimais**.
4. O campo `kg/ft²` deve ser calculado como `peso do lote / (m² × 10,764)`, com arredondamento para **2 casas decimais**.
5. O campo `% diferença` deve ser calculado por `(peso real - peso calculado) / peso calculado × 100`, com arredondamento para **2 casas decimais**.
6. Se não existir fator para o código do artigo, se a data estiver fora de qualquer vigência, se `m² = 0`, se `peso do lote = 0` ou se a data de vigência for inválida/nula, os campos calculados devem permanecer em **branco**.
7. Se houver mais de um fator válido por inconsistência preexistente no banco, o sistema deve usar o **registro mais recente** e registrar a ocorrência em log técnico.
8. Após o cálculo, a coluna `% diferença` deve aplicar cor por valor absoluto conforme as faixas verde, amarelo e vermelho definidas no produto.

---
*Documento gerado por @pm para refinamento por @sm.*
