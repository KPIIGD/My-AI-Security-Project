# M4 External Codex Data Analysis v1

- phase: `Codex data analysis after user-approved PII-only labels`
- approved_label_count: `1999`
- hard_negative_row_count: `832`
- probability_support_gate_status: `fail`
- runtime_scoring_behavior_changed: `false`
- score_delta_changed: `false`
- raw_candidate_values_persisted_in_reports: `false`

## Conclusion

Codex-approved guardrail disagreements are already useful as hard negatives, but only ADDRESS is ready for probability comparison. The next data round should target PERSON_NAME, PHONE, EMAIL, REGISTRATION_IDENTIFIER, BANK_ACCOUNT before score tuning.

## Core Entity Group Analysis

| entity_group | pii | not_pii | hard_negatives | status | primary_gap |
|---|---:|---:|---:|---|---|
| PERSON_NAME | 4 | 10 | 10 | needs_more_data | insufficient_total_support |
| ADDRESS | 295 | 391 | 391 | ready_for_probability_comparison | none |
| PHONE | 286 | 0 | 0 | needs_more_data | insufficient_not_pii_hard_negatives |
| EMAIL | 63 | 0 | 0 | needs_more_data | insufficient_not_pii_hard_negatives |
| REGISTRATION_IDENTIFIER | 471 | 0 | 0 | needs_more_data | insufficient_not_pii_hard_negatives |
| BANK_ACCOUNT | 0 | 0 | 0 | needs_more_data | insufficient_total_support |

## Collection Targets

- `PERSON_NAME`: collect more person-name-like common nouns, brand/shop fragments, and true person-name contexts; current total support is small
- `ADDRESS`: current group is usable; add more region-only/location-only hard negatives only if source diversity is needed
- `PHONE`: collect sample/test/documentation phone-like strings approved as not PII by Codex; keep public organization phone numbers as PII
  - Do not count as not-PII: public organization or business phone numbers
- `EMAIL`: collect sample/test/placeholder email-like strings approved as not PII by Codex; keep public business emails as PII
  - Do not count as not-PII: public business or organization email addresses
- `REGISTRATION_IDENTIFIER`: collect invalid/sample/unrelated registration-like codes that guardrail extracts but Codex approves as not PII
  - Do not count as not-PII: valid public business or corporate registration identifiers
- `BANK_ACCOUNT`: collect both real account-context candidates and sample/test account-like false positives; current support is absent
  - Do not count as not-PII: real payment/refund/settlement account details

## Next Bounded Run

- Collect or stage additional raw rows targeted to guardrail/Codex not-PII disagreements for: PERSON_NAME, PHONE, EMAIL, REGISTRATION_IDENTIFIER, BANK_ACCOUNT
- Run existing guardrail candidate extraction without changing detector logic.
- Run Codex PII-only classification and user approval in the same label model.
- Rebuild hard-negative disagreement rows and probability/logLR evidence.
- Run M4-only delta sweep only if all core support gates pass.
