# M4 External Raw Data Intake Manifest

- phase: Phase A. Raw Data Intake Manifest
- raw_root_exists: true
- zip_file_count: 28
- compressed_bytes_total: 26465440451
- hash_files_requested: true
- score_tuning_allowed_by_this_phase: false
- raw_text_persisted_in_reports: false
- raw_candidate_values_persisted_in_reports: false

## Gate

- status: pass
- failure_verdicts: external_raw_intake_gate_pass

## Source Summary

| source_id | zip_files |
|---|---:|
| aihub_624_web_corpus | 4 |
| aihub_free_conversation_speech_labels | 4 |
| aihub_specialized_corpus | 20 |

## Extension Summary

| extension | entries |
|---|---:|
| .json | 1879845 |
| .txt | 2 |
| <none> | 2105 |

## File Decisions

| relative_path | source_id | role | split | zip_entries | text_like_entries | audio_like_entries | recommended_action | parser_status |
|---|---|---|---:|---:|---:|---:|---|---|
| 030.웹데이터 기반 한국어 말뭉치 데이터\01.데이터\1.Training\라벨링데이터\TL1.zip | aihub_624_web_corpus | label | training | 51847 | 51830 | 0 | include_for_context_extraction | parsed_small_json_shape |
| 030.웹데이터 기반 한국어 말뭉치 데이터\01.데이터\1.Training\원천데이터\TS1.zip | aihub_624_web_corpus | source | training | 51830 | 51830 | 0 | include_for_context_extraction | parsed_small_json_shape |
| 030.웹데이터 기반 한국어 말뭉치 데이터\01.데이터\2.Validation\라벨링데이터\VL1.zip | aihub_624_web_corpus | label | validation | 7184 | 7167 | 0 | include_for_context_extraction | parsed_small_json_shape |
| 030.웹데이터 기반 한국어 말뭉치 데이터\01.데이터\2.Validation\원천데이터\VS1.zip | aihub_624_web_corpus | source | validation | 7167 | 7167 | 0 | include_for_context_extraction | parsed_small_json_shape |
| 자유대화 음성(일반남녀)\Training\[라벨]1.AI챗봇.zip | aihub_free_conversation_speech_labels | label | training | 1371739 | 1370295 | 0 | include_for_parser_probe | parsed_small_json_shape |
| 자유대화 음성(일반남녀)\Training\[라벨]3.스튜디오.zip | aihub_free_conversation_speech_labels | label | training | 214953 | 214789 | 0 | include_for_parser_probe | parsed_small_json_shape |
| 자유대화 음성(일반남녀)\Validation\[라벨]1.AI챗봇.zip | aihub_free_conversation_speech_labels | label | validation | 149451 | 149009 | 0 | include_for_parser_probe | parsed_small_json_shape |
| 자유대화 음성(일반남녀)\Validation\[라벨]3.스튜디오.zip | aihub_free_conversation_speech_labels | label | validation | 27114 | 27093 | 0 | include_for_parser_probe | parsed_small_json_shape |
| 전문분야 말뭉치\Training\[라벨]training_논문.zip | aihub_specialized_corpus | label | training | 23 | 23 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Training\[라벨]training_법령제개정.zip | aihub_specialized_corpus | label | training | 9 | 9 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Training\[라벨]training_의안.zip | aihub_specialized_corpus | label | training | 11 | 11 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Training\[라벨]training_자치법규_제개정문.zip | aihub_specialized_corpus | label | training | 1 | 1 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Training\[라벨]training_자치법규_조례.zip | aihub_specialized_corpus | label | training | 15 | 15 | 0 | include_for_parser_probe | json_parse_failed |
| 전문분야 말뭉치\Training\[라벨]training_자치법규_행정규칙.zip | aihub_specialized_corpus | label | training | 4 | 4 | 0 | include_for_parser_probe | parsed_small_json_shape |
| 전문분야 말뭉치\Training\[라벨]training_특허.zip | aihub_specialized_corpus | label | training | 505 | 505 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Training\[라벨]training_판례.zip | aihub_specialized_corpus | label | training | 7 | 7 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Training\[라벨]training_행정규칙_제개정문.zip | aihub_specialized_corpus | label | training | 2 | 2 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Training\[원천]전문분야_train.zip | aihub_specialized_corpus | source | training | 34 | 34 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_논문.zip | aihub_specialized_corpus | label | validation | 2 | 2 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_법령제개정.zip | aihub_specialized_corpus | label | validation | 1 | 1 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_의안.zip | aihub_specialized_corpus | label | validation | 2 | 2 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_자치법규_제개정문.zip | aihub_specialized_corpus | label | validation | 1 | 1 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_자치법규_조례.zip | aihub_specialized_corpus | label | validation | 2 | 2 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_자치법규_행정규칙.zip | aihub_specialized_corpus | label | validation | 1 | 1 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_특허.zip | aihub_specialized_corpus | label | validation | 40 | 40 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_판례.zip | aihub_specialized_corpus | label | validation | 1 | 1 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[라벨]validation_행정규칙_제개정문.zip | aihub_specialized_corpus | label | validation | 1 | 1 | 0 | include_for_parser_probe | skipped |
| 전문분야 말뭉치\Validation\[원천]전문분야_valid.zip | aihub_specialized_corpus | source | validation | 5 | 5 | 0 | include_for_parser_probe | skipped |

## Parser Probe Notes

Only key paths and type names are recorded. Raw text values are not recorded.

