# ContainerOOMKilled

## Symptoms
Container terminated with `OOMKilled`.

## Impact
Requests fail and in-memory state is lost.

## Checks
```bash
kubectl -n <namespace> describe pod <pod>
kubectl -n <namespace> top pod <pod> --containers
```
PromQL: `kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}`

## Likely causes
Memory limit too low, memory leak, or larger workload input.

## Mitigation
Fix memory use or adjust requests and limits.

## Verification
PromQL: `container_memory_working_set_bytes{namespace="<namespace>",pod="<pod>"}`

