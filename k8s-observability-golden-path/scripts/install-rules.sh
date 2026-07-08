#!/usr/bin/env bash
set -euo pipefail

eval "$(scripts/resolve-config.sh)"
for file in rules/*.yaml; do
  sed -e "s/__NAMESPACE__/$NAMESPACE/g" "$file"
  echo "---"
done | kubectl apply -n "$NAMESPACE" -f -
