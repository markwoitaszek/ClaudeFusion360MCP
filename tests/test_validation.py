"""Tests for validation helpers (mcp-server/validation.py)."""

import pytest
from validation import validate_axis, validate_count, validate_enum, validate_plane, validate_positive, validate_range


class TestValidatePlane:
    def test_valid_planes(self):
        assert validate_plane("XY") == "XY"
        assert validate_plane("XZ") == "XZ"
        assert validate_plane("YZ") == "YZ"

    def test_invalid_plane(self):
        with pytest.raises(ValueError, match="Invalid plane"):
            validate_plane("AB")

    def test_lowercase_plane(self):
        with pytest.raises(ValueError, match="Invalid plane"):
            validate_plane("xy")


class TestValidateAxis:
    def test_valid_axes(self):
        assert validate_axis("X") == "X"
        assert validate_axis("Y") == "Y"
        assert validate_axis("Z") == "Z"

    def test_invalid_axis(self):
        with pytest.raises(ValueError, match="Invalid axis"):
            validate_axis("W")


class TestValidateEnum:
    def test_valid_value(self):
        assert validate_enum("cut", ["cut", "join", "intersect"], "operation") == "cut"

    def test_invalid_value(self):
        with pytest.raises(ValueError, match="Invalid operation.*'merge'"):
            validate_enum("merge", ["cut", "join", "intersect"], "operation")


class TestValidatePositive:
    def test_positive_value(self):
        assert validate_positive(1.5, "radius") == 1.5

    def test_zero_rejected(self):
        with pytest.raises(ValueError, match="radius must be positive"):
            validate_positive(0, "radius")

    def test_negative_rejected(self):
        with pytest.raises(ValueError, match="radius must be positive"):
            validate_positive(-1, "radius")


class TestValidateRange:
    def test_within_range(self):
        assert validate_range(5, 0, 10, "value") == 5

    def test_at_bounds(self):
        assert validate_range(0, 0, 10, "value") == 0
        assert validate_range(10, 0, 10, "value") == 10

    def test_below_range(self):
        with pytest.raises(ValueError, match="value must be between"):
            validate_range(-1, 0, 10, "value")

    def test_above_range(self):
        with pytest.raises(ValueError, match="value must be between"):
            validate_range(11, 0, 10, "value")


class TestValidateCount:
    def test_valid_count(self):
        assert validate_count(3, 2, "count") == 3

    def test_at_minimum(self):
        assert validate_count(2, 2, "count") == 2

    def test_below_minimum(self):
        with pytest.raises(ValueError, match="count must be at least 2"):
            validate_count(1, 2, "count")
