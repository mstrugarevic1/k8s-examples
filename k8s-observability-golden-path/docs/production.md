# Production Reference

The production profile enables VictoriaMetrics cluster mode (`vmstorage` x3 with persistent volumes, `vmselect` x2, `vminsert` x2, replication factor 2), two vmagent replicas, persistent Alertmanager with two replicas, persistent Grafana, production-sized resource requests, and Loki Distributed mode backed by object storage.

Required object storage variables:

```bash
export LOKI_OBJECT_STORE_BUCKET=<bucket>
export LOKI_OBJECT_STORE_REGION=<region>
```

Use workload identity or a Secret managed outside Git for credentials.

vmalert runs as a single replica. For duplicate-free high availability, run a second replica behind deduplication as described in the VictoriaMetrics vmalert documentation.

Live validation (`make test`) supports the kind and local profiles only; the production profile exposes the query API through `vmselect` instead of `vmsingle`.
