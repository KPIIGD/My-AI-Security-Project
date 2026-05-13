import builtins
import re
import sys
import types

import pytest

from pii_guardrail.interfaces import TextVariant
from pii_guardrail.preprocess import NormalizationMapError, preprocess_text, restore_variant_span


def _variant(result, name: str) -> TextVariant:
    for variant in result.variants:
        if variant.name == name:
            return variant
    raise AssertionError(f"Missing variant {name}")


def _assert_variant_mapping_is_valid(raw: str, variant: TextVariant) -> None:
    assert len(variant.text) == len(variant.variant_to_raw)
    assert len(variant.text) == len(variant.variant_to_raw_span)
    for index, span in enumerate(variant.variant_to_raw_span):
        assert span is not None
        assert variant.variant_to_raw[index] == span[0]
        assert 0 <= span[0] < span[1] <= len(raw)
        assert restore_variant_span(variant, index, index + 1) == span


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


@pytest.mark.parametrize("dash", ["‐", "‑", "‒", "–", "—", "―", "−", "﹘", "﹣", "－"])
def test_dash_variants_normalize_and_restore_raw_span(dash: str) -> None:
    raw = f"010{dash}1234{dash}5678"
    result = preprocess_text(raw)
    normalized = _variant(result, "normalized")

    assert normalized.text == "010-1234-5678"
    raw_start, raw_end = restore_variant_span(normalized, 0, len(normalized.text))
    assert raw[raw_start:raw_end] == raw


def test_mathematical_and_circled_digits_normalize() -> None:
    raw = "𝟎𝟏𝟎 ①②③"
    result = preprocess_text(raw)

    assert result.normalized_text == "010 123"


def test_mathematical_and_circled_digits_restore_raw_span() -> None:
    raw = "𝟎𝟏𝟎 ①②③"
    result = preprocess_text(raw)
    normalized = _variant(result, "normalized")

    raw_start, raw_end = restore_variant_span(normalized, 0, len(normalized.text))
    assert raw[raw_start:raw_end] == raw


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


@pytest.mark.parametrize(
    ("variant", "start", "end"),
    [
        (TextVariant(name="bad", text="abc", variant_to_raw=(0, 1, 2), variant_to_raw_span=((0, 1), (1, 2), (2, 3))), -1, 1),
        (TextVariant(name="bad", text="abc", variant_to_raw=(0, 1, 2), variant_to_raw_span=((0, 1), (1, 2), (2, 3))), 1, 1),
        (TextVariant(name="bad", text="abc", variant_to_raw=(0,), variant_to_raw_span=((0, 1),)), 0, 1),
        (TextVariant(name="bad", text="abc", variant_to_raw=(0, 1, 2), variant_to_raw_span=((0, 1), (2, 2), (2, 3))), 1, 2),
    ],
)
def test_restore_variant_span_rejects_invalid_mapping_without_raw_value(
    variant: TextVariant,
    start: int,
    end: int,
) -> None:
    with pytest.raises(NormalizationMapError) as exc_info:
        restore_variant_span(variant, start, end)
    assert variant.text not in str(exc_info.value)


def test_restore_variant_span_supports_legacy_raw_index_mapping() -> None:
    variant = TextVariant(name="legacy", text="ab", variant_to_raw=(2, 3))

    assert restore_variant_span(variant, 0, 2) == (2, 4)


def test_digit_compact_variant_restores_phone_with_separators() -> None:
    raw = "연락처 010 - 1234 - 5678"
    result = preprocess_text(raw)
    variant = _variant(result, "digit_compact")

    assert "01012345678" in variant.text
    start = variant.text.index("01012345678")
    raw_start, raw_end = restore_variant_span(variant, start, start + len("01012345678"))
    assert raw[raw_start:raw_end] == "010 - 1234 - 5678"


def test_digit_space_compact_variant_restores_spaced_digits() -> None:
    raw = "9 0 0 1 0 1 - 1 2 3 4 5 6 8"
    result = preprocess_text(raw)
    variant = _variant(result, "digit_space_compact")

    assert "900101-1234568" in variant.text
    start = variant.text.index("900101")
    raw_start, raw_end = restore_variant_span(variant, start, start + len("900101"))
    assert raw[raw_start:raw_end] == "9 0 0 1 0 1"


def test_digit_space_compact_variant_restores_full_rrn_candidate() -> None:
    raw = "9 0 0 1 0 1 - 1 2 3 4 5 6 8"
    result = preprocess_text(raw)
    variant = _variant(result, "digit_space_compact")

    assert "900101-1234568" in variant.text
    start = variant.text.index("900101-1234568")
    raw_start, raw_end = restore_variant_span(variant, start, start + len("900101-1234568"))
    assert raw[raw_start:raw_end] == raw


def test_korean_keyword_spacing_variant_restores_keyword() -> None:
    raw = "주 민 번 호 900101-1234568"
    result = preprocess_text(raw)
    variant = _variant(result, "korean_keyword_spacing_compact")

    assert "주민번호" in variant.text
    start = variant.text.index("주민번호")
    raw_start, raw_end = restore_variant_span(variant, start, start + len("주민번호"))
    assert raw[raw_start:raw_end] == "주 민 번 호"


