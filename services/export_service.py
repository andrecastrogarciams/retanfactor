"""
Serviço de exportação PDF para o relatório de recurtimento.
Story 1.4 — Exportar PDF com ReportLab.

Função pública:
    exportar_pdf(rows, filtros, resumo, estacao) -> bytes
"""
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models.report_row import CorDiferenca, ReportRow

logger = logging.getLogger(__name__)

_LOGO_PATH = Path(__file__).parent.parent / "docs" / "logo" / "logo_viposa.png"

# Paleta visual (alinhada com relatorio page)
_COR_VERDE = colors.HexColor("#d4edda")
_COR_AMARELO = colors.HexColor("#fff3cd")
_COR_VERMELHO = colors.HexColor("#f8d7da")
_COR_HEADER = colors.HexColor("#343a40")
_COR_ZEBRA = colors.HexColor("#f8f9fa")
_COR_BORDA = colors.HexColor("#dee2e6")
_BRANCO = colors.white
_PRETO = colors.HexColor("#212529")
_CINZA = colors.HexColor("#6c757d")

# Definição de colunas: (campo em ReportRow, rótulo PDF, largura em pt)
_COLUNAS = [
    ("data_recurtimento", "Data Recurtimento", 52),
    ("artigo",            "Artigo",            65),
    ("cor",               "Cor",               42),
    ("lote_fabricacao",   "Lote Fab.",         52),
    ("codigo_artigo",     "Cod. Artigo",       42),
    ("m2",                "m2",                28),
    ("peso_lote",         "Peso Lote",         38),
    ("kg_m2",             "kg/m2",             33),
    ("kg_ft2",            "kg/ft2",            33),
    ("fator_aplicado",    "Fator",             33),
    ("peso_calculado",    "Peso Calc.",        42),
    ("pct_diferenca",     "% Dif.",            40),
]

_NUMERICAS = {
    "m2", "peso_lote", "kg_m2", "kg_ft2",
    "fator_aplicado", "peso_calculado", "pct_diferenca",
}

_TOP_MARGIN = 2.5 * cm   # espaço reservado no topo para o cabeçalho
_SIDE_MARGIN = 1.5 * cm
_BOT_MARGIN = 1.5 * cm


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _fmt(value, key: str) -> str:
    if value is None:
        return "—"
    if key in _NUMERICAS:
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _draw_header(canvas, doc, *, estacao: str, filtros: dict, emitido_em: str) -> None:
    """Cabeçalho institucional desenhado diretamente no canvas em cada página."""
    canvas.saveState()
    width, height = A4
    lm = doc.leftMargin

    # Posições absolutas: o conteúdo começa em height - topMargin;
    # o cabeçalho ocupa a faixa acima dessa linha.
    rule_y = height - doc.topMargin + 4
    title_y = rule_y + 22
    sub_y = rule_y + 10

    # --- Logo ---
    logo_h = 28
    if _LOGO_PATH.exists():
        try:
            img_reader = ImageReader(str(_LOGO_PATH))
            iw, ih = img_reader.getSize()
            logo_w = (iw / ih) * logo_h
            canvas.drawImage(
                str(_LOGO_PATH),
                lm, rule_y + 2,
                width=logo_w, height=logo_h,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(_CINZA)
            canvas.drawString(lm, rule_y + 10, "[LOGO]")
    else:
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(_CINZA)
        canvas.drawString(lm, rule_y + 10, "[LOGO]")

    # --- Título ---
    canvas.setFillColor(_PRETO)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawCentredString(width / 2, title_y, "Relatório de Recurtimento")

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(_CINZA)
    canvas.drawCentredString(width / 2, sub_y, f"Estação: {estacao}")

    # --- Emissão e período (canto direito) ---
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(width - lm, title_y, f"Emitido: {emitido_em}")
    periodo = (
        f"Período: {filtros.get('data_inicio', '')} → {filtros.get('data_fim', '')}"
    )
    canvas.drawRightString(width - lm, sub_y, periodo)

    # --- Linha separadora ---
    canvas.setStrokeColor(_COR_BORDA)
    canvas.setLineWidth(0.7)
    canvas.line(lm, rule_y, width - lm, rule_y)

    # --- Rodapé ---
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_CINZA)
    canvas.drawCentredString(width / 2, 12, f"Página {doc.page}")

    canvas.restoreState()


