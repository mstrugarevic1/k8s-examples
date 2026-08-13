TEAM ?= payments-staging
TEAM_FILE ?= teams/$(TEAM).yaml
OUT ?= generated
PYTHON ?= .venv/bin/python

.PHONY: install generate generate-all test validate check clean

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

generate:
	$(PYTHON) scripts/generate.py $(TEAM_FILE) --out $(OUT)

generate-all:
	@set -e; for config in $(sort $(wildcard teams/*.yaml)); do \
		$(PYTHON) scripts/generate.py "$$config" --out "$(OUT)"; \
	done

test:
	$(PYTHON) -m pytest -q

validate:
	kubeconform -strict -summary "$(OUT)"

check:
	$(MAKE) test
	@set -e; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
		$(MAKE) generate-all OUT="$$tmp"; \
		$(MAKE) validate OUT="$$tmp"; \
		diff -ru "$(OUT)" "$$tmp"

clean:
	rm -rf $(OUT)
