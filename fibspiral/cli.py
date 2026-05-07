"""CLI entry-point for fibspiral.

Usage
-----
    python -m fibspiral [N]

Prints the Fibonacci sequence F(0)…F(N) (N+1 values) with the ratio of
each term to its predecessor, illustrating convergence toward φ.
"""

from __future__ import annotations

import sys

from .core import PHI, fib_sequence


def main(argv: list[str] | None = None) -> None:
    """Print N+1 Fibonacci numbers and their ratios to stdout."""
    argv = sys.argv[1:] if argv is None else argv

    if argv and not argv[0].isdigit():
        print("Usage: python -m fibspiral [N]  (N must be a non-negative integer)")
        sys.exit(1)

    n = int(argv[0]) if argv else 12

    terms = list(fib_sequence(n + 1))  # F(0) … F(n)

    header = f"Fibonacci sequence  (n={n}, φ ≈ {PHI:.10f})"
    sep = "─" * len(header)
    print(header)
    print(sep)
    print(f"{'i':>4}  {'F(i)':>12}  {'F(i)/F(i−1)':>14}")
    print(f"{'─'*4}  {'─'*12}  {'─'*14}")

    for i, val in enumerate(terms):
        if i == 0:
            ratio_str = "        —"
        elif terms[i - 1] == 0:
            ratio_str = "          ∞"
        else:
            ratio = val / terms[i - 1]
            ratio_str = f"{ratio:14.10f}"
        print(f"{i:>4}  {val:>12}  {ratio_str}")

    print(sep)
