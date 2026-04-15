"""Tests for fusion-addin/FusionMCP.py pure-Python logic.

Tests execute_command (registry dispatch), handle_batch (batch validation),
monitor_commands token logic, protocol version validation, stale file cleanup,
ping health check, and command file TTL without requiring Fusion 360.
"""

import json
import os
import sys
import time
import types
from pathlib import Path
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

    def test_all_handlers_have_three_param_signature(self):
        """Every handler in HANDLER_REGISTRY must accept exactly 3 positional params (design, rootComp, params)."""
        import inspect
        for name, handler in FusionMCP.HANDLER_REGISTRY.items():
            sig = inspect.signature(handler)
            # Count parameters that are positional (no default) or have defaults
            params = [p for p in sig.parameters.values() if p.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )]
            assert len(params) == 3, (
                f"HANDLER_REGISTRY['{name}'] has {len(params)} params, expected 3 (design, rootComp, params)"
            )


class TestHandlePing:
    """Tests for the NR-6 ping health check handler."""

    def test_ping_returns_success_without_active_design(self):
        """handle_ping works without an active design (its key differentiator)."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.version = "2.0.20440"
        result = FusionMCP.handle_ping(None, None, {})
        assert result["success"] is True
        assert result["status"] == "ok"
        assert result["addin_version"] == FusionMCP.ADDIN_VERSION
        assert result["protocol_version"] == FusionMCP.PROTOCOL_VERSION
        assert result["fusion_version"] == "2.0.20440"

    def test_ping_via_execute_command_without_design(self):
        """Ping through execute_command succeeds even with no active design."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.activeProduct = None
        FusionMCP.app.version = "2.0.20440"
        result = FusionMCP.execute_command({"name": "ping", "params": {}})
        assert result["success"] is True
        assert result["status"] == "ok"

    def test_ping_via_batch(self):
        """Ping through batch handler works (regression test for signature mismatch)."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.version = "2.0.20440"
        design = MagicMock()
        rootComp = MagicMock()
        result = FusionMCP.handle_batch(design, rootComp, {"commands": [{"name": "ping", "params": {}}]})
        assert result["success"] is True
        assert result["executed"] == 1
        assert result["results"][0]["status"] == "ok"

    def test_ping_handles_version_error(self):
        """handle_ping returns 'unknown' if app.version raises."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.version = property(lambda self: (_ for _ in ()).throw(RuntimeError("no version")))
        type(FusionMCP.app).version = property(lambda self: (_ for _ in ()).throw(RuntimeError))
        result = FusionMCP.handle_ping(None, None, {})
        assert result["success"] is True
        assert result["fusion_version"] == "unknown"


class TestCleanupStaleFiles:
    """Tests for the NR-2 stale file cleanup function."""

    def test_removes_stale_command_and_response_files(self, tmp_path):
        """_cleanup_stale_files removes command and response files from COMM_DIR."""
        with patch.object(FusionMCP, "COMM_DIR", tmp_path):
            # Create stale files
            (tmp_path / "command_old1.json").write_text("{}")
            (tmp_path / "response_old1.json").write_text("{}")
            (tmp_path / "command_old2.tmp").write_text("{}")
            (tmp_path / "response_old2.tmp").write_text("{}")
            # Create a non-matching file that should NOT be removed
            (tmp_path / "other_file.txt").write_text("keep me")

            FusionMCP._cleanup_stale_files()

            assert not (tmp_path / "command_old1.json").exists()
            assert not (tmp_path / "response_old1.json").exists()
            assert not (tmp_path / "command_old2.tmp").exists()
            assert not (tmp_path / "response_old2.tmp").exists()
            assert (tmp_path / "other_file.txt").exists()

    def test_handles_unlink_errors_gracefully(self, tmp_path):
        """_cleanup_stale_files continues if individual unlink fails."""
        with patch.object(FusionMCP, "COMM_DIR", tmp_path):
            f = tmp_path / "command_err.json"
            f.write_text("{}")
            with patch.object(Path, "unlink", side_effect=PermissionError("denied")):
                # Should not raise
                FusionMCP._cleanup_stale_files()

    def test_empty_directory(self, tmp_path):
        """_cleanup_stale_files handles empty COMM_DIR gracefully."""
        with patch.object(FusionMCP, "COMM_DIR", tmp_path):
            FusionMCP._cleanup_stale_files()  # Should not raise


