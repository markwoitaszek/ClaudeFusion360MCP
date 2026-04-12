"""Tests for IPC layer (mcp-server/ipc.py)."""

import json
import os
from unittest.mock import patch

import ipc
import pytest


class TestInitializeIpc:
    def test_creates_comm_dir(self, mock_comm_dir):
        with patch.object(ipc, "COMM_DIR", mock_comm_dir):
            # Remove the dir so initialize_ipc creates it
            os.rmdir(mock_comm_dir)
            ipc.initialize_ipc()
            assert mock_comm_dir.exists()
            assert oct(mock_comm_dir.stat().st_mode)[-3:] == "700"

    def test_generates_session_token(self, mock_comm_dir):
        with patch.object(ipc, "COMM_DIR", mock_comm_dir):
            ipc.initialize_ipc()
            token_path = mock_comm_dir / "session_token"
            assert token_path.exists()
            token = token_path.read_text()
            assert len(token) == 32  # secrets.token_hex(16) = 32 hex chars

    def test_token_file_permissions(self, mock_comm_dir):
        with patch.object(ipc, "COMM_DIR", mock_comm_dir):
            ipc.initialize_ipc()
            token_path = mock_comm_dir / "session_token"
            assert oct(token_path.stat().st_mode)[-3:] == "600"


class TestSendFusionCommand:
    def test_writes_command_file(self, mock_comm_dir):
        with patch.object(ipc, "COMM_DIR", mock_comm_dir), patch.object(ipc, "_session_token", "test_token"):
            # Write a pre-canned response so send_fusion_command finds it
            def write_response(*args, **kwargs):
                # Find the command file and write a matching response
                cmd_files = list(mock_comm_dir.glob("command_*.json"))
                if cmd_files:
                    with open(cmd_files[0]) as f:
                        cmd = json.load(f)
                    resp_file = mock_comm_dir / f"response_{cmd['id']}.json"
                    with open(resp_file, "w") as f:
                        json.dump({"success": True, "result": "ok"}, f)
                return 0.0  # Return 0 for time.sleep mock

            with patch("ipc.time.sleep", side_effect=write_response):
                result = ipc.send_fusion_command("test_tool", {"key": "value"})
                assert result["success"] is True

    def test_command_includes_session_token(self, mock_comm_dir):
        with patch.object(ipc, "COMM_DIR", mock_comm_dir), patch.object(ipc, "_session_token", "my_token"):
            # Just check the command file content before it gets consumed
            def check_and_respond(*args, **kwargs):
                cmd_files = list(mock_comm_dir.glob("command_*.json"))
                if cmd_files:
                    with open(cmd_files[0]) as f:
                        cmd = json.load(f)
                    assert cmd["session_token"] == "my_token"
                    assert cmd["name"] == "test_tool"
                    resp_file = mock_comm_dir / f"response_{cmd['id']}.json"
                    with open(resp_file, "w") as f:
                        json.dump({"success": True}, f)
                return 0.0

            with patch("ipc.time.sleep", side_effect=check_and_respond):
                ipc.send_fusion_command("test_tool", {})

    def test_timeout_raises_exception(self, mock_comm_dir):
        with patch.object(ipc, "COMM_DIR", mock_comm_dir), patch.object(ipc, "_session_token", None):
            with patch("ipc.time.sleep", return_value=None):
                with pytest.raises(Exception, match="Timeout after 45s"):
                    ipc.send_fusion_command("slow_tool", {})

    def test_error_response_raises_exception(self, mock_comm_dir):
        with patch.object(ipc, "COMM_DIR", mock_comm_dir), patch.object(ipc, "_session_token", None):

            def respond_with_error(*args, **kwargs):
                cmd_files = list(mock_comm_dir.glob("command_*.json"))
                if cmd_files:
                    with open(cmd_files[0]) as f:
                        cmd = json.load(f)
                    resp_file = mock_comm_dir / f"response_{cmd['id']}.json"
                    with open(resp_file, "w") as f:
                        json.dump({"success": False, "error": "Something went wrong"}, f)
                return 0.0

            with patch("ipc.time.sleep", side_effect=respond_with_error):
                with pytest.raises(Exception, match="Something went wrong"):
                    ipc.send_fusion_command("failing_tool", {})
