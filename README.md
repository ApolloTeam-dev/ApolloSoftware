# ApolloSoftware
Master repository for all current and legacy releases of Apollo specific drivers, tools and libraries 

Install and update with **ApolloUpdate** (`Tools/ApolloUpdate`). To get it
the first time, download the newest one with an Amiga browser (IBrowse,
AWeb, NetSurf with AmiSSL) from this fixed address, unpack it with LhA and
start it - from then on it keeps itself up to date:

    https://raw.githubusercontent.com/ApolloTeam-dev/ApolloSoftware/main/ApolloUpdate.lha

The library as a web page for Amiga browsers (IBrowse, AWeb, NetSurf), with
the same download: https://apolloteam-dev.github.io/ApolloSoftware/

Software for members of [Apollo-Vampire-Lair](https://ko-fi.com/apollovampirelair)
is in the separate ApolloSoftware-AVL repository; ApolloUpdate shows it to members.

## Folder Convention

Level-1 = Category (Drivers, FileSystems, Libraries, Resources, Tools, Icons, Cores, ROM, ...)

Level-2 = Name (Official name of the Apollo Software title)

Level-3 = Version (Official version -no spaces- example: 1.0e or 26.9R1).
A version ending in `-beta` (lower case, e.g. `12556E-beta`) is a **beta**;
any other is a **release**. ApolloUpdate shows betas only with its Beta
switch on. The version decides what is newest - the `-beta` suffix is left
out of the comparison, and of two equal versions the release wins
(`1.2` is newer than `1.2-beta`). The overviews show the newest **Release**
and the newest **Beta** (when it is newer than that release, else "-").
The ApolloROM uses `Rx.y-RCz` (major, minor, release candidate): numbers
compare as numbers, and a release candidate `-RC<n>` is older than its
release (`R9.6-RC05` < `R9.6-RC06` < `R9.6` < `R9.7-RC01`).

Level-4 = Deployment (Folder structure for copy to SYS: by ApolloUpdate)

Example (single file):
- Tools/ApolloMap/Info
- Tools/ApolloMap/2.30/C/ApolloMap

Example (multiple files):
- Tools/ApolloExplorer/Info
- Tools/ApolloExplorer/1.4.0/C/ApolloExplorerSrv
- Tools/ApolloExplorer/1.4.0/C/ApolloExplorerTool
- Tools/ApolloExplorer/1.4.0/Tools/ApolloExplorer
- Tools/ApolloExplorer/1.4.0/Tools/ApolloExplorer.info

### The Info file

Each Name folder holds one text file `Info`, `KEY=VALUE` per line, `;`
starts a comment:

```
OS=ApolloOS,AmigaOS
MINCORE=11000
MINCORE.1.0e=10900
DESCRIPTION=One line of text, shown in the bubble help of ApolloUpdate.
```

| Key | |
|---|---|
| `OS` | required: `ApolloOS`, `AmigaOS` or both, comma separated |
| `MINCORE` | the lowest Apollo core it runs on (core number); ApolloUpdate shows the entry in blue and does not install it on an older core |
| `MINCORE.<release>` | the same for one release, overrides `MINCORE` |
| `DESCRIPTION` | one line, at most 160 characters (longer is cut with "..."); ApolloUpdate wraps it at about 48 characters per line, `\n` forces a break. Plain ASCII: typographic quotes and accents are converted |

Leave a value empty when unknown. On every push a GitHub workflow checks the
layout and the `Info` files, and writes the table below and
`ApolloSoftware.index`, the file ApolloUpdate reads (do not edit it).
A new Name without an `Info` gets one from the workflow, for both OSes.
Check it and fill in the rest.

### Cores and ROM

Two kinds of image are flashed, not copied to SYS:

| Category / Name | OS | Release holds | ApolloUpdate keeps it in | Flashed by |
|---|---|---|---|---|
| `Cores/<core>` | both | the core (FPGA logic), one file | `SYS:ApolloUpdate/Cores/` | ApolloFlash |
| `ROM/ApolloROM` | ApolloOS | `ApolloROM` (the 1MB ApolloOS Kickstart: main ROM at $F80000, extended at $E00000) and `Modules` | `SYS:ApolloUpdate/ApolloROM/` | ApolloFlash |
| `ROM/AmigaROM` | AmigaOS | `AmigaROM` (the 192KB Expansion ROM at $F00000, for all AmigaOS releases incl. Coffin) and `Modules` | `SYS:ApolloUpdate/AmigaROM/` | ApolloExpROM |

`Modules` in a ROM release says which modules, in which version, make up
that ROM - **in ROM order**, one `Category/Name/Version` per line:

```
; AmigaROM 48.00 - its modules in ROM order
Libraries/68040.library/40.2
Libraries/680x0.library/40.1
...
Drivers/sagasd.device/2.41
```

The modules themselves are ordinary entries in their own category
(Drivers, FileSystems, Libraries, Resources, ...) with their own versions.
A module's file sits in an `AmigaROM/` (or `ApolloROM/`) drawer of its
release, e.g. `Drivers/sagasd.device/2.41/AmigaROM/sagasd.device`: such
files are only built into the ROM, never copied to SYS:. The AmigaROM's
header (ROM id and version) is made from the ROM's version, not listed.
Where an ApolloOS and an AmigaOS module would have the same Name, they get
the suffix `-ApolloOS` / `-AmigaOS`.

For now each ROM release also holds the compiled image; once ApolloUpdate
builds ROMs itself, `Modules` alone will do.

The workflow checks that every `Modules` line names an existing release
with its file in the ROM's drawer and for the ROM's OS, each module once;
that `ROM/ApolloROM` is `OS=ApolloOS` and `ROM/AmigaROM` `OS=AmigaOS`; and
the image sizes (ApolloROM 1MB, AmigaROM at most 192KB).

Before it copies, ApolloUpdate deletes whatever is already in its drawer in
`SYS:ApolloUpdate`, so the drawer only holds what was just installed. Then
it starts the flash tool (for now, a requester shows what would be flashed).

## Releases

<!-- releases:start -->
<!-- Generated by .github/scripts/releases.py on every push - do not edit by hand. -->

| Category | Name | Release | Beta | ApolloOS | AmigaOS | Minimal Core | Description |
|---|---|---|---|:-:|:-:|---|---|
| Cores | UniCorn-Core | **12001** | 12556E-beta | ✓ | ✓ |  | UniCorn Core |
| ROM | AmigaROM | **48.00** | - |  | ✓ |  | AmigaOS Expansion ROM ($F0): the Apollo drivers, filesystems and resources for all AmigaOS releases |
| ROM | ApolloROM | **R9.6-RC06** | - | ✓ |  |  | ApolloOS Kickstart ROM, 1MB: main ($F8) and extended ($E0) ROM |
| Resources | processor.resource | **44.3** | - |  | ✓ |  | processor.resource |
| Resources | vampire.resource | **45.3** | - |  | ✓ |  | vampire.resource |
| Drivers | AmiTCP | **4.1.7** | - |  | ✓ |  | TCP/IP Stack |
| Drivers | arne.audio | **4.23** | - | ✓ | ✓ |  | AHI Audio Driver |
| Drivers | cd.device | **40.29** | - |  | ✓ |  | CD32-Driver |
| Drivers | Keymaps | **1.0** | - | ✓ | ✓ |  | Keyboard Configurations |
| Drivers | sagagfx.hidd | **1.0** | - | ✓ |  | 12500 | CyberGraphics RTG Driver |
| Drivers | sagasd.device | **2.41** | - |  | ✓ | 12500 | SD-Card Driver |
| Drivers | scsi.device | **48.13** | - |  | ✓ |  | IDE Driver for AmigaOS |
| Drivers | v4net.device | **2.97** | 2.99-beta | ✓ | ✓ |  | Network Interface Driver |
| Drivers | vampiregfx.card | **1.61** | - |  | ✓ |  | Picasso 96 RTG Driver |
| Libraries | 68040.library | **40.2** | - |  | ✓ |  | 68040.library for the AC68080 |
| Libraries | 680x0.library | **40.1** | - |  | ✓ |  | 680x0.library, Apollo AC68080 support |
| Libraries | i2c.library | **40.0** | - | ✓ | ✓ |  | I2C Chip Library |
| Libraries | maggie.library | **4.0** | - | ✓ | ✓ |  | Maggie 3DFX API library |
| Libraries | VampireSupport | **40.49** | - |  | ✓ |  | Vampire support: V4 chip/fast RAM, FPU |
| FileSystems | exfat-handler | **1.11** | - |  | ✓ |  | Ex-FAT Filesystem |
| FileSystems | fat95 | **4.0** | - |  | ✓ |  | FAT Filesystem |
| FileSystems | ODFileSystem | **0.8.0** | - |  | ✓ |  | CD (ISO9660) Filesystem |
| Tools | AmiPlexAMP | **0.54** | - | ✓ | ✓ |  | Plex Audio Client |
| Tools | ApolloAMP | **26.9R1** | - | ✓ | ✓ |  | SAGA Audioplayer |
| Tools | ApolloControl | **2.21** | - | ✓ | ✓ |  | Apollo V4 Settings |
| Tools | ApolloExpROM | **1.1** | - |  | ✓ |  | Flash/Dump Expansion ROM ($F0) |
| Tools | ApolloFlash | **2.30** | - | ✓ | ✓ |  | Flash Core or ROM |
| Tools | ApolloFloppy | **1.2** | - | ✓ | ✓ |  | Apollo Virtual Floppy Loader |
| Tools | ApolloMap | **2.30** | - | ✓ | ✓ |  | Map ROM (SoftKick) |
| Tools | ApolloMon | **1.0e** | - | ✓ | ✓ |  | CPU Monitoring Widget |
| Tools | ApolloUpdate | **0.67** | - | ✓ | ✓ |  | Apollo Update Manager for ApolloOS and AmigaOS |
| Tools | ApolloVNC | **26.6R1** | - | ✓ | ✓ |  | Fast & Easy Remote VNC Application |
| Tools | ApolloWHDSet | **0.3.3** | - | ✓ | ✓ |  | Set SAGA Display ToolTypes |
| Tools | ApolloWheel | **0.1i** | - | ✓ | ✓ |  | Apollo MouseWheel Driver |
| Tools | i2clock | **0.7** | - | ✓ | ✓ |  | Load/Save date & time to RTC |
| Tools | RiVA | **0.63R4** | - | ✓ | ✓ |  | SAGA Videoplayer |
| Icons | def_SDROM | **1.0** | - | ✓ | ✓ |  | Default SD-Card Icon |

37 items: 22 for ApolloOS, 35 for AmigaOS.
<!-- releases:end -->

