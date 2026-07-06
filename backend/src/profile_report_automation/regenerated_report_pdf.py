from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Group, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from profile_report_automation.workbook_exports import (
    _build_anchor_summary_lines,
    _build_conclusion_lines,
    _build_culture_summary_lines,
    _build_neopi_summary_lines,
    _build_procedures_label,
    _build_profiler_summary,
)


PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 52
RIGHT_MARGIN = 50
TOP_MARGIN = 42
BOTTOM_MARGIN = 34
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
LOGO_WIDTH = 64
SECTION_MARKER_SIZE = 12
ACCENT_ORANGE = colors.HexColor("#ff5a1f")
TEXT_COLOR = colors.HexColor("#111111")
LIGHT_BORDER = colors.HexColor("#b5b5b5")
GRID_COLOR = colors.HexColor("#d0d0d0")
PROFILER_COLORS = {
    "Executor": colors.HexColor("#ff0000"),
    "Comunicador": colors.HexColor("#ffff00"),
    "Planejador": colors.HexColor("#2e7d32"),
    "Analista": colors.HexColor("#0f6fb6"),
}
ANCHOR_BAR_COLOR = colors.HexColor("#ff5a1f")
CULTURE_LINE_COLOR = colors.HexColor("#ff5a1f")
CULTURE_ORDER = ["Clã", "Inovativa", "Mercado", "Hierárquica"]

METHODOLOGY_TEXT = (
    "O presente documento se propõe a trazer uma síntese do perfil comportamental, dentro do enfoque "
    "organizacional, a partir da análise dos instrumentos supracitados. Destaca-se que os dados aqui "
    "representados são indicadores a serem considerados dentro de todo o contexto. E assim como toda "
    "análise, não se deve entender como uma determinação rígida mas sim, como interpretação de pontos "
    "relevantes a serem considerados em reflexão."
)
NEOPI_INTRO_TEXTS = [
    "O Inventário de Personalidade NEO Revisado (NEO PI-R) é um instrumento de avaliação da personalidade, "
    "validado pelo CFP, baseado no modelo clássico dos Cinco Grandes Fatores, que compreendem a personalidade "
    "a partir da combinação de 5 grandes fatores.",
    "A partir dos resultados apontados pelo NEOPI-R, destacamos características observadas em cada um dos fatores.",
]
PROFILER_INTRO_TEXT = (
    "Ferramenta para mapeamento de estilo comportamental baseado em quatro características comportamentais: "
    "Executores (competitivos e dinâmicos, que não têm medo de assumir riscos e enfrentar desafios), "
    "Comunicadores (extrovertidos, sociáveis, não apreciando monotonias), Planejadores (autocontrolados, "
    "prudentes, observadores e bem adaptados à rotina) e Analistas (detalhistas, precisos, cautelosos e críticos). "
    "As pessoas apresentam características de todos os estilos, usualmente havendo o predomínio de um a três estilos."
)
ANCHORS_INTRO_TEXT = (
    "O questionário visa a reflexão sobre o que é mais importante para você dentro de suas áreas de competência, "
    "objetivos e valores, a partir da categorização em 8 âncoras de carreira: Técnico Funcional, Administração Geral, "
    "Autonomia e Independência, Segurança e Estabilidade, Criatividade Empreendedora, Estilo de Vida, Puro Desafio e "
    "Vontade de Servir."
)
CULTURE_INTRO_TEXT = (
    "O questionário adaptado da teoria Competing Values de Cameron & Quinn identifica as preferências de cultura "
    "organizacional categorizando em 4 tipos de cultura: hierárquica (estabilidade e previsibilidade), clã "
    "(relações humanas), inovadora (flexível e criativa) e de mercado (produtividade e eficiência)."
)


def build_regenerated_pdf_report(
    path: str | Path,
    bundle: dict[str, Any],
    draft: dict[str, Any],
    *,
    logo_path: str | Path | None = None,
) -> None:
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    canvas = Canvas(str(target_path), pagesize=A4)
    canvas.setTitle("Relatorio de Analise de Perfil")

    context = _build_report_context(bundle, draft)
    resolved_logo_path = _resolve_logo_path(logo_path)

    _draw_page_one(canvas, context, resolved_logo_path)
    canvas.showPage()
    _draw_page_two(canvas, context, resolved_logo_path)
    canvas.showPage()
    _draw_page_three(canvas, context, resolved_logo_path)
    canvas.save()


