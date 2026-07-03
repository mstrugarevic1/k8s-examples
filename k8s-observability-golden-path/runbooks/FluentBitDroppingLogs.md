# FluentBitDroppingLogs

## Symptoms
Fluent Bit is dropping output records.

## Impact
Application logs may be missing from Loki.

## Checks
```bash
kubectl -n observability logs -l app.kubernetes.io/name=fluent-bit --tail=100
```
PromQL: `rate(fluentbit_output_dropped_records_total[5m])`

## Likely causes
Loki unreachable, retry queue full, malformed records, or network failures.

## Mitigation
Restore Loki, reduce log volume, or increase Fluent Bit buffers.

## Verification
LogQL: `{namespace="<namespace>",pod="<pod>"}`

