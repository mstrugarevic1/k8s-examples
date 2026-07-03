# PrometheusTargetDown

## Symptoms
Prometheus target is down.

## Impact
Metrics and alerts may be missing.

## Checks
```bash
kubectl -n observability get servicemonitor,podmonitor
kubectl -n <namespace> get endpoints,svc,pods
```
PromQL: `up == 0`

## Likely causes
Pod down, service selector mismatch, blocked network, or bad scrape port.

## Mitigation
Restore the target or fix its ServiceMonitor.

## Verification
PromQL: `up{job="<job>",instance="<instance>"}`

