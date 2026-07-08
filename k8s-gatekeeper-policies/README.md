# OPA Gatekeeper Policies

This project contains practical examples of OPA Gatekeeper policies for Kubernetes. The goal is education and demonstration of how to use ConstraintTemplate and Constraint resources to enforce security and operational rules.

## Requirements

- Kubernetes cluster
- OPA Gatekeeper installed on the cluster

### Gatekeeper Installation

If you don't already have Gatekeeper installed, you can install it with the following command:

```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.22.2/deploy/gatekeeper.yaml
```

## Project Structure

- `policies/`: Contains ConstraintTemplate and Constraint definitions.
- `examples/good/`: Example manifests that satisfy the policies.
- `examples/bad/`: Example manifests that violate the policies (used for testing).

## Policies in this Repository

1. **Namespace owner label**: Every Namespace must have an `owner` label.
2. **No privileged containers**: Pods must not use privileged containers.
3. **Approved registries**: Pods may only use images from allowed registries (e.g., `gcr.io`).
4. **Resource requests**: All containers must have CPU and memory requests defined.
5. **No LoadBalancer in dev/staging**: LoadBalancer type services are forbidden in `dev` and `staging` namespaces.
6. **No hostPath volumes**: Pods must not use `hostPath` volumes.

## Usage

### Applying Policies

To apply all policies to your cluster, run:

```bash
make apply
```

### Testing Policies

To test valid manifests (should pass):

```bash
make test-good
```

To test invalid manifests (should be rejected):

```bash
make test-bad
```

### Cleanup

To remove all resources created by these examples:

```bash
make clean
```

## Policy Explanation

Every policy consists of two parts:
1. **ConstraintTemplate**: Defines the Rego logic and policy parameters.
2. **Constraint**: Application of the policy to specific resources (e.g., only to Pods or specific namespaces).
