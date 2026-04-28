# Story 4.4 — Redesign: Página Histórico de Fatores

**Epic:** Epic 4 — Design e UX das Páginas
**Status:** Ready
**Estimativa:** M

## Descrição
Como operador do setor de recurtimento, quero que a tela de histórico de fatores siga o visual "Industrial Precision", para que a consulta e gestão dos registros seja clara, densa em dados e consistente com as demais páginas.

## Acceptance Criteria

1. O header da página deve exibir logo Viposa e título "Histórico de Fatores" via `render_page_header()`.
2. O painel de filtros deve ser exibido em linha horizontal (usando `st.columns`), com labels em **Inter SemiBold 12px**, incluindo filtros de Código do Artigo, Data Início, Data Fim e checkbox "Somente vigentes".
3. A tabela de histórico deve usar AgGrid com:
   - Estilo zebra (alternância de fundo por linha)
   - Header com fundo `#f1f3f5`
   - Altura de linha 36px
   - Colunas numéricas (`Fator`) alinhadas à direita
4. A coluna `Status` deve exibir badge colorido:
   - Azul (`#d5e3ff` / texto `#1f477b`) para `Ativa`
   - Cinza (`#eeedf2` / texto `#43474f`) para `Inativa`
5. As ações **Duplicar** e **Inativar** devem aparecer como botões ícone na coluna de ações, visíveis somente em hover sobre a linha (via CSS `.ag-row:hover`).
6. O modal de inativação deve seguir o padrão do design system:
   - Borda `1px solid #dee2e6`, padding 20px, radius 4px
   - Campo de texto obrigatório "Motivo da inativação"
   - Botão **Confirmar Inativação** primário (`#dc3545`) e botão **Cancelar** secundário
7. Os botões **Limpar** e **Aplicar Filtros** devem seguir estilos secundário e primário respectivamente (Story 4.1).
8. O banner de ambiente (homologação) deve usar o padrão `#dc3545` com ícone de aviso.
9. O `inject_global_css()` deve ser chamado no início da página.

## Escopo

**IN:**
- Header com logo via `render_page_header()`
- Filtros em layout horizontal com `st.columns`
- Tabela AgGrid: zebra, header `#f1f3f5`, altura 36px, alinhamento numérico
- Badge de Status (Ativa/Inativa) via `cellStyle` JsCode
- Botões de ação ícone (Duplicar/Inativar) — visíveis no hover
- Modal de inativação estilizado com campo de motivo obrigatório
- Botões Limpar/Aplicar Filtros nos estilos corretos

**OUT:**
- Alteração da lógica de inativação ou duplicação
- Paginação server-side
- Exportação de dados

## Dependências
- Story 4.1 — `inject_global_css()` e `render_page_header()` disponíveis
- Story 4.2 — padrões AgGrid estabelecidos (zebra, header, altura de linha)

## Riscos
- Ações por linha (Duplicar/Inativar) no AgGrid exigem `cellRenderer` JavaScript. Mitigação: usar `JsCode` para renderizar botões ícone HTML na célula de ações; capturar clique via `AgGrid` `gridOptions` `onCellClicked`.
- Modal de inativação não é nativo do Streamlit. Mitigação: usar `st.expander` estilizado ou `st.dialog` (Streamlit ≥ 1.32) para o fluxo de confirmação.

## Dev Notes

**Arquivo principal:** `pages/03_historico.py`

**Referência visual:**
- `docs/templates/hist_rico_de_fatores_retanfactor/screen.png` e `code.html`
- `docs/templates/hist_rico_de_fatores_inativa_o_retanfactor/screen.png` e `code.html`

**Layout de filtros:**
```python
col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
with col1: codigo = st.text_input("Cód Artigo", placeholder="Digite o código")
with col2: data_inicio = st.date_input("Data Início")
with col3: data_fim = st.date_input("Data Fim")
with col4: somente_vigentes = st.checkbox("Somente vigentes")
with col5:
    st.write("")
    aplicar = st.button("Aplicar Filtros", type="primary")
```

**AgGrid badge de status via JsCode:**
```python
from st_aggrid.shared import JsCode

cell_style_status = JsCode("""
function(params) {
    if (params.value === 'Ativa')
        return { backgroundColor: '#d5e3ff', color: '#1f477b',
                 borderRadius: '12px', padding: '2px 8px',
                 display: 'inline-block', fontWeight: '500' };
    return { backgroundColor: '#eeedf2', color: '#43474f',
             borderRadius: '12px', padding: '2px 8px',
             display: 'inline-block', fontWeight: '500' };
}
""")
```

**Fluxo de inativação (usando st.dialog se disponível):**
```python
@st.dialog("Confirmar Inativação")
def modal_inativacao(fator_id: int):
    st.warning("Esta ação inativará o fator selecionado.")
    motivo = st.text_area("Motivo da inativação *", height=80)
    col_cancel, col_confirm = st.columns([1, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()
    with col_confirm:
        if st.button("Confirmar Inativação", type="primary",
                     use_container_width=True):
            # chamar service de inativação
            ...
```

## Tasks

- [ ] Adicionar `render_page_header("Histórico de Fatores")` e `inject_global_css()` no topo
- [ ] Refatorar filtros para layout horizontal `st.columns` com labels 12px
- [ ] Aplicar tema AgGrid: zebra, header `#f1f3f5`, altura 36px, alinhamento numérico para `Fator`
- [ ] Implementar `cellStyle` via `JsCode` para badge de Status (Ativa/Inativa)
- [ ] Adicionar coluna de ações com botões ícone Duplicar/Inativar via `JsCode` `cellRenderer`
- [ ] Implementar modal de inativação com campo obrigatório e botões primário/secundário
- [ ] Ajustar botões Limpar/Aplicar Filtros para estilos secundário/primário (Story 4.1)
- [ ] Verificar que banner de ambiente usa padrão `#dc3545`
- [ ] Atualizar testes afetados pela refatoração de layout

## Change Log
- 2026-04-28: Story criada por @pm — Epic 4, redesign da página histórico
