from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "paper" / "figures"
PNG_OUT = OUT_DIR / "kcgsa_pipeline_guardrail_architecture.png"
SVG_OUT = OUT_DIR / "kcgsa_pipeline_guardrail_architecture.svg"
PNG_VERTICAL_OUT = OUT_DIR / "kcgsa_pipeline_guardrail_architecture_vertical.png"
SVG_VERTICAL_OUT = OUT_DIR / "kcgsa_pipeline_guardrail_architecture_vertical.svg"
PNG_COMPACT_OUT = OUT_DIR / "kcgsa_pipeline_guardrail_architecture_compact.png"
SVG_COMPACT_OUT = OUT_DIR / "kcgsa_pipeline_guardrail_architecture_compact.svg"

FONT_REG = Path("C:/Windows/Fonts/NotoSansKR-VF.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")


W, H = 2400, 940
VW, VH = 1200, 2050
CW, CH = 1100, 980

COLORS = {
    "bg": "#ffffff",
    "ink": "#1f2937",
    "muted": "#4b5563",
    "line": "#9ca3af",
    "band": "#f8fafc",
    "band_edge": "#cbd5e1",
    "input": "#f3f4f6",
    "l0": "#dcfce7",
    "l0_edge": "#16a34a",
    "pre": "#e0f2fe",
    "pre_edge": "#0284c7",
    "llm": "#fef3c7",
    "llm_edge": "#d97706",
    "post": "#ede9fe",
    "post_edge": "#7c3aed",
    "response": "#f3f4f6",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REG
    return ImageFont.truetype(str(path), size=size)


def center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    lines: list[str],
    size: int,
    fill: str = COLORS["ink"],
    bold_first: bool = False,
    line_gap: int = 8,
) -> None:
    fonts = [font(size, bold_first and i == 0) for i in range(len(lines))]
    heights = [draw.textbbox((0, 0), line, font=fonts[i])[3] for i, line in enumerate(lines)]
    total_h = sum(heights) + line_gap * (len(lines) - 1)
    y = box[1] + (box[3] - box[1] - total_h) / 2
    for i, line in enumerate(lines):
        fnt = fonts[i]
        bbox = draw.textbbox((0, 0), line, font=fnt)
        x = box[0] + (box[2] - box[0] - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), line, font=fnt, fill=fill)
        y += heights[i] + line_gap


def rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str,
    width: int = 4,
    radius: int = 28,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    fill: str = COLORS["line"],
    width: int = 6,
) -> None:
    draw.line((start, end), fill=fill, width=width)
    x2, y2 = end
    draw.polygon(
        [(x2, y2), (x2 - 22, y2 - 13), (x2 - 22, y2 + 13)],
        fill=fill,
    )


def down_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    fill: str = COLORS["line"],
    width: int = 6,
) -> None:
    draw.line((start, end), fill=fill, width=width)
    x2, y2 = end
    draw.polygon(
        [(x2, y2), (x2 - 14, y2 - 22), (x2 + 14, y2 - 22)],
        fill=fill,
    )


