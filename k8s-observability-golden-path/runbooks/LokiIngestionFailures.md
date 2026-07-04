# LokiIngestionFailures

## Meaning
Loki push endpoints are returning server errors.

## User impact
Fluent Bit retries or drops logs, leaving gaps in Grafana.

## Verification commands
```bash
kubectl -n observability get pods -l app.kubernetes.io/name=loki
kubectl -n observability logs -l app.kubernetes.io/name=loki --tail=100
```
PromQL: `rate(loki_request_duration_seconds_count{route=~".*push.*",status_code=~"5.."}[5m])`

## Likely causes
Object storage failures, bad Loki config, unavailable ingesters, or disk pressure.

## Mitigation
Restore storage access, check ingester readiness, and roll back broken Loki values.

## Rollback/escalation
Roll back the Loki release if failures started after an upgrade. Escalate to the storage owner for object-store errors.
