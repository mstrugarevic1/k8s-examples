# Kubernetes Examples

A collection of Kubernetes examples focused on practical platform engineering patterns.

## Purpose

This repository collects small, hands-on Kubernetes examples for learning and validating common platform patterns. The examples are intended for engineers who want practical manifests, policy examples, and observability demos they can run in a test cluster.

It is not a production platform template. Treat the examples as learning material and starting points for your own environment.

> [!NOTE]
> This repository is provided as-is for learning and experimentation, without warranty of any kind. The examples are not fully tested for production use. You are responsible for reviewing, adapting, and validating them before use, and the author is not liable for misuse, damage, data loss, security issues, or other consequences resulting from this material.

## Examples

* **[SLO Demo](./k8s-slo-demo/README.md)**: A demonstration of Service Level Objectives (SLOs) and error budgets using a Flask application, Prometheus, and Grafana.
* **[Gatekeeper Policies](./k8s-gatekeeper-policies/README.md)**: OPA Gatekeeper ConstraintTemplates and Constraints for enforcing cluster-wide rules, with good and bad example manifests.
* **[Namespace Onboarding](./k8s-namespace-onboarding/README.md)**: A small generator that turns one team YAML into namespace-scoped manifests: RBAC, quotas, limits, and NetworkPolicy.
* **[Observability Golden Path](./k8s-observability-golden-path/README.md)**: A Helmfile baseline for Prometheus, Grafana, Loki, Fluent Bit, dashboards, alerts, and runbooks.
