SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

PROFILE ?= kind
NAMESPACE ?= observability
ENVIRONMENT ?= $(PROFILE)
STORAGE_CLASS ?=
ifeq ($(PROFILE),production)
VM_STORAGE_SIZE ?= 100Gi
VM_RETENTION ?= 15d
LOKI_STORAGE_SIZE ?= 50Gi
LOKI_RETENTION ?= 15d
GRAFANA_STORAGE_SIZE ?= 10Gi
ALERTMANAGER_STORAGE_SIZE ?= 10Gi
else
VM_STORAGE_SIZE ?= 8Gi
VM_RETENTION ?= 24h
LOKI_STORAGE_SIZE ?= 10Gi
LOKI_RETENTION ?= 24h
GRAFANA_STORAGE_SIZE ?= 2Gi
ALERTMANAGER_STORAGE_SIZE ?= 2Gi
endif
CONFIRM_PRODUCTION ?= no

export PROFILE NAMESPACE ENVIRONMENT STORAGE_CLASS VM_STORAGE_SIZE VM_RETENTION
export LOKI_STORAGE_SIZE LOKI_RETENTION GRAFANA_STORAGE_SIZE ALERTMANAGER_STORAGE_SIZE CONFIRM_PRODUCTION

HELMFILE := helmfile -e $(PROFILE) -f helmfile.yaml.gotmpl

.PHONY: help doctor template install upgrade status credentials grafana metrics validate demo-up demo-failures demo-reset demo-down test uninstall purge

help:
	@awk 'BEGIN {FS = ":.*##"; print "Targets:"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

doctor: ## Check tools, context, storage, and profile inputs.
	@scripts/doctor.sh

template: ## Render the selected profile.
	@eval "$$(scripts/resolve-config.sh)"; $(HELMFILE) template

install: doctor ## Install the selected profile.
	@eval "$$(scripts/resolve-config.sh)"; scripts/confirm-write.sh; $(HELMFILE) sync; scripts/install-dashboards.sh; scripts/install-rules.sh; scripts/wait-ready.sh

upgrade: install ## Upgrade the selected profile.

status: ## Show installed resources.
	@eval "$$(scripts/resolve-config.sh)"; kubectl -n "$$NAMESPACE" get pods,svc,pvc,vmrules

credentials: ## Print safe Grafana credential commands.
	@eval "$$(scripts/resolve-config.sh)"; echo "user: admin"; echo "password command:"; echo "kubectl -n $$NAMESPACE get secret victoria-metrics-k8s-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo"

grafana: ## Port-forward Grafana to http://localhost:3000.
	@scripts/port-forward.sh grafana

metrics: ## Port-forward VictoriaMetrics to http://localhost:8428.
	@scripts/port-forward.sh metrics

validate: ## Run static validation.
	@scripts/validate-static.sh

demo-up: ## Install the healthy demo workload.
	@kubectl apply -f demos/base/namespace.yaml
	@kubectl apply -f demos/base
	@kubectl -n golden-path-demo rollout status deploy/golden-path-api --timeout=3m
	@kubectl -n golden-path-demo rollout status deploy/golden-path-traffic --timeout=3m

demo-failures: ## Install controlled failure fixtures.
	@kubectl apply -f demos/failures

demo-reset: ## Remove controlled failure fixtures.
	@kubectl delete -f demos/failures --ignore-not-found

demo-down: demo-reset ## Remove all demo resources.
	@kubectl delete -f demos/base --ignore-not-found

test: ## Run live validation against an installed stack.
	@scripts/validate-live.py --demo

uninstall: ## Remove Helm releases and Git-provisioned rules/dashboards, keeping PVCs.
	@eval "$$(scripts/resolve-config.sh)"; scripts/confirm-write.sh; kubectl -n "$$NAMESPACE" delete vmrule -l app.kubernetes.io/part-of=observability-golden-path --ignore-not-found; kubectl -n "$$NAMESPACE" delete configmap -l app.kubernetes.io/part-of=observability-golden-path --ignore-not-found; $(HELMFILE) destroy

purge: ## Delete releases and PVC data. Destructive.
	@eval "$$(scripts/resolve-config.sh)"; scripts/confirm-write.sh; echo "PURGE deletes PVC data in namespace $$NAMESPACE"; test "$${CONFIRM_PURGE:-no}" = yes || { echo "Set CONFIRM_PURGE=yes to continue"; exit 1; }; $(HELMFILE) destroy; kubectl -n "$$NAMESPACE" delete pvc --all --ignore-not-found
