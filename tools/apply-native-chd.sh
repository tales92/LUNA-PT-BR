#!/usr/bin/env bash
set -euo pipefail

OPL_ROOT="$1"
if [[ -z "$OPL_ROOT" ]]; then
  echo "Usage: apply-native-chd.sh <opl-submodule>" >&2
  exit 2
fi
CHD_REPO="https://github.com/tales92/experiment-native-chd.git"
CHD_REF="refs/heads/experiment/chd-v5-zlib"
CHD_BASE="b3a2199795fe89ba7e2dd7b843354472dff2c3eb"
CHD_EXPECTED="0e3fb918a2a0690553a4a254d7f4d89924ed14af"
REMOTE="luna-native-chd"

test -d "$OPL_ROOT/.git" || test -f "$OPL_ROOT/.git" || {
  echo "OPL submodule is not a Git checkout: $OPL_ROOT" >&2
  exit 2
}

if git -C "$OPL_ROOT" remote get-url "$REMOTE" >/dev/null 2>&1; then
  git -C "$OPL_ROOT" remote set-url "$REMOTE" "$CHD_REPO"
else
  git -C "$OPL_ROOT" remote add "$REMOTE" "$CHD_REPO"
fi

git -C "$OPL_ROOT" fetch --no-tags "$REMOTE" "$CHD_REF"
CHD_HEAD="$(git -C "$OPL_ROOT" rev-parse FETCH_HEAD)"
if [[ "$CHD_HEAD" != "$CHD_EXPECTED" ]]; then
  echo "Unexpected CHD source revision: $CHD_HEAD (expected $CHD_EXPECTED)" >&2
  exit 3
fi

git -C "$OPL_ROOT" cat-file -e "$CHD_BASE^{commit}"
PATCH_FILE="$(mktemp)"
trap 'rm -f "$PATCH_FILE"' EXIT

git -C "$OPL_ROOT" diff --binary --full-index "$CHD_BASE" "$CHD_HEAD" -- \
  modules/isofs modules/iopcore/cdvdman > "$PATCH_FILE"

if [[ ! -s "$PATCH_FILE" ]]; then
  echo "The pinned CHD patch is empty." >&2
  exit 4
fi

git -C "$OPL_ROOT" apply --3way --index "$PATCH_FILE"
# Third-party miniz/bitstream sources retain upstream whitespace; verify conflict
# markers separately rather than rejecting the unchanged vendor source style.
if [[ -n "$(git -C "$OPL_ROOT" ls-files -u)" ]]; then
  echo "Native CHD patch left unresolved index conflicts." >&2
  git -C "$OPL_ROOT" ls-files -u >&2
  exit 6
fi

for path in \
  modules/isofs/chd.c \
  modules/isofs/chd.h \
  modules/isofs/chd/miniz.c \
  modules/iopcore/cdvdman/cdvdman.c; do
  test -s "$OPL_ROOT/$path" || {
    echo "CHD integration is incomplete: $path is missing." >&2
    exit 5
  }
done

grep -q 'chd_read_sector' "$OPL_ROOT/modules/iopcore/cdvdman/cdvdman.c"
echo "Applied native CHD v5/zlib support to the LUNA OPL runtime."
echo "Source: $CHD_HEAD (base $CHD_BASE)"
