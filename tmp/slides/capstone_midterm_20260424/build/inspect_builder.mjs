import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:/Users/andyw/Desktop/My-AI-Security-Project";
const TMP_ROOT = path.join(ROOT, "tmp", "slides", "capstone_midterm_20260424");
const INPUT_PPTX = path.join(ROOT, "outputs", "capstone_midterm_20260424", "output_updated.pptx");
const OUTPUT_PPTX = path.join(ROOT, "outputs", "capstone_midterm_20260424", "output_kimminwoo_merged.pptx");
const PREVIEW_DIR = path.join(TMP_ROOT, "preview", "merged");
const COMPARE_IMAGE = path.join(TMP_ROOT, "preview", "source", "slide-03.png");
const FALLBACK_PLATE =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=";

const TRANSPARENT = "#00000000";
const INK = "#1F2937";
const MUTED = "#475467";
const PAPER = "#FFFFFF";
const LINE = "#D0D5DD";
const DOT = "#111827";

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

async function saveBlobToFile(blob, filePath) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  await fs.writeFile(filePath, bytes);
}

function getShapeText(shape) {
  try {
    return shape?.text?.toString?.() ?? "";
  } catch {
    return "";
  }
}

function cloneInsets(insets) {
  if (!insets) return { left: 0, right: 0, top: 0, bottom: 0 };
  return {
    left: insets.left ?? 0,
    right: insets.right ?? 0,
    top: insets.top ?? 0,
    bottom: insets.bottom ?? 0,
  };
}

function snapshotTextStyle(text) {
  return {
    fontSize: text?.fontSize,
    bold: text?.bold,
    italic: text?.italic,
    underline: text?.underline,
    color: text?.color,
    alignment: text?.alignment,
    verticalAlignment: text?.verticalAlignment,
    autoFit: text?.autoFit,
    wrap: text?.wrap,
    insets: cloneInsets(text?.insets),
    typeface: text?.typeface,
  };
}

function applyTextStyle(text, style = {}) {
  if (!text) return;
  if (style.fontSize !== undefined) text.fontSize = style.fontSize;
  if (style.bold !== undefined) text.bold = style.bold;
  if (style.italic !== undefined) text.italic = style.italic;
  if (style.underline !== undefined) text.underline = style.underline;
  if (style.color !== undefined) text.color = style.color;
  if (style.alignment !== undefined) text.alignment = style.alignment;
  if (style.verticalAlignment !== undefined) text.verticalAlignment = style.verticalAlignment;
  if (style.autoFit !== undefined) text.autoFit = style.autoFit;
  if (style.wrap !== undefined) text.wrap = style.wrap;
  if (style.insets !== undefined) text.insets = cloneInsets(style.insets);
  if (style.typeface !== undefined) text.typeface = style.typeface;
}

function rewriteShape(shape, newText, overrides = {}) {
  const base = snapshotTextStyle(shape.text);
  shape.text = newText;
  applyTextStyle(shape.text, { ...base, ...overrides });
}

function addShape(slide, geometry, position, fill = TRANSPARENT, line = { style: "solid", fill: TRANSPARENT, width: 0 }) {
  return slide.shapes.add({
    geometry,
    position,
    fill,
    line,
  });
}

function addTextBox(
  slide,
  text,
  position,
  {
    fontSize = 18,
    bold = false,
    color = INK,
    alignment = "left",
    verticalAlignment = "top",
    fill = TRANSPARENT,
    lineFill = TRANSPARENT,
    lineWidth = 0,
    insets = { left: 0, right: 0, top: 0, bottom: 0 },
  } = {},
) {
  const shape = addShape(slide, "rect", position, fill, {
    style: "solid",
    fill: lineFill,
    width: lineWidth,
  });
  shape.text = text;
  applyTextStyle(shape.text, {
    fontSize,
    bold,
    color,
    alignment,
    verticalAlignment,
    insets,
  });
  return shape;
}

function addBulletRow(slide, left, top, width, text, options = {}) {
  addShape(
    slide,
    "ellipse",
    { left, top: top + 10, width: 8, height: 8 },
    options.dotFill ?? DOT,
    { style: "solid", fill: options.dotFill ?? DOT, width: 0 },
  );
  return addTextBox(
    slide,
    text,
    { left: left + 20, top, width, height: options.height ?? 56 },
    {
      fontSize: options.fontSize ?? 18,
      color: options.color ?? INK,
      lineWidth: 0,
    },
  );
}

