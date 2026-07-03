# PersistentVolumeAlmostFull

## Symptoms
PVC usage is above 85 percent.

## Impact
Applications may fail writes.

## Checks
```bash
kubectl -n <namespace> describe pvc <persistentvolumeclaim>
kubectl -n <namespace> exec <pod> -- df -h
```
PromQL: `kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes`

## Likely causes
Log growth, data growth, or cleanup failure.

## Mitigation
Delete safe data, increase PVC size, or move data out.

## Verification
PromQL: `kubelet_volume_stats_used_bytes{persistentvolumeclaim="<pvc>"} / kubelet_volume_stats_capacity_bytes{persistentvolumeclaim="<pvc>"}`

