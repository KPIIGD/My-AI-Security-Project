"use strict";

const fs = require("node:fs");
const path = require("node:path");

function loadRhwp() {
  const candidates = [
    "k-skill-rhwp",
    "C:/Users/andyw/AppData/Local/npm-cache/_npx/d3dffeb053155d07/node_modules/k-skill-rhwp"
  ];
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch {
      // Try the next candidate.
    }
  }
  throw new Error("k-skill-rhwp module not found. Run `npx --yes k-skill-rhwp --help` first.");
}

const rhwp = loadRhwp();

const repoRoot = "C:/Users/andyw/Desktop/My-AI-Security-Project";
const templatePath = "C:/Users/andyw/Desktop/캡스톤디자인_결과보고서 양식_정보보호학전공.hwp";
const outputDir = path.join(repoRoot, "output/doc");
const finalMarkdownPath = path.join(outputDir, "캡스톤디자인_결과보고서_4개항목_비전공자용_최종본.md");
const outputPath = path.join(outputDir, "캡스톤디자인_결과보고서_한국어PII가드레일_양식맞춤_최종본.hwp");
const markdownPath = path.join(outputDir, "캡스톤디자인_결과보고서_한국어PII가드레일_양식맞춤_최종본.md");
const section = 0;

const form = {
  major: "정보보호학전공",
  professor: "임정묵",
  courseCode: "확인 필요",
  courseName: "캡스톤디자인",
  taskType: "□ 전공융합형  ■ 전공심화형  □ 창업연계형  □ 사회기여형",
  outputType: "□ 시작품제작과제  ■ 소프트웨어개발과제  □ 기타(연구·평가 산출물)",
  projectName: "생성형 AI 환경에서의 한국어 개인정보 탐지 및 비식별화 보안 가드레일 시스템",
  company: "참여기업명 : 해당 없음",
  period: "2026. 03. (확인 필요) ~ 2026. 06. 15. (월)",
  date: "2026년 6월 15일"
};

const figures = [
  {
    cell: 1,
    captionCell: 3,
    path: path.join(repoRoot, "paper/figures/kcgsa_pipeline_guardrail_architecture.png"),
    width: 22000,
    height: 11500,
    description: "시스템 전체 구조도",
    caption: "내용 : 사용자 입력이 AI 모델로 전달되기 전에 한국어 정규화, 개인정보 후보 탐지, 문맥 판단, 정책 기반 마스킹을 거치는 전체 흐름."
  },
  {
    cell: 2,
    captionCell: 4,
    path: path.join(repoRoot, "PII/results/figures/fig11_kr_semantic_4way.png"),
    width: 22000,
    height: 14500,
    description: "한국어 의미형 개인정보 성능 비교",
    caption: "내용 : 한국어 의미형 개인정보 구간에서 한국어 선행 필터 포함 구성이 기존 구성보다 높은 탐지율을 보인 평가 그래프."
  },
  {
    cell: 5,
    captionCell: 7,
    path: path.join(repoRoot, "PII/results/figures/fig13_ablation.png"),
    width: 22000,
    height: 14500,
    description: "한국어 선행 필터 구성요소 분석",
    caption: "내용 : 정규화, 사전, 탐지 규칙의 기여도를 나누어 분석한 결과. 한국어 사전과 패턴 탐지가 핵심 개선 요인임을 보여준다."
  },
  {
    cell: 6,
    captionCell: 8,
    path: path.join(repoRoot, "PII/results/figures/fig10_4way_bypass.png"),
    width: 22000,
    height: 14500,
    description: "4가지 방어 구성 우회율 비교",
    caption: "내용 : 기본 구성, 추가 판단 구성, 한국어 선행 필터 구성, 전체 구성의 개인정보 통과 비율을 비교한 그래프."
  }
];

const professorEval = [
  "담당교수 작성란입니다. 학생 작성본에서는 임의 평가를 기재하지 않았습니다.",
  "검토 시 과제 수행 성실성, 구현 완성도, 실험 및 검증의 충실성, 문서화 수준, 실무 활용 가능성을 기준으로 종합평가를 작성해 주시면 됩니다."
];

const submission = [
  "캡스톤디자인 과제운영에 따른 결과보고서를 제출합니다.",
  "",
  `                            ${form.date}`,
  "",
  "                         팀    장 : [대표학생 확인 필요]              (인)",
  "                         담당교수 : 임정묵              (인)",
  "",
  "교무처 현장실습지원센터장 귀하"
];

function parseResult(raw, op) {
  const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
  if (!parsed || parsed.ok !== true) {
    throw new Error(`${op} failed: ${raw}`);
  }
  return parsed;
}

