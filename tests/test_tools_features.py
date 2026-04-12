"""Tests for features tool module (mcp-server/tools/features.py)."""

from unittest.mock import patch

import pytest
from tools import features


class TestFillet:
    def test_valid_fillet(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.fillet(0.5)
            mock.assert_called_once_with("fillet", {"radius": 0.5})

    def test_with_edges(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.fillet(0.5, edges=[0, 2])
            mock.assert_called_once_with("fillet", {"radius": 0.5, "edges": [0, 2]})

    def test_zero_radius_rejected(self):
        with pytest.raises(ValueError, match="radius must be positive"):
            features.fillet(0)


class TestChamfer:
    def test_valid_chamfer(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.chamfer(0.3)
            mock.assert_called_once_with("chamfer", {"distance": 0.3})

    def test_negative_distance_rejected(self):
        with pytest.raises(ValueError, match="distance must be positive"):
            features.chamfer(-1)


class TestShell:
    def test_valid_shell(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.shell(0.2)
            mock.assert_called_once_with("shell", {"thickness": 0.2})

    def test_zero_thickness_rejected(self):
        with pytest.raises(ValueError, match="thickness must be positive"):
            features.shell(0)


class TestDraft:
    def test_valid_draft(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.draft(2.0)
            mock.assert_called_once_with("draft", {"angle": 2.0, "pull_x": 0, "pull_y": 0, "pull_z": 1})

    def test_zero_angle_rejected(self):
        with pytest.raises(ValueError, match="angle must be positive"):
            features.draft(0)


class TestCombine:
    def test_valid_cut(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.combine(0, [1], "cut")
            mock.assert_called_once_with(
                "combine", {"target_body": 0, "tool_bodies": [1], "operation": "cut", "keep_tools": False}
            )

    def test_invalid_operation_rejected(self):
        with pytest.raises(ValueError, match="Invalid operation"):
            features.combine(0, [1], "merge")

    def test_valid_operations(self):
        for op in ["cut", "join", "intersect"]:
            with patch("tools.features.send_fusion_command", return_value={"success": True}):
                features.combine(0, [1], op)


class TestPatternRectangular:
    def test_valid_pattern(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.pattern_rectangular(4, 2.5)
            mock.assert_called_once_with(
                "pattern_rectangular", {"x_count": 4, "x_spacing": 2.5, "y_count": 1, "y_spacing": 0}
            )

    def test_count_too_low(self):
        with pytest.raises(ValueError, match="x_count must be at least 2"):
            features.pattern_rectangular(1, 2.5)

    def test_zero_spacing_rejected(self):
        with pytest.raises(ValueError, match="x_spacing must be positive"):
            features.pattern_rectangular(4, 0)


class TestPatternCircular:
    def test_valid_pattern(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.pattern_circular(6)
            mock.assert_called_once_with("pattern_circular", {"count": 6, "angle": 360, "axis": "Z"})

    def test_invalid_axis_rejected(self):
        with pytest.raises(ValueError, match="Invalid axis"):
            features.pattern_circular(6, axis="W")


class TestMirror:
    def test_valid_mirror(self):
        with patch("tools.features.send_fusion_command", return_value={"success": True}) as mock:
            features.mirror("XY")
            mock.assert_called_once_with("mirror", {"plane": "XY"})

    def test_invalid_plane_rejected(self):
        with pytest.raises(ValueError, match="Invalid plane"):
            features.mirror("AB")
