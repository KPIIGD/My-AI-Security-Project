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
const projectRoot = path.join(repoRoot, "korean_pii_guardrail_v0_2");
const templatePath = "C:/Users/andyw/Desktop/캡스톤디자인_결과보고서 양식_정보보호학전공.hwp";
const outputDir = path.join(repoRoot, "output/doc");
const outputPath = path.join(outputDir, "캡스톤디자인_결과보고서_한국어PII가드레일_통합본.hwp");
const markdownPath = path.join(outputDir, "캡스톤디자인_결과보고서_한국어PII가드레일_통합본.md");
const section = 0;

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function fixed(value, digits = 4) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "확인 필요";
  }
  return value.toFixed(digits);
}

const releaseGate = readJson(path.join(projectRoot, "reports/release_gate_v0_2.json"));
const metrics = {
  records: releaseGate.records_processed,
  overallPrecision: fixed(releaseGate.overall_precision),
  overallRecall: fixed(releaseGate.overall_recall),
  overallF1: fixed(releaseGate.overall_f1),
  actionablePrecision: fixed(releaseGate.actionable_overall_precision),
  actionableRecall: fixed(releaseGate.actionable_overall_recall),
  actionableF1: fixed(releaseGate.actionable_overall_f1),
  highRiskRecall: fixed(releaseGate.high_risk_recall),
  actionableHighRiskRecall: fixed(releaseGate.actionable_high_risk_recall),
  deterministicP95: fixed(releaseGate.deterministic_latency_ms?.p95, 1),
  deterministicP99: fixed(releaseGate.deterministic_latency_ms?.p99, 1),
  rawLogging: releaseGate.raw_pii_logging_count,
  invalidOffsets: releaseGate.invalid_offset_count,
  releaseStatus: releaseGate.release_gate?.overall_status || "확인 필요",
  generatedAt: releaseGate.generated_at || "확인 필요"
};

const form = {
  major: "정보보호학전공",
  professor: "임정묵",
  courseCode: "확인 필요",
  courseName: "캡스톤디자인",
  taskType: "□ 전공융합형  ■ 전공심화형  □ 창업연계형  □ 사회기여형",
  outputType: "□ 시작품제작과제  ■ 소프트웨어개발과제  □ 기타(연구·평가 산출물)",
  projectName: "한국어 개인정보 탐지 및 비식별화 LLM Gateway 가드레일 설계와 구현",
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
    caption: "내용 : 사용자 입력이 LLM으로 전달되기 전에 한국어 정규화, 개인정보 후보 탐지, 문맥 점수화, 정책 기반 마스킹을 거치는 전체 흐름."
  },
  {
    cell: 2,
    captionCell: 4,
    path: path.join(repoRoot, "PII/results/figures/fig11_kr_semantic_4way.png"),
    width: 22000,
    height: 14500,
    description: "한국어 의미형 PII 성능 비교",
    caption: "내용 : 한국어 의미형 개인정보 구간에서 Layer 0 포함 구성이 LLM judge 구성보다 높은 탐지율을 보인 평가 그래프."
  },
  {
    cell: 5,
    captionCell: 7,
    path: path.join(repoRoot, "PII/results/figures/fig13_ablation.png"),
    width: 22000,
    height: 14500,
    description: "Layer 0 ablation 결과",
    caption: "내용 : 정규화, 사전, 탐지 규칙의 기여도를 나누어 분석한 결과. 한국어 사전과 패턴 탐지가 핵심 개선 요인임을 보여준다."
  },
  {
    cell: 6,
    captionCell: 8,
    path: path.join(repoRoot, "PII/results/figures/fig10_4way_bypass.png"),
    width: 22000,
    height: 14500,
    description: "4-way 우회율 비교",
    caption: "내용 : Baseline, LLM judge, Layer 0, Full stack의 누출 차단 효과를 비교한 그래프."
  }
];

