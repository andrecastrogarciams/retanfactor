# PRD — Relatório de Recurtimento em Streamlit com Oracle, AgGrid e Cadastro de Fatores

## PARTE 1: VISÃO DE PRODUTO

### 1. Visão Geral

#### 1.1 Contexto e problema a resolver
Atualmente, o relatório operacional de recurtimento é realizado em **Excel**, com cálculos manuais e consolidação manual dos dados. Esse processo gera quatro problemas centrais:

1. **Tempo excessivo** para consulta e geração do relatório.
2. **Risco de erro manual** nos cálculos de peso e percentual de diferença.
3. **Falta de padronização** visual e lógica entre usuários.
4. **Ausência de centralização** da consulta e do cadastro de fatores aplicáveis aos artigos.

#### 1.2 Solução proposta
Construir uma aplicação web interna em **Streamlit**, publicada em servidor local com **Nginx + systemd**, que:

- consome em tempo real a view Oracle `USU_VBI_OPREC_V2`;
- apresenta os dados em tabela **AgGrid** com filtros e interações de análise;
- calcula colunas derivadas com base em fatores cadastrados localmente em **SQLite**;
- destaca visualmente o percentual de diferença por faixas de cor;
- permite exportação para **PDF** e **Excel**;
- oferece telas para **cadastro**, **histórico**, **duplicação** e **inativação** de fatores por código do artigo.

#### 1.3 Stakeholders principais
- **Usuário operacional principal:** setor de Recurtimento.
- **Equipe de TI:** validação final, publicação, suporte técnico.
- **Desenvolvedor responsável:** construção, deploy e manutenção.
- **Gestão operacional local:** consumo do relatório e padronização do processo.
- **Infraestrutura local:** suporte ao servidor, Nginx e disponibilidade da rede interna.

---

### 2. Objetivos de Negócio

#### 2.1 Objetivos principais
- Reduzir o tempo operacional de geração do relatório.
- Padronizar cálculos de peso calculado e percentual de diferença.
- Evitar erros manuais oriundos do Excel.
- Centralizar a consulta operacional e o cadastro de fatores em uma única aplicação.

#### 2.2 Metas SMART
[A DEFINIR]

#### 2.3 OKRs
[A DEFINIR]

#### 2.4 Impacto esperado
- **Eficiência operacional:** redução de retrabalho e tempo de consolidação.
- **Qualidade do processo:** menor variabilidade no cálculo.
- **Governança operacional:** fatores versionados por vigência, com histórico e rastreabilidade básica.
- **Confiabilidade do relatório:** geração padronizada de PDF e Excel a partir da mesma fonte e mesma lógica.

---

### 3. Público-Alvo e Personas

#### 3.1 Usuários finais
**Operador/analista do setor de recurtimento**
- Usa o relatório diariamente.
- Precisa consultar dados do mês corrente por padrão.
- Gera relatório em PDF para uso operacional.
- Não precisa editar dados Oracle, apenas consultar e exportar.

#### 3.2 Administradores/operadores
Não haverá perfil administrador formal no MVP. Qualquer uso permitido ocorrerá a partir de **computadores liberados**, com acesso controlado por **hostname e/ou allowlist de IP no Nginx**.

#### 3.3 Equipes técnicas de suporte
**TI interna**
- Faz validação final.
- Apoia acesso ao servidor local.
- Pode apoiar publicação via Nginx, se necessário, mas a manutenção prevista é do mesmo dev.

#### 3.4 Stakeholders de compliance/legal
Não há exigência formal de LGPD, auditoria regulatória ou compliance específico, pois a solução consome apenas **dados operacionais de produção**.

---

### 4. User Experience & Interface

#### 4.1 Visão de UX
- **Filosofia geral:** interface corporativa simples, funcional e orientada à produtividade.
- **Canal primário:** aplicação web interna em desktop.
- **Canal secundário:** inexistente no MVP.
- **Princípio de eficiência:** a ação mais frequente deve ocorrer em poucos passos: abrir tela → ajustar filtros → consultar/exportar.
- **Meta de esforço de uso:** consulta operacional com no máximo 3 interações principais após abertura da tela.

#### 4.2 Telas e Visões Principais

| Tela | Propósito | Perfis com Acesso | Paradigma de Interação Principal |
|------|-----------|-------------------|----------------------------------|
| Relatório | Consultar dados da view Oracle, calcular colunas derivadas e exportar | Computadores liberados | Filtros + tabela AgGrid + exportação |
| Cadastro de Fatores | Criar novo fator por código do artigo com vigência | Computadores liberados | Formulário + validação + persistência |
| Histórico de Fatores | Consultar fatores cadastrados, vigentes, duplicar e inativar | Computadores liberados | Tabela/listagem + filtros + ações por registro |

#### 4.3 Responsividade e Plataformas
- **Dispositivo-alvo:** desktop.
- **Tablet:** fora de escopo do MVP.
- **Mobile:** fora de escopo do MVP.
- **Estratégia:** interface web desktop-first.
- **PWA/app nativo:** não aplicável.
- **Breakpoints críticos:** [A DEFINIR] — o MVP não terá requisito de adaptação mobile/tablet.

#### 4.4 Acessibilidade
Sem requisito formal de conformidade WCAG para o MVP.  
Ainda assim, recomenda-se:
- contraste legível nas faixas de cor;
- texto auxiliar para estados sem cálculo;
- mensagens explícitas de erro e sucesso.

#### 4.5 Branding e Design System
- **Estilo visual:** corporativo simples e funcional.
- **Design system formal:** inexistente.
- **Paleta obrigatória no domínio:** cores da coluna `% diferença`:
  - verde: `|diferença| <= 5%`
  - amarelo: `5,01% <= |diferença| <= 10%`
  - vermelho: `|diferença| > 10%`
- **Logo:** obrigatório no PDF; uso na interface web [A DEFINIR].

