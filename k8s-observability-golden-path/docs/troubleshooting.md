# Troubleshooting

Run `make doctor` first. It checks tools, context, Kubernetes API access, nodes, StorageClass, CRDs, and production object-store inputs.

For dashboard query issues, run:

```bash
make validate
make test
```

For Grafana access:

```bash
make credentials
make grafana
```
