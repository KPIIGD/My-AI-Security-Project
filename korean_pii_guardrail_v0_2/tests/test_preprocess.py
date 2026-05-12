import re

import pytest

from pii_guardrail.interfaces import TextVariant
from pii_guardrail.preprocess import NormalizationMapError, preprocess_text, restore_variant_span


def _variant(result, name: str) -> TextVariant:
    for variant in result.variants:
        if variant.name == name:
            return variant
    raise AssertionError(f"Missing variant {name}")


def test_preprocess_preserves_clean_korean_text() -> None:
    result = preprocess_text("안녕하세요. 오늘 날씨가 좋습니다.")

    assert result.normalized_text == "안녕하세요. 오늘 날씨가 좋습니다."
    assert result.raw_to_norm[0] == 0
    assert result.norm_to_raw[0] == 0
    assert result.sentences[0].text == "안녕하세요."
    assert [token.text for token in result.eojeols] == ["안녕하세요.", "오늘", "날씨가", "좋습니다."]


def test_zero_width_phone_restores_raw_span() -> None:
    raw = "010\u200b-1234\u200b-5678"
    result = preprocess_text(raw)
    normalized = _variant(result, "normalized")

    assert result.normalized_text == "010-1234-5678"
    start = normalized.text.index("010-1234-5678")
    raw_start, raw_end = restore_variant_span(normalized, start, start + len("010-1234-5678"))
    assert (raw_start, raw_end) == (0, 15)
    assert raw[raw_start:raw_end] == raw


def test_soft_hyphen_is_removed_without_mapping_leak() -> None:
    raw = "계\u00ad좌\u00ad번호"
    result = preprocess_text(raw)

    assert result.normalized_text == "계좌번호"
    assert "\u00ad" not in result.normalized_text
    assert result.raw_to_norm[1] is None
    assert result.raw_to_norm[3] is None


def test_fullwidth_digits_and_dash_restore_original_span() -> None:
    raw = "０１０－１２３４－５６７８"
    result = preprocess_text(raw)
    normalized = _variant(result, "normalized")

    assert result.normalized_text == "010-1234-5678"
    raw_start, raw_end = restore_variant_span(normalized, 0, len(normalized.text))
    assert raw[raw_start:raw_end] == raw


def test_mathematical_and_circled_digits_normalize() -> None:
    raw = "𝟎𝟏𝟎 ①②③"
    result = preprocess_text(raw)

    assert result.normalized_text == "010 123"


def test_emoji_does_not_shift_offsets() -> None:
    raw = "안녕하세요 😊 010-1234-5678입니다."
    result = preprocess_text(raw)
    normalized = _variant(result, "normalized")
    start = normalized.text.index("010-1234-5678")
    raw_start, raw_end = restore_variant_span(normalized, start, start + len("010-1234-5678"))

    assert raw[raw_start:raw_end] == "010-1234-5678"


def test_restore_variant_span_rejects_unmapped_span_without_raw_value() -> None:
    variant = TextVariant(
        name="bad",
        text="abc",
        variant_to_raw=(0, None, 2),
        variant_to_raw_span=((0, 1), None, (2, 3)),
    )

    with pytest.raises(NormalizationMapError) as exc_info:
        restore_variant_span(variant, 0, 2)
    assert "abc" not in str(exc_info.value)


def test_digit_compact_variant_restores_phone_with_separators() -> None:
    raw = "연락처 010 - 1234 - 5678"
    result = preprocess_text(raw)
    variant = _variant(result, "digit_compact")

    assert "01012345678" in variant.text
    start = variant.text.index("01012345678")
    raw_start, raw_end = restore_variant_span(variant, start, start + len("01012345678"))
    assert raw[raw_start:raw_end] == "010 - 1234 - 5678"


def test_digit_space_compact_variant_restores_spaced_digits() -> None:
    raw = "9 0 0 1 0 1 - 1 2 3 4 5 6 7"
    result = preprocess_text(raw)
    variant = _variant(result, "digit_space_compact")

    assert "900101-1234567" in variant.text
    start = variant.text.index("900101")
    raw_start, raw_end = restore_variant_span(variant, start, start + len("900101"))
    assert raw[raw_start:raw_end] == "9 0 0 1 0 1"


def test_korean_keyword_spacing_variant_restores_keyword() -> None:
    raw = "주 민 번 호 900101-1234567"
    result = preprocess_text(raw)
    variant = _variant(result, "korean_keyword_spacing_compact")

    assert "주민번호" in variant.text
    start = variant.text.index("주민번호")
    raw_start, raw_end = restore_variant_span(variant, start, start + len("주민번호"))
    assert raw[raw_start:raw_end] == "주 민 번 호"


@pytest.mark.parametrize(
    ("raw", "variant_name", "needle", "expected_raw"),
    [
        ("ㅈㅜㅁㅣㄴ번호 900101-1234567", "jamo_composed", "주민번호", "ㅈㅜㅁㅣㄴ번호"),
        ("ㅈㅁㅂㅎ는 900101-1234567", "choseong_restored", "주민번호", "ㅈㅁㅂㅎ"),
        ("즈민뜽록볜훟 900101-1234567", "yamin_restored", "주민등록번호", "즈민뜽록볜훟"),
        ("jumin beonho 900101-1234567", "romanized_restored", "주민번호", "jumin beonho"),
    ],
)
def test_l0_derived_text_variants_restore_raw_span(
    raw: str,
    variant_name: str,
    needle: str,
    expected_raw: str,
) -> None:
    result = preprocess_text(raw)
    variant = _variant(result, variant_name)

    assert needle in variant.text
    start = variant.text.index(needle)
    raw_start, raw_end = restore_variant_span(variant, start, start + len(needle))
    assert raw[raw_start:raw_end] == expected_raw


def test_korean_digit_variant_requires_context_and_restores_raw_span() -> None:
    raw = "연락처는 공일공 일이삼사 오육칠팔입니다."
    result = preprocess_text(raw)
    variant = _variant(result, "korean_digit_restored")

    assert "01012345678" in variant.text
    start = variant.text.index("01012345678")
    raw_start, raw_end = restore_variant_span(variant, start, start + len("01012345678"))
    assert raw[raw_start:raw_end] == "공일공 일이삼사 오육칠팔"


def test_korean_digit_variant_does_not_convert_without_context() -> None:
    raw = "오늘은 일이 많습니다."
    result = preprocess_text(raw)
    variant = _variant(result, "korean_digit_restored")

    assert variant.text == raw


def test_use_kiwi_falls_back_when_dependency_is_missing_or_unavailable() -> None:
    result = preprocess_text("홍길동이 신청했습니다.", use_kiwi=True)

    assert result.sentences
    assert result.eojeols


def test_variant_restore_for_regex_match_keeps_raw_contract() -> None:
    raw = "010\u200b-1234\u200b-5678"
    result = preprocess_text(raw)
    normalized = _variant(result, "normalized")
    match = re.search(r"010-1234-5678", normalized.text)
    assert match is not None

    raw_start, raw_end = restore_variant_span(normalized, match.start(), match.end())
    assert raw[raw_start:raw_end] == raw
