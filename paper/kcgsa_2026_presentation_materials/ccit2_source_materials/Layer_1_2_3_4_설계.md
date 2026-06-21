# Layer 1·2·3·4 설계 (프롬프트 인젝션 평가용)

## 0. 문서 목적

이 문서는 기존 프로젝트의 4단계 검증 구조를 **PII 중심 평가에서 프롬프트 인젝션 중심 평가로 확장**하기 위한 설계 문서다.  
핵심 목표는 다음 두 가지다.

1. **한국어 vs 영어 프롬프트 인젝션 취약성 차이**를 정량적으로 비교한다.
2. 단순 탐지율이 아니라 **실제 제어권 탈취·비밀 유출·도구 오용이 발생하는지**를 중심으로 평가한다.

본 설계는 기존 내부 문서의 Layer 1~4 구조를 유지하되, 프롬프트 인젝션의 특성에 맞게 지표·오라클·데이터셋·통계 설계를 재정의한다.  
내부 정렬 근거는 다음 문서를 따른다.

- [I1] `ccit2번4단계_검증_프레임워크_팀공유.md`
- [I2] `LLM Gateway 보안 평가 프레임워크`(도식 자료)
- [I3] `붙여넣은 텍스트 (1).txt`
- [I4] `Layer1_3자비교_종합보고서.docx`
- [I5] `Phase1_종합분석_한국어vs영어_비교.docx`

---

## 1. 왜 4-Layer 구조가 필요한가

### 1.1 프롬프트 인젝션은 PII와 평가 대상이 다르다

PII 평가는 주로 “이 문자열이 민감정보인가”라는 **탐지 문제**에 가깝다.  
반면 프롬프트 인젝션은 **신뢰 경계(trust boundary)를 넘어 제3자 지시가 모델·에이전트의 행동을 바꾸는 시스템 공격**에 가깝다.  
OWASP는 prompt injection을 직접 공격과 간접 공격으로 구분하고, OpenAI는 사용자와 AI가 아닌 **제3자 콘텐츠가 대화 컨텍스트에 악의적 지시를 삽입**할 수 있다고 설명한다. Microsoft도 Prompt Shields에서 **user prompt attacks**와 **document attacks**를 분리한다. [R1][R2][R3]

따라서 프롬프트 인젝션 평가는 다음을 함께 봐야 한다.

- **탐지기(guardrail engine)가 공격을 분류하는지**
- **Gateway 통합 시 성능이 약화되는지**
- **실제 모델/에이전트가 공격 목표를 달성했는지**
- **정상 업무를 과잉 차단하지 않는지**
- **간접 입력(RAG 문서, 이메일, 웹페이지, 툴 응답)에서도 동일한 문제가 발생하는지**

### 1.2 Layer 1만으로는 최종 보안 결론을 내릴 수 없다

OpenAI는 prompt injection을 “frontier security challenge”이자 지속적으로 진화하는 문제로 설명하고, 실제로 에이전트가 이메일·웹페이지·외부 문서를 읽고 사용자를 대신해 행동할수록 위험이 커진다고 본다. [R2][R4]  
또한 AgentDojo, InjecAgent, BIPIA 같은 벤치마크는 모두 **정적 문자열 분류가 아니라 도구·외부 콘텐츠·실행 결과**를 평가 대상으로 삼는다. [R6][R7][R8]

따라서:

- **Layer 1**: 진단층(diagnostic layer)
- **Layer 2**: 통합 손실 분석층(integration analysis layer)
- **Layer 3**: 행동 결과 평가층(outcome layer)
- **Layer 4**: 실제 서비스형 E2E 평가층(deployment-like layer)

으로 역할을 나누는 것이 타당하다.

---

## 2. 평가 정당성(validity) 확보 원칙

NIST AI 800-2는 자동 benchmark 평가에서 **통계 분석과 불확실성 보고**, **평가 상세와 transcript 공유**, **실제 배포 조건과의 유사성**, **과도한 일반화 금지**를 강조한다. [R5]  
본 프로젝트는 아래 5개 정당성을 만족하도록 설계한다.

