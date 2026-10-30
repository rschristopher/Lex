"""Agility bonus to strike and defense, and free steps for pulling a blow."""

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


def pull_free_steps(score: int) -> int:
    """Prefix steps a blow can always be pulled down with no roll."""
    return 1 + agility_bonus(score) // 2


def pull_fails_on(score: int, steps: int) -> int:
    """d20 results that fail a pull of `steps` prefix steps: 1..extra steps past the free ones."""
    return max(0, int(steps) - pull_free_steps(score))