### 030.웹데이터 기반 한국어 말뭉치 데이터\01.데이터\1.Training\라벨링데이터\TL1.zip

- source_id: aihub_624_web_corpus
- recommended_action: include_for_context_extraction
- text_candidate_key_paths: named_entity[].content:list, named_entity[].content[].labels:list, named_entity[].content[].labels[]:list, named_entity[].content[].sentence:str, named_entity[].content[]:list, named_entity[].subtitle:list, named_entity[].subtitle[]:list, named_entity[].title:list, named_entity[].title[].labels:list, named_entity[].title[].labels[]:list, named_entity[].title[].sentence:str, named_entity[].title[]:list
- parser_probe_skipped_reason: none

### 030.웹데이터 기반 한국어 말뭉치 데이터\01.데이터\1.Training\원천데이터\TS1.zip

- source_id: aihub_624_web_corpus
- recommended_action: include_for_context_extraction
- text_candidate_key_paths: SJML.text:list, SJML.text[].board:str, SJML.text[].content:str, SJML.text[].source_site:str, SJML.text[].subtitle:str, SJML.text[].title:str, SJML.text[].url:str, SJML.text[].write_date:str, SJML.text[].writer:str, SJML.text[]:list
- parser_probe_skipped_reason: none

### 030.웹데이터 기반 한국어 말뭉치 데이터\01.데이터\2.Validation\라벨링데이터\VL1.zip

- source_id: aihub_624_web_corpus
- recommended_action: include_for_context_extraction
- text_candidate_key_paths: named_entity[].content:list, named_entity[].content[].labels:list, named_entity[].content[].labels[]:list, named_entity[].content[].sentence:str, named_entity[].content[]:list, named_entity[].subtitle:list, named_entity[].subtitle[]:list, named_entity[].title:list, named_entity[].title[].labels:list, named_entity[].title[].labels[]:list, named_entity[].title[].sentence:str, named_entity[].title[]:list
- parser_probe_skipped_reason: none

### 030.웹데이터 기반 한국어 말뭉치 데이터\01.데이터\2.Validation\원천데이터\VS1.zip

- source_id: aihub_624_web_corpus
- recommended_action: include_for_context_extraction
- text_candidate_key_paths: SJML.text:list, SJML.text[].board:str, SJML.text[].content:str, SJML.text[].source_site:str, SJML.text[].subtitle:str, SJML.text[].title:str, SJML.text[].url:str, SJML.text[].write_date:str, SJML.text[].writer:str, SJML.text[]:list
- parser_probe_skipped_reason: none

### 자유대화 음성(일반남녀)\Training\[라벨]1.AI챗봇.zip

- source_id: aihub_free_conversation_speech_labels
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: 발화정보.fileNm:str, 발화정보.recrdDt:str, 발화정보.recrdQuality:str, 발화정보.recrdTime:str, 발화정보.scriptId:str, 발화정보.scriptSetNo:str, 발화정보.stt:str, 발화정보:dict
- parser_probe_skipped_reason: none

### 자유대화 음성(일반남녀)\Training\[라벨]3.스튜디오.zip

- source_id: aihub_free_conversation_speech_labels
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: 발화정보.fileNm:str, 발화정보.recrdDt:str, 발화정보.recrdQuality:str, 발화정보.recrdTime:str, 발화정보.scriptId:str, 발화정보.scriptSetNo:str, 발화정보.stt:str, 발화정보:dict
- parser_probe_skipped_reason: none

### 자유대화 음성(일반남녀)\Validation\[라벨]1.AI챗봇.zip

- source_id: aihub_free_conversation_speech_labels
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: 발화정보.fileNm:str, 발화정보.recrdDt:str, 발화정보.recrdQuality:str, 발화정보.recrdTime:str, 발화정보.scriptId:str, 발화정보.scriptSetNo:str, 발화정보.stt:str, 발화정보:dict
- parser_probe_skipped_reason: none

### 자유대화 음성(일반남녀)\Validation\[라벨]3.스튜디오.zip

- source_id: aihub_free_conversation_speech_labels
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: 발화정보.fileNm:str, 발화정보.recrdDt:str, 발화정보.recrdQuality:str, 발화정보.recrdTime:str, 발화정보.scriptId:str, 발화정보.scriptSetNo:str, 발화정보.stt:str, 발화정보:dict
- parser_probe_skipped_reason: none

### 전문분야 말뭉치\Training\[라벨]training_논문.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Training\[라벨]training_법령제개정.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Training\[라벨]training_의안.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Training\[라벨]training_자치법규_제개정문.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Training\[라벨]training_자치법규_조례.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: none

### 전문분야 말뭉치\Training\[라벨]training_자치법규_행정규칙.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: data[].title:str
- parser_probe_skipped_reason: none

### 전문분야 말뭉치\Training\[라벨]training_특허.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Training\[라벨]training_판례.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Training\[라벨]training_행정규칙_제개정문.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Training\[원천]전문분야_train.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_논문.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_법령제개정.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_의안.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_자치법규_제개정문.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_자치법규_조례.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_자치법규_행정규칙.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_특허.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_판례.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[라벨]validation_행정규칙_제개정문.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit

### 전문분야 말뭉치\Validation\[원천]전문분야_valid.zip

- source_id: aihub_specialized_corpus
- recommended_action: include_for_parser_probe
- text_candidate_key_paths: none
- parser_probe_skipped_reason: no_small_json_entries_under_probe_limit