class TestProtocolVersionValidation:
    """Tests for NR-1 protocol version validation in monitor_commands."""

    def test_matching_version_accepted(self, tmp_path):
        """Commands with matching protocol_version are dispatched."""
        with patch.object(FusionMCP, "COMM_DIR", tmp_path):
            cmd_id = "test_match_123"
            cmd = {
                "type": "tool",
                "name": "ping",
                "params": {},
                "id": cmd_id,
                "protocol_version": FusionMCP.PROTOCOL_VERSION,
                "session_token": "tok123",
            }
            cmd_file = tmp_path / f"command_{cmd_id}.json"
            cmd_file.write_text(json.dumps(cmd))

            FusionMCP._session_token = "tok123"
            FusionMCP.app = MagicMock()
            FusionMCP._stop_event.clear()

            # Run one iteration of monitor_commands then stop
            with patch.object(FusionMCP._stop_event, "is_set", side_effect=[False, True]):
                with patch.object(FusionMCP._stop_event, "wait"):
                    with patch.object(FusionMCP.app, "fireCustomEvent") as mock_fire:
                        FusionMCP.monitor_commands()
                        mock_fire.assert_called_once_with(FusionMCP.CUSTOM_EVENT_ID, cmd_id)

    def test_mismatched_version_rejected(self, tmp_path):
        """Commands with wrong protocol_version are rejected with error response."""
        with patch.object(FusionMCP, "COMM_DIR", tmp_path):
            cmd_id = "test_mismatch_456"
            cmd = {
                "type": "tool",
                "name": "get_design_info",
                "params": {},
                "id": cmd_id,
                "protocol_version": 999,  # Wrong version
                "session_token": "tok123",
            }
            cmd_file = tmp_path / f"command_{cmd_id}.json"
            cmd_file.write_text(json.dumps(cmd))

            FusionMCP._session_token = "tok123"
            FusionMCP.app = MagicMock()
            FusionMCP._stop_event.clear()

            with patch.object(FusionMCP._stop_event, "is_set", side_effect=[False, True]):
                with patch.object(FusionMCP._stop_event, "wait"):
                    with patch.object(FusionMCP.app, "fireCustomEvent") as mock_fire:
                        FusionMCP.monitor_commands()
                        # Should NOT have been dispatched
                        mock_fire.assert_not_called()

            # Error response should have been written
            resp_file = tmp_path / f"response_{cmd_id}.json"
            assert resp_file.exists()
            resp = json.loads(resp_file.read_text())
            assert resp["success"] is False
            assert "Protocol version mismatch" in resp["error"]

    def test_missing_version_rejected(self, tmp_path):
        """Commands without protocol_version field are rejected."""
        with patch.object(FusionMCP, "COMM_DIR", tmp_path):
            cmd_id = "test_missing_789"
            cmd = {
                "type": "tool",
                "name": "get_design_info",
                "params": {},
                "id": cmd_id,
                # No protocol_version field
                "session_token": "tok123",
            }
            cmd_file = tmp_path / f"command_{cmd_id}.json"
            cmd_file.write_text(json.dumps(cmd))

            FusionMCP._session_token = "tok123"
            FusionMCP.app = MagicMock()
            FusionMCP._stop_event.clear()

            with patch.object(FusionMCP._stop_event, "is_set", side_effect=[False, True]):
                with patch.object(FusionMCP._stop_event, "wait"):
                    with patch.object(FusionMCP.app, "fireCustomEvent") as mock_fire:
                        FusionMCP.monitor_commands()
                        mock_fire.assert_not_called()

            resp_file = tmp_path / f"response_{cmd_id}.json"
            assert resp_file.exists()
            resp = json.loads(resp_file.read_text())
            assert resp["success"] is False
            assert "Protocol version mismatch" in resp["error"]


