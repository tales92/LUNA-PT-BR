#!/usr/bin/env python3
"""Apply the two LUNA-PT-BR build customizations to the pinned nhddl submodule.

The parent repository tracks nhddl as a submodule, so these source changes are
applied to its working tree immediately before a LUNA build. The transformation
is idempotent and fails loudly if the upstream source has drifted unexpectedly.
"""
from pathlib import Path
import sys

MARKER = "LUNA_PT_BR_ZSO"


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"{path}: expected one patch anchor, found {count}; "
            "no source was changed for this replacement"
        )
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <nhddl-source-directory>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    required = [
        root / "src/ui/language.c",
        root / "src/devices/iso.c",
        root / "src/devices/title_id.c",
        root / "src/neutrino.c",
        root / "src/opl_ata.c",
    ]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        print("LUNA source files not found:\n" + "\n".join(missing), file=sys.stderr)
        return 2

    # 1) Portuguese (Brazil) is the fresh-install default. A saved language.cfg
    # still overrides this default, so an existing user's preference is kept.
    replace_once(
        root / "src/ui/language.c",
        "static LunaLanguage activeLanguage;",
        "static LunaLanguage activeLanguage = LUNA_LANGUAGE_PORTUGUESE;",
    )
    replace_once(
        root / "src/ui/language.c",
        "  activeLanguage = LUNA_LANGUAGE_ENGLISH;",
        "  activeLanguage = LUNA_LANGUAGE_PORTUGUESE;",
    )

    # 2) Include .ZSO images in discovery. Their uncompressed ISO sectors are
    # read only for metadata; game execution is routed to the OPL core.
    replace_once(
        root / "src/devices/iso.c",
        '      if (isVcd || isPlaylist || (fileext && !strcasecmp(fileext, ".iso"))) {',
        '      int isZso = fileext && !strcasecmp(fileext, ".zso");\n'
        '      int isIso = fileext && !strcasecmp(fileext, ".iso");\n'
        '      if (isVcd || isPlaylist || isIso || isZso) {',
    )

    # Add a small, bounds-checked ZSO reader to the existing PS2 title-ID
    # parser. It decompresses only the sectors needed to find SYSTEM.CNF.
    title_id = root / "src/devices/title_id.c"
    replace_once(
        title_id,
        "#include <stdlib.h>\n#include <string.h>\n",
        "#include <stdlib.h>\n#include <strings.h>\n#include <string.h>\n",
    )
    zso_helpers = r'''
/* LUNA_PT_BR_ZSO: bounded ZISO/LZ4 sector reader for PS2 metadata scanning. */
typedef struct {
  uint32_t headerSize;
  uint64_t totalBytes;
  uint32_t blockSize;
  uint8_t align;
} ZsoInfo;

#define LUNA_ZSO_MAGIC 0x4F53495Au

static int readZsoInfo(int fd, ZsoInfo *info) {
  unsigned char header[24];
  if (lseek64(fd, 0, SEEK_SET) < 0 || readExact(fd, header, sizeof(header)))
    return -EIO;
  if (readLE32(header) != LUNA_ZSO_MAGIC)
    return -EINVAL;
  info->headerSize = readLE32(header + 4);
  info->totalBytes = (uint64_t)readLE32(header + 8) |
                     ((uint64_t)readLE32(header + 12) << 32);
  info->blockSize = readLE32(header + 16);
  info->align = header[21];
  if (info->headerSize < sizeof(header) || info->blockSize != SECTOR_SIZE ||
      info->align > 7 || info->totalBytes < (uint64_t)(TOC_LBA + 1) * SECTOR_SIZE ||
      info->totalBytes % SECTOR_SIZE || info->totalBytes > INT64_MAX)
    return -EINVAL;
  return 0;
}

static int readZsoIndex(int fd, const ZsoInfo *info, uint64_t block,
                        uint32_t *entry) {
  unsigned char raw[4];
  if (block > (UINT64_MAX - info->headerSize) / sizeof(uint32_t))
    return -EINVAL;
  uint64_t offset = (uint64_t)info->headerSize + block * sizeof(uint32_t);
  if (offset > INT64_MAX || lseek64(fd, (int64_t)offset, SEEK_SET) < 0 ||
      readExact(fd, raw, sizeof(raw)))
    return -EIO;
  *entry = readLE32(raw);
  return 0;
}

static int decompressZsoBlock(const unsigned char *src, size_t srcSize,
                              unsigned char *dst, size_t dstSize) {
  size_t in = 0, out = 0;
  while (in < srcSize && out < dstSize) {
    unsigned token = src[in++];
    size_t literals = token >> 4;
    if (literals == 15) {
      unsigned extra;
      do {
        if (in >= srcSize) return -EINVAL;
        extra = src[in++];
        if (literals > dstSize - (extra > dstSize ? dstSize : extra))
          return -EINVAL;
        literals += extra;
      } while (extra == 255);
    }
    if (literals > srcSize - in || literals > dstSize - out)
      return -EINVAL;
    memcpy(dst + out, src + in, literals);
    in += literals;
    out += literals;
    if (out == dstSize) return 0;
    if (in + 2 > srcSize) return -EINVAL;
    size_t distance = (size_t)src[in] | ((size_t)src[in + 1] << 8);
    in += 2;
    if (!distance || distance > out) return -EINVAL;
    size_t match = (token & 0x0F) + 4;
    if ((token & 0x0F) == 15) {
      unsigned extra;
      do {
        if (in >= srcSize) return -EINVAL;
        extra = src[in++];
        if (match > dstSize - (extra > dstSize ? dstSize : extra))
          return -EINVAL;
        match += extra;
      } while (extra == 255);
    }
    if (match > dstSize - out) return -EINVAL;
    for (size_t i = 0; i < match; i++)
      dst[out + i] = dst[out + i - distance];
    out += match;
  }
  return out == dstSize ? 0 : -EINVAL;
}

static int readZsoSector(int fd, const ZsoInfo *info, uint64_t sector,
                         unsigned char *out) {
  if (sector >= info->totalBytes / SECTOR_SIZE)
    return -EINVAL;
  uint32_t current, next;
  if (readZsoIndex(fd, info, sector, &current) ||
      readZsoIndex(fd, info, sector + 1, &next))
    return -EIO;
  uint32_t currentOffset = current & 0x7FFFFFFFu;
  uint32_t nextOffset = next & 0x7FFFFFFFu;
  if (nextOffset <= currentOffset)
    return -EINVAL;
  uint64_t offset = (uint64_t)currentOffset << info->align;
  uint64_t compressedSize = (uint64_t)(nextOffset - currentOffset) << info->align;
  if (offset > INT64_MAX || !compressedSize || compressedSize > 4096)
    return -EINVAL;
  if (current & 0x80000000u) {
    if (lseek64(fd, (int64_t)offset, SEEK_SET) < 0 ||
        readExact(fd, out, SECTOR_SIZE))
      return -EIO;
    return 0;
  }
  unsigned char compressed[4096];
  if (lseek64(fd, (int64_t)offset, SEEK_SET) < 0 ||
      readExact(fd, compressed, (size_t)compressedSize))
    return -EIO;
  return decompressZsoBlock(compressed, (size_t)compressedSize, out, SECTOR_SIZE);
}

static int readImageAt(int fd, uint64_t offset, void *buffer, size_t size,
                       int isZso, const ZsoInfo *info) {
  if (!isZso) {
    if (offset > INT64_MAX || lseek64(fd, (int64_t)offset, SEEK_SET) < 0)
      return -EIO;
    return readExact(fd, buffer, size);
  }
  unsigned char sectorBuffer[SECTOR_SIZE];
  unsigned char *destination = buffer;
  while (size) {
    uint64_t sector = offset / SECTOR_SIZE;
    size_t withinSector = (size_t)(offset % SECTOR_SIZE);
    if (readZsoSector(fd, info, sector, sectorBuffer))
      return -EIO;
    size_t available = SECTOR_SIZE - withinSector;
    size_t copy = size < available ? size : available;
    memcpy(destination, sectorBuffer + withinSector, copy);
    destination += copy;
    offset += copy;
    size -= copy;
  }
  return 0;
}
'''
    replace_once(
        title_id,
        "static int validRecord(const unsigned char *record, size_t available) {",
        zso_helpers + "\nstatic int validRecord(const unsigned char *record, size_t available) {",
    )
    replace_once(
        title_id,
        "static int getPVD(int fd, uint64_t isoSize, ISOExtent *root) {",
        "static int getPVD(int fd, uint64_t isoSize, ISOExtent *root,\n"
        "                 int isZso, const ZsoInfo *zso) {",
    )
    replace_once(
        title_id,
        "  if (lseek64(fd, (int64_t)TOC_LBA * SECTOR_SIZE, SEEK_SET) < 0 ||\n"
        "      readExact(fd, iso_buf, sizeof(iso_buf)))\n"
        "    return -EIO;",
        "  if (readImageAt(fd, (uint64_t)TOC_LBA * SECTOR_SIZE, iso_buf,\n"
        "                  sizeof(iso_buf), isZso, zso))\n"
        "    return -EIO;",
    )
    replace_once(
        title_id,
        "static int getTOCEntry(int fd, const ISOExtent *root, uint64_t isoSize,\n"
        "                       ISOExtent *systemCNF) {",
        "static int getTOCEntry(int fd, const ISOExtent *root, uint64_t isoSize,\n"
        "                       ISOExtent *systemCNF, int isZso, const ZsoInfo *zso) {",
    )
    replace_once(
        title_id,
        "    if (lseek64(fd, (int64_t)offset, SEEK_SET) < 0 ||\n"
        "        readExact(fd, iso_buf, bytes))\n"
        "      return -EIO;",
        "    if (readImageAt(fd, offset, iso_buf, bytes, isZso, zso))\n"
        "      return -EIO;",
    )
    replace_once(
        title_id,
        "  ISOExtent root, systemCNF;\n"
        "  char *text = NULL, *titleID = NULL;\n"
        "  int error = -EINVAL;\n"
        "  int64_t isoSize = lseek64(fd, 0, SEEK_END);\n"
        "  if (isoSize < 0) { error = -EIO; goto done; }\n"
        "  error = getPVD(fd, (uint64_t)isoSize, &root);\n"
        "  if (!error) error = getTOCEntry(fd, &root, (uint64_t)isoSize, &systemCNF);",
        "  const char *extension = strrchr(path, '.');\n"
        "  int isZso = extension && !strcasecmp(extension, \".zso\");\n"
        "  ZsoInfo zso = {0};\n"
        "  if (isZso && readZsoInfo(fd, &zso)) {\n"
        "    close(fd);\n"
        "    errno = EINVAL;\n"
        "    return NULL;\n"
        "  }\n"
        "  ISOExtent root, systemCNF;\n"
        "  char *text = NULL, *titleID = NULL;\n"
        "  int error = -EINVAL;\n"
        "  int64_t isoSize = isZso ? (int64_t)zso.totalBytes : lseek64(fd, 0, SEEK_END);\n"
        "  if (isoSize < 0) { error = -EIO; goto done; }\n"
        "  error = getPVD(fd, (uint64_t)isoSize, &root, isZso, isZso ? &zso : NULL);\n"
        "  if (!error) error = getTOCEntry(fd, &root, (uint64_t)isoSize, &systemCNF,\n"
        "                                 isZso, isZso ? &zso : NULL);",
    )

    # Route compressed images to OPL, the supported ZSO execution core.
    neutrino = root / "src/neutrino.c"
    replace_once(
        neutrino,
        "#include <string.h>\n",
        "#include <string.h>\n#include <strings.h>\n",
    )
    replace_once(
        neutrino,
        "  if (!launchTitleArgumentsFit(target, arguments, payload)) {\n"
        "    DPRINTF(\"ERROR: launch arguments exceed the kernel handoff buffer\\n\");\n"
        "    return;\n"
        "  }\n"
        "  // LUNA metadata is not a Neutrino command-line option. A missing or disabled\n",
        "  if (!launchTitleArgumentsFit(target, arguments, payload)) {\n"
        "    DPRINTF(\"ERROR: launch arguments exceed the kernel handoff buffer\\n\");\n"
        "    return;\n"
        "  }\n"
        "  const char *extension = strrchr(target->fullPath, '.');\n"
        "  if (extension && !strcasecmp(extension, \".zso\")) {\n"
        "    if (lunaOplDevice(target->device->mode) == NULL) {\n"
        "      DPRINTF(\"ERROR: ZSO requires an OPL-compatible storage device\\n\");\n"
        "      return;\n"
        "    }\n"
        "    int result = launchOplTitle(target, arguments, payload, progress, userdata);\n"
        "    DPRINTF(\"OPL ZSO launch failed or returned (%d); not falling back to Neutrino\\n\", result);\n"
        "    return;\n"
        "  }\n"
        "  // LUNA metadata is not a Neutrino command-line option. A missing or disabled\n",
    )

    # Let the OPL core accept compressed-file length and avoid probing compressed
    # bytes as if they were an ISO PVD/logo. Its bundled IOP reader handles ZSO.
    opl = root / "src/opl_ata.c"
    replace_once(
        opl,
        "#include <string.h>\n",
        "#include <string.h>\n#include <strings.h>\n",
    )
    replace_once(
        opl,
        "static int prepareDisc(Target *target, uint8_t compat, const LunaOplDevice *device,\n",
        "static int oplPathIsZso(const char *path) {\n"
        "  const char *extension = path ? strrchr(path, '.') : NULL;\n"
        "  return extension && !strcasecmp(extension, \".zso\");\n"
        "}\n\n"
        "static int prepareDisc(Target *target, uint8_t compat, const LunaOplDevice *device,\n",
    )
    replace_once(
        opl,
        "  int fd = open(target->fullPath, O_RDONLY);\n"
        "  if (fd < 0)\n"
        "    return -ENOENT;\n"
        "  int iopFd = ps2sdk_get_iop_fd(fd);\n"
        "  int fragments = 0;\n"
        "  _off64_t fileSize = lseek64(fd, 0, SEEK_END);\n"
        "  if (fileSize < 17 * 2048 || fileSize % 2048) {\n"
        "    close(fd);\n"
        "    return -EINVAL;\n"
        "  }",
        "  int fd = open(target->fullPath, O_RDONLY);\n"
        "  if (fd < 0)\n"
        "    return -ENOENT;\n"
        "  int isZso = oplPathIsZso(target->fullPath);\n"
        "  int iopFd = ps2sdk_get_iop_fd(fd);\n"
        "  int fragments = 0;\n"
        "  _off64_t fileSize = lseek64(fd, 0, SEEK_END);\n"
        "  if (fileSize < (isZso ? 24 : 17 * 2048) || (!isZso && fileSize % 2048)) {\n"
        "    close(fd);\n"
        "    return -EINVAL;\n"
        "  }",
    )
    replace_once(
        opl,
        "  if (*logo)\n    *logo = oplPrepareLogo(fd);",
        "  if (*logo && !isZso)\n    *logo = oplPrepareLogo(fd);",
    )
    replace_once(
        opl,
        "  if (lseek(fd, 16 * 2048, SEEK_SET) >= 0 &&\n",
        "  if (!isZso && lseek(fd, 16 * 2048, SEEK_SET) >= 0 &&\n",
    )

    print("Applied LUNA-PT-BR defaults and ZSO support to nhddl.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"LUNA customization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
