"""Stable enum contracts for Korean PII Guardrail v0.2."""

from __future__ import annotations

from enum import StrEnum


class EntityType(StrEnum):
    RRN = "RRN"
    FRN = "FRN"
    PASSPORT = "PASSPORT"
    DRIVER_LICENSE = "DRIVER_LICENSE"
    PHONE_MOBILE = "PHONE_MOBILE"
    PHONE_LANDLINE = "PHONE_LANDLINE"
    EMAIL = "EMAIL"
    CREDIT_CARD = "CREDIT_CARD"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    BUSINESS_REG_NO = "BUSINESS_REG_NO"
    CORPORATE_REG_NO = "CORPORATE_REG_NO"
    VEHICLE_REG_NO = "VEHICLE_REG_NO"
    PERSON_NAME = "PERSON_NAME"
    ALIAS_HANDLE = "ALIAS_HANDLE"
    ADDRESS_FULL = "ADDRESS_FULL"
    ADDRESS_UNIT = "ADDRESS_UNIT"
    ORGANIZATION = "ORGANIZATION"
    SCHOOL = "SCHOOL"
    HOSPITAL = "HOSPITAL"
    DOB = "DOB"
    AGE = "AGE"
    GENDER = "GENDER"
    CUSTOMER_ID = "CUSTOMER_ID"
    EMPLOYEE_ID = "EMPLOYEE_ID"
    STUDENT_ID = "STUDENT_ID"
    MEDICAL_RECORD_NO = "MEDICAL_RECORD_NO"
    FAMILY_RELATION = "FAMILY_RELATION"
    HEALTH_INFO = "HEALTH_INFO"
    IP_ADDRESS = "IP_ADDRESS"
    MAC_ADDRESS = "MAC_ADDRESS"
    DEVICE_ID = "DEVICE_ID"
    API_KEY_SECRET = "API_KEY_SECRET"
    COMBINED_QUASI_ID = "COMBINED_QUASI_ID"


class RiskLevel(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Action(StrEnum):
    CANDIDATE = "candidate"
    PASS = "pass"
    MASK = "mask"
    PSEUDONYMIZE = "pseudonymize"
    HASH = "hash"
    REVIEW = "review"
    BLOCK = "block"


class ScanStage(StrEnum):
    INPUT = "input"
    OUTPUT = "output"


class OutputTarget(StrEnum):
    LLM_INPUT = "llm_input"
    EXTERNAL_OUTPUT = "external_output"
    INTERNAL_UI = "internal_ui"
    ANALYTICS = "analytics"
    AUDIT_LOG = "audit_log"


class Source(StrEnum):
    REGEX = "regex"
    VALIDATOR = "validator"
    DICTIONARY = "dictionary"
    NER = "ner"
    CONTEXT = "context"
    RESOLVER = "resolver"
    POLICY = "policy"
