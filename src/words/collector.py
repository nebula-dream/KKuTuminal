from __future__ import annotations

import json
import os
import sys
import time
import unicodedata
from pathlib import Path
from typing import Iterator

DATA_DIR = Path(__file__).parent.parent.parent / "data"
WORDS_FILE = DATA_DIR / "words.json"
CACHE_STAMP_FILE = DATA_DIR / ".cache_stamp"


def normalize_word(word: str) -> str:
    return unicodedata.normalize("NFC", word).strip()


def is_valid_korean_word(word: str) -> bool:
    if not word or len(word) < 2:
        return False
    normalized = normalize_word(word)
    return all(0xAC00 <= ord(ch) <= 0xD7A3 for ch in normalized)


def load_words() -> list[str]:
    if not WORDS_FILE.exists():
        return []
    try:
        with open(WORDS_FILE, encoding="utf-8") as f:
            words = json.load(f)
        if not isinstance(words, list) or len(words) < 50:
            return []
        return words
    except Exception:
        return []


def collect_words(verbose: bool = True) -> list[str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if WORDS_FILE.exists():
        try:
            with open(WORDS_FILE, encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached, list) and len(cached) >= 200:
                if verbose:
                    print(f"  [{len(cached)}개 단어 로드 완료]")
                return cached
        except Exception:
            pass

    if verbose:
        print("  [단어 파일을 찾을 수 없습니다. 내장 단어만 사용합니다.]")
    return BUILTIN_WORDS


def build_word_index(words: list[str]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for word in words:
        if not word:
            continue
        key = word[0]
        index.setdefault(key, []).append(word)
    return index


BUILTIN_WORDS: list[str] = [
    "가구", "가나", "가능", "가로", "가면", "가방", "가수", "가야", "가을", "가이드",
    "가전", "가족", "가죽", "가지", "각도", "간격", "간단", "간식", "간장", "갈매기",
    "감기", "감동", "감자", "강남", "강물", "강아지", "강원도", "개구리", "개나리", "개미",
    "개인", "거래", "거리", "거북이", "거울", "건강", "건물", "건설", "게임", "겨울",
    "결과", "결혼", "경기", "경제", "계단", "계획", "고구마", "고기", "고래", "고양이",
    "고향", "공기", "공부", "공원", "공항", "과일", "과자", "관계", "교육", "구름",
    "국가", "국내", "국민", "국수", "국제", "군인", "그림", "근처", "기계", "기념",
    "기도", "기름", "기술", "기억", "기온", "기초", "길이", "김치", "까치", "꽃잎",
    "나라", "나무", "나비", "낙타", "남자", "남쪽", "낭비", "내용", "냉면", "냉장고",
    "노래", "노력", "노을", "놀이", "농부", "농사", "눈물", "뉴스", "니트",
    "다람쥐", "다리", "단어", "달력", "달리기", "담요", "당근", "대구", "대기", "대화",
    "도시", "도움", "도전", "독서", "동물", "동생", "동화", "된장", "두부", "드라마",
    "라디오", "라면", "레몬", "레시피", "로봇",
    "마늘", "마라톤", "마을", "마음", "마중", "만화", "말씀", "매일", "머리",
    "메시지", "모래", "목소리", "무지개", "문화", "물고기", "물론", "미래", "미소",
    "바나나", "바다", "바람", "바위", "박물관", "반지", "발전", "밤하늘", "방법", "배추",
    "버스", "벌레", "벚꽃", "보름달", "복숭아", "부모", "부산", "분위기", "불꽃", "비행기",
    "사과", "사람", "사랑", "사막", "사전", "사진", "산책", "상상", "새벽", "생각",
    "서울", "선물", "성공", "세계", "소나기", "소녀", "소식", "수박", "수업", "시간",
    "신발", "신비", "싸움",
    "아기", "아름다움", "아버지", "아이스크림", "악기", "안경", "어린이", "여행", "역사",
    "연필", "영화", "오리", "오이", "옷장", "우리", "우산", "우주", "운동", "웃음",
    "위기", "의사", "이야기",
    "자동차", "자연", "작가", "전화", "점심", "정보", "조개", "주방", "지구", "지식",
    "진심", "창문", "채소", "천사", "초록", "추억",
    "카메라", "커피", "코끼리", "태풍", "토끼", "파도", "파란색", "편지", "포도",
    "하늘", "한국", "해바라기", "호랑이", "화분", "황금",
]


if __name__ == "__main__":
    words = load_words()
    print(f"\n총 {len(words)}개 단어")
    print("샘플:", words[:20])
