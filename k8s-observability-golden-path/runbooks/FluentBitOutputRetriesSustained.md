# FluentBitOutputRetriesSustained

## Meaning
Fluent Bit is retrying Loki output delivery.

## User impact
Logs may arrive late; prolonged retries can become drops.

## Verification commands
```bash
kubectl -n observability logs -l app.kubernetes.io/name=fluent-bit --tail=100
kubectl -n observability get pods -l app.kubernetes.io/name=loki
```
PromQL: `rate(fluentbit_output_retries_total[5m])`

## Likely causes
Loki throttling, network errors, or slow object storage.

## Mitigation
Check Loki readiness, request errors, and ingestion limits. Reduce log volume if Loki is saturated.

## Rollback/escalation
Roll back recent Loki, Fluent Bit, or network changes. Escalate if retries persist with healthy Loki.
