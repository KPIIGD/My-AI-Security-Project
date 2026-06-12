# 한국어 PII 가드레일 — 최종 4-way 비교 결과 (10,000건)

## 0. FINAL — 4-way head-to-head (모든 1만건에 풀 평가)

```
A) Baseline (L1~L3, 프로덕션 stack):       TRUE 80.15%   bypass 19.85%
B) Baseline + L4 (L1~L4, GPT-4o-mini):     TRUE 90.96%   bypass  9.04%
C) With L0 (L0~L3, 한국어 정규화, LLM 없음): TRUE 94.32%   bypass  5.68%  ⭐
D) Full (L0~L4, 모두):                      TRUE 97.23%   bypass  2.77%

★ B vs C: Layer 0가 GPT-4o judge보다 +3.36%p 더 잘 잡음 (전체)
★ KR_semantic: B 87.40% vs C 96.39% → C가 +8.99%p 더 잘 잡음
★ A → D: +17.08%p (80.15 → 97.23)
```

**KR_semantic (한국어 텍스트형 PII, n=1,302):**
| Config | TRUE | Bypass |
|---|---:|---:|
| A) Baseline | 49.62% | 50.38% |
| B) +L4 (LLM judge) | 87.40% | 12.60% |
| C) +L0 (Korean norm) | **96.39%** | **3.61%** |
| D) Full (L0+L4) | 98.85% | 1.15% |

**비용/지연:**
| | L4 | L0 |
|---|---:|---:|
| Latency/건 | ~2,200ms | ~10ms (220배 빠름) |
| 비용/건 | ~$0.0001 | $0 |
| KR_semantic TRUE | 87.40% | 96.39% |

**최종 thesis:** *"Layer 0(한국어 정규화+사전, LLM 없음)가 GPT-4o-mini judge보다 한국어 PII를 +8.99%p 더 잘 잡으면서, 비용 $0·지연 220배 낮다. 둘 다 쓰면 97.23%까지 상한선 도달."*

Figures: [fig10_4way_bypass.png](fig10_4way_bypass.png), [fig11_kr_semantic_4way.png](fig11_kr_semantic_4way.png), [fig12_hardest_pii_4way.png](fig12_hardest_pii_4way.png)
Data: [run_e_final_summary.json](run_e_final_summary.json), [eval_10k_l1l4_full.json](eval_10k_l1l4_full.json), [eval_10k_l0_l1l4_full.json](eval_10k_l0_l1l4_full.json)

---

# (이전) Layer 0 단독 측정 결과

**날짜**: 2026-04-20
**평가**: LiteLLM Gateway 통한 진짜 4계층(L0+L1~L3) 호출, GPT-4o judge 제외
**데이터셋**: stratified 10,000건 (KR 6,513 / EN 3,487, semantic 1,302건)
**비교 베이스라인**: L1~L3 only (Presidio + Bedrock Guardrail + Lakera)

---

## 1. 한 줄 결론

> **프로덕션 가드레일은 영어 PII 99.2% 잡지만 한국어 텍스트형 PII는 절반 이상(52.1%) 우회된다. Layer 0(한국어 정규화 + 키워드 사전) 추가 시 같은 카테고리에서 96.1%까지 회복되어 알레르기·회사·직책 등 11개 PII 타입이 100% 차단된다. 영어 PII 탐지율은 변동 없음(99.23% 유지).**

---

## 2. 헤드라인 수치

### 전체
| 지표 | Baseline (L1~L3) | With Layer 0 (L0~L3) | Δ |
|---|---:|---:|---:|
| TRUE detection | **79.01%** | **93.73%** | **+14.72%p** |
| Real bypass (FALSE+BYPASS) | 20.99% | 6.27% | **−14.72%p (70% 감소)** |

### 언어별
| 언어 | Baseline | With L0 | Δ |
|---|---:|---:|---:|
| EN | 99.23% TRUE | 99.23% | +0.00%p (변동 없음) |
| KR | 68.19% TRUE | **90.79%** | **+22.60%p** |

### Validity group (a priori 슬라이스)
| 그룹 | Baseline | With L0 | Δ |
|---|---:|---:|---:|
| EN_format / EN_checksum | ~99% | ~99% | ≈0 |
| KR_checksum (체크섬) | 81.61% | 83.14% | +1.53%p |
| KR_format (정규식) | 72.32% | **90.17%** | **+17.85%p** |
| KR_semantic (텍스트형) | **47.93%** | **96.08%** | **+48.15%p** |

---

## 3. Layer 0 직접 기여 (Layer 0가 단독으로 살린 케이스)

```
L0 solo catches:    1,444건  (다른 가드레일 모두 놓침, L0만 차단)
L0 + 다른 레이어:    1,652건  (L0가 추가 보강)
다른 레이어만:       6,302건  (L0 효과 없음)
모두 놓침 (남은 우회): 602건   (L0도 못 잡은 6.02%)
L0 BLOCK actions:   2,983건
L0 errors:          0건
L0 EN false positive: 0건  (영어 PII에 BLOCK 없음, MASK는 정규화만)
```

---

## 4. 가장 약했던 PII 타입 — Layer 0 효과

