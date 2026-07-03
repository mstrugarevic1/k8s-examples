# Kubernetes Observability Golden Path

Reusable Kubernetes monitoring and logging baseline for small local clusters and production-like clusters. The golden path is the working default: pinned charts, Git-provisioned dashboards, actionable alerts, runbooks, logs, Kubernetes Events, and validation commands.

## Stack

- kube-prometheus-stack `61.9.0`: Prometheus, Alertmanager, Grafana, kube-state-metrics, node-exporter
- Loki `6.12.0`
- Fluent Bit `0.47.10`
- Helmfile
- Makefile

## Architecture

The single architecture diagram is maintained in [docs/architecture.md](docs/architecture.md).

## Prerequisites

- Kubernetes context for Kind, Minikube, or another cluster
- `kubectl`
- `helm`
- `helmfile`
- `promtool`
- `ruby`

## Local Quick Start

```bash
git clone <repository>
cd k8s-observability-golden-path

make prerequisites
make install PROFILE=local
make validate
make grafana
```

## Production Configuration

Local uses lightweight Loki single binary mode with short retention. Production uses Loki distributed mode with distributor, ingester, querier, query-frontend, query-scheduler, index-gateway, compactor, and gateway components.

Production requires S3-compatible object storage. Do not put credentials in Git. Provide credentials through workload identity, an external secret, or the secret method required by your Loki deployment.

Required for `make install PROFILE=production`:

```bash
export LOKI_S3_BUCKET=<bucket>
export LOKI_S3_REGION=<region>
export LOKI_S3_ENDPOINT=<endpoint>
make install PROFILE=production
```

Production values also enable persistent Prometheus storage, multiple useful replicas, PDBs where supported by the chart, topology spreading or anti-affinity, resource requests/limits, retention, and query limits.

Alertmanager defaults to a null receiver. For production, copy `environments/production/alertmanager-receiver.example.yaml` to `environments/production/alertmanager-receiver.yaml` and replace the Slack webhook placeholder outside Git.

## Make Targets

- `make prerequisites`: check tools, current Kubernetes context, and Helm repos.
- `make install PROFILE=local`: install the local profile.
- `make install PROFILE=production`: install the production profile.
- `make status`: show installed observability resources.
- `make validate`: render both profiles, check rules with `promtool`, validate dashboards, targets, and Loki queries.
- `make grafana`: port-forward Grafana to <http://localhost:3000>.
- `make test`: deploy fixtures, check metrics, container logs, Kubernetes Events, custom alerts, dashboard queries, and remove fixtures.
- `make uninstall`: remove rules, dashboards, and Helm releases.

## Dashboards

Only these dashboards are provisioned:

- [Cluster Overview](docs/images/cluster-overview.png)
- [Workload Reliability](docs/images/workload-reliability.png)
- [Capacity and Efficiency](docs/images/capacity-and-efficiency.png)
- [Logs and Events](docs/images/logs-and-events.png)
- [Observability Stack Health](docs/images/observability-stack-health.png)

Variables: `cluster`, `namespace`, `workload`, `pod`, `container`.

## Alerts

Only these alerts are installed:

- `NodeNotReady`
- `WorkloadUnavailable`
- `PodCrashLooping`
- `ContainerOOMKilled`
- `PodStuckPending`
- `PersistentVolumeAlmostFull`
- `PrometheusTargetDown`
- `LokiIngestionFailing`
- `LokiDiscardingLogs`
- `FluentBitDroppingLogs`

Each alert has `summary`, `description`, `impact`, `dashboard_url`, and absolute `runbook_url` annotations.

## Testing

Fluent Bit collects container logs and Kubernetes Events. Event labels are limited to `cluster`, `environment`, `source=kubernetes-events`, `namespace`, `reason`, and `type`; event messages are not labels.

`make test` deploys fixtures for CrashLoopBackOff, Pending Pod, failed readiness, OOMKilled, and Kubernetes Warning Events. It verifies Prometheus metrics, Loki container logs, Loki Kubernetes Events, and expected custom alert state before cleanup.

`make validate` performs static validation and live checks against an installed stack. Run it after `make install`.

## Cleanup

```bash
make uninstall
```

## Limitations

- No tracing, Tempo, OpenTelemetry, service mesh metrics, or business metrics.
- The local profile is intentionally small and uses short retention.
- Production S3 credentials are not managed here.
- Screenshots are generated from a Kind demo cluster, not production traffic.
