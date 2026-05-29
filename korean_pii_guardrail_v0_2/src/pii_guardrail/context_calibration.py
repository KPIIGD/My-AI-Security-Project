"""Build synthetic context calibration datasets for M4 evidence.

The generated cases use synthetic values only. Public context coverage from
Phase 2 informs template categories, but the emitted train/dev/test datasets
contain controlled templates with known raw offsets and expected masks.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .enums import EntityType, RiskLevel
from .evaluation_harness import EvaluationCase, load_jsonl_cases


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_VERSION = "context_calibration_v1"
SPLITS = ("train", "dev", "test")
KNOWN_SUFFIXES = (
    "입니다",
    "에게",
    "에서",
    "으로",
    "로",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "와",
    "과",
    "님",
    "씨",
)


@dataclass(frozen=True)
class SyntheticSpan:
    value: str
    entity_type: EntityType
    risk_level: RiskLevel
    placeholder: str
    suffix: str | None = None


@dataclass(frozen=True)
class TemplateSpec:
    template_id: str
    domain: str
    bucket: str
    split: str
    template: str
    spans: tuple[SyntheticSpan, ...]
    tags: tuple[str, ...]
    source_anchor_terms: tuple[str, ...]


def build_context_calibration_records() -> dict[str, list[dict[str, Any]]]:
    """Build split records with template-level isolation."""

    records_by_split: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    seen_templates: set[str] = set()
    for spec in _template_specs():
        if spec.split not in records_by_split:
            raise ValueError("Unsupported split")
        if spec.template_id in seen_templates:
            raise ValueError("Duplicate template_id")
        seen_templates.add(spec.template_id)
        records_by_split[spec.split].append(_compile_template(spec))
    return records_by_split


def write_context_calibration_datasets(
    output_dir: Path,
) -> tuple[dict[str, list[dict[str, Any]]], list[Path]]:
    records_by_split = build_context_calibration_records()
    paths: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for split, records in records_by_split.items():
        path = output_dir / f"{DATASET_VERSION}_{split}.jsonl"
        _write_jsonl(records, path)
        paths.append(path)
    return records_by_split, paths


def validate_context_calibration_records(
    records_by_split: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    validation_errors: list[dict[str, Any]] = []
    template_by_id: dict[str, str] = {}
    split_by_template_fingerprint: dict[str, str] = {}
    label_counts: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    raw_pii_safety = {
        "raw_value_logged_count": 0,
        "synthetic_fixture_only": True,
        "production_pii_used": False,
    }

    for split, records in records_by_split.items():
        split_counts[split] += len(records)
        for record in records:
            case_id = record["id"]
            text = record["text"]
            template_id = record["template_id"]
            template_fingerprint = record["template_fingerprint"]
            if template_id in template_by_id:
                validation_errors.append(
                    {
                        "case_id": case_id,
                        "error_type": "duplicate_template_id",
                        "template_id": template_id,
                    }
                )
            template_by_id[template_id] = template_fingerprint
            previous_split = split_by_template_fingerprint.get(template_fingerprint)
            if previous_split is not None and previous_split != split:
                validation_errors.append(
                    {
                        "case_id": case_id,
                        "error_type": "template_split_leakage",
                        "template_id": template_id,
                    }
                )
            split_by_template_fingerprint[template_fingerprint] = split
            if record.get("raw_value_logged"):
                raw_pii_safety["raw_value_logged_count"] += 1
            bucket_counts[record["bucket"]] += 1
            for label in record["labels"]:
                start = int(label["start"])
                end = int(label["end"])
                if start < 0 or end > len(text) or start >= end:
                    validation_errors.append(
                        {
                            "case_id": case_id,
                            "error_type": "offset_invalid",
                            "entity_type": label["entity_type"],
                        }
                    )
                    continue
                suffix = label.get("suffix")
                required_suffix = _required_suffix_after(text, end)
                if suffix:
                    suffix_start = end
                    suffix_end = end + len(suffix)
                    if text[suffix_start:suffix_end] != suffix:
                        validation_errors.append(
                            {
                                "case_id": case_id,
                                "error_type": "suffix_mismatch",
                                "entity_type": label["entity_type"],
                            }
                        )
                    elif required_suffix and suffix != required_suffix:
                        validation_errors.append(
                            {
                                "case_id": case_id,
                                "error_type": "suffix_mismatch",
                                "entity_type": label["entity_type"],
                            }
                        )
                elif required_suffix:
                    validation_errors.append(
                        {
                            "case_id": case_id,
                            "error_type": "suffix_missing",
                            "entity_type": label["entity_type"],
                        }
                    )
                label_counts[label["entity_type"]] += 1
            if _expected_masked_text(record) != record["expected_masked_text"]:
                validation_errors.append(
                    {
                        "case_id": case_id,
                        "error_type": "expected_masked_text_mismatch",
                    }
                )

    return {
        "status": "pass" if not validation_errors else "fail",
        "version": "v0.2-single-turn",
        "dataset_id": DATASET_VERSION,
        "split_counts": dict(sorted(split_counts.items())),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "template_level_split": "fail"
        if any(
            err["error_type"] in {"duplicate_template_id", "template_split_leakage"}
            for err in validation_errors
        )
        else "pass",
        "offset_validation_error_count": len(
            [
                err
                for err in validation_errors
                if err["error_type"] in {"offset_invalid", "expected_masked_text_mismatch"}
            ]
        ),
        "suffix_validation_error_count": len(
            [
                err
                for err in validation_errors
                if err["error_type"] in {"suffix_missing", "suffix_mismatch"}
            ]
        ),
        "expected_masked_text_error_count": len(
            [
                err
                for err in validation_errors
                if err["error_type"] == "expected_masked_text_mismatch"
            ]
        ),
        "validation_errors": validation_errors,
        "raw_pii_safety": raw_pii_safety,
        "generated_at": _now(),
    }


def build_dataset_card(
    records_by_split: dict[str, list[dict[str, Any]]],
    validation: dict[str, Any],
) -> str:
    lines = [
        "# Context Calibration Dataset Card v1",
        "",
        "- dataset_id: `context_calibration_v1`",
        "- phase: `Execution Phase 3. Calibration Dataset`",
        "- synthetic_fixture_only: `true`",
        "- public_context_corpus_role: `template coverage only, not score tuning`",
        "- template_level_split: `{}`".format(validation["template_level_split"]),
        "- offset_validation_status: `{}`".format(validation["status"]),
        "",
        "## Split Counts",
        "",
        "| Split | Records |",
        "|---|---:|",
    ]
    for split in SPLITS:
        lines.append(f"| {split} | {len(records_by_split.get(split, []))} |")

    lines.extend(["", "## Bucket Counts", "", "| Bucket | Records |", "|---|---:|"])
    for bucket, count in validation["bucket_counts"].items():
        lines.append(f"| {bucket} | {count} |")

    lines.extend(["", "## Label Counts", "", "| Entity | Labels |", "|---|---:|"])
    for entity, count in validation["label_counts"].items():
        lines.append(f"| {entity} | {count} |")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- raw_value_logged_count: `{}`".format(
                validation["raw_pii_safety"]["raw_value_logged_count"]
            ),
            "- production_pii_used: `false`",
            "- offset_validation_error_count: `{}`".format(
                validation["offset_validation_error_count"]
            ),
            "- suffix_validation_error_count: `{}`".format(
                validation["suffix_validation_error_count"]
            ),
            "",
            "Train/dev/test are split by template_id; near-duplicate template ids are not shared across splits.",
            "Positive and hard-negative buckets cover names, public numbers, placeholders, code/log contexts, business names, abstract-value contexts, structured identifiers, and address/account/contact contexts.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_dataset_safety_report(validation: dict[str, Any]) -> dict[str, Any]:
    safety = validation["raw_pii_safety"]
    status = (
        "pass"
        if validation["status"] == "pass"
        and safety["raw_value_logged_count"] == 0
        and not safety["production_pii_used"]
        else "fail"
    )
    reason_codes = ["context_calibration.safety.pass"] if status == "pass" else []
    if validation["status"] != "pass":
        reason_codes.append("context_calibration.validation.fail")
    if safety["raw_value_logged_count"]:
        reason_codes.append("context_calibration.raw_value_logged.fail")
    if safety["production_pii_used"]:
        reason_codes.append("context_calibration.production_pii_used.fail")
    return {
        "report_type": "ContextCalibrationDatasetSafetyReport",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 3. Calibration Dataset",
        "dataset_id": DATASET_VERSION,
        "status": status,
        "reason_codes": reason_codes,
        "split_counts": validation["split_counts"],
        "bucket_counts": validation["bucket_counts"],
        "label_counts": validation["label_counts"],
        "offset_validation_error_count": validation["offset_validation_error_count"],
        "suffix_validation_error_count": validation["suffix_validation_error_count"],
        "expected_masked_text_error_count": validation[
            "expected_masked_text_error_count"
        ],
        "raw_value_logged_count": safety["raw_value_logged_count"],
        "synthetic_fixture_only": safety["synthetic_fixture_only"],
        "production_pii_used": safety["production_pii_used"],
        "template_level_split": validation["template_level_split"],
        "generated_at": _now(),
    }


def load_generated_context_calibration_cases(
    data_dir: Path,
) -> dict[str, list[EvaluationCase]]:
    return {
        split: load_jsonl_cases(data_dir / f"{DATASET_VERSION}_{split}.jsonl")
        for split in SPLITS
    }


def _compile_template(spec: TemplateSpec) -> dict[str, Any]:
    text = spec.template
    labels: list[dict[str, Any]] = []
    expected_masked_text = spec.template
    for index, span in enumerate(spec.spans, start=1):
        token = f"{{value{index}}}"
        if token not in text:
            raise ValueError(f"template_id={spec.template_id} missing token {token}")
        start = text.index(token)
        text = text.replace(token, span.value, 1)
        expected_masked_text = expected_masked_text.replace(token, span.placeholder, 1)
        labels.append(
            {
                "start": start,
                "end": start + len(span.value),
                "entity_type": span.entity_type.value,
                "risk_level": span.risk_level.value,
                "suffix": span.suffix,
            }
        )
    case_id = f"{DATASET_VERSION}-{spec.split}-{spec.template_id}"
    return {
        "id": case_id,
        "text": text,
        "expected_masked_text": expected_masked_text,
        "labels": labels,
        "tags": list(spec.tags),
        "split": spec.split,
        "bucket": spec.bucket,
        "domain": spec.domain,
        "template_id": spec.template_id,
        "template_fingerprint": _template_fingerprint(spec.template),
        "source_anchor_terms": list(spec.source_anchor_terms),
        "synthetic_fixture": True,
        "raw_value_logged": False,
    }


def _expected_masked_text(record: dict[str, Any]) -> str:
    text = record["text"]
    labels = sorted(record["labels"], key=lambda item: item["start"])
    result: list[str] = []
    cursor = 0
    family_counts: Counter[str] = Counter()
    for label in labels:
        start = int(label["start"])
        end = int(label["end"])
        entity = EntityType(label["entity_type"])
        family = _entity_family(entity)
        family_counts[family] += 1
        result.append(text[cursor:start])
        result.append(f"[{family}_{family_counts[family]}]")
        cursor = end
    result.append(text[cursor:])
    return "".join(result)


def _template_specs() -> tuple[TemplateSpec, ...]:
    return tuple(
        spec
        for split_index, split in enumerate(SPLITS)
        for spec in _template_specs_for_split(split, split_index)
    )


def _template_specs_for_split(split: str, split_index: int) -> tuple[TemplateSpec, ...]:
    names = ("김도윤", "이서연", "박지훈")
    second_names = ("한유진", "최민준", "정하늘")
    phones = ("010-2345-6789", "010-3456-7890", "010-4567-8901")
    addresses = (
        "서울시 강남구 테헤란로 123 101동 1203호",
        "부산시 해운대구 해운대로 55 202동 303호",
        "대구시 수성구 달구벌대로 77 5층",
    )
    accounts = ("110-234-567890", "220-345-678901", "330-456-789012")
    emails = (
        "applicant01@example.test",
        "student02@example.test",
        "member03@example.test",
    )
    medical_numbers = ("PT-2026-0001", "MR-2026-0002", "CH-2026-0003")
    hospitals = ("서울중앙병원", "한국테스트병원", "도시건강병원")
    organizations = ("한국테스트연구소", "미래샘플주식회사", "도시데모센터")
    business_numbers = ("123-45-67891", "234-56-78912", "345-67-89123")
    rrns = ("900101-1234568", "910202-2345679", "920303-3456780")

    name = names[split_index]
    second_name = second_names[split_index]
    phone = phones[split_index]
    address = addresses[split_index]
    account = accounts[split_index]
    email = emails[split_index]
    medical_number = medical_numbers[split_index]
    hospital = hospitals[split_index]
    organization = organizations[split_index]
    business_number = business_numbers[split_index]
    rrn = rrns[split_index]

    wording = {
        "train": {
            "ship": "수령인",
            "phone_suffix": "로",
            "address_label": "배송지 주소는",
            "address_suffix": "로",
            "account_label": "환불계좌",
            "email_label": "신청자 이메일",
            "email_suffix": "로",
            "name_suffix": "님",
            "business_suffix": "는",
            "rrn_suffix": "은",
        },
        "dev": {
            "ship": "예약자",
            "phone_suffix": "으로",
            "address_label": "방문 주소는",
            "address_suffix": "에",
            "account_label": "정산 계좌",
            "email_label": "접수 이메일",
            "email_suffix": "로",
            "name_suffix": "에게",
            "business_suffix": "를",
            "rrn_suffix": "을",
        },
        "test": {
            "ship": "문의자",
            "phone_suffix": "로",
            "address_label": "거주지 주소는",
            "address_suffix": "에",
            "account_label": "입금계좌",
            "email_label": "회신 이메일",
            "email_suffix": "로",
            "name_suffix": "씨",
            "business_suffix": "은",
            "rrn_suffix": "는",
        },
    }[split]

    return (
        TemplateSpec(
            f"{split}_ecom_name_phone_001",
            "ecommerce",
            "positive_person_phone",
            split,
            f"{wording['ship']} {{value1}}, 연락처 {{value2}}{wording['phone_suffix']} 배송 안내를 보냅니다.",
            (
                SyntheticSpan(name, EntityType.PERSON_NAME, RiskLevel.P1, "[PERSON_1]"),
                SyntheticSpan(phone, EntityType.PHONE_MOBILE, RiskLevel.P1, "[PHONE_1]", suffix=wording["phone_suffix"]),
            ),
            ("context_calibration", "positive", "person_phone"),
            ("field:name_label", "field:phone_label"),
        ),
        TemplateSpec(
            f"{split}_ecom_address_001",
            "ecommerce",
            "positive_address",
            split,
            f"{wording['address_label']} {{value1}}{wording['address_suffix']} 입력합니다.",
            (
                SyntheticSpan(address, EntityType.ADDRESS_FULL, RiskLevel.P1, "[ADDRESS_1]", suffix=wording["address_suffix"]),
            ),
            ("context_calibration", "positive", "address"),
            ("field:address_label",),
        ),
        TemplateSpec(
            f"{split}_ecom_public_phone_001",
            "ecommerce",
            "hard_negative_public_number",
            split,
            (
                "고객센터 대표번호는 안내용 대표 회선입니다.",
                "콜센터 안내번호는 공개 상담 창구입니다.",
                "공공기관 안내번호는 민원 안내용 번호입니다.",
            )[split_index],
            (),
            ("context_calibration", "hard_negative", "public_number"),
            ("negative:public_number_context",),
        ),
        TemplateSpec(
            f"{split}_finance_account_001",
            "finance",
            "positive_bank_account",
            split,
            f"{wording['account_label']} {{value1}}로 입금 처리합니다.",
            (
                SyntheticSpan(account, EntityType.BANK_ACCOUNT, RiskLevel.P1, "[BANK_ACCOUNT_1]", suffix="로"),
            ),
            ("context_calibration", "positive", "bank_account"),
            ("field:account_label", "structured:account_label"),
        ),
        TemplateSpec(
            f"{split}_finance_order_id_001",
            "finance",
            "hard_negative_order_identifier",
            split,
            (
                "결제번호는 주문 상태 확인용 번호입니다.",
                "송장번호는 배송 조회 전용 식별자입니다.",
                "예약번호는 방문 일정 확인용 코드입니다.",
            )[split_index],
            (),
            ("context_calibration", "hard_negative", "order_identifier"),
            ("structured:order_id_label",),
        ),
        TemplateSpec(
            f"{split}_health_medical_001",
            "healthcare",
            "positive_medical",
            split,
            (
                "환자번호 {value1}, 병원 {value2}에서 진료기록을 확인합니다.",
                "차트번호 {value1}, 병원 {value2}에서 의무기록을 조회합니다.",
                "진료기록번호 {value1}, 병원 {value2}에서 접수 내역을 발급합니다.",
            )[split_index],
            (
                SyntheticSpan(medical_number, EntityType.MEDICAL_RECORD_NO, RiskLevel.P1, "[MEDICAL_RECORD_NO_1]"),
                SyntheticSpan(hospital, EntityType.HOSPITAL, RiskLevel.P2, "[HOSPITAL_1]", suffix="에서"),
            ),
            ("context_calibration", "positive", "medical"),
            ("field:medical_label",),
        ),
        TemplateSpec(
            f"{split}_education_student_001",
            "education",
            "positive_email",
            split,
            f"{wording['email_label']} {{value1}}{wording['email_suffix']} 접수 결과를 발송합니다.",
            (
                SyntheticSpan(email, EntityType.EMAIL, RiskLevel.P1, "[EMAIL_1]", suffix=wording["email_suffix"]),
            ),
            ("context_calibration", "positive", "email"),
            ("field:email_label", "field:name_label"),
        ),
        TemplateSpec(
            f"{split}_education_placeholder_001",
            "education",
            "hard_negative_placeholder",
            split,
            (
                "예시 이메일은 양식 설명용 placeholder입니다.",
                "샘플 메일 주소는 교육 자료에서만 사용합니다.",
                "테스트 전자우편 항목은 fixture 설명입니다.",
            )[split_index],
            (),
            ("context_calibration", "hard_negative", "placeholder"),
            ("negative:example_context",),
        ),
        TemplateSpec(
            f"{split}_developer_code_001",
            "developer_docs",
            "hard_negative_code_log",
            split,
            (
                "debug 변수명 user_name과 address_line은 JSON key 예시입니다.",
                "로그 컬럼명 contact_value는 stack trace 설명입니다.",
                "클래스 필드 addressLine은 테스트 fixture입니다.",
            )[split_index],
            (),
            ("context_calibration", "hard_negative", "code_log"),
            ("negative:code_context", "negative:example_context"),
        ),
        TemplateSpec(
            f"{split}_generic_abstract_001",
            "generic",
            "hard_negative_abstract_value",
            split,
            ("사랑은 중요한 가치입니다.", "믿음은 중요한 원칙입니다.", "가을은 개념입니다.")[split_index],
            (),
            ("context_calibration", "hard_negative", "abstract_value"),
            ("negative:abstract_value_context",),
        ),
        TemplateSpec(
            f"{split}_generic_business_name_001",
            "generic",
            "hard_negative_business_name",
            split,
            ("상호 하늘카페 오픈 안내입니다.", "브랜드 민수식당 공지입니다.", "상품명 서연팀 패키지입니다.")[split_index],
            (),
            ("context_calibration", "hard_negative", "business_name"),
            ("negative:business_name_context",),
        ),
        TemplateSpec(
            f"{split}_generic_name_suffix_001",
            "generic",
            "positive_name_suffix",
            split,
            f"담당자 {{value1}}{wording['name_suffix']} 전달했습니다.",
            (
                SyntheticSpan(second_name, EntityType.PERSON_NAME, RiskLevel.P1, "[PERSON_1]", suffix=wording["name_suffix"]),
            ),
            ("context_calibration", "positive", "suffix"),
            ("field:name_label",),
        ),
        TemplateSpec(
            f"{split}_enterprise_org_001",
            "enterprise_internal",
            "positive_organization_affiliation",
            split,
            (
                "{value1} 소속 담당자 {value2}에게 문의하세요.",
                "{value1} 근무 담당자 {value2}에게 연락하세요.",
                "{value1} 재직 담당자 {value2}에게 확인하세요.",
            )[split_index],
            (
                SyntheticSpan(organization, EntityType.ORGANIZATION, RiskLevel.P2, "[ORGANIZATION_1]"),
                SyntheticSpan(name, EntityType.PERSON_NAME, RiskLevel.P1, "[PERSON_1]", suffix="에게"),
            ),
            ("context_calibration", "positive", "organization_affiliation"),
            ("field:organization_label", "field:name_label"),
        ),
        TemplateSpec(
            f"{split}_institution_business_id_001",
            "institution_application",
            "positive_business_identifier",
            split,
            f"사업자등록번호 {{value1}}{wording['business_suffix']} 신청서에 기재합니다.",
            (
                SyntheticSpan(business_number, EntityType.BUSINESS_REG_NO, RiskLevel.P1, "[BUSINESS_REG_NO_1]", suffix=wording["business_suffix"]),
            ),
            ("context_calibration", "positive", "business_identifier"),
            ("structured:business_reg_no_label",),
        ),
        TemplateSpec(
            f"{split}_institution_rrn_label_001",
            "institution_application",
            "positive_personal_identifier",
            split,
            f"주민등록번호 {{value1}}{wording['rrn_suffix']} 본인확인 항목입니다.",
            (
                SyntheticSpan(rrn, EntityType.RRN, RiskLevel.P0, "[ID_1]", suffix=wording["rrn_suffix"]),
            ),
            ("context_calibration", "positive", "personal_identifier"),
            ("structured:personal_reg_no_label",),
        ),
    )


def _template_fingerprint(template: str) -> str:
    normalized = re.sub(r"\{value\d+\}", "{value}", template)
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _entity_family(entity_type: EntityType) -> str:
    if entity_type is EntityType.PERSON_NAME:
        return "PERSON"
    if entity_type in {EntityType.PHONE_MOBILE, EntityType.PHONE_LANDLINE}:
        return "PHONE"
    if entity_type in {EntityType.ADDRESS_FULL, EntityType.ADDRESS_UNIT}:
        return "ADDRESS"
    if entity_type in {EntityType.RRN, EntityType.FRN, EntityType.PASSPORT, EntityType.DRIVER_LICENSE}:
        return "ID"
    return entity_type.value


def _required_suffix_after(text: str, end: int) -> str | None:
    right = text[end:]
    for suffix in KNOWN_SUFFIXES:
        if right.startswith(suffix):
            return suffix
    return None


def _write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()
