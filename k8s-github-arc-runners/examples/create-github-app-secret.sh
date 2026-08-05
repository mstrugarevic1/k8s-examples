#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_APP_ID:?set GITHUB_APP_ID}"
: "${GITHUB_APP_INSTALLATION_ID:?set GITHUB_APP_INSTALLATION_ID}"
: "${GITHUB_APP_PRIVATE_KEY_FILE:?set GITHUB_APP_PRIVATE_KEY_FILE}"
: "${ARC_RUNNER_NAMESPACE:?set ARC_RUNNER_NAMESPACE}"

test -r "$GITHUB_APP_PRIVATE_KEY_FILE" || {
  echo "private key file is not readable" >&2
  exit 1
}

kubectl create namespace "$ARC_RUNNER_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "$ARC_RUNNER_NAMESPACE" create secret generic github-app-credentials \
  --from-literal=github_app_id="$GITHUB_APP_ID" \
  --from-literal=github_app_installation_id="$GITHUB_APP_INSTALLATION_ID" \
  --from-file=github_app_private_key="$GITHUB_APP_PRIVATE_KEY_FILE" \
  --dry-run=client -o yaml | kubectl apply -f -
