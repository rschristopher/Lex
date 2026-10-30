"""Agility bonus to strike, parry, dodge, and pulling a blow."""

from __future__ import annotations

AGILITY_CHANNELS = ("attack", "parry", "dodge")


def agility_bonus(score: int) -> int:
    return max(0, int(score) // 5 - 2)