def draw_png() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # Title
    title_f = font(48, bold=True)
    subtitle_f = font(28)
    draw.text((90, 54), "Layer 0 기반 한국어 PII Guardrail Pipeline", font=title_f, fill=COLORS["ink"])
    draw.text(
        (90, 116),
        "Target LLM과 L4 GPT-4o-mini Judge를 분리한 LLM Gateway 구조",
        font=subtitle_f,
        fill=COLORS["muted"],
    )

    # Phase bands
    bands = [
        ((470, 202, 1500, 650), "Input-side / Gateway Guardrails", "입력 단계 차단·마스킹", COLORS["band"]),
        ((1540, 202, 1800, 650), "Service Model", "실제 답변 생성", "#fffbeb"),
        ((1840, 202, 2140, 650), "Output-side Guardrail", "출력 단계 최종 검사", "#faf5ff"),
    ]
    for box, label1, label2, fill in bands:
        rounded_box(draw, box, fill=fill, outline=COLORS["band_edge"], width=3, radius=34)
        center_text(draw, (box[0], box[1] + 20, box[2], box[1] + 82), [label1, label2], 24, fill=COLORS["muted"], bold_first=True, line_gap=3)

    boxes: list[dict[str, object]] = [
        {
            "box": (90, 365, 350, 505),
            "fill": COLORS["input"],
            "edge": COLORS["line"],
            "lines": ["User Input", "사용자 입력"],
        },
        {
            "box": (510, 360, 750, 510),
            "fill": COLORS["l0"],
            "edge": COLORS["l0_edge"],
            "lines": ["L0", "Korean Normalizer", "+ PII Detector"],
        },
        {
            "box": (790, 360, 1010, 510),
            "fill": COLORS["pre"],
            "edge": COLORS["pre_edge"],
            "lines": ["L1", "Presidio PII"],
        },
        {
            "box": (1050, 360, 1270, 510),
            "fill": COLORS["pre"],
            "edge": COLORS["pre_edge"],
            "lines": ["L2", "Bedrock Guardrails", "(during-call)"],
        },
        {
            "box": (1310, 360, 1470, 510),
            "fill": COLORS["pre"],
            "edge": COLORS["pre_edge"],
            "lines": ["L3", "Lakera"],
        },
        {
            "box": (1570, 352, 1770, 518),
            "fill": COLORS["llm"],
            "edge": COLORS["llm_edge"],
            "lines": ["Target LLM", "서비스 모델"],
        },
        {
            "box": (1870, 344, 2110, 526),
            "fill": COLORS["post"],
            "edge": COLORS["post_edge"],
            "lines": ["L4", "GPT-4o-mini Judge", "(post-call)"],
        },
        {
            "box": (2180, 365, 2320, 505),
            "fill": COLORS["response"],
            "edge": COLORS["line"],
            "lines": ["Final", "Response"],
        },
    ]

    for item in boxes:
        rounded_box(draw, item["box"], item["fill"], item["edge"], width=4, radius=26)  # type: ignore[arg-type]
        lines = item["lines"]  # type: ignore[assignment]
        center_text(draw, item["box"], lines, 25, bold_first=True)  # type: ignore[arg-type]

    centers = [
        ((350, 435), (510, 435)),
        ((750, 435), (790, 435)),
        ((1010, 435), (1050, 435)),
        ((1270, 435), (1310, 435)),
        ((1470, 435), (1570, 435)),
        ((1770, 435), (1870, 435)),
        ((2110, 435), (2180, 435)),
    ]
    for start, end in centers:
        arrow(draw, start, end)

    # Notes
    note_box = (90, 710, 2310, 850)
    draw.rounded_rectangle(note_box, radius=24, fill="#f9fafb", outline="#e5e7eb", width=2)
    notes = [
        "L0~L3는 사용자 입력이 Target LLM으로 전달되기 전 PII를 차단·마스킹한다.",
        "Target LLM은 실제 서비스 응답을 생성하고, L4 GPT-4o-mini Judge는 생성된 응답을 최종 검사한다.",
        "※ L2 Bedrock Guardrails는 구현상 during-call 계층이며, 그림에서는 gateway 비교 흐름 안에 배치하였다.",
    ]
    y = 735
    for i, note in enumerate(notes):
        draw.text((125, y), note, font=font(24, bold=(i == 0)), fill=COLORS["ink"] if i < 2 else COLORS["muted"])
        y += 36

    img.save(PNG_OUT, dpi=(300, 300))


