const fs = await import("node:fs/promises");
const path = await import("node:path");
const { Presentation, PresentationFile } = await import("@oai/artifact-tool");

const W = 1280;
const H = 720;

const DECK_ID = "capstone-midterm-20260424";
const ROOT = "C:\\Users\\andyw\\Desktop\\My-AI-Security-Project";
const OUT_DIR = path.join(ROOT, "outputs", "capstone_midterm_20260424");
const SCRATCH_DIR = path.resolve(process.env.PPTX_SCRATCH_DIR || path.join(ROOT, "tmp", "slides", DECK_ID));
const PREVIEW_DIR = path.join(SCRATCH_DIR, "preview");
const VERIFICATION_DIR = path.join(SCRATCH_DIR, "verification");
const INSPECT_PATH = path.join(SCRATCH_DIR, "inspect.ndjson");
const MAX_RENDER_VERIFY_LOOPS = 3;

const PAPER = "#F7F4ED";
const PAPER_SOFT = "#FFFCF7";
const WHITE = "#FFFFFF";
const WHITE_88 = "#FFFFFFE0";
const WHITE_96 = "#FFFFFFF5";
const INK = "#101828";
const INK_2 = "#1D2939";
const TEXT = "#344054";
const MUTED = "#667085";
const LINE = "#D0D5DD";
const SUBTLE = "#EAECF0";
const EN_BLUE = "#2E6AE6";
const KR_ORANGE = "#F28C28";
const BASELINE = "#8A9099";
const JUDGE = "#203A8E";
const L0 = "#22A66A";
const FULL = "#0F172A";
const RED = "#D92D20";
const GOLD = "#D4A72C";
const PLUM = "#7A5AF8";
const TRANSPARENT = "#00000000";

const TITLE_FACE = "Malgun Gothic";
const BODY_FACE = "Malgun Gothic";
const MONO_FACE = "Aptos Mono";

const OLD_MEDIA = path.join(ROOT, "tmp_old_media");
const IMG_KDPII = path.join(OLD_MEDIA, "image1.png");
const IMG_KDPII_QUOTE = path.join(OLD_MEDIA, "image2.png");
const IMG_BEDROCK_INPUT = path.join(OLD_MEDIA, "image4.png");
const IMG_BEDROCK_OUTPUT = path.join(OLD_MEDIA, "image5.png");
const IMG_NO_GUARDRAIL = path.join(OLD_MEDIA, "image7.png");
const IMG_GATEWAY = path.join(OLD_MEDIA, "image9.png");

const SOURCES = {
  kdpii: "Li Fei et al., KDPII, IEEE Access (used through the existing project screenshot asset).",
  old_ppt: "Existing capstone PPT screenshots reused as context assets.",
  final4way: path.join(ROOT, "PII", "results", "summaries", "run_e_final_summary.json"),
  standalone: path.join(ROOT, "PII", "results", "phase1", "phase1_l0_standalone.json"),
  mcnemar: path.join(ROOT, "PII", "results", "phase1", "phase1_mcnemar.json"),
  ablation: path.join(ROOT, "PII", "results", "phase3", "phase3_ablation.json"),
  latency: path.join(ROOT, "PII", "results", "phase1", "phase1_latency_precise.json"),
  smartCascade: path.join(ROOT, "PII", "results", "phase3", "phase3_l4_smart_skip.json"),
  robustness: path.join(ROOT, "PII", "results", "phase2", "phase2_v4_final_4way.json"),
  fp: path.join(ROOT, "PII", "results", "phase1", "phase1_fp_test.json"),
  paper: path.join(ROOT, "paper", "capstone_main_v1.md"),
};

const DATA = {
  summary: {
    en: 99.37,
    krSemantic: 49.62,
    l0Stack: 96.39,
  },
  benchmarkCounts: [
    { key: "EN 체크섬", value: 2603, color: EN_BLUE },
    { key: "EN 형식", value: 884, color: "#6EA8FE" },
    { key: "KR 체크섬", value: 522, color: "#FDBA74" },
    { key: "KR 형식", value: 4689, color: KR_ORANGE },
    { key: "KR 의미형", value: 1302, color: RED },
  ],
  baselineLangGap: [
    { label: "영어", value: 99.37, color: EN_BLUE },
    { label: "한국어", value: 69.86, color: KR_ORANGE },
    { label: "한국어 의미형", value: 49.62, color: RED },
  ],
  hardestMisses: [
    { label: "session", value: 95.89 },
    { label: "court", value: 92.75 },
    { label: "allergy", value: 92.31 },
    { label: "company", value: 85.71 },
    { label: "job_title", value: 82.35 },
    { label: "course_grade", value: 80.95 },
  ],
  overall4way: { A: 80.15, B: 90.96, C: 94.32, D: 97.23 },
  lang4way: {
    영어: { A: 99.37, B: 99.37, C: 99.37, D: 99.37 },
    한국어: { A: 69.86, B: 86.46, C: 91.62, D: 96.08 },
  },
  krSemantic4way: { A: 49.62, B: 87.4, C: 96.39, D: 98.85 },
  standalone: {
    overall: 30.96,
    KR: 47.54,
    KR_semantic: 80.65,
    EN: 0.0,
    KR_checksum: 18.58,
  },
  mcnemar: { B_only: 291, C_only: 627, delta: 336, p: "p < 2.04e-28" },
  ablation: {
    baseline: 49.62,
    normOnly: 49.92,
    dictOnly: 87.71,
    full: 89.17,
    normGain: 0.31,
    dictGain: 38.1,
    synergy: 1.14,
  },
  latency: {
    B_p99: 4819,
    C_p99: 830,
    L0_p99: 135,
  },
  smartCascade: {
    total: 10000,
    neutralized: 9432,
    l4Needed: 568,
    recovered: 291,
    sameTrueRate: 97.23,
    reduction: 94.32,
    costSaved10k: 1.27332,
    },
  robustness: {
    v1: { B: 87.4, C: 96.39, gap: 8.99 },
    v4: { B: 84.76, C: 95.41, gap: 10.65 },
    overallV4: { B: 90.43, C: 94.99 },
  },
  fp: {
    after: 2,
    docs: 50,
    fpDocs: 1,
  },
};

const CONFIGS = [
  { key: "A", label: "A 기준선", color: BASELINE },
  { key: "B", label: "B + Judge", color: JUDGE },
  { key: "C", label: "C + L0", color: L0 },
  { key: "D", label: "D 전체", color: FULL },
];

const SLIDE_META = [
  { section: "개요", title: "표지" },
  { section: "개요", title: "한 장 요약" },
  { section: "개요", title: "목차" },
  { section: "문제", title: "프로젝트 시작 배경" },
  { section: "문제", title: "그렇다면 가드레일은 어떨까?" },
  { section: "문제", title: "베드록 가드레일 실험" },
  { section: "문제", title: "원인: 영어 기반 가드레일" },
  { section: "설계", title: "연구 질문과 목표" },
  { section: "설계", title: "AI Gateway 맥락" },
  { section: "설계", title: "데이터 흐름과 삽입 위치" },
  { section: "설계", title: "5계층 방어 파이프라인" },
  { section: "설계", title: "L0 설계 1: 정규화" },
  { section: "설계", title: "L0 설계 2: 탐지기" },
  { section: "평가", title: "평가 방법 개요" },
  { section: "평가", title: "벤치마크 구성" },
  { section: "결과", title: "영어 vs 한국어" },
  { section: "결과", title: "무엇을 특히 놓치는가" },
  { section: "결과", title: "4-way 전체 비교" },
  { section: "결과", title: "4-way EN/KR 분리" },
  { section: "결과", title: "KR semantic 정면 비교" },
  { section: "결과", title: "L0 단독 성능" },
  { section: "결과", title: "L0 단독 성능 해석" },
  { section: "검정", title: "통계 검정" },
  { section: "검정", title: "Ablation" },
  { section: "운영성", title: "지연과 비용" },
  { section: "운영성", title: "Smart Cascade" },
  { section: "운영성", title: "강건성 검증" },
  { section: "운영성", title: "False Positive" },
  { section: "중간발표", title: "성과와 남은 과제" },
  { section: "마무리", title: "결론 및 Q&A" },
];

const inspectRecords = [];

async function pathExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function ensureDirs() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.mkdir(SCRATCH_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(VERIFICATION_DIR, { recursive: true });
}

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function normalizeText(text) {
  if (Array.isArray(text)) return text.map((item) => String(item ?? "")).join("\n");
  return String(text ?? "");
}

function textLineCount(text) {
  const value = normalizeText(text);
  if (!value.trim()) return 0;
  return Math.max(1, value.split(/\n/).length);
}

function requiredTextHeight(text, fontSize, lineHeight = 1.2, minHeight = 8) {
  const lines = textLineCount(text);
  if (lines === 0) return minHeight;
  return Math.max(minHeight, lines * fontSize * lineHeight);
}

function assertTextFits(text, boxHeight, fontSize, role = "text") {
  const required = requiredTextHeight(text, fontSize);
  const tolerance = Math.max(2, fontSize * 0.08);
  if (normalizeText(text).trim() && boxHeight + tolerance < required) {
    throw new Error(
      `${role} text box too short: height=${boxHeight.toFixed(1)}, required=${required.toFixed(1)}, text=${normalizeText(text).slice(0, 80)}`,
    );
  }
}

function wrapText(text, widthChars) {
  const words = normalizeText(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > widthChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) lines.push(current);
  return lines.join("\n");
}

function lineConfig(fill = TRANSPARENT, width = 0) {
  return { style: "solid", fill, width };
}

function recordShape(slideNo, shape, role, shapeType, x, y, w, h) {
  inspectRecords.push({
    kind: "shape",
    slide: slideNo,
    id: shape?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    shapeType,
    bbox: [x, y, w, h],
  });
}

function recordText(slideNo, shape, role, text, x, y, w, h) {
  const value = normalizeText(text);
  inspectRecords.push({
    kind: "textbox",
    slide: slideNo,
    id: shape?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    text: value,
    textChars: value.length,
    textLines: textLineCount(value),
    bbox: [x, y, w, h],
  });
}

function recordImage(slideNo, image, role, imagePath, x, y, w, h) {
  inspectRecords.push({
    kind: "image",
    slide: slideNo,
    id: image?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    path: imagePath,
    bbox: [x, y, w, h],
  });
}

function recordChart(slideNo, chart, role, x, y, w, h) {
  inspectRecords.push({
    kind: "chart",
    slide: slideNo,
    id: chart?.id || `slide-${slideNo}-${role}-${inspectRecords.length + 1}`,
    role,
    bbox: [x, y, w, h],
  });
}

function addShape(slide, geometry, x, y, w, h, fill = TRANSPARENT, line = TRANSPARENT, lineWidth = 0, meta = {}) {
  const shape = slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: lineConfig(line, lineWidth),
  });
  if (meta.slideNo) {
    recordShape(meta.slideNo, shape, meta.role || geometry, geometry, x, y, w, h);
  }
  return shape;
}

function applyTextStyle(box, text, size, color, bold, face, align, valign, autoFit) {
  box.text = text;
  box.text.fontSize = size;
  box.text.color = color;
  box.text.bold = Boolean(bold);
  box.text.alignment = align;
  box.text.verticalAlignment = valign;
  box.text.typeface = face;
  box.text.insets = { left: 0, right: 0, top: 0, bottom: 0 };
  if (autoFit) box.text.autoFit = autoFit;
}

function addText(
  slide,
  slideNo,
  text,
  x,
  y,
  w,
  h,
  {
    size = 22,
    color = INK,
    bold = false,
    face = BODY_FACE,
    align = "left",
    valign = "top",
    fill = TRANSPARENT,
    line = TRANSPARENT,
    lineWidth = 0,
    autoFit = null,
    role = "text",
    checkFit = true,
  } = {},
) {
  if (checkFit) assertTextFits(text, h, size, role);
  const box = addShape(slide, "rect", x, y, w, h, fill, line, lineWidth, { slideNo, role });
  applyTextStyle(box, text, size, color, bold, face, align, valign, autoFit);
  recordText(slideNo, box, role, text, x, y, w, h);
  return box;
}

async function addImage(slide, slideNo, imagePath, position, { fit = "contain", role = "image", geometry = undefined, opacity = 1 } = {}) {
  const image = slide.images.add({
    blob: await readImageBlob(imagePath),
    fit,
    alt: role,
    geometry,
  });
  image.position = position;
  if (opacity !== 1) image.opacity = opacity;
  recordImage(slideNo, image, role, imagePath, position.left, position.top, position.width, position.height);
  return image;
}

function addBackground(slide, slideNo, variant = "light") {
  slide.background.fill = PAPER;
  addShape(slide, "rect", 0, 0, W, H, variant === "dark" ? FULL : PAPER, TRANSPARENT, 0, { slideNo, role: "background" });
  if (variant !== "dark") {
    addShape(slide, "ellipse", -120, -160, 420, 300, "#FFF4DB", TRANSPARENT, 0, { slideNo, role: "bg orb" });
    addShape(slide, "ellipse", 980, 520, 360, 260, "#E8F7EF", TRANSPARENT, 0, { slideNo, role: "bg orb" });
    addShape(slide, "ellipse", 1080, -40, 220, 180, "#EAF0FF", TRANSPARENT, 0, { slideNo, role: "bg orb" });
  }
}

function addHeader(slide, slideNo) {
  const meta = SLIDE_META[slideNo - 1];
  addText(slide, slideNo, meta.section.toUpperCase(), 72, 28, 220, 24, {
    size: 12,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    role: "header section",
    checkFit: false,
  });
  addText(slide, slideNo, `${String(slideNo).padStart(2, "0")} / 30`, 1080, 28, 120, 24, {
    size: 12,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    align: "right",
    role: "header index",
    checkFit: false,
  });
  addShape(slide, "rect", 72, 60, 1136, 1.5, SUBTLE, TRANSPARENT, 0, { slideNo, role: "header rule" });
}

