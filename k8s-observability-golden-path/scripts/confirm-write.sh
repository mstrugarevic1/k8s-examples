#!/usr/bin/env bash
set -euo pipefail

echo "write target: context=$KUBE_CONTEXT namespace=$NAMESPACE profile=$PROFILE"
if [[ "$PROFILE" == production && "${CONFIRM_PRODUCTION:-no}" != yes ]]; then
  echo "Refusing production write without CONFIRM_PRODUCTION=yes"
  exit 1
fi
