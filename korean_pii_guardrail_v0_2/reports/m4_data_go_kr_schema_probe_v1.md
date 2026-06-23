# M4 Data.go.kr Schema Probe

- phase: Phase B/C. Structured Source Parser And Candidate Probe
- probe_gate_status: pass
- failure_verdicts: data_go_kr_schema_probe_pass
- source_count: 10
- max_records_per_source: 500
- score_tuning_allowed_by_this_phase: false
- raw_text_persisted_in_reports: false
- raw_candidate_values_persisted_in_reports: false

## Overall Candidate Counts By Entity

| entity | count |
|---|---:|
| ADDRESS_FULL | 360 |
| ADDRESS_UNIT | 3847 |
| BUSINESS_REG_NO | 1941 |
| CORPORATE_REG_NO | 622 |
| CREDIT_CARD | 234 |
| EMAIL | 801 |
| FAMILY_RELATION | 33 |
| FRN | 3 |
| HOSPITAL | 5 |
| ORGANIZATION | 229 |
| PERSON_NAME | 57 |
| PHONE_LANDLINE | 1828 |
| RRN | 127 |
| SCHOOL | 1 |

## Source Summary

| source | files | records_seen | records_processed | top_shapes | top_entities |
|---|---:|---:|---:|---|---|
| commercial_store_info | 17 | 2725319 | 500 | phone_like:1816, business_reg_like:505, corporate_reg_like:448 | ADDRESS_UNIT:1005, ADDRESS_FULL:4, FAMILY_RELATION:1 |
| corporate_basic_info | 30 | 300000 | 500 | phone_like:1486, corporate_reg_like:504, business_reg_like:492, url_like:326 | BUSINESS_REG_NO:460, ADDRESS_UNIT:429, PHONE_LANDLINE:398, CORPORATE_REG_NO:209, ADDRESS_FULL:168 |
| detailed_address | 0 | 0 | 0 | - | - |
| fair_trade_door_to_door_sales | 16 | 26959 | 500 | business_reg_like:561, phone_like:256, corporate_reg_like:1 | BUSINESS_REG_NO:506, EMAIL:465, ADDRESS_UNIT:454, PHONE_LANDLINE:219, ORGANIZATION:10 |
| fair_trade_online_sales | 30 | 300000 | 500 | phone_like:838, business_reg_like:543, url_like:79, corporate_reg_like:77, email_like:75 | ADDRESS_UNIT:766, BUSINESS_REG_NO:500, PHONE_LANDLINE:337, EMAIL:336, CORPORATE_REG_NO:30 |
| financial_company_basic_info | 30 | 300000 | 500 | phone_like:1518, corporate_reg_like:500, business_reg_like:484, url_like:368 | BUSINESS_REG_NO:475, ADDRESS_UNIT:445, PHONE_LANDLINE:396, CORPORATE_REG_NO:383, ADDRESS_FULL:163 |
| hira_hospital_info | 14 | 112588 | 500 | phone_like:490 | ADDRESS_UNIT:748, PHONE_LANDLINE:478, ADDRESS_FULL:21, ORGANIZATION:8, HOSPITAL:4 |
| nts_business_status | 0 | 0 | 0 | - | - |
| pps_nara_marketplace | 0 | 0 | 0 | - | - |
| road_name_address | 0 | 0 | 0 | - | - |

This is a schema and candidate-connectivity probe only. It does not approve score tuning.