def _build_summary_table(resumo: dict) -> Table:
    """Tabela de resumo com métricas totais por faixa de cor (PRD Story 1.4 AC4)."""
    media = resumo.get("media_pct_diferenca")
    media_str = f"{media:.2f}%" if media is not None else "—"

    headers = ["Total Linhas", "Media % Dif.", "Verde", "Amarelo", "Vermelho", "Sem Calculo"]
    values = [
        str(resumo.get("total_linhas", 0)),
        media_str,
        str(resumo.get("total_verde", 0)),
        str(resumo.get("total_amarelo", 0)),
        str(resumo.get("total_vermelho", 0)),
        str(resumo.get("total_sem_calculo", 0)),
    ]

    col_widths = [80, 85, 60, 65, 70, 70]

    style = TableStyle([
        # Cabeçalho
        ("BACKGROUND",    (0, 0), (-1, 0), _COR_HEADER),
        ("TEXTCOLOR",     (0, 0), (-1, 0), _BRANCO),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        # Linha de valores
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1), 11),
        ("BACKGROUND",    (0, 1), (1, 1), _COR_ZEBRA),
        ("BACKGROUND",    (2, 1), (2, 1), _COR_VERDE),
        ("BACKGROUND",    (3, 1), (3, 1), _COR_AMARELO),
        ("BACKGROUND",    (4, 1), (4, 1), _COR_VERMELHO),
        ("BACKGROUND",    (5, 1), (5, 1), _COR_ZEBRA),
        # Borda
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.grey),
    ])

    return Table([headers, values], colWidths=col_widths, style=style)


def _build_data_table(rows: list[ReportRow]) -> Table:
    """Tabela de dados com coloração de % diferença (PRD Story 1.4 AC5)."""
    keys = [k for k, _, _ in _COLUNAS]
    labels = [lb for _, lb, _ in _COLUNAS]
    col_widths = [w for _, _, w in _COLUNAS]
    pct_idx = keys.index("pct_diferenca")

    table_data = [labels]
    cell_styles: list[tuple] = []

    for row_i, row in enumerate(rows, start=1):
        cells = [_fmt(getattr(row, key, None), key) for key in keys]
        table_data.append(cells)

        # Zebra nas linhas pares
        if row_i % 2 == 0:
            cell_styles.append(("BACKGROUND", (0, row_i), (-1, row_i), _COR_ZEBRA))

        # Cor da célula % diferença (PRD Story 1.4 AC5)
        bg = {
            CorDiferenca.VERDE:    _COR_VERDE,
            CorDiferenca.AMARELO:  _COR_AMARELO,
            CorDiferenca.VERMELHO: _COR_VERMELHO,
        }.get(row.cor_diferenca)

        if bg is not None:
            cell_styles.append(
                ("BACKGROUND", (pct_idx, row_i), (pct_idx, row_i), bg)
            )

    base_style = [
        # Cabeçalho
        ("BACKGROUND",    (0, 0), (-1, 0), _COR_HEADER),
        ("TEXTCOLOR",     (0, 0), (-1, 0), _BRANCO),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 7),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",        (0, 0), (-1, 0), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        # Dados
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 6.5),
        ("ALIGN",         (0, 1), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 1), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
        # Grade
        ("GRID",          (0, 0), (-1, -1), 0.3, _COR_BORDA),
        ("LINEABOVE",     (0, 0), (-1, 0), 0.5, _COR_HEADER),
    ]

    style = TableStyle(base_style + cell_styles)
    return Table(table_data, colWidths=col_widths, style=style, repeatRows=1)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def exportar_pdf(
    rows: list[ReportRow],
    filtros: dict,
    resumo: dict,
    estacao: str,
) -> bytes:
    """
    Gera o PDF do relatório de recurtimento.

    Args:
        rows: linhas filtradas do relatório.
        filtros: dicionário com data_inicio, data_fim e filtros opcionais.
        resumo: saída de calcular_resumo() com contagens por faixa de cor.
        estacao: identificação da estação/setor configurada por instância.

    Returns:
        bytes do arquivo PDF pronto para download.

    Raises:
        Exception: qualquer falha é propagada; a UI exibe mensagem de erro.
    """
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=_SIDE_MARGIN,
        rightMargin=_SIDE_MARGIN,
        topMargin=_TOP_MARGIN,
        bottomMargin=_BOT_MARGIN,
    )

    emitido_em = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def _on_page(canvas, doc):
        _draw_header(canvas, doc, estacao=estacao, filtros=filtros, emitido_em=emitido_em)

    story = []

    # --- Resumo (PRD Story 1.4 AC4) ---
    story.append(_build_summary_table(resumo))
    story.append(Spacer(1, 6))

    # --- Filtros ativos ---
    filtro_partes = [
        f"Lote: {filtros['lote']}" if filtros.get("lote") else None,
        f"Artigo: {filtros['artigo']}" if filtros.get("artigo") else None,
        f"Cor: {filtros['cor']}" if filtros.get("cor") else None,
    ]
    filtro_partes = [p for p in filtro_partes if p]
    if filtro_partes:
        p_style = ParagraphStyle(
            "filtro", fontSize=7, textColor=_CINZA, spaceAfter=2
        )
        story.append(Paragraph("Filtros: " + " | ".join(filtro_partes), p_style))

    story.append(HRFlowable(width="100%", thickness=0.5, color=_COR_BORDA, spaceAfter=6))

    # --- Tabela de dados (PRD Story 1.4 AC1-2-5) ---
    if rows:
        story.append(_build_data_table(rows))
    else:
        no_data = ParagraphStyle(
            "nodata", fontSize=9, alignment=TA_CENTER, textColor=_CINZA
        )
        story.append(Spacer(1, 20))
        story.append(Paragraph("Nenhum dado para os filtros selecionados.", no_data))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)

    buf.seek(0)
    return buf.read()
