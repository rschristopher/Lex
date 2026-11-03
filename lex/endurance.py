"""Endurance bonus on resistance rolls (poison, disease, fatigue, exposure), on the d20 scale."""

from __future__ import annotations

from lex.willpower import willpower_resist_bonus


def endurance_resist_bonus(score: int) -> int:
    """Willpower is the mental mirror of Endurance: the same scale, +20 at 100."""
    return willpower_resist_bonus(score)
