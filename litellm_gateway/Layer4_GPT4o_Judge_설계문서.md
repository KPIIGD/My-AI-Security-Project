# Layer 4 — GPT-4o PII Judge 설계 문서
## 다음 세션에서 바로 구현할 수 있도록 모든 참고 자료 + 설계 확정

---

## 1. 기존 오픈소스/실무 사례에서 긁어모은 것들

### 1.1 LiteLLM 공식 — Custom Guardrail 구현 패턴
- `apply_guardrail(text, language, entities, request_data) → str` 메서드 구현
- 차단 시 `raise Exception()`, 통과 시 text 그대로 반환
- post_call 모드: LLM 응답 생성 후 실행, 응답 내 PII 유출 여부 검증
- 스트리밍 시 post_call은 전체 응답 조립 후 실행 (audit-only)
- 출처: docs.litellm.ai/docs/proxy/guardrails/custom_guardrail

### 1.2 LiteLLM Custom Code Guardrail — 간소 버전
- `apply_guardrail(inputs, request_data, input_type)` 함수
- 반환값: `allow()`, `block(reason)`, `modify(texts=[])`
- `input_type`이 "request" 또는 "response"로 구분됨
- `http_post()`로 외부 API 비동기 호출 가능
- 출처: docs.litellm.ai/docs/proxy/guardrails/custom_code_guardrail

### 1.3 Guardrails AI — Presidio + GLiNER 조합 PII 탐지
- Presidio regex + GLiNER NER 모델 결합 → 최고 성능
- entity별 threshold 커스터마이징 가능
- PassResult / FailResult 반환 구조
- 출처: github.com/guardrails-ai/guardrails_pii

### 1.4 OneShield Privacy Guard (논문)
- Entity Recognition → Contextual Scoring → Policy Enforcement 3단계
- 컨텍스트 기반 entity 평가 — 이름+생년월일 조합 시 위험도 상승
- 출처: arxiv.org/html/2501.12456v1

### 1.5 PII Guard (Ollama 기반)
- SLM(gemma:3b)을 로컬에서 돌려서 PII 탐지
- 난독화/불완전/임베딩된 PII도 시맨틱 컨텍스트로 탐지
- 다국어 지원, regex 한계 극복
- 출처: github.com/rpgeeganage/pII-guard

### 1.6 LangChain Guardrails — 다계층 미들웨어 패턴
- Layer 1: Deterministic (regex/keyword)
- Layer 2: PII protection (input+output)
- Layer 3: Human-in-the-loop
- Layer 4: Model-based safety check
- 출처: docs.langchain.com/oss/python/langchain/guardrails

### 1.7 mcp-pii-tools — GPT-4o 기반 한국어 PII 탐지
- GPT-4o langextract 사용
- 한국어 이름/이메일/전화번호/주민번호 탐지
- 익명화 + 결정론적 암호화 + 복호화 지원
- JSON 구조화된 결과 반환
- 출처: github.com/czangyeob/mcp-pii-tools

### 1.8 OpenAI Guardrails Python (공식)
- GuardrailsAsyncOpenAI 드롭인 교체
- PII detection, URL filtering, hallucination detection
- Presidio 내부 사용
- 출처: openai.github.io/openai-guardrails-python

### 1.9 Pillar Security — Generic Guardrail API
- GuardrailRequest/GuardrailResponse 표준 스키마
- action: "BLOCKED" / "NONE" / "GUARDRAIL_INTERVENED"
- texts, images, tool_calls 모두 검사 가능
- 출처: docs.litellm.ai/docs/proxy/guardrails/pillar_security

---

## 2. Layer 4 설계 — 우리 프로젝트 맞춤

### 2.1 핵심 역할
- LLM 응답(output)에 PII가 유출됐는지 **최종 판정**
- Layer 1~3이 못 잡은 PII를 자연어 이해로 탐지
- **한국어 PII 특화** — 주민번호, 전화번호, 이름, 주소 등
- 판정 결과를 구조화된 JSON으로 반환 → 실험 데이터로 활용

### 2.2 구현 방식 선택

| 방식 | 장점 | 단점 | 선택 |
|------|------|------|------|
| CustomGuardrail 클래스 | 완전한 제어, 외부 패키지 사용 가능 | .py 파일 필요 | **✅ 선택** |
| Custom Code (YAML 인라인) | 간편 | 샌드박스 제한, http_post만 가능 | ❌ |

### 2.3 아키텍처

```
LLM 응답 도착
  → [Layer 4: GPT-4o Judge]
      1. 응답 텍스트 추출
      2. GPT-4o에 판정 프롬프트 전송
      3. JSON 결과 파싱
      4. PII 발견 시 → block / 미발견 시 → allow
      5. 판정 결과 로깅
  → 사용자에게 응답 반환 (또는 차단)
```

### 2.4 판정 프롬프트 (핵심 — 한국어 특화)

