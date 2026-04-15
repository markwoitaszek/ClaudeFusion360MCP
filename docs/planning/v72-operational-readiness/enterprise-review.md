---
title: "v7.2 Operational Readiness — Enterprise Readiness Review"
document_type: enterprise_review
created: "2026-04-14"
related:
  - discovery: "./v72-operational-readiness-2026-04-14.md"
  - optimized_requirements: "./optimized-requirements.md"
  - architecture_constraints: "./architecture-constraints.md"
  - decision_rationale: "./decision-rationale.md"
---

# Enterprise Readiness Review

## Overall Readiness: Needs Work

4 gaps and 8 risks identified across scalability, security, and deployment dimensions. All addressable within the proposed v7.2 scope.

## Review Dimensions

### Scalability/Reusability

**Ready:**
- FastMCP include_router pattern cleanly accommodates new routers
- Script convention (argparse + main()->int) is consistent and extensible
- Validation helpers in validation.py are reusable across IPC and offline tools

**Gaps:**
- Module-level session token globals create multi-process collision risk
- COMM_DIR is hardcoded with no env var override for multi-instance scenarios
- SAFE_EXPORT_DIRS is not configurable via environment

**Recommendations:**
- Document single-process constraint in ipc.py docstring
- Add `FUSION_COMM_DIR` env var override for advanced deployments
- Add `FUSION_SAFE_DIRS` env var override for non-standard deployments

### Security

**Ready:**
- Session token authentication (secrets.token_hex + hmac.compare_digest)
- 0o700 directory permissions on COMM_DIR
- Atomic file writes preventing partial-read races
- Path traversal protection via validate_filepath

**Gaps:**
- `get_session_stats` could inadvertently expose session token via module reflection
- JSON telemetry structurally promotes all log fields to extractable key-value pairs
- Offline tools (planning.py) bypass the IPC validation boundary
- Token re-read on mismatch in add-in creates a narrow TOCTOU window

**Recommendations:**
- Explicitly spec `get_session_stats` return schema — whitelist fields, do not reflect module state
- Add `logging.Filter` blocking records containing `session_token` keyword
- Offline tools must import and call same validators from validation.py
- Reload token on interval (30s in monitor loop), not opportunistically on mismatch

### Deployment/Testing

**Ready:**
- 14 test files, 157 pass, CI active with ruff+black+pytest
- install.py handles macOS/Windows with --dry-run mode
- @integration marker and FUSION_SMOKE_TESTS gate for live tests

**Gaps:**
- CI installs unpinned deps separately from pyproject.toml extras
- Integration tests call send_fusion_command directly, bypassing tool validation
- install.py has no venv detection or rollback mechanism
- Coverage threshold at 50% will not catch regressions from new code

**Recommendations:**
- Use `pip install -e '.[dev]'` in all CI jobs
- Golden path tests must call tool functions, not send_fusion_command
- Warn (not block) when no venv detected in install.py
- Raise coverage threshold to 70% after adding new modules with tests

## Gap Summary

| Gap | Dimension | Severity | Status |
|-----|-----------|----------|--------|
| get_session_stats token exposure | Security | P0 | Addressed in REQ-P1-2 spec |
| Offline tools bypass validation | Security | P1 | Addressed in REQ-P2-1 constraint |
| CI unpinned deps | Deployment | P1 | Addressed in REQ-P1-4 |
| Integration tests bypass validation | Testing | P1 | Addressed in REQ-P2-3 constraint |

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation | Residual Risk |
|------|-----------|--------|------------|---------------|
| Session token collision (multi-process) | Medium | High | Document constraint + lock file | Low |
| Offline tools unvalidated input | Medium | High | Import validators; offline_safe checklist | Low |
| JSON telemetry leaks token | Medium | Medium | Log-scrubbing filter | Very Low |
| SKILL.md version drift | High | Medium | check_version_sync.py extension | Very Low |
| Guided design over-questions experts | Medium | Medium | Brief-mode override | Low |
| install.py system Python pollution | Medium | Medium | Venv warning + docs | Low |
| CI dep version drift | Medium | Low | Use pyproject.toml extras in CI | Very Low |
| Coverage regressions from new code | Medium | Low | Raise threshold to 70% | Very Low |
