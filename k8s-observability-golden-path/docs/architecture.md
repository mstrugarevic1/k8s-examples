# Architecture

The repository keeps orchestration in Helmfile and user workflow in Make.

```text
Makefile -> scripts/resolve-config.sh -> helmfile.yaml.gotmpl
                                  |-> Grafana dashboard ConfigMaps
                                  |-> PrometheusRule resources

kube-state-metrics/node-exporter/kubelet -> Prometheus
Fluent Bit container logs ----------------> Loki
Fluent Bit Kubernetes Events -------------> Loki
Grafana ----------------------------------> Prometheus + Loki
Prometheus -------------------------------> Alertmanager
```

Single-cluster Prometheus dashboards use namespace/workload variables and repository recording rules. They do not filter raw kube-state-metrics, kubelet, node-exporter, or cAdvisor metrics by `cluster`.
