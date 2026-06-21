# 초거대 AI 플랫폼에서 한국어 개인정보 흐름 통제를 위한 LLM Gateway 기반 Layer 0 가드레일 설계 및 평가

양유상1*, 김민우2, 정연서2, [교수명1]3, [교수명2]3, [교수명3]3  
중부대학교1, CCIT연구소2, [소속 입력]3

# Design and Evaluation of a Layer 0 Guardrail for Korean Personal Information Flow Control in LLM Gateways

YuSsang Yang1*, Minwoo Kim2, Yeonseo Jeong2, [Professor Name 1]3, [Professor Name 2]3, [Professor Name 3]3  
Joongbu University1, CCIT Research Institute2, [Affiliation]3

---

요약 : 초거대 AI 플랫폼에서는 사용자 입력, 모델 응답, 감사로그를 거쳐 개인정보가 이동하므로 LLM 호출 전 단계의 흐름 통제가 필요하다. 본 논문은 한국어 정규화와 PII 사전/패턴 탐지를 결합한 LLM-free Layer 0를 LLM Gateway의 pre-call 계층으로 배치한다. 10k stratified payload 평가에서 Layer 0 포함 구성은 전체 TRUE detection 94.32%로 LLM judge 포함 구성의 90.96%를 상회했으며, KR_semantic slice에서는 96.39% 대 87.40%로 +8.99%p 높았다. 또한 p99 지연은 830ms 대 4,819ms로 낮아, 한국어 개인정보 흐름 통제를 위한 저지연 선행 방어선의 가능성을 확인하였다.

Key Words : Korean PII, LLM Gateway, Layer 0 Guardrail, Korean Normalization, Personal Information Flow Control

## 1. 서 론

초거대 AI 플랫폼을 업무 서비스에 연결하면 사용자의 입력, 모델 응답, 운영 로그, 감사 데이터 사이에서 개인정보가 이동한다. 특히 LLM Gateway는 여러 모델 호출이 집중되는 통제 지점이므로, 개인정보를 LLM 또는 외부 API로 전달하기 전에 탐지·마스킹·차단하는 보안 계층이 필요하다. 그러나 한국어 개인정보는 주민등록번호나 전화번호 같은 정형 패턴뿐 아니라 진단명, 알레르기, 종교, 직위, 소속, 결혼상태 등 텍스트형·의미형 개인정보를 포함한다. 이러한 정보는 자모 분해, Unicode 변형, 초성 표기, 야민정음, 로마자 혼합, 구분자 삽입 등으로 표면형을 쉽게 바꿀 수 있어 기존 탐지기를 우회할 수 있다.

기존 PII 탐지와 가드레일 시스템은 정규식, NER, 관리형 보안 필터, LLM judge 등을 활용한다. 여기서 NER(Named Entity Recognition)는 사람명, 기관명, 위치명 등 텍스트 안의 개체를 자동 식별하는 기법이고, LLM judge는 별도의 언어모델이 입력 또는 출력을 다시 판정하는 방식이다. 범용 탐지기는 영어 중심 엔티티와 정형 패턴에 강하지만 한국어 텍스트형 PII와 표기 변형에 충분히 최적화되어 있지 않을 수 있다. 또한 LLM judge는 의미 판별 능력이 있으나 외부 API 호출, 비용, 지연, 인터넷 의존성, 재현성 문제가 발생한다.

본 논문은 한국어 LLM Gateway에서 개인정보 흐름을 사전에 통제하기 위한 LLM-free Layer 0 PII Guardrail을 설계하고 평가한다. 제안 방식은 사용자 입력을 LLM과 외부 가드레일로 전달하기 전에 한국어 정규화기를 적용하고, 이후 PII 사전/패턴 탐지를 수행하여 PASS, BLOCK, MASK 정책을 결정한다. 본 논문의 기여는 다음과 같다. 첫째, 한국어 자모·Unicode·표기 변형을 고려한 Layer 0 선행 방어 계층을 설계하였다. 둘째, 10k stratified payload와 KR_semantic slice에서 기존 LLM judge 기반 구성과 head-to-head 비교하였다. 셋째, TRUE detection, real bypass, p99 지연, false positive, McNemar 검정, ablation을 함께 제시하여 운영형 LLM Gateway에서의 실용성을 평가하였다.

## 2. 관련연구 및 위협모델

