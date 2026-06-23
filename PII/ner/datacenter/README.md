# NER 데이터센터

> finence/datacenter 패턴을 NER 학습 데이터 수집에 이식. **구조는 차용, 철학은 뒤집음.**

## 📊 현재 상태 (2026-06-04)
- **gold ner_examples 357,948** (corpus4ev 117k CC-BY-SA + aihub 119k + kimmeoungjun 82k 격리 + synth_conv_name 40k). ⚠️ **진짜 학습/공개 가능 = CC-BY-SA ~117k**, 나머지는 라이선스/품질 격리.
- **weak_examples 164만 문서 / 690만 PII span / 16도메인** (PSEUDO, gold 미혼합 — 검수+ablation 후보).
- **gazetteer 163,691** (NAME 20k + ORG 2.8k + ADDRESS 140k). collector 23개. DB ~16GB.
- **독립 적대 검증 완료**(2026-06-04): 엔지니어링=production급 인정. 결론="수집 그만, 학습/ablation/in-domain 평가로". 갭=구조형 PII·in-domain 평가셋(대화체 NAME은 synth로 채움).

## 평가/검증 (팀원·다음 세션)
```bash
python datacenter/run_collectors.py --stats   # 전체 카운트
python datacenter/leakage_gate.py             # KLUE test 누설 (현재 3건, aihub)
python datacenter/source_ablation.py          # 소스별 엔티티 기여+누설 pre-flight
python datacenter/eval_report.py              # 팀원 평가 패키지(eval_package/, 108K) 생성
python datacenter/export_clean.py             # 깨끗한 학습셋(CC-BY-SA+누설제외) export
```
팀원은 `eval_package/`(EVAL_REPORT.md + samples_*.jsonl, 16GB DB 없이 평가) 만 받으면 됨.

---

## 왜 철학을 뒤집나

| | finance datacenter | NER 데이터센터 |
|---|---|---|
| raw 텍스트 | 그 자체로 신호 → "전부 다" 맞음 | 라벨 없으면 무용 + v2 가 31k→139k 로 KLUE 0.766→0.664 폭락 |
| 목표 | 최대 수집 (커버리지=알파) | **소스별 품질·라이선스·누설 게이트** (좋은 소스만 골라 쌓기) |

→ 데이터센터는 학습 데이터가 아니라 **"후보 금고"**. 새 소스는 누설 게이트 통과 +
소스별 고정 KLUE val ablation(이미 만든 `KlueAbortCallback` 재사용) 후에만 학습 투입.

## 구조

```
datacenter/
  schema.py          7-way BIO canonical + content_hash + BIO 검증 (학습 포맷과 동일)
  db.py              ner_datacenter.db: ner_examples(dedup 금고) + gazetteers + collector_runs
  run_collectors.py  레지스트리 + --only/--limit + 동적 실행 + 요약
  leakage_gate.py    적재 문장 ∩ KLUE test = 평가 누설 검사 (0 이어야 안전)
  collectors/
    corpus4everyone.py  examples — KLUE 파생 char-level NER 117k (Phase A 메인)
    org_krx.py          gazetteer — KRX 상장사 ORG 풀 2,765
```

collector 는 기존 `scripts/data_prep_v4` 로더를 재사용 → 학습 포맷 100% 일치 (재발명 X).

## 실행

```powershell
cd C:\My-AI-Security-Project\PII\ner
python datacenter/run_collectors.py --limit 5000     # 빠른 검증 (소스별 상한)
python datacenter/run_collectors.py                  # 전체
python datacenter/run_collectors.py --stats          # 적재 현황
python datacenter/leakage_gate.py                    # 누설 검사
```

## 새 소스 추가 절차 (v2 재발 차단)

1. `collectors/<id>.py` 작성 (`META` + `collect(limit)` → examples/gazetteer)
2. `run_collectors.REGISTRY` 에 `<id>` 추가
3. `python datacenter/run_collectors.py --only <id>` 로 적재
4. `python datacenter/leakage_gate.py` → 누설 0 확인
5. **소스 1개만 추가**해서 고정 KLUE val ablation → macro-F1 떨어지면 배제
6. 라이선스 깨끗(CC-BY-SA 등)한 것만 `export_training_json(licenses=[...])` 로 추출

## 다음 확장 후보 (INVENTORY.md)

- `open_ner_aihub` (119k, span offset) · `ziozzang_address` (도로명 136k → ADDRESS gazetteer)
- Phase B 약한 라벨링: 의료/개인정보분쟁 원문 → regex+사전+NER 자동 태깅 → 일부 검수
- finance datacenter `raw_documents` 한국어 커뮤니티 원문 재활용 (도메인 편향 주의)
