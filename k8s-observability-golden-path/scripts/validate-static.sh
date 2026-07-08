#!/usr/bin/env bash
set -euo pipefail

need() { command -v "$1" >/dev/null || { echo "missing required tool: $1"; exit 1; }; }
need helmfile
need python3
need promtool
need jq
need ruby

tmp="${TMPDIR:-/tmp}/golden-path-static"
rm -rf "$tmp"
mkdir -p "$tmp"

echo "==> rendering Helmfile profiles"
for profile in kind local production; do
  env \
    PROFILE="$profile" \
    NAMESPACE=observability \
    CLUSTER_NAME=static-cluster \
    ENVIRONMENT="$profile" \
    LOKI_OBJECT_STORE_BUCKET=placeholder-bucket \
    LOKI_OBJECT_STORE_REGION=us-east-1 \
    LOKI_OBJECT_STORE_ENDPOINT=https://s3.example.invalid \
    helmfile -e "$profile" -f helmfile.yaml.gotmpl template >"$tmp/$profile.yaml"
  test -s "$tmp/$profile.yaml"
done

echo "==> checking VictoriaMetrics rules"
for file in rules/*.yaml; do
  sed -e 's/__NAMESPACE__/observability/g' "$file"
  echo "---"
done >"$tmp/vmrules.yaml"
ruby - "$tmp/vmrules.yaml" "$tmp/rules.yaml" <<'RB'
require "yaml"
docs = YAML.load_stream(File.read(ARGV[0])).compact
groups = docs.flat_map { |doc| doc.fetch("spec").fetch("groups") }
File.write(ARGV[1], {"groups" => groups}.to_yaml)
RB
promtool check rules "$tmp/rules.yaml"

echo "==> checking dashboards"
python3 scripts/validate-dashboards.py --static

echo "==> checking YAML and Python syntax"
python3 -m py_compile scripts/validate-dashboards.py scripts/validate-live.py
ruby - <<'RB'
require "yaml"
Dir.glob("**/*.yaml").each do |path|
  next if path.start_with?(".git/")
  YAML.load_stream(File.read(path))
end
RB

echo "==> checking shell scripts"
if command -v shellcheck >/dev/null; then
  shellcheck scripts/*.sh
else
  echo "shellcheck not found; skipped"
fi

echo "==> checking placeholders, namespaces, and secrets"
python3 - <<'PY'
from pathlib import Path
import re
bad = []
secretish = re.compile(r'(?i)(api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*["\']?[A-Za-z0-9_/\-+=]{16,}')
for path in Path(".").rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.suffix in {".png", ".jpg", ".jpeg"}:
        continue
    text = path.read_text(errors="ignore")
    if "__NAMESPACE__" in text and not (str(path).startswith("rules/") or str(path).startswith("scripts/")):
        bad.append(f"unresolved namespace placeholder in {path}")
    if re.search(r'namespace:\s*observability\b', text) and str(path) not in {"README.md"}:
        bad.append(f"hardcoded observability namespace in {path}")
    if secretish.search(text) and "placeholder" not in text.lower():
        bad.append(f"secret-looking value in {path}")
if bad:
    raise SystemExit("\n".join(bad))
PY

echo "static validation passed"