function retitleCommonSlide(slide, section, title, subtitle, intro) {
  const shapes = Array.from(slide.shapes.items);
  rewriteShape(shapes[5], section);
  rewriteShape(shapes[8], title);
  rewriteShape(shapes[9], subtitle);
  rewriteShape(shapes[12], intro);
}

function removeShapes(shapes) {
  for (const shape of shapes) {
    shape?.delete?.();
  }
}

function buildPiiBoundarySlide(slide) {
  const shapes = Array.from(slide.shapes.items);
  retitleCommonSlide(
    slide,
    "중간발표",
    "민감한 PII와 비민감 정보의 경계",
    "필드별 마스킹을 넘어 문맥형 정책으로 민감도를 나눠야 한다",
    "처방전 예시는 어떤 필드가 우선 차단 대상이고, 어떤 정보가 문맥 기반 판정을 필요로 하는지 보여준다.",
  );

  removeShapes(shapes.slice(15, 31));

  rewriteShape(shapes[33], "직접 식별자");
  rewriteShape(shapes[34], "우선 차단");
  rewriteShape(shapes[37], "문맥형 정보");
  rewriteShape(shapes[38], "조건부 판정");

  addTextBox(slide, "실제 예시: 처방전 마스킹 비교", { left: 98, top: 266, width: 430, height: 30 }, { fontSize: 24, bold: true });
  addShape(
    slide,
    "roundRect",
    { left: 98, top: 308, width: 470, height: 220 },
    PAPER,
    { style: "solid", fill: LINE, width: 1 },
  );
  const image = slide.images.add({
    dataUrl: FALLBACK_PLATE,
    fit: "contain",
    alt: "민감 PII 마스킹 전후 예시",
  });
  image.position = { left: 110, top: 320, width: 446, height: 196 };

  addTextBox(
    slide,
    "성명과 DOB는 차단됐지만 질환명과 약품 정보는 그대로 남아 있다.",
    { left: 98, top: 536, width: 470, height: 24 },
    { fontSize: 15, color: MUTED },
  );

  addTextBox(slide, "경계 판단 기준", { left: 694, top: 266, width: 300, height: 30 }, { fontSize: 24, bold: true });
  addBulletRow(slide, 694, 310, 430, "성명, DOB, 연락처, 주민번호처럼 재식별이 직접 가능한 항목은 우선 차단한다.", { height: 68 });
  addBulletRow(slide, 694, 386, 430, "질환명, 처방약, 진료 맥락은 단독 정보일 때와 식별자 결합 시의 민감도가 다르다.", { height: 68 });
  addBulletRow(slide, 694, 462, 430, "따라서 한국어 보호 정책은 정적 목록보다 문맥형 분류 규칙을 함께 가져가야 한다.", { height: 68 });
}

function buildPipelineSlide(slide) {
  const shapes = Array.from(slide.shapes.items);
  retitleCommonSlide(
    slide,
    "중간발표",
    "보완 검증 파이프라인",
    "외부 서비스 조합으로 한국어 PII 누락 구간을 교차 검증한다",
    "Presidio와 Azure AI Language를 조합해 누락과 과탐을 분리해서 보는 외부 검증 흐름을 둔다.",
  );

  const replacements = [
    [15, "1차 탐지"],
    [16, "Presidio\nregex + NER"],
    [19, "2차 의미 보강"],
    [20, "Azure AI Language\nPII Redaction"],
    [23, "3차 정책 매핑"],
    [24, "민감/비민감 경계와\n마스킹 기준 일치"],
    [27, "4차 결과 비교"],
    [28, "원문과 redacted 결과를\n케이스 단위로 검수"],
    [31, "5차 로그 축적"],
    [32, "한국어 실패 케이스를\n사전·규칙으로 환류"],
    [35, "외부 서비스 조합으로 baseline을 교차 검증하면 과탐과 누락을 분리해서 볼 수 있다."],
    [37, "특히 한국어 semantic PII는 단일 엔진보다 파이프라인형 검증이 운영상 더 안정적이다."],
  ];

  for (const [index, text] of replacements) {
    rewriteShape(shapes[index], text);
  }
}

