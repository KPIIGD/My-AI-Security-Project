# Alphagyuu False Positive Check on Normal Korean

Input: `PII/results/data/normal_kr_10k.json`
Preprocess: `korean`

Evaluated rows before stop: 8000 / 10000

Important correction: `LABEL_0` is treated as the non-entity/O label and is excluded from false-positive counting.

Raw any-detection rate before label filtering: 100.00%
Corrected false-positive documents: 37 / 8000 (0.46%)

## Non-O Labels

| Label | Count |
|---|---:|
| `LABEL_9` | 29 |
| `LABEL_10` | 13 |
| `LABEL_11` | 8 |
| `LABEL_12` | 2 |

## Sample Corrected False Positives

- Text: 질문입니다. 스포츠 경기 안내문은 짧은 문장으로 작성하고 핵심만 남깁니다. 에너지 절감 안내문은 짧은 문장으로 작성하고 핵심만 남깁니다. 우선순위 조정이 필요할까요?
  Non-O labels: LABEL_9

- Text: 질문입니다. 스포츠 경기에 대한 질문은 범위를 좁혀 순서대로 처리합니다. 어떤 방식이 더 적절한지 검토해 주세요.
  Non-O labels: LABEL_9

- Text: 메모: 반려식물 관리 결과를 표로 정리하면 차이를 쉽게 확인할 수 있습니다. 중복된 내용은 제외합니다.
  Non-O labels: LABEL_10, LABEL_9

- Text: 사용 방법: 문서 보관 과정에서 발견된 내용을 사용자 관점에서 분석합니다. 완료 후 결과를 다시 확인합니다.
  Non-O labels: LABEL_11

- Text: 사용 방법: 리스크 관리의 완료 조건을 사용자 관점에서 정리합니다. 완료 후 결과를 다시 확인합니다.
  Non-O labels: LABEL_11, LABEL_12

- Text: 절차 안내: 특히 스포츠 경기의 운영 계획을 반복해서 분석합니다. 순서를 바꾸지 않도록 주의합니다.
  Non-O labels: LABEL_9

- Text: 검토 메모: 카페 분위기 안내문은 짧은 문장으로 작성하고 핵심만 남깁니다. 중복된 내용은 제외합니다.
  Non-O labels: LABEL_9

- Text: 사용 방법: 응답 방식의 확인 항목을 사용자 관점에서 제안합니다. 완료 후 결과를 다시 확인합니다.
  Non-O labels: LABEL_11, LABEL_12

- Text: 검토가 필요합니다. 성과 공유 관련 의견을 모아 세부 기준을 다음 회의에서 검토합니다. 어떤 방식이 더 적절한지 검토해 주세요.
  Non-O labels: LABEL_10, LABEL_9

- Text: 핵심 요약: 관광 활성화 안내문은 짧은 문장으로 작성하고 핵심만 남깁니다. 불필요한 예시는 줄였습니다.
  Non-O labels: LABEL_10, LABEL_9