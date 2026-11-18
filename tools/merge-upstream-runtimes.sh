#!/usr/bin/env bash
# Merge reviewed upstream Neutrino and OPL commits into temporary submodule checkouts.
# This runs only in CI; the upstream repositories are never modified.
set -Eeuo pipefail

merge_runtime() {
  local path="$1"
  local upstream_url="$2"
  local upstream_branch="$3"
  local label="$4"
  local expected_sha="$5"
  local conflict_strategy="${6:-stop}"
  local -a merge_options=()
  if [[ "$conflict_strategy" == "ours" ]]; then
    merge_options=(-X ours)
  fi

  echo "::group::Fetch and merge $label"
  echo "Local revision:"
  git -C "$path" log -1 --oneline

  git -C "$path" config user.name "LUNA Runtime Integration CI"
  git -C "$path" config user.email "luna-runtime-integration@users.noreply.github.com"
  git -C "$path" fetch --no-tags "$upstream_url" "$upstream_branch"
  local upstream_ref="FETCH_HEAD"
  local fetched_sha
  fetched_sha="$(git -C "$path" rev-parse "$upstream_ref")"
  if [[ "$fetched_sha" != "$expected_sha" ]]; then
    echo "::error::$label upstream moved: expected $expected_sha, fetched $fetched_sha. Review tools/upstream-runtime-pins.json before updating."
    exit 1
  fi

  if git -C "$path" merge-base --is-ancestor "$upstream_ref" HEAD; then
    echo "$label is already at or ahead of upstream."
  else
    if ! git -C "$path" merge "${merge_options[@]}" --no-edit --no-ff "$upstream_ref"; then
      local conflicts
      conflicts="$(git -C "$path" diff --name-only --diff-filter=U || true)"
      if [[ -n "$conflicts" ]]; then
        echo "::error::$label has unresolved merge conflicts. No automatic side preference was applied."
        printf "%s\n" "$conflicts"
      else
        echo "::error::Git could not create the $label merge commit; inspect the error above."
      fi
      git -C "$path" status --short || true
      git -C "$path" diff --cc || true
      exit 1
    fi
  fi

  echo "Integrated revision:"
  git -C "$path" log -1 --oneline
  echo "::endgroup::"
}

merge_runtime \
  "neutrino" \
  "https://github.com/ps2max32/neutrino.git" \
  "master" \
  "Neutrino" \
  "1310a9af7c7395381042f49dd77c4e002515d0f7" \
  "ours"

# Preserve LUNA's UDPFS IP override and HostFS notes; add the upstream SMB/NFS
# backend condition and docs without discarding either side's behavior.
python3 - <<'PY'
from pathlib import Path
import subprocess

root = Path("neutrino")
main_path = root / "ee/loader/src/main.c"
main = main_path.read_text(encoding="utf-8")
old = 'if ((!strcmp(sys.sBSD, "mmce")) || (!strcmp(sys.sBSD, "udpfs")))'
new = (
    'if ((!strcmp(sys.sBSD, "mmce")) || (!strcmp(sys.sBSD, "udpfs")) ||\n'
    '            (!strcmp(sys.sBSD, "smb")) || (!strcmp(sys.sBSD, "nfs")))'
)
if new not in main:
    if main.count(old) != 1:
        raise SystemExit("Could not safely extend Neutrino's filesystem-free backend condition")
    main_path.write_text(main.replace(old, new, 1), encoding="utf-8", newline="\n")

readme_path = root / "README.md"
readme = readme_path.read_text(encoding="utf-8")
marker = "## UDPFS / UDPBD PC Server"
if "\n## SMB\n" not in readme:
    upstream = subprocess.run(
        ["git", "-C", str(root), "show", "HEAD^2:README.md"],
        check=True, text=True, stdout=subprocess.PIPE
    ).stdout
    start = upstream.find("## SMB\n")
    end = upstream.find(marker, start)
    if start < 0 or end < 0 or marker not in readme:
        raise SystemExit("Could not safely merge upstream SMB/NFS documentation")
    readme = readme.replace(marker, "\n" + upstream[start:end].rstrip() + "\n\n" + marker, 1)
    readme_path.write_text(readme, encoding="utf-8", newline="\n")
print("Applied LUNA-preserving Neutrino SMB/NFS adaptations.")
PY

# The official Neutrino SMB/NFS backends have nested source dependencies.
git -C neutrino submodule sync --recursive
git -C neutrino submodule update --init --recursive

# OPL is merged without a preferred side. Any conflicts stop CI for review.
merge_runtime \
  "opl" \
  "https://github.com/ps2homebrew/Open-PS2-Loader.git" \
  "master" \
  "Open PS2 Loader" \
  "b3a2199795fe89ba7e2dd7b843354472dff2c3eb"

echo "Both pinned upstream runtime merges completed."
echo "Neutrino:"
git -C neutrino log -1 --oneline
echo "OPL:"
git -C opl log -1 --oneline
