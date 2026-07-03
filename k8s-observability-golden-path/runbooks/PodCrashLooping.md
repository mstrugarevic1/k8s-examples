# PodCrashLooping

## Symptoms
Container repeatedly restarts.

## Impact
The workload may be unavailable.

## Checks
```bash
kubectl -n <namespace> describe pod <pod>
kubectl -n <namespace> logs <pod> -c <container> --previous
```
LogQL: `{namespace="<namespace>",pod="<pod>"} |~ "(?i)error|panic|fatal"`

## Likely causes
Bad config, missing dependency, failed startup, or image bug.

## Mitigation
Fix the failing config or roll back the deployment.

## Verification
PromQL: `rate(kube_pod_container_status_restarts_total{namespace="<namespace>",pod="<pod>"}[15m])`

