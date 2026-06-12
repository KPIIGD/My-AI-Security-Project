# 한국어 PII 가드레일 벤치마크 (이식 가능)

> 우리 gold 평가셋(NAME/ADDRESS/ORG)을 **여러 가드레일에 통과시켜 누가 한국어 PII를 더 잡나(recall)** 비교.
> **이 폴더만 있으면** 다른 세션/PC 에서도 돈다 (원본 데이터 의존 끊김).

## 파일
| 파일 | 역할 |
|---|---|
| `eval_gold.jsonl` | 독립 평가셋 (val 5,901 + test 5,901 + klue_test 5,000). 각 줄 `{id, split, sentence, spans:[{start,end,type}]}` |
| `benchmark.py` | 벤치 실행기 (gold → 가드레일 → 타입별 recall) |
| `export_eval_gold.py` | gold 재생성기 (원본 pii_ner_v4_full.json 있을 때만 필요) |

## 실행

```powershell
cd C:\litellm\guardrail_benchmark

# 로직 검증 (네트워크 0)
python benchmark.py --self-test

# 우리 NER vs Presidio (내부 test 500건)
python benchmark.py --systems our_ner,presidio --split test --n 500

# 외부 KLUE 평가셋으로
python benchmark.py --systems our_ner,presidio --split klue_test --n 500

# 결과 JSON 저장
python benchmark.py --systems our_ner --split test --save result_v3.json
```

출력 = `시스템 × {NAME, ADDRESS, ORG, 전체} recall` 표.

### 전제 (실행 시)
- **our_ner**: 사이드카 떠 있어야 함 → `docker compose up -d` (C:\litellm). `OUR_NER_URL` env 로 주소 변경 가능.
- **presidio**: `docker start presidio-analyzer` → localhost:5001. `PRESIDIO_URL` env 로 변경.
- 다른 PC면 endpoint 만 env 로 맞추면 됨.

## 🔌 새 가드레일 추가 (3단계)

`benchmark.py` 의 **"가드레일 어댑터" 섹션**에:

1. **어댑터 함수** 추가 — `text → [(start, end, "NAME"/"ADDRESS"/"ORG"), ...]`
   그 시스템의 entity_type 을 우리 3타입으로 매핑 (없는 타입은 버림):
   ```python
   def adapter_comprehend(text):
       import boto3
       r = boto3.client("comprehend").detect_pii_entities(Text=text, LanguageCode="ko")
       MAP = {"NAME": "NAME", "ADDRESS": "ADDRESS"}
       return [(e["BeginOffset"], e["EndOffset"], MAP[e["Type"]])
               for e in r["Entities"] if e["Type"] in MAP]
   ```
2. **ADAPTERS dict 에 등록**: `"comprehend": adapter_comprehend,`
3. **실행**: `python benchmark.py --systems our_ner,presidio,comprehend`

→ Bedrock / Azure PII / Google DLP 등 뭐든 같은 패턴. 엔드포인트/키는 함수 안에서 env 로.

## 평가 방식
- **recall 중심**: "우리가 라벨한 PII를 잡았나". (precision 은 우리 gold 가 3타입뿐이라 phone/email 도 잡는 상대에 불공정 → 제외)
- **매칭**: gold span 과 같은 타입 span 이 **overlap** 하면 catch (관대한 recall).
- span 의 start/end 는 char offset (`sentence[start:end] == 개체`).

## 참고 결과 (v3 NER 기준)
| 평가셋 | our_ner | Presidio |
|---|---|---|
| 내부 test | **79.2%** | 3.5% |
| 외부 KLUE | **69.0%** | 4.9% |

→ 영어 중심 Presidio 는 한국어 ORG **0%**. 우리 가드레일이 14~22배. (v4 학습 후 재실행하면 향상 측정)
