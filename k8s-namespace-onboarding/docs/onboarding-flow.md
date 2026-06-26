# Onboarding Flow

1. An application team submits a YAML configuration under `teams/`.
2. CI validates the configuration and runs tests.
3. The generator produces Kubernetes manifests under `generated/<team>-<environment>/`.
4. A platform engineer reviews the pull request, including the generated RBAC, quota, limits, and network policies.
5. The manifests are applied through GitOps or manually with `kubectl`.
6. The team receives namespace-scoped access through the generated RoleBindings.

## Rollback

To roll back an onboarding change, revert the onboarding pull request and remove the generated manifests from the deployment path.

Before deleting a namespace, review persistent resources and data ownership. Do not automatically delete namespaces containing production data. Production cleanup should be a deliberate operational change with backup and retention checks.
