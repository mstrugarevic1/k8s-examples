#!/usr/bin/env bash
set -euo pipefail

eval "$(scripts/resolve-config.sh)"
kubectl -n "$NAMESPACE" delete configmap -l grafana_dashboard=1,app.kubernetes.io/part-of=observability-golden-path --ignore-not-found
for file in grafana/dashboards/golden-path/*.json; do
  name="golden-path-$(basename "$file" .json)"
  kubectl -n "$NAMESPACE" create configmap "$name" --from-file="$(basename "$file")=$file" --dry-run=client -o yaml |
    kubectl label -f - --local -o yaml grafana_dashboard=1 app.kubernetes.io/part-of=observability-golden-path |
    kubectl apply -f -
done