const purpose = [
  "본 과제는 생성형 AI 서비스에서 한국어 개인정보가 외부 LLM, 모델 출력, 운영 로그, 감사 데이터로 흘러가는 위험을 줄이기 위해 수행한 보안 소프트웨어 개발 과제이다. LLM은 사용자의 질문을 외부 모델 API로 보내 답변을 받는 구조가 많기 때문에, 질문 안에 개인정보가 섞이면 모델 호출 이전 단계에서 먼저 걸러야 한다.",
  "기존 상용 가드레일은 전화번호, 이메일, 주민등록번호처럼 형식이 뚜렷한 정보에는 비교적 강하지만, 한국어 문장 속 이름, 주소, 학교, 병원, 가족관계, 의료기록번호, 조직명처럼 문맥으로 판단해야 하는 개인정보에는 약점이 있다. 또한 한국어는 조사와 어미가 붙고, 자모 분해, 초성 표기, 전각 숫자, zero-width 문자 삽입처럼 표면형을 바꾸는 방식으로 탐지를 우회할 수 있다.",
  "따라서 본 프로젝트의 목적은 한국어 입력을 LLM에 보내기 전에 개인정보 후보를 탐지하고, 정책에 따라 마스킹, 해시, 차단을 수행하는 가드레일을 구현하는 것이다. 단순 정규식 모음이 아니라 원문 위치 보존, 한국어 조사 분리, 변이형 표현 복원, 문맥 점수화, 중복 span 정리, raw PII 없는 감사로그까지 포함한 end-to-end 파이프라인을 목표로 했다.",
  "평가자가 AI 보안이나 개인정보 탐지에 익숙하지 않더라도 이해할 수 있도록 요약하면, 이 작품은 '한국어 문장 안의 개인정보를 찾아 LLM으로 넘어가기 전에 안전한 표시로 바꾸는 필터'이다. 예를 들어 실제 이름이나 연락처를 그대로 보내지 않고, 의미를 알 수 있는 `[PERSON_1]`, `[PHONE_1]` 같은 라벨로 바꾼다.",
  `최종 구현물은 Python 패키지, FastAPI 기반 API 서비스, React/Vite 웹 콘솔, 설정 파일, JSON Schema, 평가 하네스, release gate 리포트로 구성된다. 2026-05-25 기준 v0.2 release gate는 synthetic fixture ${metrics.records}건에서 ${metrics.releaseStatus} 상태이며, raw PII logging count ${metrics.rawLogging}건, invalid offset count ${metrics.invalidOffsets}건을 기록했다.`
];

const process = [
  "1단계에서는 문제를 정의했다. 생성형 AI 서비스에서 개인정보가 유출되는 지점은 사용자 입력, LLM 호출, 모델 응답, 운영 로그로 나뉜다. 특히 LLM Gateway는 여러 모델 호출이 집중되는 통제 지점이므로, 여기서 사전 탐지와 비식별화를 수행하는 것이 실무적으로 효과적이라고 판단했다.",
  "2단계에서는 기존 연구 스택을 통해 한국어 가드레일의 취약성을 분석했다. LiteLLM Gateway 환경에 Presidio, AWS Bedrock Guardrails, Lakera Guard, GPT-4o-mini judge를 결합하고, 한국어 PII 퍼저로 만든 10,000건 stratified payload를 사용해 Baseline, LLM judge, Layer 0, Full stack을 비교했다.",
  "3단계에서는 한국어 특화 Layer 0를 설계했다. Layer 0는 LLM 호출 없이 로컬에서 동작하는 결정론적 계층이다. Unicode/NFKC 정규화, zero-width 제거, 자모 결합, 초성 복원, 한글 숫자 처리 같은 전처리와 한국어 PII 사전, 정규식, validator를 결합해 개인정보 후보를 만든다.",
  "4단계에서는 연구용 코드를 제품형 v0.2 single-turn core로 정리했다. RAG 문서 스캔, 멀티턴 세션 추적, fragment ledger, human review dashboard는 v0.2 범위에서 제외하고, 하나의 입력 텍스트 안에서 개인정보를 탐지, 보정, 판정, 마스킹하는 기능에 집중했다.",
  "5단계에서는 패키지를 모듈화했다. 주요 모듈은 `schema/enums`, `preprocess`, `regex_detectors`, `validators`, `korean_boundary`, `dictionary_loader`, `dictionary_detectors`, `context_scorer`, `span_resolver`, `policy`, `masker`, `audit_logger`, `pipeline`, `evaluation_harness`이다. 각 모듈은 테스트와 설정 파일에 맞추어 독립적으로 검증되도록 구성했다.",
  `6단계에서는 release gate로 품질을 확인했다. 최신 release gate는 ${metrics.records}건을 처리했고 overall precision/recall/F1은 ${metrics.overallPrecision}/${metrics.overallRecall}/${metrics.overallF1}, actionable precision/recall/F1은 ${metrics.actionablePrecision}/${metrics.actionableRecall}/${metrics.actionableF1}이다. high-risk recall은 ${metrics.highRiskRecall}, actionable high-risk recall은 ${metrics.actionableHighRiskRecall}이며, raw PII logging count와 invalid offset count는 모두 0이다.`
];

