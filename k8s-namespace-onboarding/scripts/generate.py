#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml


ALLOWED_ENVIRONMENTS = {"development", "staging", "production"}
DNS_LABEL = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
CPU = re.compile(r"^([0-9]+)(m?)$")
MEMORY = re.compile(r"^([0-9]+)(Ki|Mi|Gi|Ti)?$")
APP_RESOURCES = ["pods", "pods/log", "services", "configmaps"]
APP_RESOURCES_APPS = ["deployments", "replicasets"]
WRITE_VERBS = ["get", "list", "watch", "create", "update", "patch", "delete"]
READ_VERBS = ["get", "list", "watch"]
COUNT_DEFAULTS = {
    "services": 10,
    "configmaps": 20,
    "secrets": 20,
    "persistentVolumeClaims": 5,
}


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def load_config(path: Path) -> dict[str, Any]:
    with path.open() as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError("configuration must be a YAML map")
    return data


def require_map(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"missing or invalid map: {key}")
    return value


def require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid string: {key}")
    return value.strip()


def require_bool(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"missing or invalid boolean: {key}")
    return value


def optional_bool(data: dict[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"invalid boolean: {key}")
    return value


def require_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"missing or invalid positive integer: {key}")
    return value


def optional_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"invalid positive integer: {key}")
    return value


def optional_string(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid string: {key}")
    return value.strip()


def optional_string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"invalid string list: {key}")
    return [item.strip() for item in value]


def require_dns_label(value: str, field: str) -> None:
    if len(value) > 63 or not DNS_LABEL.match(value):
        raise ValueError(f"{field} must be a valid Kubernetes DNS label")


def cpu_millicores(value: str, field: str) -> int:
    match = CPU.match(value)
    if not match:
        raise ValueError(f"{field} must be a CPU quantity like 100m or 4")
    amount = int(match.group(1))
    return amount if match.group(2) == "m" else amount * 1000


