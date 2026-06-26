# Architecture

This project stores namespace onboarding configuration in Git because Git gives platform teams review history, ownership, rollback, and a familiar collaboration workflow. A team can propose a small YAML file, and reviewers can see exactly what namespace, quota, network, and RBAC settings will be created.

Generated output is committed on purpose. The generated Kubernetes manifests are the operational contract that will be applied to a cluster or consumed by GitOps. Keeping generated output in the repository makes pull requests reviewable by engineers who do not want to run the generator locally. It also lets CI detect when a configuration change was made without regenerating manifests.

Permissions are namespace-scoped because onboarding a team should not grant cluster-wide access. The generator creates only `Role` and `RoleBinding` resources inside the target namespace. It does not create `ClusterRole`, `ClusterRoleBinding`, or `cluster-admin` style permissions. Developer access is limited to common application resources, and Secrets are intentionally excluded.

Default-deny networking is used because a new namespace should start closed. The generated policies deny ingress and egress by default. DNS egress is added explicitly when requested, and same-namespace traffic can be enabled as a small, clear exception. Broader ingress or egress rules should be reviewed as application-specific changes.

Argo CD or Flux could be added later by pointing a GitOps controller at the `generated/` directory or by copying these manifests into an existing GitOps repository. This project does not install or configure a GitOps controller. That keeps the example focused on namespace onboarding instead of cluster platform installation.

The first version intentionally avoids a Kubernetes operator. An operator would add a custom API, controller lifecycle, permissions, reconciliation behavior, and operational burden. For this use case, a small generator plus Git review is easier to understand, easier to audit, and enough to demonstrate the onboarding pattern.
