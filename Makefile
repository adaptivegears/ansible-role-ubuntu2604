.DEFAULT_GOAL := help

# Ansible
ANSIBLE_COLLECTIONS_PATH ?= $(CURDIR)/.ansible/collections
ANSIBLE_GALAXY ?= uvx --from ansible-core ansible-galaxy
ANSIBLE_INVENTORY ?= inventory.ini
ANSIBLE_LINT ?= uvx --from ansible-lint ansible-lint
ANSIBLE_ROLE_DIR ?= ubuntu_2604

# Testinfra
TESTINFRA_HOSTS ?= ansible://all?controlpersist=300&timeout=30
TESTINFRA_PYTEST ?= uvx --from pytest --with pytest-testinfra --with pytest-xdist --with ansible-core pytest
TESTINFRA_WORKERS ?= 2

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: check
check: lint ## Run all checks

.PHONY: deps
deps: ## Install Ansible collection dependencies
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_GALAXY) collection install -r requirements.yml -p $(ANSIBLE_COLLECTIONS_PATH)

.PHONY: lint
lint: deps ## Run ansible-lint against the role
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_LINT) $(ANSIBLE_ROLE_DIR)

.PHONY: test
test: ## Run testinfra verification tests against inventory.ini
	ANSIBLE_HOST_KEY_CHECKING=False $(TESTINFRA_PYTEST) -n $(TESTINFRA_WORKERS) --dist=worksteal --hosts='$(TESTINFRA_HOSTS)' --ansible-inventory=$(ANSIBLE_INVENTORY) $(ANSIBLE_ROLE_DIR)/tests
