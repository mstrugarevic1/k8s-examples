# Kubernetes Examples

A collection of Kubernetes examples focused on practical platform engineering patterns.

## Purpose

This repository collects small, hands-on Kubernetes examples for learning and validating common platform patterns. The examples are intended for engineers who want practical manifests, policy examples, and observability demos they can run in a test cluster.

It is not a production platform template. Treat the examples as learning material and starting points for your own environment.

> [!NOTE]
> This repository is provided as-is for learning and experimentation, without warranty of any kind. The examples are not fully tested for production use. You are responsible for reviewing, adapting, and validating them before use, and the author is not liable for misuse, damage, data loss, security issues, or other consequences resulting from this material.

## Examples

* **[SLO Demo](./slo-demo/README.md)**: A practical demonstration of Service Level Objectives (SLOs) using Prometheus and Grafana.
* **[Gatekeeper Policy Examples](./gatekeeper-policy-examples/README.md)**: A set of OPA Gatekeeper policies for enforcing cluster-wide constraints.
* **[Kubernetes Namespace Onboarding](./k8s-namespace-onboarding/README.md)**: A small generator that turns one team YAML into namespace-scoped Kubernetes onboarding manifests.

## Technologies Demonstrated

- Kubernetes manifests and workload configuration.
- Prometheus and Grafana for SLO-style observability demos.
- OPA Gatekeeper policies and constraints.
- Git-based namespace onboarding with generated RBAC, quotas, limits, and NetworkPolicy.
- Practical deployment and validation workflows for test clusters.
