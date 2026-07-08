# FluentBitDroppingRecords

## Meaning
Fluent Bit reports dropped output records.

## User impact
Container logs or Kubernetes Events may be missing from Loki.

## Verification commands
```bash
kubectl -n observability logs -l app.kubernetes.io/name=fluent-bit --tail=100
make metrics
```
PromQL: `rate(fluentbit_output_dropped_records_total[5m])`

## Likely causes
Loki is unavailable, Fluent Bit buffers are full, or records are rejected.

## Mitigation
Restore Loki, reduce noisy logs, or increase bounded buffers after confirming disk capacity.

## Rollback/escalation
Roll back recent logging or Loki changes. Escalate if drops continue after Loki is healthy.
