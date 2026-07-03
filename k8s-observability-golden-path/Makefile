SHELL := /bin/bash
PROFILE ?= local
NAMESPACE ?= observability
HELMFILE := helmfile -e $(PROFILE)

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
	kubectl apply -n $(NAMESPACE) -f rules/; \
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
	kubectl apply -f tests/fixtures/; \
	trap 'kubectl delete -f tests/fixtures/ --ignore-not-found >/dev/null' EXIT; \
	sleep 45; \
	kubectl -n observability-fixtures get pods; \
	kubectl -n $(NAMESPACE) port-forward svc/kube-prometheus-stack-prometheus 9091:9090 >/tmp/golden-path-test-prometheus.log 2>&1 & prom_pf=$$!; \
	kubectl -n $(NAMESPACE) port-forward svc/loki-gateway 3101:80 >/tmp/golden-path-test-loki.log 2>&1 & loki_pf=$$!; \
	trap 'kill $$prom_pf $$loki_pf 2>/dev/null || true; kubectl delete -f tests/fixtures/ --ignore-not-found >/dev/null' EXIT; \
	sleep 3; \
	curl -fsS -G http://127.0.0.1:9091/api/v1/query --data-urlencode 'query=kube_pod_status_phase{namespace="observability-fixtures",phase="Pending"}' >/dev/null; \
	curl -fsS -G http://127.0.0.1:9091/api/v1/query --data-urlencode 'query=kube_pod_container_status_restarts_total{namespace="observability-fixtures"}' >/dev/null; \
	curl -fsS -G http://127.0.0.1:3101/loki/api/v1/query --data-urlencode 'query={namespace="observability-fixtures"}' >/dev/null

uninstall:
	@set -euo pipefail; \
	kubectl delete -n $(NAMESPACE) -f rules/ --ignore-not-found; \
	kubectl -n $(NAMESPACE) delete configmap -l grafana_dashboard=1,app.kubernetes.io/part-of=observability-golden-path --ignore-not-found; \
	$(HELMFILE) destroy
