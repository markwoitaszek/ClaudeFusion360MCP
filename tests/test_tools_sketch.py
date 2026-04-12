"""Tests for sketch tool module (mcp-server/tools/sketch.py)."""

from unittest.mock import patch

import pytest
from tools import sketch


class TestCreateSketch:
    def test_valid_plane(self):
        with patch("tools.sketch.send_fusion_command", return_value={"success": True}) as mock:
            result = sketch.create_sketch("XY")
            mock.assert_called_once_with("create_sketch", {"plane": "XY", "offset": 0})
            assert result["success"]

    def test_with_offset(self):
        with patch("tools.sketch.send_fusion_command", return_value={"success": True}) as mock:
            sketch.create_sketch("XZ", offset=5.0)
            mock.assert_called_once_with("create_sketch", {"plane": "XZ", "offset": 5.0})

    def test_invalid_plane_rejected(self):
        with pytest.raises(ValueError, match="Invalid plane"):
            sketch.create_sketch("AB")


class TestDrawCircle:
    def test_valid_circle(self):
        with patch("tools.sketch.send_fusion_command", return_value={"success": True}) as mock:
            sketch.draw_circle(0, 0, 5.0)
            mock.assert_called_once_with("draw_circle", {"center_x": 0, "center_y": 0, "radius": 5.0})

    def test_zero_radius_rejected(self):
        with pytest.raises(ValueError, match="radius must be positive"):
            sketch.draw_circle(0, 0, 0)

    def test_negative_radius_rejected(self):
        with pytest.raises(ValueError, match="radius must be positive"):
            sketch.draw_circle(0, 0, -1)


class TestDrawPolygon:
    def test_valid_polygon(self):
        with patch("tools.sketch.send_fusion_command", return_value={"success": True}) as mock:
            sketch.draw_polygon(0, 0, 5.0, sides=8)
            mock.assert_called_once_with("draw_polygon", {"center_x": 0, "center_y": 0, "radius": 5.0, "sides": 8})

    def test_too_few_sides_rejected(self):
        with pytest.raises(ValueError, match="sides must be at least 3"):
            sketch.draw_polygon(0, 0, 5.0, sides=2)


class TestUndo:
    def test_default_count(self):
        with patch("tools.sketch.send_fusion_command", return_value={"success": True}) as mock:
            sketch.undo()
            mock.assert_called_once_with("undo", {"count": 1})

    def test_zero_count_rejected(self):
        with pytest.raises(ValueError, match="count must be at least 1"):
            sketch.undo(count=0)


class TestDrawLine:
    def test_valid_line(self):
        with patch("tools.sketch.send_fusion_command", return_value={"success": True}) as mock:
            sketch.draw_line(0, 0, 5, 5)
            mock.assert_called_once_with("draw_line", {"x1": 0, "y1": 0, "x2": 5, "y2": 5})


class TestBatch:
    def test_batch_forwarding(self):
        commands = [{"name": "create_sketch", "params": {"plane": "XY"}}]
        with patch("tools.sketch.send_fusion_command", return_value={"success": True}) as mock:
            sketch.batch(commands)
            mock.assert_called_once_with("batch", {"commands": commands})