def _build_report_context(bundle: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    person = bundle.get("person", {})

    profiler_scores: list[dict[str, Any]] = []
    for item in bundle.get("profiler", {}).get("scores", []):
        if not isinstance(item, dict):
            continue
        style = str(item.get("style") or "").strip()
        if not style:
            continue
        percentage = float(item.get("percentage") or 0.0)
        profiler_scores.append(
            {
                "style": style,
                "percentage": percentage,
                "color": PROFILER_COLORS.get(style, colors.HexColor("#666666")),
            }
        )

    anchor_scores: list[dict[str, Any]] = []
    for item in bundle.get("career_anchors", {}).get("scores", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        anchor_scores.append(
            {
                "name": name,
                "average": float(item.get("average") or 0.0),
            }
        )

    culture_scores_map = {
        str(item.get("culture") or "").strip(): float(item.get("score") or 0.0)
        for item in bundle.get("cultural_diagnosis", {}).get("scores", [])
        if isinstance(item, dict)
    }

    return {
        "person_rows": [
            ("Nome", str(person.get("name") or "-")),
            ("Data da aplicação", _format_application_date(person.get("application_date"))),
            ("Unidade de negócios", str(person.get("business_unit") or "-")),
            ("Demanda", str(person.get("demand") or "-")),
            ("Cargo", str(person.get("role") or "-")),
            ("Procedimentos realizados", _build_procedures_label(bundle)),
        ],
        "neopi_lines": _build_neopi_summary_lines(bundle, draft),
        "profiler_scores": profiler_scores,
        "profiler_dominant_style": str(bundle.get("profiler", {}).get("dominant_style") or "-"),
        "profiler_summary": _build_profiler_summary(bundle),
        "anchor_scores": anchor_scores,
        "anchor_lines": _build_anchor_summary_lines(bundle),
        "culture_values": [culture_scores_map.get(culture_name, 0.0) for culture_name in CULTURE_ORDER],
        "culture_lines": _build_culture_summary_lines(bundle),
        "conclusion_lines": _build_conclusion_lines(bundle, draft),
    }


def _draw_page_one(canvas: Canvas, context: dict[str, Any], logo_path: Path | None) -> None:
    styles = _build_styles()
    y = PAGE_HEIGHT - TOP_MARGIN

    _draw_logo(canvas, logo_path, y_top=y + 2)
    canvas.setFillColor(TEXT_COLOR)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawCentredString(PAGE_WIDTH / 2, y - 2, "ANÁLISE DE PERFIL COMPORTAMENTAL")
    y -= 34

    y = _draw_section_heading(canvas, "I. Identificação:", y)
    for label, value in context["person_rows"]:
        y = _draw_paragraph(
            canvas,
            f"<b>{escape(label)}:</b> {escape(value)}",
            styles["body"],
            LEFT_MARGIN,
            y,
            CONTENT_WIDTH - 18,
            space_after=7,
        )

    y -= 10
    y = _draw_section_heading(canvas, "II. Metodologia e objetivo:", y)
    y = _draw_paragraph(canvas, escape(METHODOLOGY_TEXT), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 18, 14)

    y = _draw_section_heading(canvas, "III. Resultados da Análise:", y)
    y = _draw_subheading(canvas, "3.1- NEOPI-R", y, styles["subheading"])
    for paragraph in NEOPI_INTRO_TEXTS:
        y = _draw_paragraph(canvas, escape(paragraph), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 18, 7)

    for line in context["neopi_lines"]:
        y = _draw_paragraph(canvas, _format_labeled_text(line), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 18, 8)

    _draw_footer(canvas, 1, 3)


def _draw_page_two(canvas: Canvas, context: dict[str, Any], logo_path: Path | None) -> None:
    styles = _build_styles()
    y = PAGE_HEIGHT - TOP_MARGIN + 4

    _draw_logo(canvas, logo_path, y_top=y)
    y = _draw_section_heading(canvas, "III. Resultados da Análise:", y)
    y = _draw_subheading(canvas, "3.2- Profiler", y, styles["subheading"])
    y = _draw_paragraph(canvas, escape(PROFILER_INTRO_TEXT), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 118, 12)

    profiler_chart = _build_profiler_chart(context["profiler_scores"])
    profiler_chart_y = y - 118
    renderPDF.draw(profiler_chart, canvas, LEFT_MARGIN - 4, profiler_chart_y)
    y = profiler_chart_y - 8

    dominant_style = context["profiler_dominant_style"]
    y = _draw_paragraph(
        canvas,
        f"Nesse momento, apresenta o estilo: <b>{escape(dominant_style)}</b>.",
        styles["body"],
        LEFT_MARGIN,
        y,
        CONTENT_WIDTH - 18,
        space_after=8,
    )
    y = _draw_paragraph(canvas, escape(context["profiler_summary"]), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 18, 16)

    y = _draw_subheading(canvas, "3.3- Âncoras de Carreira", y, styles["subheading"])
    y = _draw_paragraph(canvas, escape(ANCHORS_INTRO_TEXT), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 18, 12)

    anchors_chart = _build_anchor_chart(context["anchor_scores"])
    anchors_chart_y = y - 192
    renderPDF.draw(anchors_chart, canvas, LEFT_MARGIN - 6, anchors_chart_y)
    y = anchors_chart_y - 10

    for line in context["anchor_lines"]:
        y = _draw_paragraph(canvas, _format_labeled_text(line), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 18, 10)

    _draw_footer(canvas, 2, 3)


def _draw_page_three(canvas: Canvas, context: dict[str, Any], logo_path: Path | None) -> None:
    styles = _build_styles()
    y = PAGE_HEIGHT - TOP_MARGIN + 4

    _draw_logo(canvas, logo_path, y_top=y)
    y = _draw_section_heading(canvas, "III. Resultados da Análise:", y)
    y = _draw_subheading(canvas, "3.4- Diagnóstico Cultural", y, styles["subheading"])
    y = _draw_paragraph(canvas, escape(CULTURE_INTRO_TEXT), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 118, 12)

    culture_chart = _build_culture_chart(context["culture_values"])
    culture_chart_y = y - 214
    renderPDF.draw(culture_chart, canvas, LEFT_MARGIN + 24, culture_chart_y)
    y = culture_chart_y - 6

    for line in context["culture_lines"]:
        y = _draw_paragraph(canvas, _format_labeled_text(line), styles["body"], LEFT_MARGIN, y, CONTENT_WIDTH - 18, 10)

    y -= 4
    y = _draw_section_heading(canvas, "IV. Conclusão:", y)
    y = _draw_paragraph(
        canvas,
        "A partir dos indicadores de seu perfil, apresenta:",
        styles["body"],
        LEFT_MARGIN,
        y,
        CONTENT_WIDTH - 18,
        8,
    )

    for index, line in enumerate(context["conclusion_lines"], start=1):
        y = _draw_paragraph(
            canvas,
            f"{index}- {escape(line)}",
            styles["body"],
            LEFT_MARGIN,
            y,
            CONTENT_WIDTH - 18,
            8,
        )

    _draw_footer(canvas, 3, 3)


def _draw_logo(canvas: Canvas, logo_path: Path | None, *, y_top: float) -> None:
    if logo_path is None:
        return

    image = ImageReader(str(logo_path))
    image_width, image_height = image.getSize()
    scale = LOGO_WIDTH / image_width
    logo_height = image_height * scale
    x = PAGE_WIDTH - RIGHT_MARGIN - LOGO_WIDTH
    y = y_top - logo_height
    canvas.drawImage(image, x, y, width=LOGO_WIDTH, height=logo_height, mask="auto")


def _draw_section_heading(canvas: Canvas, title: str, y: float) -> float:
    marker_y = y - 12
    canvas.setFillColor(ACCENT_ORANGE)
    canvas.rect(LEFT_MARGIN - 18, marker_y, SECTION_MARKER_SIZE, SECTION_MARKER_SIZE, fill=1, stroke=0)
    canvas.setFillColor(TEXT_COLOR)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(LEFT_MARGIN, y - 3, title)
    return y - 22


def _draw_subheading(canvas: Canvas, title: str, y: float, style: ParagraphStyle) -> float:
    return _draw_paragraph(canvas, f"<u>{escape(title)}</u>", style, LEFT_MARGIN, y, CONTENT_WIDTH - 18, 6)


def _draw_paragraph(
    canvas: Canvas,
    text: str,
    style: ParagraphStyle,
    x: float,
    y: float,
    width: float,
    space_after: float,
) -> float:
    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(width, PAGE_HEIGHT)
    paragraph.drawOn(canvas, x, y - height)
    return y - height - space_after


def _draw_footer(canvas: Canvas, page_number: int, total_pages: int) -> None:
    canvas.setFillColor(TEXT_COLOR)
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(PAGE_WIDTH / 2, BOTTOM_MARGIN - 2, f"Página {page_number} de {total_pages}")


def _build_styles() -> dict[str, ParagraphStyle]:
    return {
        "body": ParagraphStyle(
            "RegeneratedBody",
            fontName="Helvetica",
            fontSize=10.1,
            leading=12.4,
            textColor=TEXT_COLOR,
            allowWidows=1,
            allowOrphans=1,
        ),
        "subheading": ParagraphStyle(
            "RegeneratedSubheading",
            fontName="Helvetica",
            fontSize=10.8,
            leading=12.2,
            textColor=TEXT_COLOR,
        ),
    }


def _build_profiler_chart(scores: list[dict[str, Any]]) -> Drawing:
    drawing = Drawing(392, 112)
    drawing.add(Rect(0, 8, 392, 94, rx=10, ry=10, fillColor=colors.white, strokeColor=LIGHT_BORDER, strokeWidth=0.9))

    legend_y = 90
    legend_x = 100
    for item in scores:
        color = item["color"]
        style = item["style"]
        drawing.add(Rect(legend_x, legend_y, 7, 7, fillColor=color, strokeColor=colors.black, strokeWidth=0.6))
        drawing.add(String(legend_x + 10, legend_y - 1, style, fontName="Helvetica", fontSize=8.2, fillColor=TEXT_COLOR))
        legend_x += 54 if style != "Comunicador" else 66

    chart_x = 42
    chart_y = 44
    chart_width = 304
    chart_height = 24
    axis_max = 120.0
    total_width = chart_width * (100.0 / axis_max)
    current_x = chart_x
    for item in scores:
        percentage = float(item["percentage"])
        segment_width = total_width * (percentage / 100.0)
        drawing.add(
            Rect(
                current_x,
                chart_y,
                segment_width,
                chart_height,
                fillColor=item["color"],
                strokeColor=colors.black,
                strokeWidth=0.8,
            )
        )
        if segment_width >= 22:
            drawing.add(
                String(
                    current_x + (segment_width / 2),
                    chart_y + 8,
                    _format_percentage(percentage),
                    fontName="Helvetica-Bold",
                    fontSize=7.6,
                    fillColor=TEXT_COLOR,
                    textAnchor="middle",
                )
            )
        current_x += segment_width

    drawing.add(Line(chart_x, chart_y, chart_x, chart_y + chart_height, strokeColor=colors.black, strokeWidth=0.8))
    drawing.add(String(25, chart_y + 6, "Nome", fontName="Helvetica", fontSize=8, fillColor=TEXT_COLOR))
    drawing.add(String(35, chart_y + 8, "1", fontName="Helvetica", fontSize=8, fillColor=TEXT_COLOR))

    for tick in range(0, 121, 20):
        tick_x = chart_x + (chart_width * (tick / axis_max))
        drawing.add(Line(tick_x, chart_y - 3, tick_x, chart_y, strokeColor=TEXT_COLOR, strokeWidth=0.6))
        drawing.add(
            String(
                tick_x,
                chart_y - 16,
                f"{tick},00%",
                fontName="Helvetica",
                fontSize=7.4,
                fillColor=TEXT_COLOR,
                textAnchor="middle",
            )
        )

    return drawing


def _build_anchor_chart(scores: list[dict[str, Any]]) -> Drawing:
    drawing = Drawing(392, 188)
    drawing.add(Rect(0, 0, 392, 182, rx=10, ry=10, fillColor=colors.white, strokeColor=LIGHT_BORDER, strokeWidth=0.9))
    chart_left = 140
    chart_bottom = 46
    chart_width = 170
    chart_height = 104
    max_value = 6.0
    row_height = 12
    bar_height = 8

    for tick in range(0, 7):
        tick_x = chart_left + ((chart_width / max_value) * tick)
        drawing.add(Line(tick_x, chart_bottom, tick_x, chart_bottom + chart_height, strokeColor=GRID_COLOR, strokeWidth=0.6))
        drawing.add(
            String(
                tick_x,
                chart_bottom - 16,
                str(tick),
                fontName="Helvetica",
                fontSize=8,
                fillColor=TEXT_COLOR,
                textAnchor="middle",
            )
        )

    drawing.add(Line(chart_left, chart_bottom, chart_left + chart_width, chart_bottom, strokeColor=TEXT_COLOR, strokeWidth=0.8))

    for index, item in enumerate(scores):
        value = float(item["average"])
        row_y = chart_bottom + chart_height - ((index + 1) * row_height)
        label_lines = _wrap_anchor_label(str(item["name"])).splitlines()
        label_y = row_y + 1
        for offset, line in enumerate(label_lines):
            drawing.add(
                String(
                    chart_left - 12,
                    label_y + ((len(label_lines) - offset - 1) * 7) - 1,
                    line,
                    fontName="Helvetica",
                    fontSize=7.6,
                    fillColor=TEXT_COLOR,
                    textAnchor="end",
                )
            )

        bar_width = chart_width * (value / max_value)
        drawing.add(
            Rect(
                chart_left,
                row_y,
                bar_width,
                bar_height,
                fillColor=ANCHOR_BAR_COLOR,
                strokeColor=colors.black,
                strokeWidth=0.6,
            )
        )
        drawing.add(
            String(
                chart_left + bar_width + 6,
                row_y + 1,
                _format_decimal(value),
                fontName="Helvetica",
                fontSize=8,
                fillColor=TEXT_COLOR,
            )
        )
    return drawing


def _build_culture_chart(values: list[float]) -> Drawing:
    drawing = Drawing(276, 222)
    drawing.add(Rect(0, 0, 276, 214, rx=10, ry=10, fillColor=colors.white, strokeColor=LIGHT_BORDER, strokeWidth=0.9))

    center_x = 132
    center_y = 104
    radius = 76
    max_value = 40.0
    levels = [10, 20, 30, 40]

    for level in levels:
        level_radius = radius * (level / max_value)
        drawing.add(
            Polygon(
                [
                    center_x,
                    center_y + level_radius,
                    center_x + level_radius,
                    center_y,
                    center_x,
                    center_y - level_radius,
                    center_x - level_radius,
                    center_y,
                ],
                fillColor=None,
                strokeColor=GRID_COLOR,
                strokeWidth=0.7,
            )
        )

    drawing.add(Line(center_x, center_y + radius, center_x, center_y - radius, strokeColor=GRID_COLOR, strokeWidth=0.7))
    drawing.add(Line(center_x - radius, center_y, center_x + radius, center_y, strokeColor=GRID_COLOR, strokeWidth=0.7))

    for level in [0, *levels]:
        level_radius = radius * (level / max_value)
        drawing.add(
            String(
                center_x - 22,
                center_y + level_radius - 3,
                str(level),
                fontName="Helvetica",
                fontSize=8,
                fillColor=TEXT_COLOR,
            )
        )

    drawing.add(String(center_x, center_y + radius + 8, "Clã", fontName="Helvetica", fontSize=9, fillColor=TEXT_COLOR, textAnchor="middle"))
    drawing.add(String(center_x + radius + 8, center_y, "Inovativa", fontName="Helvetica", fontSize=9, fillColor=TEXT_COLOR))
    drawing.add(String(center_x, center_y - radius - 14, "Mercado", fontName="Helvetica", fontSize=9, fillColor=TEXT_COLOR, textAnchor="middle"))
    drawing.add(String(center_x - radius - 42, center_y, "Hierárquica", fontName="Helvetica", fontSize=9, fillColor=TEXT_COLOR))

    points: list[float] = []
    vectors = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    for value, (x_vector, y_vector) in zip(values, vectors):
        scaled_radius = radius * (min(max(value, 0.0), max_value) / max_value)
        points.extend([center_x + (scaled_radius * x_vector), center_y + (scaled_radius * y_vector)])

    drawing.add(
        Polygon(
            points,
            fillColor=None,
            strokeColor=CULTURE_LINE_COLOR,
            strokeWidth=2.0,
        )
    )
    return drawing


def _resolve_logo_path(logo_path: str | Path | None) -> Path | None:
    if logo_path is not None:
        candidate = Path(logo_path).expanduser().resolve()
        return candidate if candidate.exists() else None

    default_logo = Path(__file__).resolve().parent / "assets" / "iebt-logo.png"
    return default_logo if default_logo.exists() else None


def _format_application_date(value: Any) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return "-"

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw_value, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return raw_value


def _format_labeled_text(raw_text: str) -> str:
    label, separator, remainder = raw_text.partition(":")
    if not separator:
        return escape(raw_text)
    return f"<b>{escape(label)}:</b>{escape(remainder)}"


def _format_percentage(value: float) -> str:
    return f"{value:.2f}%".replace(".", ",")


def _format_decimal(value: float) -> str:
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _wrap_anchor_label(value: str) -> str:
    normalized = value.replace("Autonomia Independência", "Autonomia\nIndependência")
    normalized = normalized.replace("Autonomia Independencia", "Autonomia\nIndependência")
    normalized = normalized.replace("Segurança Estabilidade", "Segurança\nEstabilidade")
    normalized = normalized.replace("Criatividade Empreendedora", "Criatividade\nEmpreendedora")
    normalized = normalized.replace("Vontade de Servir", "Vontade de Servir")
    return normalized
