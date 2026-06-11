# Kubernetes Examples

A collection of Kubernetes examples focused on practical platform engineering patterns.

## Purpose

This repository collects small, hands-on Kubernetes examples for learning and validating common platform patterns. The examples are intended for engineers who want practical manifests, policy examples, and observability demos they can run in a test cluster.

It is not a production platform template. Treat the examples as learning material and starting points for your own environment.

## Examples

* **[SLO Demo](./slo-demo/README.md)**: A practical demonstration of Service Level Objectives (SLOs) using Prometheus and Grafana.
* **[Gatekeeper Policy Examples](./gatekeeper-policy-examples/README.md)**: A set of OPA Gatekeeper policies for enforcing cluster-wide constraints.

## Getting Started

Each directory contains its own README with prerequisites and usage instructions.

Typical usage:

```bash
cd slo-demo
# Follow the README in that example directory.
```

## Technologies Demonstrated

- Kubernetes manifests and workload configuration.
- Prometheus and Grafana for SLO-style observability demos.
- OPA Gatekeeper policies and constraints.
- Practical deployment and validation workflows for test clusters.
