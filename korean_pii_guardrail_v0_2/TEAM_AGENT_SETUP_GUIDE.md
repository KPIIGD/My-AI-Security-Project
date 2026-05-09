# Team Agent Setup Guide

이 문서는 `korean_pii_guardrail_v0_2` 프로젝트에서 AI 코딩 도구를 사용할 때 팀원이 맞춰야 할 최소 설정 가이드입니다.

목표는 도구가 달라도 다음을 일관되게 지키게 하는 것입니다.

- v0.2 단일 턴 범위 유지
- 기존 `PII/` 연구 스택과 새 패키지 분리
- raw PII 안전 규칙 준수
- raw text offset 계약 준수
- 작업별 문서와 config를 먼저 읽고 구현

## 1. 공통 프로젝트 지침 파일

각 도구가 자동으로 읽는 프로젝트 지침 파일을 만든다.

Codex 사용자는 이 프로젝트에 이미 있는 파일을 사용한다.

```text
korean_pii_guardrail_v0_2/AGENTS.md
```

Claude 사용자는 본인 환경이 읽는 프로젝트 지침 파일에 같은 내용을 옮긴다.

예:

```text
korean_pii_guardrail_v0_2/CLAUDE.md
```

도구가 다른 파일명을 요구하면 그 파일명으로 만들면 된다. 중요한 것은 파일명이 아니라 내용이다.

## 2. 공통으로 넣어야 할 핵심 규칙

프로젝트 지침 파일에는 아래 내용을 반드시 포함한다.

