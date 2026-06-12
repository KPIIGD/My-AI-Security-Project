# 한국어 PII 가드레일 프로젝트 — 컨텍스트 요약 v2

> **목적**: 다른 AI/검토자가 이 문서만 읽으면 프로젝트 전체 맥락과 결정사항을 파악할 수 있도록 정리한 문서.
> **버전**: 2026.5 v2 (직전 v1: 2026.5 / 변경 이력은 문서 끝)

---

## 1. 프로젝트 개요

### 1.1 최종 목표
**한국어 PII/민감정보 비식별화에 특화된 단일 통합 가드레일 — L0 결정론 엔진 + KLUE-RoBERTa NER + Tier 4 문맥 룰 결합형**

- **L0 결정론 엔진** = 13단계 정규화 + 정규식 42개 + 키워드 사전 22카테고리 (→27 강화)
- **NER 보완 모듈** = KLUE-RoBERTa-base 사전학습 체크포인트 inference-only (NAME/ADDRESS/ORG/TITLE/DEPT)
- **Tier 4 문맥 룰** = quasi-identifier 3-slot 조합 (재식별 위험 플래그)
- **Span Ledger 아키텍처** = 4 detector 결과를 placeholder 치환 없이 (start, end, type) 메타로 통합

> **표현 주의**: "단일 통합 가드레일" framing 가능. "단독 완전 보호 엔진"이라는 표현은 금지 — L0 단독 overall 31%로 standalone 주장 부족.

### 1.2 입력 모달리티 (텍스트 + 문서)
```
[텍스트] ──────────────────┐
[문서]   ──PDF/XLSX/CSV───┼──→ [통합 텍스트] ──→ [한국어 PII 가드레일] ──→ [비식별 결과]
```

- **문서 (W5 어댑터)**:
  - PDF 본문: PyMuPDF
  - PDF 표: pdfplumber
  - XLSX: openpyxl (행 단위 concat → NER, 별도 dict로 quasi-id 판정)
  - CSV: pandas
- **음성 STT**: ❌ 범위 외, 향후 과제 (Whisper 명칭 불명확, STT 노이즈 검증 부담, F1 수치 오염 위험)
- **HWP / OCR (Tesseract) / Layout 시각 복원**: ❌ 범위 외, 향후 과제

### 1.3 핵심 성과 (실측 완료, 2026-04 기준)
| 지표 | 값 |
|---|---|
| KR_semantic 탐지율 (L0+5계층) | **96.4%** |
| GPT-4o-mini judge baseline | 87.4% (p<1e-28로 능가) |
| 비용 (10k req) | **$0.08** vs GPT-4o judge $1.35 (**17배 절감**) |
| L0 단독 overall | 31% |
| L0 단독 KR_semantic | 80.65% |

### 1.4 차별화 포인트
1. **한국어 정규화 깊이**: 자모 분해 + 동형문자 + 야민정음 + 코드스위칭 — 13단계 결정론
2. **카테고리별 차등 framing**:
   - Tier 1 (RRN/PHONE/CARD/EMAIL) → L0가 standalone 1차 detector
   - NAME/ADDRESS/ORG → NER 보강 필요
3. **Span Ledger 아키텍처**: placeholder 치환 없이 (start, end, type) 메타로 detector 결과 통합

---

## 2. 시스템 아키텍처

### 2.1 4-detector 단일 가드레일
```
입력 텍스트 (또는 문서 어댑터 → 텍스트)
   ↓
[L0: 13단계 정규화]   (자모/동형문자/야민정음/공백 등 결정론)
   ↓
[Detector 4종 병렬 적용]
 ├─ ① 정규식 42→60 → Tier 1 정형 PII (RRN/PHONE/EMAIL/CARD/JWT/세션)
 ├─ ② 사전 22→27   → Tier 2/3 텍스트형 PII (병명/처방/회사/학교 + salary/debt/family/location/job-title)
 ├─ ③ NER inference → 문맥 의존 PII (NAME/ADDRESS/ORG/TITLE/DEPT)
 └─ ④ Tier 4 룰    → quasi-id 3-slot 재식별 risk_flag
   ↓
[Span Ledger 통합]   (우선순위 · merge · tie-break)
   ↓
[비식별 출력 + risk_flag 메타]
```

