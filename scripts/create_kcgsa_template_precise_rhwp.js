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

const templatePath =
  "C:/Users/andyw/Desktop/My-AI-Security-Project/output/doc/kcgsa_template_original_ascii.hwp";
const outputPath =
  "C:/Users/andyw/Desktop/My-AI-Security-Project/output/doc/kcgsa_2026_template_precise_rhwp.hwp";

const entries = [
  { exemplar: 0, text: "초거대 AI 플랫폼에서 한국어 개인정보 흐름 통제를 위한 LLM Gateway 기반 Layer 0 가드레일 설계 및 평가" },
  { exemplar: 1, text: "양유상1*, 김민우2, 정연서2, [교수명1]3, [교수명2]3, [교수명3]3" },
  { exemplar: 2, text: "중부대학교1, CCIT연구소2, [소속 입력]3" },
  { exemplar: 3, text: "" },
  { exemplar: 4, text: "Design and Evaluation of a Layer 0 Guardrail for Korean Personal Information Flow Control in LLM Gateways" },
  { exemplar: 5, text: "YuSsang Yang1*, Minwoo Kim2, Yeonseo Jeong2, [Professor Name 1]3, [Professor Name 2]3, [Professor Name 3]3, Joongbu University1, CCIT Research Institute2, [Affiliation]3" },
  { exemplar: 6, text: "__ORIGINAL__" },
  { exemplar: 7, text: "요약 : 초거대 AI 플랫폼에서는 사용자 입력, 모델 응답, 감사로그를 거쳐 개인정보가 이동하므로 LLM 호출 전 단계의 흐름 통제가 필요하다. 본 논문은 한국어 정규화와 PII 사전, 패턴 탐지를 결합한 LLM-free Layer 0를 LLM Gateway의 pre-call 계층으로 배치한다. 10k stratified payload 평가에서 Layer 0 구성은 전체 TRUE detection 94.32%, KR_semantic 96.39%, p99 830ms를 보였고, LLM judge 구성의 90.96%, 87.40%, p99 4,819ms보다 높은 탐지율과 낮은 지연을 달성하였다." },
  { exemplar: 8, text: "" },
  { exemplar: 9, text: "Key Words : Korean PII, LLM Gateway, Layer 0 Guardrail, Korean Normalization, Personal Information Flow Control" },
  { exemplar: 10, text: "" },
  { exemplar: 11, text: "1. 서 론" },
  { exemplar: 12, text: "초거대 AI 플랫폼이 업무 서비스에 연결되면 개인정보는 사용자 입력, 모델 응답, 운영 로그, 감사 데이터로 이동한다. LLM Gateway는 여러 모델 호출이 집중되는 통제 지점이므로, 개인정보를 LLM 또는 외부 API로 보내기 전에 탐지, 차단, 마스킹하는 선행 방어 계층이 필요하다." },
  { exemplar: 13, text: "한국어 개인정보는 주민등록번호와 전화번호 같은 정형 패턴뿐 아니라 진단명, 알레르기, 종교, 직위, 소속, 결혼상태 등 의미형 개인정보를 포함한다. 공격자는 자모 분해, 초성 표기, 야민정음, Unicode 변형, 구분자 삽입으로 표면형을 바꾸어 기존 탐지를 우회할 수 있다." },
  { exemplar: 14, text: "기존 PII 탐지는 정규식, NER, 관리형 보안 필터, LLM judge 등을 활용한다. NER(Named Entity Recognition)는 텍스트 안의 사람명, 기관명, 주소 같은 개체를 자동 식별하는 기법이고, LLM judge는 별도 언어모델이 입력 또는 출력을 재판정하는 방식이다. 그러나 LLM judge는 비용, 지연, 외부 API 의존성을 동반한다." },
  { exemplar: 15, text: "본 논문은 한국어 정규화와 PII 사전, 패턴 탐지를 결합한 Layer 0를 pre-call 단계에 배치하고, 기존 LLM judge 구성과 비교하여 한국어 개인정보 흐름 통제의 효과를 평가한다." },
  { exemplar: 16, text: "" },
  { exemplar: 17, text: "2. 관련연구 및 위협모델" },
  { exemplar: 18, text: "2.1 관련연구  한국어 개인정보 탐지는 한글 자모, 호환 자모, Unicode 정규화, 표기 변형의 영향을 받는다. 기존 한글 정규화 연구는 유니코드 환경에서 한글 표현 체계와 조합 문제를 분석하였고[1], 한국어 PII 연구는 개인 식별 번호와 개인정보 처리 능력을 평가하였다[2]. 최근에는 KcBERT, Chain-of-Thought 프롬프팅, 정규화 사전을 결합한 한국어 개인정보 보호 연구가 제안되었다[3]. 문자 수준 공격과 guardrail robustness 연구는 인코딩 교란과 mutation이 우회 수단이 될 수 있음을 보였다[4][5]." },
  { exemplar: 19, text: "2.2 위협모델  본 연구는 LLM 사용자가 개인정보 검사를 우회하기 위해 입력 표면형을 변형하는 상황을 가정한다. 공격자는 시스템 내부 설정에는 접근하지 못하지만 입력 텍스트는 자유롭게 구성할 수 있다. 예를 들어 알레르기, 처방, 사건번호, 계좌번호, 소속, 직책 같은 민감정보를 자모 분해, zero-width 문자, fullwidth 숫자, 초성 표기, 로그 문맥 형태로 입력할 수 있다. 방어 목표는 원문 개인정보를 LLM 호출 전에 탐지하고 정책에 따라 차단 또는 마스킹하는 것이다." },
  { exemplar: 20, text: "" },
  { exemplar: 11, text: "3. 연구내용" },
  { exemplar: 12, text: "3.1 제안 방법 개요  제안 Layer 0는 사용자 입력이 LLM과 외부 가드레일로 전달되기 전에 실행되는 pre-call 계층이다. 먼저 한국어 normalizer가 Unicode, 자모, 초성, 야민정음, 숫자와 구분자 변형을 표준형으로 복원한다. 이후 한국어 PII detector가 regex, 키워드, 의미 사전으로 개인정보 후보를 탐지한다. Layer 0는 LLM 호출 없이 로컬에서 동작하므로 재현성과 감사 가능성이 높다." },
  { exemplar: 12, text: "3.2 실험 설계  10k stratified payload를 사용하여 네 가지 구성을 비교하였다. 주요 slice는 한국어 의미형 PII를 포함하는 KR_semantic(n=1,302)이다. TRUE detection은 ground-truth PII payload의 차단 또는 마스킹 성공률이고, real bypass는 해당 payload가 통과한 비율이다. p99 latency는 전체 요청 지연시간을 오름차순 정렬했을 때 99% 지점의 값이다." },
  { exemplar: 21, text: "Table 1. Evaluation Configurations and Main Results" },
  { exemplar: 20, text: "" },
  { exemplar: 12, text: "3.3 실험 결과  Layer 0를 포함한 C 구성은 LLM judge를 포함한 B 구성보다 전체와 KR_semantic 모두에서 높은 TRUE detection을 보였다. 전체 10k 기준으로 C는 94.32%, B는 90.96%였으며, C가 B보다 3.36%p 높았다. KR_semantic slice에서는 C가 96.39%, B가 87.40%로 +8.99%p 차이를 보였다." },
  { exemplar: 12, text: "지연 측면에서도 C는 B보다 우수하였다. C의 p99 latency는 830ms인 반면 B는 4,819ms였다. B와 C의 paired 비교에서 McNemar p-value는 2.04e-28로 보고되어, Layer 0 포함 구성의 개선을 우연한 차이로 보기 어렵다. 정상 텍스트에 대한 false positive는 2%로 측정되었다. ablation 결과 KR_semantic 기준 정규화 단독 gain은 0.31%p로 제한적이었고, detector와 dictionary의 기여가 더 컸다." },
  { exemplar: 16, text: "" },
  { exemplar: 16, text: "" },
  { exemplar: 16, text: "" },
  { exemplar: 31, text: "3.4 논의" },
  { exemplar: 12, text: "C가 B보다 높은 결과를 보인 것은 Layer 0가 모든 경우의 LLM judge를 대체한다는 의미가 아니라, 한국어 의미형 PII 중 상당 부분을 LLM 호출 전에 deterministic하게 탐지할 수 있음을 보여준다. 정책적으로는 반복적 자모 분해, invisible character 삽입, 표기 변형 입력을 개인정보 검사 우회 목적의 잠재적 공격으로 간주할 수 있다. 원문 개인정보를 저장하지 않는 범위에서 탐지 유형, 변형 유형, 정책 결정, span 길이, HMAC 기반 식별자 등을 감사로그로 남기고 반복 시도에는 경고, rate limit, 관리자 검토, 이용 제재 절차를 둘 필요가 있다." },
  { exemplar: 16, text: "" },
  { exemplar: 34, text: "4. 결 론" },
  { exemplar: 35, text: "본 논문은 초거대 AI 플랫폼에서 한국어 개인정보 흐름을 사전에 통제하기 위한 LLM Gateway 기반 Layer 0 Guardrail을 설계하고 평가하였다. 실험 결과 Layer 0 포함 구성은 전체 TRUE detection과 KR_semantic slice에서 LLM judge 포함 구성보다 높은 탐지율을 보였고 p99 지연도 낮았다." },
  { exemplar: 12, text: "향후 연구에서는 실제 한국어 운영 로그에 가까운 clean corpus, attack-family별 ablation, 도메인별 PII 사전 확장, Smart Skip 기반 L4 호출 최적화를 추가 검증할 필요가 있다. 본 연구는 deterministic pre-call guardrail이 한국어 LLM 서비스의 저지연 개인정보 방어선이 될 수 있음을 보이며, 초거대 AI 플랫폼의 개인정보 흐름 통제와 융합보안 거버넌스 설계에 실증적 근거를 제공한다." },
  { exemplar: 16, text: "" },
  { exemplar: 38, text: "참고문헌" },
  { exemplar: 39, text: "" },
  { exemplar: 40, text: "[1]\t안대혁, 박영배, 유니코드 환경에서의 올바른 한글 정규화를 위한 수정 방안, 정보과학회논문지: 소프트웨어 및 응용, Vol. 34, No. 2, pp. 169-177, 2007." },
  { exemplar: 41, text: "[2]\t강예지, 비람, 박서현, 손연지, 이종국, 김현수, 한국어 언어모델의 개인 식별 번호 처리 능력 연구, 한국콘텐츠학회논문지, Vol. 24, No. 4, pp. 42-58, 2024." },
  { exemplar: 42, text: "[3]\t이태규, 이익현, 이제미, 정수민, 조혜민, 김형진, 생성형AI 시대 한국어 데이터 보호 연구: KcBERT와 Chain-of-Thought 프롬프팅 기반 하이브리드 접근법, 경영정보학연구, Vol. 27, No. 1, pp. 247-268, 2025." },
  { exemplar: 43, text: "[4]\tN. Boucher, I. Shumailov, R. Anderson, and N. Papernot, Bad Characters: Imperceptible NLP Attacks, Proceedings of the IEEE Symposium on Security and Privacy, 2022. [5] E. Bassani and I. Sanchez, On Guardrail Models Robustness to Mutations and Adversarial Attacks, Findings of ACL: EMNLP 2025, pp. 16995-17006, 2025." }
];

