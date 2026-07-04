#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import time
import urllib.request


def run(cmd, check=True):
    return subprocess.run(cmd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def wait_http(url, timeout=60):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                body = resp.read().decode()
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return body
        except Exception as exc:
            last = exc
            time.sleep(2)
    raise RuntimeError(f"{url} not ready: {last}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    env = run(["bash", "-lc", "scripts/resolve-config.sh"]).stdout
    vals = {}
    for line in env.splitlines():
        key, value = line.replace("export ", "", 1).split("=", 1)
        vals[key] = value.strip("'")
    ns = vals["NAMESPACE"]

    run(["kubectl", "-n", ns, "get", "helmrelease"], check=False)
    for svc in ["kube-prometheus-stack-prometheus", "kube-prometheus-stack-grafana", "loki-gateway"]:
        run(["kubectl", "-n", ns, "get", "svc", svc])
    run(["kubectl", "-n", ns, "wait", "--for=condition=Ready", "pods", "--all", "--timeout=5m"])
    run(["kubectl", "-n", ns, "get", "pvc"])

    prom = subprocess.Popen(["kubectl", "-n", ns, "port-forward", "svc/kube-prometheus-stack-prometheus", "9090:9090"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    loki = subprocess.Popen(["kubectl", "-n", ns, "port-forward", "svc/loki-gateway", "3100:80"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    grafana = subprocess.Popen(["kubectl", "-n", ns, "port-forward", "svc/kube-prometheus-stack-grafana", "3000:80"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_http("http://127.0.0.1:9090/-/ready")
        wait_http("http://127.0.0.1:3100/loki/api/v1/status/buildinfo")
        wait_http("http://127.0.0.1:3000/api/health")
        expected = ["--expected", "tests/expected-panels.yaml"] if args.demo else []
        run(["python3", "scripts/validate-dashboards.py", "--prom-url", "http://127.0.0.1:9090", "--loki-url", "http://127.0.0.1:3100", *expected])
    finally:
        for proc in (prom, loki, grafana):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