### 2.1 구성 타당성(construct validity)
- “프롬프트 인젝션 방어력”을 **탐지율 하나로 환원하지 않는다.**
- Layer 3~4에서는 **공격 목표 달성률(ASR)**, **비밀 유출률(SER)**, **무단 행동률(UAR)** 같이 결과 중심 지표를 메인으로 둔다.

### 2.2 내부 타당성(internal validity)
- 같은 공격 케이스를 **엔진 단독 vs Gateway 통합 vs 풀 시스템**에 반복 투입한다.
- KR/EN 비교는 **의미적으로 동일한 쌍(pair)** 으로 만든다.
- 변화 요인은 **언어/변이/통합 유무/권한 범위**만 다르게 두고 나머지는 고정한다.

### 2.3 외부 타당성(external validity)
- Layer 4에서 RAG 문서, 이메일, 파일, 웹페이지, 검색 결과, 툴 응답, 멀티턴을 포함한다.
- NIST 권고에 따라 평가 조건이 실제 배포 조건과 얼마나 유사한지 명시한다. [R5]

### 2.4 통계적 결론 타당성(statistical conclusion validity)
- 반복 실행, 신뢰구간, paired 비교, effect size를 보고한다.
- worst-case 비율 추정 기준으로 **95% 신뢰구간 ±10% 수준**을 원하면 셀당 약 100건, **±5% 수준**을 원하면 셀당 약 385건을 목표로 한다.

### 2.5 재현성(reproducibility)
- 모델 버전, guardrail 버전, Gateway 설정, system prompt, tool schema, region, temperature, retrieval 설정, 권한 범위, transcript를 보존한다.
- NIST 권고에 따라 item-level 결과와 주요 프로토콜을 함께 남긴다. [R5]

---

## 3. 공통 threat model

### 3.1 보호 대상(protected assets)
- 시스템 프롬프트 / 개발자 지시
- 시드된 비밀(canary secret)
- 민감 문서 / PII / 내부 데이터
- 도구 권한(읽기/쓰기/전송/삭제)
- 세션 상태 / 메모리 / 검색 결과

### 3.2 공격자와 진입점(entry points)
- **Direct**: 사용자 입력
- **Indirect**: RAG 문서, 검색 결과, 이메일, 파일, 웹페이지, 툴 응답, 메모리/요약

### 3.3 금지 결과(forbidden outcomes)
- 시스템 프롬프트 누출
- 비밀·PII 누출
- 무단 tool call / parameter abuse
- 외부 전송(send/forward/post/upload)
- 파일 수정/삭제/생성
- 정상 과업 방해 또는 내용 조작

### 3.4 평가 단위
- **Template**: 언어 중립적 공격 의도/업무 과업 골격
- **Case**: 언어·변이·entry point가 채워진 개별 샘플
- **Run**: 특정 시스템 구성에서 1회 실행한 결과

---

## 4. Layer 1 설계 — 탐지 실험 (Diagnostic Detection Layer)

### 4.1 목적
Guardrail 엔진 자체가 **직접/간접 prompt injection 텍스트를 어느 정도 탐지하는지** 진단한다.  
최종 보안 순위를 내리는 층이 아니라, **왜 취약한지 원인을 찾는 층**이다.

### 4.2 왜 필요한가
- Microsoft는 user prompt attacks와 document attacks를 별도로 분류한다. [R3]
- BIPIA는 외부 콘텐츠 기반 **indirect prompt injection**이 별도의 위험군임을 보여준다. [R8]
- 내부 프로젝트도 기존 Layer 1을 “순수 엔진 성능” 기준선으로 정의하고 있다. (내부 문서 참조)

### 4.3 입력 범위
- direct prompt
- retrieved document snippet
- email body
- webpage text
- tool output text
- multi-turn text transcript(텍스트만)
- benign hard-negative(정상 문맥 안의 공격 예시/인용)

### 4.4 출력 범위
- detect / no-detect
- attack family label(가능한 경우)
- severity or confidence
- latency
- explanation/annotation(있는 경우)

