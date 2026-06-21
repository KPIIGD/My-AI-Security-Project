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
      // Try next candidate.
    }
  }
  throw new Error("k-skill-rhwp module not found. Run `npx --yes k-skill-rhwp --help` first.");
}

const rhwp = loadRhwp();

const templatePath = "C:/Users/andyw/Desktop/캡스톤디자인_결과보고서 양식_정보보호학전공.hwp";
const outputDir = "C:/Users/andyw/Desktop/My-AI-Security-Project/output/doc";
const outputPath = path.join(outputDir, "캡스톤디자인_결과보고서_한국어PII가드레일_작성본.hwp");
const markdownPath = path.join(outputDir, "캡스톤디자인_결과보고서_한국어PII가드레일_작성본.md");

const section = 0;

const figures = [
  {
    cell: 1,
    captionCell: 3,
    path: "C:/Users/andyw/Desktop/My-AI-Security-Project/paper/figures/kcgsa_pipeline_guardrail_architecture.png",
    width: 22000,
    height: 11500,
    description: "시스템 전체 구조도",
    caption: "내용 : LLM Gateway 앞단에서 Layer 0 한국어 정규화·PII 탐지 계층이 입력을 선제 검사하고, 이후 Presidio, Bedrock, Lakera, LLM judge와 결합되는 전체 구조."
  },
  {
    cell: 2,
    captionCell: 4,
    path: "C:/Users/andyw/Desktop/My-AI-Security-Project/PII/results/figures/fig11_kr_semantic_4way.png",
    width: 22000,
    height: 14500,
    description: "KR semantic 4-way 성능 비교",
    caption: "내용 : 한국어 텍스트형 PII slice에서 Layer 0 포함 구성이 LLM judge 구성보다 높은 TRUE detection을 보인 핵심 평가 그래프."
  },
  {
    cell: 5,
    captionCell: 7,
    path: "C:/Users/andyw/Desktop/My-AI-Security-Project/PII/results/figures/fig13_ablation.png",
    width: 22000,
    height: 14500,
    description: "Layer 0 ablation 결과",
    caption: "내용 : 정규화 단독 효과보다 한국어 PII 사전·패턴 탐지의 기여가 크다는 점을 확인한 ablation 결과."
  },
  {
    cell: 6,
    captionCell: 8,
    path: "C:/Users/andyw/Desktop/My-AI-Security-Project/PII/results/figures/fig10_4way_bypass.png",
    width: 22000,
    height: 14500,
    description: "4-way 우회율 비교",
    caption: "내용 : Baseline, LLM judge, Layer 0, Full stack의 전체 우회율을 비교하여 제안 계층의 실질적 누출 저감 효과를 시각화."
  }
];

const form = {
  major: "정보보호학전공",
  professor: "임정묵",
  courseCode: "확인 필요",
  courseName: "캡스톤디자인",
  taskType: "□ 전공융합형  ■ 전공심화형  □ 창업연계형  □ 사회기여형",
  outputType: "□ 시작품제작과제  ■ 소프트웨어개발과제  □ 기타(연구·평가 산출물)",
  projectName: "한국어 LLM Gateway 환경에서 변이형 PII 우회 저감을 위한 LLM-free Layer 0 Guardrail 설계와 평가",
  company: "참여기업명 : 해당 없음",
  period: "2026. 03. (확인 필요) ~ 2026. 06. 15. (월)",
  date: "2026년 6월 15일"
};

