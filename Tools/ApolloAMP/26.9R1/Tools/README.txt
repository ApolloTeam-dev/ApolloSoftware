ApolloAMP 26.9 R1

(c) 2026 RedBug (m dot maci at gmx dot ch)

ApolloAMP (Codename: Intrepid) is a WinAMP clone for Apollo V4 cards with direct hardware 
playback via ARNE (no AHI = better quality).

Skins:
IFF, BMP, PNG supported. AROS (ApolloOS) may have problems loading images via datatypes
(use PNG = different loader instead). Click on info / lightning button (bottom right) to 
load skin.

Audio:
- Files: MP3, AIFF, FLAC, WAV, M4A (AAC) supported (M4A only on AmigaOS).
- Streams: MP3 (http/https via M3U/PLS playlists)

Playlists:
Basic support for M3U/PLS playlists (files/streams).

Favorites:
One-Click-Favorite-Saving = when listening to a stream with ICY metadata support, click on
song title to save the actual song & artist to FAVORITES.TXT.

Remotes:
Click on STATUS (left to big digits) and use joystick | joypad | mouse for remote control.
- fire | middle button: toggle prev/next vs volume
- wheelup/down | joyup/down: 
  + next/previous song (playing)
  + volume up/down (mode 1 stopped + voice)
The red (1) / yellow (2) light indicates which mode is active.

Tooltypes:
SKIN/K,FILE/K,VOLUME/N,BALANCE/N,VOICE/N,PRIOLO/N,PRIONO/N,PRIOHI/N,REORDER/N,AUDPER2/S

Shell:
Tranquillity, the audio backend used by ApolloAMP, can also be run in the shell. For more info, 
type: Tranquillity ?

Voice:
Disabled on AROS (no narrator.device).

Libs:
- Use libmad (NOT Tavenard): https://aminet.net/package/util/libs/mpega_libmad
- Install latest AmiSSL (for streams): https://aminet.net/package/util/libs/AmiSSL-v5-OS3

Full version (= no grayscaled skins, no 5 mins limit for streaming) available at:
apollo-vampire-lair.com

* * *

RELEASE NOTES

VERSION 26.9 R1 - INITIAL RELEASE

- Classic WinAMP 2.x skins (BMP, IFF, PNG)
- MP3, AIFF, WAV, FLAC, M4A (AAC) formats
- MP3 streaming (http/https via AmiSSL)
- ICY metadata parsing (artist & title)
- One-Click-Favorite-Saving (streams)
- Single file and directory playlists
- Basic M3U/PLS playlist support
- Tranquillity audio server (ARNE)
- Native audio quality (no AHI)
- Remote control (mouse/joyport)
- Text-to-speak (narrator.device)
- Collection of nice skins included

* * *

COPYRIGHT

(c) 2026 RedBug / ApolloTeam

Third-party copyrights and patents have been carefully researched, and no known 
conflicts with existing rights or licenses have been identified. However, patent 
rights may vary by jurisdiction. ApolloAMP may disable individual codecs or 
functionalities without notice in response to a rights holder's claim or for 
legal or technical reasons. ApolloAMP performs a secure HTTPS revocation check at 
startup. No personal information beyond standard connection data is transmitted.

THIRD PARTY LICENSES

(1) https://github.com/nothings/stb/blob/master/stb_image.h [PNG loader, MIT/PD]
(2) https://github.com/tpunix/flacat [FLAC decoder, MIT]
(3) https://github.com/lieff/minimp3/blob/master/minimp3.h [MP3 Streaming, CC0]
(4) https://github.com/lieff/minimp4 [MP4 parsing, CC0]
(5) https://github.com/CrispStrobe/glint.git [AAC decoding, MIT]

ORIGINAL LICENSE NOTICES

FOR (1) - STB PNG LOADER

------------------------------------------------------------------------------
This software is available under 2 licenses -- choose whichever you prefer.
------------------------------------------------------------------------------
ALTERNATIVE A - MIT License
Copyright (c) 2017 Sean Barrett
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
------------------------------------------------------------------------------
ALTERNATIVE B - Public Domain (www.unlicense.org)
This is free and unencumbered software released into the public domain.
Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.
In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
------------------------------------------------------------------------------

FOR (2): SIMPLE FLAC DECODER

Copyright (c) 2020 Project Nayuki. (MIT License)
https://www.nayuki.io/page/simple-flac-implementation

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:
- The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.
- The Software is provided "as is", without warranty of any kind, express or
  implied, including but not limited to the warranties of merchantability,
  fitness for a particular purpose and noninfringement. In no event shall the
  authors or copyright holders be liable for any claim, damages or other
  liability, whether in an action of contract, tort or otherwise, arising from,
  out of or in connection with the Software or the use or other dealings in the
  Software.

FOR (3): MINIMP3

https://github.com/lieff/minimp3
To the extent possible under law, the author(s) have dedicated all copyright and 
related and neighboring rights to this software to the public domain worldwide.
This software is distributed without any warranty.
See <http://creativecommons.org/publicdomain/zero/1.0/>.

FOR (4): MINIMP4

https://github.com/aspt/mp4
https://github.com/lieff/minimp4
To the extent possible under law, the author(s) have dedicated all copyright and 
related and neighboring rights to this software to the public domain worldwide.
This software is distributed without any warranty.
See <http://creativecommons.org/publicdomain/zero/1.0/>.

For (5): GLINT

MIT License

Copyright (c) 2026 CrispStrobe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