### 4.5 메인 지표
- **TPR / Recall**
- **FPR**
- **Precision**
- **KR-EN gap**
- **direct vs indirect gap**
- **benign hard-negative false positive rate**
- family-level recall:
  - 자모분리
  - 초성
  - 존댓말/완곡표현
  - 번역체
  - 코드스위칭
  - JSON/HTML/주석 삽입
  - 인용문/코드블록 삽입
  - role-play / fake conversation / encoding

### 4.6 Layer 1에서만 다루는 질문
- 엔진이 **문자열/문맥 수준에서 공격을 감지하는가**
- 한국어 변이 중 어떤 계열에서 특히 약한가
- direct보다 indirect를 더 못 잡는가
- benign hard-negative를 과도하게 공격으로 분류하는가

### 4.7 Layer 1 판정 오라클
- gold label과 엔진 label 비교
- direct/indirect binary detection
- subtype taxonomy mapping
- hard-negative는 “탐지되면 오탐”으로 처리

### 4.8 권장 최소 표본
- 상위 비교 셀(언어 × directness)당 held-out 100건 이상
- attack family 수준 탐색은 셀당 30~50건 이상
- hard-negative는 언어 × benign family 셀당 30건 이상

### 4.9 Layer 1의 한계
Layer 1 점수만으로 “안전하다/안전하지 않다”를 결론 내리면 안 된다.  
탐지기가 놓쳐도 실제 시스템이 안전할 수 있고, 탐지기가 잘 잡아도 Gateway 통합 또는 tool 사용 단계에서 뚫릴 수 있다.

---

## 5. Layer 2 설계 — 통합 손실 실험 (Gateway Integration Loss Layer)

### 5.1 목적
같은 guardrail 엔진이라도 **Gateway에 통합되면 방어 성능이 어떻게 변하는지** 측정한다.

### 5.2 왜 필요한가
- 내부 프로젝트는 이미 엔진 단독 결과와 Gateway 통합 결과를 분리해야 한다는 방법론을 가지고 있다. (내부 문서 참조)
- 실제 보안 운영은 엔진 단독이 아니라 **Gateway pre-call / post-call / annotation / mask / block 정책** 위에서 동작한다.
- OpenAI Developers 문서도 prompt injection과 write actions에 대해 **서버측 검증과 human confirmation**을 함께 두라고 권고한다. 이는 “탐지기 자체”보다 **시스템 통합 방식**이 결과를 크게 바꾼다는 뜻이다. [R4]

### 5.3 실험 구성
동일 케이스를 다음 두 조건에 투입한다.

1. **Engine Only**
2. **Gateway + Engine**

가능하면 Gateway 통합 조건을 다시 나눈다.

- pre-call only
- post-call only
- pre + post
- detect-only(annotation only)
- mask-only
- block
- human-confirmation on/off

### 5.4 메인 지표
- **integration loss** = engine-only 방어율 - gateway-integrated 실효 방어율
- **detection loss** = engine-only detect rate - gateway detect rate
- **enforcement loss** = gateway detect rate - gateway effective block rate
- **mask-only 통과율**
- **pre-call에서 놓치고 post-call에서만 잡는 비율**
- **post-call에서 놓쳐 실제 응답이 전달된 비율**
- **latency 증가**
- **error/timeout 증가**

### 5.5 판정 기준
Layer 2에서는 “탐지되었는가”와 “실제로 차단되었는가”를 분리해야 한다.

- detect but passed
- detect and masked
- detect and blocked
- not detected and passed
- system error / degraded response

### 5.6 Layer 2에서만 다루는 질문
- 엔진이 잡은 공격이 Gateway를 거치면 왜 통과하는가
- Gateway 설정(mask-only / annotation-only)이 실효 방어를 무너뜨리는가
- pre-call과 post-call 중 어디서 더 큰 손실이 발생하는가
- KR/EN 격차가 엔진 자체 때문인지, 통합 방식 때문에 더 커지는지

