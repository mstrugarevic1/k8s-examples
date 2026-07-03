# LokiIngestionFailing

## Symptoms
Loki is discarding log samples.

## Impact
Some logs are not searchable.

## Checks
```bash
kubectl -n observability logs -l app.kubernetes.io/name=loki --tail=100
```
PromQL: `rate(loki_discarded_samples_total[5m])`

## Likely causes
Rate limits, bad timestamps, storage errors, or schema/storage config issues.

## Mitigation
Fix storage access, reduce noisy logs, or tune Loki limits.

## Verification
LogQL: `{namespace="observability"}`