function getPngSize(buffer) {
  return {
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20)
  };
}

function clearCell(doc, tablePara, controlIdx, cellIdx) {
  const paraCount = doc.getCellParagraphCount(section, tablePara, controlIdx, cellIdx);
  for (let cp = 0; cp < paraCount; cp += 1) {
    const len = doc.getCellParagraphLength(section, tablePara, controlIdx, cellIdx, cp);
    if (len > 0) {
      parseResult(
        doc.deleteTextInCell(section, tablePara, controlIdx, cellIdx, cp, 0, len),
        `deleteTextInCell ${tablePara}:${cellIdx}:${cp}`
      );
    }
  }
}

function ensureCellParagraphs(doc, tablePara, controlIdx, cellIdx, count) {
  let paraCount = doc.getCellParagraphCount(section, tablePara, controlIdx, cellIdx);
  while (paraCount < count) {
    const last = paraCount - 1;
    const len = doc.getCellParagraphLength(section, tablePara, controlIdx, cellIdx, last);
    parseResult(
      doc.splitParagraphInCell(section, tablePara, controlIdx, cellIdx, last, len),
      `splitParagraphInCell ${tablePara}:${cellIdx}:${last}`
    );
    paraCount += 1;
  }
}

function setCellParagraphs(doc, tablePara, cellIdx, paragraphs, controlIdx = 0) {
  clearCell(doc, tablePara, controlIdx, cellIdx);
  ensureCellParagraphs(doc, tablePara, controlIdx, cellIdx, Math.max(1, paragraphs.length));
  paragraphs.forEach((paragraph, index) => {
    if (paragraph) {
      parseResult(
        doc.insertTextInCell(section, tablePara, controlIdx, cellIdx, index, 0, paragraph),
        `insertTextInCell ${tablePara}:${cellIdx}:${index}`
      );
    }
  });
}

function setCellText(doc, tablePara, cellIdx, text, controlIdx = 0) {
  setCellParagraphs(doc, tablePara, cellIdx, [text], controlIdx);
}

function replaceBodyParagraph(doc, paragraphIndex, text) {
  const len = doc.getParagraphLength(section, paragraphIndex);
  if (len > 0) {
    parseResult(doc.deleteText(section, paragraphIndex, 0, len), `deleteText paragraph ${paragraphIndex}`);
  }
  if (text) {
    parseResult(doc.insertText(section, paragraphIndex, 0, text), `insertText paragraph ${paragraphIndex}`);
  }
}

function deleteNonResultForms(doc) {
  for (let paragraphIndex = 17; paragraphIndex >= 10; paragraphIndex -= 1) {
    parseResult(doc.deleteParagraph(section, paragraphIndex), `deleteParagraph ${paragraphIndex}`);
  }
}