function addTitleBlock(slide, slideNo, title, subtitle = null, { x = 72, y = 82, w = 780 } = {}) {
  addText(slide, slideNo, title, x, y, w, 76, {
    size: 31,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "title",
  });
  if (subtitle) {
    addText(slide, slideNo, subtitle, x, y + 74, w, 44, {
      size: 16,
      color: TEXT,
      face: BODY_FACE,
      role: "subtitle",
    });
  }
}

function addTakeaway(slide, slideNo, text, color = KR_ORANGE, { x = 72, y = 160, w = 900 } = {}) {
  addShape(slide, "roundRect", x, y, w, 40, WHITE_96, color, 1.2, { slideNo, role: "takeaway panel" });
  addShape(slide, "rect", x, y, 8, 40, color, TRANSPARENT, 0, { slideNo, role: "takeaway accent" });
  addText(slide, slideNo, text, x + 22, y + 9, w - 34, 22, {
    size: 15,
    color: INK_2,
    bold: true,
    face: BODY_FACE,
    role: "takeaway text",
    checkFit: false,
  });
}

function addPanel(slide, slideNo, x, y, w, h, { fill = WHITE_96, line = LINE, radius = true, role = "panel" } = {}) {
  return addShape(slide, radius ? "roundRect" : "rect", x, y, w, h, fill, line, 1, { slideNo, role });
}

function addMetricCard(slide, slideNo, x, y, w, h, value, label, { color = L0, note = null } = {}) {
  const compact = h < 118;
  const mini = h < 92;
  const valueSize = mini ? 20 : compact ? 24 : 30;
  const labelSize = mini ? 11 : compact ? 13 : 15;
  const valueY = y + (mini ? 12 : compact ? 14 : 18);
  const labelY = y + (mini ? 40 : compact ? 52 : 74);
  const labelH = mini ? 16 : compact ? 18 : 30;
  addPanel(slide, slideNo, x, y, w, h, { fill: WHITE_96, line: LINE, role: `metric ${label}` });
  addShape(slide, "rect", x, y, w, 6, color, TRANSPARENT, 0, { slideNo, role: `metric accent ${label}` });
  addText(slide, slideNo, value, x + 18, valueY, w - 36, mini ? 28 : compact ? 38 : 52, {
    size: valueSize,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: `metric value ${label}`,
  });
  if (label) {
    addText(slide, slideNo, label, x + 18, labelY, w - 36, labelH, {
      size: labelSize,
      color: TEXT,
      face: BODY_FACE,
      role: `metric label ${label}`,
      checkFit: false,
    });
  }
  if (note && !compact) {
    addText(slide, slideNo, note, x + 18, y + h - 28, w - 36, 18, {
      size: 10,
      color: MUTED,
      face: BODY_FACE,
      role: `metric note ${label}`,
      checkFit: false,
    });
  }
}

function addBulletList(slide, slideNo, items, x, y, w, h, { size = 19, color = INK, role = "bullets", gap = 16 } = {}) {
  let cursorY = y;
  for (const item of items) {
    addShape(slide, "ellipse", x, cursorY + 10, 8, 8, color, TRANSPARENT, 0, { slideNo, role: "bullet dot" });
    const wrapped = wrapText(item, Math.max(24, Math.floor((w - 26) / 12)));
    const boxH = requiredTextHeight(wrapped, size) + 4;
    addText(slide, slideNo, wrapped, x + 20, cursorY, w - 20, boxH, {
      size,
      color,
      face: BODY_FACE,
      role,
    });
    cursorY += boxH + gap;
    if (cursorY > y + h) break;
  }
}

function addChip(slide, slideNo, x, y, text, color, { textColor = INK, width = null } = {}) {
  const w = width ?? Math.max(88, text.length * 8 + 28);
  const solid = textColor === WHITE;
  addShape(slide, "roundRect", x, y, w, 30, solid ? color : WHITE, color, 1, { slideNo, role: `chip ${text}` });
  addShape(slide, "ellipse", x + 12, y + 10, 10, 10, solid ? WHITE : color, TRANSPARENT, 0, { slideNo, role: "chip dot" });
  addText(slide, slideNo, text, x + 30, y + 7, w - 38, 16, {
    size: 12,
    color: textColor,
    face: BODY_FACE,
    bold: true,
    role: `chip label ${text}`,
    checkFit: false,
  });
  return w;
}

function addConfigLegend(slide, slideNo, x, y) {
  let cursor = x;
  for (const config of CONFIGS) {
    const w = addChip(slide, slideNo, cursor, y, config.label, config.color, { textColor: config.key === "D" ? WHITE : INK });
    cursor += w + 10;
  }
}

function styleChart(chart, { direction = "bar", showLegend = false } = {}) {
  if (direction === "column") {
    chart.barOptions.direction = "column";
  }
  chart.hasLegend = showLegend;
  chart.plotAreaFill = TRANSPARENT;
  chart.titleTextStyle.typeface = BODY_FACE;
  chart.titleTextStyle.fontSize = 14;
  chart.titleTextStyle.fill = INK;
  chart.legend.textStyle.typeface = BODY_FACE;
  chart.legend.textStyle.fontSize = 11;
  chart.xAxis.textStyle.typeface = BODY_FACE;
  chart.xAxis.textStyle.fontSize = 12;
  chart.yAxis.textStyle.typeface = BODY_FACE;
  chart.yAxis.textStyle.fontSize = 12;
  chart.dataLabels.showValue = true;
  chart.dataLabels.position = "outEnd";
  chart.dataLabels.textStyle.typeface = BODY_FACE;
  chart.dataLabels.textStyle.fontSize = 11;
  chart.dataLabels.textStyle.fill = INK;
}

function addBarChart(
  slide,
  slideNo,
  {
    x,
    y,
    w,
    h,
    categories,
    series,
    direction = "bar",
    role = "chart",
    showLegend = false,
  },
) {
  const chart = slide.charts.add("bar");
  chart.position = { left: x, top: y, width: w, height: h };
  chart.categories = categories;
  styleChart(chart, { direction, showLegend });
  for (const entry of series) {
    const s = chart.series.add(entry.name);
    s.categories = categories;
    s.values = entry.values;
    s.fill = entry.color;
    s.stroke = { width: 1, style: "solid", fill: entry.color };
  }
  recordChart(slideNo, chart, role, x, y, w, h);
  return chart;
}

function addTwoColumnDivider(slide, slideNo, x = 650) {
  addShape(slide, "rect", x, 120, 1.5, 520, SUBTLE, TRANSPARENT, 0, { slideNo, role: "divider" });
}

function addFlowArrow(slide, slideNo, x1, y1, x2, y2, color = MUTED) {
  const left = Math.min(x1, x2);
  const width = Math.max(18, Math.abs(x2 - x1));
  const top = Math.min(y1, y2) - 6;
  addShape(slide, "rightArrow", left, top, width, 12, color, TRANSPARENT, 0, { slideNo, role: "flow arrow" });
}

function addNotes(slide, body, sourceKeys = []) {
  const lines = sourceKeys.map((key) => `- ${SOURCES[key] || key}`).join("\n");
  slide.speakerNotes.setText(`${body}\n\n[Sources]\n${lines}`);
}

function buildCover(presentation) {
  const slideNo = 1;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addShape(slide, "roundRect", 64, 86, 610, 556, WHITE_96, LINE, 1, { slideNo, role: "cover panel" });
  addShape(slide, "rect", 64, 86, 10, 556, L0, TRANSPARENT, 0, { slideNo, role: "cover accent" });
  addText(slide, slideNo, "MIDTERM PRESENTATION", 90, 98, 220, 20, {
    size: 12,
    color: L0,
    face: MONO_FACE,
    bold: true,
    role: "cover kicker",
    checkFit: false,
  });
  addText(slide, slideNo, "한국어 LLM 게이트웨이에서\n계층형 PII 가드레일의 한계와 Layer 0 설계", 92, 134, 520, 160, {
    size: 34,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cover title",
  });
  addText(slide, slideNo, "영어 중심 가드레일의 한국어 공백을 Layer 0 (L0)가 메운다", 94, 314, 520, 54, {
    size: 18,
    color: TEXT,
    face: BODY_FACE,
    role: "cover subtitle",
  });
  addBulletList(
    slide,
    slideNo,
    [
      "영어는 이미 잘 막지만, 한국어 텍스트형 PII는 기존 스택에서 크게 무너진다.",
      "L0는 한국어 입력을 먼저 정규화하고, 한국어 의미형 PII를 사전 중심으로 보강한다.",
      "결과적으로 LLM Judge보다 더 빠르고 싸면서 한국어 의미형에서 더 높은 탐지율을 보였다.",
    ],
    96,
    400,
    508,
    176,
    { size: 17, color: INK, role: "cover bullets", gap: 12 },
  );
  addText(slide, slideNo, "2026.04  |  CCIT 통합전공 캡스톤 중간발표", 94, 602, 360, 18, {
    size: 11,
    color: MUTED,
    face: MONO_FACE,
    role: "cover footer",
    checkFit: false,
  });

  addPanel(slide, slideNo, 720, 86, 496, 556, { fill: "#101828", line: FULL, role: "cover viz panel" });
  const nodes = [
    { x: 770, y: 170, w: 130, h: 74, label: "사용자 입력", color: WHITE_88, text: INK },
    { x: 934, y: 170, w: 130, h: 74, label: "Layer 0", color: L0, text: WHITE },
    { x: 1098, y: 170, w: 90, h: 74, label: "L1~L3", color: BASELINE, text: WHITE },
    { x: 770, y: 324, w: 130, h: 74, label: "KR 의미형", color: RED, text: WHITE },
    { x: 934, y: 324, w: 130, h: 74, label: "LLM judge", color: JUDGE, text: WHITE },
    { x: 1098, y: 324, w: 90, h: 74, label: "외부 LLM", color: WHITE_88, text: INK },
  ];
  for (const node of nodes) {
    addShape(slide, "roundRect", node.x, node.y, node.w, node.h, node.color, TRANSPARENT, 0, { slideNo, role: `cover node ${node.label}` });
    addText(slide, slideNo, node.label, node.x, node.y + 22, node.w, 28, {
      size: 18,
      color: node.text,
      face: BODY_FACE,
      bold: true,
      align: "center",
      role: `cover node label ${node.label}`,
    });
  }
  addFlowArrow(slide, slideNo, 900, 207, 932, 207, WHITE);
  addFlowArrow(slide, slideNo, 1064, 207, 1096, 207, WHITE);
  addFlowArrow(slide, slideNo, 900, 361, 932, 361, WHITE);
  addFlowArrow(slide, slideNo, 1064, 361, 1096, 361, WHITE);
  addText(slide, slideNo, "핵심 숫자", 762, 464, 120, 18, {
    size: 12,
    color: "#D0D5DD",
    face: MONO_FACE,
    bold: true,
    role: "cover metric label",
    checkFit: false,
  });
  addMetricCard(slide, slideNo, 758, 492, 132, 114, "99.37%", "EN", { color: EN_BLUE, note: "Baseline TRUE" });
  addMetricCard(slide, slideNo, 902, 492, 146, 114, "49.62%", "KR 의미형", { color: RED, note: "기준선 TRUE" });
  addMetricCard(slide, slideNo, 1062, 492, 126, 114, "96.39%", "L0+기존스택", { color: L0, note: "의미형 TRUE" });
  addNotes(slide, "Cover slide. Present the thesis first: Korean semantic PII is the gap, and L0 is the proposed gateway augmentation layer. Team-internal shorthand was v0, but visible slide terminology is Layer 0 (L0).", ["final4way", "paper"]);
}

function buildSummary(presentation) {
  const slideNo = 2;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "한 장 요약", "발표 전체 결론을 먼저 보여주는 슬라이드");
  addTakeaway(slide, slideNo, "영어는 이미 막지만, 한국어 텍스트형 PII는 기존 가드레일에서 큰 공백이 남는다.");
  addMetricCard(slide, slideNo, 92, 258, 326, 170, `${DATA.summary.en.toFixed(2)}%`, "영어 TRUE 탐지율", {
    color: EN_BLUE,
    note: "기준선 A",
  });
  addMetricCard(slide, slideNo, 478, 258, 326, 170, `${DATA.summary.krSemantic.toFixed(2)}%`, "한국어 의미형 TRUE 탐지율", {
    color: RED,
    note: "기준선 A",
  });
  addMetricCard(slide, slideNo, 864, 258, 326, 170, `${DATA.summary.l0Stack.toFixed(2)}%`, "L0 적용 후 의미형", {
    color: L0,
    note: "C = L0 + 기존 스택",
  });
  addPanel(slide, slideNo, 92, 470, 1098, 156, { fill: WHITE_96, line: LINE, role: "summary conclusions" });
  addBulletList(
    slide,
    slideNo,
    [
      "영어는 기준선만으로 99.37%를 기록했지만, 한국어 의미형 PII는 49.62%에 머물렀다.",
      "Layer 0를 기존 스택 앞단에 붙이면 한국어 의미형이 96.39%까지 올라가 LLM Judge보다 높았다.",
      "그리고 p99 지연 830ms, L4 호출 94.32% 절감으로 Judge 대비 더 실용적인 운영 구성이 가능했다.",
    ],
    118,
    496,
    1042,
    108,
    { size: 18, color: INK, role: "summary bullets", gap: 14 },
  );
  addNotes(slide, "Use this slide to set the three messages: KR/EN gap, why L0 exists, and why L0 is practical versus the judge.", ["final4way", "latency", "paper"]);
}