| PII 타입 | Baseline 우회 | With L0 우회 | Δ |
|---|---:|---:|---:|
| allergy (알레르기) | 92.3% | **0.0%** | −92.3%p ✨ |
| company (회사) | 85.7% | **0.0%** | −85.7%p |
| job_title (직책) | 82.4% | **0.0%** | −82.4%p |
| gps | 74.1% | **0.0%** | −74.1%p |
| degree (학위) | 73.7% | **0.0%** | −73.7%p |
| blood (혈액형) | 72.0% | **0.0%** | −72.0%p |
| marital (혼인상태) | 66.0% | **0.0%** | −66.0%p |
| dept (부서) | 64.8% | **0.0%** | −64.8%p |
| jwt | 63.3% | **0.0%** | −63.3%p |
| diagnosis (진단) | 62.5% | **0.0%** | −62.5%p |
| religion (종교) | 59.0% | **0.0%** | −59.0%p |
| session (세션토큰) | 95.9% | 4.1% | −91.8%p |
| court (사건번호) | 92.8% | 2.9% | −89.9%p |
| surgery (수술) | 87.5% | 1.4% | −86.1%p |
| prescription (처방) | 71.8% | 1.3% | −70.5%p |

**11개 한국어 텍스트형 PII가 0% 우회 = 100% 차단** (allergy, company, job_title, gps, degree, blood, marital, dept, jwt, diagnosis, religion).

---

## 5. 변이 레벨별 효과 (mutation level)

| 레벨 | 종류 | Baseline 우회 | With L0 우회 | Δ |
|---|---|---:|---:|---:|
| L0 | Original | 8.2% | **0.6%** | −7.6%p |
| L1 | Character (자모/초성) | 21.4% | **4.8%** | −16.7%p |
| L2 | Encoding (zwsp/combining) | 24.3% | 13.5% | −10.8%p |
| L3 | Format (구분자) | 13.1% | 10.4% | −2.7%p |
| L4 | Linguistic (한자/축약) | 30.4% | **5.4%** | −25.0%p |
| L5 | Context (ctx_json/ctx_rag) | 28.8% | **2.3%** | −26.5%p |

L4/L5 (가장 어려운 변이)에서도 회복 큼 — Layer 0 키워드 사전이 문맥 안에서도 한국어 PII를 잡아냄.

---

## 6. 남은 한계 (602건 real bypass)

```
PII 타입 top 5:
  emp_id 39, face_id 35, car_ins 30, EN_SSN 27, rrn 25

Validity group:
  format 443건 (특수 형식 PII — 정규식 의존)
  checksum 111건 (한국 사업자번호 등 일부 변이)
  semantic 48건 (한국어 텍스트형 — L0가 거의 다 잡음)

Mutation level:
  L2 Encoding 235건 (정규화 못한 인코딩)
  L1 Character 144건
  L3 Format 133건
```

→ 남은 약점은 **format 그룹 + L2 인코딩 변이**. 향후 과제: 추가 정규식 패턴 + 더 강한 인코딩 정규화.

---

## 7. 시각화

| 파일 | 내용 |
|---|---|
| [fig1_overall_bypass.png](fig1_overall_bypass.png) | 전체/언어/validity별 우회율 baseline vs L0 |
| [fig2_lang_x_validity.png](fig2_lang_x_validity.png) | Lang × Validity TRUE detection rate |
| [fig3_hardest_pii.png](fig3_hardest_pii.png) | Top 20 hardest PII bypass before/after |
| [fig4_mutation_level.png](fig4_mutation_level.png) | 변이 레벨별 회복 효과 |
| [fig5_l0_solo_pii.png](fig5_l0_solo_pii.png) | L0 단독 차단 PII 타입 분포 |

---

## 8. 데이터 신뢰성

- **L1~L3 baseline**: 4/19 fresh 호출 (Bedrock 정상화 후), 4/16 데이터와 일치 (TRUE 79.01% vs 78.5%)
- **Bedrock 정상 작동**: errors 0건, sanity check 50건 100% 일치
- **Presidio**: errors 0건
- **Lakera**: errors 0건, catch 0% (인젝션 전용, 4/16과 동일 — PII는 안 잡음이 정상)
- **Layer 0**: errors 0건, false positive 0건 (영어에 BLOCK 안 함)

데이터 오염 없음. cherry-picking 없음 (validity_group은 퍼저 단계의 a priori 분류).

---

## 9. 데이터 파일

| 파일 | 설명 |
|---|---|
| [eval_10k_l1l3.json](eval_10k_l1l3.json) | Baseline 평가 (L1~L3, 10k) |
| [eval_10k_l0_l1l3.json](eval_10k_l0_l1l3.json) | L0 추가 평가 (L0~L3, 10k) |
| [run_b_10k_summary.json](run_b_10k_summary.json) | Baseline 집계 |
| [run_c_l0_summary.json](run_c_l0_summary.json) | L0 vs Baseline 비교 집계 |
| [analyze_l0_deep.json](analyze_l0_deep.json) | L0 솔로/잔여 우회/FP 깊은 분석 |
| [payloads_10k.json](payloads_10k.json) | 평가 입력 (재현 가능) |
