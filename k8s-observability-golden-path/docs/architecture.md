# Architecture

```mermaid
flowchart LR
    Pods[Application Pods] --> FluentBit[Fluent Bit]
    FluentBit --> Loki[Loki]

    Nodes[Kubernetes Nodes] --> NodeExporter[node-exporter]
    KubernetesAPI[Kubernetes API] --> KSM[kube-state-metrics]

    NodeExporter --> Prometheus[Prometheus]
    KSM --> Prometheus
    FluentBit --> Prometheus
    Loki --> Prometheus

    Prometheus --> Grafana[Grafana]
    Loki --> Grafana
    Prometheus --> Alertmanager[Alertmanager]
```

Application logs flow through Fluent Bit into Loki. Kubernetes and node metrics flow into Prometheus through node-exporter, kube-state-metrics, Fluent Bit metrics, and Loki metrics. Grafana reads Prometheus and Loki, and Prometheus sends alerts to Alertmanager.

Dashboard screenshots are stored under [docs/images](images/).