const purpose = [
  "생성형 AI 서비스와 LLM Gateway가 실제 업무 환경에 도입되면 사용자 입력, 모델 응답, 운영 로그, 감사 데이터에 주민등록번호·전화번호·이메일·계좌번호·의료정보·직장정보 등 개인정보가 섞여 외부 모델이나 후속 시스템으로 전달될 수 있다. 특히 한국어 개인정보는 정형 숫자뿐 아니라 알레르기, 처방, 가족관계, 직책, 학교, 병원, 주소처럼 문맥에 의존하는 의미형 정보가 많아 영어 중심 상용 가드레일만으로는 탐지 공백이 발생한다.",
  "본 과제의 목적은 한국어 입력에서 개인정보 후보를 낮은 비용과 지연으로 선제 탐지하고, 정책에 따라 마스킹·해시·차단을 수행하는 소프트웨어 가드레일을 설계·구현·평가하는 것이다. 단순 정규식 모음이 아니라 원문 offset 보존, 한국어 조사·호칭·어미 분리, 변이형 표현 복원, 문맥 점수화, 중복 span 병합, raw PII 비저장 감사로그까지 포함한 end-to-end 파이프라인을 목표로 삼았다.",
  "필요성은 세 가지다. 첫째, 영어 중심 가드레일은 한국어 자모 분해, 초성 표기, zero-width 문자, 전각 숫자, 야민정음, 로마자 혼합 같은 변이형 공격에 취약하다. 둘째, 모든 의심 입력을 LLM judge에 맡기면 API 비용, 외부 의존성, p99 지연, 재현성 문제가 커진다. 셋째, 개인정보 보호 관점에서는 탐지 결과 자체도 민감할 수 있으므로 평가 리포트와 감사로그에 raw PII가 남지 않는 구조가 필요하다.",
  "따라서 본 프로젝트는 한국어 PII 탐지를 LLM 호출 이전의 결정론적 방어선으로 배치하고, 필요 시 기존 상용 가드레일 또는 LLM judge와 조합할 수 있는 실무형 보안 모듈을 만드는 데 의의가 있다."
];

const process = [
  "1단계에서는 기존 프로덕션형 LLM Gateway 보안 구성을 분석했다. LiteLLM Gateway 환경에 Presidio, AWS Bedrock Guardrails, Lakera Guard, GPT-4o-mini judge를 결합한 다계층 평가 구조를 만들고, 한국어 PII 퍼저로 생성한 10,000건 stratified payload를 통해 영어 중심 가드레일의 한국어 탐지 공백을 수치화했다.",
  "2단계에서는 한국어 특화 Layer 0 방어 계층을 설계했다. Korean Normalizer는 NFKC, zero-width 제거, 전각·원문자 숫자 정규화, 자모 결합, 초성·야민정음·로마자 한국어·한글 숫자 복원 등 변이형 입력을 탐지 가능한 형태로 바꿨다. Korean PII Detector는 정규식, 체크섬 validator, 키워드 사전, 문맥 키워드를 결합해 정형·비정형 PII 후보를 생성했다.",
  "3단계에서는 초기 연구 스택을 제품형 v0.2 single-turn core로 정리했다. RAG scan, 멀티턴 session monitor, fragment ledger, human review dashboard 등은 v0.2 범위에서 제외하고, 단일 입력 텍스트의 탐지·보정·판정·마스킹에 집중했다. 이 과정에서 raw text character offset 보존, public span raw text 제거, audit event raw PII 저장 금지를 핵심 계약으로 고정했다.",
  "4단계에서는 Python 패키지 `pii_guardrail`을 구현했다. 주요 모듈은 schema/enums, preprocess, regex_detectors, validators, korean_boundary, dictionary_loader, dictionary_detectors, context_scorer, NER interface, span_resolver, policy, masker, audit_logger, pipeline, evaluation harness, ablation runner로 구성된다. FastAPI 기반 로컬 콘솔 API와 React/Vite 웹 콘솔도 함께 구성했다.",
  "5단계에서는 평가와 검증을 수행했다. legacy 10k 4-way 평가에서는 Layer 0 포함 구성이 KR_semantic slice에서 GPT-4o-mini judge 구성보다 높은 탐지율을 보였다. v0.2 release gate에서는 synthetic fixture 5,000건을 대상으로 overall F1, actionable F1, high-risk recall, josa boundary accuracy, raw PII logging count, invalid offset count 등을 확인했다."
];

