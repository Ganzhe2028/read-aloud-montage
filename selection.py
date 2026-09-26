"""Choose a contiguous excerpt from locally detected speech intervals."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Excerpt:
    start: float
    end: float
    speech_seconds: float
    first_speech_at: float
    warning: str = ""


def choose_excerpt(
    speech_intervals: list[tuple[float, float]],
    duration: float,
    *,
    target_seconds: float = 17.0,
    max_seconds: float = 21.0,
) -> Excerpt | None:
    """Keep real speech, including short readings that start late in a recording."""
    intervals = sorted(
        (max(0.0, start), min(duration, end))
        for start, end in speech_intervals
        if end > start and start < duration
    )
    intervals = [(start, end) for start, end in intervals if end - start >= 0.25]
    if not intervals:
        return None

    first_speech_at = intervals[0][0]
    groups: list[list[float]] = []
    for start, end in intervals:
        if groups and start - groups[-1][1] <= 1.0 and end - groups[-1][0] <= max_seconds:
            groups[-1][1] = max(groups[-1][1], end)
        else:
            groups.append([start, end])

    candidates: list[tuple[float, float, float, float, float]] = []
    for group_start, group_end in groups:
        if group_end - group_start < 2.0:
            continue
        start = max(0.0, group_start - 0.15)
        end = min(duration, group_end + 0.15)
        if end - start > max_seconds:
            end = start + max_seconds
        speech_seconds = sum(
            max(0.0, min(end, speech_end) - max(start, speech_start))
            for speech_start, speech_end in intervals
        )
        coverage = speech_seconds / (end - start)
        if coverage < 0.45:
            continue
        length = end - start
        score = coverage * 3 + min(length, target_seconds) / target_seconds
        score -= max(0.0, length - target_seconds) * 0.02
        score -= (start / max(duration, 1.0)) * 0.03
        candidates.append((score, start, end, speech_seconds, coverage))

    if not candidates:
        return None
    long_clear = [item for item in candidates if item[2] - item[1] >= 12 and item[4] >= 0.65]
    chosen = min(long_clear, key=lambda item: (item[1], -item[0])) if long_clear else max(candidates)
    _, start, end, speech_seconds, _ = chosen
    warnings = []
    if first_speech_at >= 5:
        warnings.append(f"开头约 {first_speech_at:.1f} 秒未检测到人声，已避开")
    if end - start < 8:
        warnings.append("可用朗读较短，请试听")
    return Excerpt(start, end, speech_seconds, first_speech_at, "；".join(warnings))
