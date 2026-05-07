"""Tests for fibspiral.core — Fibonacci computation and spiral geometry."""

from __future__ import annotations

import math

import pytest

from fibspiral.core import (
    PHI,
    fib,
    fib_iterative,
    fib_sequence,
    spiral_geometry,
)

# Reference values F(0)…F(20)
KNOWN: list[int] = [
    0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144,
    233, 377, 610, 987, 1597, 2584, 4181, 6765,
]


# ---------------------------------------------------------------------------
# fib()
# ---------------------------------------------------------------------------


class TestFibMemoised:
    def test_base_cases(self):
        assert fib(0) == 0
        assert fib(1) == 1

    @pytest.mark.parametrize("n,expected", list(enumerate(KNOWN)))
    def test_known_values(self, n, expected):
        assert fib(n) == expected

    def test_large(self):
        # Spot-check a large value; Binet's formula holds well for n≤70
        n = 30
        binet = round((PHI**n - (1 - PHI) ** n) / math.sqrt(5))
        assert fib(n) == binet

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            fib(-1)

    def test_negative_large_raises(self):
        with pytest.raises(ValueError):
            fib(-100)


# ---------------------------------------------------------------------------
# fib_iterative()
# ---------------------------------------------------------------------------


class TestFibIterative:
    @pytest.mark.parametrize("n,expected", list(enumerate(KNOWN)))
    def test_matches_reference(self, n, expected):
        assert fib_iterative(n) == expected

    def test_agrees_with_fib(self):
        for n in range(21):
            assert fib_iterative(n) == fib(n)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            fib_iterative(-1)


# ---------------------------------------------------------------------------
# fib_sequence()
# ---------------------------------------------------------------------------


class TestFibSequence:
    def test_zero_yields_nothing(self):
        assert list(fib_sequence(0)) == []

    def test_single(self):
        assert list(fib_sequence(1)) == [0]

    def test_two(self):
        assert list(fib_sequence(2)) == [0, 1]

    def test_fourteen(self):
        assert list(fib_sequence(14)) == KNOWN[:14]

    def test_all_twenty_one(self):
        assert list(fib_sequence(21)) == KNOWN

    def test_is_generator(self):
        import types

        result = fib_sequence(5)
        assert isinstance(result, types.GeneratorType)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            list(fib_sequence(-1))


# ---------------------------------------------------------------------------
# spiral_geometry()
# ---------------------------------------------------------------------------


class TestSpiralGeometry:
    def test_default_count(self):
        assert len(spiral_geometry()) == 12

    def test_explicit_count(self):
        for n in [1, 3, 6, 12, 15]:
            assert len(spiral_geometry(n)) == n

    def test_zero_squares(self):
        assert spiral_geometry(0) == []

    def test_side_equals_fibonacci(self):
        """Each square's side must equal the matching Fibonacci number F(i+1)."""
        geometry = spiral_geometry(12)
        for sq in geometry:
            assert sq["side"] == fib(sq["fib_index"])
            assert sq["value"] == sq["side"]

    def test_arc_radius_equals_side(self):
        for sq in spiral_geometry(12):
            assert sq["arc_r"] == sq["side"]

    def test_fib_indices_sequential(self):
        geometry = spiral_geometry(12)
        for i, sq in enumerate(geometry):
            assert sq["index"] == i
            assert sq["fib_index"] == i + 1

    def test_arc_start_angles_cycle(self):
        """Start angles must cycle 270, 0, 90, 180 as direction rotates."""
        expected_cycle = [270, 0, 90, 180]
        for sq in spiral_geometry(12):
            assert sq["arc_start_angle"] == expected_cycle[sq["index"] % 4]

    def test_arc_continuity(self):
        """The end-point of arc i must equal the start-point of arc i+1."""
        geometry = spiral_geometry(12)
        tol = 1e-9

        def arc_endpoints(sq):
            cx, cy, r = sq["arc_cx"], sq["arc_cy"], sq["arc_r"]
            a_start = math.radians(sq["arc_start_angle"])
            a_end = a_start + math.pi / 2  # CW 90°
            start = (cx + r * math.cos(a_start), cy + r * math.sin(a_start))
            end = (cx + r * math.cos(a_end), cy + r * math.sin(a_end))
            return start, end

        prev_end = None
        for sq in geometry:
            start, end = arc_endpoints(sq)
            if prev_end is not None:
                assert abs(start[0] - prev_end[0]) < tol, (
                    f"Arc {sq['index']} start-x {start[0]} ≠ prev end-x {prev_end[0]}"
                )
                assert abs(start[1] - prev_end[1]) < tol, (
                    f"Arc {sq['index']} start-y {start[1]} ≠ prev end-y {prev_end[1]}"
                )
            prev_end = end

    def test_squares_tile_without_overlap(self):
        """No two squares should overlap (disjoint interiors)."""
        geometry = spiral_geometry(12)

        def overlaps(a, b):
            # Two rectangles overlap if they intersect in both x and y
            return (
                a["x"] < b["x"] + b["side"]
                and a["x"] + a["side"] > b["x"]
                and a["y"] < b["y"] + b["side"]
                and a["y"] + a["side"] > b["y"]
            )

        for i, a in enumerate(geometry):
            for j, b in enumerate(geometry):
                if i >= j:
                    continue
                msg = (
                    f"Square {i} (side={a['side']}) overlaps"
                    f" square {j} (side={b['side']})"
                )
                assert not overlaps(a, b), msg

    def test_bounding_box_is_fibonacci_rectangle(self):
        """The overall bounding box should be a Fibonacci rectangle."""
        geometry = spiral_geometry(12)
        xs = [sq["x"] for sq in geometry] + [sq["x"] + sq["side"] for sq in geometry]
        ys = [sq["y"] for sq in geometry] + [sq["y"] + sq["side"] for sq in geometry]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        # For 12 terms, the rectangle should be F(12)×F(13) = 144×233
        assert width == fib(12)
        assert height == fib(13)

    def test_negative_n_raises(self):
        with pytest.raises(ValueError):
            spiral_geometry(-1)


# ---------------------------------------------------------------------------
# PHI constant
# ---------------------------------------------------------------------------


def test_phi_value():
    assert abs(PHI - 1.6180339887498948) < 1e-12


def test_phi_approaches_via_ratios():
    """Consecutive Fibonacci ratios should converge toward PHI."""
    geometry = spiral_geometry(12)
    last = geometry[-1]
    prev = geometry[-2]
    ratio = last["value"] / prev["value"]
    assert abs(ratio - PHI) < 0.01
