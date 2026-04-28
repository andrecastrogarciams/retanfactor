# Story 4.2 — Redesign: Página Relatório de Recurtimento

**Epic:** Epic 4 — Design e UX das Páginas
**Status:** Ready for Review
**Estimativa:** L

## Descrição
Como operador do setor de recurtimento, quero que a tela de relatório siga o visual "Industrial Precision", para que a consulta diária seja clara, densa em dados e profissional.

## Acceptance Criteria

1. O painel de filtros deve ser exibido em linha horizontal (usando `st.columns`), com labels em **Inter SemiBold 12px** acima de cada campo.
2. A tabela AgGrid deve aplicar estilo zebra (alternância de fundo por linha), header com `#f1f3f5`, altura de linha 36px e texto alinhado à direita para colunas numéricas.
3. A coluna `% diferença` deve exibir células coloridas:
   - Verde (`#28a745`) para `|diferença| ≤ 5%`
   - Amarelo (`#ffc107`) para `5,01% ≤ |diferença| ≤ 10%`
   - Vermelho (`#dc3545`) para `|diferença| > 10%`
4. O card de resumo (totais/médias) deve seguir o padrão do design system: borda `1px solid #dee2e6`, padding 20px, radius 4px, sem sombra.
5. Os botões **Exportar PDF** e **Exportar Excel** devem ser primário e secundário respectivamente, conforme Story 4.1.
6. O logo Viposa e o título "Relatório de Recurtimento" devem aparecer no header padrão via `render_page_header()`.
7. O banner de ambiente (homologação) deve usar o padrão de alerta do design system (`#dc3545` com ícone de aviso).

## Escopo

**IN:**
- Refatorar layout de filtros para `st.columns` horizontal
- Aplicar `AgGrid` com tema corporativo: zebra, header cinza, altura 36px
- CSS para coloração de células da coluna `% diferença`
- Card de resumo estilizado
- Botões primário/secundário para PDF/Excel
- Header com logo via `render_page_header()`

**OUT:**
- Alteração da lógica de negócio ou cálculos
- Novos filtros ou colunas
- Paginação server-side

## Dependências
- Story 4.1 — `inject_global_css()` e `render_page_header()` devem estar disponíveis

## Riscos
- AgGrid no Streamlit tem limitações de CSS customizado via `gridOptions`; o estilo de células coloridas pode exigir `cellStyle` via JavaScript callback. Mitigação: usar `JsCode` do `st_aggrid` para definir `cellStyle` programaticamente.

## Dev Notes

**Arquivo principal:** `pages/01_relatorio.py`

**Referência visual:** `docs/templates/relat_rio_de_recurtimento_retanfactor/screen.png` e `code.html`

**AgGrid cellStyle para % diferença:**
```python
from st_aggrid.shared import JsCode

cell_style_pct = JsCode("""
function(params) {
    const v = Math.abs(params.value);
    if (v <= 5)  return { backgroundColor: '#d4edda', color: '#155724' };
    if (v <= 10) return { backgroundColor: '#fff3cd', color: '#856404' };
    return { backgroundColor: '#f8d7da', color: '#721c24' };
}
""")
```

**Layout de filtros:**
```python
col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
with col1: data_inicio = st.date_input("Data início", ...)
with col2: data_fim = st.date_input("Data fim", ...)
...
```

## Tasks

- [x] Refatorar filtros de `pages/01_relatorio.py` para layout horizontal em colunas
- [x] Aplicar tema AgGrid: zebra, header cinza `#f1f3f5`, altura 36px, alinhamento numérico
- [x] Implementar `cellStyle` via `JsCode` para coloração da coluna `% diferença`
- [x] Estilizar card de resumo com borda, padding e radius do design system
- [x] Ajustar botões PDF/Excel para estilos primário/secundário
- [x] Adicionar `render_page_header("Relatório de Recurtimento")` no topo
- [x] Verificar que `inject_global_css()` é chamado na página
- [x] Atualizar testes afetados pela refatoração de layout

## Dev Agent Record

### File List
- `pages/01_relatorio.py` — modificado (filtros horizontais, AgGrid streamlit+36px, card resumo HTML, botões primário/secundário)
- `docs/stories/story-4.2.md` — atualizado (checkboxes + registro)

### Completion Notes
- `cellStyle` JsCode para `% diferença` já existia com cores corretas — mantido sem alteração
- Tema AgGrid alterado de `"alpine"` → `"streamlit"` para ativar o CSS do design system
- `rowHeight=36` e `headerHeight=40` injetados via `grid_options` dict após `gb.build()`
- Testes existentes testam apenas funções puras (`_rows_to_dataframe`, `_exportar_excel`) — sem regressões (242/242)

## Change Log
- 2026-04-28: Story criada por @pm — Epic 4, redesign da página relatório
- 2026-04-28: Implementada por @dev (Dex) — 242/242 testes passando, status: Ready for Review