class TestCommandFileTTL:
    """Tests for NR-8 command file TTL (skip/delete files older than threshold)."""

    def test_fresh_file_processed(self, tmp_path):
        """Files younger than CMD_FILE_TTL_SECONDS are processed normally."""
        with patch.object(FusionMCP, "COMM_DIR", tmp_path):
            cmd_id = "test_fresh_001"
            cmd = {
                "type": "tool", "name": "ping", "params": {},
                "id": cmd_id, "protocol_version": FusionMCP.PROTOCOL_VERSION,
                "session_token": "tok123",
            }
            cmd_file = tmp_path / f"command_{cmd_id}.json"
            cmd_file.write_text(json.dumps(cmd))
            # File was just created — mtime is now

            FusionMCP._session_token = "tok123"
            FusionMCP.app = MagicMock()
            FusionMCP._stop_event.clear()

            with patch.object(FusionMCP._stop_event, "is_set", side_effect=[False, True]):
                with patch.object(FusionMCP._stop_event, "wait"):
                    with patch.object(FusionMCP.app, "fireCustomEvent") as mock_fire:
                        FusionMCP.monitor_commands()
                        mock_fire.assert_called_once()

    def test_stale_file_skipped_and_deleted(self, tmp_path):
        """Files older than CMD_FILE_TTL_SECONDS are skipped and deleted."""
        with patch.object(FusionMCP, "COMM_DIR", tmp_path):
            cmd_id = "test_stale_002"
            cmd = {
                "type": "tool", "name": "ping", "params": {},
                "id": cmd_id, "protocol_version": FusionMCP.PROTOCOL_VERSION,
                "session_token": "tok123",
            }
            cmd_file = tmp_path / f"command_{cmd_id}.json"
            cmd_file.write_text(json.dumps(cmd))
            # Backdate the file to be older than the TTL
            old_time = time.time() - FusionMCP.CMD_FILE_TTL_SECONDS - 10
            os.utime(cmd_file, (old_time, old_time))

            FusionMCP._session_token = "tok123"
            FusionMCP.app = MagicMock()
            FusionMCP._stop_event.clear()

            with patch.object(FusionMCP._stop_event, "is_set", side_effect=[False, True]):
                with patch.object(FusionMCP._stop_event, "wait"):
                    with patch.object(FusionMCP.app, "fireCustomEvent") as mock_fire:
                        FusionMCP.monitor_commands()
                        # Stale file should NOT have been dispatched
                        mock_fire.assert_not_called()

            # Stale file should have been deleted
            assert not cmd_file.exists()


class TestVersionComparison:
    """Tests for NR-9 version comparison logic."""

    def test_older_version_logs_warning(self):
        """Versions older than baseline trigger a warning."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.version = "2.0.10000"
        with patch.object(FusionMCP.logger, "warning") as mock_warn:
            FusionMCP._log_fusion_version()
            assert any("older than" in str(call) for call in mock_warn.call_args_list)

    def test_newer_version_no_warning(self):
        """Versions newer than baseline do not trigger a warning."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.version = "2.0.99999"
        with patch.object(FusionMCP.logger, "warning") as mock_warn:
            FusionMCP._log_fusion_version()
            # No warning should be logged (only info)
            assert not any("older than" in str(call) for call in mock_warn.call_args_list)

    def test_numeric_comparison_not_lexicographic(self):
        """Version '2.0.9999' is correctly identified as older than '2.0.20440'."""
        FusionMCP.app = MagicMock()
        FusionMCP.app.version = "2.0.9999"  # Lexicographically > but numerically <
        with patch.object(FusionMCP.logger, "warning") as mock_warn:
            FusionMCP._log_fusion_version()
            assert any("older than" in str(call) for call in mock_warn.call_args_list)