function normalizeParagraph(block) {
  let text = block.trim();
  text = text.replace(/^###\s+/, "");
  text = text.replace(/^##\s+/, "");
  text = text.replace(/^#\s+/, "");
  text = text.replace(/`([^`]+)`/g, "$1");
  text = text.replace(/\*\*([^*]+)\*\*/g, "$1");
  text = text.replace(/<br\s*\/?>/gi, " ");
  return text;
}

function convertMarkdownTable(block) {
  const rows = block
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|") && !/^\|\s*-+/.test(line));

  if (rows.length === 0) {
    return [];
  }

  return rows.map((row) => {
    const cells = row
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim().replace(/---?:?/g, ""))
      .filter((cell) => cell.length > 0);
    return cells.join(" / ");
  });
}

function sectionBlocks(markdown, heading) {
  const lines = markdown.split(/\r?\n/);
  const start = lines.findIndex((line) => line.trim() === `## ${heading}`);
  if (start === -1) {
    throw new Error(`Markdown section not found: ${heading}`);
  }
  let end = lines.length;
  for (let index = start + 1; index < lines.length; index += 1) {
    if (lines[index].startsWith("## ")) {
      end = index;
      break;
    }
  }

  const rawBlocks = lines.slice(start + 1, end).join("\n").trim().split(/\n\s*\n/g);
  const result = [];
  for (const block of rawBlocks) {
    if (block.trim().startsWith("|")) {
      result.push(...convertMarkdownTable(block));
      continue;
    }
    const normalized = normalizeParagraph(block);
    if (normalized) {
      result.push(normalized);
    }
  }
  return result;
}

function insertFigure(doc, figure) {
  if (!fs.existsSync(figure.path)) {
    setCellText(doc, 5, figure.cell, `(그림 파일 없음) ${figure.path}`);
    return;
  }
  clearCell(doc, 5, 0, figure.cell);
  const image = fs.readFileSync(figure.path);
  const size = getPngSize(image);
  const cellPath = JSON.stringify([{ controlIndex: 0, cellIndex: figure.cell, cellParaIndex: 0 }]);
  parseResult(
    doc.insertPicture(
      section,
      5,
      0,
      cellPath,
      image,
      figure.width,
      figure.height,
      size.width,
      size.height,
      "png",
      figure.description
    ),
    `insertPicture ${figure.description}`
  );
  setCellText(doc, 5, figure.captionCell, figure.caption);
}

function appendSanitizedFullMarkdown(doc, markdown) {
  const paragraphs = [
    "",
    "최종 본문 원문",
    ...markdown
      .split(/\n\s*\n/g)
      .flatMap((block) => {
        const trimmed = block.trim();
        if (!trimmed) return [];
        if (trimmed.startsWith("|")) return convertMarkdownTable(trimmed);
        return [normalizeParagraph(trimmed)];
      })
      .filter(Boolean)
  ];

  const start = doc.getParagraphCount(section);
  for (let index = 0; index < paragraphs.length; index += 1) {
    const tail = doc.getParagraphCount(section) - 1;
    parseResult(doc.insertParagraph(section, tail), `insertParagraph ${start + index}`);
  }
  for (let index = 0; index < paragraphs.length; index += 1) {
    replaceBodyParagraph(doc, start + index, paragraphs[index]);
  }
}

function buildTemplateMarkdown(sections) {
  const figureLines = figures.map((figure, index) => `${index + 1}. ${figure.description}: ${figure.path}\n   ${figure.caption}`);
  return [
    "# 캡스톤디자인 결과보고서 양식맞춤 최종본",
    "",
    "## 기본사항",
    "",
    `- 전공(과): ${form.major}`,
    `- 담당교수명: ${form.professor}`,
    `- 교과목코드: ${form.courseCode}`,
    `- 교과목명: ${form.courseName}`,
    `- 과제유형: ${form.taskType}`,
    `- 결과물 유형: ${form.outputType}`,
    `- 작품(과제)명: ${form.projectName}`,
    `- 기업참여: ${form.company}`,
    `- 운영기간: ${form.period}`,
    "",
    "## 1. 과제 목적 및 필요성",
    "",
    ...sections.purpose,
    "",
    "## 2. 작품 제작 과정",
    "",
    ...sections.process,
    "",
    "## 3. 작품개념, 구성 및 상세내용",
    "",
    ...sections.concept,
    "",
    "## 4. 기대효과 및 활용방안",
    "",
    ...sections.effects,
    "",
    "## 5. 결과물 사진",
    "",
    ...figureLines,
    "",
    "## 6. 지도교수 종합평가",
    "",
    ...professorEval
  ].join("\n\n");
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const markdown = fs.readFileSync(finalMarkdownPath, "utf8");
  const sections = {
    purpose: sectionBlocks(markdown, "1. 과제 목적 및 필요성"),
    process: sectionBlocks(markdown, "2. 작품 제작 과정"),
    concept: sectionBlocks(markdown, "3. 작품개념, 구성 및 상세내용"),
    effects: sectionBlocks(markdown, "4. 기대효과 및 활용방안")
  };

  const doc = await rhwp.loadDocument(templatePath);
  try {
    deleteNonResultForms(doc);

    setCellText(doc, 1, 4, form.major);
    setCellText(doc, 1, 6, form.professor);
    setCellText(doc, 1, 8, form.courseCode);
    setCellText(doc, 1, 10, form.courseName);
    setCellText(doc, 1, 12, form.taskType);
    setCellText(doc, 1, 14, form.outputType);
    setCellText(doc, 1, 16, form.projectName);
    setCellText(doc, 1, 18, form.company);
    setCellText(doc, 1, 20, form.period);
    setCellParagraphs(doc, 1, 22, sections.purpose);
    setCellParagraphs(doc, 1, 24, sections.process);

    setCellParagraphs(doc, 2, 1, sections.concept);
    setCellParagraphs(doc, 2, 3, sections.effects);

    for (const figure of figures) {
      insertFigure(doc, figure);
    }

    setCellParagraphs(doc, 7, 1, professorEval);
    setCellParagraphs(doc, 7, 2, submission);

    rhwp.writeHwp(doc, outputPath);
  } finally {
    doc.free();
  }

  fs.writeFileSync(markdownPath, buildTemplateMarkdown(sections), "utf8");

  const info = await rhwp.getDocumentInfo(outputPath);
  console.log(JSON.stringify({ outputPath, markdownPath, info }, null, 2));
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
