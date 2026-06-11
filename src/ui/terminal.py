from __future__ import annotations

import os
import re
import random
import sys
import time
from typing import Optional

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

FG_BLACK = "\033[30m"
FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_MAGENTA = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[37m"
FG_BRIGHT_RED = "\033[91m"
FG_BRIGHT_GREEN = "\033[92m"
FG_BRIGHT_YELLOW = "\033[93m"
FG_BRIGHT_BLUE = "\033[94m"
FG_BRIGHT_MAGENTA = "\033[95m"
FG_BRIGHT_CYAN = "\033[96m"
FG_BRIGHT_WHITE = "\033[97m"

BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"
BG_BRIGHT_BLUE = "\033[104m"
BG_BRIGHT_CYAN = "\033[106m"

SUPPORTS_COLOR = sys.stdout.isatty() or os.environ.get("TERM", "") not in ("", "dumb")

MAX_MISTAKES = 5


def c(text: str, *styles: str) -> str:
    if not SUPPORTS_COLOR:
        return text
    return "".join(styles) + text + RESET


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 80


def horizontal_rule(char: str = "─", width: Optional[int] = None) -> str:
    w = width or get_terminal_width()
    return char * w


def _strip_ansi(text: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", text)


def _display_width(text: str) -> int:
    s = _strip_ansi(text)
    w = 0
    for ch in s:
        w += 2 if ord(ch) > 0x2E7F else 1
    return w


def center_text(text: str, width: Optional[int] = None, fill: str = " ") -> str:
    w = width or get_terminal_width()
    pad = max(0, w - _display_width(text))
    left = pad // 2
    right = pad - left
    return fill * left + text + fill * right


def print_banner() -> None:
    w = get_terminal_width()
    lines = [
        c("  ██╗  ██╗██╗  ██╗██╗   ██╗████████╗██╗   ██╗", FG_BRIGHT_WHITE, BOLD),
        c("  ██║ ██╔╝██║ ██╔╝██║   ██║╚══██╔══╝██║   ██║ ", FG_BRIGHT_WHITE, BOLD),
        c("  █████╔╝ █████╔╝ ██║   ██║   ██║   ██║   ██║ ", FG_BRIGHT_WHITE, BOLD),
        c("  ██╔═██╗ ██╔═██╗ ██║   ██║   ██║   ██║   ██║ ", FG_BRIGHT_WHITE, BOLD),
        c("  ██║  ██╗██║  ██╗╚██████╔╝   ██║   ╚██████╔╝ ", FG_WHITE, BOLD),
        c("  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ", FG_WHITE, BOLD),
    ]
    subtitle = c("끄투코리아를 기반으로 한 끝말잇기 게임", FG_BRIGHT_WHITE, ITALIC)
    version = c("Made by nebula-dream", DIM)

    print()
    for line in lines:
        print(center_text(line, w))
    print()
    print(center_text(subtitle, w))
    print(center_text(version, w))
    print()
    print(c(horizontal_rule("═", w), FG_BRIGHT_WHITE))
    print()


def print_game_header(
    turn: int,
    current_word: str,
    required_char: str,
    player_score: int,
    cpu_score: int,
    player_mistakes: int = 0,
    difficulty: str = "보통",
) -> None:
    w = get_terminal_width()
    print(c(horizontal_rule("─", w), DIM))

    left = f" {c('턴', FG_BRIGHT_WHITE, BOLD)} {c(str(turn), FG_BRIGHT_YELLOW, BOLD)}"
    mistakes_display = c(f"오답 {player_mistakes}/{MAX_MISTAKES}", FG_BRIGHT_RED if player_mistakes >= 3 else FG_BRIGHT_YELLOW)
    right = (
        f"{c('나:', FG_BRIGHT_GREEN, BOLD)} {c(str(player_score), FG_BRIGHT_GREEN)}점  "
        f"{c('봇:', FG_BRIGHT_RED, BOLD)} {c(str(cpu_score), FG_BRIGHT_RED)}점  "
        f"[{mistakes_display}]  [{c(difficulty, FG_BRIGHT_MAGENTA)}] "
    )
    pad = max(0, w - _display_width(left) - _display_width(right) - 2)
    print(left + " " * pad + right)

    if current_word:
        word_display = c(f"  이전 단어: ", FG_BRIGHT_WHITE)
        word_display += c(current_word, FG_BRIGHT_YELLOW, BOLD)
        word_display += c(f"  →  다음 시작: ", FG_WHITE)
        word_display += c(f"'{required_char}'", FG_BRIGHT_WHITE, BOLD, UNDERLINE)
        print(word_display)
    else:
        print(c("  첫 번째 단어를 입력하세요!", FG_BRIGHT_WHITE))

    print(c(horizontal_rule("─", w), DIM))


def print_bot_thinking(think_time: float) -> None:
    stages = [
        f"  {c('봇', FG_BRIGHT_RED, BOLD)} 단어 생각 중",
        f"  {c('봇', FG_BRIGHT_RED, BOLD)} 단어 검색 중",
        f"  {c('봇', FG_BRIGHT_RED, BOLD)} 최선의 단어 탐색 중",
    ]
    msg = random.choice(stages) if think_time > 0.5 else stages[0]
    end_time = time.time() + think_time
    while time.time() < end_time:
        remaining = end_time - time.time()
        dots_count = int((think_time - remaining) / think_time * 3) + 1
        display = f"\r{msg}{'.' * dots_count}   "
        print(display, end="", flush=True)
        time.sleep(0.15)
    print(f"\r{' ' * 60}\r", end="", flush=True)


def print_cpu_thinking(think_time: float) -> None:
    print_bot_thinking(think_time)


def print_word_played(player: str, word: str, score: int, is_cpu: bool) -> None:
    if is_cpu:
        icon = c("봇", FG_BRIGHT_RED, BOLD)
        word_color = c(f'"{word}"', FG_BRIGHT_RED, BOLD)
    else:
        icon = c("나", FG_BRIGHT_GREEN, BOLD)
        word_color = c(f'"{word}"', FG_BRIGHT_GREEN, BOLD)
    score_str = c(f"+{len(word)}점", FG_BRIGHT_YELLOW)
    print(f"  {icon}: {word_color}  {score_str}")


def print_mistake_warning(mistakes: int) -> None:
    remaining = MAX_MISTAKES - mistakes
    bar = c("X " * mistakes, FG_BRIGHT_RED) + c("O " * remaining, DIM)
    print(c(f"  오답: {bar}", FG_BRIGHT_YELLOW))


def print_error(reason: str, hint: str = "") -> None:
    print(f"  {c('오류:', FG_BRIGHT_RED, BOLD)} {c(reason, FG_RED)}", end="")
    if hint:
        print(f"  {c('안내:', FG_BRIGHT_YELLOW)} {c(hint, FG_YELLOW)}", end="")
    print()


def print_result_screen(
    result_name: str,
    player_score: int,
    cpu_score: int,
    total_turns: int,
    history: list,
    elapsed: float,
    player_mistakes: int = 0,
) -> None:
    w = min(get_terminal_width(), 72)
    print()
    print(c(horizontal_rule("═", w), FG_BRIGHT_WHITE))

    win_labels = {
        "player_win":        ("승리!", FG_BRIGHT_GREEN),
        "cpu_win":           ("패배", FG_BRIGHT_RED),
        "draw":              ("무승부", FG_BRIGHT_YELLOW),
        "player_lose_mistakes": ("5회 오답 - 패배", FG_BRIGHT_RED),
        "player_quit_end":   ("게임 종료", FG_BRIGHT_WHITE),
    }
    label_text, label_color = win_labels.get(result_name, ("게임 종료", FG_WHITE))

    print()
    print(c(center_text(f"[ {label_text} ]", w), label_color, BOLD))
    print()
    print(c(horizontal_rule("─", w), DIM))

    if result_name == "player_quit_end":
        if player_score > cpu_score:
            verdict = c("  플레이어 승리", FG_BRIGHT_GREEN, BOLD)
        elif cpu_score > player_score:
            verdict = c("  봇 승리", FG_BRIGHT_RED, BOLD)
        else:
            verdict = c("  무승부", FG_BRIGHT_YELLOW, BOLD)
        print(verdict)
        print()

    stats_lines = [
        f"  {'플레이어 점수':10s}: {c(str(player_score), FG_BRIGHT_GREEN, BOLD)}점",
        f"  {'봇 점수':13s}: {c(str(cpu_score), FG_BRIGHT_RED, BOLD)}점",
        f"  {'총 턴 수':13s}: {c(str(total_turns), FG_BRIGHT_WHITE)}턴",
        f"  {'오답 횟수':12s}: {c(str(player_mistakes), FG_BRIGHT_RED if player_mistakes >= 3 else FG_BRIGHT_WHITE)}회",
        f"  {'게임 시간':12s}: {c(f'{elapsed:.1f}초', FG_BRIGHT_WHITE)}",
    ]
    for line in stats_lines:
        print(line)

    if history:
        print()
        print(c(horizontal_rule("─", w), DIM))
        print(c("  게임 기록 (최근 10턴):", FG_BRIGHT_WHITE, BOLD))
        recent = history[-10:]
        for record in recent:
            player_tag = c("나  ", FG_BRIGHT_GREEN) if record.player == "player" else c("봇  ", FG_BRIGHT_RED)
            print(f"    [{record.turn:3d}] {player_tag}: {c(record.word, FG_BRIGHT_YELLOW)}")

    print()
    print(c(horizontal_rule("═", w), FG_BRIGHT_WHITE))
    print()


def prompt_word(required_char: str) -> str:
    req_display = c(f"'{required_char}'", FG_BRIGHT_WHITE, BOLD, UNDERLINE)
    prompt = f"\n  {c('▶', FG_BRIGHT_GREEN)} {req_display}(으)로 시작하는 단어: "
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "/quit"


def prompt_menu(options: list[tuple[str, str]], title: str = "") -> str:
    w = get_terminal_width()
    if title:
        print(c(f"\n  {title}", FG_BRIGHT_WHITE, BOLD))
    print(c(f"  {'─' * (w - 4)}", DIM))
    for key, label in options:
        key_display = c(f"[{key}]", FG_BRIGHT_WHITE, BOLD)
        print(f"  {key_display} {label}")
    print(c(f"  {'─' * (w - 4)}", DIM))
    try:
        choice = input(c("  선택: ", FG_BRIGHT_YELLOW)).strip().lower()
        return choice
    except (EOFError, KeyboardInterrupt):
        return "q"


def get_chosung(char: str) -> str:
    HANGUL_BASE = 0xAC00
    CHOSUNG_COUNT = 21 * 28
    CHOSUNG_LIST = [
        "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ",
        "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]
    code = ord(char) - HANGUL_BASE
    if code < 0 or code > 11171:
        return char
    return CHOSUNG_LIST[code // CHOSUNG_COUNT]


def print_hint(word: str, hint_remaining: int) -> None:
    chosung_str = " ".join(get_chosung(ch) for ch in word)
    print(f"  {c('힌트:', FG_BRIGHT_YELLOW, BOLD)} {c(chosung_str, FG_YELLOW)}  ({len(word)}글자)")
    print(f"  {c(f'남은 힌트: {hint_remaining}회', DIM)}")
