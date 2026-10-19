.DEFAULT_GOAL := help

# Ansible
ANSIBLE_BUILD_DIR ?= $(CURDIR)/dist
ANSIBLE_COLLECTIONS_PATH ?= $(CURDIR)/.ansible/collections
ANSIBLE_GALAXY ?= uvx --from ansible-core ansible-galaxy
ANSIBLE_INVENTORY ?= inventory.ini
ANSIBLE_LINT ?= uvx --from ansible-lint ansible-lint
ANSIBLE_PLAYBOOK ?= uvx --from ansible-core ansible-playbook
ANSIBLE_ROLE_DIR ?= roles/ubuntu2604

# Testinfra
TESTINFRA_HOSTS ?= ansible://all?controlpersist=300&timeout=30
TESTINFRA_PYTEST ?= uvx --from pytest --with pytest-testinfra --with pytest-xdist --with ansible-core pytest
TESTINFRA_WORKERS ?= 8

.PHONY: help
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: check
check: lint syntax ## Run all checks

.PHONY: deps
deps: ## Install the local collection and its dependencies
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_GALAXY) collection install . --force -p $(ANSIBLE_COLLECTIONS_PATH)

.PHONY: build
build: ## Build the collection artifact
	$(ANSIBLE_GALAXY) collection build --force --output-path $(ANSIBLE_BUILD_DIR)

.PHONY: lint
lint: deps ## Run ansible-lint against the collection
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_LINT) .

.PHONY: syntax
syntax: deps ## Check the installed collection playbooks syntax
	ANSIBLE_COLLECTIONS_PATH=$(ANSIBLE_COLLECTIONS_PATH) $(ANSIBLE_PLAYBOOK) --syntax-check andreygubarev.com.ubuntu2604 andreygubarev.com.kubernetes

.PHONY: test
test: ## Run testinfra verification tests against inventory.ini
	ANSIBLE_HOST_KEY_CHECKING=False $(TESTINFRA_PYTEST) -n $(TESTINFRA_WORKERS) --dist=worksteal --hosts='$(TESTINFRA_HOSTS)' --ansible-inventory=$(ANSIBLE_INVENTORY) --sudo $(ANSIBLE_ROLE_DIR)/tests