@pytest.mark.parametrize(
    ("raw", "variant_name", "needle", "expected_raw"),
    [
        ("ㅈㅜㅁㅣㄴ번호 900101-1234568", "jamo_composed", "주민번호", "ㅈㅜㅁㅣㄴ번호"),
        ("ㅈㅁㅂㅎ는 900101-1234568", "choseong_restored", "주민번호", "ㅈㅁㅂㅎ"),
        ("즈민뜽록볜훟 900101-1234568", "yamin_restored", "주민등록번호", "즈민뜽록볜훟"),
        ("jumin beonho 900101-1234568", "romanized_restored", "주민번호", "jumin beonho"),
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


def test_all_generated_variants_have_complete_restorable_raw_mapping() -> None:
    raw = "😊 ０１０－１２３４－５６７８ ㅈㅁㅂㅎ jumin beonho 즈민뜽록볜훟 연락처는 공일공 일이삼사"
    result = preprocess_text(raw)

    for variant in result.variants:
        _assert_variant_mapping_is_valid(raw, variant)
        raw_start, raw_end = restore_variant_span(variant, 0, len(variant.text))
        assert (raw_start, raw_end) == (0, len(raw))


def test_normalization_maps_are_internally_consistent() -> None:
    raw = "A\u200bＢ①—😊"
    result = preprocess_text(raw)

    assert result.normalized_text == "AB1-😊"
    assert len(result.raw_to_norm) == len(raw)
    assert len(result.norm_to_raw) == len(result.normalized_text)
    for raw_index, norm_index in enumerate(result.raw_to_norm):
        if norm_index is None:
            continue
        assert result.norm_to_raw[norm_index] == raw_index


def test_sentence_and_eojeol_spans_are_raw_offsets() -> None:
    raw = " 첫 문장입니다. 둘째 문장입니다?\n셋째"
    result = preprocess_text(raw)

    for span in (*result.sentences, *result.eojeols):
        assert 0 <= span.start < span.end <= len(raw)
        assert span.text == raw[span.start : span.end]


def test_use_kiwi_falls_back_when_dependency_is_missing_or_unavailable() -> None:
    result = preprocess_text("홍길동이 신청했습니다.", use_kiwi=True)

    assert result.sentences
    assert result.eojeols


def test_use_kiwi_import_failure_falls_back_to_default_splitters(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "kiwipiepy":
            raise ImportError("kiwi intentionally unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    raw = "홍길동이 신청했습니다. 김민수에게 연락하세요."
    result = preprocess_text(raw, use_kiwi=True)

    assert [sentence.text for sentence in result.sentences] == ["홍길동이 신청했습니다.", "김민수에게 연락하세요."]
    assert [token.text for token in result.eojeols] == ["홍길동이", "신청했습니다.", "김민수에게", "연락하세요."]


def test_use_kiwi_runtime_failure_falls_back_to_default_splitters(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenKiwi:
        def __init__(self) -> None:
            raise RuntimeError("kiwi intentionally unavailable")

    fake_module = types.ModuleType("kiwipiepy")
    fake_module.Kiwi = BrokenKiwi
    monkeypatch.setitem(sys.modules, "kiwipiepy", fake_module)
    raw = "홍길동이 신청했습니다."
    result = preprocess_text(raw, use_kiwi=True)

    assert [sentence.text for sentence in result.sentences] == ["홍길동이 신청했습니다."]
    assert [token.text for token in result.eojeols] == ["홍길동이", "신청했습니다."]


def test_use_kiwi_accepts_text_sentences_and_length_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSentence:
        text = "김민수에게 연락하세요."
        start = None
        end = None

    class FakeToken:
        start = 0
        length = 4

    class FakeKiwi:
        def split_into_sents(self, raw_text: str) -> list[FakeSentence]:
            return [FakeSentence()]

        def tokenize(self, raw_text: str) -> list[FakeToken]:
            return [FakeToken()]

    fake_module = types.ModuleType("kiwipiepy")
    fake_module.Kiwi = FakeKiwi
    monkeypatch.setitem(sys.modules, "kiwipiepy", fake_module)
    raw = "김민수에게 연락하세요."
    result = preprocess_text(raw, use_kiwi=True)

    assert [sentence.text for sentence in result.sentences] == [raw]
    assert result.eojeols[0].text == raw[:4]


def test_use_kiwi_reuses_cached_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    init_count = 0

    class FakeKiwi:
        def __init__(self) -> None:
            nonlocal init_count
            init_count += 1

        def split_into_sents(self, raw_text: str) -> list[object]:
            return []

        def tokenize(self, raw_text: str) -> list[object]:
            return []

    fake_module = types.ModuleType("kiwipiepy")
    fake_module.Kiwi = FakeKiwi
    monkeypatch.setitem(sys.modules, "kiwipiepy", fake_module)

    preprocess_text("홍길동이 신청했습니다.", use_kiwi=True)
    preprocess_text("김민수에게 연락하세요.", use_kiwi=True)

    assert init_count == 1


def test_use_kiwi_does_not_change_normalized_text() -> None:
    raw = "주 민 번 호 ９００１０１－１２３４５６７"

    assert preprocess_text(raw, use_kiwi=True).normalized_text == preprocess_text(raw, use_kiwi=False).normalized_text


def test_variant_restore_for_regex_match_keeps_raw_contract() -> None:
    raw = "010\u200b-1234\u200b-5678"
    result = preprocess_text(raw)
    normalized = _variant(result, "normalized")
    match = re.search(r"010-1234-5678", normalized.text)
    assert match is not None

    raw_start, raw_end = restore_variant_span(normalized, match.start(), match.end())
    assert raw[raw_start:raw_end] == raw
