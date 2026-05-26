.DEFAULT_GOAL := help

ROLE_DIR ?= ubuntu_2604
ANSIBLE_COLLECTIONS_PATH ?= $(CURDIR)/.ansible/collections
ANSIBLE_GALAXY ?= uvx --from ansible-core ansible-galaxy
ANSIBLE_LINT ?= uvx --from ansible-lint ansible-lint
ANSIBLE_PLAYBOOK ?= uvx --from ansible-core ansible-playbook

.PHONY: help check deps lint test

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check: lint ## Run all checks

deps: ## Install Ansible collection dependencies
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_GALAXY) collection install -r requirements.yml -p $(ANSIBLE_COLLECTIONS_PATH)

lint: deps ## Run ansible-lint against the role
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_LINT) $(ROLE_DIR)

test: ## Run verification test playbook against inventory.ini
	ANSIBLE_HOST_KEY_CHECKING=False $(ANSIBLE_PLAYBOOK) -i inventory.ini $(ROLE_DIR)/tests/test.yml
