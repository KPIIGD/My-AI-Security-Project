# KCGSA 2026 Presentation Materials

이 폴더는 한국융합보안학회 2026 하계학술대회 논문 발표 PPT 제작에 필요한 자료를 한곳에서 찾기 위한 안내입니다.

## 바로 볼 자료

- `paper/kcgsa_2026_template_compliant_draft.md`: 학회 양식에 맞춘 논문 초안
- `paper/kcgsa_2026_revised_draft.md`: 수정 논문 초안
- `paper/figures/kcgsa_pipeline_guardrail_architecture*.png`: 발표용 아키텍처 그림
- `presentations/final_ppt_architecture_overview_clean.pptx`: 발표용 아키텍처 개요 PPT
- `presentations/final_ppt_architecture_overview_clean.png`: PPT 미리보기 이미지
- `paper/kcgsa_2026_presentation_materials/ccit2_source_materials/`: 기존 CCIT 논문/발표 작성 자료
- `korean_pii_guardrail_v0_2/reports/`: 논문 수치와 근거를 뒷받침하는 평가/안전성 리포트

## 생성 스크립트

- `scripts/create_kcgsa_pipeline_figure.py`
- `scripts/create_kcgsa_hwp_background.py`
- `scripts/create_kcgsa_template_filled_rhwp.js`
- `scripts/create_kcgsa_template_precise_rhwp.js`
- `scripts/update_kcgsa_phase7_hwp.js`

## 공개 저장소 제외 항목

이 저장소는 공개 GitHub 저장소이므로 아래 원본은 커밋하지 않았습니다.

- `결과 인풋 형식.json`
- `결과 아웃풋 형식.json`
- `수정한 테스트.json`
- `논문/*.pdf`

앞의 JSON 파일들은 원본 입력/출력 평가 데이터라 식별자 형태의 payload가 많이 포함되어 있습니다. `논문/*.pdf`는 외부 참고 논문 원문 PDF라 공개 저장소에 재배포하지 않고 파일명만 `reference_papers_local_only.md`에 기록했습니다.
