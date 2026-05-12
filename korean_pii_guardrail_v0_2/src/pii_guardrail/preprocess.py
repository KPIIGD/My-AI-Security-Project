"""Offset-aware preprocessing for Korean PII Guardrail v0.2.

This module intentionally does not import the older Layer 0 implementation. It
reimplements the needed variant strategy around the v0.2 raw-offset contract.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from .interfaces import PreprocessResult, SentenceSpan, TextVariant, TokenSpan


class NormalizationMapError(ValueError):
    """Raised when a variant span cannot be restored to a raw text span."""


INVISIBLE_CHARS = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u2060",  # WORD JOINER
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE
    "\u00ad",  # SOFT HYPHEN
    "\u180e",  # MONGOLIAN VOWEL SEPARATOR
    "\u034f",  # COMBINING GRAPHEME JOINER
    "\u2061",
    "\u2062",
    "\u2063",
    "\u2064",
}

DASH_CHARS = {
    "\u2010",
    "\u2011",
    "\u2012",
    "\u2013",
    "\u2014",
    "\u2015",
    "\u2212",
    "\ufe58",
    "\ufe63",
    "\uff0d",
}

DIGIT_SEPARATORS = {"-", ".", "/", "_", " ", "\t", "\n", "\r"}

CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNGSEONG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONGSEONG = "ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"

CHOSEONG_RESTORE = {
    "ㅈㅁㄷㄹㅂㅎ": "주민등록번호",
    "ㅈㅁㅂㅎ": "주민번호",
    "ㅈㅎㅂㅎ": "전화번호",
    "ㄱㅈㅂㅎ": "계좌번호",
    "ㅇㅁㅇㅈㅅ": "이메일주소",
    "ㅇㅁㅇ": "이메일",
    "ㅈㅅ": "주소",
    "ㅇㄹ": "이름",
}

YAMIN_RESTORE = {
    "즈민뜽록볜훟": "주민등록번호",
    "즈민등록번호": "주민등록번호",
    "즈민뜽록": "주민등록",
    "즈민등록": "주민등록",
    "즈민번호": "주민번호",
    "볜훟": "번호",
}

ROMANIZED_RESTORE = {
    "jumin deungrok beonho": "주민등록번호",
    "jumin beonho": "주민번호",
    "jeonhwa beonho": "전화번호",
    "email": "이메일",
    "juso": "주소",
}

KOREAN_DIGIT_MAP = {
    "영": "0",
    "공": "0",
    "일": "1",
    "이": "2",
    "삼": "3",
    "사": "4",
    "오": "5",
    "육": "6",
    "칠": "7",
    "팔": "8",
    "구": "9",
}

KOREAN_DIGIT_CONTEXT = (
    "연락처",
    "전화",
    "휴대폰",
    "주민번호",
    "주민등록번호",
    "카드",
    "CVV",
    "cvv",
    "OTP",
    "otp",
    "인증번호",
    "계좌",
)

SPACED_KEYWORDS = (
    "주민등록번호",
    "주민번호",
    "전화번호",
    "계좌번호",
    "카드번호",
    "사업자등록번호",
    "외국인등록번호",
    "이메일주소",
    "이메일",
    "개인정보",
    "주소",
    "이름",
)


def preprocess_text(raw_text: str, *, use_kiwi: bool = False) -> PreprocessResult:
    """Return normalized text, variants, and raw-offset maps for ``raw_text``."""

    normalized_text, norm_to_raw, raw_to_norm, norm_spans = _normalize_raw_text(raw_text)
    normalized = _make_variant("normalized", normalized_text, norm_spans)

    variants = [
        normalized,
        _digit_compact_variant(normalized),
        _digit_space_compact_variant(normalized),
        _korean_keyword_spacing_variant(normalized),
        _jamo_composed_variant(normalized),
        _dictionary_replace_variant(normalized, "choseong_restored", CHOSEONG_RESTORE, ignore_case=False),
        _dictionary_replace_variant(normalized, "yamin_restored", YAMIN_RESTORE, ignore_case=False),
        _dictionary_replace_variant(normalized, "romanized_restored", ROMANIZED_RESTORE, ignore_case=True),
        _korean_digit_restored_variant(normalized),
    ]

    sentences = _split_sentences(raw_text)
    eojeols = _split_eojeols(raw_text)
    if use_kiwi:
        kiwi_sentences, kiwi_eojeols = _try_kiwi_boundaries(raw_text)
        if kiwi_sentences:
            sentences = kiwi_sentences
        if kiwi_eojeols:
            eojeols = kiwi_eojeols

    return PreprocessResult(
        raw_text=raw_text,
        normalized_text=normalized_text,
        variants=tuple(_dedupe_variants(variants)),
        norm_to_raw=norm_to_raw,
        raw_to_norm=raw_to_norm,
        sentences=sentences,
        eojeols=eojeols,
    )


def restore_variant_span(variant: TextVariant, start: int, end: int) -> tuple[int, int]:
    """Restore a half-open variant span into a half-open raw text span."""

    if start < 0 or end < start or end > len(variant.text):
        raise NormalizationMapError("Variant span is outside variant bounds")
    if start == end:
        raise NormalizationMapError("Empty variant span cannot be restored")

    spans = variant.variant_to_raw_span
    if not spans:
        spans = tuple(None if idx is None else (idx, idx + 1) for idx in variant.variant_to_raw)
    if len(spans) != len(variant.text):
        raise NormalizationMapError("Variant mapping length mismatch")

    selected = spans[start:end]
    if any(span is None for span in selected):
        raise NormalizationMapError("Variant span contains unmapped characters")

    raw_start = min(span[0] for span in selected if span is not None)
    raw_end = max(span[1] for span in selected if span is not None)
    if raw_start < 0 or raw_end <= raw_start:
        raise NormalizationMapError("Variant span restored to invalid raw bounds")
    return raw_start, raw_end


def _normalize_raw_text(raw_text: str) -> tuple[str, tuple[int | None, ...], tuple[int | None, ...], tuple[tuple[int, int], ...]]:
    output: list[str] = []
    norm_to_raw: list[int] = []
    norm_spans: list[tuple[int, int]] = []
    raw_to_norm: list[int | None] = []

    for raw_index, char in enumerate(raw_text):
        normalized = _normalize_char(char)
        if not normalized:
            raw_to_norm.append(None)
            continue
        raw_to_norm.append(len(output))
        for out_char in normalized:
            output.append(out_char)
            norm_to_raw.append(raw_index)
            norm_spans.append((raw_index, raw_index + 1))

    return "".join(output), tuple(norm_to_raw), tuple(raw_to_norm), tuple(norm_spans)


def _normalize_char(char: str) -> str:
    if char in INVISIBLE_CHARS:
        return ""
    if char in DASH_CHARS:
        return "-"
    if char in CHOSEONG or char in JUNGSEONG or char in JONGSEONG:
        return char
    normalized = unicodedata.normalize("NFKC", char)
    if normalized in DASH_CHARS:
        return "-"
    if len(normalized) == 1:
        try:
            return str(unicodedata.digit(normalized))
        except (TypeError, ValueError):
            return normalized
    return normalized


def _make_variant(name: str, text: str, spans: Iterable[tuple[int, int] | None]) -> TextVariant:
    span_tuple = tuple(spans)
    variant_to_raw = tuple(None if span is None else span[0] for span in span_tuple)
    return TextVariant(name=name, text=text, variant_to_raw=variant_to_raw, variant_to_raw_span=span_tuple)


def _dedupe_variants(variants: Iterable[TextVariant]) -> list[TextVariant]:
    seen: set[tuple[str, str]] = set()
    result: list[TextVariant] = []
    for variant in variants:
        key = (variant.name, variant.text)
        if key in seen:
            continue
        seen.add(key)
        result.append(variant)
    return result


def _digit_compact_variant(base: TextVariant) -> TextVariant:
    return _compact_separators_between_digits(base, "digit_compact", DIGIT_SEPARATORS)


def _digit_space_compact_variant(base: TextVariant) -> TextVariant:
    return _compact_separators_between_digits(base, "digit_space_compact", {" ", "\t", "\n", "\r"})


def _compact_separators_between_digits(base: TextVariant, name: str, separators: set[str]) -> TextVariant:
    output: list[str] = []
    spans: list[tuple[int, int] | None] = []
    text = base.text
    base_spans = _variant_spans(base)

    for index, char in enumerate(text):
        if char in separators and _has_digit_before(text, index) and _has_digit_after(text, index):
            continue
        output.append(char)
        spans.append(base_spans[index])

    return _make_variant(name, "".join(output), spans)


def _has_digit_before(text: str, index: int) -> bool:
    cursor = index - 1
    while cursor >= 0 and text[cursor] in DIGIT_SEPARATORS:
        cursor -= 1
    return cursor >= 0 and text[cursor].isdigit()


def _has_digit_after(text: str, index: int) -> bool:
    cursor = index + 1
    while cursor < len(text) and text[cursor] in DIGIT_SEPARATORS:
        cursor += 1
    return cursor < len(text) and text[cursor].isdigit()


def _korean_keyword_spacing_variant(base: TextVariant) -> TextVariant:
    text = base.text
    base_spans = _variant_spans(base)
    output: list[str] = []
    spans: list[tuple[int, int] | None] = []
    index = 0
    keywords = sorted(SPACED_KEYWORDS, key=len, reverse=True)

    while index < len(text):
        match = _match_spaced_keyword(text, index, keywords)
        if match is None:
            output.append(text[index])
            spans.append(base_spans[index])
            index += 1
            continue

        keyword, consumed_end, letter_indices = match
        for char, source_index in zip(keyword, letter_indices, strict=True):
            output.append(char)
            spans.append(base_spans[source_index])
        index = consumed_end

    return _make_variant("korean_keyword_spacing_compact", "".join(output), spans)


def _match_spaced_keyword(text: str, start: int, keywords: list[str]) -> tuple[str, int, list[int]] | None:
    for keyword in keywords:
        cursor = start
        letter_indices: list[int] = []
        saw_space = False
        for letter in keyword:
            while cursor < len(text) and text[cursor].isspace():
                saw_space = True
                cursor += 1
            if cursor >= len(text) or text[cursor] != letter:
                break
            letter_indices.append(cursor)
            cursor += 1
        else:
            if saw_space:
                return keyword, cursor, letter_indices
    return None


def _jamo_composed_variant(base: TextVariant) -> TextVariant:
    text = base.text
    base_spans = _variant_spans(base)
    output: list[str] = []
    spans: list[tuple[int, int] | None] = []
    index = 0

    while index < len(text):
        match = _compose_jamo_at(text, index)
        if match is None:
            output.append(text[index])
            spans.append(base_spans[index])
            index += 1
            continue

        syllable, consumed = match
        output.append(syllable)
        spans.append(_merge_spans(base_spans[index : index + consumed]))
        index += consumed

    return _make_variant("jamo_composed", "".join(output), spans)


def _compose_jamo_at(text: str, index: int) -> tuple[str, int] | None:
    if index + 1 >= len(text) or text[index] not in CHOSEONG or text[index + 1] not in JUNGSEONG:
        return None

    choseong_index = CHOSEONG.index(text[index])
    jungseong_index = JUNGSEONG.index(text[index + 1])
    jongseong_index = 0
    consumed = 2

    if index + 2 < len(text) and text[index + 2] in JONGSEONG:
        next_is_vowel = index + 3 < len(text) and text[index + 3] in JUNGSEONG
        if not next_is_vowel:
            jongseong_index = JONGSEONG.index(text[index + 2]) + 1
            consumed = 3

    codepoint = 0xAC00 + (choseong_index * 21 + jungseong_index) * 28 + jongseong_index
    return chr(codepoint), consumed


def _dictionary_replace_variant(
    base: TextVariant,
    name: str,
    replacements: dict[str, str],
    *,
    ignore_case: bool,
) -> TextVariant:
    text = base.text
    compare_text = text.lower() if ignore_case else text
    entries = sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True)
    if ignore_case:
        entries = [(source.lower(), target) for source, target in entries]
    base_spans = _variant_spans(base)
    output: list[str] = []
    spans: list[tuple[int, int] | None] = []
    index = 0

    while index < len(text):
        matched: tuple[str, str] | None = None
        for source, target in entries:
            if compare_text.startswith(source, index):
                matched = (source, target)
                break

        if matched is None:
            output.append(text[index])
            spans.append(base_spans[index])
            index += 1
            continue

        source, target = matched
        raw_span = _merge_spans(base_spans[index : index + len(source)])
        for char in target:
            output.append(char)
            spans.append(raw_span)
        index += len(source)

    return _make_variant(name, "".join(output), spans)


def _korean_digit_restored_variant(base: TextVariant) -> TextVariant:
    text = base.text
    base_spans = _variant_spans(base)
    output: list[str] = []
    spans: list[tuple[int, int] | None] = []
    index = 0

    while index < len(text):
        if text[index] in KOREAN_DIGIT_MAP and _has_korean_digit_context(text, index):
            while index < len(text) and (text[index] in KOREAN_DIGIT_MAP or text[index].isspace()):
                if text[index] in KOREAN_DIGIT_MAP:
                    output.append(KOREAN_DIGIT_MAP[text[index]])
                    spans.append(base_spans[index])
                index += 1
            continue

        output.append(text[index])
        spans.append(base_spans[index])
        index += 1

    return _make_variant("korean_digit_restored", "".join(output), spans)


def _has_korean_digit_context(text: str, index: int) -> bool:
    window = text[max(0, index - 24) : index]
    return any(keyword in window for keyword in KOREAN_DIGIT_CONTEXT)


def _variant_spans(variant: TextVariant) -> tuple[tuple[int, int] | None, ...]:
    if variant.variant_to_raw_span:
        return variant.variant_to_raw_span
    return tuple(None if idx is None else (idx, idx + 1) for idx in variant.variant_to_raw)


def _merge_spans(spans: Iterable[tuple[int, int] | None]) -> tuple[int, int] | None:
    resolved = [span for span in spans if span is not None]
    if not resolved:
        return None
    return min(span[0] for span in resolved), max(span[1] for span in resolved)


def _split_sentences(raw_text: str) -> tuple[SentenceSpan, ...]:
    spans: list[SentenceSpan] = []
    start: int | None = None
    terminators = {".", "!", "?", "。", "！", "？", "\n"}

    for index, char in enumerate(raw_text):
        if start is None and not char.isspace():
            start = index
        if start is not None and char in terminators:
            end = index + 1
            if raw_text[start:end].strip():
                spans.append(SentenceSpan(start=start, end=end, text=raw_text[start:end]))
            start = None

    if start is not None and raw_text[start:].strip():
        spans.append(SentenceSpan(start=start, end=len(raw_text), text=raw_text[start:]))

    return tuple(spans)


def _split_eojeols(raw_text: str) -> tuple[TokenSpan, ...]:
    return tuple(TokenSpan(match.start(), match.end(), match.group(0)) for match in re.finditer(r"\S+", raw_text))


def _try_kiwi_boundaries(raw_text: str) -> tuple[tuple[SentenceSpan, ...], tuple[TokenSpan, ...]]:
    try:
        from kiwipiepy import Kiwi  # type: ignore[import-not-found]
    except Exception:
        return (), ()

    try:
        kiwi = Kiwi()
        sentences = _kiwi_sentences(kiwi, raw_text)
        tokens = _kiwi_tokens(kiwi, raw_text)
    except Exception:
        return (), ()
    return sentences, tokens


def _kiwi_sentences(kiwi: object, raw_text: str) -> tuple[SentenceSpan, ...]:
    result: list[SentenceSpan] = []
    for sentence in kiwi.split_into_sents(raw_text):  # type: ignore[attr-defined]
        start = getattr(sentence, "start", None)
        end = getattr(sentence, "end", None)
        text = getattr(sentence, "text", None)
        if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(raw_text):
            result.append(SentenceSpan(start=start, end=end, text=raw_text[start:end]))
        elif isinstance(text, str):
            found = raw_text.find(text)
            if found >= 0:
                result.append(SentenceSpan(start=found, end=found + len(text), text=text))
    return tuple(result)


def _kiwi_tokens(kiwi: object, raw_text: str) -> tuple[TokenSpan, ...]:
    result: list[TokenSpan] = []
    for token in kiwi.tokenize(raw_text):  # type: ignore[attr-defined]
        start = getattr(token, "start", None)
        length = getattr(token, "len", None)
        if length is None:
            length = getattr(token, "length", None)
        if isinstance(start, int) and isinstance(length, int):
            end = start + length
            if 0 <= start < end <= len(raw_text):
                result.append(TokenSpan(start=start, end=end, text=raw_text[start:end]))
    return tuple(result)
