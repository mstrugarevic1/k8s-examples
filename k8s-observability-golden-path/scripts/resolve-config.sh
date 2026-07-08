#!/usr/bin/env bash
set -euo pipefail

sanitize() {
  tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9_.-]+/-/g; s/^-+//; s/-+$//; s/^$/cluster/'
}

profile="${PROFILE:-kind}"
namespace="${NAMESPACE:-observability}"
environment="${ENVIRONMENT:-$profile}"
context="$(kubectl config current-context 2>/dev/null || true)"
cluster="${CLUSTER_NAME:-}"

if [[ -z "$cluster" ]]; then
  [[ -n "$context" ]] || { echo "no Kubernetes context" >&2; exit 1; }
  cluster="$(printf '%s' "$context" | sanitize)"
else
  cluster="$(printf '%s' "$cluster" | sanitize)"
fi

case "$profile" in
  kind|local|production) ;;
  *) echo "PROFILE must be kind, local, or production" >&2; exit 1 ;;
esac

cat <<EOF
export PROFILE=$(printf '%q' "$profile")
export NAMESPACE=$(printf '%q' "$namespace")
export ENVIRONMENT=$(printf '%q' "$environment")
export CLUSTER_NAME=$(printf '%q' "$cluster")
export STORAGE_CLASS=$(printf '%q' "${STORAGE_CLASS:-}")
export VM_STORAGE_SIZE=$(printf '%q' "${VM_STORAGE_SIZE:-8Gi}")
export VM_RETENTION=$(printf '%q' "${VM_RETENTION:-24h}")
export LOKI_STORAGE_SIZE=$(printf '%q' "${LOKI_STORAGE_SIZE:-10Gi}")
export LOKI_RETENTION=$(printf '%q' "${LOKI_RETENTION:-24h}")
export GRAFANA_STORAGE_SIZE=$(printf '%q' "${GRAFANA_STORAGE_SIZE:-2Gi}")
export ALERTMANAGER_STORAGE_SIZE=$(printf '%q' "${ALERTMANAGER_STORAGE_SIZE:-2Gi}")
export CONFIRM_PRODUCTION=$(printf '%q' "${CONFIRM_PRODUCTION:-no}")
export KUBE_CONTEXT=$(printf '%q' "$context")
EOF
