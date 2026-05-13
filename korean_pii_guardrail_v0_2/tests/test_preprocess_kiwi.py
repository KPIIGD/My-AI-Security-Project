import pytest

from pii_guardrail.preprocess import preprocess_text


pytest.importorskip("kiwipiepy")


def test_kiwi_boundaries_stay_inside_raw_text() -> None:
    raw = "홍길동이 신청했습니다. 김민수에게 연락하세요."
    result = preprocess_text(raw, use_kiwi=True)

    assert result.sentences
    assert result.eojeols
    for span in (*result.sentences, *result.eojeols):
        assert 0 <= span.start < span.end <= len(raw)
        assert span.text == raw[span.start : span.end]
