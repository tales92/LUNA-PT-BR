#!/usr/bin/env bash
# Guard the LUNA-specific ABI and IGR behavior across upstream runtime merges.
set -Eeuo pipefail

need_file() {
  test -s "$1" || { echo "::error::Required integration file is missing: $1"; exit 1; }
}
need_text() {
  local file="$1"
  local needle="$2"
  grep -Fq -- "$needle" "$file" || {
    echo "::error::Required integration marker is missing from $file: $needle"
    exit 1
  }
}

# Neutrino: keep the LUNA UDPFS IP override, while admitting upstream SMB/NFS.
need_file neutrino/ee/loader/src/main.c
need_text neutrino/ee/loader/src/main.c "sys.sUDPFSIP"
need_text neutrino/ee/loader/src/main.c '(!strcmp(sys.sBSD, "smb"))'
need_text neutrino/ee/loader/src/main.c '(!strcmp(sys.sBSD, "nfs"))'
need_file neutrino/ee/loader/config/bsd-smb.toml
need_file neutrino/ee/loader/config/bsd-nfs.toml
need_file neutrino/iop/smb/Makefile
need_file neutrino/iop/nfs/Makefile
need_file neutrino/iop/smb/usmb2/Makefile
need_file neutrino/iop/nfs/unfs4/Makefile
need_file neutrino/ee/loader/src/mmce.c
need_text neutrino/ee/loader/src/mmce.c "mmce_set_gameid"

# OPL: preserve the LUNA MMCE/VMC and private IOPRP integration while taking
# upstream IGR polling, SIO2MAN-version handling and aligned BDM reads.
need_file opl/ee_core/include/ee_core.h
need_text opl/ee_core/include/ee_core.h "COMPAT_LUNA_MMCE_MASK"
need_text opl/ee_core/include/ee_core.h "COMPAT_LUNA_IOP_POFF"
need_file opl/ee_core/include/modules.h
need_text opl/ee_core/include/modules.h "OPL_MODULE_ID_LUNA_MMCEFHI"
need_text opl/ee_core/include/modules.h "OPL_MODULE_ID_SIO2MAN"
need_file opl/ee_core/src/iopmgr.c
need_text opl/ee_core/src/iopmgr.c "opli0:"
need_text opl/ee_core/src/iopmgr.c "LUNA_MMCE_MODE"
need_file opl/ee_core/src/padhook.c
need_text opl/ee_core/src/padhook.c "IGR_Poll_Alarm"
need_text opl/ee_core/src/padhook.c "COMPAT_LUNA_MMCE_MASK"
need_text opl/ee_core/src/padhook.c "COMPAT_LUNA_IOP_POFF"
need_text opl/ee_core/src/padhook.c "if (!(g_compat_mask & COMPAT_LUNA_IOP_POFF))"
need_text opl/ee_core/src/padhook.c "LoadMemModule(0, mmceigr_irx, size_mmceigr_irx, sizeof(slots), slots);"
need_file opl/modules/iopcore/cdvdman/device-bdm.c
need_text opl/modules/iopcore/cdvdman/device-bdm.c "bounce"
need_text opl/modules/iopcore/cdvdman/device-bdm.c "g_bd->flush"
need_file opl/modules/mcemu/mcemu.c
need_text opl/modules/mcemu/mcemu.c "DeviceVmcInit"
need_text opl/modules/mcemu/mcemu.c "hookSio2man25_1"
need_text opl/modules/mcemu/mcemu.c "hookSio2man25_2"
need_file opl/modules/mcemu/mcemu.h
need_text opl/modules/mcemu/mcemu.h "u32 transport"
need_text opl/modules/mcemu/mcemu.h "pSio2man25[2]"

echo "Runtime integration markers validated: Neutrino SMB/NFS + LUNA UDPFS/MMCE; OPL SIO2/IGR/VMC/MMCE."
