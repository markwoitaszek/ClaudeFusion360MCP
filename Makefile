# Fusion 360 MCP Server — Developer Makefile
#
# Standard targets for development, testing, and validation.
# Requires: Python 3.10+, pip install -e '.[dev]'

.PHONY: run test lint validate-skills generate-registry check-version clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

run: ## Run the MCP server (LOG_LEVEL=DEBUG)
	LOG_LEVEL=DEBUG python mcp-server/fusion360_mcp_server.py

test: ## Run tests with coverage (threshold: 70%)
	python -m pytest tests/ -v --cov=mcp-server --cov-fail-under=70

lint: ## Lint with ruff + black format check
	ruff check mcp-server/ tests/ scripts/
	black --check mcp-server/ tests/ scripts/

validate-skills: ## Validate skill file frontmatter
	python scripts/validate_skills.py docs/

generate-registry: ## Generate mcp.json from tool introspection
	python scripts/generate_mcp_registry.py

check-version: ## Check version consistency across all components
	python scripts/check_version_sync.py

clean: ## Remove build artifacts, caches, and stale IPC files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	rm -f ~/fusion_mcp_comm/command_*.json ~/fusion_mcp_comm/response_*.json 2>/dev/null || true