---

## 5. User Stories — Estrutura Epic/Story com Acceptance Criteria Detalhados

### 5.1 Epic List (Visão Geral)

| Epic | Título | Entrega Principal | Depende de |
|------|--------|--------------------|------------|
| Epic 1 | Relatório Operacional Base | Substitui o fluxo atual em Excel com consulta, cálculo e exportação | — |
| Epic 2 | Gestão de Fatores | Permite governar fatores por vigência com histórico e ações controladas | Epic 1 |
| Epic 3 | Operação e Hardening | Fortalece acesso interno, cache, logs e comportamento operacional | Epic 1 e 2 |

---

### 5.2 Stories Expandidas por Epic

## Epic 1 — Relatório Operacional Base

**Goal:** Entregar o sistema mínimo funcional que substitui o processo atual em Excel, permitindo consultar dados Oracle, aplicar filtros, calcular colunas derivadas e exportar os resultados.

### Story 1.1 — Consultar relatório operacional
*Como usuário do recurtimento, quero abrir a tela do relatório e consultar dados filtrados da view Oracle, para que eu possa analisar a produção do período desejado.*

**Acceptance Criteria:**
1. Ao abrir a tela do relatório, o filtro de data deve vir preenchido com o **mês corrente**.
2. A consulta deve buscar dados da view Oracle `USU_VBI_OPREC_V2`.
3. Os filtros mínimos do MVP devem incluir: **lote de fabricação, data (intervalo), artigo e cor**.
4. A consulta deve retornar os dados em até **30 segundos** em condição operacional aceitável.
5. Se a consulta ao Oracle falhar, a aplicação deve exibir mensagem clara de erro e **não deve exibir dados antigos em cache como se fossem atuais**.
6. Apenas acessos originados de computadores liberados devem carregar a tela com dados; acessos fora da política devem ser bloqueados.
7. O acesso bem-sucedido à aplicação deve ser registrado em log com data/hora e identificação disponível do cliente.
8. O erro de consulta Oracle deve ser registrado em log com data/hora e contexto do erro.

### Story 1.2 — Visualizar dados em AgGrid com interações analíticas
*Como usuário do recurtimento, quero visualizar os dados em uma grade interativa, para que eu possa ordenar, reorganizar e analisar o relatório com agilidade.*

**Acceptance Criteria:**
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

### Story 1.3 — Calcular peso, densidade e desvio
*Como usuário do recurtimento, quero que o sistema calcule automaticamente os valores derivados com base no fator vigente, para que eu não precise fazer conta manual no Excel.*

**Acceptance Criteria:**
1. O sistema deve identificar o fator vigente pelo **código do artigo** e pela **data de recurtimento** da linha.
2. O peso calculado deve seguir a fórmula: `m² × 10,764 × fator × 0,092903`, com arredondamento para **2 casas decimais**.
3. O campo `kg/m²` deve ser calculado como `peso do lote / m²`, com arredondamento para **2 casas decimais**.
4. O campo `kg/ft²` deve ser calculado como `peso do lote / (m² × 10,764)`, com arredondamento para **2 casas decimais**.
5. O campo `% diferença` deve ser calculado por `(peso real - peso calculado) / peso calculado × 100`, com arredondamento para **2 casas decimais**.
6. Se não existir fator para o código do artigo, se a data estiver fora de qualquer vigência, se `m² = 0`, se `peso do lote = 0` ou se a data de vigência for inválida/nula, os campos calculados devem permanecer em **branco**.
7. Se houver mais de um fator válido por inconsistência preexistente no banco, o sistema deve usar o **registro mais recente** e registrar a ocorrência em log técnico.
8. Após o cálculo, a coluna `% diferença` deve aplicar cor por valor absoluto conforme as faixas verde, amarelo e vermelho definidas no produto.

### Story 1.4 — Exportar PDF e Excel
*Como usuário do recurtimento, quero exportar o relatório em PDF e Excel, para que eu possa distribuir e arquivar a informação operacional no formato necessário.*

**Acceptance Criteria:**
1. O PDF e o Excel devem exportar sempre as **linhas filtradas**, independentemente da seleção visual de linhas na grade.
2. O PDF e o Excel devem respeitar a **ordem atual das linhas** e a **visão atual das colunas** na tela, incluindo ocultações e reordenações feitas pelo usuário.
3. O PDF deve ser gerado em formato **retrato**, com quebra automática de páginas, e deve incluir em todas as páginas: **logo, título, data/hora de emissão e estação/setor**.
4. O PDF deve conter, no topo, o resumo com **total de linhas, média de % diferença e quantidade por faixa verde/amarelo/vermelho**.
5. O PDF deve repetir visualmente a cor da coluna `% diferença`.
6. O Excel deve exportar valores numéricos como **número**, não texto, incluindo as colunas calculadas com arredondamento em **2 casas decimais**.
7. Se a exportação falhar, a aplicação deve informar claramente ao usuário que o arquivo não foi gerado.
8. O PDF será aceito quando todas as páginas estiverem corretas conforme layout definido; o Excel será aceito quando os dados refletirem corretamente a visão filtrada e ordenada da tela.

---

## Epic 2 — Gestão de Fatores

**Goal:** Permitir governança mínima dos fatores de cálculo por artigo, com vigência, histórico, duplicação e inativação controlada.

### Story 2.1 — Cadastrar novo fator com vigência
*Como usuário operacional, quero cadastrar um novo fator por código do artigo, para que os cálculos do relatório usem a regra vigente correta.*

