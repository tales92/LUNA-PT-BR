#define NEWLIB_PORT_AWARE

/*
 * Matrix Infinity R2 forwarder for LUNA-PT-BR.
 *
 * R2 boots mc0:/BOOT/BOOT2.ELF. This launcher targets the unchanged
 * APP_LUNA folder and supplies its real mc0 path as argv[0], allowing LUNA to
 * discover luna.yaml and runtime files beside luna.elf.
 *
 * This build targets an installation in physical memory-card slot 1 (mc0:).
 * LoadExecPS2's ROM/moduleload path has an MC-port inversion on some setups:
 * the load path uses mc1 to reach physical mc0, but argv[0] remains mc0 so
 * LUNA resolves its own configuration and return_path correctly.
 *
 * Physical-console validation is still required after compilation.
 */
#include <debug.h>
#include <fcntl.h>
#include <fileio.h>
#include <iopheap.h>
#include <iopcontrol.h>
#include <kernel.h>
#include <loadfile.h>
#include <sbv_patches.h>
#include <sifrpc.h>

#define LUNA_LOAD_PATH "mc1:/APP_LUNA/luna.elf"
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
  scr_printf("\nLUNA R2 forwarder\n\n%s\n\nExpected LUNA path:\n%s\n",
             message, LUNA_ARGV0);
  for (;;) {
    SleepThread();
  }
}

int main(int argc, char *argv[]) {
  int fd;
  char *target_argv[1];
  (void)argc;
  (void)argv;

  init_scr();
  scr_clear();
  scr_printf("LUNA R2 forwarder\n\nPreparing memory-card access...\n");

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
  scr_printf("Starting LUNA...\n%s\n", LUNA_ARGV0);
  target_argv[0] = (char *)LUNA_ARGV0;
  LoadExecPS2(LUNA_LOAD_PATH, 1, target_argv);

  /* LoadExecPS2 is declared noreturn; this is defensive only. */
  fatal_error("The system loader unexpectedly returned.");
  return 1;
}
