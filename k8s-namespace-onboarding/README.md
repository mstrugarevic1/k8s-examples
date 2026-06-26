# Kubernetes Namespace Onboarding

Reference implementation for Git-based onboarding of application teams into a shared Kubernetes cluster.

The project keeps onboarding small: a team submits one YAML file, the generator validates it, and deterministic Kubernetes manifests are committed for review and GitOps/manual deployment. It is a portfolio/reference project, not a complete production platform.

```text
Team YAML
    |
Configuration validation
    |
Manifest generation
    |
Pull request review
    |
GitOps repository or cluster deployment
```

## Repository Structure

```text
k8s-namespace-onboarding/
├── README.md
├── Makefile
├── requirements.txt
├── teams/
├── generated/
├── templates/
├── scripts/
├── tests/
├── docs/
└── .github/workflows/
```

## Prerequisites

- Python 3.11+
- `kubectl` for optional client-side manifest validation

Install Python dependencies:

```bash
make install
```

## Add a Team

Create a YAML file in `teams/`:

```yaml
team: payments
environment: staging

namespace:
  name: payments-staging

resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"

quota:
  cpu: "4"
  memory: "8Gi"
  pods: 20

network:
  allowDns: true
  allowIngressFromSameNamespace: true

rbac:
  readOnlyGroup: payments-readers
  developerGroup: payments-developers
```

Supported environments are `development`, `staging`, and `production`.

## Generate Manifests

```bash
make generate TEAM=payments-staging
make generate TEAM=catalog-development
```

Generated files are written to `generated/<team>-<environment>/`:

```text
00-namespace.yaml
01-service-account.yaml
02-rbac.yaml
03-resource-quota.yaml
04-limit-range.yaml
05-network-policies.yaml
```

## Test and Validate

```bash
make test
make validate TEAM=payments-staging
```

`make validate` uses `kubectl apply --dry-run=client --validate=false` when `kubectl` is installed and has a current context. If `kubectl` is missing or not configured, it prints a clear skip message.

## Generated Security Controls

- Namespace-scoped `Role` and `RoleBinding` only.
- No `ClusterRole`, `ClusterRoleBinding`, or `cluster-admin`.
- No wildcard RBAC permissions.
- No Secrets access.
- `ServiceAccount` token automount disabled by default.
- Default-deny ingress and egress `NetworkPolicy`.
- DNS egress allowed only when `network.allowDns` is true.
- Optional same-namespace traffic policy.
- `ResourceQuota` and `LimitRange` enforce resource boundaries.

## Limitations

- This project does not install Kubernetes, Argo CD, Flux, monitoring, service mesh, or secret-management infrastructure.
- It does not generate application workload resources or PodDisruptionBudgets.
- Client-side validation is a smoke check, not a substitute for server-side validation in a real test cluster.
- The RBAC model is intentionally small and may need adjustment for your platform conventions.
