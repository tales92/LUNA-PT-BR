#!/usr/bin/env bash
# Merge upstream Neutrino and OPL changes into temporary submodule checkouts.
# This runs only in the integration branch's CI workspace. No upstream fork is
# modified. Neutrino overlap hunks keep the LUNA side and receive narrow adapters.
set -Eeuo pipefail

merge_runtime() {
  local path="$1"
  local upstream_url="$2"
  local upstream_branch="$3"
  local label="$4"
  local conflict_strategy="${5:-stop}"
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

  if git -C "$path" merge-base --is-ancestor "$upstream_ref" HEAD; then
    echo "$label is already at or ahead of upstream."
  else
    if ! git -C "$path" merge "${merge_options[@]}" --no-edit --no-ff "$upstream_ref"; then
      local conflicts
      conflicts="$(git -C "$path" diff --name-only --diff-filter=U || true)"
      if [[ -n "$conflicts" ]]; then
        echo "::error::$label has merge conflicts. No automatic side preference was applied."
        echo "Conflicted paths:"
        printf "%s\n" "$conflicts"
      else
        echo "::error::Git could not create the $label merge commit; inspect the error above."
      fi
      echo "Conflict summary:"
      git -C "$path" status --short || true
      git -C "$path" diff --cc || true
      exit 1
    fi
  fi

  echo "Integrated revision:"
  git -C "$path" log -1 --oneline
  git -C "$path" diff --check HEAD^ HEAD 2>/dev/null || true
  echo "::endgroup::"
}

merge_runtime \
  "neutrino" \
  "https://github.com/ps2max32/neutrino.git" \
  "master" \
  "Neutrino" \
  "ours"

# Keep LUNA's UDPFS IP override and its HostFS build notes. Add the official
# SMB/NFS backend condition and documentation without discarding either side.
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

# The official Neutrino SMB and NFS backends add nested source dependencies.
# They only exist after the upstream merge, so initialize them afterwards.
git -C neutrino submodule sync --recursive
git -C neutrino submodule update --init --recursive

# OPL is merged without a preferred side. Any conflicts are reviewed separately.
merge_runtime \
  "opl" \
  "https://github.com/ps2homebrew/Open-PS2-Loader.git" \
  "master" \
  "Open PS2 Loader"

echo "Both upstream runtime merges completed without unresolved conflicts."
echo "Neutrino:"
git -C neutrino log -1 --oneline
echo "OPL:"
git -C opl log -1 --oneline