**Acceptance Criteria:**
1. O cadastro deve conter os campos: **código do artigo, descrição do artigo, fator, data início de vigência, data fim de vigência e observação**.
2. A lista de produtos para seleção deve vir da view Oracle `USU_VBI_ARTIGOS_SEMI_NOA`.
3. O vínculo funcional entre produto e fator deve ocorrer pelo **código do artigo**.
4. O campo `fator` não pode aceitar valor zero nem negativo.
5. A data fim de vigência pode ser vazia, significando vigência em aberto.
6. Ao salvar um fator válido, o registro deve ser persistido no SQLite em até **3 segundos** e deve aparecer imediatamente no histórico.
7. Após salvar um fator válido, ele deve passar a ser considerado imediatamente no relatório, sem aguardar expiração do cache.
8. A ação de criação deve ser registrada em log com data/hora, estação/setor, código do artigo, fator, vigência e ação realizada.

### Story 2.2 — Bloquear sobreposição de vigência
*Como usuário operacional, quero que o sistema impeça sobreposição de vigência para o mesmo código do artigo, para evitar ambiguidade no cálculo.*

**Acceptance Criteria:**
1. O sistema deve validar, antes da gravação, se já existe vigência sobreposta para o mesmo código do artigo.
2. A regra de sobreposição deve considerar tanto registros com data fim definida quanto vigência em aberto.
3. Se houver tentativa de sobreposição, o sistema deve bloquear a gravação e exibir mensagem clara de erro ao usuário.
4. O registro inválido não deve ser persistido parcialmente no SQLite.
5. A tentativa de gravação rejeitada por sobreposição deve ser registrada em log técnico.
6. O bloqueio será considerado aceito quando toda tentativa de sobreposição for impedida consistentemente.
7. Em caso de falha no acesso ao SQLite durante a validação, o sistema deve cancelar a operação e exibir erro ao usuário.
8. A validação deve ser aplicada tanto no cadastro novo quanto na duplicação de fator.

### Story 2.3 — Consultar histórico de fatores
*Como usuário operacional, quero consultar o histórico de fatores, para que eu possa entender o que está vigente e o que já foi cadastrado anteriormente.*

**Acceptance Criteria:**
1. A tela de histórico deve permitir visualizar a lista de fatores já cadastrados.
2. O histórico deve permitir pesquisar por **código do artigo**.
3. O histórico deve permitir filtrar por **período de vigência**.
4. O histórico deve permitir visualizar **somente vigentes**.
5. Registros antigos, inativos e até duplicidades acidentais já existentes no banco devem continuar visíveis no histórico.
6. A tela deve indicar claramente o status do registro, incluindo vigência aberta e cancelamento, quando aplicável.
7. Se a leitura do SQLite falhar, a tela deve informar o erro ao usuário sem exibir dados incoerentes.
8. O carregamento do histórico deve respeitar o ambiente atual da aplicação, sem cruzar dados de homologação e produção.

### Story 2.4 — Duplicar e inativar fator
*Como usuário operacional, quero duplicar um fator e também inativar um fator existente, para facilitar nova vigência e controlar registros que não devem mais ser usados.*

**Acceptance Criteria:**
1. Ao clicar em **Duplicar fator**, os campos **código do artigo, descrição, fator e observação** devem vir pré-preenchidos, enquanto **início e fim de vigência** devem permanecer em branco.
2. A duplicação deve reaproveitar os dados do registro original sem alterar o registro de origem.
3. Ao inativar/cancelar um fator, o usuário deve informar **motivo obrigatório**.
4. O motivo do cancelamento deve ser salvo no SQLite em campo próprio, por exemplo `motivo_cancelamento`.
5. A observação do cadastro inicial pode ser reaproveitada no cancelamento, mas o motivo do cancelamento deve ser persistido como informação distinta.
6. O cancelamento/inativação deve remover o fator das consultas futuras imediatamente, sem reescrever historicamente os dados Oracle.
7. A ação de duplicação e a ação de cancelamento devem ser registradas em log com seus metadados obrigatórios.
8. Se o SQLite falhar durante duplicação ou cancelamento, a aplicação deve abortar a operação e informar o erro ao usuário.

---

## Epic 3 — Operação e Hardening

**Goal:** Entregar uma solução operacionalmente viável em ambiente local, com acesso restrito, cache controlado, logs e comportamento previsível em caso de falha.

### Story 3.1 — Restringir acesso por ambiente interno
*Como equipe de TI, quero restringir o acesso à aplicação a computadores liberados, para reduzir uso indevido e manter o sistema apenas na rede interna.*

**Acceptance Criteria:**
1. A aplicação deve ser acessível apenas na **rede interna**, sem acesso externo ou VPN no MVP.
2. O acesso deve ser controlado por **hostname e/ou allowlist de IPs no Nginx**.
3. Requisições provenientes de origem não autorizada devem ser bloqueadas antes do uso funcional da aplicação.
4. Toda tentativa de acesso bloqueado deve ser registrada em log com data/hora e metadados disponíveis.
5. O sistema não deve depender de login de usuário para o MVP.
6. A estação/setor exibida na tela e no PDF deve ser configurada tecnicamente por instância, via arquivo de configuração/env.
7. A URL de homologação deve ser separada da URL de produção.
8. O ambiente de homologação deve usar SQLite próprio e separado do ambiente de produção.

### Story 3.2 — Aplicar cache temporário com atualização forçada
*Como usuário operacional, quero que a aplicação use cache temporário e também permita atualização imediata, para equilibrar desempenho e atualidade dos dados.*

**Acceptance Criteria:**
1. O relatório deve usar cache temporário com **TTL de 5 minutos**.
2. A tela do relatório deve exibir botão **Atualizar dados** para forçar nova consulta e invalidar o cache funcional da consulta.
3. Após salvar, duplicar ou inativar um fator, o relatório deve refletir imediatamente a nova regra aplicável, sem aguardar expiração natural do cache.
4. O cache não deve mascarar erro Oracle: se a consulta em tempo real falhar no refresh forçado, o sistema deve mostrar erro e não apresentar dado obsoleto como atual.
5. O uso de cache deve ser transparente ao usuário, sem exigir ação manual para o fluxo normal de consulta.
6. Se a invalidação do cache falhar, o sistema deve registrar o erro e informar que os dados podem não refletir a última alteração.
7. O comportamento do cache deve ser consistente entre homologação e produção.
8. A interface deve informar visualmente quando os dados forem recarregados com sucesso após atualização forçada.