const concept = [
  "작품의 핵심 개념은 `한국어 LLM Gateway용 개인정보 가드레일`이다. 사용자 입력 또는 모델 출력 텍스트를 받아 개인정보 후보 span을 탐지하고, 한국어 문법을 보존하면서 `[PERSON_1]`, `[PHONE_1]` 같은 label mask 또는 HMAC hash, block action을 반환한다. 탐지기는 최종 결정을 내리지 않고 후보만 생성하며, 최종 action은 context scorer, span resolver, policy router, masker가 단계적으로 결정한다.",
  "구성은 L0 Preprocessor, L1 Regex/Validator, L2 Dictionary/NER Candidate, L3 Korean Boundary Corrector, L5 Context Scorer, L6 Span Resolver, L7 Policy Router/Masker, Audit Logger, Evaluation Harness로 나뉜다. 전처리는 원문 offset map을 보존하고, 탐지용 variant를 raw span으로 복원할 수 있을 때만 후보를 허용한다. Boundary corrector는 `홍길동이`를 `홍길동` + suffix `이`로 분리하여 `[PERSON_1]이`처럼 자연스러운 마스킹을 가능하게 한다.",
  "정형 PII는 RRN, FRN, 전화번호, 이메일, 카드번호, 계좌번호, 사업자등록번호, 법인등록번호, 여권, 운전면허, IP/MAC, API key 등을 대상으로 한다. 의미형 PII는 PERSON_NAME, ADDRESS_FULL, ADDRESS_UNIT, ORGANIZATION, SCHOOL, HOSPITAL, FAMILY_RELATION, MEDICAL_RECORD_NO 등을 다룬다. 이름·주소·조직은 NER interface 뒤에 연결할 수 있도록 설계했고, mock NER와 real NER adapter 경로를 분리했다.",
  "평가 결과, 2026-05-25 기준 v0.2 release gate는 5,000건 synthetic fixture에서 pass 상태다. 주요 지표는 overall precision/recall/F1 0.8803/0.9729/0.9243, actionable precision/recall/F1 0.9975/0.8991/0.9457, high-risk structured recall 1.0000, actionable high-risk recall 0.9645, josa boundary accuracy 0.9989, raw PII logging count 0, invalid offset count 0이다.",
  "legacy 10,000건 4-way 평가에서는 Baseline(L1-L3) TRUE detection 80.15%, LLM judge 포함 90.96%, Layer 0 포함 94.32%, Full stack 97.23%를 기록했다. 한국어 텍스트형 PII(KR_semantic, n=1,302)에서는 Baseline 49.62%, LLM judge 87.40%, Layer 0 96.39%, Full stack 98.85%로 나타났다. 이는 한국어 도메인 사전과 정규화 기반 deterministic 계층이 LLM judge의 비용·지연 없이 실질적인 보강 효과를 낼 수 있음을 보여준다.",
  "현재 한계도 명확히 관리한다. PERSON_NAME NER 후보 품질, ADDRESS granularity, real NER latency 분리 계측, custom identifier profile, 도메인별 policy profile은 후속 과제로 남아 있다. 또한 v0.2는 단일 입력 텍스트만 다루며, RAG 문서 스캔과 멀티턴 조각 결합은 v1 범위로 분리했다."
];