const tableRows = [
  ["Config", "Composition", "Purpose", "Overall TRUE", "KR_semantic", "p99"],
  ["A", "L1-L3", "Baseline", "80.15%", "49.62%", "1,317ms"],
  ["B", "L1-L4", "LLM judge", "90.96%", "87.40%", "4,819ms"],
  ["C", "L0-L3", "Proposed", "94.32%", "96.39%", "830ms"],
  ["D", "L0-L4", "Full stack", "97.23%", "98.85%", "4,762ms"]
];

function parseResult(raw, op) {
  const parsed = JSON.parse(raw);
  if (!parsed || parsed.ok !== true) {
    throw new Error(`${op} failed: ${raw}`);
  }
  return parsed;
}

function readJson(raw) {
  return typeof raw === "string" ? JSON.parse(raw) : raw;
}

function safeControl(doc, op, args) {
  try {
    return JSON.parse(doc[op](...args));
  } catch (err) {
    return { ok: false, skipped: true, error: err && err.message ? err.message : String(err) };
  }
}

function collectFormats(doc) {
  const formats = [];
  for (let p = 0; p < entries.length; p += 1) {
    const len = doc.getParagraphLength(0, p);
    formats[p] = {
      text: len > 0 ? doc.getTextRange(0, p, 0, len) : "",
      style: readJson(doc.getStyleAt(0, p, 0)),
      para: readJson(doc.getParaPropertiesAt(0, p, 0)),
      char: readJson(doc.getCharPropertiesAt(0, p, 0))
    };
  }
  return formats;
}