### 2.1 관련연구

한국어 개인정보 탐지는 한글 자모, 호환 자모, Unicode 정규화, 표기 변형의 영향을 받는다. 기존 한글 정규화 연구는 유니코드 환경에서 한글 표현 체계와 조합 문제를 분석하였으며[1], 한국어 PII 연구는 개인식별번호와 개인정보 처리 능력 평가를 다루었다[2]. 최근에는 KcBERT, Chain-of-Thought 프롬프팅, 정규식, 키워드를 결합한 한국어 개인정보 보호 연구도 제안되었다[3]. 그러나 이러한 연구는 주로 데이터셋 구축, 모델 기반 탐지, 문서 비식별화에 초점을 두었고, LLM Gateway의 pre-call 단계에서 deterministic guardrail을 배치하여 지연·비용·오탐까지 함께 평가한 연구는 제한적이다.

문자 수준 공격 연구는 invisible character, homoglyph, reordering 등 인코딩 기반 교란이 NLP 시스템에 실질적인 우회 수단이 될 수 있음을 보였다[4]. 또한 최근 guardrail robustness 연구는 typo, camouflage, cipher, veiled expression 등 다양한 mutation이 가드레일 모델의 강건성을 저하시킬 수 있음을 보고하였다[5]. 본 연구는 이러한 위협을 한국어 텍스트형 PII 우회 문제로 정의하고, LLM Gateway 앞단에 한국어 특화 Layer 0를 배치해 선행 차단 효과를 평가한다.

### 2.2 위협모델

본 연구의 위협모델은 LLM 사용자가 개인정보 검사를 우회하기 위해 입력 표면형을 변형하는 상황이다. 예를 들어 사용자는 알레르기, 처방, 계좌번호, 사건번호, 소속, 직책 같은 민감 정보를 자모 분해, zero-width 문자 삽입, fullwidth 숫자, 초성 표기, 야민정음, 로마자 혼합, JSON·로그·콜센터 문맥 삽입 형태로 입력할 수 있다. 이때 기존 가드레일이 표면 문자열이나 영어 중심 엔티티에 의존하면 실제 민감정보가 LLM으로 전달될 수 있다.

본 연구는 공격자가 시스템 내부 설정이나 모델 파라미터에는 접근하지 못하지만, 입력 텍스트를 자유롭게 구성할 수 있다고 가정한다. 또한 목표는 모델 자체 공격이 아니라 개인정보 흐름 통제 우회이다. 따라서 방어 목표는 원문 개인정보를 가능한 한 LLM 호출 전에 탐지하고, 정책에 따라 마스킹 또는 차단하며, 사후 감사가 가능하도록 원문을 저장하지 않는 로그를 남기는 것이다.

## 3. 연구내용

### 3.1 제안 방법 개요

제안 Layer 0는 사용자 입력이 LLM과 외부 가드레일로 전달되기 전에 실행되는 pre-call 계층이다. 먼저 한국어 normalizer가 Unicode, 자모, 초성, 야민정음, 숫자·구분자 변형을 표준형으로 복원한다. 이후 한국어 PII detector가 regex와 키워드/의미형 사전을 이용해 개인정보를 탐지한다. 탐지 결과에 따라 요청은 PASS, BLOCK, MASK 중 하나로 처리된다.

Layer 0의 핵심은 LLM 호출 없이 로컬에서 동작한다는 점이다. deterministic 방식은 같은 입력에 항상 같은 결과를 내는 규칙 기반 방식으로, 운영 환경에서 재현성과 감사 가능성이 높다. 반면 LLM judge는 복잡한 의미 판별에 유용하지만, 모든 입력에 대해 호출하면 지연과 비용이 증가한다. 따라서 본 연구의 Layer 0는 LLM judge를 완전히 대체하기보다, judge 이전에 배치되는 저비용·저지연 선행 방어선으로 설계되었다.

Fig. 1. Architecture of Layer 0 Pre-Call Guardrail in Korean LLM Gateway

사용자 입력 → Layer 0 Korean Normalizer → Korean PII Detector → L1 Presidio → L2 Bedrock Guardrails → L3 Lakera → LLM → L4 GPT-4o-mini Judge

### 3.2 실험 설계