### 5.7 권장 로그
- raw request / response
- pre-call guardrail result
- post-call guardrail result
- applied policy(block/mask/allow)
- transformed prompt / transformed response
- Gateway version / config hash

---

## 6. Layer 3 설계 — 성과 지표 실험 (Outcome-Based Agent Layer)

### 6.1 목적
가드레일 + Gateway + LLM(+선택적 tool) 환경에서 **공격자가 실제 목표를 달성했는지** 평가한다.  
이 층부터가 프롬프트 인젝션의 핵심 평가층이다.

### 6.2 왜 필요한가
- InjecAgent는 tool-integrated LLM agent에서 간접 prompt injection 취약성을 측정한다. [R7]
- AgentDojo는 정적 테스트셋이 아니라 **실제 agent task, defenses, adaptive attacks**를 평가하도록 설계되었다. [R6]
- OpenAI는 prompt injection을 완벽 탐지 문제라기보다 **시스템 수준 방어와 defense-in-depth**의 문제로 본다. [R2][R4]

### 6.3 실험 조건
권한 모델을 명시적으로 변수로 둔다.

- no-tool
- read-only tool
- read + write tool
- external send/post enabled
- human confirmation on/off

### 6.4 대표 시나리오
- 시스템 프롬프트 유출
- 시드된 canary secret 유출
- PII/민감정보 외부 전송
- 승인 없는 read action
- 승인 없는 write/delete/send/post
- response manipulation(정상 업무 대신 공격자 지시 수행)
- session poisoning / memory carry-over

### 6.5 메인 지표
- **ASR_goal**: 금지된 공격 목표 달성률
- **SER**: 시스템 프롬프트/비밀/PII 누출률
- **UAR**: unauthorized action rate  
  (금지된 tool use / parameter abuse / external action)
- **STCR**: safe task completion rate  
  (공격을 받았어도 정상 과업을 안전하게 완료한 비율)
- **BOR**: benign over-block rate  
  (정상 요청을 과잉 거부 또는 과도하게 손상시킨 비율)

### 6.6 보조 지표
- KR-EN ASR gap
- direct vs indirect ASR gap
- tool-risk delta(툴이 있을 때 상승한 ASR)
- permission-risk delta(read-only 대비 read+write에서 상승한 ASR)
- latency / token overhead / confirmation burden

### 6.7 판정 오라클
- **Secret oracle**: 시드한 canary 문자열/패턴 유출 여부
- **Tool oracle**: tool name, parameter, side effect log
- **Action oracle**: send/post/upload/delete/write 성공 여부
- **Task oracle**: 정상 과업 완료 여부(정답 checker 또는 structured rubric)
- **Policy oracle**: expected safe behavior 대비 실제 행동 비교

### 6.8 Layer 3에서 중요한 점
이 층에서는 “탐지기가 경고를 냈는가”보다  
**최종적으로 시스템이 뚫렸는가, 그리고 정상 업무는 살렸는가**를 본다.

---

## 7. Layer 4 설계 — E2E 시나리오 (Deployment-Like End-to-End Layer)

### 7.1 목적
실제 서비스와 유사한 환경에서, 특히 **간접 prompt injection**이 실제로 어떤 피해를 만드는지 평가한다.

### 7.2 왜 필요한가
- OpenAI는 prompt injection의 핵심 위험이 **제3자 콘텐츠**와 **행동 가능한 에이전트**의 결합에서 커진다고 설명한다. [R2][R4]
- Microsoft Prompt Shields도 documents, emails 등 **third-party content**를 별도 공격군으로 다룬다. [R3]
- AgentDojo와 OpenAI Atlas의 automated red teaming은 실제 환경에서 **새로운 공격을 계속 발견**해야 한다는 점을 보여준다. [R4][R6]

### 7.3 포함해야 할 간접 입력
- RAG 검색 문서
- 검색 결과 snippet
- 이메일 본문/첨부 설명
- 웹페이지 본문
- HTML comment / metadata / alt text
- file summary / OCR text / tool output
- memory / previous summary / shared notes