### Story 3.3 — Registrar logs operacionais e tratar falhas
*Como desenvolvedor e equipe de TI, quero logs operacionais mínimos e comportamento controlado em falhas, para manter a operação rastreável e suportável.*

**Acceptance Criteria:**
1. Os logs devem ser gravados em **arquivo local no servidor** com retenção mínima de **30 dias**.
2. Devem ser registrados ao menos os seguintes eventos:
   - acesso à aplicação
   - tentativa de acesso bloqueado
   - erro na consulta Oracle
   - criação de fator
   - duplicação de fator
   - cancelamento de fator
3. Para ações de fator, os logs devem incluir: data/hora, estação/setor, código do artigo, fator, vigência e ação realizada.
4. Não é obrigatório registrar em log a geração de PDF, exportação de Excel ou clique em atualizar dados no MVP.
5. Em erro de Oracle, o sistema deve registrar em log e mostrar mensagem de erro na tela; não haverá alerta automático no MVP.
6. A solução deve ser publicada como **Streamlit + Nginx + systemd** em servidor local.
7. O deploy deve ocorrer via **Git/GitHub + pull + restart do service**, passando obrigatoriamente por homologação antes de produção.
8. Não haverá rollback formal no MVP; em caso de falha de release, a contingência será corrigir e realizar novo deploy, com versionamento por tags/releases no Git.

---

### 5.3 Edge Cases

- Registro Oracle sem `m²`, `peso do lote` ou `data de recurtimento` válida gera linhas visíveis, mas sem cálculo.
- Fator com vigência aberta coexistindo acidentalmente com outro fator válido para o mesmo artigo; sistema usa o mais recente, mas deve registrar inconsistência técnica.
- Alteração de colunas visíveis na tela seguida de exportação; arquivo deve seguir a visão atual, não o layout padrão.
- Atualização de fator seguida imediatamente de consulta com cache ativo; o sistema deve invalidar o cache funcionalmente.
- Homologação e produção apontando para a mesma base Oracle de produção podem expor testes em dados reais.
- Acesso vindo de máquina não autorizada deve ser bloqueado no Nginx antes do uso.
- Corrupção do SQLite impede leitura dos fatores e pode fazer o relatório perder cálculo derivado.
- Falha durante cancelamento de fator não pode deixar registro parcialmente cancelado.
- Duplicação de fator com vigência preenchida incorretamente deve passar pela mesma validação de sobreposição do cadastro novo.
- PDF com muitas páginas deve manter cabeçalho institucional em todas as páginas sem truncar a tabela.

---

## PARTE 2: REQUISITOS FUNCIONAIS

### 6. Funcionalidades Core

#### 6.1 Funcionalidades principais
1. Consultar relatório operacional em tempo real via Oracle.
2. Filtrar por lote de fabricação, data, artigo e cor.
3. Exibir relatório em AgGrid com recursos analíticos.
4. Calcular:
   - kg/m²
   - kg/ft²
   - fator aplicado
   - peso calculado
   - % diferença
5. Colorir `% diferença` por faixas.
6. Exportar para PDF.
7. Exportar para Excel.
8. Cadastrar fator por código do artigo com vigência.
9. Consultar histórico de fatores.
10. Duplicar fator.
11. Inativar/cancelar fator com motivo obrigatório.

#### 6.2 Fluxos principais

**Fluxo A — Consulta operacional**
1. Usuário acessa aplicação de máquina liberada.
2. Tela abre com período padrão do mês corrente.
3. Usuário ajusta filtros.
4. Aplicação consulta Oracle.
5. Sistema aplica fatores vigentes do SQLite.
6. Tabela é exibida.
7. Usuário exporta PDF ou Excel.

**Fluxo B — Cadastro de fator**
1. Usuário acessa tela de cadastro.
2. Seleciona artigo da lista Oracle.
3. Informa fator, vigência e observação.
4. Sistema valida sobreposição.
5. Persistência em SQLite.
6. Relatório passa a refletir a nova vigência.

**Fluxo C — Duplicação**
1. Usuário abre histórico.
2. Aciona duplicação.
3. Formulário reaproveita dados-base.
4. Usuário informa nova vigência.
5. Sistema valida sobreposição.
6. Novo registro é salvo.

**Fluxo D — Cancelamento**
1. Usuário acessa histórico.
2. Seleciona registro.
3. Informa motivo obrigatório.
4. Sistema marca registro como cancelado/inativo.
5. Registro deixa de valer para cálculos futuros.

#### 6.3 Regras de negócio
- O fator é determinado pelo **código do artigo**.
- A vigência é avaliada pela **data de recurtimento**.
- Sem fator aplicável, os campos calculados ficam em branco.
- Se houver múltiplos fatores válidos por inconsistência preexistente, prevalece o **mais recente**.
- Não é permitida sobreposição de vigência no cadastro normal.
- Inativação vale para uso futuro; não altera os dados Oracle históricos.
- Exportações seguem a visão atual da tela.
- A seleção de linhas não interfere na exportação.

#### 6.4 Validações e restrições
- Fator > 0.
- Início de vigência obrigatório.
- Fim de vigência opcional.
- Observação obrigatória? [A DEFINIR] — o requisito informado apenas a torna necessária no cadastro funcional, mas a obrigatoriedade explícita não foi travada.
- Motivo de cancelamento obrigatório.
- Acesso restrito a origem permitida.
- Sem edição e sem exclusão física de fator no MVP.

---

### 7. Integrações