본 연구는 10k stratified payload를 사용하여 네 가지 구성을 비교하였다. 주요 slice로는 한국어 텍스트형 PII를 포함하는 KR_semantic slice(n=1,302)를 별도로 분석하였다. 평가 지표는 TRUE detection, real bypass, KR_semantic TRUE detection, KR_semantic bypass, p99 latency를 사용하였다. TRUE detection은 ground-truth PII payload의 차단·마스킹 성공률을 의미하고, real bypass는 해당 payload가 차단·마스킹 없이 통과한 비율을 의미한다. p99 latency는 전체 요청 지연시간을 작은 순서로 정렬했을 때 99% 지점의 값이다.

Table 1. Evaluation Configurations

| Config | Composition | Purpose |
|---|---|---|
| A | L1~L3 | Production-like baseline without LLM judge |
| B | L1~L4 | Baseline with GPT-4o-mini judge |
| C | L0~L3 | Proposed Layer 0 without LLM judge |
| D | L0~L4 | Full stack with Layer 0 and LLM judge |

A는 기존 L1~L3 가드레일 스택이며, B는 A에 L4 LLM judge를 추가한 구성이다. C는 기존 스택 앞단에 Layer 0를 추가하되 LLM judge를 사용하지 않는 구성이다. D는 Layer 0와 LLM judge를 모두 포함한 full stack이다. 본 논문의 핵심 비교는 LLM judge 중심 구성인 B와 Layer 0 포함 no-LLM 구성인 C의 head-to-head 비교이다.

### 3.3 실험 결과

Table 2. Main Evaluation Results

| Config | Overall TRUE | Overall Bypass | KR_semantic TRUE | KR_semantic Bypass | p99 Latency |
|---|---:|---:|---:|---:|---:|
| A: L1~L3 | 80.15% | 19.85% | 49.62% | 50.38% | 1,317ms |
| B: L1~L4 | 90.96% | 9.04% | 87.40% | 12.60% | 4,819ms |
| C: L0~L3 | 94.32% | 5.68% | 96.39% | 3.61% | 830ms |
| D: L0~L4 | 97.23% | 2.77% | 98.85% | 1.15% | 4,762ms |

실험 결과, Layer 0를 포함한 C 구성은 LLM judge를 포함한 B 구성보다 전체와 KR_semantic 모두에서 높은 TRUE detection을 보였다. 전체 10k 기준으로 C는 94.32%, B는 90.96%였으며, C가 B보다 3.36%p 높았다. 특히 KR_semantic slice에서는 C가 96.39%, B가 87.40%로 나타나 +8.99%p의 차이를 보였다. 이는 한국어 텍스트형 PII에서 Layer 0의 한국어 정규화와 사전/패턴 기반 탐지가 효과적임을 의미한다.

지연 측면에서도 C 구성은 B 구성보다 우수하였다. C의 p99 latency는 830ms인 반면, B의 p99 latency는 4,819ms로 나타났다. 이는 LLM judge 호출을 포함하는 구성보다 Layer 0 기반 pre-call 차단이 운영 환경에서 더 낮은 지연으로 동작할 수 있음을 보여준다. B와 C의 paired 비교에서 McNemar p-value는 2.04e-28로 보고되어, Layer 0 포함 구성의 개선이 우연한 차이로 보기 어렵다. 정상 텍스트에 대한 false positive는 2%로 보고되었다.

다만 Layer 0의 효과를 정규화 단독의 효과로 해석해서는 안 된다. ablation 결과에서 KR_semantic 기준 정규화 단독 gain은 0.31%p로 제한적이며, detector/dictionary의 기여가 더 크게 나타났다. 따라서 본 연구의 주장은 “정규화만으로 성능이 향상되었다”가 아니라, “정규화-우선 구조가 한국어 PII 사전/패턴 탐지를 가능하게 하고, 이를 pre-call 계층으로 배치했을 때 한국어 텍스트형 PII 우회를 줄일 수 있다”는 것이다.

### 3.4 논의

C가 B보다 높은 결과를 보인 것은 Layer 0가 LLM judge를 모든 경우에 대체한다는 의미가 아니다. 오히려 한국어 텍스트형 PII 중 상당 부분은 LLM 호출 전에 deterministic하게 탐지·차단할 수 있음을 보여준다. LLM judge는 복잡한 문맥 판단에 유용하지만, 모든 요청에 대해 호출할 경우 지연과 비용이 증가한다. D가 가장 높은 탐지율을 보인 점은 Layer 0와 L4 judge의 상호보완성을 보여준다. 실운영에서는 Layer 0를 기본 방어선으로 두고, 고위험 또는 불확실 케이스에 L4 judge를 선택적으로 적용하는 구성이 적합하다.

