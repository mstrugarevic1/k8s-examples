# Kubernetes Observability Golden Path

Reusable Kubernetes monitoring and logging baseline for small local clusters and production-like clusters.

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
- Optional: `promtool` for deeper rule validation

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

Production uses Loki distributed mode and S3-compatible object storage. Do not put credentials in Git. Provide credentials through your cluster identity mechanism or the secret method required by your Loki deployment.

Required for `make install PROFILE=production`:

```bash
export LOKI_S3_BUCKET=<bucket>
export LOKI_S3_REGION=<region>
export LOKI_S3_ENDPOINT=<endpoint>
make install PROFILE=production
```

Production values also enable persistent Prometheus storage, multiple useful replicas, PDBs where supported by the chart, anti-affinity, and resource requests/limits.

## Make Targets

- `make prerequisites`: check tools, current Kubernetes context, and Helm repos.
- `make install PROFILE=local`: install the local profile.
- `make install PROFILE=production`: install the production profile.
- `make status`: show installed observability resources.
- `make validate`: render Helmfile, check rules, dashboards, targets, and Loki queries.
- `make grafana`: port-forward Grafana to <http://localhost:3000>.
- `make test`: deploy fixtures, check metrics/log access, and remove fixtures.
- `make uninstall`: remove rules, dashboards, and Helm releases.

## Dashboards

Only these dashboards are provisioned:

- Cluster Health
- Workload Reliability
- Capacity
- Logs
- Stack Health

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
- `FluentBitDroppingLogs`

Each alert has `summary`, `description`, `impact`, and `runbook_url` annotations.

## Testing

`make test` deploys fixtures for CrashLoopBackOff, Pending Pod, failed readiness, and excessive memory use. It checks that Prometheus is queryable and that fixture logs are visible through Kubernetes logs before cleanup.

`make validate` performs static validation and live checks against an installed stack. Run it after `make install`.

## Cleanup

```bash
make uninstall
```

## Limitations

- No tracing, Tempo, OpenTelemetry, service mesh metrics, or business metrics.
- The local profile is intentionally small and uses short retention.
- Production S3 credentials are not managed here.

