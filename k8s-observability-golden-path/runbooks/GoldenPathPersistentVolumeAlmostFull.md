# GoldenPathPersistentVolumeAlmostFull

## Meaning
A PVC is above 85 percent used.

## User impact
Prometheus, Loki, Grafana, or workloads may fail writes when the volume fills.

## Verification commands
```bash
kubectl -n <namespace> get pvc
kubectl -n <namespace> describe pvc <persistentvolumeclaim>
```
PromQL: `golden_path:pvc_usage_ratio`

## Likely causes
Retention too long, insufficient volume size, or unexpected write volume.

## Mitigation
Increase PVC size, reduce retention, or remove safe data according to the owning component docs.

## Rollback/escalation
Rollback retention changes that increased data growth. Escalate before deleting observability data.
