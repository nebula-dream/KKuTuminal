from __future__ import annotations

HANGUL_BASE = 0xAC00
CHOSUNG_COUNT = 21 * 28
JUNGSUNG_COUNT = 28

CHOSUNG_LIST = [
    "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ",
    "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]

JONGSUNG_LIST = [
    "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ",
    "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ",
    "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]

DUEUM_MAP: dict[str, str] = {
    "ㄹ": "ㄴ",
    "ㄴ": "ㄴ",
}

DUEUM_SYLLABLE_MAP: dict[str, str] = {
    "리": "이", "례": "예", "률": "율", "리": "이",
    "락": "낙", "란": "난", "랄": "날", "람": "남",
    "랍": "납", "랑": "낭", "래": "내", "랭": "냉",
    "략": "약", "량": "양", "려": "여", "력": "역",
    "련": "연", "렬": "열", "렴": "염", "렵": "엽",
    "령": "영", "례": "예", "로": "노", "록": "녹",
    "론": "논", "롱": "농", "뢰": "뇌", "료": "요",
    "룡": "용", "루": "누", "류": "유", "륙": "육",
    "륜": "윤", "률": "율", "릉": "능", "리": "이",
    "린": "인", "림": "임",
    "나": "나", "낙": "낙", "난": "난",
}


def decompose_syllable(char: str) -> tuple[str, str, str]:
    code = ord(char) - HANGUL_BASE
    if code < 0 or code > 11171:
        return (char, "", "")
    jongsung_idx = code % 28
    jungsung_idx = (code // 28) % 21
    chosung_idx = code // CHOSUNG_COUNT
    return (
        CHOSUNG_LIST[chosung_idx],
        str(jungsung_idx),
        JONGSUNG_LIST[jongsung_idx],
    )


def get_chosung(char: str) -> str:
    code = ord(char) - HANGUL_BASE
    if code < 0 or code > 11171:
        return char
    return CHOSUNG_LIST[code // CHOSUNG_COUNT]


def get_jongsung(char: str) -> str:
    code = ord(char) - HANGUL_BASE
    if code < 0 or code > 11171:
        return ""
    return JONGSUNG_LIST[code % 28]


def is_hangul(char: str) -> bool:
    return 0xAC00 <= ord(char) <= 0xD7A3


def apply_dueum(syllable: str) -> str:
    return DUEUM_SYLLABLE_MAP.get(syllable, syllable)


def get_next_char(word: str) -> str:
    if not word:
        return ""
    last_char = word[-1]
    jongsung = get_jongsung(last_char)
    if jongsung in ("ㄹ",):
        mapped = apply_dueum(last_char)
        if mapped != last_char:
            return mapped
    return last_char


def normalize_start_char(char: str) -> list[str]:
    candidates = [char]
    mapped = apply_dueum(char)
    if mapped != char:
        candidates.append(mapped)

    chosung = get_chosung(char)
    if chosung == "ㄹ":
        for alt_syllable, alt_mapped in DUEUM_SYLLABLE_MAP.items():
            if alt_mapped[0] == char[0] if char else False:
                pass
    return list(dict.fromkeys(candidates))


JAMO_COMPAT_TO_CHOSUNG: dict[str, int] = {
    "ㄱ": 0, "ㄲ": 1, "ㄴ": 2, "ㄷ": 3, "ㄸ": 4, "ㄹ": 5, "ㅁ": 6,
    "ㅂ": 7, "ㅃ": 8, "ㅅ": 9, "ㅆ": 10, "ㅇ": 11, "ㅈ": 12, "ㅉ": 13,
    "ㅊ": 14, "ㅋ": 15, "ㅌ": 16, "ㅍ": 17, "ㅎ": 18,
}


def build_syllable(chosung: str, jungsung_idx: int, jongsung: str) -> str:
    cho_idx = JAMO_COMPAT_TO_CHOSUNG.get(chosung, -1)
    if cho_idx < 0:
        return chosung
    jong_idx = JONGSUNG_LIST.index(jongsung) if jongsung in JONGSUNG_LIST else 0
    code = HANGUL_BASE + cho_idx * CHOSUNG_COUNT + jungsung_idx * 28 + jong_idx
    return chr(code)


def words_match(prev_word: str, next_word: str) -> bool:
    if not prev_word or not next_word:
        return False
    last_char = prev_word[-1]
    first_char = next_word[0]
    if last_char == first_char:
        return True
    return apply_dueum(last_char) == first_char
