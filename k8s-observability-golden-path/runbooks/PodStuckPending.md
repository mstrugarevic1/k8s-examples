# PodStuckPending

## Symptoms
Pod remains Pending.

## Impact
Desired capacity is missing.

## Checks
```bash
kubectl -n <namespace> describe pod <pod>
kubectl get events -A --field-selector reason=FailedScheduling
```
PromQL: `kube_pod_status_phase{phase="Pending"}`

## Likely causes
Insufficient CPU or memory, missing PVC, taints, or affinity rules.

## Mitigation
Free capacity, fix scheduling constraints, or provision storage.

## Verification
```bash
kubectl -n <namespace> get pod <pod>
```

