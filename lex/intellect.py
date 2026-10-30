"""Intellect bonus to knowledge and technical skill rolls."""

from __future__ import annotations

from lex.agility import agility_bonus


def intellect_bonus(score: int) -> int:
    """Same formula as the Agility bonus."""
    return agility_bonus(score)