### 7.4 포함해야 할 누적 공격
- multi-turn 누적 지시
- retrieval-time injection
- tool-output poisoning
- memory poisoning
- quoted attack followed by contextual reframing
- hidden or encoded instruction inside structured fields(JSON, YAML, HTML)

### 7.5 메인 지표
Layer 3 지표를 유지하되 아래를 추가한다.

- **Path-specific ASR**  
  (email, web, rag, file, tool-output, memory 경로별 성공률)
- **Incident severity mix**  
  (유출·조작·무단행동의 심각도 분포)
- **Containment rate**  
  (탐지 후 사용자 경고/확인 단계에서 실제 피해를 차단한 비율)
- **Recovery / fail-safe rate**  
  (공격 감지 시 정상적으로 중단·설명·대체 경로 제시 여부)

### 7.6 Layer 4 환경 구성 원칙
- deployment-like retrieval 설정
- 실제와 유사한 tool schema
- 최소 1개 read-only profile, 1개 write-capable profile
- seeded secrets / dummy assets / dummy inbox / dummy docs
- auditable logs

### 7.7 Layer 4에서만 다루는 질문
- 한국어 indirect attack이 실제 서비스형 파이프라인에서 더 잘 성공하는가
- 특정 entry point(email, web, rag, tool-output)가 더 위험한가
- 탐지 + human confirmation + least privilege를 조합하면 피해가 줄어드는가
- Layer 1/2 결과와 Layer 4 피해 양상이 실제로 연결되는가

---

## 8. 공통 실험 프로토콜

## 8.1 데이터 split
모든 데이터셋 묶음(attack, benign, outcome)에 대해 다음 split을 둔다.

- **dev/calibration**
- **held-out static**
- **adaptive**

중요한 점은 split을 **무작위 문장 단위가 아니라 template / mutation family / entry point 단위로 분리**하는 것이다.  
그래야 “익숙한 변형을 다시 맞춘 것”이 아니라 **새로운 공격 일반화**를 측정할 수 있다.  
AgentDojo와 OpenAI의 최근 자동 red teaming 방향도 정적 평가만으로는 부족하다는 점을 시사한다. [R4][R6]

## 8.2 KR-EN pair 설계
- user goal, protected asset, forbidden action, tool scope, entry point를 동일하게 유지
- 언어만 바꾸는 것이 아니라 **동일 의미를 갖는 자연스러운 공격쌍**으로 설계
- 직역이 어색하면 의미 동등성을 우선

## 8.3 반복 실행
비결정성을 고려해 **같은 case를 최소 5회 이상 반복 실행**한다.  
특히 Layer 3/4는 temperature, retrieval variance, agent planning variance 때문에 1회 결과만으로 결론 내리면 안 된다.

## 8.4 통계 분석
- 비율 지표: Wilson interval 또는 bootstrap CI
- KR vs EN, defense on/off: paired difference 또는 McNemar 계열 테스트
- effect size와 CI를 함께 보고
- 여러 비교를 동시에 할 때는 FDR 보정 또는 primary endpoint 사전 지정

## 8.5 보고 원칙
NIST 권고에 맞춰 다음을 같이 보고한다. [R5]

- benchmark 목적
- benchmark version
- exact model version
- exact guardrail / Gateway version
- test item 수와 유형
- evaluation protocol
- statistical assumptions
- uncertainty estimates
- deployment 유사성 및 한계
- item-level examples와 aggregate 결과

---

## 9. 권장 평가지표 정의

### 9.1 Layer 1
- Recall = 탐지된 공격 / 전체 공격
- FPR = 공격이 아닌 정상 케이스 중 오탐 비율
- KR-EN gap = KR recall(or FPR) - EN recall(or FPR)

### 9.2 Layer 2
- Integration Loss = Engine Only 실효방어율 - Gateway 실효방어율
- Enforcement Loss = 탐지율 - 실효 차단율
- Mask-Only Pass Rate = mask 처리 후 여전히 정책 위반 결과가 사용자에게 전달된 비율