def draw_vertical_png() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (VW, VH), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    draw.text((70, 54), "Korean PII Guardrail Pipeline", font=font(46, bold=True), fill=COLORS["ink"])
    draw.text(
        (70, 112),
        "Target LLM과 L4 Judge를 분리한 세로형 구조",
        font=font(28),
        fill=COLORS["muted"],
    )

    # Section bands first, then arrows, then labels/boxes so arrows stay behind text.
    rounded_box(draw, (150, 295, 1050, 1115), fill=COLORS["band"], outline=COLORS["band_edge"], width=3, radius=34)
    rounded_box(draw, (150, 1220, 1050, 1440), fill="#fffbeb", outline=COLORS["band_edge"], width=3, radius=34)
    rounded_box(draw, (150, 1530, 1050, 1805), fill="#faf5ff", outline=COLORS["band_edge"], width=3, radius=34)

    arrow_pairs = [
        ((VW // 2, 260), (VW // 2, 420)),
        ((VW // 2, 515), (VW // 2, 560)),
        ((VW // 2, 645), (VW // 2, 690)),
        ((VW // 2, 790), (VW // 2, 835)),
        ((VW // 2, 920), (VW // 2, 1310)),
        ((VW // 2, 1405), (VW // 2, 1650)),
        ((VW // 2, 1765), (VW // 2, 1875)),
    ]
    for start, end in arrow_pairs:
        down_arrow(draw, start, end)

    center_text(
        draw,
        (190, 320, 610, 390),
        ["Input-side / Gateway Guardrails", "입력 단계 차단·마스킹"],
        23,
        fill=COLORS["muted"],
        bold_first=True,
        line_gap=4,
    )
    center_text(draw, (190, 1245, 540, 1308), ["Service Model", "실제 답변 생성"], 23, fill=COLORS["muted"], bold_first=True, line_gap=4)
    center_text(draw, (190, 1555, 590, 1618), ["Output-side Guardrail", "출력 단계 최종 검사"], 23, fill=COLORS["muted"], bold_first=True, line_gap=4)

    box_w = 620
    x1 = (VW - box_w) // 2
    x2 = x1 + box_w
    steps: list[dict[str, object]] = [
        {"box": (x1, 185, x2, 260), "fill": COLORS["input"], "edge": COLORS["line"], "lines": ["User Input", "사용자 입력"]},
        {"box": (x1, 420, x2, 515), "fill": COLORS["l0"], "edge": COLORS["l0_edge"], "lines": ["L0", "Korean Normalizer + PII Detector"]},
        {"box": (x1, 560, x2, 645), "fill": COLORS["pre"], "edge": COLORS["pre_edge"], "lines": ["L1", "Presidio PII"]},
        {"box": (x1, 690, x2, 790), "fill": COLORS["pre"], "edge": COLORS["pre_edge"], "lines": ["L2", "Bedrock Guardrails", "(during-call)"]},
        {"box": (x1, 835, x2, 920), "fill": COLORS["pre"], "edge": COLORS["pre_edge"], "lines": ["L3", "Lakera"]},
        {"box": (x1, 1310, x2, 1405), "fill": COLORS["llm"], "edge": COLORS["llm_edge"], "lines": ["Target LLM", "서비스 응답 생성 모델"]},
        {"box": (x1, 1650, x2, 1765), "fill": COLORS["post"], "edge": COLORS["post_edge"], "lines": ["L4", "GPT-4o-mini Judge", "(post-call)"]},
        {"box": (x1, 1875, x2, 1960), "fill": COLORS["response"], "edge": COLORS["line"], "lines": ["Final Response", "사용자에게 반환"]},
    ]

    for item in steps:
        rounded_box(draw, item["box"], item["fill"], item["edge"], width=4, radius=24)  # type: ignore[arg-type]
        center_text(draw, item["box"], item["lines"], 26, bold_first=True, line_gap=6)  # type: ignore[arg-type]

    # Callout labels in the long gaps.
    draw.text((650, 1055), "PII neutralized before model call", font=font(22), fill=COLORS["muted"])
    draw.text((650, 1500), "Generated output is inspected", font=font(22), fill=COLORS["muted"])

    img.save(PNG_VERTICAL_OUT, dpi=(300, 300))


def draw_compact_png() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (CW, CH), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    draw.text((58, 45), "Korean PII Guardrail Pipeline", font=font(38, bold=True), fill=COLORS["ink"])
    draw.text((58, 92), "Compact view for paper layout", font=font(22), fill=COLORS["muted"])

    x1, x2 = 245, 855
    boxes: list[dict[str, object]] = [
        {"box": (x1, 150, x2, 220), "fill": COLORS["input"], "edge": COLORS["line"], "lines": ["User Input"]},
        {"box": (x1, 280, x2, 365), "fill": COLORS["l0"], "edge": COLORS["l0_edge"], "lines": ["L0", "Korean PII Guard"]},
        {"box": (x1, 430, x2, 515), "fill": COLORS["pre"], "edge": COLORS["pre_edge"], "lines": ["L1~L3", "Presidio · Bedrock · Lakera"]},
        {"box": (x1, 580, x2, 665), "fill": COLORS["llm"], "edge": COLORS["llm_edge"], "lines": ["Target LLM"]},
        {"box": (x1, 730, x2, 815), "fill": COLORS["post"], "edge": COLORS["post_edge"], "lines": ["L4", "Output Judge"]},
        {"box": (x1, 875, x2, 940), "fill": COLORS["response"], "edge": COLORS["line"], "lines": ["Final Response"]},
    ]

    # Group labels
    draw.text((72, 296), "Input-side", font=font(23, bold=True), fill=COLORS["muted"])
    draw.text((72, 326), "pre-call / gateway", font=font(18), fill=COLORS["muted"])
    draw.text((884, 586), "Service", font=font(23, bold=True), fill=COLORS["muted"])
    draw.text((884, 616), "model call", font=font(18), fill=COLORS["muted"])
    draw.text((884, 742), "Output-side", font=font(23, bold=True), fill=COLORS["muted"])
    draw.text((884, 772), "post-call", font=font(18), fill=COLORS["muted"])

    for item in boxes:
        rounded_box(draw, item["box"], item["fill"], item["edge"], width=4, radius=22)  # type: ignore[arg-type]
        center_text(draw, item["box"], item["lines"], 29, bold_first=True, line_gap=4)  # type: ignore[arg-type]

    for y1, y2 in [(220, 280), (365, 430), (515, 580), (665, 730), (815, 875)]:
        down_arrow(draw, (CW // 2, y1), (CW // 2, y2), width=6)

    img.save(PNG_COMPACT_OUT, dpi=(300, 300))


def svg_text(x: int, y: int, text: str, size: int, weight: int = 400, fill: str = COLORS["ink"], anchor: str = "middle") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
        f'font-family="Noto Sans KR, Malgun Gothic, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(text)}</text>'
    )


def svg_multiline(cx: int, cy: int, lines: list[str], size: int, fill: str = COLORS["ink"]) -> str:
    line_h = int(size * 1.25)
    start_y = cy - (line_h * (len(lines) - 1)) // 2
    parts = []
    for i, line in enumerate(lines):
        weight = 700 if i == 0 else 400
        parts.append(svg_text(cx, start_y + i * line_h, line, size, weight, fill))
    return "\n".join(parts)


def draw_svg() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{COLORS["bg"]}"/>',
        svg_text(90, 86, "Layer 0 기반 한국어 PII Guardrail Pipeline", 48, 700, anchor="start"),
        svg_text(90, 138, "Target LLM과 L4 GPT-4o-mini Judge를 분리한 LLM Gateway 구조", 28, 400, COLORS["muted"], "start"),
        '<defs><marker id="arrow" markerWidth="12" markerHeight="8" refX="11" refY="4" orient="auto"><path d="M0,0 L12,4 L0,8 z" fill="#9ca3af"/></marker></defs>',
    ]

    for x, y, w, h, label1, label2, fill in [
        (470, 202, 1030, 448, "Input-side / Gateway Guardrails", "입력 단계 차단·마스킹", COLORS["band"]),
        (1540, 202, 260, 448, "Service Model", "실제 답변 생성", "#fffbeb"),
        (1840, 202, 300, 448, "Output-side Guardrail", "출력 단계 최종 검사", "#faf5ff"),
    ]:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="34" fill="{fill}" stroke="{COLORS["band_edge"]}" stroke-width="3"/>')
        parts.append(svg_multiline(x + w // 2, y + 55, [label1, label2], 24, COLORS["muted"]))

    box_specs = [
        (90, 365, 260, 140, COLORS["input"], COLORS["line"], ["User Input", "사용자 입력"]),
        (510, 360, 240, 150, COLORS["l0"], COLORS["l0_edge"], ["L0", "Korean Normalizer", "+ PII Detector"]),
        (790, 360, 220, 150, COLORS["pre"], COLORS["pre_edge"], ["L1", "Presidio PII"]),
        (1050, 360, 220, 150, COLORS["pre"], COLORS["pre_edge"], ["L2", "Bedrock Guardrails", "(during-call)"]),
        (1310, 360, 160, 150, COLORS["pre"], COLORS["pre_edge"], ["L3", "Lakera"]),
        (1570, 352, 200, 166, COLORS["llm"], COLORS["llm_edge"], ["Target LLM", "서비스 모델"]),
        (1870, 344, 240, 182, COLORS["post"], COLORS["post_edge"], ["L4", "GPT-4o-mini Judge", "(post-call)"]),
        (2180, 365, 140, 140, COLORS["response"], COLORS["line"], ["Final", "Response"]),
    ]
    for x, y, w, h, fill, edge, lines in box_specs:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="26" fill="{fill}" stroke="{edge}" stroke-width="4"/>')
        parts.append(svg_multiline(x + w // 2, y + h // 2 + 8, lines, 25))

    for x1, y1, x2, y2 in [
        (350, 435, 500, 435),
        (750, 435, 780, 435),
        (1010, 435, 1040, 435),
        (1270, 435, 1300, 435),
        (1470, 435, 1560, 435),
        (1770, 435, 1860, 435),
        (2110, 435, 2170, 435),
    ]:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{COLORS["line"]}" stroke-width="6" marker-end="url(#arrow)"/>')

    parts.append('<rect x="90" y="710" width="2220" height="140" rx="24" fill="#f9fafb" stroke="#e5e7eb" stroke-width="2"/>')
    notes = [
        ("L0~L3는 사용자 입력이 Target LLM으로 전달되기 전 PII를 차단·마스킹한다.", 735, 700, COLORS["ink"]),
        ("Target LLM은 실제 서비스 응답을 생성하고, L4 GPT-4o-mini Judge는 생성된 응답을 최종 검사한다.", 771, 400, COLORS["ink"]),
        ("※ L2 Bedrock Guardrails는 구현상 during-call 계층이며, 그림에서는 gateway 비교 흐름 안에 배치하였다.", 807, 400, COLORS["muted"]),
    ]
    for text, y, weight, fill in notes:
        parts.append(svg_text(125, y, text, 24, weight, fill, "start"))

    parts.append("</svg>")
    SVG_OUT.write_text("\n".join(parts), encoding="utf-8")


def draw_vertical_svg() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{VW}" height="{VH}" viewBox="0 0 {VW} {VH}">',
        f'<rect width="{VW}" height="{VH}" fill="{COLORS["bg"]}"/>',
        svg_text(70, 88, "Korean PII Guardrail Pipeline", 46, 700, anchor="start"),
        svg_text(70, 138, "Target LLM과 L4 Judge를 분리한 세로형 구조", 28, 400, COLORS["muted"], "start"),
        '<defs><marker id="downArrow" markerWidth="8" markerHeight="12" refX="4" refY="11" orient="auto"><path d="M0,0 L8,0 L4,12 z" fill="#9ca3af"/></marker></defs>',
    ]

    for x, y, w, h, label1, label2, fill in [
        (150, 295, 900, 820, "Input-side / Gateway Guardrails", "입력 단계 차단·마스킹", COLORS["band"]),
        (150, 1220, 900, 220, "Service Model", "실제 답변 생성", "#fffbeb"),
        (150, 1530, 900, 275, "Output-side Guardrail", "출력 단계 최종 검사", "#faf5ff"),
    ]:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="34" fill="{fill}" stroke="{COLORS["band_edge"]}" stroke-width="3"/>')
        label_cx = x + 250 if label1.startswith("Input") else x + 225
        parts.append(svg_multiline(label_cx, y + 60, [label1, label2], 23, COLORS["muted"]))

    box_w = 620
    x = (VW - box_w) // 2
    box_specs = [
        (x, 185, box_w, 75, COLORS["input"], COLORS["line"], ["User Input", "사용자 입력"]),
        (x, 420, box_w, 95, COLORS["l0"], COLORS["l0_edge"], ["L0", "Korean Normalizer + PII Detector"]),
        (x, 560, box_w, 85, COLORS["pre"], COLORS["pre_edge"], ["L1", "Presidio PII"]),
        (x, 690, box_w, 100, COLORS["pre"], COLORS["pre_edge"], ["L2", "Bedrock Guardrails", "(during-call)"]),
        (x, 835, box_w, 85, COLORS["pre"], COLORS["pre_edge"], ["L3", "Lakera"]),
        (x, 1310, box_w, 95, COLORS["llm"], COLORS["llm_edge"], ["Target LLM", "서비스 응답 생성 모델"]),
        (x, 1650, box_w, 115, COLORS["post"], COLORS["post_edge"], ["L4", "GPT-4o-mini Judge", "(post-call)"]),
        (x, 1875, box_w, 85, COLORS["response"], COLORS["line"], ["Final Response", "사용자에게 반환"]),
    ]
    for bx, by, bw, bh, fill, edge, lines in box_specs:
        parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="24" fill="{fill}" stroke="{edge}" stroke-width="4"/>')
        parts.append(svg_multiline(bx + bw // 2, by + bh // 2 + 8, lines, 26))

    for y1, y2 in [(260, 410), (515, 550), (645, 680), (790, 825), (920, 1300), (1405, 1640), (1765, 1865)]:
        parts.append(f'<line x1="{VW//2}" y1="{y1}" x2="{VW//2}" y2="{y2}" stroke="{COLORS["line"]}" stroke-width="6" marker-end="url(#downArrow)"/>')

    parts.append(svg_text(650, 1055, "PII neutralized before model call", 22, 400, COLORS["muted"], "start"))
    parts.append(svg_text(650, 1500, "Generated output is inspected", 22, 400, COLORS["muted"], "start"))
    parts.append("</svg>")
    SVG_VERTICAL_OUT.write_text("\n".join(parts), encoding="utf-8")


def draw_compact_svg() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}">',
        f'<rect width="{CW}" height="{CH}" fill="{COLORS["bg"]}"/>',
        svg_text(58, 78, "Korean PII Guardrail Pipeline", 38, 700, anchor="start"),
        svg_text(58, 115, "Compact view for paper layout", 22, 400, COLORS["muted"], "start"),
        '<defs><marker id="downArrow" markerWidth="8" markerHeight="12" refX="4" refY="11" orient="auto"><path d="M0,0 L8,0 L4,12 z" fill="#9ca3af"/></marker></defs>',
    ]

    parts.extend(
        [
            svg_text(72, 318, "Input-side", 23, 700, COLORS["muted"], "start"),
            svg_text(72, 348, "pre-call / gateway", 18, 400, COLORS["muted"], "start"),
            svg_text(884, 608, "Service", 23, 700, COLORS["muted"], "start"),
            svg_text(884, 638, "model call", 18, 400, COLORS["muted"], "start"),
            svg_text(884, 764, "Output-side", 23, 700, COLORS["muted"], "start"),
            svg_text(884, 794, "post-call", 18, 400, COLORS["muted"], "start"),
        ]
    )

    x, bw = 245, 610
    box_specs = [
        (x, 150, bw, 70, COLORS["input"], COLORS["line"], ["User Input"]),
        (x, 280, bw, 85, COLORS["l0"], COLORS["l0_edge"], ["L0", "Korean PII Guard"]),
        (x, 430, bw, 85, COLORS["pre"], COLORS["pre_edge"], ["L1~L3", "Presidio · Bedrock · Lakera"]),
        (x, 580, bw, 85, COLORS["llm"], COLORS["llm_edge"], ["Target LLM"]),
        (x, 730, bw, 85, COLORS["post"], COLORS["post_edge"], ["L4", "Output Judge"]),
        (x, 875, bw, 65, COLORS["response"], COLORS["line"], ["Final Response"]),
    ]
    for bx, by, bw, bh, fill, edge, lines in box_specs:
        parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="22" fill="{fill}" stroke="{edge}" stroke-width="4"/>')
        parts.append(svg_multiline(bx + bw // 2, by + bh // 2 + 8, lines, 29))

    for y1, y2 in [(220, 270), (365, 420), (515, 570), (665, 720), (815, 865)]:
        parts.append(f'<line x1="{CW//2}" y1="{y1}" x2="{CW//2}" y2="{y2}" stroke="{COLORS["line"]}" stroke-width="6" marker-end="url(#downArrow)"/>')

    parts.append("</svg>")
    SVG_COMPACT_OUT.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    draw_png()
    draw_svg()
    draw_vertical_png()
    draw_vertical_svg()
    draw_compact_png()
    draw_compact_svg()
    print(f"wrote {PNG_OUT}")
    print(f"wrote {SVG_OUT}")
    print(f"wrote {PNG_VERTICAL_OUT}")
    print(f"wrote {SVG_VERTICAL_OUT}")
    print(f"wrote {PNG_COMPACT_OUT}")
    print(f"wrote {SVG_COMPACT_OUT}")


if __name__ == "__main__":
    main()
