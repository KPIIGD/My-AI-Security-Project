# Scope Change Note — RAG / Multi-Turn Exclusion

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 변경 결정

초기 자료에는 RAG scan, retrieval context scan, multi-turn session monitor가 포함되어 있었으나, 본 프로젝트의 v0.2 개발 범위에서는 두 개념을 제외한다.

## 2. 제외되는 기능

| 초기 개념 | v0.2 처리 |
|---|---|
| RAG context scan | 제외 |
| Retrieval document PII filter | 제외 |
| Multi-turn session monitor | 제외 |
| Fragment ledger | 제외 |
| Subject tracker | 제외 |
| 이전 턴 기반 combination risk | 제외 |
| metadata.session_id 연동 | 제외 |
| Redis TTL session store | 제외 |
| session leakage rate metric | 제외 |

## 3. 유지되는 기능

RAG와 멀티턴을 제외해도 다음 기능은 그대로 유지한다.

| 기능 | 유지 사유 |
|---|---|
| Input text scan | 기본 개인정보 유입 차단 |
| Output text scan | 모델 출력 또는 downstream 출력 검증 |
| Unicode/NFKC 정규화 및 offset map | 탐지 안정성 및 정확한 마스킹 위치 확보 |
| Regex/validator | 구조형 PII recall 확보 |
| Dictionary/NER 후보 생성 | 이름·주소·조직 등 의미형 PII 대응 |
| Boundary correction | 한국어 조사·호칭·어미 보존 |
| Context scorer | 같은 입력 텍스트 내부의 문맥 판단 |
| Span resolver | detector 결과 충돌 정리 |
| Masking policy | 목적별 비식별화 방식 선택 |
| Audit logger | raw PII 없이 추적성 확보 |
| Evaluation harness | release gate 및 ablation 검증 |

## 4. 조합 위험의 범위 재정의

v0.2에서 combination risk는 **단일 입력 텍스트 내부**로 제한한다.

허용되는 예:

```text
고객명 하늘, 연락처 010-1111-2222입니다.
```

- `하늘` 단독이면 중의적이므로 낮은 score
- 같은 문장 또는 같은 필드 블록 안에 연락처 label과 전화번호가 존재하므로 PERSON 후보 score 상승
- PERSON + PHONE 조합으로 composite flag 부여 가능

제외되는 예:

```text
T1: 이름은 하늘입니다.
T2: 전화 뒷자리는 2222입니다.
T3: 강남구에 삽니다.
```

- 이전 턴 조각 결합은 v0.2에서 처리하지 않음
- 해당 기능은 v1에서 별도 session module로 설계

## 5. 문서와 코드에서 제거해야 할 명칭

다음 명칭은 v0.2 코드/문서의 핵심 경로에 포함하지 않는다.

- `SessionMonitor`
- `FragmentLedger`
- `SubjectTracker`
- `SessionEntityGraph`
- `session_context`
- `session_id` required field
- `rag_context`
- `retrieval_scan`

단, 향후 확장 가능성을 위해 `scan_stage` enum에는 `input`과 `output`만 둔다. `retrieval`은 예약하지 않는다.

## 6. 평가 계획 변경

초기 평가셋의 `multi-turn mosaic` 항목은 제거하고, 대신 다음 단일 턴 평가 버킷을 추가한다.

| 기존 버킷 | 변경 후 |
|---|---|
| Multi-turn mosaic 100건 | Single-turn composite 200건 |
| Session leakage rate | Single-turn composite recall |
| Subject-level leakage | 현재 범위 제외 |

## 7. v1 재도입 조건

RAG와 멀티턴은 다음 조건을 만족한 뒤 v1에서 재검토한다.

1. raw offset mapping 안정화
2. 구조형 PII detector release gate 통과
3. boundary accuracy 목표치 달성
4. span resolver와 masking policy 안정화
5. no-raw-PII audit 검증 완료
6. 단일 턴 gold set에서 ablation report 작성 완료
