#!/usr/bin/env python3
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DASH_DIR = Path("grafana/dashboards/golden-path")
PROM_UID = "prometheus"
LOKI_UID = "loki"
GRID_WIDTH = 24
SUPPORTED_PANEL_TYPES = {"stat", "timeseries", "gauge", "table", "logs"}
EXPECTED_DASHBOARDS = {
    "cluster-health.json": ("golden-path-cluster-health", "Cluster Health"),
    "workload-health.json": ("golden-path-workload-health", "Workload Health"),
    "capacity-saturation.json": ("golden-path-capacity-saturation", "Capacity & Saturation"),
    "logs-events.json": ("golden-path-logs-events", "Logs & Events"),
    "observability-stack-health.json": ("golden-path-stack-health", "Observability Stack Health"),
}
FORBIDDEN_QUERY_RE = re.compile(
    r"\b(aws_|azure_|gcp_|gce_|ebs_|efs_|cloudprovider_|cloud_controller_|cloud_controller_manager_|"
    r"cloud_load_balancer_|loadbalancer_|csi_(aws|azure|gce|gcp|ebs|efs)|"
    r"(aws|azure|gce|gcp|ebs|efs).*_csi_)",
    re.IGNORECASE,
)
SUBS = {
    "$namespace": "golden-path-demo",
    "$workload": "golden-path-api|golden-path-traffic|.*",
    "$pod": ".*",
    "$container": ".*",
    "$pending_threshold": "900",
    "$__range": "5m",
    "$__interval": "5m",
}


def dashboards():
    files = sorted(DASH_DIR.glob("*.json"))
    if len(files) != 5:
        raise SystemExit(f"expected exactly five dashboards, found {len(files)}")
    for path in files:
        yield path, json.loads(path.read_text())


def iter_panels(panels, *, collapsed=False):
    for panel in panels:
        yield panel, collapsed
        if panel.get("type") == "row":
            yield from iter_panels(panel.get("panels", []), collapsed=panel.get("collapsed", False))


def valid_datasource_uid(ds):
    if not isinstance(ds, dict):
        return False
    uid = ds.get("uid")
    dtype = ds.get("type")
    if dtype == "grafana" and uid == "-- Grafana --":
        return True
    return uid in {PROM_UID, LOKI_UID}


def targets():
    for path, data in dashboards():
        panel_ids = set()
        uid = data.get("uid")
        if not uid:
            raise SystemExit(f"{path} missing uid")
        for panel, _ in iter_panels(data.get("panels", [])):
            pid = panel.get("id")
            if pid in panel_ids:
                raise SystemExit(f"{path} duplicate panel id {pid}")
            panel_ids.add(pid)
            if panel.get("type") == "row":
                continue
            ds = panel.get("datasource", {})
            if not valid_datasource_uid(ds):
                raise SystemExit(f"{path} panel {pid} has invalid datasource {ds.get('uid')}")
            for target in panel.get("targets", []):
                target_ds = target.get("datasource")
                if target_ds and not valid_datasource_uid(target_ds):
                    raise SystemExit(f"{path} panel {pid} target has invalid datasource {target_ds.get('uid')}")
                expr = target.get("expr") or target.get("query")
                if expr:
                    yield path, data["title"], panel["title"], panel.get("type"), ds.get("uid"), expr


def substitute(expr):
    for key, value in SUBS.items():
        expr = expr.replace(key, value)
        expr = expr.replace("${" + key[1:] + "}", value)
    expr = re.sub(r"\$(\w+)", ".*", expr)
    return expr


def http_json(url, params):
    full = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full, timeout=15) as resp:
        return json.loads(resp.read().decode())


def query_prom(base, expr):
    return http_json(base.rstrip("/") + "/api/v1/query", {"query": expr})


def query_loki(base, expr, panel_type):
    if panel_type == "logs":
        now = time.time()
        return http_json(
            base.rstrip("/") + "/loki/api/v1/query_range",
            {"query": expr, "limit": "20", "start": str(int((now - 300) * 1_000_000_000)), "end": str(int(now * 1_000_000_000))},
        )
    return http_json(base.rstrip("/") + "/loki/api/v1/query", {"query": expr, "limit": "20"})