### 2.2 NER 모듈 — Inference-only 보완
- **모델**: `klue/roberta-base` (110M)
- **방식**: full fine-tune ❌. KLUE-NER 사전학습 체크포인트 그대로 사용 + KLUE-NER 라벨(PER/LOC/ORG) → PII 라벨 매핑 룰 + 후처리
- **이유**: 6주 일정에 라벨 검수 + 풀학습 비현실. inference-only로 통합·데모·오류분석 산출물 확보
- **DISEASE / TITLE / DEPT**: KLUE-NER에 없는 라벨 → 사전 기반 분리 처리
- **성능 주장 제한**: 외부 평가셋(KLUE-NER test + KoJailFuzz)으로 측정 전엔 standalone 주장 금지

### 2.3 Span Ledger 아키텍처 ★ 신규
- L1 정규식이 PII를 `[PHONE]`·`[RRN]` 등으로 치환하지 **않음**
- 대신 (start, end, type, confidence) 메타만 ledger에 적재
- L2 NER엔 **원문 그대로** 입력 → BPE OOV 토큰 노이즈 회피, train-test mismatch 차단
- 후처리에서 detector별 ledger merge — 우선순위: **정규식 > NER > 사전 > Tier 4 룰**
- 충돌 시: span 겹치면 confidence 높은 쪽 채택, tie-break는 detector 우선순위

### 2.4 Tier 4 quasi-identifier 룰 ★ 신규
- **3-slot 조합**: `가족/본인 + 질환 + 지역/나이/직장` 동시 발화 시 risk_flag 활성화
- **2-slot 금지** (예: "엄마 + 당뇨"는 일반 대화 FP 너무 많음)
- 출력은 risk_flag만 (mask 금지)
- **검증**: N≥1,000 negative에서 FPR<5% 미달 시 자동 비활성화 스크립트 (n=1000일 때 95% CI ±1.35%p)

---

## 3. 제약사항 (현실 점검)

| 항목 | 상태 |
|---|---|
| GPU | Colab Free/Pro (T4/V100) |
| PII 라벨링 데이터 | **미정 (1번 리스크)** — 라벨 가이드 1페이지 W1 첫 작업으로 선행 |
| 평가 메트릭 | span-exact entity-F1 per category + macro-F1 + Tier 1 recall + parse coverage 분리 |
| 캡스톤 마감 | 6주 |
| 기존 자산 | LiteLLM 5계층 PoC, korean_pii_detector.py (정규식 42 + 사전 22), KoJailFuzz |

---

## 4. 데이터 확보 전략

### Stage 0: 라벨 가이드 1페이지 (W1 첫 작업) ★ 선행
- NAME 경계 (직책 포함? 별명? 회사 직급은?)
- ADDRESS 단위 (행정구역? 우편번호? 동/호?)
- ORG vs DEPT 분리 기준
- DISEASE 분류 (진단명만? 처방약 포함?)
- → BIO 라벨 **5-7개로 통폐합** 결정

### Stage 1: 합성 데이터 (1주)
- Faker-ko (`pip install faker`) — 한국어 PII 합성 1만 건
- KoJailFuzz 변이 20~30%를 학습 augmentation으로 포함
- **문서 단위 8:1:1 분할 후 augmentation 적용** (data leakage 방지)

### Stage 2: KLUE-NER 재라벨링 (1주)
- PER → NAME, LOC → ADDRESS, ORG → ORGANIZATION
- DISEASE/TITLE/DEPT는 사전 기반 분리

### Stage 3: AI Hub 추가 (선택, 시간 부족 시 스킵)

### Stage 4: 외부 평가셋 (필수) ★ 추가
- **KLUE-NER test split** — domain leakage 검증
- **KoJailFuzz 14종** — 적대적 견고성 평가
- 자체 데이터로만 평가 시 over-optimistic 위험 (96.4% 한 방에 무너질 가능성)

---

## 5. PII 카테고리 (라벨 스키마 통폐합)

원래 17개 BIO 태그 → **5-7개로 통폐합** (W1 라벨 가이드에서 확정)

```python
labels = [
    "O",
    "B-NAME", "I-NAME",
    "B-ADDRESS", "I-ADDRESS",
    "B-ORG", "I-ORG",
    "B-TITLE", "I-TITLE",        # 직책+직급
    "B-DEPT", "I-DEPT",          # 부서
    "B-DISEASE", "I-DISEASE",    # 진단/처방 (사전 기반 보조)
    "B-CONTACT", "I-CONTACT",    # 정규식 후처리용 통합 라벨
]
```

### 법령 기반 분류 Tier (개인정보보호법)
- **Tier 1 (고유식별정보, 제24조)**: 주민번호, 여권, 운전면허, 외국인등록 → **정규식 전담**
- **Tier 2 (민감정보, 제23조)**: 건강·의료(DISEASE), 종교, 성적지향, 정치 → **사전 + NER**
- **Tier 3 (일반 PII)**: 이름, 전화, 이메일, 주소, 카드, 생년월일 → **정규식 + NER**
- **Tier 4 (준식별자)**: 가족 + 질환 + 지역/나이/직장 등 3-slot 조합 → **Tier 4 룰 전담**