const effects = [
  "첫째, 한국어 LLM 서비스에서 개인정보 유출을 사전에 줄일 수 있다. 특히 기존 영어 중심 가드레일이 약한 한국어 의미형 PII와 변이형 입력에 대해 LLM 호출 전 deterministic 탐지를 수행하므로, 외부 API로 민감정보가 전달되는 위험을 낮춘다.",
  "둘째, 비용과 지연을 줄일 수 있다. 모든 입력을 LLM judge에 보내는 방식은 높은 p99 latency와 호출 비용을 만든다. 본 프로젝트의 Layer 0는 로컬 규칙·사전·정규화 기반으로 동작하므로 기본 방어선으로 두고, 불확실한 일부 케이스에만 LLM judge를 호출하는 Smart Cascade 구조로 확장할 수 있다.",
  "셋째, 감사 가능성과 재현성을 높인다. 같은 입력과 같은 config에서는 동일한 탐지·마스킹 결과가 나오며, audit log에는 entity type, score, action, reason code, span length, HMAC hash만 남기고 raw PII를 저장하지 않는다. 이는 보안 운영과 개인정보보호 컴플라이언스 양쪽에서 중요하다.",
  "넷째, 실무 적용 범위가 넓다. 고객상담, 의료 EMR, 금융 콜센터, 교육 행정, 공공 민원, 사내 업무 챗봇처럼 한국어 자유문 입력이 들어오는 시스템에 라이브러리, REST API, LLM Gateway plugin, 로그 마스킹 배치 작업 형태로 적용할 수 있다.",
  "다섯째, 후속 연구와 제품화 기반을 제공한다. 현재 산출물은 Python 패키지, API service, 웹 콘솔, 평가 harness, release gate report, ablation report, synthetic fixture를 포함한다. 향후 실제 비식별 정상 corpus, 도메인별 사전, ONNX/INT8 NER 최적화, RAG/multiturn 확장으로 이어갈 수 있다."
];

