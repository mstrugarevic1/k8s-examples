from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate import files_for, generate, validate_config  # noqa: E402


def valid_config() -> dict[str, Any]:
    return {
        "team": "payments",
        "environment": "staging",
        "namespace": {"name": "payments-staging"},
        "owner": "payments-team",
        "costCenter": "finops-042",
        "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"},
        },
        "quota": {
            "cpu": "4",
            "memory": "8Gi",
            "pods": 20,
            "storage": "20Gi",
            "persistentVolumeClaims": 5,
            "services": 10,
            "configmaps": 20,
            "secrets": 20,
        },
        "network": {
            "allowDns": True,
            "allowIngressFromSameNamespace": True,
            "allowIngressFromNamespaces": ["ingress-nginx"],
            "allowEgressToNamespaces": ["observability"],
            "allowExternalEgress": False,
        },
        "rbac": {
            "readOnlyGroup": "payments-readers",
            "developerGroup": "payments-developers",
            "allowExec": False,
            "allowPortForward": False,
        },
        "serviceAccount": {"create": True, "name": "deployer"},
    }


def all_documents(files: dict[str, str]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for content in files.values():
        docs.extend(doc for doc in yaml.safe_load_all(content) if doc)
    return docs


def test_valid_configuration_generates_files(tmp_path: Path) -> None:
    source = ROOT / "teams/payments-staging.yaml"
    output_dir = generate(source, tmp_path)

    assert output_dir.name == "payments-staging"
    assert sorted(path.name for path in output_dir.iterdir()) == [
        "00-namespace.yaml",
        "01-service-account.yaml",
        "02-rbac.yaml",
        "03-resource-quota.yaml",
        "04-limit-range.yaml",
        "05-network-policies.yaml",
    ]


def test_missing_required_field() -> None:
    config = valid_config()
    del config["team"]

    with pytest.raises(ValueError, match="missing or invalid string: team"):
        validate_config(config)


def test_unsupported_environment() -> None:
    config = valid_config()
    config["environment"] = "qa"

    with pytest.raises(ValueError, match="environment must be one of"):
        validate_config(config)


def test_generated_namespace_name() -> None:
    namespace = yaml.safe_load(files_for(validate_config(valid_config()))["00-namespace.yaml"])

    assert namespace["kind"] == "Namespace"
    assert namespace["metadata"]["name"] == "payments-staging"
    assert namespace["metadata"]["labels"]["pod-security.kubernetes.io/enforce"] == "restricted"


def test_no_cluster_roles_or_bindings() -> None:
    kinds = {doc["kind"] for doc in all_documents(files_for(validate_config(valid_config())))}

    assert "ClusterRole" not in kinds
    assert "ClusterRoleBinding" not in kinds


def test_no_wildcard_rbac_permissions() -> None:
    rbac_docs = list(yaml.safe_load_all(files_for(validate_config(valid_config()))["02-rbac.yaml"]))

    for doc in rbac_docs:
        if doc["kind"] != "Role":
            continue
        for rule in doc["rules"]:
            assert "*" not in rule["apiGroups"]
            assert "*" not in rule["resources"]
            assert "*" not in rule["verbs"]
            assert "secrets" not in rule["resources"]


def test_default_deny_network_policy_generation() -> None:
    policies = list(yaml.safe_load_all(files_for(validate_config(valid_config()))["05-network-policies.yaml"]))
    default_deny = next(policy for policy in policies if policy["metadata"]["name"] == "default-deny")

    assert default_deny["spec"]["podSelector"] == {}
    assert default_deny["spec"]["policyTypes"] == ["Ingress", "Egress"]


def test_namespace_to_namespace_network_policies() -> None:
    policies = list(yaml.safe_load_all(files_for(validate_config(valid_config()))["05-network-policies.yaml"]))
    names = {policy["metadata"]["name"] for policy in policies}

    assert "allow-ingress-from-namespaces" in names
    assert "allow-egress-to-namespaces" in names
    assert "allow-external-egress" not in names


def test_quota_includes_storage_and_object_counts() -> None:
    quota = yaml.safe_load(files_for(validate_config(valid_config()))["03-resource-quota.yaml"])
    hard = quota["spec"]["hard"]

    assert hard["requests.storage"] == "20Gi"
    assert hard["persistentvolumeclaims"] == "5"
    assert hard["services"] == "10"
    assert hard["configmaps"] == "20"
    assert hard["secrets"] == "20"


def test_service_account_is_bound_to_developer_role() -> None:
    docs = list(yaml.safe_load_all(files_for(validate_config(valid_config()))["02-rbac.yaml"]))
    binding = next(doc for doc in docs if doc["metadata"]["name"] == "deployer-service-account")

    assert binding["subjects"] == [{"kind": "ServiceAccount", "name": "deployer", "namespace": "payments-staging"}]
    assert binding["roleRef"]["name"] == "developer"


def test_deterministic_output() -> None:
    config = validate_config(valid_config())

    assert files_for(config) == files_for(copy.deepcopy(config))


def test_quota_must_cover_limits() -> None:
    config = valid_config()
    config["quota"]["cpu"] = "100m"

    with pytest.raises(ValueError, match="quota.cpu must be greater"):
        validate_config(config)
