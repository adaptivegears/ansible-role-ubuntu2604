.DEFAULT_GOAL := help

ROLE_DIR ?= ubuntu_2604
ANSIBLE_COLLECTIONS_PATH ?= $(CURDIR)/.ansible/collections
ANSIBLE_GALAXY ?= uvx --from ansible-core ansible-galaxy
ANSIBLE_LINT ?= uvx --from ansible-lint ansible-lint
PYTEST ?= uvx --from pytest --with pytest-testinfra --with pytest-xdist --with ansible-core pytest
PYTEST_WORKERS ?= 8
TEST_HOSTS ?= ansible://all?controlpersist=300&timeout=30
TEST_INVENTORY ?= inventory.ini

.PHONY: help check deps lint test

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check: lint ## Run all checks

deps: ## Install Ansible collection dependencies
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_GALAXY) collection install -r requirements.yml -p $(ANSIBLE_COLLECTIONS_PATH)

lint: deps ## Run ansible-lint against the role
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_LINT) $(ROLE_DIR)

test: ## Run testinfra verification tests against inventory.ini
	ANSIBLE_HOST_KEY_CHECKING=False $(PYTEST) -n $(PYTEST_WORKERS) --dist=worksteal --hosts='$(TEST_HOSTS)' --ansible-inventory=$(TEST_INVENTORY) $(ROLE_DIR)/tests
