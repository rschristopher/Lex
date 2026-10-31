"""Willpower resist bonus against mental attacks, on the d20 scale."""

from __future__ import annotations


def willpower_resist_bonus(score: int) -> int:
    """+0 up to 10, +1 per 5 points to +10 at 60, +1 per 4 points to +20 at 100."""
    s = int(score)
    if s <= 10:
        return 0
    if s <= 60:
        return (s - 10) // 5
    return min(20, 10 + (s - 60) // 4)
