#!/usr/bin/env python3
"""
romlink.py - builds the AmigaROM (the 192KB Expansion ROM at $F00000) from
its modules, as Remus does: byte-identical to Remus 1.81 (checked against
the 48.00 build and two test compiles, 13-10-2026) but for the header's
jump, which is JMP (A5) - the jump back to the ROM that called the
Expansion ROM. Remus does not take that header, so its images had
JMP $F80152 and were patched before flashing ($4EF9 -> $4ED5); built here,
the image is right as it is, and so is its checksum.

The ApolloSoftware-Manager has the same builder in JavaScript (romBuild()
in public/manager/app.js): change both together. releases.py uses this one
to check that an AmigaROM image is exactly what its ROM-Modules builds.

    python3 .github/scripts/romlink.py <out> <version> <module> ...
    e.g. romlink.py AmigaROM 48.01 68040.library 680x0.library ...

The image:
    $000  header, 16 bytes: $1111, JMP (A5) ($4ED5, then $00F80152 as in
          Remus' JMP $F80152, never reached), $0000FFFF, version.w,
          revision.w (48.01: 48, 1)
    $010  the modules in ROM order: of each its hunks back to back, every
          hunk on a 4-byte boundary, relocated to its ROM address
    ...   $FF up to the end block
    end-24: the Kickstart end block: checksum (add with carry over the whole
          image, complemented), the ROM size, then the words $18..$1F
"""

import re
import struct
import sys

BASE = 0xF00000                 # where the AmigaROM sits
SIZE = 0x30000                  # 192KB
ALIGN = 4
HEADER = bytes.fromhex("11114ed500f801520000ffff")      # + version.w revision.w
END = 24                        # the end block

HUNK_HEADER, HUNK_CODE, HUNK_DATA, HUNK_BSS = 0x3F3, 0x3E9, 0x3EA, 0x3EB
HUNK_RELOC32, HUNK_SYMBOL, HUNK_DEBUG, HUNK_END = 0x3EC, 0x3F0, 0x3F1, 0x3F2
HUNK_DREL32, HUNK_RELOC32SHORT = 0x3F7, 0x3FC          # 16-bit relocations


class RomError(Exception):
    pass


def version_words(release):
    """'48.01' (or '48.01-beta') -> (48, 1); RomError when it is no
    <number>.<number> an AmigaROM header can hold"""
    m = re.fullmatch(r"(\d+)\.(\d+)(-beta)?", release)
    if not m or int(m.group(1)) > 0xFFFF or int(m.group(2)) > 0xFFFF:
        raise RomError(f"{release}: an AmigaROM version is <number>.<number> (e.g. 48.01)")
    return int(m.group(1)), int(m.group(2))


def hunks(data, label="module"):
    """The hunks of an AmigaOS executable: [{data, relocs: [(hunk, offset)]}]"""
    pos = 0

    def long():
        nonlocal pos
        if pos + 4 > len(data):
            raise RomError(f"{label}: ends early - not a complete AmigaOS executable")
        v = struct.unpack_from(">I", data, pos)[0]
        pos += 4
        return v

    if len(data) < 4 or long() != HUNK_HEADER:
        raise RomError(f"{label}: not an AmigaOS executable (no hunk header)")
    while long():                                   # resident library names
        pass
    long()                                          # table size
    first, last = long(), long()
    sizes = [(long() & 0x3FFFFFFF) * 4 for _ in range(last - first + 1)]
    out, cur = [], None
    while pos < len(data):
        kind = long() & 0x3FFFFFFF
        if kind in (HUNK_CODE, HUNK_DATA):
            n = long() * 4
            cur = {"data": bytearray(data[pos:pos + n]), "relocs": []}
            pos += n
            if len(out) >= len(sizes):
                raise RomError(f"{label}: more hunks than its header says")
            cur["data"] += bytes(sizes[len(out)] - len(cur["data"]))
            out.append(cur)
        elif kind == HUNK_BSS:
            raise RomError(f"{label}: has a BSS hunk (uninitialised data) - ROM code cannot have one")
        elif kind == HUNK_RELOC32:
            while True:
                count = long()
                if not count:
                    break
                target = long()
                for _ in range(count):
                    cur["relocs"].append((target, long()))
        elif kind in (HUNK_DREL32, HUNK_RELOC32SHORT):
            words = []
            while True:
                count = struct.unpack_from(">H", data, pos)[0]
                pos += 2
                if not count:
                    break
                target = struct.unpack_from(">H", data, pos)[0]
                pos += 2
                for _ in range(count):
                    words.append((target, struct.unpack_from(">H", data, pos)[0]))
                    pos += 2
            cur["relocs"] += words
            pos = (pos + 3) & ~3
        elif kind == HUNK_SYMBOL:
            while True:
                n = long() & 0xFFFFFF
                if not n:
                    break
                pos += n * 4 + 4
        elif kind == HUNK_DEBUG:
            pos += long() * 4
        elif kind == HUNK_END:
            pass
        else:
            raise RomError(f"{label}: hunk type ${kind:X} is not supported")
    if len(out) != len(sizes):
        raise RomError(f"{label}: has {len(out)} of the {len(sizes)} hunks its header says")
    return out


