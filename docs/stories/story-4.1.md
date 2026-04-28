# Story 4.1 — Design System base: tema Streamlit e CSS Industrial Precision

**Epic:** Epic 4 — Design e UX das Páginas
**Status:** Ready for Review
**Estimativa:** M

## Descrição
Como usuário da aplicação, quero que todas as páginas sigam um visual corporativo coeso, para que a experiência seja profissional e legível em ambiente industrial de escritório.

## Acceptance Criteria

1. A fonte **Inter** deve ser carregada globalmente via `st.markdown` com `@import` do Google Fonts.
2. A paleta do design system "Industrial Precision" deve ser aplicada via CSS customizado:
   - Background da app: `#f9f9fe`
   - Primary (azul industrial): `#001e40`
   - Texto principal: `#1a1c1f`
   - Cards com borda `1px solid #dee2e6`, sem sombra, radius `4px`
3. Deve existir um arquivo `assets/styles.css` com as variáveis CSS e classes reutilizáveis do design system.
4. O `config.py` (ou `app.py`) deve injetar o CSS global em todas as páginas via função `inject_global_css()`.
5. O header de cada página deve exibir o **logo Viposa** (`docs/logo/logo_viposa.png`) alinhado à esquerda, com o título da tela à direita.
6. Os botões primários devem ter background `#001e40` com texto branco; secundários com borda `#001e40` e texto `#001e40`.
7. Os status de diferença devem usar as cores semânticas definidas:
   - Verde: `#28a745`
   - Amarelo: `#ffc107`
   - Vermelho: `#dc3545`

## Escopo

**IN:**
- `assets/styles.css` — variáveis CSS e classes do design system
- Função `inject_global_css()` em `config.py` ou módulo dedicado `assets/theme.py`
- Header padrão com logo + título via função `render_page_header(title)`
- Aplicação do tema em todas as páginas (importar e chamar `inject_global_css()`)
- Tipografia Inter aplicada globalmente

**OUT:**
- Componentes React/JS externos
- Substituição do AgGrid por outro componente de tabela
- Dark mode
- Responsividade mobile

## Dependências
- Nenhuma — story base do épico, sem dependências de outras stories

## Riscos
- Streamlit limita customização de CSS via `st.markdown(unsafe_allow_html=True)`; alguns componentes nativos resistem ao override. Mitigação: aplicar CSS de forma seletiva com seletores específicos.

## Dev Notes

**Arquivos a criar/modificar:**
- `assets/styles.css` — CSS completo do design system
- `assets/theme.py` — funções `inject_global_css()` e `render_page_header(title)`
- `config.py` — importar e chamar `inject_global_css()` na inicialização
- `pages/01_relatorio.py`, `02_cadastro.py`, `03_historico.py` — adicionar `render_page_header()`

**Referência de design:**
- `docs/templates/industrial_precision/DESIGN.md` — sistema de cores, tipografia, espaçamento
- `docs/templates/relat_rio_de_recurtimento_retanfactor/code.html` — implementação de referência em Tailwind/HTML

**CSS global mínimo a implementar:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --color-primary: #001e40;
    --color-primary-container: #003366;
    --color-background: #f9f9fe;
    --color-surface: #ffffff;
    --color-on-surface: #1a1c1f;
    --color-outline: #dee2e6;
    --color-status-green: #28a745;
    --color-status-yellow: #ffc107;
    --color-status-red: #dc3545;
    --radius-card: 4px;
    --font-base: 'Inter', sans-serif;
}

* { font-family: var(--font-base) !important; }

.stApp { background-color: var(--color-background); }
```

## Tasks

- [x] Criar `assets/styles.css` com variáveis CSS e classes do design system
- [x] Criar `assets/theme.py` com `inject_global_css()` e `render_page_header(title)`
- [x] Integrar `inject_global_css()` na inicialização de `config.py`
- [x] Atualizar `pages/01_relatorio.py` para usar `render_page_header()`
- [x] Atualizar `pages/02_cadastro.py` para usar `render_page_header()`
- [x] Atualizar `pages/03_historico.py` para usar `render_page_header()`
- [x] Escrever testes para `inject_global_css()` e `render_page_header()`

## Dev Agent Record

### File List
- `assets/styles.css` — criado
- `assets/theme.py` — criado
- `config.py` — modificado (re-exporta `inject_global_css`, `render_page_header`)
- `pages/01_relatorio.py` — modificado (usa `inject_global_css` + `render_page_header`)
- `pages/02_cadastro.py` — modificado (usa `inject_global_css` + `render_page_header`)
- `pages/03_historico.py` — modificado (usa `inject_global_css` + `render_page_header`)
- `tests/unit/test_theme.py` — criado (9 testes, 242/242 suite passando)

### Completion Notes
- `LOGO_PATH` aponta para `docs/logo/logo_viposa.png` (existente)
- CSS injeta `@import` da Inter via Google Fonts e sobrescreve seletores Streamlit com `!important`
- `render_page_header` usa `st.image` condicionalmente (só se o logo existir)

## Change Log
- 2026-04-28: Story criada por @pm — Epic 4, Design System base
- 2026-04-28: Implementada por @dev (Dex) — 242/242 testes passando, status: Ready for Review
