# Context Domain Profile Notes v1

- phase: `Execution Phase 6. Domain and Aggregate Follow-Up`
- default_profile_decision: `keep_global_default`
- domain_specific_profile_created: `false`
- request_time_domain_required: `false`
- fallback_behavior: global default context profile

Domain-specific rows are report-only in v0.2. Low-support rows are not tuned.

| Domain | Rule Rows | Low Support Rows | Recommendation |
|---|---:|---:|---|
| ecommerce | 7 | 7 | keep_global_default_collect_more_evidence |
| enterprise_internal | 3 | 3 | keep_global_default_collect_more_evidence |
| finance | 1 | 1 | keep_global_default_collect_more_evidence |
| generic | 4 | 4 | keep_global_default_collect_more_evidence |
| healthcare | 1 | 1 | keep_global_default_collect_more_evidence |

## Fallback

Domains without enough evidence: `education, developer_docs`

Requests without domain metadata continue to use the global default profile.
