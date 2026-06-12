"""
Korean PII Normalizer v1.0 — Layer 0 Defense
==============================================

한국어 PII 변이 공격에 대한 형태소 정규화 방어 계층.
퍼저의 7가지 변이를 표준 형태로 역변환하여 downstream 가드레일(Presidio/Bedrock)이
정확히 탐지할 수 있도록 전처리.

정규화 파이프라인:
  1. NFKC              — 동형문자, fullwidth 표준화
  2. Invisible 제거     — ZWSP, soft_hyphen, BOM
  3. Combining 제거     — diacritic marks
  4. Homoglyph 역변환  — mathematical/circled 숫자
  5. Jamo 병합          — ㅈㅜㅁㅣㄴ → 주민
  6. 초성 역매핑        — ㅈㅁㄷㄹㅂㅎ → 주민등록번호 (사전 기반)
  7. 야민정음 역변환    — 즈민뜽록 → 주민등록 (사전 기반)
  8. 한글숫자 → 아라비아 — 오이구 → 529
  9. 코드스위칭 복원    — jumin → 주민 (로마자 → 한글)
  10. 공백 정규화       — 주 민 등 록 → 주민등록 (Kiwi space)
  11. 구분자 정규화     — 900101.1234567 → 900101-1234567

Usage:
  from korean_normalizer import KoreanNormalizer
  nm = KoreanNormalizer()
  clean = nm.normalize("내 ㅈㅜㅁㅣㄴ번호는 900101-1234567")
  # → "내 주민번호는 900101-1234567"
"""

import re
import unicodedata
from typing import Optional

# Kiwi는 선택적 의존성 — 없으면 공백 정규화 스킵
try:
    from kiwipiepy import Kiwi
    _KIWI_AVAILABLE = True
except ImportError:
    _KIWI_AVAILABLE = False


# ═══════════════════════════════════════════════════════════
# 1. Invisible / Combining 문자
# ═══════════════════════════════════════════════════════════

# 제거할 invisible 문자 (공격 유형: zwsp, soft_hyphen, BOM 등)
INVISIBLE_CHARS = {
    "\u200B",  # ZERO WIDTH SPACE
    "\u200C",  # ZERO WIDTH NON-JOINER
    "\u200D",  # ZERO WIDTH JOINER
    "\u2060",  # WORD JOINER
    "\uFEFF",  # ZERO WIDTH NO-BREAK SPACE (BOM)
    "\u00AD",  # SOFT HYPHEN
    "\u180E",  # MONGOLIAN VOWEL SEPARATOR
    "\u2061", "\u2062", "\u2063", "\u2064",  # invisible math
    "\u034F",  # COMBINING GRAPHEME JOINER
}


def remove_invisible(text: str) -> str:
    """ZWSP, soft_hyphen, BOM 등 invisible 문자 제거."""
    return "".join(c for c in text if c not in INVISIBLE_CHARS)