#### 7.1 Sistemas externos
- **Oracle**
  - View relatório: `USU_VBI_OPREC_V2`
  - View produtos: `USU_VBI_ARTIGOS_SEMI_NOA`

#### 7.2 Sistema legado substituído
- Processo manual em **Excel**.

#### 7.3 Protocolos e comunicação
- Conexão da aplicação Python com Oracle: [A DEFINIR — driver e DSN detalhados].
- Comunicação web interna via Nginx reverse proxy para aplicação Streamlit.

#### 7.4 Autenticação/autorização entre sistemas
- Não há login de usuário no MVP.
- Restrição de acesso por hostname e/ou IP allowlist no Nginx.
- Credenciais Oracle devem ser mantidas fora do código, via configuração/env.

#### 7.5 SLAs de dependências externas
- Oracle é dependência crítica.
- Tempo máximo aceitável para carga do relatório: **30 segundos**.
- Sem SLA formal contratado documentado no momento. [A DEFINIR]

---

## PARTE 3: REQUISITOS NÃO-FUNCIONAIS

### 8. Performance e Escalabilidade

#### 8.1 Latência esperada
- **Consulta do relatório:** até **30 segundos**.
- **Persistência de novo fator:** até **3 segundos**.
- **Demais interações UI:** [A DEFINIR]

#### 8.2 Throughput
- Até **10 usuários simultâneos**.

#### 8.3 Volume de dados
- Base corrente desde 2026, com **menos de 1000 linhas** reportadas no estado atual.
- Projeção de crescimento:
  - 6 meses: baixo
  - 1 ano: baixo a moderado
  - 3 anos: [A DEFINIR]

#### 8.4 Escalabilidade
- Arquitetura suficiente para carga baixa e interna.
- Não há exigência de escalabilidade horizontal no MVP.

#### 8.5 Estratégia de cache
- Cache de relatório com **TTL de 5 minutos**.
- Refresh forçado por botão.
- Invalidação funcional após mudança de fator.

---

### 9. Disponibilidade e Confiabilidade

#### 9.1 SLA
[A DEFINIR]

#### 9.2 SLO
- Recuperar aplicação em até **1 hora** após indisponibilidade.

#### 9.3 SLI
- Tempo de resposta de consulta.
- Disponibilidade da aplicação.
- Taxa de falhas em consulta Oracle.
- [A DEFINIR] detalhamento exato de medição.

#### 9.4 RTO
- **1 hora**

#### 9.5 RPO
[A DEFINIR]  
Observação: não há rotina formal de backup do SQLite no MVP; perda do banco local foi classificada como impacto **médio** e potencialmente reconstruível manualmente.

#### 9.6 Failover/redundância
- Não há failover formal no MVP.
- Não há rollback formal de release.
- Contingência de release: corrigir e realizar novo deploy.

---

### 10. Segurança

#### 10.1 Autenticação
- Não haverá autenticação por login no MVP.

#### 10.2 Autorização
- Controle por origem permitida na camada Nginx/rede.
- Computadores liberados por hostname e/ou allowlist de IP.

#### 10.3 Criptografia
- Em trânsito: [A DEFINIR]
- Em repouso: [A DEFINIR]

#### 10.4 Gestão de secrets
- Credenciais Oracle e configurações sensíveis via env/arquivo técnico fora do código-fonte.

#### 10.5 Compliance
- Sem exigência formal de LGPD, GDPR, ISO 27001 etc. no escopo do MVP.

#### 10.6 Auditoria
- Trilhas básicas via logs em arquivo local.
- Persistência de cancelamento e motivo no SQLite.

#### 10.7 Testes de segurança
[A DEFINIR]  
No MVP, o foco é segurança operacional mínima por restrição de rede, não programa formal de segurança.

---

### 11. Observabilidade

#### 11.1 Logs
- Arquivo local no servidor.
- Retenção mínima: **30 dias**.
- Níveis recomendados: `INFO`, `WARNING`, `ERROR`.
- Campos recomendados: timestamp, ambiente, estação/setor, evento, código do artigo, mensagem, stacktrace quando aplicável.

#### 11.2 Métricas
**Técnicas**
- tempo de consulta
- quantidade de falhas Oracle
- quantidade de acessos permitidos
- quantidade de acessos bloqueados

**Negócio**
[A DEFINIR]

#### 11.3 Tracing
Não aplicável para MVP monolítico simples.

#### 11.4 Alertas
- Não haverá alertas automáticos no MVP.

#### 11.5 Dashboards
[A DEFINIR]

#### 11.6 Health checks
- Recomendado endpoint ou validação operacional de disponibilidade da aplicação e conectividade com Oracle/SQLite.  
[A DEFINIR] formato exato.

---

### 12. Manutenibilidade e Testabilidade

#### 12.1 Arquitetura
- Monólito simples em Python/Streamlit.
- Recomendação de estrutura modular por camadas:
  - UI
  - serviços de relatório
  - serviços de fatores
  - integração Oracle
  - repositório SQLite
  - exportação PDF/Excel
  - logging/configuração

#### 12.2 Documentação técnica
- README de setup
- runbook de deploy
- runbook de troubleshooting
- catálogo de variáveis de ambiente
- versionamento de migrações SQLite

#### 12.3 Estratégia de testes
- **Testes unitários:** regras de cálculo, regras de cor, validação de vigência, bloqueio de sobreposição.
- **Testes de integração:** Oracle e SQLite.
- **Testes E2E:** [A DEFINIR]
- **Testes de performance:** [A DEFINIR]
- **Smoke test em produção:** recomendado após deploy.

#### 12.4 Versionamento de API
Não aplicável.

#### 12.5 Backward compatibility
Baixa relevância no MVP, por se tratar de interface interna e monolítica.  
Compatibilidade de schema SQLite será garantida por **migrações simples e versionadas**.

---

## PARTE 4: ARQUITETURA E INFRAESTRUTURA

