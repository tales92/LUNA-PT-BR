#!/usr/bin/env python3
"""Apply the pinned native CHD reader to LUNA's OPL launch and ISO scanning paths."""
from pathlib import Path
import shutil
import sys

CHD_FILES = (
    "chd.c",
    "chd.h",
    "chdconfig.h",
    "chd_bitstream.c",
    "chd_bitstream.h",
    "chd_huffman.c",
    "chd_huffman.h",
    "chd/miniz.c",
    "chd/miniz.h",
)


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"{path}: expected one patch anchor, found {count}; "
            "source was not changed for this replacement"
        )
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def copy_chd_sources(opl_root: Path, nhddl_root: Path) -> None:
    source_root = opl_root / "modules/isofs"
    target_root = nhddl_root / "src/devices"
    for relative in CHD_FILES:
        source = source_root / relative
        target = target_root / relative
        if not source.is_file():
            raise RuntimeError(f"Pinned CHD source is missing: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def patch_nhddl(nhddl_root: Path) -> None:
    iso = nhddl_root / "src/devices/iso.c"
    replace_once(
        iso,
        '      int isZso = fileext && !strcasecmp(fileext, ".zso");\n'
        '      int isIso = fileext && !strcasecmp(fileext, ".iso");\n'
        '      if (isVcd || isPlaylist || isIso || isZso) {',
        '      int isZso = fileext && !strcasecmp(fileext, ".zso");\n'
        '      int isChd = fileext && !strcasecmp(fileext, ".chd");\n'
        '      int isIso = fileext && !strcasecmp(fileext, ".iso");\n'
        '      if (isVcd || isPlaylist || isIso || isZso || isChd) {',
    )

    title_id = nhddl_root / "src/devices/title_id.c"
    replace_once(
        title_id,
        '#include "devices/title_id.h"\n',
        '#include "devices/title_id.h"\n#include "chd.h"\n',
    )
    callbacks = r'''
/* LUNA native CHD metadata reader callbacks (EE-side). */
static int chdTitleFd = -1;

void *chd_alloc(u32 size) {
  return malloc((size_t)size);
}

void chd_free(void *ptr) {
  free(ptr);
}

int chd_read_raw_data(u8 *addr, u32 size, u32 offset) {
  if (chdTitleFd < 0 || offset > INT32_MAX ||
      lseek64(chdTitleFd, (int64_t)offset, SEEK_SET) < 0 ||
      readExact(chdTitleFd, addr, size))
    return -1;
  return (int)size;
}
'''
    replace_once(
        title_id,
        "static int validRecord(const unsigned char *record, size_t available) {",
        callbacks + "\nstatic int validRecord(const unsigned char *record, size_t available) {",
    )

    replace_once(
        title_id,
        "static int readImageAt(int fd, uint64_t offset, void *buffer, size_t size,\n"
        "                       int isZso, const ZsoInfo *info) {\n"
        "  if (!isZso) {",
        "static int readImageAt(int fd, uint64_t offset, void *buffer, size_t size,\n"
        "                       int isZso, const ZsoInfo *info, int isChd) {\n"
        "  if (!isZso && !isChd) {",
    )
    replace_once(
        title_id,
        "    if (readZsoSector(fd, info, sector, sectorBuffer))\n"
        "      return -EIO;",
        "    if (isChd) {\n"
        "      if (sector > UINT32_MAX ||\n"
        "          chd_read_sector(sectorBuffer, (u32)sector, 1) != 1)\n"
        "        return -EIO;\n"
        "    } else if (readZsoSector(fd, info, sector, sectorBuffer)) {\n"
        "      return -EIO;\n"
        "    }",
    )

    replace_once(
        title_id,
        "static int getPVD(int fd, uint64_t isoSize, ISOExtent *root,\n"
        "                 int isZso, const ZsoInfo *zso) {",
        "static int getPVD(int fd, uint64_t isoSize, ISOExtent *root,\n"
        "                 int isZso, const ZsoInfo *zso, int isChd) {",
    )
    replace_once(
        title_id,
        "                  sizeof(iso_buf), isZso, zso))",
        "                  sizeof(iso_buf), isZso, zso, isChd))",
    )
    replace_once(
        title_id,
        "static int getTOCEntry(int fd, const ISOExtent *root, uint64_t isoSize,\n"
        "                       ISOExtent *systemCNF, int isZso, const ZsoInfo *zso) {",
        "static int getTOCEntry(int fd, const ISOExtent *root, uint64_t isoSize,\n"
        "                       ISOExtent *systemCNF, int isZso, const ZsoInfo *zso,\n"
        "                       int isChd) {",
    )
    replace_once(
        title_id,
        "    if (readImageAt(fd, offset, iso_buf, bytes, isZso, zso))",
        "    if (readImageAt(fd, offset, iso_buf, bytes, isZso, zso, isChd))",
    )

    old_setup = (
        '  const char *extension = strrchr(path, \'.\');\n'
        '  int isZso = extension && !strcasecmp(extension, ".zso");\n'
        '  ZsoInfo zso = {0};\n'
        '  if (isZso && readZsoInfo(fd, &zso)) {\n'
        '    close(fd);\n'
        '    errno = EINVAL;\n'
        '    return NULL;\n'
        '  }\n'
        '  ISOExtent root, systemCNF;\n'
        '  char *text = NULL, *titleID = NULL;\n'
        '  int error = -EINVAL;\n'
        '  int64_t isoSize = isZso ? (int64_t)zso.totalBytes : lseek64(fd, 0, SEEK_END);\n'
        '  if (isoSize < 0) { error = -EIO; goto done; }\n'
        '  error = getPVD(fd, (uint64_t)isoSize, &root, isZso, isZso ? &zso : NULL);\n'
        '  if (!error) error = getTOCEntry(fd, &root, (uint64_t)isoSize, &systemCNF,\n'
        '                                 isZso, isZso ? &zso : NULL);'
    )
    new_setup = (
        '  const char *extension = strrchr(path, \'.\');\n'
        '  int isZso = extension && !strcasecmp(extension, ".zso");\n'
        '  int isChd = extension && !strcasecmp(extension, ".chd");\n'
        '  ZsoInfo zso = {0};\n'
        '  int chdReady = 0;\n'
        '  ISOExtent root, systemCNF;\n'
        '  char *text = NULL, *titleID = NULL;\n'
        '  int error = -EINVAL;\n'
        '  if (isZso && readZsoInfo(fd, &zso)) { error = -EINVAL; goto done; }\n'
        '  if (isChd) {\n'
        '    chdTitleFd = fd;\n'
        '    if (!chd_init()) { error = -EINVAL; goto done; }\n'
        '    chdReady = 1;\n'
        '  }\n'
        '  int64_t isoSize = isChd ? (int64_t)chd_logical_bytes() :\n'
        '                    (isZso ? (int64_t)zso.totalBytes : lseek64(fd, 0, SEEK_END));\n'
        '  if (isoSize < 0) { error = -EIO; goto done; }\n'
        '  error = getPVD(fd, (uint64_t)isoSize, &root, isZso, isZso ? &zso : NULL, isChd);\n'
        '  if (!error) error = getTOCEntry(fd, &root, (uint64_t)isoSize, &systemCNF,\n'
        '                                 isZso, isZso ? &zso : NULL, isChd);'
    )
    replace_once(title_id, old_setup, new_setup)

    replace_once(
        title_id,
        "  if (readImageAt(fd, systemCNF.offset, text, systemCNF.size,\n"
        "                  isZso, isZso ? &zso : NULL)) {",
        "  if (readImageAt(fd, systemCNF.offset, text, systemCNF.size,\n"
        "                  isZso, isZso ? &zso : NULL, isChd)) {",
    )
    replace_once(
        title_id,
        "done:\n"
        "  free(text);\n"
        "  if (close(fd) < 0) {",
        "done:\n"
        "  free(text);\n"
        "  if (chdReady) chd_close();\n"
        "  if (isChd) chdTitleFd = -1;\n"
        "  if (close(fd) < 0) {",
    )

    opl_ata = nhddl_root / "src/opl_ata.c"
    replace_once(
        opl_ata,
        "static int oplPathIsZso(const char *path) {\n"
        "  const char *extension = path ? strrchr(path, '.') : NULL;\n"
        "  return extension && !strcasecmp(extension, \".zso\");\n"
        "}\n",
        "static int oplPathIsZso(const char *path) {\n"
        "  const char *extension = path ? strrchr(path, '.') : NULL;\n"
        "  return extension && !strcasecmp(extension, \".zso\");\n"
        "}\n\n"
        "static int oplPathIsChd(const char *path) {\n"
        "  const char *extension = path ? strrchr(path, '.') : NULL;\n"
        "  return extension && !strcasecmp(extension, \".chd\");\n"
        "}\n",
    )
    replace_once(
        opl_ata,
        "  int isZso = oplPathIsZso(target->fullPath);\n"
        "  int iopFd = ps2sdk_get_iop_fd(fd);",
        "  int isZso = oplPathIsZso(target->fullPath);\n"
        "  int isChd = oplPathIsChd(target->fullPath);\n"
        "  int iopFd = ps2sdk_get_iop_fd(fd);",
    )
    replace_once(
        opl_ata,
        "  if (fileSize < (isZso ? 24 : 17 * 2048) || (!isZso && fileSize % 2048)) {",
        "  if (fileSize < (isChd ? 124 : (isZso ? 24 : 17 * 2048)) ||\n"
        "      (!isZso && !isChd && fileSize % 2048)) {",
    )
    replace_once(
        opl_ata,
        "  if (*logo && !isZso)\n    *logo = oplPrepareLogo(fd);",
        "  if (*logo && !isZso && !isChd)\n    *logo = oplPrepareLogo(fd);",
    )
    replace_once(
        opl_ata,
        "  if (!isZso && lseek(fd, 16 * 2048, SEEK_SET) >= 0 &&",
        "  if (!isZso && !isChd && lseek(fd, 16 * 2048, SEEK_SET) >= 0 &&",
    )

    cmake = nhddl_root / "CMakeLists.txt"
    replace_once(
        cmake,
        "    src/devices/hdl.c\n"
        "    src/devices/title_id.c\n)",
        "    src/devices/hdl.c\n"
        "    src/devices/chd.c\n"
        "    src/devices/title_id.c\n)",
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {Path(sys.argv[0]).name} <nhddl-source-dir> <opl-source-dir>", file=sys.stderr)
        return 2
    nhddl_root = Path(sys.argv[1]).resolve()
    opl_root = Path(sys.argv[2]).resolve()
    for required in (nhddl_root / "CMakeLists.txt", opl_root / "modules/isofs"):
        if not required.exists():
            raise RuntimeError(f"Required source path does not exist: {required}")
    copy_chd_sources(opl_root, nhddl_root)
    patch_nhddl(nhddl_root)
    print("Applied native CHD scanning, title-ID reading, and OPL launch integration.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"LUNA native CHD customization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