function buildFutureWorkSlide(slide) {
  const shapes = Array.from(slide.shapes.items);
  retitleCommonSlide(
    slide,
    "중간발표",
    "남은 과제: 한국어 PII 보호 엔진",
    "중간발표 이후에는 규칙을 다듬고, 최종발표에서는 엔진 수준 설계까지 확장한다",
    "중간발표 이후에는 한국어 semantic coverage를 넓히고, 최종발표에서는 보호 엔진 관점까지 설계를 확장한다.",
  );

  removeShapes(shapes.slice(15, 31));

  rewriteShape(shapes[33], "중간발표 이후");
  rewriteShape(shapes[34], "정책 정교화");
  rewriteShape(shapes[37], "최종 목표");
  rewriteShape(shapes[38], "한국어 보호 엔진");

  addTextBox(slide, "단기 보완 과제", { left: 98, top: 266, width: 220, height: 30 }, { fontSize: 24, bold: true });
  addBulletRow(slide, 98, 310, 430, "한국어 semantic PII taxonomy를 더 촘촘하게 확장한다.", { height: 56 });
  addBulletRow(slide, 98, 366, 430, "의료·행정·조직 문서별 규칙을 분리해 도메인 적합도를 높인다.", { height: 56 });
  addBulletRow(slide, 98, 422, 430, "context-aware 조건으로 false positive를 더 줄인다.", { height: 56 });
  addBulletRow(slide, 98, 478, 430, "새 유형과 실패 케이스를 benchmark에 지속적으로 반영한다.", { height: 56 });

  addTextBox(slide, "엔진 고도화 목표", { left: 694, top: 266, width: 260, height: 30 }, { fontSize: 24, bold: true });
  addBulletRow(slide, 694, 310, 430, "규칙 기반 Layer 0와 모델 기반 판단을 결합한 hybrid 보호 엔진 구조를 정리한다.", { height: 68 });
  addBulletRow(slide, 694, 388, 430, "output-side leakage까지 포함한 end-to-end 평가를 추가한다.", { height: 56 });
  addBulletRow(slide, 694, 452, 430, "외부 baseline과 정량 비교한 뒤 최종발표용 아키텍처를 고정한다.", { height: 56 });
}

function updatePageNumbers(presentation) {
  const total = presentation.slides.count;
  presentation.slides.items.forEach((slide, index) => {
    const label = `${String(index + 1).padStart(2, "0")} / ${String(total).padStart(2, "0")}`;
    for (const shape of slide.shapes.items) {
      const text = getShapeText(shape).trim();
      if (/^\d{2}\s*\/\s*\d{2}$/.test(text)) {
        rewriteShape(shape, label);
      }
    }
  });
}

async function attachCompareImage(slide) {
  const image = slide.images.items[0];
  if (!image) return;
  await image.replace({
    blob: await readImageBlob(COMPARE_IMAGE),
    alt: "처방전 민감 PII 마스킹 전후 비교",
  });
}

async function exportDeck(presentation) {
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  for (let idx = 0; idx < presentation.slides.items.length; idx += 1) {
    const slide = presentation.slides.items[idx];
    const preview = await presentation.export({ slide, format: "png", scale: 1 });
    const outPath = path.join(PREVIEW_DIR, `slide-${String(idx + 1).padStart(2, "0")}.png`);
    await saveBlobToFile(preview, outPath);
  }
  const pptxBlob = await PresentationFile.exportPptx(presentation);
  await pptxBlob.save(OUTPUT_PPTX);
}

async function main() {
  const imported = await PresentationFile.importPptx(await FileBlob.load(INPUT_PPTX));

  const piiSlide = imported.slides.getItem(28).duplicate();
  piiSlide.moveTo(29);

  const pipelineSlide = imported.slides.getItem(11).duplicate();
  pipelineSlide.moveTo(30);

  const futureSlide = imported.slides.getItem(28).duplicate();
  futureSlide.moveTo(31);

  buildPiiBoundarySlide(piiSlide);
  await attachCompareImage(piiSlide);
  buildPipelineSlide(pipelineSlide);
  buildFutureWorkSlide(futureSlide);
  updatePageNumbers(imported);
  await exportDeck(imported);

  console.log(OUTPUT_PPTX);
}

await main();
