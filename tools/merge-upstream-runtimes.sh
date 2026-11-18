#!/usr/bin/env bash
# Merge upstream Neutrino and OPL changes into temporary submodule checkouts.
# This runs only in the integration branch's CI workspace. No upstream fork is
# modified, and any merge conflict deliberately stops the build for review.
set -Eeuo pipefail

merge_runtime() {
  local path="$1"
  local upstream_url="$2"
  local upstream_branch="$3"
  local label="$4"

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
    if ! git -C "$path" merge --no-edit --no-ff "$upstream_ref"; then
      local conflicts
      conflicts="$(git -C "$path" diff --name-only --diff-filter=U || true)"
      if [[ -n "$conflicts" ]]; then
        echo "::error::$label has merge conflicts. No automatic side preference was applied."
        echo "Conflicted paths:"
        printf "%s\\n" "$conflicts"
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
  "Neutrino"

# The official Neutrino SMB and NFS backends add nested source dependencies.
# They only exist after the upstream merge, so initialize them afterwards.
git -C neutrino submodule sync --recursive
git -C neutrino submodule update --init --recursive

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
