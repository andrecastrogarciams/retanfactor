# Story 1.2 — Visualizar dados em AgGrid com interações analíticas

**Epic:** Epic 1 — Relatório Operacional Base
**Goal:** Como usuário do recurtimento, quero visualizar os dados em uma grade interativa, para que eu possa ordenar, reorganizar e analisar o relatório com agilidade.

## Acceptance Criteria
1. A tabela deve usar **AgGrid** e permitir: ordenação por coluna, redimensionamento, ocultar/mostrar colunas, reordenar colunas, paginação e seleção de linhas.
2. A seleção de linhas deve ser apenas **visual** e não deve alterar o comportamento padrão das exportações.
3. A tela deve exibir, na ordem padrão inicial, as colunas:
   1. data de recurtimento  
   2. artigo  
   3. cor  
   4. lote de fabricação  
   5. código do artigo  
   6. m²  
   7. peso do lote  
   8. kg/m²  
   9. kg/ft²  
   10. fator aplicado  
   11. peso calculado  
   12. % diferença
4. O usuário deve poder ocultar e reordenar colunas na visualização atual sem reiniciar a sessão da tela.
5. Se uma coluna vier nula na view Oracle, a aplicação deve exibir o campo como vazio, sem erro visual de renderização.
6. A paginação deve funcionar com o conjunto filtrado, sem duplicar linhas e sem alterar a integridade da ordenação aplicada.
7. Quando a consulta terminar com sucesso, a interface deve indicar claramente que os dados foram carregados.
8. Em caso de falha de renderização da grade, a aplicação deve exibir erro ao usuário e registrar o problema em log.

---
*Documento gerado por @pm para refinamento por @sm.*
