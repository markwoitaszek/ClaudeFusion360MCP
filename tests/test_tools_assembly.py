"""Tests for assembly tool module (mcp-server/tools/assembly.py)."""

from unittest.mock import patch

import pytest
from tools import assembly


class TestRotateComponent:
    def test_valid_rotation(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.rotate_component(45.0, "Z")
            args = mock.call_args[0]
            assert args[0] == "rotate_component"
            assert args[1]["angle"] == 45.0
            assert args[1]["axis"] == "Z"

    def test_invalid_axis_rejected(self):
        with pytest.raises(ValueError, match="Invalid axis"):
            assembly.rotate_component(45.0, "W")


class TestMoveComponent:
    def test_absolute_move(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.move_component(x=5, y=10, z=0)
            args = mock.call_args[0]
            assert args[1]["x"] == 5
            assert args[1]["y"] == 10
            assert args[1]["absolute"] is True

    def test_relative_move(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.move_component(x=5, absolute=False)
            args = mock.call_args[0]
            assert args[1]["absolute"] is False


class TestCreateComponent:
    def test_with_name(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.create_component("MyPart")
            mock.assert_called_once_with("create_component", {"name": "MyPart"})

    def test_without_name(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.create_component()
            mock.assert_called_once_with("create_component", {})


class TestListComponents:
    def test_no_params(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.list_components()
            mock.assert_called_once_with("list_components", {})


class TestDeleteComponent:
    def test_by_name(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.delete_component(name="Part1")
            mock.assert_called_once_with("delete_component", {"name": "Part1"})

    def test_by_index(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.delete_component(index=0)
            mock.assert_called_once_with("delete_component", {"index": 0})


class TestJoints:
    def test_revolute_joint(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.create_revolute_joint(x=0, y=0, z=5)
            args = mock.call_args[0]
            assert args[0] == "create_revolute_joint"
            assert args[1]["z"] == 5

    def test_slider_joint(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.create_slider_joint(x=0, y=0, z=0)
            mock.assert_called_once()

    def test_set_joint_angle(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.set_joint_angle(90.0, joint_index=0)
            mock.assert_called_once_with("set_joint_angle", {"angle": 90.0, "joint_index": 0})

    def test_set_joint_distance(self):
        with patch("tools.assembly.send_fusion_command", return_value={"success": True}) as mock:
            assembly.set_joint_distance(5.0)
            mock.assert_called_once_with("set_joint_distance", {"distance": 5.0})
