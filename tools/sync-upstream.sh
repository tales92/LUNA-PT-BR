#!/usr/bin/env bash
# Synchronize the LUNA root, frontend and official runtime pins for CI builds.
set -Eeuo pipefail

if [[ $# -ne 4 ]]; then
  echo "Usage: $0 LUNA_MAIN_SHA NHDDL_LUNA_SHA NEUTRINO_MASTER_SHA OPL_MASTER_SHA" >&2
  exit 2
fi

luna_sha="$1"
nhddl_sha="$2"
neutrino_sha="$3"
opl_sha="$4"
branch="refresh/luna-official-latest-2026-11-18"

for value in "$luna_sha" "$nhddl_sha" "$neutrino_sha" "$opl_sha"; do
  if [[ ! "$value" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Invalid upstream commit ID: $value" >&2
    exit 2
  fi
done

git config user.name "LUNA Upstream Automation"
git config user.email "luna-upstream-automation@users.noreply.github.com"

echo "::group::Merge the latest official LUNA root"
git fetch --no-tags https://github.com/dnunezx/LUNA.git "$luna_sha"
if git merge-base --is-ancestor "$luna_sha" HEAD; then
  echo "The selected LUNA upstream commit is already included."
else
  git merge --no-edit --no-ff "$luna_sha"
fi
echo "::endgroup::"

python3 - "$nhddl_sha" "$neutrino_sha" "$opl_sha" <<'PY'
import json
import re
import sys
from pathlib import Path

nhddl_sha, neutrino_sha, opl_sha = sys.argv[1:]
for value in (nhddl_sha, neutrino_sha, opl_sha):
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise SystemExit(f"Invalid upstream SHA: {value}")

dependencies_path = Path("tools/dependencies.json")
dependencies = json.loads(dependencies_path.read_text(encoding="utf-8"))
dependencies["nhddl"]["revision"] = nhddl_sha
dependencies_path.write_text(
    json.dumps(dependencies, indent=2) + "\n",
    encoding="utf-8",
    newline="\n",
)

pins_path = Path("tools/upstream-runtime-pins.json")
pins = json.loads(pins_path.read_text(encoding="utf-8"))
pins["neutrino"]["commit"] = neutrino_sha
pins["opl"]["commit"] = opl_sha
pins_path.write_text(
    json.dumps(pins, indent=2) + "\n",
    encoding="utf-8",
    newline="\n",
)
PY

git add tools/dependencies.json tools/upstream-runtime-pins.json
if ! git diff --cached --quiet; then
  git commit -m "chore: refresh official LUNA, Neutrino and OPL pins [skip ci]"
fi

# Persist the exact source pins and any newly merged LUNA root commits on the
# maintained branch so the Release tag always points to a reproducible commit.
git push origin "HEAD:refs/heads/$branch"

echo "LUNA upstream:      $luna_sha"
echo "NHDDL frontend:     $nhddl_sha"
echo "Neutrino upstream:  $neutrino_sha"
echo "OPL upstream:       $opl_sha"
echo "Integration branch: $(git rev-parse HEAD)"
git status --short
