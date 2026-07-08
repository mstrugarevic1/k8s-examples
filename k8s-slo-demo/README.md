# Kubernetes SLI/SLO Demo

This project contains a practical demonstration of Service Level Indicators (SLIs), Service Level Objectives (SLOs), and Service Level Agreements (SLAs) using a Python Flask application on Kubernetes, monitored by Prometheus and Grafana.

## Table of Contents

* [Purpose](#purpose)
* [Why SLI, SLO and SLA measurements matter](#why-sli-slo-and-sla-measurements-matter)
* [Definitions](#definitions)
* [Demo SLI](#demo-sli)
* [Practical examples](#practical-examples)
* [Prerequisites](#prerequisites)
* [Step-by-Step Workflow](#step-by-step-workflow)
    * [1. Create or select the Kind cluster](#1-create-or-select-the-kind-cluster)
    * [2. Build the local image](#2-build-the-local-image)
    * [3. Load the image into Kind](#3-load-the-image-into-kind)
    * [4. Deploy the application](#4-deploy-the-application)
    * [5. Deploy the ServiceMonitor](#5-deploy-the-servicemonitor)
    * [6. Verify the Prometheus target](#6-verify-the-prometheus-target)
    * [7. Deploy the load generator](#7-deploy-the-load-generator)
    * [8. Access Grafana](#8-access-grafana)
    * [9. Import the Grafana dashboard](#9-import-the-grafana-dashboard)
* [Interpreting the Dashboard](#interpreting-the-dashboard)
* [Dashboard Preview](#dashboard-preview)
* [Verification Commands](#verification-commands)
* [Troubleshooting](#troubleshooting)
* [Cleanup](#cleanup)

## Purpose

The goal of this demo is to show how to measure and visualize service reliability. It simulates a realistic service with occasional failures and latency, allowing you to see how these impact your SLIs, SLOs, and error budgets.

## Why SLI, SLO and SLA measurements matter

Measuring service levels is fundamental to Site Reliability Engineering (SRE). It allows teams to:
* **Quantify reliability:** Move from "the service feels unreliable" to "the availability SLI is 99.7%".
* **Manage error budgets:** Use data to decide when to focus on features vs. reliability.
* **Define clear expectations:** Align engineering, product, and customers on what "reliable" means.
* **Alert on what matters:** Reduce alert fatigue by alerting on SLO consumption rather than individual component failures.

## Definitions

* **SLI (Service Level Indicator):** The actual measured behavior. In this demo, the availability SLI is successful HTTP requests divided by all service requests.
* **SLO (Service Level Objective):** Internal target for the SLI (99.9% availability).
* **SLA (Service Level Agreement):** Contractual commitment for the SLI (99.5% availability).
* **Error Budget:** The allowable unreliability (0.1% for our 99.9% SLO).

## Demo SLI

Prometheus calculates the availability SLI from the application request counter:

```promql
100 *
sum(rate(slo_demo_http_requests_total{route!~"/metrics|/healthz", status=~"2.."}[5m]))
/
sum(rate(slo_demo_http_requests_total{route!~"/metrics|/healthz"}[5m]))
```

The demo load generator intentionally produces about **99.7% availability**. That keeps the service above the 99.5% SLA but below the 99.9% SLO, so the dashboard shows an SLI that is good enough contractually while still burning the internal SLO error budget.

## Practical examples

Use SLIs, SLOs and SLAs on user-facing service paths, not on monitoring or health-check endpoints. In this demo, that means the Flask application endpoints `/`, `/slow` and `/fail` count as service traffic, while `/metrics` and `/healthz` are excluded.

### Example 1: Availability

* **Need:** Users care whether the service answers successfully.
* **Application:** The `slo-demo` Flask service.
* **Traffic counted:** All user-facing HTTP requests.
* **SLI calculation:** `successful requests / total requests`.
* **SLO target:** 99.9% availability.
* **SLA target:** 99.5% availability.

For 100,000 requests, 99.7% availability means:

```text
99,700 successful requests / 100,000 total requests = 99.7% availability SLI
```

That misses the 99.9% SLO, so engineering is burning internal error budget. It still meets the 99.5% SLA, so it has not breached the external commitment.

### Example 2: Latency

* **Need:** A service can be "up" but still too slow for users.
* **Application:** The same `slo-demo` Flask service, especially the `/slow` endpoint.
* **Traffic counted:** User-facing HTTP request durations.
* **SLI calculation:** 95th percentile request latency.
* **Example SLO:** 95% of requests should finish under 500 ms.
* **Example SLA:** 95% of requests should finish under 1 second.

The demo dashboard shows P95 and P99 latency from `slo_demo_http_request_duration_seconds_bucket`. This demo does not enforce a latency SLO in the error-budget panels; it displays latency beside availability so you can see when successful requests are still slow.

### Example 3: Error budget

* **Need:** Teams need a concrete answer to "can we keep shipping or should we fix reliability first?"
* **Application:** The `slo-demo` Flask service.
* **Traffic counted:** Failed user-facing requests.
* **Calculation:** `actual error rate / allowed error rate`.

For a 99.9% SLO, the allowed error rate is 0.1%. If the app is actually failing 0.3% of requests:

```text
0.3% actual error rate / 0.1% allowed error rate = 3x burn rate
```

A 3x burn rate means the service is consuming its error budget three times faster than planned.

## Prerequisites

* [Docker](https://docs.docker.com/get-docker/)
* [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/)
* [kubectl](https://kubernetes.io/docs/tasks/tools/)
* A Kubernetes cluster with **Prometheus Operator** and **Grafana** already installed (e.g., via `kube-prometheus-stack`).

## Step-by-Step Workflow

### 1. Create or select the Kind cluster

If you don't have a cluster yet, you can create an empty one with Kind:

```bash
kind create cluster --name slo-demo
```

*Note: `kind create cluster` creates a basic Kubernetes cluster. Prometheus Operator and Grafana must be installed separately (e.g., via `kube-prometheus-stack`) before you can proceed with the ServiceMonitor and dashboard steps. If you already have a monitored cluster, you can skip this step.*

### 2. Build the local image

Build the application image locally. We use a local tag to avoid the need for an external registry.

```bash
docker build -t slo-demo:0.1.0 .
```

### 3. Load the image into Kind

This command copies the locally built image into the Kind node's container runtime.

```bash
kind load docker-image slo-demo:0.1.0 --name slo-demo
```

### 4. Deploy the application

Apply the namespace and application manifests:

```bash
kubectl apply -f k8s/app.yaml
```

### 5. Deploy the ServiceMonitor

The ServiceMonitor tells Prometheus to scrape metrics from our application.

```bash
kubectl apply -f k8s/servicemonitor.yaml
```

*Note: The `release` label in `k8s/servicemonitor.yaml` must match the Helm release name of your `kube-prometheus-stack` (e.g., `monitoring`). You can find this name by running `helm list -A`.*

### 6. Verify the Prometheus target

Check the Prometheus UI (Targets page) to ensure `slo-demo` is discovered and being scraped successfully. You can port-forward Prometheus to access it:

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090
```

Visit: [http://localhost:9090/targets](http://localhost:9090/targets)

### 7. Deploy the load generator

The load generator produces a deterministic pattern of traffic: ~99.7% success rate.

```bash
kubectl apply -f k8s/load-generator.yaml
```

### 8. Access Grafana

Port-forward the Grafana service to access it locally:

```bash
kubectl port-forward -n monitoring service/monitoring-grafana 3000:80
```

Access via: [http://localhost:3000](http://localhost:3000)
Default username: `admin`

Retrieve the admin password:

```bash
kubectl get secret \
  --namespace monitoring \
  monitoring-grafana \
  -o jsonpath='{.data.admin-password}' |
  base64 --decode
echo
```

### 9. Import the Grafana dashboard

1. Open your Grafana UI.
2. Go to **Dashboards** -> **Import**.
3. Upload the `grafana/slo-dashboard.json` file.
4. Select your Prometheus datasource.

## Interpreting the Dashboard

The dashboard consists of seven key panels:

1. **Availability SLI vs SLO and SLA:** A time-series view of the measured availability SLI compared to our 99.9% SLO and 99.5% SLA lines.
2. **Availability SLI:** A stat panel showing the current measured SLI for the selected time range.
3. **SLO Burn Rate:** A stat panel showing how quickly the service consumes its 99.9% SLO error budget. A burn rate of 1.0 means the budget is being consumed exactly at the rate that will exhaust it by the end of the evaluation period. Values above 1.0 are not sustainable.
4. **Error Budget Remaining:** A gauge showing how much of your error budget (based on the 99.9% SLO) remains for the selected time range.
5. **Request Rate:** Total traffic volume, grouped by HTTP status code.
6. **HTTP 5xx Error Rate:** A focused view of server-side errors.
7. **P95 and P99 Request Latency:** Tail latency, highlighting the slow requests.

## Dashboard Preview

The dashboard below shows the measured availability SLI, SLO and SLA thresholds, error-budget consumption, traffic, errors and latency produced by the demo workload.

![SLO Demo Grafana Dashboard](images/slo-demo-grafana-dashboard.png)

## Verification Commands

```bash
# Check Helm release name
helm list -n monitoring

# Check ServiceMonitor labels
kubectl get servicemonitor -n slo-demo slo-demo --show-labels

# Check Prometheus configuration and selectors
kubectl get prometheus -n monitoring -o yaml

# Check Pods
kubectl get pods -n slo-demo

# Check Service
kubectl get service -n slo-demo

# Access the application locally
kubectl port-forward -n slo-demo service/slo-demo 8080:80

# Test endpoints manually
curl http://localhost:8080/
curl http://localhost:8080/fail
curl http://localhost:8080/metrics
```

## Troubleshooting

* **Image not found:** Ensure you ran `kind load docker-image`. Kind cannot pull images from your local Docker daemon directly without this step.
* **No metrics in Grafana:** 
    * Verify the ServiceMonitor is selected by Prometheus. The `release` label in the ServiceMonitor must match the label selected by the Prometheus resource.
    * Use `kubectl get prometheus -n monitoring -o yaml` to check the `serviceMonitorSelector`.
    * Ensure the application Pods are running and `/metrics` is reachable.
    * Check if the `namespace` variable in Grafana is set to `slo-demo`.
    * Optional: To allow Prometheus to discover all ServiceMonitors regardless of labels, set `prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false` in your Helm values.
* **Zero availability:** If there is no traffic, the availability calculation may show `N/A`. Ensure the load generator is running.

## Cleanup

```bash
kubectl delete -f k8s/load-generator.yaml
kubectl delete -f k8s/servicemonitor.yaml
kubectl delete -f k8s/app.yaml
kind delete cluster --name slo-demo
```