const concept = [
  "작품의 핵심 개념은 '한국어 LLM Gateway용 개인정보 가드레일'이다. 사용자가 입력한 텍스트 또는 모델이 출력한 텍스트를 검사해 개인정보 후보 span을 찾고, 한국어 문장 구조를 보존하면서 정책에 맞게 마스킹한다. 여기서 span은 텍스트 안에서 개인정보가 시작하고 끝나는 위치를 뜻한다.",
  "전체 흐름은 GuardrailRequest 입력, L0 Preprocessor, Candidate Detectors, Korean Boundary Corrector, Context Scorer, Span Resolver, Policy Router와 Masker, Audit Logger, GuardrailResponse로 이어진다. 각 detector는 후보만 만들고 최종 조치 여부는 뒤 단계에서 결정한다. 이 구조는 탐지기 하나가 과도하게 차단하거나, 반대로 위험한 정보를 통과시키는 문제를 줄인다.",
  "L0 Preprocessor는 원문을 덮어쓰지 않고 탐지용 variant를 만든다. 예를 들어 숫자 사이에 공백이 들어가거나, 한국어 키워드가 띄어쓰기나 자모 형태로 변형되어도 탐지 가능한 형태를 추가로 만든다. 다만 최종 개인정보 위치는 항상 원문 raw text 기준으로 복원해야 하며, 복원할 수 없는 후보는 버린다.",
  "Korean Boundary Corrector는 한국어의 조사와 어미를 다룬다. 한국어에서는 개인정보 뒤에 '이', '에게', '로', '입니다' 같은 말이 붙는다. 잘못 마스킹하면 문장이 어색해지고 위치도 틀어진다. 본 시스템은 개인정보 본체만 치환하고 suffix는 보존하도록 설계했다.",
  "Context Scorer는 문맥을 본다. 예를 들어 어떤 단어가 사람 이름처럼 보이더라도 주변에 '고객명', '연락처', '주소' 같은 라벨이 없으면 낮은 점수로 둔다. 반대로 같은 문장 안에 이름 후보와 전화번호 후보가 함께 있으면 조합 위험이 커지므로 점수를 올린다.",
  "Span Resolver는 여러 탐지기가 같은 부분을 중복 탐지하거나 겹치게 탐지한 경우 하나의 최종 결과로 정리한다. 예를 들어 이메일 내부 문자열이 사람 이름 후보처럼 잡혀도 EMAIL이 더 우선된다. 이런 결정론적 우선순위가 있어야 결과가 재현 가능하고 평가도 가능하다.",
  "Policy Router와 Masker는 최종 보호 조치를 선택한다. LLM 입력에는 label mask를 적용하고, 감사 로그에는 HMAC hash만 남기며, API key 같은 높은 위험 정보는 block할 수 있다. public response와 audit event에는 raw span text가 들어가지 않도록 설계했다.",
  `평가 결과는 구현 완성도를 보여준다. v0.2 release gate는 ${metrics.records}건 synthetic fixture에서 ${metrics.releaseStatus} 상태이며, deterministic latency는 p95 ${metrics.deterministicP95}ms, p99 ${metrics.deterministicP99}ms로 측정되었다. legacy 10,000건 비교에서는 Layer 0 포함 구성이 전체 TRUE detection 94.32%, 한국어 의미형 PII 96.39%를 기록해 LLM judge 중심 구성보다 높은 성능을 보였다.`
];

