# Story 1.1 — Consultar relatório operacional

**Epic:** Epic 1 — Relatório Operacional Base
**Goal:** Como usuário do recurtimento, quero abrir a tela do relatório e consultar dados filtrados da view Oracle, para que eu possa analisar a produção do período desejado.

## Acceptance Criteria
1. Ao abrir a tela do relatório, o filtro de data deve vir preenchido com o **mês corrente**.
2. A consulta deve buscar dados da view Oracle `USU_VBI_OPREC_V2`.
3. Os filtros mínimos do MVP devem incluir: **lote de fabricação, data (intervalo), artigo e cor**.
4. A consulta deve retornar os dados em até **30 segundos** em condição operacional aceitável.
5. Se a consulta ao Oracle falhar, a aplicação deve exibir mensagem clara de erro e **não deve exibir dados antigos em cache como se fossem atuais**.
6. Apenas acessos originados de computadores liberados devem carregar a tela com dados; acessos fora da política devem ser bloqueados.
7. O acesso bem-sucedido à aplicação deve ser registrado em log com data/hora e identificação disponível do cliente.
8. O erro de consulta Oracle deve ser registrado em log com data/hora e contexto do erro.

---
*Documento gerado por @pm para refinamento por @sm.*