const professorEval = [
  "담당교수 작성란입니다. 학생 작성본에서는 임의 평가를 기재하지 않았습니다.",
  "검토 후 과제 수행 성실성, 결과물 완성도, 실험·검증의 충실성, 실무 활용 가능성 등을 기준으로 종합평가를 작성해 주시면 됩니다."
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

const appendix = [
  "붙임. 상세 결과보고서",
  "1. 프로젝트 개요",
  "본 프로젝트는 한국어 LLM Gateway 환경에서 개인정보가 사용자 입력, 모델 호출, 모델 출력, 운영 로그를 거치며 유출될 수 있는 문제를 다룬다. 기존 상용 가드레일은 영어 중심 숫자·형식형 PII에는 강하지만, 한국어 의미형 PII와 변이형 입력에서는 탐지 공백이 생긴다. 이를 보완하기 위해 한국어 정규화, 사전·패턴 탐지, 체크섬 validator, 한국어 boundary correction, context scoring, masking policy, raw-free audit logging을 결합한 보안 소프트웨어를 개발했다.",
  "2. 문제 정의",
  "LLM 기반 서비스에서 PII 방어는 단순히 모델이 답변을 조심하게 만드는 문제가 아니다. 외부 모델 호출 전에 사용자의 입력 자체가 검사되어야 하고, 모델 출력이나 감사 로그에도 원문 PII가 남지 않아야 한다. 한국어에서는 조사·호칭·어미가 PII 뒤에 붙고, 자모 분해나 zero-width 문자 삽입으로 표면형이 쉽게 변형되므로 일반적인 정규식이나 영어 중심 NER만으로는 충분하지 않다.",
  "3. 구현 산출물",
  "주요 구현 산출물은 `korean_pii_guardrail_v0_2` 패키지이다. `src/pii_guardrail/preprocess.py`는 offset-safe normalization과 탐지용 variant를 담당하고, `regex_detectors.py`와 `validators.py`는 구조형 식별자를 탐지·검증한다. `korean_boundary.py`는 한국어 suffix를 보정하고, `context_scorer.py`는 field label, co-occurrence, negative context를 반영한다. `span_resolver.py`는 겹침·중복 span을 정리하고, `policy.py`와 `masker.py`는 목적별 action과 label mask/hash/block을 수행한다. `audit_logger.py`는 원문 PII 없이 추적 가능한 감사 이벤트를 만든다.",
  "4. 평가 산출물",
  "평가는 두 축으로 수행했다. 첫째, legacy 연구 스택에서는 10,000건 stratified payload를 사용해 Baseline, LLM judge, Layer 0, Full stack을 비교했다. 둘째, v0.2 패키지에서는 5,000건 release gate를 통해 정확도, boundary, high-risk recall, raw logging safety, invalid offset count를 검증했다. 특히 raw PII logging count와 invalid offset count가 모두 0이라는 점은 보안 모듈로서 중요한 수용 기준이다.",
  "5. 핵심 성과",
  "legacy 10k 평가에서 Layer 0 포함 구성은 전체 TRUE detection 94.32%, KR_semantic TRUE detection 96.39%를 기록했다. v0.2 release gate에서는 actionable precision 0.9975, actionable F1 0.9457, high-risk structured recall 1.0000, josa boundary accuracy 0.9989를 기록했다. 이는 한국어 특화 deterministic 계층이 LLM judge의 보조 또는 대체 방어선으로 실질적 가치가 있음을 보여준다.",
  "6. 보안·윤리 고려",
  "평가 데이터는 synthetic fixture 또는 공개·비식별 자료 기반으로 구성했고, raw production PII는 사용하지 않았다. 시스템 설계상 public response와 audit event에는 raw span text가 들어가지 않는다. 오류 분석과 평가 리포트에도 raw PII를 남기지 않고 hash, span length, entity type, reason code 중심으로 기록한다.",
  "7. 한계와 향후 개선",
  "현재 v0.2는 단일 입력 텍스트 기준으로 동작하므로 RAG 문서 전체 스캔, 멀티턴 조각 결합, 세션 기반 누적 위험도는 다루지 않는다. PERSON_NAME NER recall/precision, 주소 상세도 분류, real NER latency 계측, custom identifier profile, 도메인별 정책 profile은 후속 개선 대상이다. 또한 실제 운영 로그와 유사한 정상 corpus를 더 확보해 오탐 유형을 세밀하게 분석할 필요가 있다.",
  "8. 결론",
  "본 프로젝트는 한국어 LLM 보안에서 영어 중심 가드레일의 한계를 정량적으로 확인하고, 이를 보완하는 한국어 특화 개인정보 가드레일을 구현했다. 결과물은 단순 데모가 아니라 패키지, API, 웹 콘솔, 평가 harness, 문서, release gate를 갖춘 재현 가능한 소프트웨어 산출물이며, 개인정보 유출 방지와 보안 거버넌스 관점에서 활용 가능성이 높다."
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

function appendDetailReport(doc) {
  const paragraphs = ["", ...appendix];
  const start = doc.getParagraphCount(section);
  for (let index = 0; index < paragraphs.length; index += 1) {
    const tail = doc.getParagraphCount(section) - 1;
    parseResult(doc.insertParagraph(section, tail), `insertParagraph ${start + index}`);
  }
  for (let index = 0; index < paragraphs.length; index += 1) {
    replaceBodyParagraph(doc, start + index, paragraphs[index]);
  }
}

function buildMarkdown() {
  const figureLines = figures.map((figure, index) => `${index + 1}. ${figure.description}: ${figure.path}\n   ${figure.caption}`);
  return [
    "# 캡스톤디자인 결과보고서 작성본",
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
    ...purpose,
    "",
    "## 2. 작품 제작 과정",
    "",
    ...process,
    "",
    "## 3. 작품개념, 구성 및 상세내용",
    "",
    ...concept,
    "",
    "## 4. 기대효과 및 활용방안",
    "",
    ...effects,
    "",
    "## 5. 결과물 사진",
    "",
    ...figureLines,
    "",
    "## 6. 지도교수 종합평가",
    "",
    ...professorEval,
    "",
    ...appendix
  ].join("\n\n");
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
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
    setCellParagraphs(doc, 1, 22, purpose);
    setCellParagraphs(doc, 1, 24, process);

    setCellParagraphs(doc, 2, 1, concept);
    setCellParagraphs(doc, 2, 3, effects);

    for (const figure of figures) {
      insertFigure(doc, figure);
    }

    setCellParagraphs(doc, 7, 1, professorEval);
    setCellParagraphs(doc, 7, 2, submission);

    appendDetailReport(doc);

    rhwp.writeHwp(doc, outputPath);
  } finally {
    doc.free();
  }

  fs.writeFileSync(markdownPath, buildMarkdown(), "utf8");

  const info = await rhwp.getDocumentInfo(outputPath);
  console.log(JSON.stringify({ outputPath, markdownPath, info }, null, 2));
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : err);
  process.exit(1);
});
