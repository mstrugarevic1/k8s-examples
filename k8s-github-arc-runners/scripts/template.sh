#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
source versions.env

controller_chart=oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
runner_chart=oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
render_dir="$(mktemp -d "${TMPDIR:-/tmp}/arc-render.XXXXXX")"
trap 'rm -rf "$render_dir"' EXIT

helm pull "$controller_chart" --version "$ARC_VERSION" --destination "$render_dir"
helm pull "$runner_chart" --version "$ARC_VERSION" --destination "$render_dir"
helm template arc-controller "$render_dir/gha-runner-scale-set-controller-$ARC_VERSION.tgz" --namespace arc-systems -f values/controller.yaml >"$render_dir/controller.yaml"
helm template arc-demo "$render_dir/gha-runner-scale-set-$ARC_VERSION.tgz" --namespace arc-runners-demo -f values/demo-repository.yaml >"$render_dir/runners.yaml"
helm template arc-observability charts/arc-observability --namespace observability >"$render_dir/observability.yaml"

for manifest in "$render_dir"/{controller,runners,observability}.yaml; do
  test -s "$manifest"
  kubeconform -strict -ignore-missing-schemas "$manifest"
done

ruby -ryaml - "$render_dir/controller.yaml" "$render_dir/runners.yaml" "$render_dir/observability.yaml" <<'RUBY'
controller, runners, observability = ARGV.map { |path| YAML.load_stream(File.read(path)).compact }

deployment = controller.find { |doc| doc["kind"] == "Deployment" }
args = deployment.dig("spec", "template", "spec", "containers", 0, "args")
abort("controller manager metrics are not enabled") unless args.include?("--metrics-addr=:8080")
abort("listener metrics endpoint is not enabled") unless args.include?("--listener-metrics-addr=:8080") && args.include?("--listener-metrics-endpoint=/metrics")

abort("runner chart rendered a credential Secret") if runners.any? { |doc| doc["kind"] == "Secret" }
scale_set = runners.find { |doc| doc["kind"] == "AutoscalingRunnerSet" }
abort("missing AutoscalingRunnerSet") unless scale_set
abort("runner bounds changed") unless scale_set.dig("spec", "minRunners") == 0 && scale_set.dig("spec", "maxRunners") == 5
abort("pre-existing Secret reference missing") unless scale_set.dig("spec", "githubConfigSecret") == "github-pat"
abort("listener metrics missing") unless scale_set.dig("spec", "listenerMetrics", "gauges", "gha_desired_runners")

abort("expected two ServiceMonitors") unless observability.count { |doc| doc["kind"] == "ServiceMonitor" } == 2
abort("expected Grafana dashboard ConfigMap") unless observability.any? { |doc| doc["kind"] == "ConfigMap" && doc.dig("metadata", "labels", "grafana_dashboard") == "1" }
RUBY

echo "controller, runner scale set, and observability charts rendered successfully"