function buildAgenda(presentation) {
  const slideNo = 3;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "목차", "문제에서 운영성까지 한 흐름으로 간다");
  const items = [
    ["01", "문제 정의", "왜 한국어가 영어보다 더 취약한가"],
    ["02", "설계", "왜 Layer 0를 게이트웨이에 넣었는가"],
    ["03", "평가", "왜 이 결과를 믿을 수 있는가"],
    ["04", "결과", "4-way 비교와 한국어 의미형 핵심 결과"],
    ["05", "운영성", "지연, 비용, cascade, FP, robustness"],
    ["06", "중간발표 정리", "현재까지 증명한 것과 남은 과제"],
  ];
  let y = 192;
  for (const [idx, title, desc] of items) {
    addPanel(slide, slideNo, 120, y, 1040, 68, { fill: WHITE_96, line: SUBTLE, role: `agenda ${idx}` });
    addMetricCard(slide, slideNo, 120, y, 120, 68, idx, "", { color: KR_ORANGE });
    addText(slide, slideNo, title, 270, y + 18, 220, 24, {
      size: 22,
      color: INK,
      bold: true,
      face: TITLE_FACE,
      role: `agenda title ${idx}`,
      checkFit: false,
    });
    addText(slide, slideNo, desc, 510, y + 20, 580, 20, {
      size: 15,
      color: TEXT,
      face: BODY_FACE,
      role: `agenda desc ${idx}`,
      checkFit: false,
    });
    y += 80;
  }
  addNotes(slide, "Agenda slide. Keep it short and frame the deck as one continuous narrative, not two disconnected mini-presentations.", ["paper"]);
}

function buildBackground(presentation) {
  const slideNo = 4;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "프로젝트 시작 배경", "문제의 출발점은 한국어 PII 자체의 난도였다");
  addTakeaway(slide, slideNo, "한국어 PII는 모델이 원래부터 어려워하는 영역이었고, 그 위에 영어 기반 가드레일이 다시 얹혀 있다.");
  addPanel(slide, slideNo, 72, 232, 448, 326, { fill: WHITE_96, line: LINE, role: "background text" });
  addBulletList(
    slide,
    slideNo,
    [
      "KDPII는 한국어 대화형 PII 비식별화를 정면으로 다룬 공개 연구다.",
      "해당 연구는 영어 범용 PII보다 한국어 특화 PII에서 성능이 유의하게 낮음을 보여준다.",
      "즉, 한국어 LLM 보안 문제는 애초에 더 어려운 데이터 분포에서 시작한다.",
    ],
    96,
    260,
    400,
    220,
    { size: 18, color: INK, role: "background bullets", gap: 14 },
  );
  addText(slide, slideNo, "논문 근거", 96, 500, 120, 18, {
    size: 12,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    role: "background label",
    checkFit: false,
  });
  addText(slide, slideNo, "IEEE Access, KDPII (기존 PPT 자산 재활용)", 96, 522, 260, 18, {
    size: 12,
    color: TEXT,
    face: BODY_FACE,
    role: "background citation",
    checkFit: false,
  });
  addPanel(slide, slideNo, 556, 232, 650, 326, { fill: WHITE, line: LINE, role: "kdpii image panel" });
  addImage(slide, slideNo, IMG_KDPII, { left: 572, top: 248, width: 618, height: 238 }, { fit: "contain", role: "KDPII screenshot" });
  addPanel(slide, slideNo, 556, 576, 650, 70, { fill: FULL, line: FULL, role: "quote bar" });
  addText(
    slide,
    slideNo,
    "KDPII: 주요 언어모델은 범용 PII보다 한국어 특화 PII 인식에서 더 낮은 성능을 보였다.",
    584,
    597,
    596,
    20,
    {
      size: 14,
      color: WHITE,
      face: BODY_FACE,
      role: "KDPII quote",
      checkFit: false,
    },
  );
  addNotes(slide, "Background slide using existing PPT assets from KDPII. The point is not yet the gateway stack; it is that Korean-specific PII starts harder than English.", ["kdpii", "old_ppt"]);
}

function buildGuardrailQuestion(presentation) {
  const slideNo = 5;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "그렇다면 가드레일은 어떨까?", "모델이 못 잡는다면, 게이트웨이 앞단 방어가 먼저 작동해야 한다");
  addTakeaway(slide, slideNo, "모델이 못 잡으면 게이트웨이 앞단이 막아야 한다.", RED, { w: 620 });
  addPanel(slide, slideNo, 72, 222, 430, 380, { fill: WHITE_96, line: LINE, role: "guardrail question text" });
  addBulletList(
    slide,
    slideNo,
    [
      "기업 환경에서는 사용자 입력이 외부 LLM으로 가기 전에 게이트웨이를 통과한다.",
      "따라서 한국어 PII 보호 문제는 모델 성능뿐 아니라 게이트웨이 방어 구조의 문제다.",
      "이 발표는 기존 가드레일 조합이 한국어에서 실제로 얼마나 비는지부터 확인한다.",
    ],
    96,
    252,
    382,
    260,
    { size: 18, color: INK, role: "guardrail question bullets", gap: 14 },
  );
  addPanel(slide, slideNo, 540, 212, 666, 430, { fill: FULL, line: FULL, role: "no guardrail image frame" });
  addImage(slide, slideNo, IMG_NO_GUARDRAIL, { left: 556, top: 228, width: 634, height: 398 }, { fit: "contain", role: "No guardrail gateway diagram" });
  addNotes(slide, "Use the existing no-guardrail gateway visual to pivot from the general background into the gateway-specific question.", ["old_ppt"]);
}

function buildBedrockExperiment(presentation) {
  const slideNo = 6;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "베드록 가드레일 실험", "정량보다 먼저, 직관적으로 한국어 텍스트형 PII를 놓치는 사례를 보여준다");
  addTakeaway(slide, slideNo, "이름은 가렸지만 주민번호는 그대로 남았다.", RED, { w: 520 });
  addPanel(slide, slideNo, 72, 224, 538, 330, { fill: WHITE, line: LINE, role: "bedrock input frame" });
  addPanel(slide, slideNo, 670, 224, 538, 330, { fill: WHITE, line: LINE, role: "bedrock output frame" });
  addText(slide, slideNo, "입력", 94, 234, 80, 20, {
    size: 13,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    role: "input label",
    checkFit: false,
  });
  addText(slide, slideNo, "결과", 692, 234, 80, 20, {
    size: 13,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    role: "output label",
    checkFit: false,
  });
  addImage(slide, slideNo, IMG_BEDROCK_INPUT, { left: 88, top: 258, width: 506, height: 280 }, { fit: "contain", role: "Bedrock input" });
  addImage(slide, slideNo, IMG_BEDROCK_OUTPUT, { left: 686, top: 258, width: 506, height: 280 }, { fit: "contain", role: "Bedrock output" });
  addMetricCard(slide, slideNo, 72, 582, 540, 82, "이름은 마스킹", "하지만 주민번호는 그대로 통과", { color: GOLD });
  addMetricCard(slide, slideNo, 670, 582, 540, 82, "한국어 의미형 PII", "숫자형·정규식형보다 더 취약한 영역", { color: RED });
  addNotes(slide, "This slide keeps the old Bedrock experiment screenshots but rewrites the framing around what the audience should notice immediately.", ["old_ppt"]);
}

function buildRootCause(presentation) {
  const slideNo = 7;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "원인: 대부분 가드레일은 영어 기반", "문제는 한국어 전체라기보다 한국어 텍스트형 PII의 공백이다");
  addTakeaway(slide, slideNo, "영어 중심 탐지 + 한국어 숫자형 편중 + 텍스트형 blind spot이 겹친다.");
  addCardTriple(
    slide,
    slideNo,
    [
      ["영어 중심 탐지", "기존 baseline은 English에서 99.37% TRUE detection을 기록한다."],
      ["한국어 숫자형 위주", "한국어 지원은 주민번호·사업자번호 같은 checksum / format PII에 편중돼 있다."],
      ["텍스트형 blind spot", "KR semantic slice에서는 baseline TRUE detection이 49.62%까지 떨어진다."],
    ],
    [EN_BLUE, GOLD, RED],
  );
  addPanel(slide, slideNo, 840, 458, 330, 176, { fill: WHITE_96, line: LINE, role: "early evidence panel" });
  addText(slide, slideNo, "기존 PPT 실험 증거", 860, 478, 160, 18, {
    size: 12,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    role: "early table label",
    checkFit: false,
  });
  addImage(slide, slideNo, IMG_EARLY_TABLE, { left: 858, top: 506, width: 294, height: 108 }, { fit: "contain", role: "Early Korean vs English miss table" });
  addNotes(slide, "Root-cause slide. One old 1k-sample table is kept as a contextual inset, but the main message is rewritten around the current 10k results.", ["final4way", "old_ppt"]);
}

function addCardTriple(slide, slideNo, cards, colors) {
  const baseX = 72;
  const y = 236;
  const gap = 24;
  const w = 368;
  for (let i = 0; i < 3; i += 1) {
    const x = baseX + i * (w + gap);
    const [title, body] = cards[i];
    addPanel(slide, slideNo, x, y, w, 188, { fill: WHITE_96, line: LINE, role: `triple card ${title}` });
    addShape(slide, "rect", x, y, 10, 188, colors[i], TRANSPARENT, 0, { slideNo, role: `triple accent ${title}` });
    addText(slide, slideNo, title, x + 24, y + 24, w - 40, 28, {
      size: 22,
      color: INK,
      bold: true,
      face: TITLE_FACE,
      role: `triple title ${title}`,
    });
    addText(slide, slideNo, wrapText(body, 28), x + 24, y + 72, w - 42, 92, {
      size: 17,
      color: TEXT,
      face: BODY_FACE,
      role: `triple body ${title}`,
    });
  }
}

function buildGoal(presentation) {
  const slideNo = 8;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "연구 질문과 프로젝트 목표", "이번 발표에서는 목표를 '한국어 PII 보강 계층'으로 정직하게 정의한다");
  addTakeaway(slide, slideNo, "보호 엔진 전체가 아니라, 기존 스택의 한국어 공백을 메우는 Layer 0가 목표다.", L0, { w: 760 });
  addPanel(slide, slideNo, 72, 238, 550, 354, { fill: WHITE_96, line: LINE, role: "rq panel" });
  addText(slide, slideNo, "RQ1", 98, 266, 60, 20, {
    size: 13,
    color: KR_ORANGE,
    face: MONO_FACE,
    bold: true,
    role: "rq1 label",
    checkFit: false,
  });
  addText(slide, slideNo, "왜 기존 가드레일은 영어 대비 한국어, 특히 KR semantic에서 크게 약한가?", 98, 296, 480, 46, {
    size: 22,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "rq1 title",
  });
  addText(slide, slideNo, wrapText("언어 차이 자체인지, 혹은 한국어 텍스트형 PII라는 어려운 slice 때문인지 분리해서 확인한다.", 34), 98, 350, 480, 56, {
    size: 17,
    color: TEXT,
    face: BODY_FACE,
    role: "rq1 desc",
  });
  addText(slide, slideNo, "RQ2", 98, 438, 60, 20, {
    size: 13,
    color: L0,
    face: MONO_FACE,
    bold: true,
    role: "rq2 label",
    checkFit: false,
  });
  addText(slide, slideNo, "LLM judge를 붙이는 대신, Layer 0가 더 싸고 빠르게 같은 공백을 메울 수 있는가?", 98, 468, 480, 46, {
    size: 22,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "rq2 title",
  });
  addText(slide, slideNo, wrapText("결과 비교뿐 아니라 latency, cost, smart cascade까지 포함해 실용성을 평가한다.", 34), 98, 522, 480, 40, {
    size: 17,
    color: TEXT,
    face: BODY_FACE,
    role: "rq2 desc",
  });
  addPanel(slide, slideNo, 662, 238, 546, 354, { fill: FULL, line: FULL, role: "goal panel" });
  addText(slide, slideNo, "프로젝트 목표", 694, 266, 180, 20, {
    size: 13,
    color: "#98A2B3",
    face: MONO_FACE,
    bold: true,
    role: "goal label",
    checkFit: false,
  });
  addText(slide, slideNo, "한국어 PII 보강 계층\nLayer 0 (L0)", 694, 300, 420, 92, {
    size: 34,
    color: WHITE,
    bold: true,
    face: TITLE_FACE,
    role: "goal title",
  });
  addText(slide, slideNo, wrapText("기존 L1~L3 스택을 버리지 않고, 그 앞단에서 한국어 입력을 먼저 정규화·탐지해 KR semantic blind spot을 메우는 계층", 26), 694, 412, 442, 92, {
    size: 19,
    color: "#D0D5DD",
    face: BODY_FACE,
    role: "goal desc",
  });
  addChip(slide, slideNo, 694, 534, "팀 내부 표기: v0", L0, { textColor: WHITE, width: 160 });
  addChip(slide, slideNo, 868, 534, "발표 표기: L0", WHITE, { textColor: INK, width: 140 });
  addNotes(slide, "Define the goal carefully: not a full standalone protection engine, but a Korean augmentation layer in front of the existing stack.", ["paper", "standalone"]);
}

function buildGatewayContext(presentation) {
  const slideNo = 9;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "AI Gateway 맥락", "이 연구는 모델 자체가 아니라 LLM 게이트웨이에서의 방어 배치 문제다");
  addTakeaway(slide, slideNo, "입력과 출력이 오가는 교차점이기 때문에, L0는 게이트웨이에 붙는 것이 맞다.", JUDGE, { w: 700 });
  addPanel(slide, slideNo, 72, 228, 420, 392, { fill: WHITE_96, line: LINE, role: "gateway text panel" });
  addBulletList(
    slide,
    slideNo,
    [
      "게이트웨이는 사용자 입력과 외부 LLM 사이를 통제하는 계층이다.",
      "이 지점에서 라우팅, 로깅, 인증, 입력/출력 가드레일이 함께 작동한다.",
      "따라서 한국어 입력 보호 문제를 해결하려면 모델 내부가 아니라 게이트웨이 전처리 계층이 핵심이다.",
    ],
    96,
    258,
    372,
    280,
    { size: 18, color: INK, role: "gateway bullets", gap: 14 },
  );
  addPanel(slide, slideNo, 528, 210, 680, 432, { fill: FULL, line: FULL, role: "gateway image frame" });
  addImage(slide, slideNo, IMG_GATEWAY, { left: 544, top: 226, width: 648, height: 400 }, { fit: "contain", role: "AI Gateway diagram" });
  addNotes(slide, "Gateway context slide using the existing dark AI Gateway asset. The narrative point is deployment position, not architecture detail for its own sake.", ["old_ppt"]);
}

