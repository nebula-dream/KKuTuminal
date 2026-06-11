from __future__ import annotations

import random
import sys
import time
from typing import Optional

from src.game.engine import CpuPlayer, GameResult, GameState, WordRejectReason
from src.ui.terminal import (
    BOLD,
    DIM,
    FG_BRIGHT_GREEN,
    FG_BRIGHT_RED,
    FG_BRIGHT_WHITE,
    FG_BRIGHT_YELLOW,
    FG_MAGENTA,
    FG_WHITE,
    FG_YELLOW,
    MAX_MISTAKES,
    c,
    clear,
    get_terminal_width,
    horizontal_rule,
    print_banner,
    print_bot_thinking,
    print_error,
    print_game_header,
    print_hint,
    print_mistake_warning,
    print_result_screen,
    print_word_played,
    prompt_menu,
    prompt_word,
)
from src.words.collector import build_word_index, collect_words, load_words
from src.words.korean_utils import apply_dueum

DIFFICULTY_OPTIONS = [
    ("1", "쉬움   - 봇이 짧고 잇기 쉬운단어 선호"),
    ("2", "보통   - 일반적인 난이도"),
    ("3", "어려움 - 봇이 빠르고 긴 단어, 어려운 끝글자 선호"),
    ("4", "극악   - 봇이 즉시 가장 잇기 어려운 단어를 선택"),
]
DIFFICULTY_MAP = {"1": "쉬움", "2": "보통", "3": "어려움", "4": "극악"}

SHOW_MAX_USES = {
    "쉬움": 1,
    "보통": 1,
    "어려움": 1,
    "극악": 2,
}


def build_reject_message(reason: WordRejectReason, current_word: str, word: str) -> tuple[str, str]:
    messages = {
        WordRejectReason.NOT_KOREAN: (
            "한글 단어만 입력할 수 있습니다",
            "예: '가나', '나무', '다리'",
        ),
        WordRejectReason.TOO_SHORT: (
            "두 글자 이상 입력해야 합니다",
            "",
        ),
        WordRejectReason.ALREADY_USED: (
            f"'{word}'는 이미 사용된 단어입니다",
            "다른 단어를 사용하세요",
        ),
        WordRejectReason.NOT_IN_DICT: (
            f"'{word}'는 끄코 단어장에 없는 단어입니다",
            "/hint 를 입력하면 힌트를 볼 수 있습니다",
        ),
        WordRejectReason.WRONG_START: (
            f"'{word}'는 '{apply_dueum(current_word[-1]) if current_word else '?'}'(으)로 시작해야 합니다",
            f"현재 마지막 글자: '{current_word[-1] if current_word else '?'}'",
        ),
    }
    return messages.get(reason, ("알 수 없는 오류", ""))


def select_first_word(state: GameState) -> str:
    candidates = []
    for letter in ["가", "나", "다", "마", "사", "아", "자", "하", "바", "카"]:
        words = state.words_index.get(letter, [])
        if words:
            if state.difficulty == "쉬움":
                short = [w for w in words if len(w) <= 3]
                candidates.extend(random.sample(short or words, min(3, len(short or words))))
            else:
                candidates.extend(random.sample(words, min(3, len(words))))
    if not candidates:
        all_words = list(state.all_words_set)
        candidates = random.sample(all_words, min(10, len(all_words)))
    return random.choice(candidates) if candidates else ""


def _get_show_word(state: GameState) -> Optional[str]:
    """난이도에 맞는 /show 단어를 반환합니다."""
    required = state.get_next_char_required() if state.current_word else ""
    if not required:
        return None

    candidates = state.words_index.get(required, [])
    if not candidates:
        dueum = apply_dueum(required)
        if dueum != required:
            candidates = state.words_index.get(dueum, [])
    available = [w for w in candidates if w not in state.used_words]

    if not available:
        return None

    difficulty = state.difficulty

    if difficulty == "쉬움":
        # 2~3글자 단어
        filtered = [w for w in available if 2 <= len(w) <= 3]
        if not filtered:
            filtered = available
        return random.choice(filtered)

    elif difficulty == "보통":
        # 3~5글자 단어
        filtered = [w for w in available if 3 <= len(w) <= 5]
        if not filtered:
            filtered = available
        return random.choice(filtered)

    elif difficulty == "어려움":
        # 6~9글자 단어
        filtered = [w for w in available if 6 <= len(w) <= 9]
        if not filtered:
            filtered = available
        return random.choice(filtered)

    else:  # 극악
        # 가장 긴 단어
        return max(available, key=lambda w: len(w))


