#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_PAT:?set GITHUB_PAT}"
: "${ARC_RUNNER_NAMESPACE:?set ARC_RUNNER_NAMESPACE}"

kubectl create namespace "$ARC_RUNNER_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "$ARC_RUNNER_NAMESPACE" create secret generic github-pat \
  --from-literal=github_token="$GITHUB_PAT" \
  --dry-run=client -o yaml | kubectl apply -f -