function buildInsertionPoint(presentation) {
  const slideNo = 10;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "데이터 흐름과 삽입 위치", "Layer 0는 외부 LLM 호출 전에 한국어 입력을 먼저 복원하고 탐지한다");
  addTakeaway(slide, slideNo, "삽입 위치는 pre-call 앞단이다. 여기서 한국어 입력을 복원하지 않으면 뒤 레이어는 그대로 놓친다.", L0, { w: 900 });
  const boxes = [
    { x: 92, y: 310, w: 138, h: 76, label: "사용자 입력", fill: WHITE_96, text: INK },
    { x: 256, y: 310, w: 138, h: 76, label: "Layer 0", fill: L0, text: WHITE },
    { x: 420, y: 310, w: 138, h: 76, label: "Presidio", fill: BASELINE, text: WHITE },
    { x: 584, y: 310, w: 138, h: 76, label: "Bedrock", fill: BASELINE, text: WHITE },
    { x: 748, y: 310, w: 138, h: 76, label: "Lakera", fill: BASELINE, text: WHITE },
    { x: 912, y: 310, w: 138, h: 76, label: "외부 LLM", fill: FULL, text: WHITE },
    { x: 1076, y: 310, w: 110, h: 76, label: "응답", fill: WHITE_96, text: INK },
  ];
  for (const box of boxes) {
    addShape(slide, "roundRect", box.x, box.y, box.w, box.h, box.fill, TRANSPARENT, 0, { slideNo, role: `flow box ${box.label}` });
    addText(slide, slideNo, box.label, box.x, box.y + 24, box.w, 24, {
      size: 18,
      color: box.text,
      bold: true,
      face: BODY_FACE,
      align: "center",
      role: `flow label ${box.label}`,
      checkFit: false,
    });
  }
  for (let i = 0; i < boxes.length - 1; i += 1) {
    addFlowArrow(slide, slideNo, boxes[i].x + boxes[i].w, 348, boxes[i + 1].x, 348, MUTED);
  }
  addShape(slide, "roundRect", 240, 264, 170, 160, TRANSPARENT, RED, 3, { slideNo, role: "highlight L0" });
  addText(slide, slideNo, "이번 연구의 추가 계층", 248, 432, 160, 18, {
    size: 12,
    color: RED,
    face: MONO_FACE,
    bold: true,
    align: "center",
    role: "highlight note",
    checkFit: false,
  });
  addPanel(slide, slideNo, 72, 492, 1114, 118, { fill: WHITE_96, line: LINE, role: "flow notes panel" });
  addBulletList(
    slide,
    slideNo,
    [
      "L0는 한국어 입력을 정규화해 공격 표면을 복원한다.",
      "그 다음 L1~L3는 기존 운영 스택을 그대로 유지한다.",
      "필요한 경우에만 L4 judge를 smart cascade로 호출할 수 있다.",
    ],
    96,
    514,
    1068,
    80,
    { size: 17, color: INK, role: "flow notes", gap: 10 },
  );
  addNotes(slide, "This slide makes the insertion point explicit. It is more important than showing every gateway subsystem.", ["paper"]);
}

function buildFiveLayers(presentation) {
  const slideNo = 11;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "5계층 방어 파이프라인", "L0만 새로 제안하고, 나머지는 기존 운영 가드레일을 그대로 둔다");
  addTakeaway(slide, slideNo, "핵심은 기존 스택을 대체하는 것이 아니라, 한국어 공백을 앞단에서 보강하는 것이다.", L0, { w: 760 });
  const layers = [
    { title: "L0", body: "한국어 정규화 + 키워드 사전", color: L0, top: 236 },
    { title: "L1", body: "Presidio\nregex + NER", color: BASELINE, top: 236 },
    { title: "L2", body: "Bedrock Guardrails", color: BASELINE, top: 236 },
    { title: "L3", body: "Lakera Guard", color: BASELINE, top: 236 },
    { title: "L4", body: "GPT-4o-mini judge", color: JUDGE, top: 236 },
  ];
  let x = 82;
  for (const layer of layers) {
    addPanel(slide, slideNo, x, layer.top, 214, 250, { fill: WHITE_96, line: LINE, role: `layer panel ${layer.title}` });
    addShape(slide, "rect", x, layer.top, 214, 12, layer.color, TRANSPARENT, 0, { slideNo, role: `layer accent ${layer.title}` });
    addText(slide, slideNo, layer.title, x + 22, layer.top + 28, 70, 34, {
      size: 30,
      color: layer.color,
      bold: true,
      face: TITLE_FACE,
      role: `layer title ${layer.title}`,
    });
    addText(slide, slideNo, layer.body, x + 22, layer.top + 84, 170, 62, {
      size: 18,
      color: INK,
      bold: true,
      face: BODY_FACE,
      role: `layer body ${layer.title}`,
    });
    const mode = layer.title === "L4" ? "post-call" : layer.title === "L2" ? "during-call" : "pre-call";
    addChip(slide, slideNo, x + 22, layer.top + 176, mode, layer.color, {
      textColor: layer.title === "L0" || layer.title === "L4" ? WHITE : INK,
      width: 110,
    });
    addText(slide, slideNo, layer.title === "L0" ? "이번 연구의 핵심 기여" : "기존 운영 스택", x + 22, layer.top + 214, 160, 18, {
      size: 11,
      color: MUTED,
      face: BODY_FACE,
      role: `layer note ${layer.title}`,
      checkFit: false,
    });
    x += 230;
  }
  addText(slide, slideNo, "입력", 88, 186, 40, 18, { size: 12, color: MUTED, face: MONO_FACE, bold: true, role: "input word", checkFit: false });
  addText(slide, slideNo, "LLM 응답", 1128, 186, 70, 18, { size: 12, color: MUTED, face: MONO_FACE, bold: true, role: "output word", checkFit: false });
  addNotes(slide, "Pipeline slide. Emphasize that the research contribution is L0, not the existence of the whole stack itself.", ["paper", "final4way"]);
}

function buildNormalizer(presentation) {
  const slideNo = 12;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "L0 설계 1: 정규화 파이프라인", "정규화의 목적은 한국어 입력에 숨겨진 공격 표면을 다시 복원하는 것이다");
  addTakeaway(slide, slideNo, "정규화는 성능의 중심이 아니라, 사전 매칭이 작동하도록 공격 표면을 복구하는 역할이다.", GOLD, { w: 860 });
  const cards = [
    ["자모 결합", "ㅎㅏㄴㄱㅡㄹ → 한글"],
    ["ZWSP 제거", "주민\u200b번호 → 주민번호"],
    ["Fullwidth 복원", "１２３４ → 1234"],
    ["숫자-한글 변환", "공이공칠일사 → 020714"],
    ["Homoglyph 치환", "O0 / I1 혼용 정리"],
  ];
  let x = 78;
  for (let i = 0; i < cards.length; i += 1) {
    const [title, ex] = cards[i];
    addPanel(slide, slideNo, x, 248, 220, 228, { fill: WHITE_96, line: LINE, role: `norm card ${title}` });
    addShape(slide, "ellipse", x + 72, 274, 72, 72, i % 2 === 0 ? "#EAF2FF" : "#FFF0E0", TRANSPARENT, 0, { slideNo, role: `norm icon ${title}` });
    addText(slide, slideNo, title, x + 18, 366, 184, 26, {
      size: 20,
      color: INK,
      bold: true,
      face: TITLE_FACE,
      align: "center",
      role: `norm title ${title}`,
    });
    addText(slide, slideNo, ex, x + 18, 404, 184, 50, {
      size: 17,
      color: TEXT,
      face: BODY_FACE,
      align: "center",
      role: `norm ex ${title}`,
    });
    x += 234;
  }
  addPanel(slide, slideNo, 78, 518, 1124, 94, { fill: WHITE_96, line: LINE, role: "norm summary" });
  addBulletList(
    slide,
    slideNo,
    [
      "전체 13단계 정규화 중 발표에서는 대표 5개만 보여준다.",
      "핵심은 사람이 읽는 한국어와 시스템이 매칭하는 문자열을 다시 맞추는 것이다.",
    ],
    104,
    540,
    1070,
    52,
    { size: 17, color: INK, role: "norm summary bullets", gap: 10 },
  );
  addNotes(slide, "Normalizer slide. Keep the examples simple and concrete; no need to enumerate all 13 steps in the oral talk.", ["paper", "ablation"]);
}

function buildDetector(presentation) {
  const slideNo = 13;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "L0 설계 2: 탐지기", "정규식보다 키워드 사전이 실제 개선의 중심이다");
  addTakeaway(slide, slideNo, "KR semantic 성능 상승의 대부분은 키워드 사전에서 나온다.", RED, { w: 620 });
  addPanel(slide, slideNo, 78, 236, 532, 350, { fill: WHITE_96, line: LINE, role: "regex panel" });
  addPanel(slide, slideNo, 670, 236, 532, 350, { fill: WHITE_96, line: LINE, role: "dict panel" });
  addText(slide, slideNo, "정규식 / 구조형 탐지", 102, 264, 200, 24, {
    size: 24,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "regex title",
    checkFit: false,
  });
  addBulletList(
    slide,
    slideNo,
    [
      "session token, JWT, court case number",
      "GPS 좌표, AWS key, SSH key, MAC",
      "medical record number, employee ID",
      "차량번호, 보험증권번호, 거래번호",
    ],
    102,
    312,
    470,
    220,
    { size: 18, color: TEXT, role: "regex bullets", gap: 12 },
  );
  addText(slide, slideNo, "키워드 사전 / 의미형 탐지", 694, 264, 240, 24, {
    size: 24,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "dict title",
    checkFit: false,
  });
  addBulletList(
    slide,
    slideNo,
    [
      "allergy, diagnosis, prescription, surgery",
      "family, marital, religion, nationality",
      "company, department, job title, school",
      "의료·법적·조직 맥락의 한국어 텍스트형 PII",
    ],
    694,
    312,
    470,
    220,
    { size: 18, color: TEXT, role: "dict bullets", gap: 12 },
  );
  addMetricCard(slide, slideNo, 450, 604, 380, 72, "+38.10%p", "사전만 켜도 KR semantic이 크게 상승", { color: RED });
  addMetricCard(slide, slideNo, 848, 604, 220, 72, "+0.31%p", "정규화만 단독", { color: GOLD });
  addNotes(slide, "Detector slide. Separate structured regex coverage from dictionary-driven semantic coverage so the audience understands why L0 is targeted to Korean semantic PII.", ["paper", "ablation"]);
}

function buildEvalOverview(presentation) {
  const slideNo = 14;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "평가 방법 개요", "이 결과를 믿을 수 있는 이유를 한 장에서 정리한다");
  addTakeaway(slide, slideNo, "핵심은 validity-first, real API calls, 그리고 TRUE/FALSE/BYPASS 분리다.", JUDGE, { w: 700 });
  const cards = [
    ["Validity-first fuzzer v4", "유효하지 않은 payload가 섞이면 가드레일 실패와 데이터 오류가 구분되지 않기 때문에, 체크섬·포맷·의미형 유효성을 먼저 보장했다."],
    ["Real API benchmark", "모든 케이스를 실제 LiteLLM gateway와 외부 guardrail / judge 호출로 측정해 논리 시뮬레이션이 아니라 운영 지표를 확보했다."],
    ["TRUE / FALSE / BYPASS", "단순 출력 변화가 아니라 실제 PII neutralization 여부를 기준으로 평가해, 가짜 탐지를 제외했다."],
  ];
  addCardTriple(slide, slideNo, cards, [EN_BLUE, JUDGE, L0]);
  addMetricCard(slide, slideNo, 92, 492, 250, 118, "10,000", "같은 payload로 4-way 비교", { color: KR_ORANGE });
  addMetricCard(slide, slideNo, 364, 492, 250, 118, "91 types", "PII coverage", { color: GOLD });
  addMetricCard(slide, slideNo, 636, 492, 250, 118, "TRUE", "실제 neutralization 기준", { color: L0 });
  addMetricCard(slide, slideNo, 908, 492, 250, 118, "v4", "validity-first benchmark", { color: JUDGE });
  addNotes(slide, "Method overview slide. The audience should leave this slide believing the benchmark design, not memorizing implementation details.", ["paper", "final4way"]);
}

function buildBenchmarkComposition(presentation) {
  const slideNo = 15;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "벤치마크 구성", "10k stratified sample에서 영어 / 한국어 / validity group 분포를 고정했다");
  addTakeaway(slide, slideNo, "발표의 핵심 slice는 KR semantic 1,302건이다.", RED, { w: 520 });
  let x = 74;
  for (const item of DATA.benchmarkCounts) {
    addMetricCard(slide, slideNo, x, 252, 214, 154, item.value.toLocaleString("en-US"), item.key, { color: item.color });
    x += 226;
  }
  addPanel(slide, slideNo, 74, 452, 1128, 150, { fill: WHITE_96, line: LINE, role: "benchmark notes" });
  addBulletList(
    slide,
    slideNo,
    [
      "전체 10,000건 중 English는 3,487건, Korean은 6,513건이다.",
      "그중 KR semantic 1,302건이 발표의 메인 타깃이며, 기존 가드레일의 취약성이 가장 강하게 드러나는 slice다.",
      "모든 4-way 구성은 이 동일한 payload를 공유한다.",
    ],
    100,
    478,
    1068,
    104,
    { size: 17, color: INK, role: "benchmark bullets", gap: 12 },
  );
  addNotes(slide, "Benchmark composition slide. Keep the count cards large and make KR semantic stand out as the central slice.", ["final4way"]);
}