def remove_combining(text: str) -> str:
    """Combining diacritic marks 제거 (예: 7̃ → 7).
    NFD로 분해 → Mn 카테고리 제거 → NFC로 재조합."""
    decomposed = unicodedata.normalize("NFD", text)
    filtered = "".join(c for c in decomposed
                        if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", filtered)


# ═══════════════════════════════════════════════════════════
# 2. Homoglyph 역변환
# ═══════════════════════════════════════════════════════════

# Mathematical digits → 일반 숫자
MATH_DIGIT_MAP = {}
for i in range(10):
    # Mathematical Bold (𝟎-𝟗): 0x1D7CE-0x1D7D7
    MATH_DIGIT_MAP[chr(0x1D7CE + i)] = str(i)
    # Mathematical Double-Struck (𝟘-𝟡): 0x1D7D8-0x1D7E1
    MATH_DIGIT_MAP[chr(0x1D7D8 + i)] = str(i)
    # Mathematical Sans-Serif (𝟢-𝟫): 0x1D7E2-0x1D7EB
    MATH_DIGIT_MAP[chr(0x1D7E2 + i)] = str(i)
    # Mathematical Sans-Serif Bold (𝟬-𝟵): 0x1D7EC-0x1D7F5
    MATH_DIGIT_MAP[chr(0x1D7EC + i)] = str(i)
    # Mathematical Monospace (𝟶-𝟿): 0x1D7F6-0x1D7FF
    MATH_DIGIT_MAP[chr(0x1D7F6 + i)] = str(i)

# Circled digits (①-⑨, ⓪)
CIRCLED_DIGIT_MAP = {"⓪": "0"}
for i in range(9):
    CIRCLED_DIGIT_MAP[chr(0x2460 + i)] = str(i + 1)  # ①-⑨
# Negative circled (⓵-⓿)
for i in range(10):
    if i == 0:
        CIRCLED_DIGIT_MAP["⓿"] = "0"
    else:
        CIRCLED_DIGIT_MAP[chr(0x2776 + i - 1)] = str(i)  # ❶-❿ (Heavy)

# Parenthesized digits (⑴-⒇)
PAREN_DIGIT_MAP = {}
for i in range(9):
    PAREN_DIGIT_MAP[chr(0x2474 + i)] = str(i + 1)


def denormalize_digits(text: str) -> str:
    """수학/원문자 숫자를 일반 숫자로 변환."""
    result = []
    for c in text:
        result.append(MATH_DIGIT_MAP.get(c) or
                      CIRCLED_DIGIT_MAP.get(c) or
                      PAREN_DIGIT_MAP.get(c) or c)
    return "".join(result)


# ═══════════════════════════════════════════════════════════
# 3. Jamo 병합 (ㅈㅜㅁㅣㄴ → 주민)
# ═══════════════════════════════════════════════════════════

# Compatibility Jamo → Unicode Jamo Choseong/Jungseong/Jongseong
CHOSEONG_LIST = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNGSEONG_LIST = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONGSEONG_LIST = "ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"


def compose_jamo(text: str) -> str:
    """
    Compatibility jamo 연속체를 한글 음절로 합성.
    ㅈ+ㅜ+ㅁ+ㅣ+ㄴ → 주민
    판단 규칙:
      - 초성 + 중성 형태 찾기
      - 종성 후보(다음 자모가 JONGSEONG_LIST에 있음)를 발견하면
        그 다음 글자가 중성이 아니면 종성으로 붙임
        (→ jungseong이 오면 다음 음절의 초성이므로 종성 아님)
    """
    result = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # 초성 + 중성 쌍 탐지
        if c in CHOSEONG_LIST and i + 1 < n and text[i + 1] in JUNGSEONG_LIST:
            cho_idx = CHOSEONG_LIST.index(c)
            jung_idx = JUNGSEONG_LIST.index(text[i + 1])
            jong_idx = 0
            consumed = 2
            # 종성 후보 확인
            if i + 2 < n and text[i + 2] in JONGSEONG_LIST:
                next_jamo = text[i + 2]
                # 그 다음 글자가 중성이면 → 다음 음절 초성이므로 종성 아님
                # 끝이거나 비한글/초성이면 → 종성으로 붙임
                if i + 3 < n and text[i + 3] in JUNGSEONG_LIST:
                    pass  # 새 음절 시작 → 종성 아님
                else:
                    jong_idx = JONGSEONG_LIST.index(next_jamo) + 1
                    consumed = 3
            syllable_code = 0xAC00 + (cho_idx * 21 + jung_idx) * 28 + jong_idx
            result.append(chr(syllable_code))
            i += consumed
        else:
            result.append(c)
            i += 1
    return "".join(result)


# ═══════════════════════════════════════════════════════════
# 4. 초성 역매핑 (ㅈㅁㄷㄹㅂㅎ → 주민등록번호)
# ═══════════════════════════════════════════════════════════

# PII 관련 초성 → 단어 사전
# compatibility jamo (ㄱ-ㅎ, U+3131-U+314E) 기반
CHOSEONG_TO_WORD = {
    # 핵심 PII 키워드
    "ㅈㅁㄷㄹㅂㅎ": "주민등록번호",
    "ㅈㅁㅂㅎ": "주민번호",
    "ㅈㅎㅂㅎ": "전화번호",
    "ㅇㅁㅇ": "이메일",
    "ㅇㅁㅇㅇㅈㅅ": "이메일주소",
    "ㅊㄷ": "카드",
    "ㅅㅇㅋㄷ": "신용카드",
    "ㅋㄷㅂㅎ": "카드번호",
    "ㄱㅈㅂㅎ": "계좌번호",
    "ㅇㄱㅂㅎ": "여권번호",
    "ㅇㄱㅇㄷㄹㅂㅎ": "외국인등록번호",
    "ㅇㄱㅇㄷㄹ": "외국인등록",
    "ㅅㅇㅈㄷㄹㅂㅎ": "사업자등록번호",
    "ㅅㅇㅈ": "사업자",
    "ㅈㅅ": "주소",
    "ㅇㄹ": "이름",
    "ㅅㅁ": "성명",
    "ㅂㅎ": "번호",
    "ㄱㅇㅈㅂ": "개인정보",
    "ㅂㅈㄱㄹ": "범죄기록",
    "ㄱㅊ": "계좌",
    "ㅊㅂ": "처방",
    "ㅈㄷ": "진단",
    "ㅂㅎ": "번호",
    "ㄱㅇ": "계약",
    "ㄱㅅ": "고소",
    "ㄱㅅㅈㅎ": "고소장",
}

# Unicode Jamo (U+1100-U+1112, 초성용) 기반 — NFKC가 compat → unicode 변환한 경우 대비
# 예: ㄱ(U+3131) → ᄀ(U+1100)
UNICODE_CHOSEONG_TO_COMPAT = {
    "ᄀ": "ㄱ", "ᄁ": "ㄲ", "ᄂ": "ㄴ", "ᄃ": "ㄷ", "ᄄ": "ㄸ",
    "ᄅ": "ㄹ", "ᄆ": "ㅁ", "ᄇ": "ㅂ", "ᄈ": "ㅃ", "ᄉ": "ㅅ",
    "ᄊ": "ㅆ", "ᄋ": "ㅇ", "ᄌ": "ㅈ", "ᄍ": "ㅉ", "ᄎ": "ㅊ",
    "ᄏ": "ㅋ", "ᄐ": "ㅌ", "ᄑ": "ㅍ", "ᄒ": "ㅎ",
}


def restore_choseong(text: str) -> str:
    """초성만으로 된 PII 키워드를 전체 단어로 복원.
    Unicode jamo(ᄀ)와 compatibility jamo(ㄱ) 둘 다 처리."""
    # 먼저 Unicode jamo → compat jamo 변환 (사전 매칭용)
    result = text
    for uni, compat in UNICODE_CHOSEONG_TO_COMPAT.items():
        result = result.replace(uni, compat)

    # 긴 것부터 매칭 (탐욕적 매칭 방지)
    for cho, word in sorted(CHOSEONG_TO_WORD.items(), key=lambda x: -len(x[0])):
        result = result.replace(cho, word)
    return result


# ═══════════════════════════════════════════════════════════
# 5. 야민정음 역변환 (즈민뜽록 → 주민등록)
# ═══════════════════════════════════════════════════════════

YAMINJEONGEUM_REVERSE = {
    # 퍼저의 yamin 매핑 역변환 (실제 퍼저 korean_pii_fuzzer_v4.py 참조)
    # 긴 단어 먼저 매칭되도록 정렬됨
    "즈민등록번호": "주민등록번호",
    "즈민등록": "주민등록",
    "즈민번호": "주민번호",
    "즈민": "주민",
    "즈먄": "주민",
    "먄": "민",
    "뜽록": "등록",
    "뜽": "등",
    "롣": "록",
    "롘": "록",
    "롷": "록",
    "볜호": "번호",
    "볜": "번",
    "훟": "호",
    "졘화": "전화",
    "졘": "전",
    "훠": "화",
    "잉": "이",
    "먜": "메",
    "잏": "일",
    "칰": "카",
    "듀": "드",
    "뙇": "때",
    "뚱": "둥",
    # 한자 성씨 → 한글 (hanja mutation)
    "朴": "박", "金": "김", "李": "이", "崔": "최", "鄭": "정",
    "姜": "강", "趙": "조", "尹": "윤", "張": "장", "林": "임",
    "韓": "한", "吳": "오", "申": "신", "徐": "서", "權": "권",
    "黃": "황", "安": "안", "宋": "송", "全": "전", "洪": "홍",
    "劉": "유", "柳": "류", "文": "문", "陳": "진", "南": "남",
    "盧": "노", "具": "구", "裵": "배", "白": "백", "許": "허",
    "夏": "하",
}


def denormalize_yamin(text: str) -> str:
    """야민정음 → 표준어."""
    result = text
    for yamin, standard in sorted(YAMINJEONGEUM_REVERSE.items(), key=lambda x: -len(x[0])):
        result = result.replace(yamin, standard)
    return result


# ═══════════════════════════════════════════════════════════
# 6. 한글숫자 → 아라비아 숫자
# ═══════════════════════════════════════════════════════════

# 0~9: 영/일/이/삼/사/오/육/칠/팔/구, 공/하나/둘/셋/넷/다섯/여섯/일곱/여덟/아홉
KR_DIGIT_MAP = {
    # 한자음 숫자
    "영": "0", "공": "0", "제로": "0",
    "일": "1", "이": "2", "삼": "3", "사": "4",
    "오": "5", "육": "6", "칠": "7", "팔": "8", "구": "9",
    # 순우리말 숫자
    "하나": "1", "둘": "2", "셋": "3", "넷": "4", "다섯": "5",
    "여섯": "6", "일곱": "7", "여덟": "8", "아홉": "9",
    "열": "10",
}


def denormalize_kr_digits(text: str) -> str:
    """
    한글 숫자를 아라비아 숫자로 변환.
    단, 일반 한글 단어와 구분하기 위해 다음 조건 중 하나 만족 시에만 변환:
      1. "CVV", "번호", "비밀번호" 등 숫자 컨텍스트 키워드 직후
      2. 단독으로 2자 이상 한글숫자 시퀀스가 단어 경계에 있음
    """
    # 한글 숫자 문자 집합
    KR_DIGITS_CHARS = set("영공일이삼사오육칠팔구하나둘셋넷다섯여섯일곱여덟아홉열제로")

    def convert_sequence(s):
        """한글 숫자 시퀀스를 아라비아로 변환."""
        result = []
        i = 0
        while i < len(s):
            # 2글자 한글숫자 우선 매칭
            if i + 1 < len(s) and s[i:i+2] in KR_DIGIT_MAP:
                result.append(KR_DIGIT_MAP[s[i:i+2]])
                i += 2
            elif s[i] in KR_DIGIT_MAP:
                result.append(KR_DIGIT_MAP[s[i]])
                i += 1
            else:
                result.append(s[i])
                i += 1
        return "".join(result)

    # 전략 1: 숫자 컨텍스트 키워드 뒤의 한글숫자
    context_keywords = ["CVV", "cvv", "번호", "비밀번호", "PIN", "PW", "코드", "OTP",
                         "인증번호", "숫자"]
    for kw in context_keywords:
        # "CVV 오이구" 패턴: 키워드 다음 공백/콜론 다음에 한글숫자 1자 이상
        pattern = re.compile(
            rf"({re.escape(kw)}[\s:=]*)([{''.join(KR_DIGITS_CHARS)}]+)"
        )
        text = pattern.sub(lambda m: m.group(1) + convert_sequence(m.group(2)), text)

    # 전략 2: 한글 단위로 명확히 분리된 한글숫자 (공백으로 둘러싸임)
    pattern = re.compile(rf"(?<![가-힣])([{''.join(KR_DIGITS_CHARS)}]{{2,}})(?![가-힣])")
    text = pattern.sub(lambda m: convert_sequence(m.group(1)), text)

    return text


# ═══════════════════════════════════════════════════════════
# 7. 코드스위칭 복원 (jumin → 주민)
# ═══════════════════════════════════════════════════════════

ROMANIZED_TO_KOREAN = {
    "jumin deungrok beonho": "주민등록번호",
    "jumin beonho": "주민번호",
    "jeonhwa beonho": "전화번호",
    "jumin deungrok": "주민등록",
    "gaein jeongbo": "개인정보",
    "jumin": "주민",
    "jeonhwa": "전화",
    "beonho": "번호",
    "email": "이메일",
    "jusо": "주소",  # о는 키릴문자 사례
    "juso": "주소",
    "ireum": "이름",
    "kadeu beonho": "카드번호",
    "kadeu": "카드",
    "sinyong kadeu": "신용카드",
    "yeogwon": "여권",
    "saeopja deungrok beonho": "사업자등록번호",
    "saeopja": "사업자",
}


def denormalize_romanized(text: str) -> str:
    """로마자 한국어를 한글로 복원 (대소문자 무시)."""
    result = text
    for rom, kor in sorted(ROMANIZED_TO_KOREAN.items(), key=lambda x: -len(x[0])):
        # 대소문자 무시 replace
        pattern = re.compile(re.escape(rom), re.IGNORECASE)
        result = pattern.sub(kor, result)
    return result


# ═══════════════════════════════════════════════════════════
# 8. 구분자 정규화 (숫자 사이 비표준 구분자)
# ═══════════════════════════════════════════════════════════

def normalize_separators(text: str) -> str:
    """
    숫자 사이의 비표준 구분자를 표준 '-'로 통일.
    예: 900101.1234567 → 900101-1234567
        900101/1234567 → 900101-1234567
        900101 1234567 → 900101-1234567 (단일 공백)
    """
    # 6자리-7자리 숫자 (주민번호/외국인등록번호 패턴) + 변종 구분자 (. / _ 공백 포함)
    text = re.sub(r"(\d{6})[\.\/_\s](\d{7})", r"\1-\2", text)
    # 3-4-4 (전화번호)
    text = re.sub(r"(01[016789])[\.\/_\s](\d{3,4})[\.\/_\s](\d{4})", r"\1-\2-\3", text)
    # 4-4-4-4 (카드번호)
    text = re.sub(r"(\d{4})[\.\/_\s](\d{4})[\.\/_\s](\d{4})[\.\/_\s](\d{4})", r"\1-\2-\3-\4", text)
    # 구분자 없음 (sep_none: 13자리 연속 숫자 → 주민번호 복원)
    text = re.sub(r"(?<![\d-])(\d{6})(\d{7})(?![\d])", r"\1-\2", text)
    return text


def collapse_digit_spaces(text: str) -> str:
    """
    공백으로 분리된 숫자 시퀀스를 붙임.
    예: "9 0 0 1 0 1 - 1 2 3 4 5 6 7" → "900101-1234567"
    """
    # 숫자 + 공백 + 숫자 패턴 반복 제거
    # 먼저 다중 공백 단일화
    while True:
        new = re.sub(r"(\d)\s+(\d)", r"\1\2", text)
        if new == text:
            break
        text = new
    # 숫자 + 공백 + '-' + 공백 + 숫자
    text = re.sub(r"(\d)\s*-\s*(\d)", r"\1-\2", text)
    return text


def collapse_hangul_spaces(text: str) -> str:
    """
    공백으로 분리된 한글 단어를 붙임 (PII 키워드 위주).
    예: "주 민 등 록 번 호" → "주민등록번호"
    단어 경계가 애매하므로 PII 키워드 사전 기반으로만 적용.
    """
    pii_keywords = ["주민등록번호", "주민번호", "전화번호", "카드번호",
                    "계좌번호", "여권번호", "사업자등록번호", "외국인등록번호",
                    "개인정보", "주소", "이름", "이메일"]
    for kw in pii_keywords:
        # 띄어쓴 버전을 원래 단어로
        spaced = " ".join(kw)
        text = text.replace(spaced, kw)
    return text


# ═══════════════════════════════════════════════════════════
# 9. Kiwi 기반 공백 정규화 (선택)
# ═══════════════════════════════════════════════════════════

class _KiwiWrapper:
    """Kiwi 인스턴스 lazy 초기화."""
    _instance = None

    @classmethod
    def get(cls):
        if not _KIWI_AVAILABLE:
            return None
        if cls._instance is None:
            cls._instance = Kiwi()
        return cls._instance


def normalize_spacing_kiwi(text: str) -> str:
    """Kiwi의 형태소 기반 공백 교정."""
    kiwi = _KiwiWrapper.get()
    if kiwi is None:
        return text
    try:
        return kiwi.space(text)
    except Exception:
        return text


# ═══════════════════════════════════════════════════════════
# KoreanNormalizer — 통합 파이프라인
# ═══════════════════════════════════════════════════════════

class KoreanNormalizer:
    """
    한국어 PII 변이 공격 방어용 정규화기.

    모든 단계를 on/off 가능하여 기여도 분석(ablation study) 가능.
    """

    def __init__(
        self,
        enable_nfkc: bool = True,
        enable_invisible: bool = True,
        enable_combining: bool = True,
        enable_homoglyph: bool = True,
        enable_jamo: bool = True,
        enable_choseong: bool = True,
        enable_yamin: bool = True,
        enable_kr_digits: bool = True,
        enable_romanized: bool = True,
        enable_separators: bool = True,
        enable_digit_spaces: bool = True,
        enable_hangul_spaces: bool = True,
        enable_kiwi: bool = False,  # Kiwi는 느릴 수 있어 기본 off
    ):
        self.opts = {
            "nfkc": enable_nfkc,
            "invisible": enable_invisible,
            "combining": enable_combining,
            "homoglyph": enable_homoglyph,
            "jamo": enable_jamo,
            "choseong": enable_choseong,
            "yamin": enable_yamin,
            "kr_digits": enable_kr_digits,
            "romanized": enable_romanized,
            "separators": enable_separators,
            "digit_spaces": enable_digit_spaces,
            "hangul_spaces": enable_hangul_spaces,
            "kiwi": enable_kiwi,
        }

    def normalize(self, text: str) -> str:
        """전체 정규화 파이프라인 실행."""
        if not text:
            return text

        # Step 1: Jamo 병합 먼저 (NFKC가 compatibility jamo 파괴하기 전에)
        # ㅈㅜㅁㅣㄴ → 주민 (NFKC 전에 해야 함)
        if self.opts["jamo"]:
            text = compose_jamo(text)

        # Step 2: Unicode NFKC (fullwidth → halfwidth, 호환 형태 → 표준)
        if self.opts["nfkc"]:
            text = unicodedata.normalize("NFKC", text)

        # Step 3: Invisible 문자 제거 (ZWSP, soft_hyphen)
        if self.opts["invisible"]:
            text = remove_invisible(text)

        # Step 4: Combining diacritics 제거 (7̃ → 7)
        if self.opts["combining"]:
            text = remove_combining(text)

        # Step 5: Homoglyph 숫자 역변환 (𝟏 → 1, ① → 1)
        if self.opts["homoglyph"]:
            text = denormalize_digits(text)

        # Step 6: 초성 역매핑 (ㅈㅁㄷㄹㅂㅎ → 주민등록번호)
        # NFKC 후: compatibility jamo가 unicode jamo로 바뀌었을 수 있음
        # restore_choseong 내부에서 unicode → compat 변환 후 매칭
        if self.opts["choseong"]:
            text = restore_choseong(text)

        # Step 7: 야민정음 역변환 (즈민뜽록 → 주민등록)
        if self.opts["yamin"]:
            text = denormalize_yamin(text)

        # Step 8: 로마자 한국어 복원 (jumin → 주민)
        if self.opts["romanized"]:
            text = denormalize_romanized(text)

        # Step 9: 한글숫자 → 아라비아 (CVV 오이구 → CVV 529)
        if self.opts["kr_digits"]:
            text = denormalize_kr_digits(text)

        # Step 10: 구분자 정규화 1차 — 알려진 포맷 (6-7, 4-4-4-4 등)
        if self.opts["separators"]:
            text = normalize_separators(text)

        # Step 11: 공백으로 분리된 숫자 축약 (space_digits 공격 대응)
        if self.opts["digit_spaces"]:
            text = collapse_digit_spaces(text)

        # Step 12: 구분자 정규화 2차 — 공백 축약 후 남은 13자리 → 6-7 복원
        if self.opts["separators"]:
            text = normalize_separators(text)

        # Step 13: 공백으로 분리된 한글 키워드 붙이기
        if self.opts["hangul_spaces"]:
            text = collapse_hangul_spaces(text)

        # Step 14: Kiwi 기반 공백 재교정 (선택)
        if self.opts["kiwi"]:
            text = normalize_spacing_kiwi(text)

        return text

    def explain(self, text: str) -> list:
        """
        각 단계별로 text가 어떻게 변하는지 기록.
        디버깅/ablation study용.
        """
        history = [("original", text)]
        current = text

        steps = [
            ("jamo", compose_jamo),
            ("nfkc", lambda t: unicodedata.normalize("NFKC", t)),
            ("invisible", remove_invisible),
            ("combining", remove_combining),
            ("homoglyph", denormalize_digits),
            ("choseong", restore_choseong),
            ("yamin", denormalize_yamin),
            ("romanized", denormalize_romanized),
            ("kr_digits", denormalize_kr_digits),
            ("separators", normalize_separators),
            ("digit_spaces", collapse_digit_spaces),
            ("separators", normalize_separators),
            ("hangul_spaces", collapse_hangul_spaces),
            ("kiwi", normalize_spacing_kiwi),
        ]

        for name, fn in steps:
            if not self.opts.get(name, False):
                continue
            new = fn(current)
            if new != current:
                history.append((name, new))
                current = new

        return history


# ═══════════════════════════════════════════════════════════
# CLI 테스트
# ═══════════════════════════════════════════════════════════

def _demo():
    nm = KoreanNormalizer()

    tests = [
        # L1 Character
        ("jamo",         "내 ㅈㅜㅁㅣㄴ번호는 900101-1234567"),
        ("choseong",     "내 ㅈㅁㅂㅎ는 900101-1234567"),
        ("fullwidth",    "문재현의 주민등록번호는 ７４０４２９-１１３０１３２입니다"),
        ("homoglyph",    "외국인등록번호 𝟗𝟓𝟎𝟓𝟐𝟐-𝟓𝟐𝟔𝟐𝟒𝟎𝟏"),
        ("circled",      "주민등록번호 ⑦②①①①①-①⑤⑦⑧④③①"),

        # L2 Encoding
        ("zwsp",         "주민번호: 9\u200B0\u200B0\u200B1\u200B0\u200B1-1234567"),
        ("soft_hyphen",  "9­0­0­1­0­1­-­1­2­3­4­5­6­7"),
        ("combining",    "711̀003-15431̀68"),

        # L3 Format
        ("sep_dot",      "900101.1234567"),
        ("sep_space",    "900101 1234567"),
        ("space_digits", "9 0 0 1 0 1 - 1 2 3 4 5 6 7"),

        # L4 Linguistic
        ("code_switch",  "jumin deungrok beonho 알려줘"),
        ("kr_digits",    "카드 CVV 오이구"),

        # L5 Context (JSON)
        ("ctx_json",     '{"name":"김민수","phone":"010-1234-5678"}'),

        # 야민정음
        ("yamin",        "즈민뜽록볜훟 알려줘"),
    ]

    print("=" * 80)
    print("  Korean PII Normalizer v1.0 — Demo")
    print("=" * 80)
    for label, inp in tests:
        out = nm.normalize(inp)
        changed = "✓" if out != inp else "✗"
        print(f"\n[{label}] {changed}")
        print(f"  IN : {inp}")
        print(f"  OUT: {out}")


if __name__ == "__main__":
    _demo()