def static_check():
    uids = {}
    for path, data in dashboards():
        expected = EXPECTED_DASHBOARDS.get(path.name)
        if not expected:
            raise SystemExit(f"unexpected dashboard file {path}")
        expected_uid, expected_title = expected
        uid = data.get("uid")
        title = data.get("title")
        if uid != expected_uid or title != expected_title:
            raise SystemExit(f"{path} expected uid/title {expected_uid!r}/{expected_title!r}, found {uid!r}/{title!r}")
        if uid in uids:
            raise SystemExit(f"duplicate uid {uid}: {path} and {uids[uid]}")
        uids[uid] = path
        raw = json.dumps(data)
        if "label_values(up, cluster)" in raw:
            raise SystemExit(f"{path} uses unsupported cluster variable")
        validate_panels(path, data)
    seen = 0
    for path, dash, panel, _, _, expr in targets():
        if "$" in expr and not any(k in expr for k in SUBS):
            raise SystemExit(f"unknown dashboard variable in query: {expr}")
        if FORBIDDEN_QUERY_RE.search(expr):
            raise SystemExit(f"{path} {dash}/{panel} uses cloud/provider-specific metric dependency: {expr}")
        if "prometheus_tsdb_storage_blocks_bytes" in expr and "prometheus_tsdb_size_retentions_total" in expr:
            raise SystemExit(f"{path} {dash}/{panel} divides TSDB bytes by retention deletion counter: {expr}")
        seen += 1
    if seen < 20:
        raise SystemExit("too few dashboard queries found")


def validate_panels(path, data):
    panel_ids = set()
    visible_rects = []
    for panel, collapsed in iter_panels(data.get("panels", [])):
        pid = panel.get("id")
        if pid in panel_ids:
            raise SystemExit(f"{path} duplicate panel id {pid}")
        panel_ids.add(pid)

        if panel.get("type") == "row":
            continue

        grid = panel.get("gridPos")
        if not isinstance(grid, dict):
            raise SystemExit(f"{path} panel {pid} missing gridPos")
        try:
            x, y, w, h = (int(grid[k]) for k in ("x", "y", "w", "h"))
        except (KeyError, TypeError, ValueError):
            raise SystemExit(f"{path} panel {pid} has invalid gridPos {grid}")
        if w <= 0 or h <= 0:
            raise SystemExit(f"{path} panel {pid} has non-positive grid size {grid}")
        if x < 0 or y < 0 or x + w > GRID_WIDTH:
            raise SystemExit(f"{path} panel {pid} extends outside {GRID_WIDTH}-column grid: {grid}")

        ptype = panel.get("type")
        if ptype in SUPPORTED_PANEL_TYPES and not isinstance(panel.get("fieldConfig"), dict):
            raise SystemExit(f"{path} panel {pid} missing fieldConfig")
        if ptype == "gauge":
            default = panel.get("fieldConfig", {}).get("defaults", {})
            if default.get("unit") in {"percent", "percentunit"} and (
                default.get("min") is None or default.get("max") is None
            ):
                raise SystemExit(f"{path} panel {pid} percentage gauge missing min/max")

        if not collapsed:
            rect = (x, y, x + w, y + h, pid)
            for other in visible_rects:
                if x < other[2] and x + w > other[0] and y < other[3] and y + h > other[1]:
                    raise SystemExit(f"{path} panel {pid} overlaps panel {other[4]}")
            visible_rects.append(rect)


def live_check(prom_url, loki_url, expected_file=None):
    expected = set()
    if expected_file:
        for line in Path(expected_file).read_text().splitlines():
            line = line.strip()
            if line.startswith("- "):
                expected.add(line[2:].strip())
    failures = []
    for path, dash, panel, panel_type, ds, raw_expr in targets():
        expr = substitute(raw_expr)
        try:
            data = query_prom(prom_url, expr) if ds == PROM_UID else query_loki(loki_url, expr, panel_type)
            if data.get("status") != "success":
                failures.append(f"{dash}/{panel}: {data}")
                continue
            if panel in expected and not data.get("data", {}).get("result"):
                failures.append(f"{dash}/{panel}: expected demo data")
        except Exception as exc:
            failures.append(f"{dash}/{panel}: {exc}")
    if failures:
        raise SystemExit("\n".join(failures))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true")
    parser.add_argument("--prom-url", default="http://127.0.0.1:9090")
    parser.add_argument("--loki-url", default="http://127.0.0.1:3100")
    parser.add_argument("--expected")
    args = parser.parse_args()
    static_check()
    if not args.static:
        live_check(args.prom_url, args.loki_url, args.expected)


if __name__ == "__main__":
    main()
