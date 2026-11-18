#!/usr/bin/env python3
"""Apply narrow LUNA compatibility adaptations after merging official Neutrino."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NEUTRINO = ROOT / "neutrino"


def git_show(spec: str) -> str:
    return subprocess.run(
        ["git", "-C", str(NEUTRINO), "show", spec],
        check=True, text=True, stdout=subprocess.PIPE
    ).stdout


def patch_main() -> None:
    path = NEUTRINO / "ee/loader/src/main.c"
    source = path.read_text(encoding="utf-8")
    old = 'if ((!strcmp(sys.sBSD, "mmce")) || (!strcmp(sys.sBSD, "udpfs")))'
    new = (
        'if ((!strcmp(sys.sBSD, "mmce")) || (!strcmp(sys.sBSD, "udpfs")) ||\n'
        '            (!strcmp(sys.sBSD, "smb")) || (!strcmp(sys.sBSD, "nfs")))'
    )
    if new in source:
        print("Neutrino main.c: SMB/NFS filesystem bypass already present")
        return
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one LUNA filesystem condition in {path}; found {count}"
        )
    path.write_text(source.replace(old, new, 1), encoding="utf-8", newline="\n")
    print("Neutrino main.c: preserved LUNA UDPFS IP override and added SMB/NFS modes")


def merge_readme_sections() -> None:
    path = NEUTRINO / "README.md"
    current = path.read_text(encoding="utf-8")
    if "\n## SMB\n" in current:
        print("Neutrino README: SMB/NFS documentation already present")
        return
    upstream = git_show("HEAD^2:README.md")
    start_marker = "## SMB\n"
    end_marker = "## UDPFS / UDPBD PC Server"
    start = upstream.find(start_marker)
    end = upstream.find(end_marker, start)
    if start < 0 or end < 0:
        raise RuntimeError("Could not locate upstream SMB/NFS documentation section")
    section = upstream[start:end].rstrip()
    insertion = "\n" + section + "\n\n"
    if end_marker not in current:
        raise RuntimeError("Could not locate LUNA README insertion point before UDPFS docs")
    current = current.replace(end_marker, insertion + end_marker, 1)
    path.write_text(current, encoding="utf-8", newline="\n")
    print("Neutrino README: retained LUNA HostFS notes and added official SMB/NFS docs")


def main() -> int:
    if not NEUTRINO.is_dir():
        raise RuntimeError("Neutrino submodule is missing")
    patch_main()
    merge_readme_sections()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"upstream Neutrino adaptation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