### 13. Arquitetura de Solução

#### 13.1 Diagrama de componentes (alto nível)

```text
[Usuário em PC liberado]
        |
        v
     [Nginx]
        |
        v
 [Aplicação Streamlit]
   |       |        |
   |       |        +--> [SQLite local - fatores]
   |       |
   |       +--> [Módulo de exportação PDF/Excel]
   |
   +--> [Conector Oracle]
              |
              +--> [USU_VBI_OPREC_V2]
              +--> [USU_VBI_ARTIGOS_SEMI_NOA]
```

#### 13.2 Stack tecnológico
- **Backend/UI:** Python + Streamlit
- **Grade de dados:** AgGrid
- **Banco local:** SQLite
- **Exportação Excel:** biblioteca Python (ex.: openpyxl/xlsxwriter) [A DEFINIR]
- **Exportação PDF:** biblioteca Python (ex.: reportlab) [A DEFINIR]
- **Reverse proxy:** Nginx
- **Process manager:** systemd
- **Versionamento:** Git/GitHub

#### 13.3 Padrão arquitetural
- **Monólito modular**
- Justificativa:
  - 1 dev
  - baixa carga
  - ambiente on-premise simples
  - menor custo operacional
  - menor superfície de falha

#### 13.4 Edge vs cloud
- **On-premise/local server**
- Sem requisito de cloud no MVP.

---

### 14. Infraestrutura

#### 14.1 Ambiente
- Servidor local interno.
- Acesso apenas por rede interna.

#### 14.2 Ambientes
- **Homologação**
- **Produção**

#### 14.3 Topologia
- Homologação e produção com:
  - URLs separadas
  - SQLite separado
  - mesma base Oracle de produção

#### 14.4 Recursos computacionais
[A DEFINIR]
- CPU
- RAM
- storage
- limites de processo

#### 14.5 Rede
- Sem exposição externa.
- Restrição por hostname/IP.
- Nginx como camada de publicação e controle.

#### 14.6 Containers / serverless
- Não aplicável no MVP.

---

### 15. Estratégia de Dados

#### 15.1 Modelo de dados de alto nível

**Entidade: fator_artigo**
- id
- codigo_artigo
- descricao_artigo
- fator
- data_inicio_vigencia
- data_fim_vigencia
- observacao
- status
- motivo_cancelamento
- created_at
- updated_at
- cancelled_at

**Entidade: schema_migration**
- id
- version
- applied_at

**Fonte externa: relatorio_oracle**
- data_recurtimento
- artigo
- cor
- lote_fabricacao
- codigo_artigo
- m2
- peso_lote
- demais campos de origem [A DEFINIR]

#### 15.2 Relacionamentos
- `relatorio_oracle.codigo_artigo` ↔ `fator_artigo.codigo_artigo`
- A associação efetiva depende da data de recurtimento estar dentro da vigência do fator.

#### 15.3 Volume esperado
- SQLite: baixo volume.
- Oracle consumido em leitura: baixo volume atual.

#### 15.4 Retenção
- Fatores: retenção histórica indefinida, salvo decisão futura.
- Logs: 30 dias em arquivo local.

#### 15.5 Backup e restore
- Backup SQLite: **não previsto no MVP**
- Restore: [A DEFINIR]
- Risco assumido: reconstrução manual em caso de perda/corrupção.

#### 15.6 Migração de dados
- Não há migração de legado estruturado; o legado atual é processo em Excel.
- Estratégia de adoção: substituir uso operacional gradualmente após homologação.
- Migração de schema SQLite: **scripts simples e versionados**.

#### 15.7 Rollback de dados
- Não há rollback formal automatizado no MVP.
- Contingência: correção pontual e novo deploy, se o problema for de aplicação.
- Para fator incorreto cadastrado, o fluxo de correção esperado é novo cadastro/inativação, não edição direta.

#### 15.8 Data warehouse / analytics
Não aplicável.

---

## PARTE 5: OPERAÇÃO E DEPLOYMENT

### 16. CI/CD e Deployment

#### 16.1 Pipeline
- Sem CI/CD sofisticado no MVP.
- Fluxo previsto:
  1. Commit no Git/GitHub
  2. Promoção para homologação
  3. Validação
  4. Tag/release no Git
  5. Pull no servidor
  6. Restart do service

#### 16.2 Estratégia de release
- **Promoção manual** entre ambientes.
- Homologação obrigatória antes de produção.
- Versionamento com tags/releases no Git.

#### 16.3 Rollback
- **Não haverá rollback formal no MVP**.
- Em caso de falha, a contingência é corrigir e realizar novo deploy.

#### 16.4 Feature flags
Não previsto.

#### 16.5 Aprovações
- Validação final pela **TI**.

---

### 17. Runbooks e Operação

#### 17.1 Procedimentos operacionais
- subir homologação
- validar consulta Oracle
- validar SQLite e migrações
- validar exportação PDF/Excel
- promover para produção
- reiniciar service
- verificar logs

#### 17.2 Troubleshooting comum
- erro de conexão Oracle
- erro de permissão/restrição Nginx
- SQLite bloqueado/corrompido
- cache não invalidado
- falha na exportação

#### 17.3 Contatos / responsáveis
- Responsável principal: **mesmo dev que constrói**
- Apoio de TI: [A DEFINIR] conforme disponibilidade interna

#### 17.4 SLAs internos
[A DEFINIR]  
O único valor explicitado foi RTO de 1 hora.

---

### 18. Disaster Recovery

#### 18.1 Cenários contemplados
- indisponibilidade Oracle
- queda da aplicação Streamlit/service
- erro de publicação/release
- corrupção do SQLite
- bloqueio indevido por política Nginx

