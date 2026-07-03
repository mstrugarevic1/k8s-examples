# WorkloadUnavailable

## Symptoms
Available replicas are below desired replicas.

## Impact
Traffic may fail or run with reduced redundancy.

## Checks
```bash
kubectl -n <namespace> describe deploy <deployment>
kubectl -n <namespace> get pods -o wide
```
PromQL: `kube_deployment_status_replicas_available < kube_deployment_spec_replicas`

## Likely causes
Bad image, failing readiness, insufficient capacity, or broken config.

## Mitigation
Roll back, fix readiness/config, or add capacity.

## Verification
```bash
kubectl -n <namespace> rollout status deploy/<deployment>
```