def memory_bytes(value: str, field: str) -> int:
    match = MEMORY.match(value)
    if not match:
        raise ValueError(f"{field} must be a memory quantity like 128Mi or 8Gi")
    amount = int(match.group(1))
    unit = match.group(2) or ""
    multiplier = {"": 1, "Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4}[unit]
    return amount * multiplier


def validated_namespaces(values: list[str], field: str) -> list[str]:
    for value in values:
        require_dns_label(value, field)
    return values


def validate_config(raw: dict[str, Any]) -> dict[str, Any]:
    team = require_string(raw, "team")
    environment = require_string(raw, "environment")
    namespace = require_string(require_map(raw, "namespace"), "name")
    owner = optional_string(raw, "owner", team)
    cost_center = optional_string(raw, "costCenter", "unknown")
    resources = require_map(raw, "resources")
    requests = require_map(resources, "requests")
    limits = require_map(resources, "limits")
    quota = require_map(raw, "quota")
    network = require_map(raw, "network")
    rbac = require_map(raw, "rbac")

    if environment not in ALLOWED_ENVIRONMENTS:
        raise ValueError("environment must be one of: development, staging, production")
    for field, value in {"team": team, "namespace.name": namespace}.items():
        require_dns_label(value, field)

    request_cpu = require_string(requests, "cpu")
    request_memory = require_string(requests, "memory")
    limit_cpu = require_string(limits, "cpu")
    limit_memory = require_string(limits, "memory")
    quota_cpu = require_string(quota, "cpu")
    quota_memory = require_string(quota, "memory")
    quota_pods = require_int(quota, "pods")
    quota_storage = optional_string(quota, "storage", "10Gi")

    cpu_millicores(request_cpu, "resources.requests.cpu")
    memory_bytes(request_memory, "resources.requests.memory")
    limit_cpu_value = cpu_millicores(limit_cpu, "resources.limits.cpu")
    limit_memory_value = memory_bytes(limit_memory, "resources.limits.memory")
    quota_cpu_value = cpu_millicores(quota_cpu, "quota.cpu")
    quota_memory_value = memory_bytes(quota_memory, "quota.memory")
    memory_bytes(quota_storage, "quota.storage")
    if quota_cpu_value < limit_cpu_value:
        raise ValueError("quota.cpu must be greater than or equal to resources.limits.cpu")
    if quota_memory_value < limit_memory_value:
        raise ValueError("quota.memory must be greater than or equal to resources.limits.memory")

    service_account = raw.get("serviceAccount", {})
    if not isinstance(service_account, dict):
        raise ValueError("missing or invalid map: serviceAccount")
    service_account_create = optional_bool(service_account, "create", True)
    service_account_name = optional_string(service_account, "name", "deployer")
    require_dns_label(service_account_name, "serviceAccount.name")

    ingress_namespaces = validated_namespaces(
        optional_string_list(network, "allowIngressFromNamespaces"), "network.allowIngressFromNamespaces"
    )
    egress_namespaces = validated_namespaces(
        optional_string_list(network, "allowEgressToNamespaces"), "network.allowEgressToNamespaces"
    )

    return {
        "team": team,
        "environment": environment,
        "bundle": f"{team}-{environment}",
        "namespace": namespace,
        "owner": owner,
        "costCenter": cost_center,
        "resources": {
            "requests": {"cpu": request_cpu, "memory": request_memory},
            "limits": {"cpu": limit_cpu, "memory": limit_memory},
        },
        "quota": {
            "cpu": quota_cpu,
            "memory": quota_memory,
            "pods": quota_pods,
            "storage": quota_storage,
            **{key: optional_int(quota, key, default) for key, default in COUNT_DEFAULTS.items()},
        },
        "network": {
            "allowDns": require_bool(network, "allowDns"),
            "allowIngressFromSameNamespace": require_bool(network, "allowIngressFromSameNamespace"),
            "allowIngressFromNamespaces": ingress_namespaces,
            "allowEgressToNamespaces": egress_namespaces,
            "allowExternalEgress": optional_bool(network, "allowExternalEgress", False),
        },
        "rbac": {
            "readOnlyGroup": require_string(rbac, "readOnlyGroup"),
            "developerGroup": require_string(rbac, "developerGroup"),
            "allowExec": optional_bool(rbac, "allowExec", False),
            "allowPortForward": optional_bool(rbac, "allowPortForward", False),
        },
        "serviceAccount": {
            "create": service_account_create,
            "name": service_account_name,
        },
    }


def dump(resource: Any) -> str:
    return yaml.dump_all(
        resource if isinstance(resource, list) else [resource],
        Dumper=NoAliasDumper,
        explicit_start=True,
        sort_keys=False,
    )


def metadata(config: dict[str, Any], name: str | None = None) -> dict[str, Any]:
    labels = {
        "app.kubernetes.io/managed-by": "k8s-namespace-onboarding",
        "platform.example.com/team": config["team"],
        "platform.example.com/environment": config["environment"],
        "platform.example.com/owner": config["owner"],
        "platform.example.com/cost-center": config["costCenter"],
    }
    data: dict[str, Any] = {"name": name or config["namespace"], "labels": labels}
    if name:
        data["namespace"] = config["namespace"]
    return data


def namespace(config: dict[str, Any]) -> dict[str, Any]:
    data = metadata(config)
    data["labels"].update(
        {
            "pod-security.kubernetes.io/enforce": "restricted",
            "pod-security.kubernetes.io/audit": "restricted",
            "pod-security.kubernetes.io/warn": "restricted",
        }
    )
    return {"apiVersion": "v1", "kind": "Namespace", "metadata": data}


def service_account(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": metadata(config, config["serviceAccount"]["name"]),
        "automountServiceAccountToken": False,
    }


def role(name: str, config: dict[str, Any], verbs: list[str], include_debug_access: bool = False) -> dict[str, Any]:
    core_resources = [*APP_RESOURCES]
    if include_debug_access and config["rbac"]["allowExec"]:
        core_resources.append("pods/exec")
    if include_debug_access and config["rbac"]["allowPortForward"]:
        core_resources.append("pods/portforward")
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "Role",
        "metadata": metadata(config, name),
        "rules": [
            {"apiGroups": [""], "resources": core_resources, "verbs": verbs},
            {"apiGroups": ["apps"], "resources": APP_RESOURCES_APPS, "verbs": verbs},
        ],
    }


def role_binding(name: str, group: str, role_name: str, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": metadata(config, name),
        "subjects": [{"kind": "Group", "name": group, "apiGroup": "rbac.authorization.k8s.io"}],
        "roleRef": {
            "kind": "Role",
            "name": role_name,
            "apiGroup": "rbac.authorization.k8s.io",
        },
    }


