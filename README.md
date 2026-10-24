<p align="center">
  <img src="assets/luna-logo.svg" alt="LUNA logo" width="700">
  <br>
  <sub>LIMEN UMBRAE NEXUS ARCANUM</sub>
</p>

LUNA is a modern visual game launcher for the PlayStation 2, built on
[NHDDL](https://github.com/pcm720/nhddl). Designed to bring a polished,
console-like experience, LUNA combines game discovery, library management, and multiple launch engines into one lightweight, unified interface.

PS2 games launch through [Neutrino](https://github.com/rickgaiser/neutrino) or
[OPL](https://github.com/ps2homebrew/Open-PS2-Loader). PS1 games launch
through [PSXCore](https://github.com/dnunezx/PSXCore).


PSXCore is an in-house, open-source project developed specifically for LUNA as an alternative to POPStarter.
It was born from the need for a dedicated PlayStation 1 solution that could be actively maintained, updated, and improved over time.
Development has already seen major breakthroughs in game compatibility, with significant progress on games previously thought to be broken or incompatible, and now has disc-set management,
in-game disc swapping, and in-game return.


## Library views

| View | Experience |
| --- | --- |
| **List** | A title list with a cover and spinning disc label. Choose Separate or Overlap artwork. |
| **Collections** | A PSBBN-inspired cover flow using square artwork. |
| **Orbit** | A rotating ring of covers with perspective, depth, and Random Scan. |
| **3D** | A 6 × 4 display of game cases with a selected-cover preview and PS1 jewel-case styling. |
| **Scroll** | A horizontal logo strip above a cover carousel. Missing logos fall back to title text. |

<table>
  <tr>
    <td align="center" width="50%"><strong>List</strong><br><img src="assets/previews/classic.gif" alt="List view with cover art and a rotating disc label" width="360"></td>
    <td align="center" width="50%"><strong>Collections</strong><br><img src="assets/previews/collection.gif" alt="Collections view moving through game artwork" width="360"></td>
  </tr>
  <tr>
    <td align="center"><strong>Orbit</strong><br><img src="assets/previews/orbit.gif" alt="Orbit view moving through a ring of game covers" width="360"></td>
  </tr>
</table>

The previews illustrate these views; individual details may differ in newer builds.

Press **Circle** to cycle through enabled views. List, Collections, Orbit,
and 3D are enabled by default; enable Scroll in **Options → Views**.
Favorites, the selected view, and the game-platform filter are remembered.

## Requirements

- **PlayStation 2:** hardware testing has been performed on a fat PS2.
- **Free McBoot memory card:** enough space for the complete `APP_LUNA` folder.
- **Internal ATA/exFAT HDD:** the intended setup for library and artwork
  performance, with an MBR or GPT partition table and an exFAT partition.
- **Compatible network adapter or HDD bridge:** hardware testing used a
  GameStar PS2 SATA HDD Adapter.
- **Optional artwork:** games can launch without it. Use
  [OrbitPS2 Manager — LUNA Edition](https://github.com/dnunezx/OrbitPS2-Manager-LUNA-edition)
  to prepare the library and artwork.

Other storage sources are selectable through **Start → Storage Devices**.
Artwork performance on slower devices can affect navigation.

## Installation

These steps use a memory card in slot 1 (`mc0:`), a working FMCB setup, and
a USB drive your PS2 can read.

1. Download the package ending in `-FMCB-mc0.zip` from
   [LUNA Releases](https://github.com/dnunezx/LUNA/releases).
2. Extract it and copy the complete `APP_LUNA` folder to the USB drive's root.
3. On the PS2, open uLaunchELF or wLaunchELF from FMCB. Copy `APP_LUNA` from
   `mass:/` to `mc0:/`.
4. Open FMCB Configurator, add a menu item named **LUNA**, and set its path to
   `mc0:/APP_LUNA/luna.elf`. Save the FMCB configuration.
5. Connect the prepared game drive and start LUNA from FMCB.

### Optional: direct Matrix Infinity boot with R1 (DEV1)

This fork's ZIP contains `BOOT/BOOT.ELF`, a small forwarder for the Matrix Infinity DEV1/R1 shortcut. Matrix DEV1 expects the file at `mc0:/BOOT/BOOT.ELF`; R2 uses a different filename, `BOOT2.ELF`.

1. Install the complete `APP_LUNA` folder at `mc0:/APP_LUNA/` as described above.
2. Back up your existing `mc0:/BOOT/BOOT.ELF` (which may currently be uLaunchELF/wLaunchELF) to a PC or rename it to `BOOT3.ELF` if you want to preserve a recovery launcher reachable using L2.
3. Copy the package's `BOOT/BOOT.ELF` to `mc0:/BOOT/BOOT.ELF`, **replacing the old BOOT.ELF**. Do not put it in the root of the memory card or inside `APP_LUNA`.
4. Fully power off the PS2, then hold **R1** on controller 1 while turning it on. Alternatively set Matrix `BOOT MODE` to `DEV1` to attempt this shortcut automatically.

The forwarder starts `mc0:/APP_LUNA/luna.elf` without moving or duplicating the LUNA application folder. `luna.yaml`, `neutrino.elf`, `config/`, `modules/`, and OPL runtime files remain in the original `APP_LUNA` structure. The configured `return_path` should remain `mc0:/APP_LUNA/luna.elf`.

**Status:** the R1 forwarder is compiled in CI, but still requires testing on this physical PS2/Matrix setup. Keep a backup of the old file manager ELF before replacing it.

Keep the application folder intact:

```text
mc0:/APP_LUNA/
  luna.elf
  luna.yaml
  neutrino.elf
  config/
  modules/
```

A PSXCore-enabled installation also needs `psxcore-runtime-bootstrap.elf`
beside `neutrino.elf`. Use the matching runtime files supplied for your build.

For memory-card slot 2, use `mc1:/APP_LUNA/luna.elf` and change `return_path`
in `luna.yaml` to match for the PS2 launch engines. PSXCore's IGR return target
is set in its runtime build, so its destination must also match your installation.
Changing `luna.yaml` alone does not change PSXCore's return target.

### Optional ambient music

If your release includes `Ambient-Music-Add-On`, copy its `ambient.wav` file
into `APP_LUNA`. It uses about 1.3 MB of additional card space. Enable
**Options → Global → Ambient sound**, then press **Start** to save.
LUNA also works without the music file.

## Preparing your library

Mount the drive in **OrbitPS2 Manager — LUNA Edition** and accept its prompt
to create missing library folders. Import your PS2 games and obtain artwork
through the manager. Keep games and artwork on the game drive.

```text
/CD/                         PS2 CD images
/DVD/                        PS2 DVD images (ISO, ZSO, and supported CHD)
/VCD/                        PS1 VCD images
/ART/                        Cover and disc artwork
/ART/PSBBN/                  Square artwork
/ART/SCROLL/                 Scroll logos
/CHT/                        Raw PS2RD cheat files
/VMC/                        PS2 virtual memory cards
/LUNA/                       Library state and settings
```

An existing OPL library can retain its title-ID artwork conventions.
Connect storage before launching LUNA; live insertion and removal are not
supported by the Storage Devices menu.

## Experimental native CHD support

This branch adds native CHD reading to the bundled OPL runtime and LUNA's
library scanner. Place supported `.chd` DVD images on a storage device scanned
by LUNA; `/DVD/` is a convenient location. Use CHD files created from DVD-style
PS2 ISOs with MAME's `chdman`, for example:

```powershell
chdman createdvd -i "Game.iso" -o "Game.chd" -c zlib -hs 262144
```

**Current format limits:** CHD v5, 2048-byte logical sectors, zlib codec,
uncompressed hunks, and self-hunk aliases. Parent CHDs, CD-track CHDs, and
LZMA/Huffman/FLAC/Zstandard codecs are not supported. Keep the source ISO until
you have tested the CHD on your own console. The decoder is host-tested and the
runtime build is checked in CI, but gameplay on a physical PS2 has not yet
been validated. CHD metadata is read natively when LUNA scans the library.

### PlayStation setup

PS1 discovery and launch preparation support **internal ATA and USB drives**.
Place compatible `.VCD` images in `VCD/` on the game drive. Supply the exact
firmware files accepted by the bundled PSXCore version on that same drive:

```text
/POPS/POPS.ELF
/POPS/IOPRP252.IMG
```

Sony's POPS runtime is proprietary and **is not included**. LUNA checks the
firmware's size and SHA-256 before launch and reports missing or mismatched files.
Keep `psxcore-runtime-bootstrap.elf` beside `neutrino.elf` in `APP_LUNA`.

Press **L3** to choose Mix or PS1, select a game, and press **Cross**.
Missing default cards are created automatically. The default pair is shared;
choose a named pair in the game's memory-card settings for separate saves.

### Multi-disc games

A disc set combines **two to four VCD images** into one library entry. Keep
every image on the same drive and arrange them in the game's disc order.

#### Create a set in LUNA

1. Highlight one of the game's discs and open **Triangle → Game → Discs**.
2. Select **Manage discs**. LUNA can suggest nearby images with matching
   names such as `Game (Disc 1).VCD` and `Game (Disc 2).VCD`.
3. Check the suggestion. Use **Add disc** for missing images. Select an entry
   to **Move earlier**, **Move later**, or **Remove disc**. The first entry is Disc 1.
4. Choose **Save disc set**, enter a name when creating a new set, and confirm.
   LUNA saves an `.m3u` playlist and refreshes the library. If prompted, refresh
   the drive through **Start → Storage Devices**.
5. Highlight the grouped entry. Under **Game → Discs → Start disc**, choose
   the disc to boot and press **Start** to save. Return to the library and press
   **Cross** to launch.

Save any pending game settings with **Start** before opening **Manage discs**.
Filename suggestions need your confirmation; matching names alone do not create a set.
Valid sets appear once in the library, with their individual disc entries hidden.

#### Create a playlist on your computer

Place the `.m3u` file alongside the game's VCD images in `VCD/`. List one
image per line in disc order, without quotation marks:

```text
/VCD/
  Example Game.m3u
  Example Game (Disc 1).VCD
  Example Game (Disc 2).VCD
```

Contents of `Example Game.m3u`:

```m3u
Example Game (Disc 1).VCD
Example Game (Disc 2).VCD
```

Relative paths resolve from the playlist's folder. Paths must stay on the same
drive. Rescan the drive after adding or changing a playlist. Keep each image in
one set; overlapping playlists, missing images, and duplicate discs are rejected.
LUNA-created playlists include an identity line; preserve it when editing them.

#### Swap discs during play

Launch the **grouped entry** so PSXCore receives the complete set. When the
game asks you to change discs, use controller port 1:

| Hold together | Selects |
| --- | --- |
| **L2 + R2 + Select + Up** | Disc 1 |
| **L2 + R2 + Select + Right** | Disc 2 |
| **L2 + R2 + Select + Down** | Disc 3 |
| **L2 + R2 + Select + Left** | Disc 4 |

Release all buttons before entering a shortcut, then release them again after
selecting the disc so the swap can finish. Follow the game's on-screen prompts.
Only discs registered in the launched set are available. These shortcuts follow
[PSXCore's disc-swap controls](https://github.com/dnunezx/PSXCore/blob/e4218a478c93caac4c868aed6f3451540db6a03e/runtime/cdswap.c).
This changes the disc
in the running game; it does not launch an unrelated game from your library.

All discs use the set's selected memory-card pair. Choose a named pair before
playing if you want the set to have its own saves.

LUNA reads the complete images to validate a set before launch, which can take
time. If you intentionally replace an image and LUNA reports changed content,
open **Manage discs**, select that image, and choose **Revalidate image**.
Confirm the replacement; the next launch checks and records its current content.

## Controls

| Button | Library action |
| --- | --- |
| **Cross** | Launch the selected game. |
| **Circle** | Switch to the next enabled view. |
| **Triangle** | Open Options. |
| **Start** | Open the main menu. |
| **Select** | Switch between All and Favorites. |
| **L3** | Cycle Mix → PS2 → PS1 in PSXCore-enabled builds. |
| **Hold R1** | Open the quick menu. |
| **Square in List** | Add or remove the selected Favorite. |
| **Square in Orbit** | Start Random Scan; navigation cancels it. |
| **L2 / R2 in List or 3D** | Move between pages. |
| **Hold L2 / R2 in Collections** | Fast scan through covers. |

While holding **R1**, use **Cross** to toggle the Favorites filter,
**Circle** to toggle the selected Favorite, **Triangle** for Options,
**L3** for the platform filter, or **R3** for Orbit Random Scan.

### In-game return

Use the familiar LUNA combination:

**L1 + L2 + R1 + R2 + Start + Select**

- **PS2 / Neutrino or OPL:** hold the combination for roughly one second to
  return to the configured LUNA ELF. Leave IGR enabled in the game's settings.
- **PS1 / an IGR-enabled PSXCore runtime:** use the same combination to open
  the native in-game menu, then confirm **Quit** to load the runtime's return ELF.
  A runtime configured to return to LUNA needs that ELF at its expected memory-card path.

Finish saving before returning. PSXCore's return destination is supplied by its
runtime build and is independent of LUNA's `return_path` setting.

**Runtime availability:** the current upstream PSXCore source builds native
disc swapping and IGR return as separate configurations. A disc-swapping runtime
does not automatically include IGR. Use a package that explicitly provides the
feature you need. See [PSXCore's runtime source](https://github.com/dnunezx/PSXCore/blob/e4218a478c93caac4c868aed6f3451540db6a03e/runtime/main.c)
and [IGR return implementation](https://github.com/dnunezx/PSXCore/blob/e4218a478c93caac4c868aed6f3451540db6a03e/runtime/igrreturn.h).

## Game settings

Open **Triangle → Game** for the selected title, or **Global** for defaults.
Press **Start** to save changes.

- **PS2 game core:** OPL is the default on a fresh setup in this fork. Select Neutrino globally or per game if needed. A saved per-drive preference in `/LUNA/gameCore.txt` overrides the fresh-setup default.
  OPL launch integration covers ATA/FAT32/exFAT, APA/HDL, USB, MX4SIO, iLink,
  MMCE, and UDPFS.
- **Compatibility and video:** choose the settings for the selected PS2 core.
  Neutrino includes 240p/288p, 480p/576p, and 1080i scaling options. Output
  changes do not automatically increase a game's internal rendering resolution.
- **Startup logo:** set the PS2 logo globally or override it for a game.
- **Cheats:** select entries from `CHT/<TITLE_ID>.cht`, enable cheats, and save.
  Cheats are off by default. This path uses raw PS2RD codes and the matching
  LUNA Neutrino runtime; encrypted cheat files are not supported.
- **PS1 compatibility:** open **Game → Compatibility → Code Validation**
  if a title fails to boot or shows a black screen. It is off by default;
  enable it for the affected game and press **Start** to save.
- **PS1 discs:** use **Game → Discs** to manage a set or select its starting disc.
  These options apply to PlayStation games.


## Virtual memory cards

Open **Start → Virtual Memory Cards** to manage cards. PSXCore-enabled builds
offer separate PlayStation and PlayStation 2 managers.

### PlayStation 2

Create formatted 8 MiB cards or assign existing compatible raw OPL `.bin`
images from the game's drive. Open **Game → Virtual memory cards** to assign
slot 1 and slot 2, then press **Start** to save. Physical cards remain an option.

Supported local card locations include exFAT HDD, USB, MX4SIO, iLink, and
mounted APA/PFS metadata storage. Neutrino accepts compatible raw 8, 16, 32,
and 64 MiB images. APA/PFS cards require the matching runtime and have layout
and fragmentation limits; compatibility still needs physical-console testing.
UDPFS does not offer local file-card creation or selection.

### PlayStation

Use the **default shared cards** on the game drive, or create and assign a
**named pair** through the game's memory-card settings. Both slots follow the
selected pair. Press **Start** in game settings to save the assignment.

```text
/POPS/ps1emu/card0              Default shared slot 1
/POPS/ps1emu/card1              Default shared slot 2
/POPS/CARDS/<name>/card0.vmc     Named pair, slot 1
/POPS/CARDS/<name>/card1.vmc     Named pair, slot 2
```

Each card is 128 KB. The manager supports import, export, backups of both
cards, and recovery of interrupted card operations. Importing into a shared
card affects every game using it. These management features are part of the
experimental PS1 integration; real-game save/reload testing remains ongoing.



## Storage and built-in tools

**Start → Storage Devices** selects ATA/exFAT HDD, APA/HDLoader HDD, USB,
MX4SIO, MMCE, iLink, or UDPFS. Toggle sources and choose
**Apply changes & scan**, rescan one enabled source with **Square**, or rescan
all enabled devices. MX4SIO and MMCE cannot be selected together. UDPFS needs
Ethernet and a running server; its console-IP setting is the PS2's address.

### File Explorer

Open **Start → File Explorer** to browse available storage and memory cards.
The browser keeps your marked items in a copy tray while you choose a destination.

| Button | Explorer action |
| --- | --- |
| **Cross** | Open a folder, preview supported text, or confirm a homebrew ELF launch. |
| **Circle** | Go up one folder; leave Explorer from the device list. |
| **L1** | Return to the device list. |
| **Square** | Mark or unmark an item in the tray. |
| **Triangle** | Open actions for the selected item. |
| **R2** | Open folder and tray actions. |
| **R1** | Expand or collapse a populated tray. |
| **Start** | Copy the tray to the current folder, or move it after choosing a Move action. |
| **Select** | Clear the tray after confirmation. |
| **Hold L2 + Up / Down** | Move a page at a time. |

To copy files, mark them with **Square**, open the destination folder, and
press **Start**. For a move, choose the appropriate **Move** action first,
then open the destination and press **Start**. Transfers show progress and offer
**Skip**, **Keep Both**, or **Replace** for name conflicts. Moves verify copied
data before removing the source.

Context menus also offer folder creation, rename, deletion, file and folder
details, name filtering, and sorting by name, size, or date. Supported text and
configuration files open in a read-only preview. Compatible PS2 homebrew `.elf`
files can launch directly after confirmation.

### Language and system actions

**Start → Language** selects English, Español, or Português (Brazilian
Portuguese). The preference applies immediately and is saved beside LUNA.
The main menu also offers **Exit LUNA** and **Shutdown**.

## Make LUNA your own

Open **Triangle → Global → Background** to choose Stars & cubes, Ambient Orbs,
Red Clouds, Midnight Cubes, System Configuration, Neo, Aurora, Ronin,
Gridrunner, Torch, or Tempest. Choose a glass color and font on the same page,
then press **Start** to save.

Under **Options → Views**, enable the views you want in the **Circle** cycle.
The **View appearance** section contains:

- **List art layout:** Separate or Overlap for the cover and disc artwork.
- **PS1 case style:** Jewel case or Tall in List and 3D. PS2 covers retain
  their tall cases.

Select Ambient Orbs as the background to customize its theme, light appearance,
colors, trails, and enabled shapes in **Options → Orbs**. Press **Start** to
save your changes.

## Artwork and saved preferences

Artwork is optional. LUNA uses title IDs and these PNG naming conventions:

```text
/ART/<TITLE_ID>_COV.png         Cover artwork
/ART/<TITLE_ID>_ICO.png         Optional disc label
/ART/PSBBN/<TITLE_ID>.png       Square artwork for Collections and Orbit
/ART/SCROLL/<TITLE_ID>_LGO.png  Optional Scroll logo
```


Library state lives under `/LUNA` on the game drive, including cache,
last-launched title, Favorites, view selection, and game settings. Legacy
`/nhddl` state remains readable as a fallback. Storage and language preferences
are saved beside the LUNA executable. PS1 card selections live under
`/POPS/CARD_SELECTIONS` on the game drive.

## Source and credits

| Component | Role |
| --- | --- |
| [`nhddl/`](https://github.com/dnunezx/nhddl-luna) | LUNA frontend derived from NHDDL. |
| [`neutrino/`](https://github.com/dnunezx/neutrino-luna) | Default PS2 game runtime. |
| [`opl/`](https://github.com/dnunezx/Open-PS2-Loader) | Alternate PS2 launch integration. |
| [`psxcore/`](https://github.com/dnunezx/PSXCore) | Independently maintained, experimental PS1 dependency in early development. |

Initialize the pinned dependencies with `git submodule update --init --recursive`.
PSXCore is consumed unchanged; LUNA-specific integration belongs in LUNA.

Special thanks to **Ivan V ([pcm720](https://github.com/pcm720))** for NHDDL,
**Rick Gaiser ([Maximus32](https://github.com/ps2max32))** for Neutrino,
and the **Open PS2 Loader contributors**.

Thanks to **[CosmicScale](https://github.com/CosmicScale)** and the
**[PSBBN Definitive Project](https://github.com/CosmicScale/PSBBN-Definitive-Project)**
for design inspiration and assets, **[NathanNeurotic (Ripto)](https://github.com/NathanNeurotic)**
for help with ambient orbs, **[aap](https://github.com/aap/osdbits)** for OSDSYS
reverse engineering, and all LUNA beta testers.

See [AUTHORS.md](AUTHORS.md), [UPSTREAM.md](UPSTREAM.md), and
the preserved licenses in [LICENSES](LICENSES/) for attribution and source lineage.
Original LUNA code and modifications: **Danny Nunez (dnunezx), 2026**.
Games, Sony firmware, and proprietary POPS runtime files are not distributed
in this source repository.
