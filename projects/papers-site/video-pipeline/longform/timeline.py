"""Timeline, transition, and subtitle helpers for longform videos."""

from __future__ import annotations

import math
import re
from pathlib import Path

from .models import Timeline, TimelineEntry, VisualScene


_PUNCTUATION = "，。、；：,.!?;！？:"
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[\^+./-][A-Za-z0-9]+)*|[\u4e00-\u9fff]|[^\s]")


def build_timeline(visual_scenes: list[VisualScene], transition: str = "crossfade", transition_sec: float = 0.45) -> Timeline:
    entries: list[TimelineEntry] = []
    cursor = 0.0
    for i, scene in enumerate(visual_scenes):
        duration = max(12.0, float(scene.duration_sec))
        start = round(cursor, 3)
        end = round(start + duration, 3)
        entries.append(TimelineEntry(scene_index=scene.index, start_sec=start, end_sec=end, transition="cut" if i == 0 else transition, narration=scene.narration))
        cursor = end
    return Timeline(entries=entries, total_duration_sec=round(cursor, 3), transition_sec=transition_sec)


def _srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    h, rest = divmod(millis, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _tokenize_caption(text: str) -> list[str]:
    raw_tokens = _TOKEN_RE.findall(" ".join(text.strip().split()))
    tokens: list[str] = []
    for token in raw_tokens:
        if token in _PUNCTUATION and tokens:
            tokens[-1] += token
        elif token.strip():
            tokens.append(token)
    return [token for token in tokens if token not in _PUNCTUATION]


def _join_caption_tokens(tokens: list[str]) -> str:
    text = ""
    for token in tokens:
        if not text:
            text = token
            continue
        previous = text[-1]
        current = token[0]
        if previous.isascii() and previous.isalnum() and current.isascii() and current.isalnum():
            text += " " + token
        elif previous.isascii() and previous.isalnum() and not current.isascii():
            text += " " + token
        elif not previous.isascii() and current.isascii() and current.isalnum():
            text += " " + token
        elif previous in ":：" and current.isascii() and current.isalnum():
            text += " " + token
        elif previous.isascii() and current.isascii() and current not in _PUNCTUATION and previous not in "([{/:^-":
            text += " " + token
        else:
            text += token
    return text.strip()


def _split_caption_text(text: str, target_count: int) -> list[str]:
    tokens = _tokenize_caption(text)
    if not tokens:
        clean = " ".join(text.strip().split())
        return [clean] if clean else []

    target = min(max(1, target_count), len(tokens))
    if target == 1:
        return [_join_caption_tokens(tokens)]

    total_chars = sum(len(token) for token in tokens)
    ideal = max(1, math.ceil(total_chars / target))
    chunks: list[list[str]] = []
    current: list[str] = []
    current_len = 0

    for i, token in enumerate(tokens):
        remaining_tokens = len(tokens) - i
        remaining_slots = target - len(chunks) - 1
        should_close = current and current_len + len(token) > ideal and remaining_tokens > remaining_slots
        if should_close:
            chunks.append(current)
            current = []
            current_len = 0
        current.append(token)
        current_len += len(token)

    if current:
        chunks.append(current)

    while len(chunks) < target:
        index = max(range(len(chunks)), key=lambda value: sum(len(token) for token in chunks[value]))
        chunk = chunks[index]
        if len(chunk) <= 1:
            break
        midpoint = len(chunk) // 2
        chunks[index : index + 1] = [chunk[:midpoint], chunk[midpoint:]]

    return [_join_caption_tokens(chunk) for chunk in chunks if chunk]


def _caption_blocks_for_entry(entry: TimelineEntry, max_caption_duration: float) -> list[tuple[float, float, str]]:
    duration = max(0.001, entry.end_sec - entry.start_sec)
    by_duration = max(1, math.ceil(duration / max_caption_duration))
    by_text = max(1, math.ceil(len(entry.narration) / 48))
    chunks = _split_caption_text(entry.narration, max(by_duration, by_text))
    if not chunks:
        return []

    segment_duration = duration / len(chunks)
    blocks: list[tuple[float, float, str]] = []
    cursor = entry.start_sec
    for i, chunk in enumerate(chunks):
        start = cursor
        end = entry.end_sec if i == len(chunks) - 1 else round(start + segment_duration, 3)
        blocks.append((round(start, 3), round(end, 3), chunk))
        cursor = end
    return blocks


def write_srt(timeline: Timeline, output_path: Path | str, max_caption_duration: float = 7.0) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    index = 1
    for entry in timeline.entries:
        for start, end, text in _caption_blocks_for_entry(entry, max_caption_duration):
            blocks.append(f"{index}\n{_srt_time(start)} --> {_srt_time(end)}\n{text}\n")
            index += 1
    path.write_text("\n".join(blocks), encoding="utf-8")
    return path