#### 18.2 Plano de recuperação
- **Oracle indisponível:** exibir erro, registrar em log, aguardar restabelecimento da origem.
- **Queda da aplicação:** reiniciar service e validar Nginx.
- **Erro de release:** corrigir e realizar novo deploy.
- **SQLite corrompido:** restaurar manualmente ou reconstruir cadastro, conforme viabilidade.
- **Bloqueio indevido:** ajustar allowlist/hostname rule e republish/reload Nginx.

#### 18.3 RTO / RPO específicos
- RTO: 1 hora
- RPO: [A DEFINIR]

#### 18.4 Testes de DR
[A DEFINIR]

---

## PARTE 6: VIABILIDADE E RISCOS

### 19. Análise de Viabilidade Técnica

#### 19.1 Capacidade do time
- **1 dev**
- Mantém também deploy e operação inicial.
- Stack proposta é compatível com cenário de time enxuto.

#### 19.2 Skills disponíveis necessárias
- Python
- Streamlit
- integração Oracle
- SQLite
- Nginx
- systemd
- Git/GitHub
- exportação PDF/Excel

#### 19.3 Esforço por componente
- Consulta Oracle: baixa/média
- Cálculos e regras: baixa
- UI AgGrid: baixa/média
- Exportação PDF: média
- Cadastro e vigência de fatores: média
- Operação com Nginx/systemd: baixa/média
- Hardening de acesso por IP/hostname: média

#### 19.4 Prazo realista
Não foi definido prazo alvo.  
Seção mantida como **[A DEFINIR]**.

#### 19.5 Viabilidade geral
Viável, com complexidade **baixa a média**, desde que:
- a conexão Oracle seja estável;
- o PDF seja tratado com cuidado;
- as migrações SQLite sejam disciplinadas;
- o acesso via Nginx seja bem configurado.

---

### 20. Build vs Buy vs Integrate

#### 20.1 Componente: relatório operacional
- **Build:** Streamlit customizado.
- **Buy:** Power BI / outra ferramenta BI.
- **Integrate:** solução híbrida sobre ferramenta existente.

**Recomendação:** **Build**  
Justificativa:
- necessidade de regra de cálculo específica por vigência;
- exportação PDF/Excel alinhada à visão atual da tela;
- controle operacional local;
- menor atrito para ajuste evolutivo.

#### 20.2 Componente: armazenamento de fatores
- **Build:** SQLite local.
- **Buy:** banco gerenciado/comercial.
- **Integrate:** reutilizar banco corporativo.

**Recomendação:** **Build com SQLite**  
Justificativa:
- baixa carga;
- 1 servidor;
- 1 instância;
- simplicidade operacional.
- mitigação necessária: migrações versionadas.

#### 20.3 Componente: autenticação/autorização
- **Build:** login próprio.
- **Buy:** SSO/corporativo.
- **Integrate:** AD/LDAP [A DEFINIR se existir].

**Recomendação para MVP:** **Não implementar login**; usar restrição por rede/origem.  
Justificativa:
- escopo operacional enxuto;
- ambiente interno;
- ausência de exigência formal de compliance.

---

### 21. Riscos Técnicos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação | Contingência |
|------|---------------|---------|-----------|--------------|
| Indisponibilidade do Oracle | Média | Alto | Tratamento claro de erro, logs, refresh manual | Aguardar origem restabelecer e reprocessar consulta |
| Fator cadastrado errado | Média | Alto | Validações, histórico, cancelamento com motivo, sem edição destrutiva | Inativar fator incorreto e cadastrar novo fator correto |
| Homologação usando mesma base Oracle de produção | Alta | Médio | Restringir uso de homologação, sinalizar ambiente, cuidado em testes | Suspender testes operacionais até alinhamento e reforçar segregação lógica |
| Ausência de rollback formal | Média | Médio/Alto | Homologação obrigatória e tags Git | Corrigir defeito e fazer novo deploy |
| Corrupção/perda do SQLite | Baixa/Média | Médio | Migrações versionadas e cuidado operacional | Reconstrução manual do cadastro ou restauração local se houver cópia informal |
| Falha na geração de PDF | Média | Médio | Testes de paginação, layout e grandes volumes | Exportar Excel como contingência temporária |
| Restrição por IP/hostname mal configurada | Média | Médio | Testar acesso por ambiente antes da publicação | Ajustar Nginx e revalidar com máquina autorizada |
| Cache mascarando dado não atualizado | Baixa/Média | Médio | Botão atualizar e invalidação após salvar fator | Recarregar forçadamente e revisar estratégia de cache |

---

### 22. Dívida Técnica

#### 22.1 Dívida existente
- Processo atual dependente de Excel.
- Ausência de rastreabilidade estruturada do fator fora da nova aplicação.

#### 22.2 Dívida que será criada no MVP
- Sem rollback formal.
- Sem backup estruturado do SQLite.
- Sem autenticação de usuário.
- Homologação usando mesma base Oracle de produção.
- Ausência de alertas automáticos.

#### 22.3 Plano para endereçar
- Evoluir rollback em versão futura.
- Avaliar backup do SQLite.
- Avaliar autenticação por AD/LDAP/SSO.
- Separar base Oracle de homologação, se disponível.
- Evoluir alertas e health checks.

---

## PARTE 7: MÉTRICAS E CUSTOS

### 23. Métricas de Sucesso

#### 23.1 Métricas de Negócio (KPIs)
[A DEFINIR]  
O usuário optou por não definir métricas de sucesso de negócio neste MVP.

#### 23.2 Métricas Técnicas (SLIs)
- Tempo de carga do relatório: alvo de aceite até **30 segundos**
- Tempo de persistência de fator: alvo de aceite até **3 segundos**
- Taxa de falhas Oracle: [A DEFINIR]
- Disponibilidade da aplicação: [A DEFINIR]
- Error rate HTTP/aplicação: [A DEFINIR]
- Throughput: até 10 usuários simultâneos

