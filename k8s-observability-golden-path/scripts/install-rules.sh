#!/usr/bin/env bash
set -euo pipefail

config_file="$(mktemp)"
scripts/resolve-config.sh >"$config_file"
# shellcheck source=/dev/null
source "$config_file"
rm -f "$config_file"
for file in prometheus/*.yaml; do
  sed \
    -e "s/__CLUSTER_NAME__/$CLUSTER_NAME/g" \
    -e "s/__ENVIRONMENT__/$ENVIRONMENT/g" \
    -e "s/__NAMESPACE__/$NAMESPACE/g" \
    "$file"
  echo "---"
done | kubectl apply -n "$NAMESPACE" -f -