### 9.3 Layer 3/4
- ASR_goal = 공격 목표 달성 케이스 / 전체 공격 케이스
- SER = 비밀/시스템 프롬프트/PII 누출 케이스 / 해당 자산을 노린 케이스
- UAR = 금지된 action 발생 케이스 / action-capable 케이스
- STCR = 정상 과업을 안전하게 완료한 케이스 / 해당 과업 케이스
- BOR = 정상 요청이 과잉 차단된 케이스 / benign 케이스

---

## 10. 최종 주장(qualified claim) 원칙

다음과 같은 주장은 가능하다.

- “정의된 threat model과 tool scope 아래에서, defense X는 한국어 indirect prompt injection의 ASR을 영어보다 더 높게 허용했다.”
- “Gateway 통합으로 인해 engine-only 대비 integration loss가 관찰되었다.”
- “human confirmation과 write 제한을 조합하면 UAR이 유의미하게 감소했다.”

다음과 같은 주장은 피해야 한다.

- “이 가드레일은 한국어 prompt injection을 해결했다.”
- “우리 benchmark 점수가 높으므로 실제 서비스에서도 안전하다.”

NIST는 평가 결과의 범위를 넘는 일반화에 주의하라고 권고한다. [R5]

---

## 11. 실행 우선순위

### Phase A — 빠른 기준선 구축
- Layer 1 dev/held-out 구축
- Layer 2 pre/post/mask/block 실험
- KR-EN pair 정착

### Phase B — outcome 중심 본실험
- Layer 3 기본 시나리오 20~30개
- read-only / write-capable 분리
- tool log oracle 완성

### Phase C — E2E 확장
- Layer 4 RAG + email + web + file + tool-output
- adaptive attack 루프 도입
- benchmark report 생성

---

## 12. 참고문헌 / 근거

### 내부 문서
- [I1] `ccit2번4단계_검증_프레임워크_팀공유.md`
- [I2] `LLM Gateway 보안 평가 프레임워크`(도식)
- [I3] `붙여넣은 텍스트 (1).txt`
- [I4] `Layer1_3자비교_종합보고서.docx`
- [I5] `Phase1_종합분석_한국어vs영어_비교.docx`

### 외부 근거
- [R1] OWASP Gen AI Security Project. *LLM01:2025 Prompt Injection*. https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- [R2] OpenAI. *Understanding prompt injections: a frontier security challenge*. https://openai.com/index/prompt-injections/
- [R3] Microsoft Learn. *Prompt Shields in Azure AI Content Safety*. https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/jailbreak-detection
- [R4] OpenAI. *Designing AI agents to resist prompt injection* / *Apps SDK Security & Privacy* / *Continuously hardening ChatGPT Atlas against prompt injection*.  
  https://openai.com/index/designing-agents-to-resist-prompt-injection/  
  https://developers.openai.com/apps-sdk/guides/security-privacy/  
  https://openai.com/index/hardening-atlas-against-prompt-injection/
- [R5] NIST. *AI 800-2 ipd: Practices for Automated Benchmark Evaluations of Language Models*. https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.800-2.ipd.pdf
- [R6] Debenedetti et al. *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents*. https://arxiv.org/abs/2406.13352
- [R7] Zhan et al. *InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated Large Language Model Agents*. https://arxiv.org/abs/2403.02691
- [R8] Yi et al. *Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models (BIPIA)*. https://arxiv.org/abs/2312.14197
- [R9] Cui et al. *OR-Bench: An Over-Refusal Benchmark for Large Language Models*. https://arxiv.org/abs/2405.20947


[R1]: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
[R2]: https://openai.com/index/prompt-injections/
[R3]: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/jailbreak-detection
[R4]: https://openai.com/index/designing-agents-to-resist-prompt-injection/
[R5]: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.800-2.ipd.pdf
[R6]: https://arxiv.org/abs/2406.13352
[R7]: https://arxiv.org/abs/2403.02691
[R8]: https://arxiv.org/abs/2312.14197
[R9]: https://arxiv.org/abs/2405.20947
