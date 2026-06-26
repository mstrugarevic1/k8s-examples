TEAM ?= payments-staging
TEAM_FILE ?= teams/$(TEAM).yaml
OUT ?= generated

.PHONY: install generate test validate clean

install:
	python3 -m pip install -r requirements.txt

generate:
	python3 scripts/generate.py $(TEAM_FILE) --out $(OUT)

test:
	python3 -m pytest -q

validate: generate
	@if ! command -v kubectl >/dev/null 2>&1; then \
		echo "kubectl is not installed; skipping client-side manifest validation."; \
	elif ! kubectl config current-context >/dev/null 2>&1; then \
		echo "kubectl has no current context; skipping client-side manifest validation."; \
	else \
		kubectl apply --dry-run=client --validate=false -f $(OUT)/$(TEAM); \
	fi

clean:
	rm -rf $(OUT)
