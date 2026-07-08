#!/usr/bin/env bash
set -euo pipefail

eval "$(scripts/resolve-config.sh)"
kind="${1:?usage: port-forward.sh grafana|metrics|loki}"
case "$kind" in
  grafana) svc=victoria-metrics-k8s-stack-grafana; local_port=3000; remote_port=80; url=http://localhost:3000 ;;
  metrics)
    if [[ "$PROFILE" == production ]]; then
      svc=vmselect-vm; local_port=8481; remote_port=8481; url=http://localhost:8481/select/0/prometheus
    else
      svc=vmsingle-vm; local_port=8428; remote_port=8428; url=http://localhost:8428
    fi ;;
  loki) svc=loki-gateway; local_port=3100; remote_port=80; url=http://localhost:3100 ;;
  *) echo "unknown port-forward target: $kind"; exit 1 ;;
esac

echo "$kind: $url"
kubectl -n "$NAMESPACE" port-forward "svc/$svc" "$local_port:$remote_port"