# ---------------------------------------------------------------------------
# the packed size: the AmigaROM is flashed NOVA-packed into a 128KB block
# ($710000-$72FFFF); the core unpacks it to $F00000. Port of ApolloUpdate's
# nova.c (pknova7 of ApolloFlash / ApolloExpROM): the same length, byte for
# byte. Only the length is needed here.
# ---------------------------------------------------------------------------

PACKED_MAX = 0x20000            # the flash block of the AmigaROM
NOVA_HEADER = 12
NOVA_DIST_EXP = 65535           # ApolloExpROM's search distance


def packed_size(image, distance=NOVA_DIST_EXP):
    """The NOVA7 packed length (header included) of an image"""
    src = bytes(image) + bytes(16)                  # the packer reads past the end
    n = len(image)
    head, prev = {}, [0] * n
    out = NOVA_HEADER
    to_copy, last0, last1 = 1, 9999, 9999

    def h(p):
        return (src[p] << 16) | (src[p + 1] << 8) | src[p + 2]

    def insert(p):
        k = h(p)
        prev[p] = head.get(k, -99999)
        head[k] = p

    def copy(size):
        nonlocal out, to_copy, last0, last1
        if last1 < 1000 and last0 in (2003, 3004) and last1 + size <= 60:
            size += last1
            out -= 1 + last1
            if last0 > 3000:
                size += 4
                out -= 3
            else:
                size += 3
                out -= 2
        out += 1 + size
        to_copy = 0
        last1, last0 = last0, size

    def crunch(dist, size):
        nonlocal out, last0, last1
        if dist > 2047 or size > 17:
            out += 3
            last1, last0 = last0, 3000 + size
        else:
            out += 2
            last1, last0 = last0, 2000 + size

    insert(0)
    ptr = 1
    while ptr < n:
        length = min(n - ptr, 65)
        best, best_dist = 0, 0
        pointer = head.get(h(ptr), -99999)
        lo = ptr - min(ptr, distance) + 1
        if ptr - pointer < 65535:
            while pointer >= lo:
                m = 0
                while m < length and src[pointer + m] == src[ptr + m]:
                    m += 1
                if m > best:
                    best, best_dist = m, ptr - pointer
                    if m == 65:
                        break
                pointer = prev[pointer]
        if best > 3 or (best > 2 and best_dist <= 2047) or (best == 2 and to_copy == 0 and best_dist <= 2047):
            if to_copy > 0:
                copy(to_copy)
            crunch(best_dist, best)
            for _ in range(best):
                insert(ptr)
                ptr += 1
        else:
            insert(ptr)
            to_copy += 1
            ptr += 1
            if to_copy == 64:
                copy(to_copy)
    if to_copy > 0:
        copy(to_copy)
    return out


def checksum(rom):
    """The Kickstart checksum: add with carry over every longword (with the
    checksum longword 0), complemented"""
    s = 0
    for (v,) in struct.iter_unpack(">I", rom):
        s += v
        if s > 0xFFFFFFFF:
            s = (s & 0xFFFFFFFF) + 1
    return ~s & 0xFFFFFFFF


