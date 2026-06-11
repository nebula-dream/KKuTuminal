from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.words.korean_utils import apply_dueum, is_hangul, words_match


class GameResult(Enum):
    ONGOING = "ongoing"
    PLAYER_WIN = "player_win"
    CPU_WIN = "cpu_win"
    DRAW = "draw"
    PLAYER_LOSE_MISTAKES = "player_lose_mistakes"
    PLAYER_QUIT_END = "player_quit_end"


class WordRejectReason(Enum):
    OK = "ok"
    NOT_KOREAN = "not_korean"
    TOO_SHORT = "too_short"
    ALREADY_USED = "already_used"
    NOT_IN_DICT = "not_in_dict"
    WRONG_START = "wrong_start"


@dataclass
class TurnRecord:
    turn: int
    player: str
    word: str
    timestamp: float
    elapsed_ms: int


@dataclass
class GameState:
    words_index: dict[str, list[str]]
    all_words_set: set[str]
    difficulty: str = "보통"
    max_turns: int = 9999

    current_word: str = ""
    used_words: set[str] = field(default_factory=set)
    history: list[TurnRecord] = field(default_factory=list)
    turn: int = 0
    result: GameResult = GameResult.ONGOING
    player_score: int = 0
    cpu_score: int = 0
    player_mistakes: int = 0
    start_time: float = field(default_factory=time.time)

    def get_next_char_required(self) -> str:
        if not self.current_word:
            return ""
        last_char = self.current_word[-1]
        dueum = apply_dueum(last_char)
        if dueum != last_char:
            return dueum
        return last_char

    def validate_word(self, word: str) -> WordRejectReason:
        if not word:
            return WordRejectReason.TOO_SHORT
        word = word.strip()
        if len(word) < 2:
            return WordRejectReason.TOO_SHORT
        if not all(is_hangul(ch) for ch in word):
            return WordRejectReason.NOT_KOREAN
        if word in self.used_words:
            return WordRejectReason.ALREADY_USED
        if self.current_word and not words_match(self.current_word, word):
            return WordRejectReason.WRONG_START
        if word not in self.all_words_set:
            return WordRejectReason.NOT_IN_DICT
        return WordRejectReason.OK

    def apply_word(self, word: str, player: str, elapsed_ms: int) -> None:
        self.used_words.add(word)
        self.current_word = word
        self.turn += 1
        self.history.append(
            TurnRecord(
                turn=self.turn,
                player=player,
                word=word,
                timestamp=time.time(),
                elapsed_ms=elapsed_ms,
            )
        )
        if player == "player":
            self.player_score += len(word)
        else:
            self.cpu_score += len(word)


class CpuPlayer:
    def __init__(self, difficulty: str = "보통") -> None:
        self.difficulty = difficulty
        self._think_time_range = self._get_think_time()

    def _get_think_time(self) -> tuple[float, float]:
        return {
            "쉬움": (1.5, 3.0),
            "보통": (0.6, 1.8),
            "어려움": (0.2, 0.8),
            "극악": (0.05, 0.2),
        }.get(self.difficulty, (0.6, 1.8))

    def think(self) -> float:
        lo, hi = self._think_time_range
        return random.uniform(lo, hi)

    def _hard_ending_bonus(self, word: str) -> float:
        last_char = word[-1]
        try:
            from unicodedata import name as uname
            n = uname(last_char)
            hard_endings = ["HIEUH", "RIEUL-KIYEOK", "RIEUL-PIEUP", "SSANGSIOS"]
            for h in hard_endings:
                if h in n:
                    return 15.0
        except Exception:
            pass
        return 0.0

    def choose_word(
        self,
        state: GameState,
        candidates: list[str],
    ) -> Optional[str]:
        """봇은 항상 가능한 단어를 찾으면 반드시 선택합니다 (확률적 실패 없음)."""
        if not candidates:
            return None
        available = [w for w in candidates if w not in state.used_words]
        if not available:
            return None

        if self.difficulty == "쉬움":
            # 짧은 단어 선호 (2~3글자), 없으면 전체 중 임의 선택
            short = [w for w in available if len(w) <= 3]
            pool = short if short else available
            return random.choice(pool)

        if self.difficulty == "보통":
            # 중간 길이 단어 선호 (3~4글자), 없으면 전체 중 임의 선택
            mid = [w for w in available if 3 <= len(w) <= 4]
            pool = mid if mid else available
            return random.choice(pool)

        if self.difficulty == "어려움":
            # 길고 어려운 끝글자 선호, 상위권 중 선택
            scored = sorted(
                available,
                key=lambda w: len(w) * 10.0 + self._hard_ending_bonus(w) + random.uniform(0, 3),
                reverse=True,
            )
            top_n = max(1, len(scored) // 5)
            return scored[random.randint(0, top_n - 1)]

        # 극악: 항상 가장 길고 어려운 단어 선택 (무조건)
        scored = sorted(
            available,
            key=lambda w: (len(w), self._hard_ending_bonus(w)),
            reverse=True,
        )
        return scored[0]

    def find_candidates(self, state: GameState) -> list[str]:
        required = state.get_next_char_required()
        if not required:
            return []
        candidates = state.words_index.get(required, [])
        if not candidates:
            dueum = apply_dueum(required)
            if dueum != required:
                candidates = state.words_index.get(dueum, [])
        return [w for w in candidates if w not in state.used_words]

    def make_move(self, state: GameState) -> Optional[str]:
        """봇이 반드시 단어를 찾아 반환합니다. 후보가 없을 때만 None 반환."""
        candidates = self.find_candidates(state)
        return self.choose_word(state, candidates)
