# Korean PII Guardrail v0.2 Project File Manifest

본 패키지는 한국어 개인정보 탐지 및 비식별화 가드레일 개발 착수를 위한 프로젝트 파일 세트입니다.

## 적용 범위

- 포함: 단일 입력 텍스트 기준 개인정보 탐지, 한국어 경계 보정, 점수 산정, span 병합, 정책 기반 마스킹, 감사 로그, 평가 하네스.
- 제외: RAG 컨텍스트 스캔, 멀티턴 세션 그래프, fragment ledger, subject tracker, 이전 턴 기반 위험 누적.

## 주요 문서

| 파일 | 목적 |
|---|---|
| `README.md` | 프로젝트 개요 및 실행 기준 |
| `docs/00_PROJECT_PLAN.md` | 상세 개발 계획서 |
| `docs/01_REQUIREMENTS_SPEC.md` | 요구사항 명세서 |
| `docs/02_ARCHITECTURE_SPEC.md` | 단일 턴 아키텍처 명세서 |
| `docs/03_SCORING_POLICY_SPEC.md` | 점수 산정 및 결합 명세서 |
| `docs/04_CONTEXT_POLICY_SPEC.md` | 단일 턴 context window 및 context judge 명세서 |
| `docs/05_MASKING_POLICY_SPEC.md` | 마스킹 정책 선택 명세서 |
| `docs/06_INTERFACE_SPEC.md` | Python/HTTP 인터페이스 명세서 |
| `docs/07_IMPLEMENTATION_ROADMAP.md` | 구현 로드맵 및 작업 분해 |
| `docs/08_EVALUATION_PLAN.md` | 평가 데이터셋, 지표, ablation 계획 |
| `docs/09_COMPLIANCE_AND_AUDIT_SPEC.md` | 가명처리/감사/로그 안전 명세 |
| `docs/10_DEVELOPMENT_HANDOFF.md` | 개발자 핸드오프 문서 |
| `docs/11_ANNOTATION_GUIDELINE.md` | 라벨링 가이드라인 초안 |
| `docs/12_SCOPE_CHANGE_NOTE.md` | RAG/멀티턴 제외에 따른 변경사항 |

## 개발 시작용 파일

| 파일 | 목적 |
|---|---|
| `schemas/*.schema.json` | API 및 내부 객체 JSON Schema |
| `configs/*.yaml` | entity, scoring, policy, context, josa 설정 |
| `api/openapi.yaml` | REST API 계약 초안 |
| `src/pii_guardrail/*.py` | Python 패키지 인터페이스 skeleton |
| `data/eval/hard_cases_v0.jsonl` | 단일 턴 hard-case 평가 샘플 |
| `tests/test_contract_smoke.py` | schema/import smoke test |
| `pyproject.toml` | Python 프로젝트 설정 초안 |

## 문서 기준 버전

- Project version: `v0.2-single-turn`
- Date: `2026-05-09`
- Scope decision: RAG와 멀티턴은 v0.2 범위에서 제외하고, 단일 턴 텍스트 guardrail을 먼저 완성한다.