def _draw_player_turn_screen(
    state: GameState,
    required: str,
    hint_count: list[int],
    show_count: list[int],
    error_msg: str = "",
    error_hint: str = "",
) -> None:
    clear()
    print_banner()
    print_game_header(
        turn=state.turn,
        current_word=state.current_word,
        required_char=required or "아무 글자",
        player_score=state.player_score,
        cpu_score=state.cpu_score,
        player_mistakes=state.player_mistakes,
        difficulty=state.difficulty,
    )

    if state.history:
        print()
        recent = state.history[-5:]
        print(c("  최근 기록:", DIM))
        for rec in recent:
            tag = c("나  ", FG_BRIGHT_GREEN) if rec.player == "player" else c("봇  ", FG_BRIGHT_RED)
            print(f"    {tag}: {c(rec.word, FG_BRIGHT_YELLOW)}")

    if error_msg:
        print()
        print_error(error_msg, error_hint)

    max_show = SHOW_MAX_USES.get(state.difficulty, 1)
    show_remaining = max_show - show_count[0]

    print()
    print(c(
        f"  명령어: /quit 즉시종료  /end 결과보기  "
        f"/hint 힌트 - {3 - hint_count[0]}회  "
        f"/show 단어보기 - {show_remaining}회  "
        f"/skip 이번 턴 포기",
        DIM
    ))
    print()


def run_player_turn(
    state: GameState,
    hint_count: list[int],
    show_count: list[int],
) -> Optional[str]:
    required = state.get_next_char_required() if state.current_word else ""
    _draw_player_turn_screen(state, required, hint_count, show_count)

    while True:
        word = prompt_word(required or "아무 글자")

        if word.lower() in ("/quit", "q", "quit", "exit"):
            return None

        if word.lower() == "/end":
            return "__END__"

        if word.lower() == "/skip":
            return "__SKIP__"

        if word.lower() == "/hint":
            if hint_count[0] >= 3:
                _draw_player_turn_screen(state, required, hint_count, show_count)
                print(c("  힌트를 모두 사용했습니다. (최대 3회)", FG_BRIGHT_RED))
                print()
            else:
                candidates = state.words_index.get(required, []) if required else []
                available = [w for w in candidates if w not in state.used_words]
                if available:
                    hint_word = random.choice(available)
                    hint_count[0] += 1
                    _draw_player_turn_screen(state, required, hint_count, show_count)
                    print_hint(hint_word, 3 - hint_count[0])
                    input(c("  [엔터] 계속", DIM))
                    _draw_player_turn_screen(state, required, hint_count, show_count)
                else:
                    _draw_player_turn_screen(state, required, hint_count, show_count)
                    print(c("  힌트로 제안할 단어가 없습니다.", FG_YELLOW))
                    print()
            continue

        if word.lower() == "/show":
            max_show = SHOW_MAX_USES.get(state.difficulty, 1)
            if show_count[0] >= max_show:
                _draw_player_turn_screen(state, required, hint_count, show_count)
                print(c(f"  /show는 최대 {max_show}회까지만 사용할 수 있습니다.", FG_BRIGHT_RED))
                print()
            else:
                show_word = _get_show_word(state)
                show_count[0] += 1
                max_show = SHOW_MAX_USES.get(state.difficulty, 1)
                show_remaining = max_show - show_count[0]

                # 난이도별 안내 메시지
                length_desc = {
                    "쉬움": "2~3글자",
                    "보통": "3~5글자",
                    "어려움": "6~9글자",
                    "극악": "가장 긴",
                }.get(state.difficulty, "")

                _draw_player_turn_screen(state, required, hint_count, show_count)
                if show_word:
                    print(c(f"  사용 가능한 단어 ({length_desc}): ", FG_BRIGHT_YELLOW, BOLD) + c(show_word, FG_BRIGHT_WHITE, BOLD))
                    print(c(f"  남은 /show: {show_remaining}회", DIM))
                else:
                    print(c("  사용 가능한 단어를 찾을 수 없습니다.", FG_YELLOW))
                print()
                input(c("  [엔터] 계속", DIM))
                _draw_player_turn_screen(state, required, hint_count, show_count)
            continue

        reason = state.validate_word(word)
        if reason == WordRejectReason.OK:
            return word

        msg, hint = build_reject_message(reason, state.current_word, word)
        state.player_mistakes += 1

        if state.player_mistakes >= MAX_MISTAKES:
            _draw_player_turn_screen(state, required, hint_count, show_count, msg, hint)
            print_mistake_warning(state.player_mistakes)
            print()
            print(c("  오답 5회! 게임 오버입니다.", FG_BRIGHT_RED, BOLD))
            time.sleep(2.5)
            return "__LOSE__"

        _draw_player_turn_screen(state, required, hint_count, show_count, msg, hint)
        print_mistake_warning(state.player_mistakes)
        time.sleep(2.0)
        _draw_player_turn_screen(state, required, hint_count, show_count)


def run_bot_turn(state: GameState, cpu: CpuPlayer) -> Optional[str]:
    think_time = cpu.think()
    print()
    print_bot_thinking(think_time)
    word = cpu.make_move(state)
    return word