---

## 6. NER 추론 설정 (Inference-only)

```python
from transformers import AutoTokenizer, AutoModelForTokenClassification

# 사전학습된 KLUE-NER 체크포인트 로드, 추가 학습 X
model = AutoModelForTokenClassification.from_pretrained("klue/roberta-base")
tokenizer = AutoTokenizer.from_pretrained("klue/roberta-base")

# KLUE-NER 라벨 → PII 라벨 매핑 룰 (후처리)
NER_TO_PII = {
    "PER": "NAME",
    "LOC": "ADDRESS",
    "OG":  "ORG",
    # DISEASE/TITLE/DEPT는 사전 기반 분리
}
```

**예상 시간**: inference-only라 학습 시간 0. 라벨 매핑 룰 + 후처리 작성 1주.

---

## 7. 6주 마일스톤

| 주차 | 작업 | 산출물 |
|---|---|---|
| **W1** | 라벨 가이드 + 합성 데이터 | 1페이지 라벨 가이드 + Faker-ko 1만 건 + 8:1:1 분할 |
| **W2** | KLUE-NER 재라벨링 + 외부 평가셋 준비 | KLUE-NER test split, KoJailFuzz 14종 |
| **W3** | NER inference + Tier 4 룰 | KLUE-RoBERTa 추론 + PII 매핑 룰 + Tier 4 3-slot |
| **W4** | Span Ledger 통합 + L0 강화 | 4 detector merge + 정규식 (42→60) + 사전 (22→27) |
| **W5** | 문서 어댑터 | PDF + XLSX + CSV (HWP/OCR 향후 과제로 명시) |
| **W6** | 평가 + 발표 | span-F1 / KoJailFuzz 유지율 / latency / parse coverage / Tier 4 FPR |

### 범위 외 (향후 과제)
- 음성 STT (Whisper, Naver Clova, Google STT)
- HWP 파싱 (pyhwp/pyhwpx 안정성 부족)
- OCR (Tesseract, PaddleOCR — 이미지 PDF)
- Layout 시각 복원

---

## 8. 평가 계획

### 평가 메트릭 (4종)
1. **탐지 정확도**: span-exact entity-F1 per category + macro-F1 + Tier 1 recall (micro-F1 단독 금지)
2. **적대적 견고성**: KoJailFuzz 14종 적용 시 F1 유지율
3. **추론 속도**: latency p50/p95 ms (T4 기준)
4. **파싱 커버리지** (문서): parse coverage % vs PII F1 분리 보고

### 비교 baseline
- Microsoft Presidio (영어 중심, 한국어 약함)
- 자체 정규식 단독 baseline
- KLUE-RoBERTa-base inference-only 단독 (룰 없이)
- 데이타스 UDmaster (공개 정보 정성 비교 — 부차)

### 외부 평가셋 ★ 필수
- **KLUE-NER test split** — domain leakage 검증
- **KoJailFuzz 14종** — 옵션: 8종 학습 / 6종 unseen test split (unseen variant generalization 주장 가능 시)

---

## 9. 캡스톤 발표 프레이밍

> "본 시스템은 한국어 PII 탐지에 특화된 **단일 통합 가드레일**이다.
>
> ① **결정론 엔진(L0)**: 13단계 정규화 + 정규식 42 + 사전 22→27 — KR_semantic **96.4%**, 단독 80.65%, p<1e-28로 GPT-4o-mini judge(87.4%) 능가
>
> ② **NER 보완 모듈**: KLUE-RoBERTa-base inference-only — NAME/ADDRESS/ORG/TITLE/DEPT 문맥 PII 보강
>
> ③ **Tier 4 룰**: 3-slot 재식별 quasi-identifier 조합 (FPR<5% 검증)
>
> ④ **Span Ledger**: placeholder 치환 없이 detector별 (start, end, type) 메타로 통합
>
> ⑤ **비용/속도**: $0.08/10k vs GPT-4o judge $1.35/10k (**17배 절감**), latency p95 XX ms
>
> ⑥ **적대적 견고성**: KoJailFuzz 14종 변이에 F1 X% 유지"

---

## 10. 법적/특허 고려사항

