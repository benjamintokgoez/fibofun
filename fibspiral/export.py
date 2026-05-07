"""Export spiral geometry to web/data.json for the static frontend.

Usage
-----
    python -m fibspiral.export [OUTPUT_PATH] [--n N]

Defaults: OUTPUT_PATH = web/data.json, N = 12.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from .core import PHI, fib_sequence, spiral_geometry


def build_payload(n: int = 12) -> dict:
    """Build the full JSON payload consumed by spiral.js."""
    squares = spiral_geometry(n)

    # Bounding box
    xs = [sq["x"] for sq in squares] + [sq["x"] + sq["side"] for sq in squares]
    ys = [sq["y"] for sq in squares] + [sq["y"] + sq["side"] for sq in squares]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Include ratio_to_previous for each square (matching fibonacci-facts.json)
    fibs = list(fib_sequence(n + 2))  # a few extra to compute ratios
    for sq in squares:
        idx = sq["fib_index"]
        prev = fibs[idx - 1] if idx >= 1 else None
        curr = fibs[idx]
        if prev and prev != 0:
            sq["ratio_to_previous"] = round(curr / prev, 10)
        else:
            sq["ratio_to_previous"] = None

    return {
        "n": n,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "phi": PHI,
        "bounds": {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y,
        },
        "squares": squares,
    }


def export(output_path: str | Path = "web/data.json", n: int = 12) -> None:
    """Write spiral geometry JSON to *output_path*."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload(n)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload['squares'])} squares → {path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    out = args[0] if args else "web/data.json"
    n_val = 12
    if "--n" in args:
        idx = args.index("--n")
        n_val = int(args[idx + 1])
    export(out, n_val)
