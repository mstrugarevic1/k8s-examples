#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-local}"
NAMESPACE="${2:-observability}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

need() {
  command -v "$1" >/dev/null || { echo "missing $1"; exit 1; }
}

say() {
  printf '==> %s\n' "$1"
}

need kubectl
need helm
need helmfile
need python3
need curl
prom_pf=""
loki_pf=""
trap '[[ -n "$prom_pf" ]] && kill "$prom_pf" 2>/dev/null || true; [[ -n "$loki_pf" ]] && kill "$loki_pf" 2>/dev/null || true' EXIT

say "checking Kubernetes context"
kubectl config current-context >/dev/null || { echo "no current Kubernetes context"; exit 1; }

say "rendering Helmfile"
helmfile -e "$PROFILE" template >/tmp/golden-path-helmfile.yaml
test -s /tmp/golden-path-helmfile.yaml

say "checking dashboard JSON"
python3 -m json.tool dashboards/cluster-health.json >/dev/null
python3 -m json.tool dashboards/workload-reliability.json >/dev/null
python3 -m json.tool dashboards/capacity.json >/dev/null
python3 -m json.tool dashboards/logs.json >/dev/null
python3 -m json.tool dashboards/stack-health.json >/dev/null

say "checking required alerts and annotations"
python3 - <<'PY'
from pathlib import Path
text = Path("rules/alerts.yaml").read_text()
alerts = [
    "NodeNotReady", "WorkloadUnavailable", "PodCrashLooping",
    "ContainerOOMKilled", "PodStuckPending", "PersistentVolumeAlmostFull",
    "PrometheusTargetDown", "LokiIngestionFailing", "FluentBitDroppingLogs",
]
missing = [a for a in alerts if f"alert: {a}" not in text]
if missing:
    raise SystemExit(f"missing alerts: {', '.join(missing)}")
for alert in alerts:
    block = text.split(f"alert: {alert}", 1)[1].split("\n        - alert:", 1)[0]
    for key in ("summary:", "description:", "impact:", "runbook_url:"):
        if key not in block:
            raise SystemExit(f"{alert} missing annotation {key}")
PY

say "checking recording rules"
python3 - <<'PY'
from pathlib import Path
text = Path("rules/recording-rules.yaml").read_text()
for rule in (
    "golden_path:workload_readiness_ratio",
    "golden_path:namespace_cpu_usage_ratio",
    "golden_path:namespace_memory_usage_ratio",
    "golden_path:pod_restart_rate",
):
    if rule not in text:
        raise SystemExit(f"missing recording rule {rule}")
PY

if command -v promtool >/dev/null; then
  say "checking Prometheus rule syntax with promtool"
  python3 - <<'PY' >/tmp/golden-path-rules.yaml
from pathlib import Path
print("groups:")
for p in ("rules/alerts.yaml", "rules/recording-rules.yaml"):
    text = Path(p).read_text()
    spec = text.split("spec:\n", 1)[1]
    for line in spec.splitlines()[1:]:
        print(line[2:] if line.startswith("  ") else line)
PY
  promtool check rules /tmp/golden-path-rules.yaml
else
  echo "promtool not found; skipped Prometheus expression syntax check"
fi

say "checking installed Prometheus targets"
kubectl -n "$NAMESPACE" get svc kube-prometheus-stack-prometheus >/dev/null
kubectl -n "$NAMESPACE" port-forward svc/kube-prometheus-stack-prometheus 9090:9090 >/tmp/golden-path-prometheus.log 2>&1 &
prom_pf=$!
sleep 3
curl -fsS 'http://127.0.0.1:9090/api/v1/query?query=up' >/tmp/golden-path-up.json
python3 - <<'PY'
import json
data = json.load(open("/tmp/golden-path-up.json"))
if data.get("status") != "success" or not data["data"]["result"]:
    raise SystemExit("Prometheus target query returned no data")
PY

say "checking Loki log ingestion"
kubectl -n "$NAMESPACE" get svc loki-gateway >/dev/null
kubectl -n "$NAMESPACE" port-forward svc/loki-gateway 3100:80 >/tmp/golden-path-loki.log 2>&1 &
loki_pf=$!
sleep 3
curl -fsS -G 'http://127.0.0.1:3100/loki/api/v1/query' --data-urlencode 'query={namespace=~".+"}' >/tmp/golden-path-loki.json
python3 - <<'PY'
import json
data = json.load(open("/tmp/golden-path-loki.json"))
if data.get("status") != "success":
    raise SystemExit("Loki query failed")
PY

say "validation passed"
