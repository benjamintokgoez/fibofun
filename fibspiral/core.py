"""Core Fibonacci computation and golden-spiral geometry.

Coordinate system
-----------------
All geometry uses screen coordinates: x increases right, y increases *down*.
Arc angles are in degrees measured clockwise from the positive-x axis (right),
consistent with SVG's default arc direction.  Every arc sweeps exactly 90°
clockwise.

Arc-centre derivation (verified by induction)
---------------------------------------------
Squares are placed in a repeating 4-direction cycle:

    dir 0 – right :  arc_cx = x,       arc_cy = y + f,   start = 270°
    dir 1 – down  :  arc_cx = x,       arc_cy = y,        start = 0°
    dir 2 – left  :  arc_cx = x + f,   arc_cy = y,        start = 90°
    dir 3 – up    :  arc_cx = x + f,   arc_cy = y + f,    start = 180°

where (x, y) is the top-left corner of the new square and f its side length.
"""

from __future__ import annotations

import math
from collections.abc import Generator
from functools import cache

__all__ = ["PHI", "fib", "fib_iterative", "fib_sequence", "spiral_geometry"]

PHI: float = (1 + math.sqrt(5)) / 2  # golden ratio ≈ 1.6180339887…


# ---------------------------------------------------------------------------
# Fibonacci implementations
# ---------------------------------------------------------------------------


@cache
def fib(n: int) -> int:
    """Return the *n*-th Fibonacci number (memoised recursive, F(0) = 0).

    Raises ``ValueError`` for negative *n*.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    return n if n <= 1 else fib(n - 1) + fib(n - 2)


def fib_iterative(n: int) -> int:
    """Return the *n*-th Fibonacci number (pure iterative, F(0) = 0).

    Preferred for very large *n* where recursion depth is a concern.
    Raises ``ValueError`` for negative *n*.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_sequence(n: int) -> Generator[int, None, None]:
    """Yield the first *n* Fibonacci numbers starting from F(0) = 0."""
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


# ---------------------------------------------------------------------------
# Spiral geometry
# ---------------------------------------------------------------------------

#: Placement direction → (x-offset fn, y-offset fn, arc_cx fn, arc_cy fn, start°)
#: Each lambda receives (min_x, max_x, min_y, max_y, f) and returns the square
#: origin (x, y), arc centre (arc_cx, arc_cy), and arc start angle.
_DIRS = [
    # dir 0: place to the RIGHT of current bounding box
    lambda mn_x, mx_x, mn_y, mx_y, f: (mx_x, mn_y, mx_x, mn_y + f, 270),
    # dir 1: place BELOW (larger y in screen space)
    lambda mn_x, mx_x, mn_y, mx_y, f: (mn_x, mx_y, mn_x, mx_y, 0),
    # dir 2: place to the LEFT
    lambda mn_x, mx_x, mn_y, mx_y, f: (mn_x - f, mn_y, mn_x, mn_y, 90),
    # dir 3: place ABOVE (smaller y in screen space)
    lambda mn_x, mx_x, mn_y, mx_y, f: (mn_x, mn_y - f, mx_x, mn_y, 180),
]


def spiral_geometry(n: int = 12) -> list[dict]:
    """Return placement and arc data for an *n*-term Fibonacci spiral.

    Squares correspond to F(1) … F(n); F(0) = 0 is skipped because a
    zero-side square is degenerate.

    Each dictionary in the returned list has keys:

    * ``index``           – 0-based position in this list
    * ``fib_index``       – index into the Fibonacci sequence (starts at 1)
    * ``value``           – Fibonacci number (= side length)
    * ``x``, ``y``        – top-left corner of the square (screen coords)
    * ``side``            – side length (equals ``value``)
    * ``arc_cx``, ``arc_cy`` – centre of the quarter-circle arc
    * ``arc_r``           – arc radius (equals ``side``)
    * ``arc_start_angle`` – start angle in degrees (CW from positive-x)
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")

    squares: list[dict] = []
    min_x = max_x = min_y = max_y = 0

    for i in range(n):
        f = fib(i + 1)  # start from F(1)
        x, y, arc_cx, arc_cy, start_angle = _DIRS[i % 4](
            min_x, max_x, min_y, max_y, f
        )

        squares.append(
            {
                "index": i,
                "fib_index": i + 1,
                "value": f,
                "x": x,
                "y": y,
                "side": f,
                "arc_cx": arc_cx,
                "arc_cy": arc_cy,
                "arc_r": f,
                "arc_start_angle": start_angle,
            }
        )

        # Expand bounding box
        min_x = min(min_x, x)
        max_x = max(max_x, x + f)
        min_y = min(min_y, y)
        max_y = max(max_y, y + f)

    return squares
