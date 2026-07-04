#!/usr/bin/env bash
set -euo pipefail

config_file="$(mktemp)"
scripts/resolve-config.sh >"$config_file"
# shellcheck source=/dev/null
source "$config_file"
rm -f "$config_file"
kubectl -n "$NAMESPACE" rollout status deploy/kube-prometheus-stack-grafana --timeout=10m
kubectl -n "$NAMESPACE" rollout status deploy/kube-prometheus-stack-kube-state-metrics --timeout=10m
kubectl -n "$NAMESPACE" rollout status daemonset/kube-prometheus-stack-prometheus-node-exporter --timeout=10m
kubectl -n "$NAMESPACE" rollout status daemonset/fluent-bit --timeout=10m
kubectl -n "$NAMESPACE" rollout status statefulset/prometheus-kube-prometheus-stack-prometheus --timeout=10m
kubectl -n "$NAMESPACE" rollout status statefulset/alertmanager-kube-prometheus-stack-alertmanager --timeout=10m || true
kubectl -n "$NAMESPACE" get pvc
