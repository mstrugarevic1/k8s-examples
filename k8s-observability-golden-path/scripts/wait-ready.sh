#!/usr/bin/env bash
set -euo pipefail

eval "$(scripts/resolve-config.sh)"
kubectl -n "$NAMESPACE" rollout status deploy/victoria-metrics-k8s-stack-grafana --timeout=10m
kubectl -n "$NAMESPACE" rollout status deploy/victoria-metrics-k8s-stack-kube-state-metrics --timeout=10m
kubectl -n "$NAMESPACE" rollout status daemonset/victoria-metrics-k8s-stack-prometheus-node-exporter --timeout=10m
kubectl -n "$NAMESPACE" rollout status daemonset/fluent-bit --timeout=10m
if [[ "$PROFILE" == production ]]; then
  kubectl -n "$NAMESPACE" rollout status statefulset/vmstorage-vm --timeout=10m
  kubectl -n "$NAMESPACE" rollout status deploy/vminsert-vm --timeout=10m
else
  kubectl -n "$NAMESPACE" rollout status deploy/vmsingle-vm --timeout=10m
fi
kubectl -n "$NAMESPACE" rollout status deploy/vmagent-vm --timeout=10m
kubectl -n "$NAMESPACE" rollout status deploy/vmalert-vm --timeout=10m
# VMAlertmanager uses the OnDelete update strategy, which rollout status does not support.
kubectl -n "$NAMESPACE" wait --for=condition=Ready pod -l app.kubernetes.io/name=vmalertmanager --timeout=10m
kubectl -n "$NAMESPACE" get pvc
