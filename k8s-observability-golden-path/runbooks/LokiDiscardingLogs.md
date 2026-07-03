# LokiDiscardingLogs

## Symptoms
Loki is discarding samples.

## Impact
Some container logs or Kubernetes Events are not searchable.

## Checks
```bash
kubectl -n observability logs -l app.kubernetes.io/name=loki --tail=100
```
PromQL: `rate(loki_discarded_samples_total[5m])`

## Likely causes
Rate limits, invalid timestamps, malformed labels, or retention/tenant limits.

## Mitigation
Reduce log volume, fix invalid records, or tune Loki limits.

## Verification
LogQL: `{source=~"container|kubernetes-events"}`

