"""Tests for fusion-addin/FusionMCP.py pure-Python logic.

Tests execute_command (registry dispatch), handle_batch (batch validation),
and monitor_commands token logic without requiring Fusion 360.
"""

import os
import sys
import types
from unittest.mock import MagicMock, patch

# Mock the adsk module before importing FusionMCP
adsk_mock = types.ModuleType("adsk")
adsk_core_mock = types.ModuleType("adsk.core")
adsk_fusion_mock = types.ModuleType("adsk.fusion")

# Minimal stubs for classes referenced at module level
adsk_core_mock.CustomEventHandler = type("CustomEventHandler", (), {"__init__": lambda self: None})
adsk_core_mock.CustomEventArgs = MagicMock()
adsk_core_mock.Application = MagicMock()
adsk_core_mock.ValueInput = MagicMock()
adsk_core_mock.Point3D = MagicMock()
adsk_fusion_mock.FeatureOperations = MagicMock()
adsk_fusion_mock.JointGeometry = MagicMock()
adsk_fusion_mock.JointDirections = MagicMock()

adsk_mock.core = adsk_core_mock
adsk_mock.fusion = adsk_fusion_mock
sys.modules["adsk"] = adsk_mock
sys.modules["adsk.core"] = adsk_core_mock
sys.modules["adsk.fusion"] = adsk_fusion_mock

# Add fusion-addin to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fusion-addin"))

import FusionMCP  # noqa: E402


class TestExecuteCommand:
    def test_unknown_tool_returns_error(self):
        """execute_command returns error for unregistered tool names."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.activeProduct = MagicMock()
        FusionMCP.app.activeProduct.rootComponent = MagicMock()
        result = FusionMCP.execute_command({"name": "nonexistent_tool", "params": {}})
        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    def test_no_active_design_returns_error(self):
        """execute_command returns error when no design is active."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.activeProduct = None
        result = FusionMCP.execute_command({"name": "get_design_info", "params": {}})
        assert result["success"] is False
        assert "No active design" in result["error"]

    def test_handler_exception_returns_error(self):
        """execute_command catches handler exceptions and returns error dict."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.activeProduct = MagicMock()
        FusionMCP.app.activeProduct.rootComponent = MagicMock()
        # Patch a handler to raise
        with patch.dict(
            FusionMCP.HANDLER_REGISTRY, {"boom": lambda d, r, p: (_ for _ in ()).throw(ValueError("test error"))}
        ):
            result = FusionMCP.execute_command({"name": "boom", "params": {}})
            assert result["success"] is False
            assert "test error" in result["error"]


class TestHandleBatch:
    def setup_method(self):
        self.design = MagicMock()
        self.rootComp = MagicMock()

    def test_exceeds_max_batch_commands(self):
        """handle_batch rejects batches exceeding MAX_BATCH_COMMANDS."""
        commands = [{"name": "fit_view", "params": {}} for _ in range(FusionMCP.MAX_BATCH_COMMANDS + 1)]
        result = FusionMCP.handle_batch(self.design, self.rootComp, {"commands": commands})
        assert result["success"] is False
        assert "exceeds" in result["error"]

    def test_nested_batch_rejected(self):
        """handle_batch rejects nested batch commands."""
        commands = [{"name": "batch", "params": {"commands": []}}]
        result = FusionMCP.handle_batch(self.design, self.rootComp, {"commands": commands})
        assert result["success"] is False
        assert "Nested batch" in result["error"]

    def test_unknown_tool_in_batch(self):
        """handle_batch stops on unknown tool and returns partial results."""
        commands = [{"name": "nonexistent_tool_xyz", "params": {}}]
        result = FusionMCP.handle_batch(self.design, self.rootComp, {"commands": commands})
        assert result["success"] is False
        assert "Unknown tool" in result["error"]
        assert "partial_results" in result

    def test_successful_batch(self):
        """handle_batch returns all results for a successful batch."""
        mock_handler = MagicMock(return_value={"success": True, "result": "ok"})
        with patch.dict(FusionMCP.HANDLER_REGISTRY, {"test_cmd": mock_handler}):
            commands = [{"name": "test_cmd", "params": {"a": 1}}, {"name": "test_cmd", "params": {"b": 2}}]
            result = FusionMCP.handle_batch(self.design, self.rootComp, {"commands": commands})
            assert result["success"] is True
            assert result["executed"] == 2
            assert len(result["results"]) == 2

    def test_batch_stops_on_first_failure(self):
        """handle_batch stops on first failed command and returns partial results."""
        call_count = 0

        def mock_handler(design, root, params):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return {"success": False, "error": "second failed"}
            return {"success": True}

        with patch.dict(FusionMCP.HANDLER_REGISTRY, {"test_cmd": mock_handler}):
            commands = [
                {"name": "test_cmd", "params": {}},
                {"name": "test_cmd", "params": {}},
                {"name": "test_cmd", "params": {}},
            ]
            result = FusionMCP.handle_batch(self.design, self.rootComp, {"commands": commands})
            assert result["success"] is False
            assert "step 1" in result["error"]
            assert len(result["partial_results"]) == 2


class TestHandlerRegistry:
    def test_all_registry_values_are_callable(self):
        """Every entry in HANDLER_REGISTRY must be a callable function."""
        for name, handler in FusionMCP.HANDLER_REGISTRY.items():
            assert callable(handler), f"HANDLER_REGISTRY['{name}'] is not callable"

    def test_registry_has_expected_tool_count(self):
        """Registry should have at least 39 tools (9 original + 30 new)."""
        assert len(FusionMCP.HANDLER_REGISTRY) >= 39