### 참고 법령
- **개인정보보호법** 제2조(정의), 제23조(민감정보), 제24조(고유식별정보), 제24조의2(주민번호)
- **시행령** 제18조(민감정보 범위), 제19조(고유식별정보 범위)
- **가명정보 처리 가이드라인 2026.3 개정판** (개인정보보호위원회)
  - 본권 PART 3 비정형데이터 가명처리 기준
  - 별권 PART 4 가명처리 기술·기법
  - 별권 PART 7 한국어 대화형 AI 챗봇 시나리오 ⭐

### 특허 회피 (데이타스)
- **등록**: "가명정보 처리 및 재식별 가능성 평가 시스템" (2022.2, PAmaster용) — 정형 데이터 위험도 측정 위주, 직접 충돌 X
- **출원 중**: "AI 문맥 기반 / 단어 관계도 기반 개인정보 추출" (UDmaster) — 단어관계도 기법 회피 필요
- **회피 전략**: 단어관계도 X / KoBERT 임베딩 유사도 X / 한국어 적대적 변이 정규화 O / Span Ledger 룰 기반 통합 O
- **학사 캡스톤은 특허법 제96조 연구·시험 면책** (상용화/오픈소스 공개 시 별도 검토)

---

## 11. 다음 액션 (우선순위 순)

1. ⭐ **W1 첫날: 라벨 가이드 1페이지** (NAME/ADDRESS/ORG 경계, BIO 태그 5-7개 확정)
2. Faker-ko 합성 1만 건 (라벨 가이드 따라 + KoJailFuzz augmentation 20~30%)
3. KLUE-NER 재라벨링 + 외부 평가셋 준비
4. KLUE-RoBERTa-base inference + PII 매핑 룰 + Tier 4 3-slot 룰
5. Span Ledger 통합 + 정규식 강화 (42→60) + 사전 강화 (22→27)
6. PDF/XLSX/CSV 어댑터
7. KoJailFuzz 14종 평가 + 발표 자료 + parse coverage / FPR 분리 메트릭

---

## 12. 핵심 원칙

- ❌ 모델 비교에 시간 낭비 X — KLUE-RoBERTa-base inference-only로 시작
- ❌ NER full fine-tune 욕심 X — inference-only로 6주 일정 보호
- ❌ 음성 STT 욕심 X — 범위 외, 향후 과제
- ❌ HWP / OCR 욕심 X — PDF/XLSX/CSV에 집중
- ❌ "4-detector" 마케팅 숫자 부풀리기 X — 실제 신규는 NER + Tier 4 두 개, 정규식·사전은 L0 feature 확장
- ❌ "단독 완전 보호 엔진" 표현 X — L0 단독 overall 31%
- ✅ **라벨 가이드 1페이지가 데이터 합성보다 먼저** (W1 첫 작업)
- ✅ **외부 평가셋 필수** — KLUE-NER test + KoJailFuzz, domain leakage 차단
- ✅ **Span Ledger 선행** — detector 충돌 룰 명세 없으면 F1 산식 흔들림
- ✅ **카테고리별 차등 framing** — Tier 1 standalone / NAME/ADDRESS 보강
- ✅ **단일 통합 가드레일** framing 가능 (단, 단독 완전 보호 엔진은 금지)
- ✅ "단일 모델 1개"가 아니라 "단일 시스템" — 룰 + inference-only NER + Tier 4 룰 조합

---

**문서 버전**: 2026.5 v2 / **작성**: 캡스톤 PII 탐지 담당자 / **검토 의뢰용**

### v1 → v2 변경 이력 (2026-05-06)

다중 AI 토론(Claude Opus 4.7 + GPT-5.5 + Gemini 2.5-pro, 5 라운드 ×4 회) 결과 반영:

- **명칭 정정**: "단일 통합 엔진" → "L0 결정론 + NER + Tier 4 단일 통합 가드레일" (실제 구조 일치)
- **실측 수치 반영**: 96.4%, 87.4%, p<1e-28, $0.08 vs $1.35/10k 등
- **자산 갱신**: 정규식 17→42, 사전 16→22(→27)
- **신규 추가**: Span Ledger 아키텍처, Tier 4 3-slot 룰
- **라벨 스키마**: 17개 → 5-7개 통폐합 (W1 라벨 가이드 선행)
- **외부 평가셋 필수화**: KLUE-NER test, KoJailFuzz
- **NER 모드**: full fine-tune → inference-only
- **음성 STT 완전 제외**: 범위 외, 향후 과제
- **문서 어댑터 명확화**: PDF + XLSX + CSV (HWP/OCR 향후 과제)
- **카테고리별 차등 framing**: Tier 1 standalone / NAME/ADDRESS 보강
- **금지 표현**: "단독 완전 보호 엔진"
