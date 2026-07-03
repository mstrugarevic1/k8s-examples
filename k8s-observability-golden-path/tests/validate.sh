#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-local}"
NAMESPACE="${2:-observability}"
CLUSTER="$PROFILE"
ENVIRONMENT="$PROFILE"
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
need ruby
need promtool

prom_pf=""
loki_pf=""
trap '[[ -n "$prom_pf" ]] && kill "$prom_pf" 2>/dev/null || true; [[ -n "$loki_pf" ]] && kill "$loki_pf" 2>/dev/null || true' EXIT

say "checking Kubernetes context"
kubectl config current-context >/dev/null || { echo "no current Kubernetes context"; exit 1; }

say "rendering Helmfile profiles"
helmfile -e local template >/tmp/golden-path-local.yaml
LOKI_S3_BUCKET=placeholder-bucket LOKI_S3_REGION=us-east-1 LOKI_S3_ENDPOINT=https://s3.invalid helmfile -e production template >/tmp/golden-path-production.yaml
test -s /tmp/golden-path-local.yaml
test -s /tmp/golden-path-production.yaml

say "checking dashboard JSON, UIDs, and variables"
python3 - <<'PY'
import json
from pathlib import Path

required = {
    "cluster-overview.json": {"cluster", "namespace"},
    "workload-reliability.json": {"cluster", "namespace", "workload", "pod"},
    "capacity-and-efficiency.json": {"cluster", "namespace", "workload"},
    "logs-and-events.json": {"cluster", "namespace", "workload", "pod", "container"},
    "observability-stack-health.json": {"cluster"},
}
uids = {}
for name, variables in required.items():
    data = json.loads(Path("dashboards", name).read_text())
    uid = data["uid"]
    if uid in uids:
        raise SystemExit(f"duplicate dashboard UID {uid}: {name} and {uids[uid]}")
    uids[uid] = name
    found = {v["name"] for v in data.get("templating", {}).get("list", [])}
    missing = variables - found
    if missing:
        raise SystemExit(f"{name} missing variables: {', '.join(sorted(missing))}")
    raw = json.dumps(data)
    for var in variables:
        if f"${var}" not in raw:
            raise SystemExit(f"{name} variable {var} is not used")
PY

say "checking required alerts, annotations, and runbooks"
python3 - <<'PY'
from pathlib import Path
text = Path("rules/alerts.yaml").read_text()
alerts = [
    "NodeNotReady", "WorkloadUnavailable", "PodCrashLooping",
    "ContainerOOMKilled", "PodStuckPending", "PersistentVolumeAlmostFull",
    "PrometheusTargetDown", "LokiIngestionFailing", "LokiDiscardingLogs",
    "FluentBitDroppingLogs",
]
missing = [a for a in alerts if f"alert: {a}" not in text]
if missing:
    raise SystemExit(f"missing alerts: {', '.join(missing)}")
for alert in alerts:
    block = text.split(f"alert: {alert}", 1)[1].split("\n        - alert:", 1)[0]
    for key in ("summary:", "description:", "impact:", "dashboard_url:", "runbook_url:"):
        if key not in block:
            raise SystemExit(f"{alert} missing annotation {key}")
    if f"runbooks/{alert}.md" not in block:
        raise SystemExit(f"{alert} runbook_url does not point at its runbook")
    if not Path("runbooks", f"{alert}.md").exists():
        raise SystemExit(f"{alert} missing runbook file")
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
    "golden_path:cluster_cpu_request_ratio",
    "golden_path:cluster_memory_request_ratio",
):
    if rule not in text:
        raise SystemExit(f"missing recording rule {rule}")
PY

say "checking Prometheus rule syntax with promtool"
for f in rules/*.yaml; do sed -e "s/__CLUSTER__/$CLUSTER/g" -e "s/__ENVIRONMENT__/$ENVIRONMENT/g" "$f"; echo "---"; done >/tmp/golden-path-prometheusrules.yaml
ruby -e 'require "yaml"; groups = ARGF.read.split(/^---$/).map { |doc| doc.strip.empty? ? nil : YAML.safe_load(doc).fetch("spec").fetch("groups") }.compact.flatten; puts({"groups" => groups}.to_yaml)' /tmp/golden-path-prometheusrules.yaml >/tmp/golden-path-rules.yaml
promtool check rules /tmp/golden-path-rules.yaml

if command -v shellcheck >/dev/null; then
  say "checking shell scripts with shellcheck"
  shellcheck tests/validate.sh
else
  echo "shellcheck not found; skipped shell script lint"
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
curl -fsS -G 'http://127.0.0.1:3100/loki/api/v1/query' --data-urlencode 'query={source=~"container|kubernetes-events"}' >/tmp/golden-path-loki.json
python3 - <<'PY'
import json
data = json.load(open("/tmp/golden-path-loki.json"))
if data.get("status") != "success":
    raise SystemExit("Loki query failed")
PY

say "validation passed"
