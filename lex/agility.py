"""Agility bonus to strike, defense, and pulling a blow."""

from __future__ import annotations

AGILITY_CHANNELS = ("strike", "defense")


def agility_bonus(score: int) -> int:
    return max(0, int(score) // 5 - 2)


def reflex_free(score: int) -> int:
    """Reflex Defense rolls per melee with no penalty."""
    return 1 + agility_bonus(score)


def reflex_penalty(score: int, nth: int) -> int:
    """Penalty on the nth Reflex Defense in a melee: 0 while free, then -2 cumulative."""
    return -2 * max(0, int(nth) - reflex_free(score))
