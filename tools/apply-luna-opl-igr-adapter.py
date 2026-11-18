#!/usr/bin/env python3
"""Reapply the LUNA-specific IGR rules after merging current upstream OPL."""
from pathlib import Path
import sys

path = Path("opl/ee_core/src/padhook.c")
source = path.read_text(encoding="utf-8")

old_power = """        /*
         * Preserve the original power-button monitoring.
         * These registers require kernel mode.
         */
        ee_kmode_enter();

        if ((*CDVD_R_NDIN & 0x20) &&
            (*CDVD_R_POFF & 0x04)) {
            Power_Button.press++;

            // Cancel immediate poweroff to allow double-press detection.
            *CDVD_R_SDIN = 0x00;
            *CDVD_R_SCMD = 0x1B;
        }

        if (Power_Button.press) {
            if (Power_Button.vb_count++ >= 50) {
                if (Power_Button.press == 1) {
                    Pad_Data.combo_type = IGR_COMBO_R3_L3;
                } else {
                    Pad_Data.combo_type = IGR_COMBO_START_SELECT;
                }
            }
        }

        ee_kmode_exit();

"""
new_power = """        /*
         * LUNA delegates physical power-button handling to Neutrino's IOP
         * shutdown thread when COMPAT_LUNA_IOP_POFF is enabled.
         */
        if (!(g_compat_mask & COMPAT_LUNA_IOP_POFF)) {
            ee_kmode_enter();

            if ((*CDVD_R_NDIN & 0x20) &&
                (*CDVD_R_POFF & 0x04)) {
                Power_Button.press++;

                // Cancel immediate poweroff to allow double-press detection.
                *CDVD_R_SDIN = 0x00;
                *CDVD_R_SCMD = 0x1B;
            }

            if (Power_Button.press) {
                if (Power_Button.vb_count++ >= 50) {
                    if (Power_Button.press == 1) {
                        Pad_Data.combo_type = IGR_COMBO_R3_L3;
                    } else {
                        Pad_Data.combo_type = IGR_COMBO_START_SELECT;
                    }
                }
            }

            ee_kmode_exit();
        }

"""

if new_power not in source:
    count = source.count(old_power)
    if count != 1:
        raise SystemExit(
            f"Expected one upstream polling power-button block; found {count}. "
            "Review OPL changes before adapting."
        )
    source = source.replace(old_power, new_power, 1)

if "LoadMemModule(0, mmceigr_irx, size_mmceigr_irx, sizeof(slots), slots);" not in source:
    declaration = "extern unsigned int size_mmceigr_irx;"
    if "extern unsigned char mmceigr_irx[];" not in source:
        anchor = "extern void *_end;"
        if source.count(anchor) != 1:
            raise SystemExit("Could not safely add the MMCE IGR module declaration")
        source = source.replace(
            anchor,
            anchor + "\nextern unsigned char mmceigr_irx[];\nextern unsigned int size_mmceigr_irx;",
            1
        )
    elif declaration not in source:
        source = source.replace(
            "extern unsigned char mmceigr_irx[];",
            "extern unsigned char mmceigr_irx[];\n" + declaration,
            1
        )

    reset_call = """        LoadOPLModule(
            OPL_MODULE_ID_RESETSPU,
            0,
            0,
            NULL);"""
    if source.count(reset_call) != 1:
        raise SystemExit(
            "Could not uniquely locate OPL's IGR RESETSPU load for MMCE restoration"
        )
    restore = """
        // Restore only the physical MMCE boot cards switched by LUNA.
        // This runs after IOP reset and before the launcher is reloaded.
        if (config->_CompatMask & COMPAT_LUNA_MMCE_MASK) {
            char slots[] = {(config->_CompatMask & COMPAT_LUNA_MMCE_SLOT0) ? '1' : '0',
                            (config->_CompatMask & COMPAT_LUNA_MMCE_SLOT1) ? '1' : '0', '\\0'};
            LoadMemModule(0, mmceigr_irx, size_mmceigr_irx, sizeof(slots), slots);
        }
"""
    source = source.replace(reset_call, reset_call + restore, 1)

if "if (!(g_compat_mask & COMPAT_LUNA_IOP_POFF))" not in source:
    raise SystemExit("LUNA IOP power-button guard is missing after adaptation")
if "LoadMemModule(0, mmceigr_irx, size_mmceigr_irx, sizeof(slots), slots);" not in source:
    raise SystemExit("LUNA MMCE boot-card restoration is missing after adaptation")

path.write_text(source, encoding="utf-8", newline="\n")
print("Applied LUNA IGR power-button and selective MMCE restoration adapters.")
