"""Easing curves and timing helpers. All take and return values in 0..1."""
import math

__all__ = [
    "clamp", "progress", "lerp",
    "linear", "in_cubic", "out_cubic", "in_out_cubic",
    "out_expo", "in_expo", "out_back", "out_elastic",
]


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def progress(t, start, duration):
    """How far through [start, start+duration] the time t is, clamped to 0..1."""
    if duration <= 0:
        return 1.0 if t >= start else 0.0
    return clamp((t - start) / duration)


def lerp(a, b, p):
    return a + (b - a) * p


def linear(p):
    return p


def in_cubic(p):
    return p ** 3


def out_cubic(p):
    return 1 - (1 - p) ** 3


def in_out_cubic(p):
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def out_expo(p):
    return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)


def in_expo(p):
    return 0.0 if p <= 0 else 2 ** (10 * p - 10)


def out_back(p, s=1.70158):
    p -= 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


def out_elastic(p):
    if p in (0, 1):
        return p
    return 2 ** (-10 * p) * math.sin((p * 10 - 0.75) * (2 * math.pi) / 3) + 1
