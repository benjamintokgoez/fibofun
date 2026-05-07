"""Tests for fibspiral.cli and fibspiral.export."""

from __future__ import annotations

import json

import pytest

from fibspiral.cli import main
from fibspiral.export import build_payload, export

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCLI:
    def test_default_output(self, capsys):
        main([])
        out = capsys.readouterr().out
        assert "F(i)" in out
        assert "φ" in out

    def test_n12_has_13_rows(self, capsys):
        main(["12"])
        out = capsys.readouterr().out
        # F(0)…F(12) = 13 data rows in the table
        data_lines = [
            ln for ln in out.splitlines() if ln.strip() and ln.strip()[0].isdigit()
        ]
        assert len(data_lines) == 13

    def test_ratios_present(self, capsys):
        main(["5"])
        out = capsys.readouterr().out
        assert "1.6" in out  # ratio approaching phi

    def test_f0_no_ratio(self, capsys):
        main(["3"])
        out = capsys.readouterr().out
        assert "—" in out  # no ratio for F(0)

    def test_invalid_arg_exits(self):
        with pytest.raises(SystemExit):
            main(["abc"])

    def test_zero_n(self, capsys):
        main(["0"])
        out = capsys.readouterr().out
        # Should print at least the header and F(0)
        assert "0" in out


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class TestBuildPayload:
    def test_n12_square_count(self):
        payload = build_payload(12)
        assert len(payload["squares"]) == 12

    def test_phi_present(self):
        payload = build_payload(12)
        assert abs(payload["phi"] - 1.6180339887) < 1e-9

    def test_squares_have_required_keys(self):
        required = {
            "index", "fib_index", "value", "x", "y", "side",
            "arc_cx", "arc_cy", "arc_r", "arc_start_angle",
            "ratio_to_previous",
        }
        for sq in build_payload(12)["squares"]:
            assert required.issubset(sq.keys())

    def test_bounds_correct(self):
        payload = build_payload(12)
        b = payload["bounds"]
        assert b["width"] > 0
        assert b["height"] > 0

    def test_first_ratio_is_none(self):
        """F(1)/F(0) is undefined — should be None."""
        payload = build_payload(12)
        assert payload["squares"][0]["ratio_to_previous"] is None


class TestExport:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "out.json"
        export(out, n=6)
        assert out.exists()

    def test_valid_json(self, tmp_path):
        out = tmp_path / "data.json"
        export(out, n=6)
        data = json.loads(out.read_text())
        assert data["n"] == 6
        assert len(data["squares"]) == 6

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "nested" / "dir" / "data.json"
        export(out, n=3)
        assert out.exists()
