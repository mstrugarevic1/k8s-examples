#!/usr/bin/env bash
set -euo pipefail

: "${CONTROLLER_NAMESPACE:=arc-systems}"
: "${RUNNER_NAMESPACE:=arc-runners-demo}"
: "${OBSERVABILITY_NAMESPACE:=observability}"

helm uninstall arc-demo --namespace "$RUNNER_NAMESPACE" --ignore-not-found
helm uninstall arc-controller --namespace "$CONTROLLER_NAMESPACE" --ignore-not-found
helm uninstall arc-observability --namespace "$OBSERVABILITY_NAMESPACE" --ignore-not-found
kubectl delete namespace "$RUNNER_NAMESPACE" "$CONTROLLER_NAMESPACE" --ignore-not-found

echo "ARC lab releases and namespaces removed; observability namespace retained"
