SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

include versions.env

CONTROLLER_CHART := oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
RUNNER_CHART := oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
CONTROLLER_NAMESPACE ?= arc-systems
RUNNER_NAMESPACE ?= arc-runners-demo
OBSERVABILITY_NAMESPACE ?= observability
RUNNER_SCALE_SET_NAME ?= miroslav-kind-runners
GITHUB_CONFIG_URL ?= https://github.com/OWNER/REPOSITORY

export ARC_VERSION CONTROLLER_CHART RUNNER_CHART CONTROLLER_NAMESPACE RUNNER_NAMESPACE
export OBSERVABILITY_NAMESPACE RUNNER_SCALE_SET_NAME GITHUB_CONFIG_URL

.PHONY: kind-up kind-down create-secret install-controller install-runners install-observability install validate template verify cleanup argocd-apply

kind-up:
	kind create cluster --config kind/cluster.yaml

kind-down:
	kind delete cluster --name arc-runners

create-secret:
	ARC_RUNNER_NAMESPACE="$(RUNNER_NAMESPACE)" examples/create-github-app-secret.sh

install-controller:
	helm upgrade --install arc-controller "$(CONTROLLER_CHART)" --version "$(ARC_VERSION)" --namespace "$(CONTROLLER_NAMESPACE)" --create-namespace --wait -f values/controller.yaml

install-runners:
	@test "$(GITHUB_CONFIG_URL)" != "https://github.com/OWNER/REPOSITORY" || { echo "set GITHUB_CONFIG_URL=https://github.com/<owner>/<repository>"; exit 1; }
	kubectl -n "$(RUNNER_NAMESPACE)" get secret github-app-credentials >/dev/null
	helm upgrade --install arc-demo "$(RUNNER_CHART)" --version "$(ARC_VERSION)" --namespace "$(RUNNER_NAMESPACE)" --create-namespace --wait -f values/demo-repository.yaml --set-string githubConfigUrl="$(GITHUB_CONFIG_URL)"

install-observability:
	helm upgrade --install arc-observability charts/arc-observability --namespace "$(OBSERVABILITY_NAMESPACE)" --create-namespace --wait

install: install-controller install-runners install-observability

validate:
	scripts/validate.sh

template:
	scripts/template.sh

verify:
	scripts/verify.sh

cleanup:
	scripts/cleanup.sh

argocd-apply:
	@! rg -q 'OWNER/REPOSITORY' argocd || { echo "replace OWNER/REPOSITORY in argocd manifests first"; exit 1; }
	kubectl apply -f argocd/app-project.yaml -f argocd/controller-application.yaml -f argocd/runner-scale-set-application.yaml -f argocd/observability-application.yaml
