#!/usr/bin/env bash
set -euo pipefail

: "${CONTROLLER_NAMESPACE:=arc-systems}"
: "${RUNNER_NAMESPACE:=arc-runners-demo}"
: "${OBSERVABILITY_NAMESPACE:=observability}"
: "${RUNNER_SCALE_SET_NAME:=miroslav-kind-runners}"

kubectl cluster-info >/dev/null
kubectl get namespace "$CONTROLLER_NAMESPACE" "$RUNNER_NAMESPACE" "$OBSERVABILITY_NAMESPACE" >/dev/null
kubectl -n "$CONTROLLER_NAMESPACE" rollout status deployment -l app.kubernetes.io/component=controller-manager --timeout=2m
kubectl -n "$CONTROLLER_NAMESPACE" wait --for=condition=Ready pod -l "actions.github.com/scale-set-name=$RUNNER_SCALE_SET_NAME" --timeout=2m
kubectl -n "$RUNNER_NAMESPACE" get autoscalingrunnerset "$RUNNER_SCALE_SET_NAME" >/dev/null
kubectl -n "$OBSERVABILITY_NAMESPACE" get servicemonitor arc-controller arc-listener >/dev/null
kubectl -n "$OBSERVABILITY_NAMESPACE" get configmap github-arc-dashboard >/dev/null
kubectl -n "$CONTROLLER_NAMESPACE" get endpointslice -l kubernetes.io/service-name=arc-controller-metrics -o name | grep -q .
kubectl -n "$CONTROLLER_NAMESPACE" get endpointslice -l kubernetes.io/service-name=arc-listener-metrics -o name | grep -q .

legacy="$({ kubectl get runnerdeployments.actions.summerwind.dev -A -o name 2>/dev/null || true; kubectl get horizontalrunnerautoscalers.actions.summerwind.dev -A -o name 2>/dev/null || true; })"
test -z "$legacy" || { echo "legacy ARC resources are installed: $legacy" >&2; exit 1; }

echo "controller, listener, scale set, monitors, metric services, and dashboard are present"
echo "GitHub workflow execution is intentionally not tested by this target"