```
당신은 PII(개인식별정보) 탐지 전문가입니다.
아래 텍스트에 개인식별정보가 포함되어 있는지 판정하세요.

## 탐지 대상 PII 유형
- 한국 주민등록번호 (6자리-7자리 형식 또는 변형)
- 한국 전화번호 (010-XXXX-XXXX, 02-XXX-XXXX 등)
- 한국인 이름 (2~4글자 한국어 성명)
- 한국 주소 (시/구/동/로 포함)
- 이메일 주소
- 신용카드 번호
- 은행 계좌번호
- 여권번호, 운전면허번호
- 사업자등록번호
- 외국인등록번호

## 특별 지시
- 자모 분해(ㅈㅜㅁㅣㄴ), 초성(ㅈㅁㄷㄹㅂㅎ), 야민정음 등 한국어 변이 형태도 탐지
- 숫자가 부분적으로 마스킹된 경우(예: 010-****-5678)도 탐지
- 문맥상 PII로 추론 가능한 경우도 포함

## 응답 형식 (반드시 JSON만 출력)
{
  "contains_pii": true/false,
  "confidence": 0.0~1.0,
  "entities": [
    {
      "type": "PII 유형",
      "value": "탐지된 값",
      "start": 시작위치,
      "end": 끝위치,
      "confidence": 0.0~1.0
    }
  ],
  "reasoning": "판정 근거 한 줄 요약"
}

## 검사 대상 텍스트
{text}
```

### 2.5 비용 최적화 전략 (3AI 피드백 반영)

1. **gpt-4o-mini 우선 테스트**
   - 소규모 샘플(50건)로 4o vs 4o-mini 판정 일치율 확인
   - 일치율 90%+ 이면 mini로 스케일업 → 비용 1/10

2. **Cascade 구조**
   - Layer 1~3을 전부 통과한 응답만 Layer 4로 전달
   - Layer 1~3에서 이미 차단된 건 Judge 불필요

3. **OpenAI Batch API**
   - 실시간 아닌 실험 평가 시 Batch API 사용 → 추가 50% 절감

4. **캐싱**
   - 동일 입력에 대한 판정 결과 캐싱 → 중복 호출 방지

### 2.6 LiteLLM 등록 구조

**파일**: `custom_guardrail.py` → Docker 볼륨 마운트

**config.yaml 추가**:
```yaml
guardrails:
  - guardrail_name: "gpt4o-pii-judge"
    litellm_params:
      guardrail: custom_guardrail.GPT4oPIIJudge
      mode: "post_call"
      default_on: true
```

**Docker 마운트**: `C:\litellm\custom_guardrail.py` → `/app/config/custom_guardrail.py`

### 2.7 판정 결과 구조 (실험 데이터용)

```json
{
  "judge_model": "gpt-4o-mini",
  "contains_pii": true,
  "confidence": 0.95,
  "entities": [
    {
      "type": "KR_RRN",
      "value": "900101-1234567",
      "start": 8,
      "end": 22,
      "confidence": 0.98
    },
    {
      "type": "KR_PHONE",
      "value": "010-1234-5678",
      "start": 30,
      "end": 43,
      "confidence": 0.97
    }
  ],
  "reasoning": "주민등록번호와 전화번호가 평문으로 노출됨",
  "latency_ms": 1250,
  "action": "BLOCK"
}
```

---

## 3. 차별화 포인트 (오픈소스 대비)

| 기존 | 우리 Layer 4 |
|------|-------------|
| 영어 PII 위주 | **한국어 PII 특화 프롬프트** |
| 단순 yes/no | **entity별 위치+신뢰도+유형 반환** |
| 단일 모델 | **gpt-4o / gpt-4o-mini 스위칭** |
| 독립 실행 | **LiteLLM 파이프라인 내장 (post_call)** |
| PII만 | **한국어 변이 형태(자모/초성/야민정음) 인식** |

---

## 4. 구현 순서 (다음 세션)

### Step 1: custom_guardrail.py 작성
- CustomGuardrail 상속
- apply_guardrail에서 OpenAI API 호출
- JSON 파싱 + 에러 핸들링

### Step 2: config.yaml 수정
- guardrails 섹션에 gpt4o-pii-judge 추가
- mode: post_call, default_on: true

### Step 3: Docker 재시작
- docker-compose down → up
- custom_guardrail.py 마운트 확인

### Step 4: Playground 테스트
- 영어 PII → 탐지 확인
- 한국어 PII → 탐지 확인
- 한국어 변이 PII → 탐지 확인

### Step 5: 4계층 풀스택 테스트
- Presidio + Bedrock + Lakera + GPT-4o Judge 전부 ON
- 동일 입력으로 각 계층 결과 비교

---

## 5. 참고 URL 전체

- LiteLLM Custom Guardrail: https://docs.litellm.ai/docs/proxy/guardrails/custom_guardrail
- LiteLLM Custom Code: https://docs.litellm.ai/docs/proxy/guardrails/custom_code_guardrail
- LiteLLM Generic Guardrail API: https://docs.litellm.ai/docs/adding_provider/generic_guardrail_api
- Guardrails AI PII: https://github.com/guardrails-ai/guardrails_pii
- OneShield 논문: https://arxiv.org/html/2501.12456v1
- PII Guard (Ollama): https://github.com/rpgeeganage/pII-guard
- mcp-pii-tools: https://github.com/czangyeob/mcp-pii-tools
- OpenAI Guardrails Python: https://openai.github.io/openai-guardrails-python
- LangChain Guardrails: https://docs.langchain.com/oss/python/langchain/guardrails
- Langfuse Security: https://langfuse.com/docs/security-and-guardrails
- LiteLLM Guardrails Registry: https://github.com/BerriAI/litellm-guardrails
- Pillar Security: https://docs.litellm.ai/docs/proxy/guardrails/pillar_security
- Pangea AI Guard: https://docs.litellm.ai/docs/proxy/guardrails/pangea
- NVIDIA NeMo Guardrails: https://developer.nvidia.com/nemo-guardrails
- Databricks Guardrails: https://www.databricks.com/blog/implementing-llm-guardrails