function buildLangGap(presentation) {
  const slideNo = 16;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "핵심 문제 데이터: 영어 vs 한국어", "기준선 A만 놓고 보면 영어와 한국어의 차이는 이미 충분히 크다");
  addTakeaway(slide, slideNo, "영어는 잘 막지만 한국어 텍스트형 PII는 절반 수준까지 떨어진다.", RED, { w: 720 });
  let chipX = 74;
  for (const item of DATA.baselineLangGap) {
    chipX += addChip(slide, slideNo, chipX, 218, item.label, item.color, { textColor: item.label === "KR semantic" ? WHITE : INK }) + 10;
  }
  addPanel(slide, slideNo, 74, 252, 720, 350, { fill: WHITE_96, line: LINE, role: "lang gap chart panel" });
  addBarChart(slide, slideNo, {
    x: 96,
    y: 286,
    w: 676,
    h: 286,
    categories: ["TRUE detection"],
    direction: "bar",
    role: "lang gap chart",
    series: DATA.baselineLangGap.map((item) => ({ name: item.label, values: [item.value], color: item.color })),
  });
  addMetricCard(slide, slideNo, 828, 282, 360, 132, "-29.51%p", "Korean vs English gap", { color: KR_ORANGE });
  addMetricCard(slide, slideNo, 828, 438, 360, 132, "-49.75%p", "KR semantic vs English gap", { color: RED });
  addNotes(slide, "This is the main language-gap slide. The audience should immediately see that the real collapse is on Korean semantic PII, not English.", ["final4way"]);
}

function buildHardestMisses(presentation) {
  const slideNo = 17;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "무엇을 특히 놓치는가", "Baseline이 특히 취약한 PII 유형은 대부분 한국어 텍스트형 PII다");
  addTakeaway(slide, slideNo, "session, court, allergy, company, job_title에서 실패율이 극단적으로 높다.", RED, { w: 760 });
  addPanel(slide, slideNo, 74, 248, 838, 370, { fill: WHITE_96, line: LINE, role: "hardest chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 280,
    w: 790,
    h: 310,
    categories: DATA.hardestMisses.map((item) => item.label),
    direction: "bar",
    role: "hardest misses chart",
    series: [{ name: "Real bypass rate", values: DATA.hardestMisses.map((item) => item.value), color: RED }],
  });
  addPanel(slide, slideNo, 944, 248, 258, 370, { fill: FULL, line: FULL, role: "hardest note panel" });
  addText(slide, slideNo, "읽는 법", 970, 276, 90, 20, {
    size: 12,
    color: "#98A2B3",
    face: MONO_FACE,
    bold: true,
    role: "hardest note label",
    checkFit: false,
  });
  addBulletList(
    slide,
    slideNo,
    [
      "막대는 baseline A의 real bypass rate(%)다.",
      "높을수록 기존 스택이 놓치는 비율이 크다.",
      "상위 유형 대부분이 한국어 의미형 또는 문맥형 PII다.",
    ],
    970,
    306,
    200,
    180,
    { size: 17, color: WHITE, role: "hardest note bullets", gap: 12 },
  );
  addMetricCard(slide, slideNo, 970, 506, 180, 86, "95.89%", "session bypass", { color: RED });
  addNotes(slide, "Hardest misses slide. Use bypass rate so the pain is obvious.", ["final4way"]);
}

function buildOverall4Way(presentation) {
  const slideNo = 18;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "4-way 전체 비교", "L0 포함 구성이 LLM judge 포함 baseline보다 높다");
  addTakeaway(slide, slideNo, "전체 10k 기준에서도 C(+L0)가 B(+judge)보다 높다.", L0, { w: 620 });
  addConfigLegend(slide, slideNo, 74, 218);
  addPanel(slide, slideNo, 74, 252, 760, 336, { fill: WHITE_96, line: LINE, role: "overall chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 292,
    w: 712,
    h: 268,
    categories: ["10k benchmark"],
    direction: "bar",
    role: "overall 4way chart",
    series: CONFIGS.map((config) => ({ name: config.label, values: [DATA.overall4way[config.key]], color: config.color })),
  });
  addMetricCard(slide, slideNo, 870, 272, 310, 120, "94.32%", "C = L0 + existing stack", { color: L0 });
  addMetricCard(slide, slideNo, 870, 414, 310, 120, "+3.36%p", "C vs B overall", { color: L0 });
  addNotes(slide, "Overall 4-way slide. The core comparison is B versus C, not only A versus D.", ["final4way"]);
}

function buildLangSplit4Way(presentation) {
  const slideNo = 19;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "4-way 한국어/영어 분리 비교", "개선 여지는 영어가 아니라 한국어에 있다");
  addTakeaway(slide, slideNo, "English는 이미 포화 상태고, 한국어가 실제 개선 구간이다.", KR_ORANGE, { w: 640 });
  addConfigLegend(slide, slideNo, 74, 218);
  addPanel(slide, slideNo, 74, 252, 850, 350, { fill: WHITE_96, line: LINE, role: "lang split chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 286,
    w: 802,
    h: 286,
    categories: Object.keys(DATA.lang4way),
    direction: "column",
    role: "lang split chart",
    series: CONFIGS.map((config) => ({
      name: config.label,
      values: Object.keys(DATA.lang4way).map((key) => DATA.lang4way[key][config.key]),
      color: config.color,
    })),
  });
  addMetricCard(slide, slideNo, 954, 274, 236, 130, "99.37%", "English ceiling", { color: EN_BLUE });
  addMetricCard(slide, slideNo, 954, 426, 236, 130, "96.08%", "Korean full stack", { color: KR_ORANGE });
  addNotes(slide, "Language split slide. The key oral line is that English stays flat across configurations while Korean drives the gains.", ["final4way"]);
}

function buildKrSemantic(presentation) {
  const slideNo = 20;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "KR semantic 정면 비교", "이 발표의 핵심 figure");
  addTakeaway(slide, slideNo, "L0가 GPT-4o-mini judge를 KR semantic에서 +8.99%p 능가한다.", RED, { w: 700 });
  addConfigLegend(slide, slideNo, 74, 218);
  addPanel(slide, slideNo, 74, 252, 760, 336, { fill: WHITE_96, line: LINE, role: "kr semantic chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 292,
    w: 712,
    h: 268,
    categories: ["KR semantic"],
    direction: "bar",
    role: "kr semantic chart",
    series: CONFIGS.map((config) => ({
      name: config.label,
      values: [DATA.krSemantic4way[config.key]],
      color: config.color,
    })),
  });
  addMetricCard(slide, slideNo, 864, 272, 326, 120, "96.39%", "C = L0 + existing stack", { color: L0 });
  addMetricCard(slide, slideNo, 864, 414, 326, 120, "+8.99%p", "C vs B on KR semantic", { color: RED });
  addNotes(slide, "KR semantic head-to-head slide. This is the primary result figure for the midterm talk.", ["final4way"]);
}

function buildStandalone(presentation) {
  const slideNo = 21;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "L0(v0) 단독 성능", "Standalone 수치를 따로 떼서 보여줘야 보강 계층 framing이 정직해진다");
  addTakeaway(slide, slideNo, "L0는 standalone 엔진이 아니라 한국어 보강 계층으로 보는 것이 맞다.", L0, { w: 720 });
  addMetricCard(slide, slideNo, 92, 264, 250, 160, `${DATA.standalone.overall.toFixed(2)}%`, "overall", { color: BASELINE });
  addMetricCard(slide, slideNo, 368, 264, 250, 160, `${DATA.standalone.KR.toFixed(2)}%`, "KR", { color: KR_ORANGE });
  addMetricCard(slide, slideNo, 644, 264, 250, 160, `${DATA.standalone.KR_semantic.toFixed(2)}%`, "KR semantic", { color: L0 });
  addMetricCard(slide, slideNo, 920, 264, 250, 160, `${DATA.standalone.EN.toFixed(2)}%`, "EN", { color: EN_BLUE });
  addPanel(slide, slideNo, 92, 468, 1078, 136, { fill: WHITE_96, line: LINE, role: "standalone notes" });
  addBulletList(
    slide,
    slideNo,
    [
      "KR semantic만 놓고 보면 80.65%로 강한 편이다.",
      "하지만 EN 0.00%, overall 30.96%이기 때문에 전체 보호 엔진으로 말하면 과장된다.",
      "따라서 L0의 정체성은 '한국어 보강 계층'이 가장 정확하다.",
    ],
    116,
    492,
    1032,
    92,
    { size: 17, color: INK, role: "standalone bullets", gap: 12 },
  );
  addNotes(slide, "Standalone slide. This is the honesty slide that prevents overclaiming L0 as a full engine.", ["standalone"]);
}

function buildStandaloneInterpretation(presentation) {
  const slideNo = 22;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "L0 단독 성능의 해석", "무엇을 잘하고, 무엇을 의도적으로 안 하며, 무엇이 약한지 분리한다");
  addTakeaway(slide, slideNo, "L0의 강점과 한계를 같이 보여줘야 발표 논리가 단단해진다.", GOLD, { w: 640 });
  addCardTriple(
    slide,
    slideNo,
    [
      ["잘하는 것", "KR semantic 80.65%\n한국어 의미형 PII 보강"],
      ["의도적으로 안 하는 것", "EN 0.00%\n영어는 기존 스택에 맡김"],
      ["약한 것", "KR checksum 18.58%\n체크섬형은 기존 레이어가 더 강함"],
    ],
    [L0, EN_BLUE, RED],
  );
  addMetricCard(slide, slideNo, 408, 506, 464, 84, "한국어 보호 엔진이 아니라 한국어 보강 계층", "발표 framing", { color: L0 });
  addNotes(slide, "Interpretation slide. This is where you explicitly name L0 as an augmentation layer.", ["standalone", "paper"]);
}

function buildMcNemar(presentation) {
  const slideNo = 23;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "통계 검정", "숫자 차이가 우연이 아니라는 점을 B vs C 한 장으로 정리한다");
  addTakeaway(slide, slideNo, "B(+judge)보다 C(+L0)만 맞힌 케이스가 훨씬 더 많다.", RED, { w: 680 });
  addPanel(slide, slideNo, 74, 252, 690, 320, { fill: WHITE_96, line: LINE, role: "mcnemar chart panel" });
  addBarChart(slide, slideNo, {
    x: 104,
    y: 290,
    w: 630,
    h: 248,
    categories: ["Matched-pair wins"],
    direction: "bar",
    role: "mcnemar chart",
    series: [
      { name: "B only", values: [DATA.mcnemar.B_only], color: JUDGE },
      { name: "C only", values: [DATA.mcnemar.C_only], color: L0 },
    ],
  });
  addPanel(slide, slideNo, 804, 252, 386, 320, { fill: FULL, line: FULL, role: "mcnemar stats panel" });
  addMetricCard(slide, slideNo, 838, 286, 150, 92, `${DATA.mcnemar.B_only}`, "B only", { color: JUDGE });
  addMetricCard(slide, slideNo, 1006, 286, 150, 92, `${DATA.mcnemar.C_only}`, "C only", { color: L0 });
  addMetricCard(slide, slideNo, 838, 404, 318, 92, `${DATA.mcnemar.delta}건`, "차이", { color: RED });
  addText(slide, slideNo, DATA.mcnemar.p, 838, 530, 318, 22, {
    size: 18,
    color: WHITE,
    bold: true,
    face: TITLE_FACE,
    align: "center",
    role: "mcnemar p",
    checkFit: false,
  });
  addNotes(slide, "McNemar slide. Keep only B vs C; do not dilute the narrative with every pairwise test.", ["mcnemar"]);
}

function buildAblation(presentation) {
  const slideNo = 24;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "Ablation", "효과의 대부분은 정규식이 아니라 키워드 사전에서 나온다");
  addTakeaway(slide, slideNo, "KR semantic 개선의 약 96%가 사전에서 발생했다.", RED, { w: 620 });
  addPanel(slide, slideNo, 74, 252, 760, 338, { fill: WHITE_96, line: LINE, role: "ablation chart panel" });
  addBarChart(slide, slideNo, {
    x: 100,
    y: 290,
    w: 708,
    h: 270,
    categories: ["Baseline", "+Norm only", "+Dict only", "+Full"],
    direction: "column",
    role: "ablation chart",
    series: [{ name: "KR semantic TRUE", values: [DATA.ablation.baseline, DATA.ablation.normOnly, DATA.ablation.dictOnly, DATA.ablation.full], color: RED }],
  });
  addMetricCard(slide, slideNo, 870, 266, 300, 90, `+${DATA.ablation.normGain.toFixed(2)}%p`, "정규화 단독", { color: GOLD });
  addMetricCard(slide, slideNo, 870, 380, 300, 90, `+${DATA.ablation.dictGain.toFixed(2)}%p`, "사전 단독", { color: RED });
  addMetricCard(slide, slideNo, 870, 494, 300, 90, `+${DATA.ablation.synergy.toFixed(2)}%p`, "시너지", { color: L0 });
  addNotes(slide, "Ablation slide. This is where you justify the dictionary-heavy design of L0.", ["ablation"]);
}

function buildLatencyCost(presentation) {
  const slideNo = 25;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "지연과 비용 비교", "L0는 judge보다 느리지 않고, 오히려 운영성 측면에서 더 낫다");
  addTakeaway(slide, slideNo, "C(+L0)는 B(+judge)보다 더 빠르고 더 싸다.", L0, { w: 520 });
  addPanel(slide, slideNo, 74, 252, 524, 336, { fill: WHITE_96, line: LINE, role: "latency panel" });
  addText(slide, slideNo, "p99 latency", 100, 282, 140, 22, {
    size: 22,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "latency title",
    checkFit: false,
  });
  addMetricCard(slide, slideNo, 100, 326, 212, 126, `${DATA.latency.B_p99.toLocaleString("en-US")}ms`, "B + judge", { color: JUDGE });
  addMetricCard(slide, slideNo, 344, 326, 212, 126, `${DATA.latency.C_p99.toLocaleString("en-US")}ms`, "C + L0", { color: L0 });
  addMetricCard(slide, slideNo, 222, 476, 212, 82, `${DATA.latency.L0_p99}ms`, "L0 layer alone", { color: GOLD });

  addPanel(slide, slideNo, 640, 252, 548, 336, { fill: WHITE_96, line: LINE, role: "cost panel" });
  addText(slide, slideNo, "10k calls cost", 666, 282, 180, 22, {
    size: 22,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cost title",
    checkFit: false,
  });
  addMetricCard(slide, slideNo, 666, 326, 226, 126, `$${DATA.cost.B_10k.toFixed(2)}`, "B + judge", { color: JUDGE });
  addMetricCard(slide, slideNo, 926, 326, 226, 126, `$${DATA.cost.C_10k.toFixed(2)}`, "C + L0", { color: L0 });
  addMetricCard(slide, slideNo, 796, 476, 226, 82, "judge 대비 대폭 절감", "운영 비용", { color: RED });
  addNotes(slide, "Latency/cost slide. This is a practical-decision slide, not just a performance slide.", ["latency", "paper"]);
}

