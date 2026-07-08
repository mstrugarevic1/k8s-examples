# Architecture

The repository keeps orchestration in Helmfile and user workflow in Make.

```text
Makefile -> scripts/resolve-config.sh -> helmfile.yaml.gotmpl
                                  |-> Grafana dashboard ConfigMaps
                                  |-> VMRule resources

kube-state-metrics/node-exporter/kubelet -> vmagent -> VictoriaMetrics
Fluent Bit container logs ----------------> Loki
Fluent Bit Kubernetes Events -------------> Loki
Grafana ----------------------------------> VictoriaMetrics + Loki
vmalert (rules) --------------------------> VictoriaMetrics + Alertmanager
```

Helmfile installs four releases in dependency order: `prometheus-operator-crds` (ServiceMonitor and PrometheusRule CRDs), `victoria-metrics-k8s-stack`, then Loki and Fluent Bit. The Loki and Fluent Bit charts create ServiceMonitors, which the VictoriaMetrics operator converts to VMServiceScrapes. The CRD release must exist first, otherwise the charts silently skip ServiceMonitor creation.

vmagent scrapes all targets and attaches `cluster` and `environment` external labels. vmalert evaluates the repository VMRules and the stack default rules, writes results back to VictoriaMetrics, and notifies Alertmanager.

The stack default rules (kube-prometheus rule groups, including the `namespace_workload_pod:kube_pod_owner:relabel` recording rule the dashboards depend on) are applied by the chart sync-job, which downloads them from upstream GitHub at install time. Installation therefore needs outbound internet access.

Single-cluster dashboards use namespace/workload variables and repository recording rules. They do not filter raw kube-state-metrics, kubelet, node-exporter, or cAdvisor metrics by `cluster`.