#### 23.3 Métricas de Qualidade
- Cobertura de testes unitários: [A DEFINIR]
- Cobertura de testes de integração: [A DEFINIR]
- MTTR: [A DEFINIR]
- Frequência de deploy: [A DEFINIR]
- Lead time commit → produção: [A DEFINIR]

---

### 24. TCO (Total Cost of Ownership)

#### 24.1 CAPEX
[A DEFINIR]
- desenvolvimento
- tempo de homologação
- eventual ajuste de infraestrutura

#### 24.2 OPEX
[A DEFINIR]
- servidor local já existente
- manutenção do dev
- operação Nginx/systemd
- custo indireto de suporte

#### 24.3 Break-even
[A DEFINIR]

---

## PARTE 8: APÊNDICES

### 25. Glossário

- **AgGrid:** componente de grade interativa usado para exibir tabelas.
- **Código do artigo:** chave técnica usada para localizar o fator aplicável.
- **Artigo:** descrição visível do produto/artigo.
- **Fator:** multiplicador usado no cálculo do peso calculado.
- **Vigência:** intervalo de datas em que o fator é válido.
- **Peso calculado:** resultado da fórmula baseada em m² e fator.
- **Peso real:** peso do lote oriundo da view Oracle.
- **% diferença:** desvio percentual entre peso real e peso calculado.
- **SQLite:** banco local usado para armazenar fatores.
- **Oracle view:** origem dos dados operacionais e lista de artigos.
- **Nginx allowlist:** regra de acesso por IP/hostname.

---

### 26. Referências

- View Oracle de relatório: `USU_VBI_OPREC_V2`
- View Oracle de artigos: `USU_VBI_ARTIGOS_SEMI_NOA`
- Requisitos coletados nesta entrevista
- Processo atual em Excel
- Git/GitHub como fluxo de publicação

---

### 27. Dúvidas em Aberto

1. DSN, credenciais e forma exata de conexão Oracle.
2. Bibliotecas definitivas para exportação PDF e Excel.
3. Recurso computacional exato do servidor de homologação e produção.
4. Estratégia exata de health check.
5. Necessidade futura de backup do SQLite.
6. Se `observação` será obrigatória em validação de cadastro ou apenas campo disponível.
7. Se haverá logo também na interface web ou apenas no PDF.
8. Se haverá TLS interno no Nginx.
9. SLAs/SLOs formais além do RTO.
10. Métricas de negócio e prazo alvo do projeto.

---

### 28. Checklist de Auto-Validação

#### Rubrica de Avaliação

| # | Categoria | Critério | Status | Observações |
|---|-----------|----------|--------|-------------|
| 1 | Definição do Problema | Problema claro, personas definidas, KPIs mensuráveis | ⚠️ | Problema e personas estão claros; KPIs ficaram [A DEFINIR] por decisão do solicitante |
| 2 | Escopo MVP | Cada Epic entrega valor standalone; fronteira MVP vs futuro definida | ✅ | MVP e trade-offs estão explícitos |
| 3 | User Experience | Telas mapeadas, paradigmas de interação definidos, responsividade especificada | ✅ | Desktop-only e layout macro definidos |
| 4 | Requisitos Funcionais | Funcionalidades testáveis, regras de negócio explícitas, sem ambiguidade | ✅ | Regras de cálculo e exportação estão fechadas |
| 5 | Requisitos Não-Funcionais | Performance, segurança, disponibilidade, observabilidade cobertos com métricas | ⚠️ | Parte coberta; SLA, RPO e alguns SLIs ficaram [A DEFINIR] |
| 6 | Epic & Story Structure | Epics sequenciados; Stories com 5-8 ACs testáveis; edge cases documentados | ✅ | Estrutura atende ao requisito |
| 7 | Arquitetura & Stack | Stack definido com justificativa; modelo de dados documentado; diagrama presente | ✅ | Monólito Python/Streamlit/SQLite/Oracle bem justificado |
| 8 | Operação & Infra | CI/CD, backup, DR, health checks, requisitos de hardware documentados | ⚠️ | Deploy e DR foram cobertos; backup e sizing ainda incompletos |
| 9 | Riscos & Viabilidade | Riscos com probabilidade/impacto/mitigação/contingência; Build vs Buy justificado | ✅ | Riscos centrais documentados |
| 10 | Clareza & Comunicação | Linguagem clara, estrutura consistente, glossário presente | ✅ | Estrutura completa e consistente |

#### Resultado

| Item | Valor |
|------|-------|
| Completude geral do PRD | 88% |
| Escopo MVP | ✅ |
| Pronto para fase de Arquitetura/SPEC | ⚠️ |

#### Issues Identificadas (por prioridade)

**HIGH:**  
- Homologação utiliza a mesma base Oracle de produção.  
- Não há rollback formal no MVP.  
- Não há estratégia formal de backup/restore do SQLite.

**MEDIUM:**  
- SLA, RPO e métricas técnicas detalhadas não foram fechados.  
- Segurança depende apenas de rede/origem, sem autenticação de usuário.  
- Falta definição exata de health checks e sizing do servidor.

**LOW:**  
- Ausência de design system formal.  
- Sem alertas automáticos no MVP.  
- KPIs de negócio e prazo alvo não definidos.

#### Next Steps Recomendados

- `@architect` — transformar este PRD em documento de arquitetura técnica detalhada, incluindo diagrama de componentes, fluxos de dados e estratégia de cache.
- `@tech-lead` — definir DSN/driver Oracle, biblioteca final de PDF/Excel, política de health checks e estrutura final do SQLite.
- `@infra` — detalhar publicação Nginx, service systemd, allowlist de IP/hostname e segregação entre homologação e produção.
- `@qa` — derivar casos de teste a partir das stories e critérios de aceite.
- `@ux-design-expert` — criar wireframes desktop das 3 telas com foco em produtividade operacional.
