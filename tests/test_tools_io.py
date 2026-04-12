"""Tests for IO tool module (mcp-server/tools/io.py)."""

from unittest.mock import patch

import pytest
from tools import io as io_tools


class TestMeasure:
    def test_valid_body_measurement(self):
        with patch("tools.io.send_fusion_command", return_value={"success": True}) as mock:
            io_tools.measure("body")
            mock.assert_called_once_with("measure", {"type": "body"})

    def test_valid_edge_measurement(self):
        with patch("tools.io.send_fusion_command", return_value={"success": True}) as mock:
            io_tools.measure("edge", edge_index=2)
            mock.assert_called_once_with("measure", {"type": "edge", "edge_index": 2})

    def test_invalid_type_rejected(self):
        with pytest.raises(ValueError, match="Invalid measurement_type"):
            io_tools.measure("volume")


class TestGetBodyInfo:
    def test_default_body(self):
        with patch("tools.io.send_fusion_command", return_value={"success": True}) as mock:
            io_tools.get_body_info()
            mock.assert_called_once_with("get_body_info", {})

    def test_specific_body(self):
        with patch("tools.io.send_fusion_command", return_value={"success": True}) as mock:
            io_tools.get_body_info(body_index=2)
            mock.assert_called_once_with("get_body_info", {"body_index": 2})


class TestImportMesh:
    def test_invalid_unit_rejected(self):
        with pytest.raises(ValueError, match="Invalid unit"):
            io_tools.import_mesh("~/Desktop/test.stl", unit="meters")

    def test_valid_units(self):
        for unit in ["mm", "cm", "in"]:
            with patch("tools.io.send_fusion_command", return_value={"success": True}):
                with patch("tools.io.validate_filepath", return_value="~/Desktop/test.stl"):
                    io_tools.import_mesh("~/Desktop/test.stl", unit=unit)


class TestExportStl:
    def test_filepath_validation_called(self):
        with (
            patch("tools.io.send_fusion_command", return_value={"success": True}),
            patch("tools.io.validate_filepath", return_value="/home/user/Desktop/test.stl") as mock_validate,
        ):
            io_tools.export_stl("~/Desktop/test.stl")
            mock_validate.assert_called_once_with("~/Desktop/test.stl", allowed_extensions=[".stl"])


class TestFitView:
    def test_no_params(self):
        with patch("tools.io.send_fusion_command", return_value={"success": True}) as mock:
            io_tools.fit_view()
            mock.assert_called_once_with("fit_view", {})
