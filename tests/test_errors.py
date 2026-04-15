"""Tests for the typed exception hierarchy (mcp-server/errors.py)."""

import pytest
from errors import FusionError, FusionIPCError, FusionTimeoutError


class TestFusionError:
    def test_base_error_code(self):
        err = FusionError("test message")
        assert err.error_code == "F360_ERROR"

    def test_tool_name_and_remediation(self):
        err = FusionError("msg", tool_name="ping", remediation="try again")
        assert err.tool_name == "ping"
        assert err.remediation == "try again"

    def test_to_safe_dict_strips_cause(self):
        try:
            try:
                raise ValueError("internal detail")
            except ValueError:
                raise FusionError("user-visible", tool_name="export_stl", remediation="check path") from None
        except FusionError as e:
            sanitized = e.to_safe_dict()
            assert sanitized["error_code"] == "F360_ERROR"
            assert sanitized["error"] == "user-visible"
            assert sanitized["tool_name"] == "export_stl"
            assert sanitized["remediation"] == "check path"
            assert "__cause__" not in sanitized

    def test_to_safe_dict_output_keys(self):
        err = FusionError("msg")
        sanitized = err.to_safe_dict()
        assert set(sanitized.keys()) == {"error_code", "error", "tool_name", "remediation"}


class TestFusionTimeoutError:
    def test_error_code(self):
        err = FusionTimeoutError("timed out", tool_name="extrude")
        assert err.error_code == "F360_TIMEOUT"
        assert isinstance(err, FusionError)

    def test_is_catchable_as_base(self):
        with pytest.raises(FusionError):
            raise FusionTimeoutError("timeout")


class TestFusionIPCError:
    def test_error_code(self):
        err = FusionIPCError("comm dir missing", tool_name="ping", remediation="restart")
        assert err.error_code == "F360_IPC_ERROR"
        assert isinstance(err, FusionError)
        assert err.tool_name == "ping"
