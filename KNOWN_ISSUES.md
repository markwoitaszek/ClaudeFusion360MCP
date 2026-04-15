# Known Issues

Documented issues and limitations in the current release.

## Session Token Race Condition

**Severity**: Low (single-user desktop app)
**Status**: Accepted

When the Fusion 360 add-in detects a session token mismatch, it re-reads the token file from disk. This creates a narrow TOCTOU (Time-Of-Check-Time-Of-Use) window where:

1. MCP server writes new token to `session_token.tmp`
2. Add-in reads the old token from `session_token`
3. MCP server renames `session_token.tmp` to `session_token`
4. Add-in rejects the command due to mismatch, then re-reads

**Impact**: A single command retry resolves the issue. In practice, this window is microseconds wide and rarely triggered.

**Mitigation**: The MCP server uses atomic file writes (`os.replace()`) to minimize the window. The add-in's re-read behavior provides automatic recovery.

## Multi-Process Session Token Collision

**Severity**: Medium (advanced deployments only)
**Status**: Documented constraint

Module-level globals (`_session_token`, `_command_counter`, `_stats`) in `ipc.py` assume a single MCP server process. Running multiple MCP server instances targeting the same `COMM_DIR` will cause:

- Session token overwrites between processes
- Command ID counter collisions (mitigated by random suffix)
- Stats counter inaccuracy

**Mitigation**: Document single-process constraint. For multi-instance scenarios, use separate `COMM_DIR` paths (future: `FUSION_COMM_DIR` environment variable override).

## Image References in README

Some image references in README.md (e.g., `images/hero-demo.gif`) may not resolve if the images directory is not present. This does not affect functionality.