function buildSmartCascade(presentation) {
  const slideNo = 26;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "Smart Cascade", "탐지율을 유지한 채 L4 judge 호출을 극단적으로 줄일 수 있다");
  addTakeaway(slide, slideNo, "10,000건 중 568건에만 judge를 호출해도 최종 TRUE rate는 그대로 유지된다.", L0, { w: 860 });
  const funnel = [
    { x: 100, y: 280, w: 1020, h: 72, fill: FULL, text: WHITE, value: "10,000", label: "전체 케이스" },
    { x: 170, y: 370, w: 880, h: 72, fill: L0, text: WHITE, value: "9,432", label: "L0~L3에서 neutralized" },
    { x: 330, y: 460, w: 560, h: 72, fill: JUDGE, text: WHITE, value: "568", label: "L4 judge 호출" },
    { x: 450, y: 550, w: 320, h: 72, fill: KR_ORANGE, text: WHITE, value: "291", label: "L4가 추가 회수" },
  ];
  for (const row of funnel) {
    addShape(slide, "roundRect", row.x, row.y, row.w, row.h, row.fill, TRANSPARENT, 0, { slideNo, role: `funnel ${row.label}` });
    addText(slide, slideNo, row.value, row.x + 32, row.y + 14, 160, 36, {
      size: 30,
      color: row.text,
      bold: true,
      face: TITLE_FACE,
      role: `funnel value ${row.label}`,
      checkFit: false,
    });
    addText(slide, slideNo, row.label, row.x + 220, row.y + 24, row.w - 260, 22, {
      size: 18,
      color: row.text,
      face: BODY_FACE,
      role: `funnel label ${row.label}`,
      checkFit: false,
    });
  }
  addMetricCard(slide, slideNo, 930, 242, 250, 100, `${DATA.smartCascade.reduction.toFixed(2)}%`, "L4 호출 절감", { color: L0 });
  addMetricCard(slide, slideNo, 930, 356, 250, 100, `${DATA.smartCascade.sameTrueRate.toFixed(2)}%`, "최종 TRUE 유지", { color: JUDGE });
  addNotes(slide, "Smart cascade slide. The core message is identical detection with much fewer judge calls.", ["smartCascade"]);
}

function buildRobustness(presentation) {
  const slideNo = 27;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "강건성 검증", "더 어려운 v4에서도 L0 우위는 유지된다");
  addTakeaway(slide, slideNo, "KR semantic에서 B-C 격차가 +8.99%p에서 +10.65%p로 오히려 커졌다.", RED, { w: 880 });
  addPanel(slide, slideNo, 74, 252, 760, 336, { fill: WHITE_96, line: LINE, role: "robustness chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 286,
    w: 712,
    h: 270,
    categories: ["v1 KR semantic", "v4 KR semantic"],
    direction: "column",
    role: "robustness chart",
    series: [
      { name: "B + judge", values: [DATA.robustness.v1.B, DATA.robustness.v4.B], color: JUDGE },
      { name: "C + L0", values: [DATA.robustness.v1.C, DATA.robustness.v4.C], color: L0 },
    ],
  });
  addMetricCard(slide, slideNo, 870, 266, 300, 90, `+${DATA.robustness.v1.gap.toFixed(2)}%p`, "v1 gap", { color: JUDGE });
  addMetricCard(slide, slideNo, 870, 380, 300, 90, `+${DATA.robustness.v4.gap.toFixed(2)}%p`, "v4 gap", { color: RED });
  addMetricCard(slide, slideNo, 870, 494, 300, 90, `${DATA.robustness.overallV4.C.toFixed(2)}%`, "v4 overall C", { color: L0 });
  addNotes(slide, "Robustness slide. The point is that L0's advantage is not an artifact of one dataset snapshot.", ["robustness", "final4way"]);
}

function buildFalsePositive(presentation) {
  const slideNo = 28;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "False Positive와 운영 가능성", "운영에 넣을 수 있으려면 정확도뿐 아니라 정상 문서에서의 FP도 낮아야 한다");
  addTakeaway(slide, slideNo, "컨텍스트 조건을 넣은 뒤 clean Korean docs 기준 FP가 26%에서 2%로 줄었다.", L0, { w: 860 });
  addMetricCard(slide, slideNo, 102, 282, 290, 170, `${DATA.fp.before}%`, "초기 FP", { color: RED });
  addMetricCard(slide, slideNo, 494, 282, 290, 170, `${DATA.fp.after}%`, "개선 후 FP", { color: L0 });
  addMetricCard(slide, slideNo, 886, 282, 290, 170, `${DATA.fp.docs}`, "정상 한국어 문서", { color: GOLD, note: "clean set" });
  addPanel(slide, slideNo, 102, 492, 1074, 118, { fill: WHITE_96, line: LINE, role: "fp example panel" });
  addText(slide, slideNo, "개선 포인트", 126, 516, 120, 18, {
    size: 12,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    role: "fp label",
    checkFit: false,
  });
  addBulletList(
    slide,
    slideNo,
    [
      "2글자 이하 키워드는 단독 매칭이 아니라 컨텍스트 조건을 붙였다.",
      "예: '개발부', '경영지원팀' 같은 정상 조직 표현의 과탐을 줄였다.",
      "중간발표 시점에서는 '운영 가능한 수준으로 FP를 낮췄다'는 메시지를 주면 충분하다.",
    ],
    126,
    540,
    1024,
    56,
    { size: 17, color: INK, role: "fp bullets", gap: 10 },
  );
  addNotes(slide, "False-positive slide. Keep it operational: enough evidence to say the system is not unusably noisy.", ["fp", "paper"]);
}

function buildRootCauseRevised(presentation) {
  const slideNo = 7;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "원인: 대부분 가드레일은 영어 기반", "문제의 핵심은 한국어 전체보다 한국어 의미형 PII 탐지 공백이다");
  addTakeaway(slide, slideNo, "영어 중심 탐지, 한국어 숫자형 편중, 의미형 PII 탐지 공백이 겹친다.");
  addCardTriple(
    slide,
    slideNo,
    [
      ["영어 중심 탐지", "기존 기준선은 영어에서 99.37% TRUE 탐지율을 기록한다."],
      ["한국어 숫자형 위주", "기존 스택은 주민번호·사업자번호 같은 체크섬·형식형 PII에서 상대적으로 강하다."],
      ["의미형 PII 탐지 공백", "한국어 의미형 slice에서는 기준선 TRUE 탐지율이 49.62%까지 떨어진다."],
    ],
    [EN_BLUE, GOLD, RED],
  );
  addPanel(slide, slideNo, 72, 468, 1132, 144, { fill: WHITE_96, line: LINE, role: "root cause panel" });
  addText(slide, slideNo, "발표 해석", 98, 492, 120, 18, {
    size: 12,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    role: "root cause label",
    checkFit: false,
  });
  addBulletList(
    slide,
    slideNo,
    [
      "초기 소규모 탐색 표는 본문에서 빼고, 메인 논리는 10k 벤치마크 기준으로만 전개한다.",
      "따라서 이후 결과는 '한국어 전체'보다 '한국어 의미형 PII'를 중심으로 읽어야 한다.",
      "모델이 놓치는 입력은 게이트웨이 앞단의 Layer 0에서 먼저 보강한다.",
    ],
    98,
    516,
    1068,
    72,
    { size: 17, color: INK, role: "root cause bullets", gap: 10 },
  );
  addNotes(slide, "Root-cause slide. Keep only the 10k-backed story in the main deck and move the old exploratory table out of the primary narrative.", ["final4way"]);
}

function buildGoalRevised(presentation) {
  const slideNo = 8;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "연구 질문과 프로젝트 목표", "이번 발표에서는 목표를 '한국어 PII 보강 계층'으로 정직하게 정의한다");
  addTakeaway(slide, slideNo, "보호 엔진 전체가 아니라 기존 스택 앞단의 한국어 보강 계층이 목표다.", L0, { w: 760 });
  addPanel(slide, slideNo, 72, 238, 550, 354, { fill: WHITE_96, line: LINE, role: "rq panel" });
  addText(slide, slideNo, "RQ1", 98, 266, 60, 20, {
    size: 13,
    color: KR_ORANGE,
    face: MONO_FACE,
    bold: true,
    role: "rq1 label",
    checkFit: false,
  });
  addText(slide, slideNo, "왜 기존 가드레일은 영어 대비 한국어, 특히 한국어 의미형에서 크게 약한가?", 98, 296, 480, 46, {
    size: 22,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "rq1 title",
  });
  addText(slide, slideNo, wrapText("언어 차이 자체인지, 혹은 한국어 의미형 PII라는 어려운 slice 때문인지 분리해서 확인한다.", 34), 98, 350, 480, 56, {
    size: 17,
    color: TEXT,
    face: BODY_FACE,
    role: "rq1 desc",
  });
  addText(slide, slideNo, "RQ2", 98, 438, 60, 20, {
    size: 13,
    color: L0,
    face: MONO_FACE,
    bold: true,
    role: "rq2 label",
    checkFit: false,
  });
  addText(slide, slideNo, "LLM Judge 대신 Layer 0가 더 싸고 빠르게 같은 공백을 메울 수 있는가?", 98, 468, 480, 46, {
    size: 22,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "rq2 title",
  });
  addText(slide, slideNo, wrapText("결과 비교뿐 아니라 지연, 비용, 스마트 캐스케이드까지 포함해 실용성을 평가한다.", 34), 98, 522, 480, 40, {
    size: 17,
    color: TEXT,
    face: BODY_FACE,
    role: "rq2 desc",
  });
  addPanel(slide, slideNo, 662, 238, 546, 354, { fill: FULL, line: FULL, role: "goal panel" });
  addText(slide, slideNo, "프로젝트 목표", 694, 266, 180, 20, {
    size: 13,
    color: "#98A2B3",
    face: MONO_FACE,
    bold: true,
    role: "goal label",
    checkFit: false,
  });
  addText(slide, slideNo, "한국어 PII 보강 계층\nLayer 0 (L0)", 694, 300, 420, 92, {
    size: 34,
    color: WHITE,
    bold: true,
    face: TITLE_FACE,
    role: "goal title",
  });
  addText(slide, slideNo, wrapText("기존 L1~L3 스택을 유지한 채, 그 앞단에서 한국어 입력을 먼저 정규화·탐지해 한국어 의미형 PII 탐지 공백을 메우는 계층", 26), 694, 412, 442, 92, {
    size: 19,
    color: "#D0D5DD",
    face: BODY_FACE,
    role: "goal desc",
  });
  addChip(slide, slideNo, 694, 534, "발표 표기: L0", L0, { textColor: WHITE, width: 140 });
  addChip(slide, slideNo, 850, 534, "기존 스택 유지", WHITE, { textColor: INK, width: 150 });
  addNotes(slide, "Define the goal carefully: not a full standalone protection engine, but a Korean augmentation layer in front of the existing stack. Team-internal shorthand was v0; presentation terminology is Layer 0 (L0).", ["paper", "standalone"]);
}

function buildEvalOverviewRevised(presentation) {
  const slideNo = 14;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "평가 방법 개요", "왜 이 결과를 믿을 수 있는지 세 가지 원칙으로만 정리한다");
  addTakeaway(slide, slideNo, "핵심은 유효성 우선, 실제 API 호출, 그리고 TRUE/FALSE/BYPASS 분리다.", JUDGE, { w: 760 });
  const cards = [
    ["유효성 우선 fuzzer v4", "형태만 그럴듯한 payload가 아니라 실제로 동작 가능한 한국어 PII 입력을 우선 생성했다."],
    ["실제 API 호출 벤치마크", "모든 케이스를 LiteLLM Gateway와 외부 guardrail / judge 호출로 직접 측정했다."],
    ["TRUE / FALSE / BYPASS", "출력 문구가 아니라 실제 무해화 여부를 기준으로 결과를 분리했다."],
  ];
  addCardTriple(slide, slideNo, cards, [EN_BLUE, JUDGE, L0]);
  addMetricCard(slide, slideNo, 92, 492, 250, 118, "10,000", "동일 payload 4-way 비교", { color: KR_ORANGE });
  addMetricCard(slide, slideNo, 364, 492, 250, 118, "91개", "PII 유형", { color: GOLD });
  addMetricCard(slide, slideNo, 636, 492, 250, 118, "TRUE", "실제 무해화 기준", { color: L0 });
  addMetricCard(slide, slideNo, 908, 492, 250, 118, "v4", "유효성 우선 벤치마크", { color: JUDGE });
  addNotes(slide, "Method overview slide. The audience should leave this slide believing the benchmark design, not memorizing implementation details.", ["paper", "final4way"]);
}

