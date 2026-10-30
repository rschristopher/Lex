"""Strength dice: what a bare fist does at a Strength, and hand-to-hand damage."""

from __future__ import annotations

from lex.prefixes import exp

PATTERN = (1, 2, 3, 5, 7)
LANDINGS = ((88, "tera"), (73, "giga"), (58, "mega"), (43, "kilo"), (38, "hecto"), (33, "deka"))


def strength_dice(score: int) -> tuple[int, str]:
    """Number of d6 and prefix for a fist at this Strength."""
    s = max(1, min(int(score), 100))
    if s <= 30:
        return max(1, s // 10), "unit"
    if s < 33:
        return PATTERN[s - 28], "unit"
    for land, prefix in LANDINGS:
        if s >= land:
            q, r = divmod(s - land, 5)
            return PATTERN[r] * 10**q, prefix
    raise AssertionError(s)


def _dice_count(dice: str) -> int:
    n, _, sides = (dice or "1d6").lower().partition("d")
    if sides != "6":
        raise ValueError(f"hand-to-hand dice must be d6: {dice!r}")
    return int(n or 1)


def melee_damage(weapon_dice: str, score: int, durability: str) -> dict:
    """Strength bonus (Strength dice - 1) plus the weapon's dice, at the Strength prefix.

    A Strength prefix above the durability destroys the weapon on the blow.
    """
    n, prefix = strength_dice(score)
    return {
        "damage": f"{n - 1 + _dice_count(weapon_dice)}d6",
        "prefix": prefix,
        "destroyed": exp(prefix) > exp(durability),
    }

