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
SUBS = {
    "$namespace": "golden-path-demo",
    "$workload": "golden-path-api|golden-path-traffic|.*",
    "$pod": ".*",
    "$container": ".*",
    "$pending_threshold": "900",
    "$__range": "5m",
}


def dashboards():
    files = sorted(DASH_DIR.glob("*.json"))
    if len(files) != 5:
        raise SystemExit(f"expected exactly five dashboards, found {len(files)}")
    for path in files:
        yield path, json.loads(path.read_text())


def targets():
    for path, data in dashboards():
        panel_ids = set()
        uid = data.get("uid")
        if not uid:
            raise SystemExit(f"{path} missing uid")
        for panel in data.get("panels", []):
            pid = panel.get("id")
            if pid in panel_ids:
                raise SystemExit(f"{path} duplicate panel id {pid}")
            panel_ids.add(pid)
            ds = panel.get("datasource", {}).get("uid")
            if ds not in {PROM_UID, LOKI_UID}:
                raise SystemExit(f"{path} panel {pid} has invalid datasource {ds}")
            for target in panel.get("targets", []):
                expr = target.get("expr") or target.get("query")
                if expr:
                    yield path, data["title"], panel["title"], ds, expr


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


def query_loki(base, expr):
    return http_json(base.rstrip("/") + "/loki/api/v1/query", {"query": expr, "limit": "20"})


def static_check():
    uids = {}
    expected_titles = {
        "Cluster Health",
        "Workload Health",
        "Capacity & Saturation",
        "Logs & Events",
        "Observability Stack Health",
    }
    titles = set()
    for path, data in dashboards():
        titles.add(data.get("title"))
        uid = data["uid"]
        if uid in uids:
            raise SystemExit(f"duplicate uid {uid}: {path} and {uids[uid]}")
        uids[uid] = path
        raw = json.dumps(data)
        if "label_values(up, cluster)" in raw:
            raise SystemExit(f"{path} uses unsupported cluster variable")
    if titles != expected_titles:
        raise SystemExit(f"dashboard title mismatch: {sorted(titles)}")
    seen = 0
    for _, _, _, _, expr in targets():
        if "$" in expr and not any(k in expr for k in SUBS):
            raise SystemExit(f"unknown dashboard variable in query: {expr}")
        seen += 1
    if seen < 20:
        raise SystemExit("too few dashboard queries found")


def live_check(prom_url, loki_url, expected_file=None):
    expected = set()
    if expected_file:
        for line in Path(expected_file).read_text().splitlines():
            line = line.strip()
            if line.startswith("- "):
                expected.add(line[2:].strip())
    failures = []
    for path, dash, panel, ds, raw_expr in targets():
        expr = substitute(raw_expr)
        try:
            data = query_prom(prom_url, expr) if ds == PROM_UID else query_loki(loki_url, expr)
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