function applyFormat(doc, paragraph, format) {
  parseResult(doc.applyStyle(0, paragraph, format.style.id), `applyStyle ${paragraph}`);
  parseResult(doc.applyParaFormat(0, paragraph, JSON.stringify(format.para)), `applyParaFormat ${paragraph}`);
  const len = doc.getParagraphLength(0, paragraph);
  if (len > 0) {
    parseResult(
      doc.applyCharFormat(0, paragraph, 0, len, JSON.stringify(format.char)),
      `applyCharFormat ${paragraph}`
    );
  }
}

function findControls(doc) {
  const controls = [];
  const count = doc.getParagraphCount(0);
  for (let p = 0; p < count; p += 1) {
    const len = doc.getParagraphLength(0, p);
    for (const offset of [0, Math.max(0, len - 1), len]) {
      try {
        const c = JSON.parse(doc.findNearestControlForward(0, p, offset));
        if (c.type !== "none" && !controls.some((x) => x.type === c.type && x.para === c.para && x.ci === c.ci)) {
          controls.push(c);
        }
      } catch {
        // Ignore malformed cursor probes.
      }
    }
  }
  return controls;
}

async function main() {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  const doc = await rhwp.loadDocument(templatePath);
  try {
    const formats = collectFormats(doc);

    safeControl(doc, "deleteHeaderFooter", [0, true, 1]);
    safeControl(doc, "deleteHeaderFooter", [0, true, 2]);
    safeControl(doc, "deletePictureControl", [0, 24, 0]);
    safeControl(doc, "deleteTableControl", [0, 23, 0]);

    for (let p = 0; p < entries.length; p += 1) {
      const len = doc.getParagraphLength(0, p);
      if (len > 0) {
        parseResult(doc.deleteText(0, p, 0, len), `deleteText ${p}`);
      }
      const entry = entries[p];
      if (entry.exemplar !== p) {
        applyFormat(doc, p, formats[entry.exemplar]);
      }
      const text = entry.text === "__ORIGINAL__" ? formats[p].text : entry.text;
      if (text) {
        parseResult(doc.insertText(0, p, 0, text), `insertText ${p}`);
        if (entry.exemplar !== p) {
          applyFormat(doc, p, formats[entry.exemplar]);
        }
      }
    }

    const tableParagraph = 25;
    const created = parseResult(
      doc.createTable(0, tableParagraph, 0, tableRows.length, tableRows[0].length),
      "createTable"
    );
    const bodyChar = formats[12].char;
    for (let r = 0; r < tableRows.length; r += 1) {
      for (let c = 0; c < tableRows[r].length; c += 1) {
        const cell = r * tableRows[r].length + c;
        parseResult(
          doc.insertTextInCell(0, created.paraIdx, created.controlIdx, cell, 0, 0, tableRows[r][c]),
          `insertTextInCell ${r},${c}`
        );
        safeControl(doc, "applyCharFormatInCell", [0, created.paraIdx, created.controlIdx, cell, 0, 0, tableRows[r][c].length, JSON.stringify(bodyChar)]);
      }
    }

    for (const control of findControls(doc).filter((c) => c.type === "equation").sort((a, b) => b.para - a.para)) {
      const len = doc.getParagraphLength(0, control.para);
      const text = len > 0 ? doc.getTextRange(0, control.para, 0, len) : "";
      if (text.trim() === "" || text.trim() === "(1)") {
        safeControl(doc, "deleteParagraph", [0, control.para]);
      } else {
        safeControl(doc, "deleteEquationControl", [0, control.para, control.ci]);
      }
    }

    rhwp.writeHwp(doc, outputPath);
  } finally {
    doc.free();
  }

  const info = await rhwp.getDocumentInfo(outputPath);
  console.log(JSON.stringify({ outputPath, info }, null, 2));
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
