"""Harm scale: a per-hit threshold. SI prefixes are nicknames for ×10^n.

Any ratio is allowed (42:1 is 4.2 deka). Convert into the target's units and
truncate toward zero. Fractions are discarded every hit — a kitten never
accumulates through a starship hull.
"""

from __future__ import annotations

PREFIXES: dict[str, int] = {
    "centi": -2,
    "deci": -1,
    "unit": 0,
    "deka": 1,
    "hecto": 2,
    "kilo": 3,
    "mega": 6,
    "giga": 9,
    "tera": 12,
}

ORDER = sorted(PREFIXES, key=PREFIXES.get)


def exp(prefix: str) -> int:
    p = (prefix or "unit").lower()
    if p not in PREFIXES:
        raise ValueError(f"unknown prefix {prefix!r}")
    return PREFIXES[p]


def factor(prefix: str | None = None, scale: float | None = None) -> float:
    """Linear size vs unit. `scale` is an exact ratio (42 = 42:1)."""
    if scale is not None:
        return float(scale)
    return 10.0 ** exp(prefix or "unit")


def hit_factor(piece: dict | None) -> float:
    """SI scale of a hits piece (unit 1, deka 10, hecto 100). Not the damage threshold."""
    if not piece:
        return 1.0
    return factor(piece.get("prefix") or "unit")


def hit_threshold(piece: dict | None) -> int:
    """Minimum damage in this layer's units that counts. Default 1. Under that, 0."""
    if not piece:
        return 1
    if piece.get("threshold") is not None:
        return max(1, int(piece["threshold"]))
    return 1


def color_band(f: float) -> str:
    """Prefix color decade for a factor. 2 stays unit (red); 42 is deka; 100 is hecto."""
    x = float(f)
    if x < 0.1:
        return "centi"
    if x < 1:
        return "deci"
    if x < 10:
        return "unit"
    if x < 100:
        return "deka"
    if x < 1000:
        return "hecto"
    if x < 1_000_000:
        return "kilo"
    if x < 1_000_000_000:
        return "mega"
    if x < 1_000_000_000_000:
        return "giga"
    return "tera"


def convert(
    amount: int | float,
    src: str = "unit",
    dst: str = "unit",
    src_scale: float | None = None,
    dst_scale: float | None = None,
    threshold: int = 1,
) -> int:
    """Amount at src, as integer points at dst. Truncates toward 0.

    `threshold` is the minimum dest points that count (default 1). Below that
    the hit is superficial — same idea as a damage threshold, at any scale.
    """
    src_f = factor(src, src_scale)
    dst_f = factor(dst, dst_scale)
    if dst_f == 0:
        return 0
    x = float(amount) * src_f / dst_f
    if x >= 0:
        n = int(x)
    else:
        n = -int(-x)
    if abs(n) < max(1, int(threshold)):
        return 0
    return n


def interacts(
    amount: int | float,
    src: str = "unit",
    dst: str = "unit",
    src_scale: float | None = None,
    dst_scale: float | None = None,
    threshold: int = 1,
) -> bool:
    return convert(amount, src, dst, src_scale, dst_scale, threshold) != 0


def bump(prefix: str, decades: int) -> str:
    """Shift a named prefix by whole decades (10 hecto → kilo)."""
    target = exp(prefix) + decades
    for name, e in PREFIXES.items():
        if e == target:
            return name
    return prefix


def describe_scale(scale: float) -> str:
    """Human ratio: 42 → '4.2 deka', 100 → 'hecto'."""
    s = float(scale)
    if s <= 0:
        return "0"
    import math

    log = math.log10(s)
    # Prefer coefficient in [1, 10): 42 → 4.2 deka, not 0.42 hecto.
    floor_e = math.floor(log)
    named = [e for e in PREFIXES.values() if e <= floor_e]
    e = max(named) if named else min(PREFIXES.values())
    name = next(n for n, v in PREFIXES.items() if v == e)
    mag = s / (10.0 ** e)
    if abs(mag - 1) < 1e-9:
        return name
    if abs(mag - round(mag)) < 1e-9:
        return f"{int(round(mag))} {name}"
    return f"{mag:.4g} {name}"