def rbac(config: dict[str, Any]) -> list[dict[str, Any]]:
    resources = [
        role("read-only", config, READ_VERBS),
        role("developer", config, WRITE_VERBS, include_debug_access=True),
        role_binding("read-only", config["rbac"]["readOnlyGroup"], "read-only", config),
        role_binding("developer", config["rbac"]["developerGroup"], "developer", config),
    ]
    if config["serviceAccount"]["create"]:
        resources.append(role_binding("deployer-service-account", config["serviceAccount"]["name"], "developer", config))
        resources[-1]["subjects"] = [{"kind": "ServiceAccount", "name": config["serviceAccount"]["name"], "namespace": config["namespace"]}]
    return resources


def resource_quota(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "ResourceQuota",
        "metadata": metadata(config, "namespace-quota"),
        "spec": {
            "hard": {
                "requests.cpu": config["quota"]["cpu"],
                "requests.memory": config["quota"]["memory"],
                "limits.cpu": config["quota"]["cpu"],
                "limits.memory": config["quota"]["memory"],
                "pods": str(config["quota"]["pods"]),
                "requests.storage": config["quota"]["storage"],
                "persistentvolumeclaims": str(config["quota"]["persistentVolumeClaims"]),
                "services": str(config["quota"]["services"]),
                "configmaps": str(config["quota"]["configmaps"]),
                "secrets": str(config["quota"]["secrets"]),
            }
        },
    }


def limit_range(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "LimitRange",
        "metadata": metadata(config, "container-defaults"),
        "spec": {
            "limits": [
                {
                    "type": "Container",
                    "defaultRequest": config["resources"]["requests"],
                    "default": config["resources"]["limits"],
                }
            ]
        },
    }


def network_policies(config: dict[str, Any]) -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = [
        {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": metadata(config, "default-deny"),
            "spec": {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]},
        }
    ]
    if config["network"]["allowDns"]:
        policies.append(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": metadata(config, "allow-dns"),
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Egress"],
                    "egress": [
                        {
                            "to": [
                                {
                                    "namespaceSelector": {
                                        "matchLabels": {"kubernetes.io/metadata.name": "kube-system"}
                                    },
                                    "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
                                }
                            ],
                            "ports": [{"protocol": "UDP", "port": 53}, {"protocol": "TCP", "port": 53}],
                        }
                    ],
                },
            }
        )
    if config["network"]["allowIngressFromSameNamespace"]:
        policies.append(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": metadata(config, "allow-same-namespace"),
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Ingress", "Egress"],
                    "ingress": [{"from": [{"podSelector": {}}]}],
                    "egress": [{"to": [{"podSelector": {}}]}],
                },
            }
        )
    if config["network"]["allowIngressFromNamespaces"]:
        policies.append(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": metadata(config, "allow-ingress-from-namespaces"),
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Ingress"],
                    "ingress": [{"from": namespace_peers(config["network"]["allowIngressFromNamespaces"])}],
                },
            }
        )
    if config["network"]["allowEgressToNamespaces"]:
        policies.append(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": metadata(config, "allow-egress-to-namespaces"),
                "spec": {
                    "podSelector": {},
                    "policyTypes": ["Egress"],
                    "egress": [{"to": namespace_peers(config["network"]["allowEgressToNamespaces"])}],
                },
            }
        )
    if config["network"]["allowExternalEgress"]:
        policies.append(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": metadata(config, "allow-external-egress"),
                "spec": {"podSelector": {}, "policyTypes": ["Egress"], "egress": [{"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}]}]},
            }
        )
    return policies


def namespace_peers(namespaces: list[str]) -> list[dict[str, Any]]:
    return [
        {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": namespace}}}
        for namespace in namespaces
    ]


def files_for(config: dict[str, Any]) -> dict[str, str]:
    files = {
        "00-namespace.yaml": dump(namespace(config)),
        "02-rbac.yaml": dump(rbac(config)),
        "03-resource-quota.yaml": dump(resource_quota(config)),
        "04-limit-range.yaml": dump(limit_range(config)),
        "05-network-policies.yaml": dump(network_policies(config)),
    }
    if config["serviceAccount"]["create"]:
        files["01-service-account.yaml"] = dump(service_account(config))
    return dict(sorted(files.items()))


def generate(config_path: Path, output_root: Path = Path("generated")) -> Path:
    config = validate_config(load_config(config_path))
    output_dir = output_root / config["bundle"]
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    for name, content in files_for(config).items():
        (output_dir / name).write_text(content)
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--out", type=Path, default=Path("generated"))
    args = parser.parse_args()
    try:
        print(generate(args.config, args.out))
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
