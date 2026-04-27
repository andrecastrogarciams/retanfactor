# Story 1.4 — Exportar PDF e Excel

**Epic:** Epic 1 — Relatório Operacional Base
**Goal:** Como usuário do recurtimento, quero exportar o relatório em PDF e Excel, para que eu possa distribuir e arquivar a informação operacional no formato necessário.

## Acceptance Criteria
1. O PDF e o Excel devem exportar sempre as **linhas filtradas**, independentemente da seleção visual de linhas na grade.
2. O PDF e o Excel devem respeitar a **ordem atual das linhas** e a **visão atual das colunas** na tela, incluindo ocultações e reordenações feitas pelo usuário.
3. O PDF deve ser gerado em formato **retrato**, com quebra automática de páginas, e deve incluir em todas as páginas: **logo, título, data/hora de emissão e estação/setor**.
4. O PDF deve conter, no topo, o resumo com **total de linhas, média de % diferença e quantidade por faixa verde/amarelo/vermelho**.
5. O PDF deve repetir visualmente a cor da coluna `% diferença`.
6. O Excel deve exportar valores numéricos como **número**, não texto, incluindo as colunas calculadas com arredondamento em **2 casas decimais**.
7. Se a exportação falhar, a aplicação deve informar claramente ao usuário que o arquivo não foi gerado.
8. O PDF será aceito quando todas as páginas estiverem corretas conforme layout definido; o Excel será aceito quando os dados refletirem corretamente a visão filtrada e ordenada da tela.

---
*Documento gerado por @pm para refinamento por @sm.*
