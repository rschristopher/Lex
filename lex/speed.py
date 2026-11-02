"""Top speed from the Speed attribute (docs/universal-system.md, Attributes)."""

from __future__ import annotations

LIGHT = 299_792_458.0  # m/s


def top_speed_ms(score: float) -> float:
    """0.7 m/s per point to 30; 21 m/s x 10^((Speed - 30) / 8.39) to 90; c x 5^(Speed - 90) above, to 100."""
    s = min(float(score), 100.0)
    if s <= 30:
        return 0.7 * s
    if s <= 90:
        return 21.0 * 10 ** ((s - 30) / 8.39)
    return LIGHT * 5 ** (s - 90)
