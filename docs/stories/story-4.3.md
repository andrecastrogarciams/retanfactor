# Story 4.3 — Redesign: Página Cadastro de Fator

**Epic:** Epic 4 — Design e UX das Páginas
**Status:** Ready
**Estimativa:** M

## Descrição
Como operador do setor de recurtimento, quero que a tela de cadastro de fator siga o visual "Industrial Precision", para que o preenchimento seja intuitivo, preciso e visualmente coeso com as demais páginas.

## Acceptance Criteria

1. O header da página deve exibir logo Viposa e título "Cadastro de Fator de Recurtimento" via `render_page_header()`.
2. O formulário deve ser apresentado dentro de um card com borda `1px solid #dee2e6`, padding 20px e radius 4px (sem sombra), centralizado com `max-width` equivalente a `st.columns([1, 2, 1])`.
3. Os campos de input (`Código do artigo`, `Fator`, `Data início vigência`, `Data fim vigência`, `Observação`) devem ter label em **Inter SemiBold 12px** acima de cada campo, altura 40px e borda `#c3c6d1` com foco em `#001e40`.
4. O campo `Descrição do artigo` deve ser exibido como read-only, com fundo `#eeedf2` e texto `#43474f`, indicando preenchimento automático.
5. O botão **Salvar Fator** deve ser primário: background `#001e40`, texto branco, ícone de salvar, hover `#003366`.
6. O botão **Cancelar/Limpar** deve ser secundário: borda `#737780`, texto `#43474f`, sem preenchimento.
7. Mensagens de validação de erro (ex: sobreposição de vigência, campo obrigatório) devem aparecer abaixo do campo afetado em vermelho `#dc3545`, tamanho 12px.
8. O banner de ambiente (homologação) deve usar o padrão `#dc3545` com ícone de aviso.
9. O `inject_global_css()` deve ser chamado no início da página.

## Escopo

**IN:**
- Header com logo via `render_page_header()`
- Card de formulário com padding/borda/radius do design system
- Estilo de inputs, selects e textarea com foco `#001e40`
- Campo de descrição read-only estilizado
- Botões primário/secundário conforme Story 4.1
- Mensagens de validação inline estilizadas

**OUT:**
- Alteração da lógica de validação ou regras de negócio
- Novos campos ou fluxos de cadastro
- Autocomplete via API externo

## Dependências
- Story 4.1 — `inject_global_css()` e `render_page_header()` disponíveis

## Riscos
- Streamlit não possui componente nativo de input com ícone ou lógica de foco visual. Mitigação: usar CSS customizado via `inject_global_css()` para sobrescrever estilos dos `st.text_input`, `st.number_input`, `st.date_input` e `st.text_area`.

## Dev Notes

**Arquivo principal:** `pages/02_cadastro.py`

**Referência visual:** `docs/templates/cadastro_de_fator_retanfactor/screen.png` e `code.html`

**Layout do formulário:**
```python
_, col_form, _ = st.columns([1, 4, 1])
with col_form:
    with st.container():
        # card estilizado via CSS
        codigo = st.selectbox("Código do artigo", ...)
        descricao = st.text_input("Descrição do artigo", value=..., disabled=True)
        fator = st.number_input("Fator", min_value=0.001, step=0.001, format="%.3f")
        data_inicio = st.date_input("Data início vigência")
        data_fim = st.date_input("Data fim vigência (Opcional)")
        observacao = st.text_area("Observação", height=100)
```

**CSS para campos read-only:**
```css
/* Campo descrição read-only */
[data-testid="stTextInput"][data-disabled="true"] input {
    background-color: #eeedf2 !important;
    color: #43474f !important;
    cursor: not-allowed !important;
}
```

**Mensagens de validação inline:**
```python
if erro_sobreposicao:
    st.markdown(
        '<p style="color:#dc3545;font-size:12px;margin-top:4px;">⚠ Vigência sobreposta com fator existente.</p>',
        unsafe_allow_html=True
    )
```

## Tasks

- [ ] Adicionar `render_page_header("Cadastro de Fator de Recurtimento")` e `inject_global_css()` no topo
- [ ] Envolver formulário em card estilizado com borda/padding/radius do design system
- [ ] Aplicar CSS para inputs, selects, textarea: altura 40px, borda `#c3c6d1`, foco `#001e40`
- [ ] Estilizar campo `Descrição do artigo` como read-only (fundo `#eeedf2`, texto `#43474f`)
- [ ] Ajustar botões Salvar/Cancelar para estilos primário/secundário (Story 4.1)
- [ ] Estilizar mensagens de validação inline em vermelho `#dc3545`, 12px
- [ ] Verificar que banner de ambiente usa padrão `#dc3545`
- [ ] Atualizar testes afetados pela refatoração de layout

## Change Log
- 2026-04-28: Story criada por @pm — Epic 4, redesign da página cadastro