def build(release, modules):
    """The AmigaROM image for a release from [(label, data)] in ROM order.
    Returns (image, [(label, address, size)])."""
    version, revision = version_words(release)
    rom = bytearray(HEADER + struct.pack(">HH", version, revision))
    placed = []
    for label, data in modules:
        hs = hunks(data, label)
        start, addr, at = len(rom), [], len(rom)
        for h in hs:                                # every hunk 4-byte aligned
            addr.append(BASE + at)
            at = (at + len(h["data"]) + ALIGN - 1) // ALIGN * ALIGN
        for i, h in enumerate(hs):
            d = h["data"]
            for target, off in h["relocs"]:
                if target >= len(hs) or off + 4 > len(d):
                    raise RomError(f"{label}: a relocation points outside its hunks")
                v = struct.unpack_from(">I", d, off)[0] + addr[target]
                struct.pack_into(">I", d, off, v & 0xFFFFFFFF)
            rom += bytes(addr[i] - BASE - len(rom)) + d
        rom += bytes(at - len(rom))
        placed.append((label, BASE + start, len(rom) - start))
    if len(rom) > SIZE - END:
        raise RomError(f"the modules take {len(rom)} bytes - an AmigaROM holds {SIZE - END}")
    rom += b"\xff" * (SIZE - END - len(rom))
    rom += struct.pack(">II", 0, SIZE) + struct.pack(">8H", *range(0x18, 0x20))
    struct.pack_into(">I", rom, SIZE - END, checksum(rom))
    return bytes(rom), placed


def selftest():
    """A two-hunk module with relocations either way; the checksum makes the
    image sum to $FFFFFFFF"""
    exe = (struct.pack(">7I", HUNK_HEADER, 0, 2, 0, 1, 4, 2)
           + struct.pack(">6I", HUNK_CODE, 4, 0x4E714E75, 4, 0, 0)       # nop rts, -> data+4
           + struct.pack(">5I", HUNK_RELOC32, 1, 1, 4, 0) + struct.pack(">I", HUNK_END)
           + struct.pack(">4I", HUNK_DATA, 2, 0x12345678, 8)             # -> code+8
           + struct.pack(">5I", HUNK_RELOC32, 1, 0, 4, 0) + struct.pack(">I", HUNK_END))
    rom, placed = build("48.01", [("test", exe)])
    assert rom[:16] == bytes.fromhex("11114ed500f801520000ffff00300001")
    assert struct.unpack_from(">I", rom, 16 + 4)[0] == BASE + 32 + 4            # code -> data + 4
    assert struct.unpack_from(">I", rom, 32 + 4)[0] == BASE + 16 + 8            # data -> code + 8
    assert placed == [("test", BASE + 16, 24)]
    assert checksum(rom[:SIZE - END] + bytes(4) + rom[SIZE - END + 4:]) == struct.unpack_from(">I", rom, SIZE - END)[0]
    s = 0
    for (v,) in struct.iter_unpack(">I", rom):
        s += v
        if s > 0xFFFFFFFF:
            s = (s & 0xFFFFFFFF) + 1
    assert s == 0xFFFFFFFF
    # packed lengths as ApolloUpdate's nova.c gives them
    assert packed_size(bytes(1000)) == 63
    mixed, x = bytearray(70000), 12345
    for i in range(len(mixed)):
        x = (x * 1103515245 + 12345) & 0xFFFFFFFFFFFFFFFF
        mixed[i] = 65 if i % 7 == 0 else (x >> 16) & 0xFF
    assert packed_size(bytes(mixed)) == 71013
    for bad in ("48", "48.1.2", "R9.6", "70000.1"):
        try:
            version_words(bad)
            raise AssertionError(bad)
        except RomError:
            pass
    print("romlink selftest: passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
        sys.exit(0)
    if len(sys.argv) < 4:
        sys.exit(__doc__.split("\n\n")[2])
    out, release, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    try:
        image, placed = build(release, [(f, open(f, "rb").read()) for f in files])
    except RomError as e:
        sys.exit(f"romlink: {e}")
    open(out, "wb").write(image)
    for label, addr, size in placed:
        print(f"${addr:06X}  {size:6d}  {label}")
    print(f"{out}: {sum(p[2] for p in placed) + 16} of {SIZE - END} bytes used, "
          f"packed {packed_size(image)} of {PACKED_MAX}")
