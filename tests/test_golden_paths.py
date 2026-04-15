"""Golden path workflow tests (REQ-P2-3).

These tests call tool functions (not send_fusion_command directly) to exercise
the full validation pipeline. IPC is mocked since live Fusion 360 is not required.

Each test corresponds to a golden path workflow in docs/golden-paths.md.
"""

from unittest.mock import patch

from tools import io as io_tools


class TestGP1ExtrudedBox:
    """GP1: Extruded box workflow."""

    def test_ping_connectivity(self):
        with patch("tools.io.send_fusion_command", return_value={"success": True, "status": "ok"}) as mock:
            result = io_tools.ping()
            assert result["success"] is True
            mock.assert_called_once_with("ping", {}, timeout_s=5.0)

    def test_measure_body_returns_dimensions(self):
        expected = {
            "success": True,
            "volume_cm3": 30.0,
            "surface_area_cm2": 62.0,
            "bounding_box": {"size": {"x": 5.0, "y": 3.0, "z": 2.0}},
        }
        with patch("tools.io.send_fusion_command", return_value=expected):
            result = io_tools.measure("body")
            assert result["success"] is True
            assert result["volume_cm3"] == 30.0

    def test_export_stl_validates_path(self):
        with (
            patch("tools.io.send_fusion_command", return_value={"success": True}),
            patch("tools.io.validate_filepath", return_value="/home/user/Desktop/box.stl") as mock_val,
        ):
            io_tools.export_stl("~/Desktop/box.stl")
            mock_val.assert_called_once_with("~/Desktop/box.stl", allowed_extensions=[".stl"])


class TestGP2RevolvedBody:
    """GP2: Revolved body with Z-negation."""

    def test_measure_after_revolve(self):
        expected = {"success": True, "volume_cm3": 245.0}
        with patch("tools.io.send_fusion_command", return_value=expected):
            result = io_tools.measure("body")
            assert result["success"] is True


class TestGP3TwoComponentAssembly:
    """GP3: Two-component assembly."""

    def test_get_design_info_shows_components(self):
        expected = {
            "success": True,
            "name": "BoxAssembly",
            "component_count": 2,
            "body_count": 2,
        }
        with patch("tools.io.send_fusion_command", return_value=expected):
            result = io_tools.get_design_info()
            assert result["component_count"] == 2

    def test_export_step_validates_extensions(self):
        with (
            patch("tools.io.send_fusion_command", return_value={"success": True}),
            patch("tools.io.validate_filepath", return_value="/home/user/Desktop/assembly.step") as mock_val,
        ):
            io_tools.export_step("~/Desktop/assembly.step")
            mock_val.assert_called_once_with("~/Desktop/assembly.step", allowed_extensions=[".step", ".stp"])