const effects = [
  "첫째, 한국어 LLM 서비스에서 개인정보 유출 가능성을 낮출 수 있다. 사용자 입력이 외부 모델 API로 전달되기 전에 로컬 가드레일이 먼저 검사하므로, 민감정보가 그대로 모델 또는 후속 시스템에 전달되는 위험을 줄인다.",
  "둘째, 비용과 지연을 줄일 수 있다. 모든 입력을 LLM judge에 보내면 호출 비용과 응답 지연이 커진다. 본 프로젝트의 핵심 계층은 규칙, 사전, validator, 문맥 점수 기반으로 동작하므로 기본 방어선으로 두고, 애매한 일부 케이스에만 LLM judge를 선택적으로 붙이는 방식으로 확장할 수 있다.",
  "셋째, 감사 가능성과 재현성이 높다. 같은 입력과 같은 설정이면 같은 결과가 나오고, 감사 로그에는 원문 개인정보 대신 entity type, score, action, reason code, span length, HMAC hash만 기록한다. 이는 보안 운영과 개인정보보호 컴플라이언스 모두에 중요하다.",
  "넷째, 적용 범위가 넓다. 고객상담 챗봇, 금융 상담, 의료 문진, 학교 행정, 공공 민원, 사내 업무 자동화처럼 한국어 자유문이 들어오는 서비스에 라이브러리, REST API, Gateway plugin, 배치 로그 마스킹 형태로 적용할 수 있다.",
  "다섯째, 후속 연구와 제품화 기반이 된다. 현재 산출물은 패키지, API, 웹 콘솔, 평가 하네스, 문서, release gate 리포트를 포함한다. 향후 실제 비식별 정상 corpus, 도메인별 사전, ONNX/INT8 NER 최적화, RAG와 멀티턴 확장으로 발전시킬 수 있다."
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

const appendix = [
  "상세 수행 내용",
  "1. 프로젝트 요약",
  "본 프로젝트는 한국어 LLM 서비스에서 개인정보가 외부 모델이나 로그로 넘어가기 전에 탐지하고 비식별화하는 보안 소프트웨어이다. 평가자가 기술 배경이 적더라도 쉽게 이해하면, 이 시스템은 한국어 문장 속 개인정보를 찾아 안전한 라벨로 바꾸는 필터이다.",
  "2. 배경과 문제 상황",
  "생성형 AI 서비스는 사용자의 질문을 LLM에 보내 답변을 받는다. 이때 사용자가 고객 상담 내용, 의료 상담 내용, 금융 문의, 학교 행정 문의처럼 개인정보가 섞인 문장을 입력하면 그 정보가 외부 모델, 운영 로그, 모니터링 시스템에 남을 수 있다. 개인정보 보호 관점에서는 LLM이 답변을 잘하는 것보다 먼저 개인정보가 외부로 나가지 않도록 막는 장치가 필요하다.",
  "기존 가드레일은 대체로 영어 중심이거나 숫자 형식 중심이다. 전화번호나 이메일처럼 모양이 일정한 정보는 잡기 쉽지만, 한국어 문장 안의 이름, 병원, 가족관계, 조직명, 학교, 주소, 의료기록번호처럼 문맥으로 판단해야 하는 정보는 놓치기 쉽다. 또한 한국어는 조사와 어미가 붙기 때문에 단순히 단어를 지우면 문장이 깨지고, 탐지 위치도 틀릴 수 있다.",
  "3. 핵심 용어 설명",
  "PII는 Personal Identifiable Information의 약자로, 개인을 직접 또는 간접적으로 식별할 수 있는 정보를 뜻한다. 본 프로젝트에서는 주민등록번호, 외국인등록번호, 전화번호, 이메일, 카드번호, 계좌번호, 여권번호, 운전면허번호, 주소, 이름, 학교, 병원, 조직, 의료기록번호, API key 등을 탐지 대상으로 다뤘다.",
  "LLM Gateway는 애플리케이션과 LLM 사이에 놓이는 중간 통제 지점이다. 여러 모델 호출을 한곳에서 관리하고, 비용과 보안 정책을 적용한다. 본 프로젝트의 가드레일은 이 Gateway 앞단 또는 내부에 붙어 LLM 호출 전에 개인정보를 검사한다.",
  "Guardrail은 안전장치라는 뜻이다. 여기서는 입력 또는 출력 텍스트를 검사해 위험한 정보를 통과시키지 않거나, 안전한 형태로 바꾸는 소프트웨어 모듈을 의미한다.",
  "4. 개발 범위",
  "v0.2의 범위는 단일 입력 텍스트이다. 즉, 한 번 들어온 문자열 안에서 개인정보 후보를 찾고 처리한다. RAG 문서 전체 스캔, 여러 대화 턴을 이어 붙여 개인정보를 추론하는 멀티턴 세션 추적, human review dashboard, full LLM judge는 v0.2 범위에서 제외했다. 이 결정은 구현 범위를 명확히 줄여 핵심 기능인 탐지, 보정, 정책, 마스킹, 평가를 안정화하기 위한 것이다.",
  "다만 같은 입력 텍스트 안에서 발생하는 조합 위험은 포함했다. 예를 들어 한 문장 안에 사람 이름 후보와 연락처 후보가 함께 있으면 단독 단어보다 위험도가 높아진다. 이런 경우 context scorer와 span resolver가 조합 위험을 반영한다.",
  "5. 시스템 구조",
  "첫 번째 단계는 전처리이다. 전처리는 텍스트를 영구적으로 바꾸는 것이 아니라 탐지기가 볼 수 있는 표현을 늘리는 단계이다. 전각 숫자, zero-width 문자, 하이픈 변형, 숫자 띄어쓰기, 한국어 키워드 띄어쓰기, 자모 분해, 초성 표기, 한글 숫자 같은 변형을 탐지 가능한 형태로 만든다.",
  "두 번째 단계는 후보 탐지이다. 구조가 있는 개인정보는 regex와 validator로 찾는다. 예를 들어 카드번호는 Luhn checksum, 사업자등록번호와 법인등록번호는 형식 및 문맥, 전화번호와 이메일은 국내 형식과 도메인 구조를 활용한다. 이름, 주소, 학교, 병원, 조직처럼 의미 판단이 필요한 정보는 사전, NER interface, 문맥 근거를 함께 사용한다.",
  "세 번째 단계는 한국어 boundary correction이다. 한국어에서는 개인정보 뒤에 조사나 어미가 붙는 경우가 많다. 시스템은 개인정보 본체와 suffix를 분리해 본체만 마스킹하고 suffix는 남긴다. 이렇게 해야 결과 문장이 자연스럽고, 원문 위치도 정확하게 유지된다.",
  "네 번째 단계는 문맥 점수화이다. 단어 하나만 보면 개인정보인지 아닌지 모호한 경우가 많다. 주변에 '성명', '고객명', '연락처', '주소', '계좌', '환자번호' 같은 라벨이 있으면 점수를 높이고, '예시', '테스트', '날씨', '대표번호' 같은 오탐 가능 문맥이 있으면 점수를 낮춘다.",
  "다섯 번째 단계는 span resolver이다. 여러 탐지기가 같은 구간을 잡거나 서로 겹치는 구간을 잡을 수 있다. resolver는 entity 우선순위와 점수를 기준으로 최종 span set을 만든다. 이메일 내부 문자열이 사람 이름처럼 잡히더라도 EMAIL을 우선하는 식이다.",
  "여섯 번째 단계는 정책과 마스킹이다. LLM에 전달할 입력은 label mask를 기본으로 하고, 감사 로그는 HMAC hash를 기본으로 한다. 높은 위험의 보안비밀은 block할 수 있다. 이 단계에서 public response와 audit event에 원문 개인정보가 들어가지 않도록 제한한다.",
  "6. 구현 산출물",
  "주요 코드 산출물은 `korean_pii_guardrail_v0_2/src/pii_guardrail` 패키지이다. `preprocess.py`는 원문 offset을 보존하는 정규화와 variant 생성을 담당한다. `regex_detectors.py`와 `validators.py`는 구조형 식별자를 찾고 검증한다. `korean_boundary.py`는 한국어 suffix를 분리한다. `context_scorer.py`는 문맥 근거를 계산한다.",
  "`span_resolver.py`는 중복과 겹침을 정리하고, `policy.py`와 `masker.py`는 최종 action과 치환 결과를 만든다. `audit_logger.py`는 원문 개인정보 없이 추적 가능한 이벤트를 기록한다. `pipeline.py`는 이 흐름을 하나로 연결한다.",
  "API 산출물로는 `api/openapi.yaml`, `schemas/*.schema.json`, `api_service`가 있다. 웹 콘솔 산출물로는 `web` 디렉터리의 React/Vite UI가 있다. 평가 산출물은 `reports/release_gate_v0_2.json`, `reports/eval_v0_2.json`, `reports/ablation_v0_2.json`, failure case report, audit safety report로 관리된다.",
  "7. 평가 방법",
  `평가는 두 종류로 수행했다. 첫째, 연구용 10,000건 4-way 비교에서는 기존 상용 가드레일 중심 Baseline, LLM judge 추가 구성, Layer 0 추가 구성, Full stack을 비교했다. 둘째, v0.2 패키지 release gate에서는 synthetic fixture ${metrics.records}건으로 정확도, 재현율, F1, 고위험 정보 재현율, 한국어 조사 경계 정확도, raw logging safety, invalid offset count를 확인했다.`,
  "평가에서 중요한 점은 단순히 '탐지기가 반응했는가'가 아니라 '실제 개인정보가 안전하게 처리되었는가'이다. 그래서 candidate-level metric과 actionable metric을 분리했다. candidate-level은 후보로 잡힌 span 전체를 보고, actionable metric은 실제 mask, hash, block으로 조치된 span만 본다.",
  "8. 주요 평가 결과",
  `v0.2 release gate 결과는 records processed ${metrics.records}, overall precision/recall/F1 ${metrics.overallPrecision}/${metrics.overallRecall}/${metrics.overallF1}, actionable precision/recall/F1 ${metrics.actionablePrecision}/${metrics.actionableRecall}/${metrics.actionableF1}이다. high-risk recall은 ${metrics.highRiskRecall}, actionable high-risk recall은 ${metrics.actionableHighRiskRecall}이다.`,
  `안전성 측면에서 raw PII logging count는 ${metrics.rawLogging}, invalid offset count는 ${metrics.invalidOffsets}이다. 이는 평가 리포트와 감사로그가 원문 개인정보를 저장하지 않도록 설계한 결과이며, 보안 과제에서 중요한 수용 기준이다.`,
  `운영 성능 측면에서 release gate의 deterministic latency는 p95 ${metrics.deterministicP95}ms, p99 ${metrics.deterministicP99}ms로 기록되었다. 단, release gate에는 real NER 경로가 포함되어 있어 deterministic-only CPU path SLA와는 분리해서 해석해야 한다.`,
  "legacy 10,000건 4-way 비교에서는 Baseline TRUE detection 80.15%, LLM judge 포함 90.96%, Layer 0 포함 94.32%, Full stack 97.23%가 보고되었다. 한국어 의미형 PII 구간에서는 Baseline 49.62%, LLM judge 87.40%, Layer 0 96.39%, Full stack 98.85%였다. 이 결과는 한국어 특화 deterministic 계층이 LLM judge보다 낮은 비용과 지연으로 강한 보강 효과를 낼 수 있음을 보여준다.",
  "9. 보안 및 윤리 고려",
  "본 프로젝트는 raw production PII를 사용하지 않는 것을 원칙으로 한다. 테스트와 평가는 synthetic fixture 또는 비식별 자료 기반으로 구성한다. 또한 public span, audit event, failure report, metric label에는 raw span text를 넣지 않는다. 오류 분석도 hash, span length, entity type, reason code 중심으로 수행한다.",
  "감사로그는 보안 운영에 필요하지만, 잘못 설계하면 또 다른 개인정보 저장소가 될 수 있다. 따라서 audit log에는 원문 값이 아니라 HMAC hash와 span length만 저장한다. HMAC key는 애플리케이션 설정과 분리해 관리하는 것이 원칙이며, 복원형 token mapping은 v0.2 기본 범위에서 제외했다.",
  "10. 사용자 관점 동작 예시",
  "사용자 입력에 이름 후보, 연락처 후보, 주소 후보가 함께 들어오면 시스템은 각 후보를 탐지하고, 문맥상 개인정보 가능성이 높은 경우 label mask를 적용한다. 결과는 실제 값 대신 `[PERSON_1]`, `[PHONE_1]`, `[ADDRESS_1]` 같은 라벨로 바뀐다. 이 라벨은 정보의 종류는 알려 주지만 실제 개인을 식별할 수 있는 값은 포함하지 않는다.",
  "감사로그에서는 같은 값이 반복되었는지 추적할 필요가 있을 수 있다. 이때 실제 값을 저장하지 않고 HMAC hash를 사용하면, 같은 값인지 비교할 수 있으면서도 원문 노출 위험을 줄일 수 있다.",
  "11. 한계",
  "첫째, v0.2는 단일 입력 텍스트만 다룬다. 여러 대화 턴에 나누어 입력된 조각을 합쳐 개인정보를 복원하는 공격은 v1 범위로 남겨 두었다. 둘째, PERSON_NAME NER 후보 품질과 ADDRESS granularity는 계속 개선이 필요하다. 셋째, real NER latency는 배포 방식에 따라 크게 달라질 수 있어 별도 계측이 필요하다.",
  "넷째, 고객번호, 사번, 학번 같은 custom identifier는 조직마다 형식이 다르다. 따라서 기본 detector가 임의로 추정 탐지하기보다, 실제 도입 조직이 pattern, validator, checksum을 profile로 명시하는 방식이 필요하다. 다섯째, 실제 운영 환경에 가까운 정상 corpus를 더 확보해 오탐 유형을 세밀하게 분석할 필요가 있다.",
  "12. 향후 개선 계획",
  "향후에는 실제 한국어 운영 로그와 유사한 clean corpus를 확보해 false positive를 더 정밀하게 낮출 계획이다. 또한 domain-specific dictionary, custom identifier profile, real NER calibration, ONNX 또는 INT8 기반 NER 최적화, RAG 문서 스캔, 멀티턴 fragment ledger를 단계적으로 검토할 수 있다.",
  "운영 제품화 관점에서는 FastAPI API를 Gateway plugin으로 쉽게 붙일 수 있는 배포 패키지, 관리자가 정책을 조정할 수 있는 설정 UI, release gate 자동 실행, audit safety report 자동 생성 기능을 추가하면 실무 적용성이 높아진다.",
  "13. 결론",
  "본 프로젝트는 한국어 LLM 보안에서 영어 중심 가드레일의 공백을 확인하고, 이를 보완하는 한국어 특화 개인정보 탐지 및 비식별화 가드레일을 구현했다. 결과물은 단순 아이디어가 아니라 코드, API, 웹 콘솔, 설정, 테스트, 평가 리포트, 문서를 포함한 재현 가능한 소프트웨어 산출물이다.",
  "특히 raw offset 보존, 한국어 suffix 보존, 문맥 점수화, span resolver, target별 policy, raw-free audit logging을 하나의 파이프라인으로 연결했다는 점에서 실무형 보안 과제로서 의미가 있다. 평가 결과도 release gate pass와 raw logging zero를 확인했으므로, 후속 보완을 거쳐 한국어 LLM Gateway 환경의 기본 개인정보 방어선으로 발전시킬 수 있다."
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
    "# 캡스톤디자인 결과보고서 상세본",
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
    `- release gate generated_at: ${metrics.generatedAt}`,
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
