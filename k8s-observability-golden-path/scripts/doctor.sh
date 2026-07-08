#!/usr/bin/env bash
set -euo pipefail

need() { command -v "$1" >/dev/null || { echo "missing required tool: $1"; exit 1; }; }

need kubectl
need helm
need helmfile
need python3
need jq
need promtool

eval "$(scripts/resolve-config.sh)"

echo "profile: $PROFILE"
echo "namespace: $NAMESPACE"
echo "context: $KUBE_CONTEXT"
echo "cluster_name: $CLUSTER_NAME"
echo "environment: $ENVIRONMENT"
echo "storage_class: ${STORAGE_CLASS:-<default>}"
echo "vm_storage_size: $VM_STORAGE_SIZE"
echo "loki_storage_size: $LOKI_STORAGE_SIZE"

kubectl version --client >/dev/null
kubectl cluster-info >/dev/null
helm version --short >/dev/null
helmfile --version >/dev/null

nodes="$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')"
[[ "$nodes" -gt 0 ]] || { echo "no schedulable Kubernetes nodes found"; exit 1; }
kubectl get nodes -o wide

if [[ -n "$STORAGE_CLASS" ]]; then
  kubectl get storageclass "$STORAGE_CLASS" >/dev/null || { echo "StorageClass '$STORAGE_CLASS' not found"; exit 1; }
else
  kubectl get storageclass -o jsonpath='{range .items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")]}{.metadata.name}{"\n"}{end}' | grep -q . || {
    echo "no default StorageClass found; set STORAGE_CLASS or install one explicitly for local clusters"
    exit 1
  }
fi

for crd in servicemonitors.monitoring.coreos.com prometheusrules.monitoring.coreos.com; do
  if kubectl get crd "$crd" >/dev/null 2>&1; then
    echo "existing CRD: $crd"
  else
    echo "CRD will be installed by the prometheus-operator-crds release: $crd"
  fi
done
for crd in vmsingles.operator.victoriametrics.com vmagents.operator.victoriametrics.com vmrules.operator.victoriametrics.com; do
  if kubectl get crd "$crd" >/dev/null 2>&1; then
    echo "existing CRD: $crd"
  else
    echo "CRD will be installed by victoria-metrics-k8s-stack: $crd"
  fi
done

if [[ "$PROFILE" == production ]]; then
  [[ -n "${LOKI_OBJECT_STORE_BUCKET:-}" ]] || { echo "PROFILE=production requires LOKI_OBJECT_STORE_BUCKET"; exit 1; }
  [[ -n "${LOKI_OBJECT_STORE_REGION:-}" ]] || { echo "PROFILE=production requires LOKI_OBJECT_STORE_REGION"; exit 1; }
fi