def run_game(words: list[str], difficulty: str) -> None:
    word_index = build_word_index(words)
    words_set = set(words)

    state = GameState(
        words_index=word_index,
        all_words_set=words_set,
        difficulty=difficulty,
    )
    cpu = CpuPlayer(difficulty=difficulty)
    game_start = time.time()
    hint_count = [0]
    show_count = [0]

    first_word = select_first_word(state)
    if first_word:
        state.apply_word(first_word, "cpu", 0)
        clear()
        print_banner()
        print(c(f"\n  게임 시작! 봇의 첫 단어: ", FG_BRIGHT_WHITE) + c(first_word, FG_BRIGHT_YELLOW, BOLD))
        print(c(f"  '{apply_dueum(first_word[-1])}'(으)로 시작하는 단어를 입력하세요!", FG_BRIGHT_WHITE))
        print()
        time.sleep(1.5)

    while state.result == GameResult.ONGOING:

        result = run_player_turn(state, hint_count, show_count)

        if result is None:
            state.result = GameResult.CPU_WIN
            break

        if result == "__END__":
            state.result = GameResult.PLAYER_QUIT_END
            break

        if result == "__LOSE__":
            state.result = GameResult.PLAYER_LOSE_MISTAKES
            break

        if result == "__SKIP__":
            clear()
            print_banner()
            print(c("  이번 턴을 포기했습니다. 봇의 차례로 넘어갑니다.", FG_YELLOW))
            time.sleep(1.2)
        else:
            state.apply_word(result, "player", 0)
            clear()
            print_banner()
            print_game_header(
                turn=state.turn,
                current_word=state.current_word,
                required_char=state.get_next_char_required(),
                player_score=state.player_score,
                cpu_score=state.cpu_score,
                player_mistakes=state.player_mistakes,
                difficulty=state.difficulty,
            )
            print_word_played("player", result, state.player_score, is_cpu=False)
            time.sleep(0.8)

        bot_word = run_bot_turn(state, cpu)

        if bot_word is None:
            state.result = GameResult.PLAYER_WIN
            clear()
            print_banner()
            print(c("\n  봇이 단어를 찾지 못했습니다! 승리!", FG_BRIGHT_GREEN, BOLD))
            time.sleep(2.0)
            break

        state.apply_word(bot_word, "cpu", 0)
        clear()
        print_banner()
        print_game_header(
            turn=state.turn,
            current_word=state.current_word,
            required_char=state.get_next_char_required(),
            player_score=state.player_score,
            cpu_score=state.cpu_score,
            player_mistakes=state.player_mistakes,
            difficulty=state.difficulty,
        )
        print_word_played("cpu", bot_word, state.cpu_score, is_cpu=True)
        time.sleep(1.2)

    elapsed = time.time() - game_start

    if state.result == GameResult.CPU_WIN and hint_count[0] == 0 and state.turn <= 1:
        return

    clear()
    print_banner()
    print_result_screen(
        result_name=state.result.value,
        player_score=state.player_score,
        cpu_score=state.cpu_score,
        total_turns=state.turn,
        history=state.history,
        elapsed=elapsed,
        player_mistakes=state.player_mistakes,
    )
    input(c("  [엔터] 계속", DIM))


def show_main_menu() -> Optional[dict]:
    clear()
    print_banner()

    difficulty_choice = prompt_menu(
        DIFFICULTY_OPTIONS,
        title="난이도 선택",
    )
    if difficulty_choice not in DIFFICULTY_MAP:
        difficulty_choice = "2"
    difficulty = DIFFICULTY_MAP[difficulty_choice]

    return {"difficulty": difficulty}


def show_loading_screen(words: list[str]) -> None:
    clear()
    print_banner()
    print(c(f"\n  단어 DB 로딩 중...", FG_BRIGHT_WHITE))
    print(c(f"  총 {len(words)}개 단어 준비 완료!", FG_BRIGHT_GREEN, BOLD))
    print()
    time.sleep(1.0)


def run() -> None:
    try:
        clear()
        print_banner()
        print(c("  단어 데이터 준비 중...", FG_BRIGHT_WHITE))
        print()

        words = load_words()

        if len(words) < 100:
            print(c("  단어 수집 중 (최초 실행 시 시간이 걸릴 수 있습니다)...", FG_BRIGHT_WHITE))
            words = collect_words(verbose=True)

        show_loading_screen(words)

        while True:
            config = show_main_menu()
            if config is None:
                break

            run_game(
                words=words,
                difficulty=config["difficulty"],
            )

            clear()
            print_banner()
            again = prompt_menu(
                [("1", "다시 플레이"), ("2", "종료")],
                title="게임 종료",
            )
            if again != "1":
                break

        clear()
        print_banner()
        print(c("\n  플레이해주셔서 감사합니다!\n", FG_BRIGHT_WHITE, BOLD))

    except KeyboardInterrupt:
        print(c("\n\n  게임을 종료합니다.\n", FG_BRIGHT_RED))
        sys.exit(0)
