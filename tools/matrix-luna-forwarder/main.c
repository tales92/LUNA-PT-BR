#define NEWLIB_PORT_AWARE

/*
 * Matrix Infinity DEV1/R1 forwarder for LUNA-PT-BR.
 *
 * R1/DEV1 boots mc0:/BOOT/BOOT.ELF. This launcher targets the unchanged
 * APP_LUNA folder and supplies its real mc path as argv[0], allowing LUNA to
 * discover luna.yaml and runtime files beside luna.elf.
 *
 * IMPORTANT: LoadExecPS2() only supports rom0: and cdrom: paths. Since LUNA
 * lives on a memory card, use PS2SDK's LoadELFFromFile() ELF loader instead.
 *
 * This build targets an installation in physical memory-card slot 1 (mc0:).
 * The validation path and ELF loader path must both point to that same card.
 */
#include <debug.h>
#include <elf-loader.h>
#include <fcntl.h>
#include <fileio.h>
#include <iopheap.h>
#include <iopcontrol.h>
#include <kernel.h>
#include <loadfile.h>
#include <sbv_patches.h>
#include <sifrpc.h>

#define LUNA_LOAD_PATH "mc0:/APP_LUNA/luna.elf"
#define LUNA_ARGV0     "mc0:/APP_LUNA/luna.elf"

static void reset_iop(void) {
  SifInitRpc(0);
  while (!SifIopReset("", 0)) {
  }
  while (!SifIopSync()) {
  }
  SifInitRpc(0);
}

static void fatal_error(const char *message) {
  init_scr();
  scr_clear();
  scr_printf("\nLUNA R1 forwarder\n\n%s\n\nExpected LUNA path:\n%s\n",
             message, LUNA_ARGV0);
  for (;;) {
    SleepThread();
  }
}

int main(int argc, char *argv[]) {
  int fd;
  (void)argc;
  (void)argv;
  char *target_argv[1];

  init_scr();
  scr_clear();
  scr_printf("LUNA R1 forwarder\n\nPreparing memory-card access...\n");

  reset_iop();
  if (SifInitIopHeap() < 0)
    fatal_error("Could not initialize the IOP heap.");
  if (SifLoadFileInit() < 0)
    fatal_error("Could not initialize the IOP loader.");
  if (fioInit() < 0)
    fatal_error("Could not initialize file I/O.");

  sbv_patch_disable_prefix_check();

  if (SifLoadModule("rom0:SIO2MAN", 0, NULL) < 0)
    fatal_error("Could not load SIO2MAN.");
  if (SifLoadModule("rom0:MCMAN", 0, NULL) < 0)
    fatal_error("Could not load MCMAN.");
  if (SifLoadModule("rom0:MCSERV", 0, NULL) < 0)
    fatal_error("Could not load MCSERV.");

  fd = fioOpen(LUNA_ARGV0, O_RDONLY);
  if (fd < 0)
    fatal_error("LUNA was not found. Check mc0:/APP_LUNA/luna.elf.");
  fioClose(fd);

  scr_clear();
  scr_printf("Loading LUNA from memory card...\n%s\n", LUNA_LOAD_PATH);
  target_argv[0] = (char *)LUNA_ARGV0;

  /*
   * LoadExecPS2() cannot execute an ELF directly from mc0:. The PS2SDK ELF
   * loader reads the file from the memory card and transfers control to it.
   * On successful execution this call does not return.
   */
  LoadELFFromFile(LUNA_LOAD_PATH, 1, target_argv);

  fatal_error("The ELF loader returned unexpectedly. LUNA could not be started.");
  return 1;
}
