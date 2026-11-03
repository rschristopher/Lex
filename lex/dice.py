"""The campaign die. Every bonus is stored on a d20 scale (+1 is 5%, no bonus succeeds on 11+, 50%);
a roll target converts to any die by probability: the closest chance the die can give."""

from __future__ import annotations

import random
import re
from functools import lru_cache

_DIE = re.compile(r"^\s*(\d*)d(\d+)\s*$", re.I)


def parse(die: str) -> tuple[int, int]:
    m = _DIE.match(die or "")
    if not m:
        raise ValueError(f"not a die: {die!r}")
    n, sides = int(m.group(1) or 1), int(m.group(2))
    if n < 1 or sides < 2:
        raise ValueError(f"not a die: {die!r}")
    return n, sides


@lru_cache(maxsize=64)
def distribution(die: str) -> dict[int, float]:
    n, sides = parse(die)
    dist = {0: 1.0}
    for _ in range(n):
        nxt: dict[int, float] = {}
        for total, p in dist.items():
            for face in range(1, sides + 1):
                nxt[total + face] = nxt.get(total + face, 0.0) + p / sides
        dist = nxt
    return dist


def span(die: str) -> tuple[int, int]:
    n, sides = parse(die)
    return n, n * sides


def chance(bonus: int | float) -> float:
    """Chance of success for a d20-scale bonus: 50% at +0, 5% per point, within 0 to 100%."""
    return min(1.0, max(0.0, 0.5 + 0.05 * float(bonus)))


def _success_chance(die: str, k: int, low: bool) -> float:
    dist = distribution(die)
    return sum(p for t, p in dist.items() if (t <= k if low else t >= k))


def target(bonus: int | float, die: str = "d20", low: bool = False) -> int:
    """The roll needed: k or higher (or k or lower on a low die) whose chance is closest to the bonus's."""
    want = chance(bonus)
    lo, hi = span(die)
    best, best_diff = lo if low else hi, 2.0
    candidates = range(lo, hi + 1) if low else range(hi, lo - 1, -1)
    for k in candidates:
        diff = abs(_success_chance(die, k, low) - want)
        if diff < best_diff - 1e-12:
            best, best_diff = k, diff
    return best


def meets(roll: int, needed: int, low: bool = False) -> bool:
    return roll <= needed if low else roll >= needed


def describe(needed: int, low: bool = False) -> str:
    return f"{needed} or {'lower' if low else 'higher'}"


def d20_equivalent(roll: int, die: str = "d20", low: bool = False) -> float:
    """A roll on any die as the d20 roll with the same chance of doing at least as well."""
    q = _success_chance(die, roll, low)
    return 21 - 20 * q


def roll(die: str, rng: random.Random | None = None) -> int:
    n, sides = parse(die)
    r = rng or random
    return sum(r.randint(1, sides) for _ in range(n))


def valid(value: int, die: str) -> bool:
    lo, hi = span(die)
    return isinstance(value, int) and lo <= value <= hi
