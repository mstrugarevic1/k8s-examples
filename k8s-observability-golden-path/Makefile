SHELL := /bin/bash
PROFILE ?= local
NAMESPACE ?= observability
HELMFILE := helmfile -e $(PROFILE)
CLUSTER := $(PROFILE)
ENVIRONMENT := $(PROFILE)

.PHONY: prerequisites install status validate grafana test uninstall

prerequisites:
	@set -euo pipefail; \
	for bin in kubectl helm helmfile; do command -v $$bin >/dev/null || { echo "missing $$bin"; exit 1; }; done; \
	kubectl config current-context >/dev/null || { echo "no current Kubernetes context"; exit 1; }; \
	echo "context: $$(kubectl config current-context)"; \
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null; \
	helm repo add grafana https://grafana.github.io/helm-charts >/dev/null; \
	helm repo add fluent https://fluent.github.io/helm-charts >/dev/null; \
	helm repo update >/dev/null

install: prerequisites
	@set -euo pipefail; \
	if [[ "$(PROFILE)" == "production" && -z "$${LOKI_S3_BUCKET:-}" ]]; then echo "PROFILE=production requires LOKI_S3_BUCKET and S3 credentials or workload identity"; exit 1; fi; \
	$(HELMFILE) sync; \
	for f in rules/*.yaml; do sed -e 's/__CLUSTER__/$(CLUSTER)/g' -e 's/__ENVIRONMENT__/$(ENVIRONMENT)/g' "$$f"; echo "---"; done | kubectl apply -n $(NAMESPACE) -f -; \
	kubectl -n $(NAMESPACE) delete configmap -l grafana_dashboard=1,app.kubernetes.io/part-of=observability-golden-path --ignore-not-found; \
	for f in dashboards/*.json; do \
	  name="golden-path-$$(basename "$$f" .json)"; \
	  kubectl -n $(NAMESPACE) create configmap "$$name" --from-file="$$(basename "$$f")=$$f" --dry-run=client -o yaml | \
	  kubectl label -f - --local -o yaml grafana_dashboard=1 app.kubernetes.io/part-of=observability-golden-path | \
	  kubectl apply -f -; \
	done; \
	kubectl -n $(NAMESPACE) rollout status deploy/kube-prometheus-stack-grafana --timeout=5m

status:
	@set -euo pipefail; \
	kubectl config current-context >/dev/null || { echo "no current Kubernetes context"; exit 1; }; \
	kubectl -n $(NAMESPACE) get pods,svc; \
	kubectl -n $(NAMESPACE) get prometheusrules,configmaps -l app.kubernetes.io/part-of=observability-golden-path

validate:
	@tests/validate.sh $(PROFILE) $(NAMESPACE)

grafana:
	@set -euo pipefail; \
	kubectl -n $(NAMESPACE) get svc kube-prometheus-stack-grafana >/dev/null || { echo "Grafana service not found; run make install first"; exit 1; }; \
	echo "Grafana: http://localhost:3000  user: admin  password: stored in secret kube-prometheus-stack-grafana"; \
	kubectl -n $(NAMESPACE) port-forward svc/kube-prometheus-stack-grafana 3000:80

test:
	@set -euo pipefail; \
	command -v curl >/dev/null || { echo "missing curl"; exit 1; }; \
	command -v python3 >/dev/null || { echo "missing python3"; exit 1; }; \
	kubectl apply -f tests/fixtures/; \
	trap 'kubectl delete -f tests/fixtures/ --ignore-not-found >/dev/null' EXIT; \
	sleep 90; \
	kubectl -n observability-fixtures get pods; \
	kubectl -n $(NAMESPACE) port-forward svc/kube-prometheus-stack-prometheus 9091:9090 >/tmp/golden-path-test-prometheus.log 2>&1 & prom_pf=$$!; \
	kubectl -n $(NAMESPACE) port-forward svc/loki-gateway 3101:80 >/tmp/golden-path-test-loki.log 2>&1 & loki_pf=$$!; \
	trap 'kill $$prom_pf $$loki_pf 2>/dev/null || true; kubectl delete -f tests/fixtures/ --ignore-not-found >/dev/null' EXIT; \
	sleep 3; \
	curl -fsS -G http://127.0.0.1:9091/api/v1/query --data-urlencode 'query=kube_pod_status_phase{namespace="observability-fixtures",pod="pending-too-large",phase="Pending"}' > /tmp/golden-path-test-pending.json; \
	curl -fsS -G http://127.0.0.1:9091/api/v1/query --data-urlencode 'query=kube_pod_container_status_restarts_total{namespace="observability-fixtures",pod=~"crashloop.*"}' > /tmp/golden-path-test-restarts.json; \
	curl -fsS -G http://127.0.0.1:9091/api/v1/query --data-urlencode 'query=kube_pod_container_status_last_terminated_reason{namespace="observability-fixtures",pod=~"excessive-memory.*",reason="OOMKilled"}' > /tmp/golden-path-test-oom.json; \
	curl -fsS -G http://127.0.0.1:9091/api/v1/query --data-urlencode 'query=ALERTS{alertname=~"WorkloadUnavailable|PodCrashLooping|ContainerOOMKilled|PodStuckPending",namespace="observability-fixtures",alertstate=~"pending|firing"}' > /tmp/golden-path-test-alerts.json; \
	curl -fsS -G http://127.0.0.1:9091/api/v1/query --data-urlencode 'query=sum(golden_path:pod_restart_rate{namespace="observability-fixtures"})' > /tmp/golden-path-test-dashboard-query.json; \
	curl -fsS -G http://127.0.0.1:3101/loki/api/v1/query_range --data-urlencode 'query={namespace="observability-fixtures",source="container"}' --data-urlencode 'limit=20' > /tmp/golden-path-test-logs.json; \
	curl -fsS -G http://127.0.0.1:3101/loki/api/v1/query_range --data-urlencode 'query={namespace="observability-fixtures",source="kubernetes-events",reason=~"FailedScheduling|FailedMount|BackOff|Unhealthy|ImagePullBackOff|Killing"}' --data-urlencode 'limit=20' > /tmp/golden-path-test-events.json; \
	python3 -c 'import json; value=lambda p: sum(float(r["value"][1]) for r in json.load(open(p))["data"]["result"]); streams=lambda p: len(json.load(open(p))["data"]["result"]); values=lambda p: sum(len(r.get("values", [])) for r in json.load(open(p))["data"]["result"]); ok=lambda p: json.load(open(p))["status"] == "success"; assert value("/tmp/golden-path-test-pending.json") > 0, "Pending fixture metric missing"; assert value("/tmp/golden-path-test-restarts.json") > 0, "CrashLoop fixture metric missing"; assert value("/tmp/golden-path-test-oom.json") > 0, "OOMKilled fixture metric missing"; assert streams("/tmp/golden-path-test-alerts.json") > 0, "Expected custom alert missing"; assert ok("/tmp/golden-path-test-dashboard-query.json"), "Dashboard query failed"; assert values("/tmp/golden-path-test-logs.json") > 0, "Container logs missing from Loki"; assert values("/tmp/golden-path-test-events.json") > 0, "Kubernetes Events missing from Loki"'

uninstall:
	@set -euo pipefail; \
	kubectl -n $(NAMESPACE) delete prometheusrule -l app.kubernetes.io/part-of=observability-golden-path --ignore-not-found; \
	kubectl -n $(NAMESPACE) delete configmap -l grafana_dashboard=1,app.kubernetes.io/part-of=observability-golden-path --ignore-not-found; \
	$(HELMFILE) destroy