function buildBenchmarkCompositionRevised(presentation) {
  const slideNo = 15;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "벤치마크 구성", "10k 계층 표본에서 영어·한국어·유효성 그룹 분포를 고정했다");
  addTakeaway(slide, slideNo, "발표의 핵심 slice는 한국어 의미형 1,302건이다.", RED, { w: 540 });
  let x = 74;
  for (const item of DATA.benchmarkCounts) {
    addMetricCard(slide, slideNo, x, 252, 214, 154, item.value.toLocaleString("en-US"), item.key, { color: item.color });
    x += 226;
  }
  addPanel(slide, slideNo, 74, 452, 1128, 140, { fill: WHITE_96, line: LINE, role: "benchmark notes" });
  addBulletList(
    slide,
    slideNo,
    [
      "전체 10,000건 중 영어는 3,487건, 한국어는 6,513건이다.",
      "그중 한국어 의미형 1,302건이 발표의 메인 타깃이며 취약성이 가장 강하게 드러나는 구간이다.",
      "모든 4-way 구성은 동일한 payload를 공유한다.",
    ],
    100,
    476,
    1068,
    96,
    { size: 17, color: INK, role: "benchmark bullets", gap: 10 },
  );
  addNotes(slide, "Benchmark composition slide. Keep the count cards large and make Korean semantic PII stand out as the central slice.", ["final4way"]);
}

function buildLangGapRevised(presentation) {
  const slideNo = 16;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "핵심 문제 데이터: 영어 vs 한국어", "기준선 A만 놓고 보면 영어와 한국어 사이의 격차가 바로 보인다");
  addTakeaway(slide, slideNo, "영어는 잘 막지만 한국어 의미형 PII는 절반 수준까지 떨어진다.", RED, { w: 700 });
  let chipX = 74;
  for (const item of DATA.baselineLangGap) {
    chipX += addChip(slide, slideNo, chipX, 218, item.label, item.color, { textColor: item.color === RED ? WHITE : INK }) + 10;
  }
  addPanel(slide, slideNo, 74, 252, 720, 350, { fill: WHITE_96, line: LINE, role: "lang gap chart panel" });
  addBarChart(slide, slideNo, {
    x: 96,
    y: 286,
    w: 676,
    h: 286,
    categories: ["TRUE 탐지율"],
    direction: "bar",
    role: "lang gap chart",
    series: DATA.baselineLangGap.map((item) => ({ name: item.label, values: [item.value], color: item.color })),
  });
  addMetricCard(slide, slideNo, 828, 282, 360, 132, "-29.51%p", "한국어 vs 영어 격차", { color: KR_ORANGE });
  addMetricCard(slide, slideNo, 828, 438, 360, 132, "-49.75%p", "의미형 vs 영어 격차", { color: RED });
  addNotes(slide, "This is the main language-gap slide. The audience should immediately see that the real collapse is on Korean semantic PII, not English.", ["final4way"]);
}

function buildOverall4WayRevised(presentation) {
  const slideNo = 18;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "4-way 전체 비교", "L0 포함 구성이 LLM Judge 포함 기준선보다 높다");
  addTakeaway(slide, slideNo, "전체 10k 기준에서도 C(+L0)가 B(+Judge)보다 높다.", L0, { w: 620 });
  addConfigLegend(slide, slideNo, 74, 218);
  addPanel(slide, slideNo, 74, 252, 760, 336, { fill: WHITE_96, line: LINE, role: "overall chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 292,
    w: 712,
    h: 268,
    categories: ["10k 벤치마크"],
    direction: "bar",
    role: "overall 4way chart",
    series: CONFIGS.map((config) => ({ name: config.label, values: [DATA.overall4way[config.key]], color: config.color })),
  });
  addMetricCard(slide, slideNo, 870, 272, 310, 120, "94.32%", "C = L0 + 기존 스택", { color: L0 });
  addMetricCard(slide, slideNo, 870, 414, 310, 120, "+3.36%p", "C가 B보다 높음", { color: L0 });
  addNotes(slide, "Overall 4-way slide. The core comparison is B versus C, not only A versus D.", ["final4way"]);
}

function buildLangSplit4WayRevised(presentation) {
  const slideNo = 19;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "4-way 한국어/영어 분리 비교", "개선의 대부분은 영어가 아니라 한국어에서 나온다");
  addTakeaway(slide, slideNo, "영어는 이미 포화 상태고, 한국어가 실제 개선 구간이다.", KR_ORANGE, { w: 620 });
  addConfigLegend(slide, slideNo, 74, 218);
  addPanel(slide, slideNo, 74, 252, 850, 350, { fill: WHITE_96, line: LINE, role: "lang split chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 286,
    w: 802,
    h: 286,
    categories: Object.keys(DATA.lang4way),
    direction: "column",
    role: "lang split chart",
    series: CONFIGS.map((config) => ({
      name: config.label,
      values: Object.keys(DATA.lang4way).map((key) => DATA.lang4way[key][config.key]),
      color: config.color,
    })),
  });
  addMetricCard(slide, slideNo, 954, 274, 236, 130, "99.37%", "영어는 이미 포화", { color: EN_BLUE });
  addMetricCard(slide, slideNo, 954, 426, 236, 130, "96.08%", "한국어 전체 스택", { color: KR_ORANGE });
  addNotes(slide, "Language split slide. The key oral line is that English stays flat across configurations while Korean drives the gains.", ["final4way"]);
}

function buildKrSemanticRevised(presentation) {
  const slideNo = 20;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "한국어 의미형 정면 비교", "이 발표의 핵심 figure");
  addTakeaway(slide, slideNo, "L0가 GPT-4o-mini Judge를 한국어 의미형에서 +8.99%p 능가한다.", RED, { w: 760 });
  addConfigLegend(slide, slideNo, 74, 218);
  addPanel(slide, slideNo, 74, 252, 760, 336, { fill: WHITE_96, line: LINE, role: "kr semantic chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 292,
    w: 712,
    h: 268,
    categories: ["한국어 의미형"],
    direction: "bar",
    role: "kr semantic chart",
    series: CONFIGS.map((config) => ({
      name: config.label,
      values: [DATA.krSemantic4way[config.key]],
      color: config.color,
    })),
  });
  addMetricCard(slide, slideNo, 864, 272, 326, 120, "96.39%", "C = L0 + 기존 스택", { color: L0 });
  addMetricCard(slide, slideNo, 864, 414, 326, 120, "+8.99%p", "C가 B보다 높음", { color: RED });
  addNotes(slide, "Korean semantic head-to-head slide. This is the primary result figure for the midterm talk.", ["final4way"]);
}

function buildStandaloneRevised(presentation) {
  const slideNo = 21;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "L0 단독 성능", "단독 수치를 따로 보여줘야 보강 계층이라는 해석이 정직해진다");
  addTakeaway(slide, slideNo, "L0는 단독 엔진이 아니라 한국어 보강 계층으로 보는 것이 맞다.", L0, { w: 720 });
  addMetricCard(slide, slideNo, 92, 264, 250, 160, `${DATA.standalone.overall.toFixed(2)}%`, "전체", { color: BASELINE });
  addMetricCard(slide, slideNo, 368, 264, 250, 160, `${DATA.standalone.KR.toFixed(2)}%`, "한국어", { color: KR_ORANGE });
  addMetricCard(slide, slideNo, 644, 264, 250, 160, `${DATA.standalone.KR_semantic.toFixed(2)}%`, "한국어 의미형", { color: L0 });
  addMetricCard(slide, slideNo, 920, 264, 250, 160, `${DATA.standalone.EN.toFixed(2)}%`, "영어", { color: EN_BLUE });
  addPanel(slide, slideNo, 92, 468, 1078, 136, { fill: WHITE_96, line: LINE, role: "standalone notes" });
  addBulletList(
    slide,
    slideNo,
    [
      "한국어 의미형만 놓고 보면 80.65%로 강한 편이다.",
      "하지만 영어 0.00%, 전체 30.96%이기 때문에 전체 보호 엔진으로 말하면 과장이다.",
      "따라서 L0의 정체성은 '한국어 보강 계층'이 가장 정확하다.",
    ],
    116,
    492,
    1032,
    92,
    { size: 17, color: INK, role: "standalone bullets", gap: 12 },
  );
  addNotes(slide, "Standalone slide. This is the honesty slide that prevents overclaiming L0 as a full engine.", ["standalone"]);
}

function buildStandaloneInterpretationRevised(presentation) {
  const slideNo = 22;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "L0 단독 성능의 해석", "무엇을 잘하고 무엇을 의도적으로 하지 않는지 분리한다");
  addTakeaway(slide, slideNo, "L0의 강점과 한계를 같이 보여줘야 발표 논리가 정직해진다.", GOLD, { w: 640 });
  addCardTriple(
    slide,
    slideNo,
    [
      ["잘하는 것", "한국어 의미형 80.65%\n한국어 의미형 PII 보강"],
      ["의도적으로 안 하는 것", "영어 0.00%\n영어는 기존 스택에 맡김"],
      ["약한 것", "KR checksum 18.58%\n체크섬형은 기존 스택이 더 강함"],
    ],
    [L0, EN_BLUE, RED],
  );
  addMetricCard(slide, slideNo, 408, 506, 464, 84, "한국어 보호 엔진이 아니라 한국어 보강 계층", "발표 해석", { color: L0 });
  addNotes(slide, "Interpretation slide. This is where you explicitly name L0 as a Korean augmentation layer.", ["standalone", "paper"]);
}

function buildAblationRevised(presentation) {
  const slideNo = 24;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "구성 요소 분석", "효과의 대부분이 정규화보다 사전에서 나온다는 점을 분리해 보여준다");
  addTakeaway(slide, slideNo, "한국어 의미형 개선의 약 96%가 사전에서 발생했다.", RED, { w: 700 });
  addPanel(slide, slideNo, 74, 252, 760, 338, { fill: WHITE_96, line: LINE, role: "ablation chart panel" });
  addBarChart(slide, slideNo, {
    x: 100,
    y: 290,
    w: 708,
    h: 270,
    categories: ["Baseline", "+정규화", "+사전", "+전체"],
    direction: "column",
    role: "ablation chart",
    series: [{ name: "한국어 의미형 TRUE", values: [DATA.ablation.baseline, DATA.ablation.normOnly, DATA.ablation.dictOnly, DATA.ablation.full], color: RED }],
  });
  addMetricCard(slide, slideNo, 870, 266, 300, 90, `+${DATA.ablation.normGain.toFixed(2)}%p`, "정규화만 적용", { color: GOLD });
  addMetricCard(slide, slideNo, 870, 380, 300, 90, `+${DATA.ablation.dictGain.toFixed(2)}%p`, "사전만 적용", { color: RED });
  addMetricCard(slide, slideNo, 870, 494, 300, 90, `+${DATA.ablation.synergy.toFixed(2)}%p`, "시너지", { color: L0 });
  addNotes(slide, "Ablation slide. This is where you justify the dictionary-heavy design of L0.", ["ablation"]);
}

function buildLatencyCostRevised(presentation) {
  const slideNo = 25;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "지연과 운영 비용", "L0는 Judge보다 빠르고, Judge 호출 자체를 크게 줄일 수 있다");
  addTakeaway(slide, slideNo, "C(+L0)는 B(+Judge)보다 훨씬 빠르고, Smart Cascade와 결합하면 운영 부담도 낮아진다.", L0, { w: 900 });

  addPanel(slide, slideNo, 74, 252, 524, 336, { fill: WHITE_96, line: LINE, role: "latency panel" });
  addText(slide, slideNo, "p99 지연", 100, 282, 120, 22, {
    size: 22,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "latency title",
    checkFit: false,
  });
  addMetricCard(slide, slideNo, 100, 326, 212, 126, `${DATA.latency.B_p99.toLocaleString("en-US")}ms`, "B + Judge", { color: JUDGE });
  addMetricCard(slide, slideNo, 344, 326, 212, 126, `${DATA.latency.C_p99.toLocaleString("en-US")}ms`, "C + L0", { color: L0 });
  addMetricCard(slide, slideNo, 222, 476, 212, 82, `${DATA.latency.L0_p99}ms`, "L0 단독", { color: GOLD });

  addPanel(slide, slideNo, 640, 252, 548, 336, { fill: WHITE_96, line: LINE, role: "cost panel" });
  addText(slide, slideNo, "1만 건 요청 기준 운영비", 666, 282, 260, 22, {
    size: 22,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "cost title",
    checkFit: false,
  });
  addMetricCard(slide, slideNo, 666, 326, 226, 126, `${DATA.smartCascade.reduction.toFixed(2)}%`, "L4 호출 절감", { color: L0 });
  addMetricCard(slide, slideNo, 926, 326, 226, 126, `$${DATA.smartCascade.costSaved10k.toFixed(2)}`, "1만 건 기준 추정 절감액", { color: JUDGE });
  addMetricCard(slide, slideNo, 796, 476, 226, 82, `${DATA.smartCascade.sameTrueRate.toFixed(2)}%`, "최종 TRUE 유지", { color: RED });
  addText(slide, slideNo, "동일 Judge 호출 가정 기준 추정치", 676, 566, 466, 16, {
    size: 11,
    color: MUTED,
    face: BODY_FACE,
    role: "cost footnote",
    align: "center",
    checkFit: false,
  });
  addNotes(slide, "Latency/cost slide. Ambiguous per-config dollar cards were removed; the main slide keeps only directly grounded latency and smart-cascade cost-saving numbers.", ["latency", "smartCascade"]);
}

