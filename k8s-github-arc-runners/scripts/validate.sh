#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

for command in bash helm jq ruby; do
  command -v "$command" >/dev/null || { echo "missing required tool: $command"; exit 1; }
done

echo "==> YAML and Argo CD manifests"
ruby <<'RUBY'
require "yaml"

paths = Dir.glob("**/*.{yaml,yml}").reject { |path| path.start_with?("charts/arc-observability/templates/") }
documents = paths.to_h { |path| [path, YAML.load_stream(File.read(path)).compact] }

legacy = documents.flat_map do |path, docs|
  docs.each_with_object([]) do |doc, found|
    found << [path, doc["kind"]] if %w[RunnerDeployment HorizontalRunnerAutoscaler].include?(doc["kind"])
  end
end
abort("legacy ARC resources found: #{legacy.inspect}") unless legacy.empty?

argo = documents.select { |path, _| path.start_with?("argocd/") }.values.flatten
abort("expected one AppProject") unless argo.count { |doc| doc["kind"] == "AppProject" } == 1
abort("expected three Applications") unless argo.count { |doc| doc["kind"] == "Application" } == 3
abort("expected one ApplicationSet") unless argo.count { |doc| doc["kind"] == "ApplicationSet" } == 1

argo.select { |doc| %w[Application ApplicationSet].include?(doc["kind"]) }.each do |doc|
  policy = doc.dig("spec", "syncPolicy") || doc.dig("spec", "template", "spec", "syncPolicy")
  abort("#{doc["kind"]} missing automated prune/self-heal") unless policy.dig("automated", "prune") && policy.dig("automated", "selfHeal")
  abort("#{doc["kind"]} missing CreateNamespace") unless policy.fetch("syncOptions", []).include?("CreateNamespace=true")
end

values = documents.fetch("values/demo-repository.yaml").first
abort("runner bounds changed") unless values["minRunners"] == 0 && values["maxRunners"] == 5
abort("secret must be referenced by name") unless values["githubConfigSecret"] == "github-pat"
labels = values.fetch("listenerMetrics").values.flat_map(&:values).flat_map { |metric| metric.fetch("labels", []) }
forbidden = %w[job_name event_name job_workflow_ref job_workflow_name job_workflow_target]
abort("high-cardinality listener labels enabled") unless (labels & forbidden).empty?
RUBY

echo "==> shell syntax"
bash -n scripts/*.sh examples/*.sh

echo "==> local observability chart"
helm lint charts/arc-observability
rendered_chart="$(mktemp "${TMPDIR:-/tmp}/arc-observability.XXXXXX.yaml")"
trap 'rm -f "$rendered_chart"' EXIT
helm template arc-observability charts/arc-observability --namespace observability >"$rendered_chart"
ruby -ryaml -e 'abort("empty chart render") if YAML.load_stream(File.read(ARGV[0])).compact.empty?' "$rendered_chart"

echo "==> dashboard JSON and queries"
jq -e '.uid and .title and (.panels | length == 11)' charts/arc-observability/dashboards/github-arc.json >/dev/null
ruby <<'RUBY'
require "json"
dashboard = JSON.parse(File.read("charts/arc-observability/dashboards/github-arc.json"))
expected = ["Desired runners", "Registered runners", "Busy runners", "Idle runners", "Assigned jobs", "Running jobs", "Completed jobs by result", "Runner utilization", "Job startup duration (p95)", "Job execution duration (p95)", "Scale-set saturation"]
abort("dashboard panels are incomplete") unless expected.sort == dashboard.fetch("panels").map { |panel| panel["title"] }.sort
abort("wrong Grafana datasource UID") unless dashboard.to_s.include?("prometheus")
abort("high-cardinality dashboard labels enabled") if dashboard.to_s.match?(/job_workflow_(ref|name)/)
RUBY

echo "==> credential and architecture guardrails"
if rg -n --hidden -g '!.git/**' -g '!docs/images/**' 'gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----' .; then
  echo "credential-looking content found" >&2
  exit 1
fi
if rg -n --glob '*.yaml' --glob '*.yml' '^kind:[[:space:]]+(RunnerDeployment|HorizontalRunnerAutoscaler)$' .; then
  echo "legacy ARC resource found" >&2
  exit 1
fi

echo "validation passed"
