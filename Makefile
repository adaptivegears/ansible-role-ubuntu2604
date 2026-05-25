.DEFAULT_GOAL := help

ROLE_DIR ?= ubuntu_2604
ANSIBLE_LINT ?= uvx --from ansible-lint ansible-lint

.PHONY: help check lint

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check: lint ## Run all checks

lint: ## Run ansible-lint against the role
	$(ANSIBLE_LINT) $(ROLE_DIR)
