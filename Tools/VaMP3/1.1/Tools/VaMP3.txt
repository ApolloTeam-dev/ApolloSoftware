Short Description: MUI MP3 Player for Apollo V4 / AmigaOS
Author: Tomas Jacobsen (Bedroomcoders.com)
Uploader: tomas@bedroomcoders.com
Version: 1.1
Type: mus/play
Architecture: m68k-amigaos >= 3.5 (optimized for 68080)


DESCRIPTION
-----------
VaMP3 is a lightweight and minimalistic MUI-based audio player designed 
specifically for the Apollo V4 platform. It features a compact, visually 
premium dashboard coupled with robust playlist and directory management 
capabilities.


FEATURES
--------
* Coded in 100% Assembly (complete source code is available).
* Utilizes SAGA/ARNE audio for high-quality DMA playback.
* Modern Magic User Interface (MUI) layout with a space-saving compact mode.
* Drag & Drop support in both regular and compact modes, as well as directly 
  into the playlist.
* Automatic Playlist Persistence: Active playlists automatically save on exit 
  and restore on startup (via PROGDIR:vaMP3.playlist).
* Standard M3U Playlist support: Easily load, save, and backup custom playlist 
  files (.m3u) from the main menu bar.
* Resizable sidecar windows: Dedicated Directory List (Dirlist) and Playlist 
  dashboards.
* User-customizable Tapedeck buttons using standard Datatypes.


SYSTEM REQUIREMENTS
-------------------
* ApolloOS / AmigaOS 3.5+ / AmigaOS 3.2+
* Apollo Vampire V4 Accelerator or standalone system.
* muimaster.library (MUI 3.8+ recommended).
* mpega.library (Libmad version recommended).
* CyberGraphX RTG graphics system.
* datatypes.library (V43+ pictures class).


INSTALLATION
------------
Copy the "VaMP3" drawer to any location on your hard drive.


USAGE
-----
Double-click the "vaMP3" icon from Workbench or run it from the CLI/Shell.

At first startup, the default "GrayNWhite" tapedeck buttons by HanSOLO are displayed. 
Additional buttonsets are included in the package and can be selected via the 
settings menu. Or why not create your own buttons with any datatype supported images?

There are fours ways to select and play your music:
  * Drag & Drop files directly onto the player window.
  * Use the Dirlist window to navigate your folders and select songs. The player 
    will automatically continue playing the next song in the directory when the 
    active track finishes. This is a convenient way to play complete albums 
    stored on your hard drive.
  * Build a custom Playlist using Drag & Drop, or add single files and complete 
    directories using the playlist control buttons.
  * Pass a MP3's filename as a command line argument

COPYRIGHT
---------
vaMP3 is Copyright (c) 2026 Bedroomcoders.com. 
All rights reserved.

