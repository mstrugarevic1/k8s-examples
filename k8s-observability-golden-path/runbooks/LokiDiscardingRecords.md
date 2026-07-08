# LokiDiscardingRecords

## Meaning
Loki is accepting requests but discarding samples.

## User impact
Some logs or Kubernetes Events are not searchable.

## Verification commands
```bash
kubectl -n observability logs -l app.kubernetes.io/name=loki --tail=100
make metrics
```
PromQL: `rate(loki_discarded_samples_total[5m])`

## Likely causes
Rate limits, old timestamps, bad labels, or tenant limits.

## Mitigation
Fix rejecting labels/timestamps, reduce noisy workloads, or tune Loki limits deliberately.

## Rollback/escalation
Roll back recent Fluent Bit parser/label changes. Escalate if storage or tenant limits are unclear.
