# Capstone Midterm Deck Plan

## Audience
- Midterm presentation for professors / evaluators
- Result-focused, but still needs enough context to justify why Layer 0 exists

## Objective
- Make the audience understand three points immediately:
- Why Korean is more vulnerable than English in current gateway guardrails
- Why `Layer 0 (L0)` was added at the gateway level
- Why L0 is more practical than an LLM judge for Korean semantic PII

## Narrative Arc
1. Background: Korean PII is intrinsically harder
2. Problem check: existing guardrails still miss Korean text-type PII
3. Root cause: most production guardrails are English-centered
4. Proposal: add a Korean augmentation layer at the gateway
5. Method: evaluate on validity-first, real API benchmark
6. Results: Korean gap, 4-way comparison, KR semantic slice
7. Interpretation: L0 is an augmentation layer, not a standalone engine
8. Practicality: latency, cost, smart cascade, robustness, FP
9. Midterm framing: what is already proven, what remains
10. Extension: PII boundary, validation pipeline, and future Korean protection engine work

## Slide List
1. Cover
2. One-page summary
3. Agenda
4. Project background
5. Then what about guardrails?
6. Bedrock guardrail experiment
7. Root cause: English-centered guardrails
8. Research questions and goal
9. AI Gateway context
10. Data flow and insertion point
11. Five-layer defense pipeline
12. L0 design: normalizer
13. L0 design: detector
14. Evaluation overview
15. Benchmark composition
16. Main problem data: English vs Korean
17. What baseline especially misses
18. 4-way overall comparison
19. 4-way English/Korean split
20. KR semantic head-to-head
21. L0 standalone performance
22. Interpreting standalone L0
23. McNemar significance
24. Ablation
25. Latency and cost
26. Smart cascade
27. Robustness
28. False positives and operational readiness
29. Midterm achievements and remaining work
30. Sensitive vs non-sensitive PII boundary
31. Validation pipeline extension
32. Remaining work: Korean PII protection engine
33. Conclusion and Q&A

## Source Plan
- Existing PPT screenshots / media
  - `tmp_old_media/image1.png`: KDPII paper screenshot
  - `tmp_old_media/image2.png`: Korean quote on Korean-specific PII difficulty
  - `tmp_old_media/image3.png`: earlier Korean vs English miss-rate table
  - `tmp_old_media/image4.png`: Bedrock input screenshot
  - `tmp_old_media/image5.png`: Bedrock result screenshot
  - `tmp_old_media/image7.png`: no-guardrail gateway diagram
  - `tmp_old_media/image9.png`: AI Gateway / data flow diagram
  - `tmp/slides/capstone_midterm_20260424/preview/source/slide-03.png`: prescription masking comparison from `김민우가.pptx`
- Current evaluation data
  - `PII/results/summaries/run_e_final_summary.json`
  - `PII/results/phase1/phase1_l0_standalone.json`
  - `PII/results/phase1/phase1_mcnemar.json`
  - `PII/results/phase1/phase1_latency_precise.json`
  - `PII/results/phase1/phase1_fp_test.json`
  - `PII/results/phase2/phase2_v4_final_4way.json`
  - `PII/results/phase3/phase3_ablation.json`
  - `PII/results/phase3/phase3_l4_smart_skip.json`
- Project paper / manuscript
  - `paper/capstone_main_v1.md`

## Visual System
- Background: warm light neutral (`#F7F4ED`)
- Ink: dark navy (`#101828`)
- Secondary body: muted slate (`#475467`)
- English: blue (`#2E6AE6`)
- Korean: orange (`#F28C28`)
- Baseline(A): gray (`#8A9099`)
- +LLM Judge(B): navy (`#203A8E`)
- +Layer 0(C): green (`#22A66A`)
- Full(D): near-black navy (`#0F172A`)
- Alert / emphasis: red (`#D92D20`)
- Typography: `Malgun Gothic` for Korean readability, `Aptos Mono` for labels

## Asset Needs
- Reuse old PPT screenshots for background/problem/setup slides
- Rebuild all data slides with editable charts/cards
- Keep charts native and readable in 5 seconds

## Editability Plan
- All titles, body text, labels, callouts, metrics, and notes are authored as editable PowerPoint objects
- Data-backed visuals use native chart objects
- Screenshots are only used as contextual evidence, not as a substitute for new data slides
