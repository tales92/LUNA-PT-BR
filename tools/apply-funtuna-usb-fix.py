#!/usr/bin/env python3
"""Apply the isolated upstream FunTuna/USB boot-discovery fix to NHDDL.

This reproduces the source change in dnunezx/nhddl-luna commit
3ec0d650cab5b13e1e3264b5a8bae1491b1a902c while keeping it separate from
the PT-BR, OPL-default, and ZSO customizations in this fork.
"""
from pathlib import Path
import sys

OLD_INIT = "    initModules(MODE_ATA | MODE_USB | MODE_MX4SIO);"
NEW_INIT = "    initModules(MODE_ATA | MODE_USB);"

OLD_PROBE = r'''    int fd = 0;
    int attempts = 0;
    for (int i = 0; i < 8; i++) {
      result[4] = '0' + i;
      printf("Resolve root: probing %s\n", result);
      if (probePath(result, 2)) {
        printf("Resolve root: failed to probe\n");
        return result; // No BDM devices were found
      }
      fd = open(result, O_RDONLY);
      if (fd >= 0) {
        printf("Resolve root: found root path\n");
        close(fd);
        return result;
      }
    }'''

NEW_PROBE = r'''    // Prefer the supplied device, then allow for BDM renumbering after reset.
    // A missing file on one volume does not rule out the remaining volumes.
    char originalIndex = argv0[4] >= '0' && argv0[4] <= '9' ? argv0[4] : '0';
    for (int pass = 0; pass < 2; pass++) {
      if (pass) {
        // Loading an unused memory-card adapter can block USB startup.
        // Keep MX4SIO boot support as a separate, clean-driver fallback.
        printf("Resolve root: trying MX4SIO boot fallback\n");
        initStorageModules(MODE_MX4SIO, 1);
      }
      for (int i = 0; i < 10; i++) {
        result[4] = '0' + (originalIndex - '0' + i) % 10;
        printf("Resolve root: probing %s\n", result);
        if (!probePath(result, 2)) {
          printf("Resolve root: found root path\n");
          return result;
        }
      }
    }
    // Keep the original directory available to the normal config fallbacks.
    result[4] = originalIndex;
    printf("Resolve root: boot file not found on any BDM volume\n");'''

def replace_once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"src/main.c: expected one {label} anchor, found {count}; "
            "source was not changed for this replacement"
        )
    return source.replace(old, new, 1)

def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <nhddl-source-directory>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    path = root / "src/main.c"
    if not path.is_file():
        print(f"NHDDL source file not found: {path}", file=sys.stderr)
        return 2

    source = path.read_text(encoding="utf-8")
    source = replace_once(source, OLD_INIT, NEW_INIT, "deferred MX4SIO initialization")
    source = replace_once(source, OLD_PROBE, NEW_PROBE, "BDM USB boot discovery")

    # Refuse to report success unless both parts of the fix are present.
    if NEW_INIT not in source or NEW_PROBE not in source:
        raise RuntimeError("USB boot fix validation failed after patching")
    path.write_text(source, encoding="utf-8")
    print("Applied isolated FunTuna USB boot-discovery fix to nhddl/src/main.c.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"FunTuna USB customization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