```md
# Project Agent Instructions

## Scope

These instructions apply only to `korean_pii_guardrail_v0_2`.

Do not treat sibling directories such as `PII/`, `paper/`, `build/`, `outputs/`, or `tmp/` as part of this package unless explicitly asked.

## Start Of Work

Before code changes, read:

1. `README.md`
2. `docs/12_SCOPE_CHANGE_NOTE.md`
3. `docs/10_DEVELOPMENT_HANDOFF.md`

Always inspect existing source, tests, schemas, and configs before editing.

## Core Rules

- Keep v0.2 single-turn only.
- Do not implement RAG scanning, retrieval sanitization, multi-turn session monitoring, fragment ledger, subject tracker, Redis TTL store, previous-turn risk accumulation, full LLM judge, or human review dashboard.
- All detector spans must use raw text character offsets.
- Every internal `PIISpan` must satisfy `span.text == raw_text[span.start:span.end]`.
- Detectors produce candidates only; final actions belong to resolver, policy, and masking stages.
- Never write raw PII into logs, exceptions, metrics, reports, audit events, or public response spans.
- Keep entity, scoring, context, and policy behavior config-driven.
- Do not promote dictionary-only `PERSON_NAME` matches to high confidence without context.
- Preserve Korean suffixes during masking: replace only the PII body and keep josa/honorific/ending text outside the replacement.

## Change Protocol

- Entity changes: update `configs/entities.yaml`, `src/pii_guardrail/enums.py`, and `schemas/pii_span.schema.json`.
- Score changes: update `configs/scoring.yaml` and `docs/03_SCORING_POLICY_SPEC.md`.
- Context changes: update `configs/context_rules.yaml` and `docs/04_CONTEXT_POLICY_SPEC.md`.
- Policy changes: update `configs/policy_profiles.yaml` and `docs/05_MASKING_POLICY_SPEC.md`.
- API/schema changes: update `api/openapi.yaml`, `schemas/*.schema.json`, dataclasses, and `docs/06_INTERFACE_SPEC.md`.

## Tests

Run focused pytest targets while developing, then the full suite when practical:

```bash
python -m pytest
```
```

## 3. Codex 사용자 설정

Codex 사용자는 선택적으로 개인 스킬을 만든다.

추천 스킬 이름:

```text
korean-pii-guardrail-dev
```

추천 위치:

```text
%USERPROFILE%\.codex\skills\korean-pii-guardrail-dev\SKILL.md
```

주의:

- 개인 PC 절대경로는 각자 자기 경로로 바꾼다.
- 스킬에는 세부 문서 라우팅을 넣는다.
- `AGENTS.md`에는 항상 지킬 최소 규칙만 둔다.

현재 예시 스킬은 다음 역할을 한다.

- 작업이 preprocess인지, masking인지, audit인지에 따라 어떤 문서를 먼저 읽을지 안내
- 기존 `PII/` 연구 스택과 새 패키지를 분리
- v0.2 금지 범위와 raw PII 안전 규칙을 재확인

## 4. Claude 사용자 설정

Claude 사용자는 Codex 스킬을 그대로 복사하지 말고, 같은 원칙을 Claude용 프로젝트 지침이나 개인 프롬프트 템플릿으로 옮긴다.

권장 구성:

```text
korean_pii_guardrail_v0_2/CLAUDE.md
```

또는 Claude 프로젝트 설정의 custom instructions에 아래 내용을 넣는다.

```md
When working on `korean_pii_guardrail_v0_2`, first read `README.md`, `docs/12_SCOPE_CHANGE_NOTE.md`, and `docs/10_DEVELOPMENT_HANDOFF.md`.

Use v0.2 single-turn scope only. Do not implement RAG, multi-turn, session monitor, fragment ledger, subject tracker, Redis TTL store, full LLM judge, or human review dashboard.

Preserve raw text offsets. Never write raw PII into logs, exceptions, metrics, reports, audit events, or public response spans.

Before implementation, inspect relevant docs, configs, schemas, source, and tests.
```

## 5. 작업별 문서 라우팅

세부 구현을 시작할 때는 작업 종류에 맞춰 아래 문서를 먼저 읽는다.

| Work area | Read these first |
|---|---|
| Schema/API/contracts | `docs/06_INTERFACE_SPEC.md`, `schemas/*.schema.json`, `api/openapi.yaml`, `src/pii_guardrail/schema.py`, `src/pii_guardrail/enums.py` |
| Preprocess/raw offset map | `docs/01_REQUIREMENTS_SPEC.md`, `docs/02_ARCHITECTURE_SPEC.md`, `docs/07_IMPLEMENTATION_ROADMAP.md`, `src/pii_guardrail/interfaces.py` |
| Regex detectors/validators | `configs/entities.yaml`, `configs/scoring.yaml`, `data/eval/hard_cases_v0.jsonl`, `docs/03_SCORING_POLICY_SPEC.md` |
| Korean boundary correction | `configs/josa_rules.yaml`, `docs/05_MASKING_POLICY_SPEC.md`, `docs/11_ANNOTATION_GUIDELINE.md`, `data/eval/hard_cases_v0.jsonl` |
| Dictionary/context scoring | `docs/03_SCORING_POLICY_SPEC.md`, `docs/04_CONTEXT_POLICY_SPEC.md`, `configs/context_rules.yaml`, `configs/scoring.yaml` |
| NER interface | `docs/06_INTERFACE_SPEC.md`, `src/pii_guardrail/ner/base.py`, `src/pii_guardrail/ner/mock_ner.py`, `src/pii_guardrail/ner/finetuned_wrapper.py` |
| Span resolver | `docs/02_ARCHITECTURE_SPEC.md`, `docs/03_SCORING_POLICY_SPEC.md`, `configs/entities.yaml`, `data/eval/hard_cases_v0.jsonl` |
| Policy/masking | `docs/05_MASKING_POLICY_SPEC.md`, `configs/policy_profiles.yaml`, `configs/entities.yaml` |
| Audit/log safety | `docs/09_COMPLIANCE_AND_AUDIT_SPEC.md`, `docs/05_MASKING_POLICY_SPEC.md`, `schemas/guardrail_response.schema.json` |
| Pipeline integration | `docs/02_ARCHITECTURE_SPEC.md`, `docs/07_IMPLEMENTATION_ROADMAP.md`, `docs/06_INTERFACE_SPEC.md` |
| Evaluation/ablation | `docs/08_EVALUATION_PLAN.md`, `data/eval/eval_manifest_v0.yaml`, `data/eval/hard_cases_v0.jsonl`, `scripts/run_eval.py`, `scripts/run_ablation.py` |

## 6. 공유하면 안 되는 것

팀원에게 그대로 공유하지 말아야 할 것:

- 개인 PC 절대경로
- 개인 Codex 스킬 폴더 경로
- API key, token, secret
- 개인 환경 변수

팀원에게 공유해도 되는 것:

- `AGENTS.md`의 핵심 규칙
- 이 문서의 작업별 문서 라우팅 표
- 금지 기능 목록
- 테스트 기준

## 7. 권장 사용 방식

새 작업을 시작할 때 AI 도구에 이렇게 요청한다.

```text
이 작업은 korean_pii_guardrail_v0_2 프로젝트 작업이다.
프로젝트 지침 파일을 먼저 읽고, 관련 docs/config/schema/source/tests를 확인한 뒤 구현해줘.
v0.2 단일 턴 범위를 벗어나지 말고 raw PII 안전 규칙을 지켜줘.
```

Codex에서 스킬을 설치한 경우:

```text
$korean-pii-guardrail-dev 를 사용해서 다음 milestone을 구현해줘.
```
