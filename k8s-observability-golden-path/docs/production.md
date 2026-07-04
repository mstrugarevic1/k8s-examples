# Production Reference

The production profile enables persistent Prometheus and Alertmanager, production-sized resource requests, and Loki Distributed mode backed by object storage.

Required object storage variables:

```bash
export LOKI_OBJECT_STORE_BUCKET=<bucket>
export LOKI_OBJECT_STORE_REGION=<region>
```

Use workload identity or a Secret managed outside Git for credentials.
