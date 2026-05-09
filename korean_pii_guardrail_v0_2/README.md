# Korean PII Guardrail v0.2 — Single-Turn Core

한국어 개인정보 탐지 및 비식별화 가드레일의 개발 착수용 프로젝트 파일입니다.

본 버전은 **RAG와 멀티턴 개념을 제외**하고, 단일 입력 텍스트에서 개인정보 후보를 탐지·보정·판정·마스킹하는 deterministic core를 먼저 완성하는 것을 목표로 합니다.

## 목표

1. 한국어 개인정보 후보를 raw text offset 기준으로 안정적으로 탐지한다.
2. 조사·호칭·어미가 붙은 한국어 span을 PII 본체와 suffix로 분리한다.
3. detector별 점수를 통일된 score 체계로 변환하고, 겹침·중복 span을 결정론적으로 병합한다.
4. output target과 policy profile에 따라 label mask, partial mask, pseudonym, HMAC hash, block을 선택한다.
5. raw PII가 로그, 평가 리포트, telemetry에 저장되지 않도록 한다.

## 명시적 제외 범위

다음 기능은 v0.2에서 구현하지 않습니다.

- RAG 문서 또는 retrieval context 스캔
- 멀티턴 세션 그래프
- fragment ledger
- subject tracker
- 이전 턴 기반 combination risk
- session_id 기반 TTL store
- full LLM judge
- NeuroFilter/activation-space guardrail
- human review dashboard

단, **현재 입력 텍스트 내부에서의 조합 위험**은 포함합니다. 예를 들어 같은 문장 안에 이름과 전화번호가 함께 있으면 composite PII로 승격할 수 있습니다.

## 권장 개발 순서

1. `schema.py`, `enums.py`, JSON Schema 확정
2. 전처리와 raw offset map 구현
3. 구조형 regex detector 및 validator 구현
4. 한국어 boundary corrector 구현
5. dictionary/context scorer 구현
6. span resolver와 masking engine 구현
7. audit logger와 no-raw-PII 검증 구현
8. evaluation harness와 ablation runner 구현
9. mock NER 연동 후 실제 NER wrapper 교체

## 산출물 위치

- 계획서: `docs/00_PROJECT_PLAN.md`
- 요구사항 명세서: `docs/01_REQUIREMENTS_SPEC.md`
- 아키텍처 명세서: `docs/02_ARCHITECTURE_SPEC.md`
- 점수 산정 명세서: `docs/03_SCORING_POLICY_SPEC.md`
- context 명세서: `docs/04_CONTEXT_POLICY_SPEC.md`
- 마스킹 정책 명세서: `docs/05_MASKING_POLICY_SPEC.md`
- 인터페이스 명세서: `docs/06_INTERFACE_SPEC.md`
- API 계약: `api/openapi.yaml`
- 설정 파일: `configs/`
- 스키마 파일: `schemas/`
- 개발 skeleton: `src/pii_guardrail/`

## 핵심 계약

모든 detector는 반드시 원문 raw text 기준 character offset을 반환해야 합니다.

```python
PIISpan.start  # raw text 기준 inclusive offset
PIISpan.end    # raw text 기준 exclusive offset
```

정규화 텍스트 기준 offset만 반환하는 detector는 pipeline에 연결할 수 없습니다.

## 로그 원칙

- raw PII 저장 금지
- audit log에는 entity type, score, source, reason code, span length, HMAC hash만 기록
- 복원 가능한 token mapping이 필요한 경우 application DB와 분리된 저장소 및 별도 접근권한 필요

## 상태

이 패키지는 구현을 시작하기 위한 **명세 및 skeleton**입니다. production-ready 코드는 아닙니다.
