# NodeNotReady

## Symptoms
Node is `NotReady`.

## Impact
Pods may be evicted or unavailable.

## Checks
```bash
kubectl describe node <node>
kubectl get pods -A --field-selector spec.nodeName=<node>
```
PromQL: `kube_node_status_condition{condition="Ready",status="true"}`

## Likely causes
Kubelet failure, network issue, disk pressure, or node shutdown.

## Mitigation
Cordon the node, drain if needed, then repair or replace it.

## Verification
```bash
kubectl get nodes
```