function buildSmartCascadeRevised(presentation) {
  const slideNo = 26;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "스마트 캐스케이드", "L4 Judge를 필요한 경우에만 호출해 비용과 지연을 줄인다");
  addTakeaway(slide, slideNo, "10,000건 중 568건에만 Judge를 호출해도 최종 TRUE rate는 그대로 유지된다.", L0, { w: 840 });
  const funnel = [
    { x: 100, y: 280, w: 1020, h: 72, fill: FULL, text: WHITE, value: "10,000", label: "전체 케이스" },
    { x: 170, y: 370, w: 880, h: 72, fill: L0, text: WHITE, value: "9,432", label: "L0~L3에서 neutralized" },
    { x: 330, y: 460, w: 560, h: 72, fill: JUDGE, text: WHITE, value: "568", label: "L4 Judge 호출" },
    { x: 450, y: 550, w: 320, h: 72, fill: KR_ORANGE, text: WHITE, value: "291", label: "L4가 추가 회수" },
  ];
  for (const row of funnel) {
    addShape(slide, "roundRect", row.x, row.y, row.w, row.h, row.fill, TRANSPARENT, 0, { slideNo, role: `funnel ${row.label}` });
    addText(slide, slideNo, row.value, row.x + 32, row.y + 14, 160, 36, {
      size: 30,
      color: row.text,
      bold: true,
      face: TITLE_FACE,
      role: `funnel value ${row.label}`,
      checkFit: false,
    });
    addText(slide, slideNo, row.label, row.x + 220, row.y + 24, row.w - 260, 22, {
      size: 18,
      color: row.text,
      face: BODY_FACE,
      role: `funnel label ${row.label}`,
      checkFit: false,
    });
  }
  addMetricCard(slide, slideNo, 930, 242, 250, 100, `${DATA.smartCascade.reduction.toFixed(2)}%`, "L4 호출 절감", { color: L0 });
  addMetricCard(slide, slideNo, 930, 356, 250, 100, `${DATA.smartCascade.sameTrueRate.toFixed(2)}%`, "최종 TRUE 유지", { color: JUDGE });
  addNotes(slide, "Smart cascade slide. The core message is identical detection with much fewer judge calls.", ["smartCascade"]);
}

function buildRobustnessRevised(presentation) {
  const slideNo = 27;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "강건성 검증", "데이터를 더 어렵게 바꿔도 L0 우위는 유지된다");
  addTakeaway(slide, slideNo, "한국어 의미형에서 B-C 격차가 +8.99%p에서 +10.65%p로 오히려 커졌다.", RED, { w: 900 });
  addPanel(slide, slideNo, 74, 252, 760, 336, { fill: WHITE_96, line: LINE, role: "robustness chart panel" });
  addBarChart(slide, slideNo, {
    x: 98,
    y: 286,
    w: 712,
    h: 270,
    categories: ["v1 한국어 의미형", "v4 한국어 의미형"],
    direction: "column",
    role: "robustness chart",
    series: [
      { name: "B + Judge", values: [DATA.robustness.v1.B, DATA.robustness.v4.B], color: JUDGE },
      { name: "C + L0", values: [DATA.robustness.v1.C, DATA.robustness.v4.C], color: L0 },
    ],
  });
  addMetricCard(slide, slideNo, 870, 266, 300, 90, `+${DATA.robustness.v1.gap.toFixed(2)}%p`, "v1 격차", { color: JUDGE });
  addMetricCard(slide, slideNo, 870, 380, 300, 90, `+${DATA.robustness.v4.gap.toFixed(2)}%p`, "v4 격차", { color: RED });
  addMetricCard(slide, slideNo, 870, 494, 300, 90, `${DATA.robustness.overallV4.C.toFixed(2)}%`, "v4 전체 C", { color: L0 });
  addNotes(slide, "Robustness slide. The point is that L0's advantage is not an artifact of one dataset snapshot.", ["robustness", "final4way"]);
}

function buildFalsePositiveRevised(presentation) {
  const slideNo = 28;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "오탐과 운영 가능성", "운영 가능성을 말하려면 정상 문서에서의 오탐부터 보여줘야 한다");
  addTakeaway(slide, slideNo, "정상 한국어 문서 50건 기준 FP는 2%였다.", L0, { w: 560 });
  addMetricCard(slide, slideNo, 102, 282, 290, 170, `${DATA.fp.after}%`, "FP 비율", { color: L0 });
  addMetricCard(slide, slideNo, 494, 282, 290, 170, `${DATA.fp.docs}`, "정상 한국어 문서", { color: GOLD });
  addMetricCard(slide, slideNo, 886, 282, 290, 170, `${DATA.fp.fpDocs}`, "오탐 문서", { color: RED });
  addPanel(slide, slideNo, 102, 492, 1074, 118, { fill: WHITE_96, line: LINE, role: "fp example panel" });
  addText(slide, slideNo, "해석 포인트", 126, 516, 120, 18, {
    size: 12,
    color: MUTED,
    face: MONO_FACE,
    bold: true,
    role: "fp label",
    checkFit: false,
  });
  addBulletList(
    slide,
    slideNo,
    [
      "현재 저장된 결과는 정상 한국어 문서 50건 중 1개 문서에서만 오탐을 기록했다.",
      "오탐 유형은 부서명 계열이었고, 운영 규칙 보정 대상으로 해석할 수 있다.",
      "따라서 중간발표에서는 '운영이 불가능할 정도의 노이즈는 아니다'까지 방어 가능하다.",
    ],
    126,
    540,
    1024,
    56,
    { size: 17, color: INK, role: "fp bullets", gap: 10 },
  );
  addNotes(slide, "False-positive slide. The main deck keeps only directly grounded numbers: 2% over 50 clean Korean docs, with 1 false-positive document. The earlier 26% exploratory figure stays out of the main deck until its source is reattached.", ["fp"]);
}

function buildAchievements(presentation) {
  const slideNo = 29;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo);
  addHeader(slide, slideNo);
  addTitleBlock(slide, slideNo, "중간발표 시점의 성과와 남은 과제", "이미 증명한 것과 최종발표 전 보강할 것을 분리한다");
  addTakeaway(slide, slideNo, "중간발표에서는 이미 증명한 부분을 선명하게 말하고, 남은 과제는 과장 없이 적는 것이 중요하다.", GOLD, { w: 980 });
  addPanel(slide, slideNo, 72, 236, 540, 382, { fill: "#ECFDF3", line: "#ABEFCD", role: "done panel" });
  addPanel(slide, slideNo, 668, 236, 540, 382, { fill: "#FFF7ED", line: "#FED7AA", role: "todo panel" });
  addText(slide, slideNo, "이미 증명한 것", 98, 266, 180, 24, {
    size: 24,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "done title",
    checkFit: false,
  });
  addBulletList(
    slide,
    slideNo,
    [
      "한국어 vs 영어 성능 격차를 10k benchmark로 확인했다.",
      "한국어 의미형에서 L0가 Judge보다 높다는 점을 증명했다.",
      "McNemar로 B vs C 차이가 통계적으로 유의함을 보였다.",
      "latency, cost, smart cascade, FP로 운영성도 제시했다.",
    ],
    98,
    310,
    470,
    240,
    { size: 18, color: INK, role: "done bullets", gap: 14 },
  );
  addText(slide, slideNo, "최종발표 전 보강할 것", 694, 266, 220, 24, {
    size: 24,
    color: INK,
    bold: true,
    face: TITLE_FACE,
    role: "todo title",
    checkFit: false,
  });
  addBulletList(
    slide,
    slideNo,
    [
      "output-side leakage 평가 추가",
      "prompt injection 결합 시나리오 확대",
      "신규 PII 유형과 외부 baseline 비교 보강",
    ],
    694,
    310,
    470,
    240,
    { size: 18, color: INK, role: "todo bullets", gap: 14 },
  );
  addMetricCard(slide, slideNo, 214, 556, 240, 88, "중간발표 완료", "핵심 가설 검증", { color: L0 });
  addMetricCard(slide, slideNo, 828, 556, 220, 88, "최종발표 과제", "확장 검증", { color: KR_ORANGE });
  addNotes(slide, "Midterm framing slide. Show progress and remaining scope without weakening the already-proven result story.", ["paper", "robustness"]);
}

function buildConclusion(presentation) {
  const slideNo = 30;
  const slide = presentation.slides.add();
  addBackground(slide, slideNo, "dark");
  addHeader(slide, slideNo);
  addText(slide, slideNo, "결론 및 Q&A", 72, 92, 320, 44, {
    size: 34,
    color: WHITE,
    bold: true,
    face: TITLE_FACE,
    role: "final title",
  });
  addShape(slide, "roundRect", 72, 170, 1136, 96, "#1F2937", TRANSPARENT, 0, { slideNo, role: "final line 1" });
  addShape(slide, "roundRect", 72, 286, 1136, 96, "#1F2937", TRANSPARENT, 0, { slideNo, role: "final line 2" });
  addShape(slide, "roundRect", 72, 402, 1136, 96, "#1F2937", TRANSPARENT, 0, { slideNo, role: "final line 3" });
  addText(slide, slideNo, "영어는 잘 막지만 한국어 텍스트형 PII는 공백이 있다", 104, 198, 1000, 36, {
    size: 28,
    color: WHITE,
    bold: true,
    face: TITLE_FACE,
    role: "final statement 1",
  });
  addText(slide, slideNo, "Layer 0가 그 공백을 메운다", 104, 314, 1000, 36, {
    size: 28,
    color: WHITE,
    bold: true,
    face: TITLE_FACE,
    role: "final statement 2",
  });
  addText(slide, slideNo, "그리고 LLM Judge보다 더 싸고 빠르며 한국어 의미형에서 더 잘 잡는다", 104, 430, 1000, 36, {
    size: 28,
    color: WHITE,
    bold: true,
    face: TITLE_FACE,
    role: "final statement 3",
  });
  addMetricCard(slide, slideNo, 164, 556, 230, 102, "99.37%", "영어 기준선", { color: EN_BLUE });
  addMetricCard(slide, slideNo, 456, 556, 230, 102, "49.62%", "한국어 의미형 기준선", { color: RED });
  addMetricCard(slide, slideNo, 748, 556, 230, 102, "96.39%", "L0 적용 후 의미형", { color: L0 });
  addText(slide, slideNo, "Q&A", 1108, 622, 70, 22, {
    size: 18,
    color: "#98A2B3",
    face: MONO_FACE,
    bold: true,
    role: "qa",
    checkFit: false,
  });
  addNotes(slide, "Final slide. Keep the close concise and metric-backed, then move to questions.", ["final4way", "latency"]);
}

function buildSlides(presentation) {
  buildCover(presentation);
  buildSummary(presentation);
  buildAgenda(presentation);
  buildBackground(presentation);
  buildGuardrailQuestion(presentation);
  buildBedrockExperiment(presentation);
  buildRootCauseRevised(presentation);
  buildGoalRevised(presentation);
  buildGatewayContext(presentation);
  buildInsertionPoint(presentation);
  buildFiveLayers(presentation);
  buildNormalizer(presentation);
  buildDetector(presentation);
  buildEvalOverviewRevised(presentation);
  buildBenchmarkCompositionRevised(presentation);
  buildLangGapRevised(presentation);
  buildHardestMisses(presentation);
  buildOverall4WayRevised(presentation);
  buildLangSplit4WayRevised(presentation);
  buildKrSemanticRevised(presentation);
  buildStandaloneRevised(presentation);
  buildStandaloneInterpretationRevised(presentation);
  buildMcNemar(presentation);
  buildAblationRevised(presentation);
  buildLatencyCostRevised(presentation);
  buildSmartCascadeRevised(presentation);
  buildRobustnessRevised(presentation);
  buildFalsePositiveRevised(presentation);
  buildAchievements(presentation);
  buildConclusion(presentation);
}

async function createDeck() {
  await ensureDirs();
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  buildSlides(presentation);
  return presentation;
}

async function saveBlobToFile(blob, filePath) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  await fs.writeFile(filePath, bytes);
}

async function writeInspectArtifact(presentation) {
  const records = [
    {
      kind: "deck",
      id: DECK_ID,
      slideCount: presentation.slides.count,
      slideSize: { width: W, height: H },
    },
  ];
  presentation.slides.items.forEach((slide, index) => {
    records.push({ kind: "slide", slide: index + 1, id: slide?.id || `slide-${index + 1}` });
  });
  records.push(...inspectRecords);
  const lines = records.map((record) => JSON.stringify(record)).join("\n") + "\n";
  await fs.writeFile(INSPECT_PATH, lines, "utf8");
}

async function currentRenderLoopCount() {
  const logPath = path.join(VERIFICATION_DIR, "render_verify_loops.ndjson");
  if (!(await pathExists(logPath))) return 0;
  const previous = await fs.readFile(logPath, "utf8");
  return previous.split(/\r?\n/).filter((line) => line.trim()).length;
}

async function appendRenderVerifyLoop(presentation, previewPaths, pptxPath) {
  const logPath = path.join(VERIFICATION_DIR, "render_verify_loops.ndjson");
  const priorCount = await currentRenderLoopCount();
  const record = {
    kind: "render_verify_loop",
    deckId: DECK_ID,
    loop: priorCount + 1,
    maxLoops: MAX_RENDER_VERIFY_LOOPS,
    timestamp: new Date().toISOString(),
    slideCount: presentation.slides.count,
    previewCount: previewPaths.length,
    previewDir: PREVIEW_DIR,
    inspectPath: INSPECT_PATH,
    pptxPath,
  };
  await fs.appendFile(logPath, JSON.stringify(record) + "\n", "utf8");
}

async function verifyAndExport(presentation) {
  await ensureDirs();
  const nextLoop = (await currentRenderLoopCount()) + 1;
  if (nextLoop > MAX_RENDER_VERIFY_LOOPS) {
    throw new Error(`Render loop cap reached (${MAX_RENDER_VERIFY_LOOPS}).`);
  }
  await writeInspectArtifact(presentation);
  const previewPaths = [];
  for (let idx = 0; idx < presentation.slides.items.length; idx += 1) {
    const slide = presentation.slides.items[idx];
    const preview = await presentation.export({ slide, format: "png", scale: 1 });
    const previewPath = path.join(PREVIEW_DIR, `slide-${String(idx + 1).padStart(2, "0")}.png`);
    await saveBlobToFile(preview, previewPath);
    previewPaths.push(previewPath);
  }
  const pptxBlob = await PresentationFile.exportPptx(presentation);
  let pptxPath = path.join(OUT_DIR, "output.pptx");
  try {
    await pptxBlob.save(pptxPath);
  } catch (error) {
    if (error?.code !== "EBUSY") throw error;
    pptxPath = path.join(OUT_DIR, "output_updated.pptx");
    await pptxBlob.save(pptxPath);
  }
  await appendRenderVerifyLoop(presentation, previewPaths, pptxPath);
  return pptxPath;
}

const presentation = await createDeck();
const pptxPath = await verifyAndExport(presentation);
console.log(pptxPath);
