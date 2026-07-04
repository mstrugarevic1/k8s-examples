#!/usr/bin/env bash
set -euo pipefail

config_file="$(mktemp)"
scripts/resolve-config.sh >"$config_file"
# shellcheck source=/dev/null
source "$config_file"
rm -f "$config_file"
kind="${1:?usage: port-forward.sh grafana|prometheus|loki}"
case "$kind" in
  grafana) svc=kube-prometheus-stack-grafana; local_port=3000; remote_port=80; url=http://localhost:3000 ;;
  prometheus) svc=kube-prometheus-stack-prometheus; local_port=9090; remote_port=9090; url=http://localhost:9090 ;;
  loki) svc=loki-gateway; local_port=3100; remote_port=80; url=http://localhost:3100 ;;
  *) echo "unknown port-forward target: $kind"; exit 1 ;;
esac

echo "$kind: $url"
kubectl -n "$NAMESPACE" port-forward "svc/$svc" "$local_port:$remote_port"