개인정보 흐름 통제 관점에서는 탐지 성능뿐 아니라 정책적 대응도 필요하다. 사용자가 자모 분해, invisible character, 표기 변형 등을 반복적으로 사용해 개인정보 검사를 회피하려는 행위는 단순 입력 오류가 아니라 잠재적 우회 시도로 간주할 수 있다. 따라서 원문 개인정보를 저장하지 않는 범위에서 탐지 유형, 변형 유형, 정책 결정, span 길이, HMAC 기반 식별자 등을 감사로그로 남기고, 반복 시도에 대해서는 경고, rate limit, 관리자 검토, 이용약관 기반 제재 등 단계적 대응 정책을 둘 필요가 있다. 이러한 정책은 초거대 AI 플랫폼에서 개인정보 흐름 통제와 융합보안 거버넌스를 함께 구현하기 위한 운영 기준이 될 수 있다.

본 연구의 한계도 존재한다. 첫째, 사용 데이터는 synthetic payload 중심이므로 실제 운영 로그와의 외부 타당성 검증이 필요하다. 둘째, 사전/패턴 기반 탐지는 신규 PII 표현과 도메인 특화 표현에 대해 지속적인 사전 확장이 필요하다. 셋째, 일부 비교 구성은 외부 API와 관리형 가드레일에 의존하므로, 실행 환경과 서비스 설정에 따라 재현성 차이가 발생할 수 있다.

## 4. 결론

본 논문은 초거대 AI 플랫폼에서 한국어 개인정보 흐름을 사전에 통제하기 위한 LLM Gateway 기반 Layer 0 Guardrail을 설계하고, 10k stratified payload에서 기존 LLM judge 기반 구성과 비교 평가하였다. 실험 결과 Layer 0 포함 구성은 전체 TRUE detection과 KR_semantic slice 모두에서 LLM judge 포함 구성보다 높은 탐지율을 보였고, p99 지연도 낮았다. 특히 KR_semantic에서 +8.99%p의 차이는 한국어 정규화와 사전/패턴 기반 pre-call 탐지가 한국어 텍스트형 PII 방어에 효과적임을 보여준다.

향후 연구에서는 실제 한국어 운영 로그에 가까운 clean corpus, attack-family별 ablation, 한국어 도메인별 PII 사전 확장, Smart Skip 기반 L4 호출 최적화를 추가 검증할 필요가 있다. 본 연구는 한국어 LLM 서비스에서 deterministic pre-call guardrail이 저지연 개인정보 방어선으로 활용될 수 있음을 보이며, 초거대 AI 플랫폼의 개인정보 흐름 통제와 융합보안 거버넌스 설계에 실증적 근거를 제공한다.

## 참고문헌

[1] 안대혁, 박영배, “유니코드 환경에서의 올바른 한글 정규화를 위한 수정 방안,” 정보과학회논문지: 소프트웨어 및 응용, Vol. 34, No. 2, pp. 169-177, 2007.  
[2] 강예지, 비립, 박서윤, 장연지, 이종규, 김한샘, “한국어 언어모델의 개인 식별 번호 처리 능력 연구,” 한국콘텐츠학회논문지, Vol. 24, No. 4, pp. 42-58, 2024.  
[3] 이태규, 이익희, 이제민, 정수민, 조혜민, 김형진, “생성형AI 시대의 한국어 데이터를 위한 개인정보 보호: KcBERT와 Chain-of-Thought 프롬프팅 기반 하이브리드 접근을 중심으로,” 경영정보학연구, Vol. 27, No. 1, pp. 247-268, 2025.  
[4] N. Boucher, I. Shumailov, R. Anderson, and N. Papernot, “Bad Characters: Imperceptible NLP Attacks,” Proceedings of the IEEE Symposium on Security and Privacy, 2022.  
[5] E. Bassani and I. Sanchez, “On Guardrail Models’ Robustness to Mutations and Adversarial Attacks,” Findings of the Association for Computational Linguistics: EMNLP 2025, pp. 16995-17006, 2025.
