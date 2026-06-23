"use strict";

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

const inputPath =
  "C:/Users/andyw/Desktop/최종본수정함한국융합보안학회 하계학술대회 논문 양유상(2026).hwp";
const outputPath =
  "C:/Users/andyw/Desktop/최종본재실험반영한국융합보안학회 하계학술대회 논문 양유상(2026).hwp";

const section = 0;

const replacements = new Map([
  [
    35,
    "B와 C의 paired 비교에서 McNemar p-value는 2.04e-28로 나타나 차이가 우연으로 보기 어렵다. 초기 clean-pass 50건에서는 1건(2.0%)의 false positive가 관찰되었으나, 추가로 생성한 정상 한국어 corpus 10,000건에 대해 Layer 0를 재평가한 결과 false positive는 0건(0.0%), clean-pass rate는 100.0%였다. 다만 해당 corpus 역시 synthetic 정상 문장으로 구성되어 실제 상담·민원·의료·금융 환경의 전체 오탐률을 대표하지는 않으므로, 향후 비식별 정상 corpus 확장을 통한 오탐 유형 분석이 필요하다. 한편 ablation에서 KR_semantic 기준 정규화 단독 gain은 0.31%p로 제한적이므로, 본 연구의 주장은 “정규화 단독의 성능 향상”이 아니라 “정규화-우선 구조가 한국어 PII 사전/패턴 탐지를 유효하게 만든다”는 것이다."
  ],
  [
    37,
    "D(L0-L4)가 가장 높은 탐지율을 보인 점은 Layer 0와 L4 judge가 경쟁 관계가 아니라 상호보완 관계임을 보여준다. 실운영에서는 Layer 0를 기본 방어선으로 두고, Layer 0-L3에서 확정 판정이 나지 않은 고위험·불확실 케이스에만 L4 judge를 호출하는 Smart Skip 구성이 적합하다. 이 정책은 detection impact 없이 L4 호출을 94.32% 줄일 수 있어 비용과 지연을 함께 낮춘다."
  ],
  [
    38,
    "제안 방식은 특정 LLM이나 외부 API에 종속되지 않아 고객상담, 의료, 금융, 교육, 공공 민원처럼 한국어 자유문 입력이 들어오는 서비스에 적용할 수 있다. 다만 본 연구의 10k stratified payload와 10k clean corpus는 synthetic set이므로 실제 운영 로그의 문장 길이, 도메인 은어, 복합 개인정보 표현, 오탐 분포를 완전히 대표하지 않는다. 외부 관리형 guardrail과 LLM judge는 네트워크·API 설정·모델 버전에 따라 재현성 차이가 날 수 있으며, 실제 배포 시에는 도메인 사전 버전 관리와 정기 회귀 테스트가 필요하다."
  ],
  [39, ""],
  [40, ""],
  [41, ""],
  [42, ""]
]);

function parseResult(raw, op) {
  const parsed = JSON.parse(raw);
  if (!parsed || parsed.ok !== true) {
    throw new Error(`${op} failed: ${raw}`);
  }
  return parsed;
}

function setParagraphText(doc, paragraph, text) {
  const length = doc.getParagraphLength(section, paragraph);
  if (length > 0) {
    parseResult(doc.deleteText(section, paragraph, 0, length), `deleteText ${paragraph}`);
  }
  if (text) {
    parseResult(doc.insertText(section, paragraph, 0, text), `insertText ${paragraph}`);
  }
}

async function main() {
  const doc = await rhwp.loadDocument(inputPath);
  try {
    for (const [paragraph, text] of replacements) {
      setParagraphText(doc, paragraph, text);
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
