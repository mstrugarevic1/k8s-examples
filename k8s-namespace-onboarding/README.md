# Kubernetes Namespace Onboarding

Small example for creating a Kubernetes namespace from one YAML file.

A team fills in a config file, the script checks it, and the script writes the Kubernetes YAML for that namespace. The generated files can be reviewed in Git and then applied manually or by a GitOps tool.

This is an example project, not a complete production platform.

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

owner: payments-team
costCenter: finops-042

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
  storage: "20Gi"
  persistentVolumeClaims: 5
  services: 10
  configmaps: 20
  secrets: 20

network:
  allowDns: true
  allowIngressFromSameNamespace: true
  allowIngressFromNamespaces:
    - ingress-nginx
  allowEgressToNamespaces:
    - observability
  allowExternalEgress: false

rbac:
  readOnlyGroup: payments-readers
  developerGroup: payments-developers
  allowExec: false
  allowPortForward: false

serviceAccount:
  create: true
  name: deployer
```

Supported environments are `development`, `staging`, and `production`.

## What the Main Fields Mean

- `resources` sets default CPU/memory requests and limits for containers in the namespace.
- `quota` sets total namespace limits for CPU, memory, pods, storage, PVCs, Services, ConfigMaps, and Secrets count.
- `network.allowDns` lets pods use Kubernetes DNS.
- `network.allowIngressFromSameNamespace` lets pods in the same namespace talk to each other.
- `network.allowIngressFromNamespaces` allows traffic from listed namespaces.
- `network.allowEgressToNamespaces` allows traffic to listed namespaces.
- `network.allowExternalEgress` allows outbound traffic to any IP. Keep it `false` unless the namespace really needs internet or external service access.
- `rbac.allowExec` and `rbac.allowPortForward` are off by default because they give stronger debugging access.

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

- Roles and RoleBindings are created only inside the namespace.
- No cluster-wide admin permissions are generated.
- RBAC does not use `*` permissions.
- Roles do not allow access to Kubernetes Secrets.
- The generated ServiceAccount does not mount a token by default.
- Network traffic is denied by default.
- DNS access is added only when `network.allowDns` is true.
- Same-namespace traffic is optional.
- Namespace-to-namespace traffic must be listed explicitly.
- Quotas, storage limits, object count limits, and default container limits are generated.

## Limitations

- It does not install Kubernetes or any cluster add-ons.
- It does not create application Deployments, Services, or PodDisruptionBudgets.
- `make validate` is only a basic local check.
- The RBAC rules are simple and may need changes for a real company setup.
