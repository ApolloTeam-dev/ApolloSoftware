#!/usr/bin/env python3
"""
releases.py - checks the ApolloSoftware (or ApolloSoftware-AVL) layout and
writes the releases table in README.md. Run by .github/workflows/releases.yml
on every push, and by hand from the top of the repository:

    python3 .github/scripts/releases.py --selftest
    python3 .github/scripts/releases.py --check --readme README.md --index ApolloSoftware.index
    python3 .github/scripts/releases.py --avl --public ../ApolloSoftware --check --readme README.md --index ApolloSoftware.index

The same script serves both repositories; --avl selects the rules of
ApolloSoftware-AVL (every Name needs AVL=Bronze|Silver|Gold, the minimum
membership level), and --public points at a checkout of the public
repository to find SYS: files installed by both.

Layout (the contract with the ApolloUpdate client):

    Category / Name / Release / <copied 1:1 to SYS:>
    Cores   / Name / Release / file      flashed, not copied to SYS::
    KickROM / Name / Release / file        one ROM file, by ApolloFlash
    ExpROM  / Name / Release / files       modules, ApolloExpROM builds them
                                           into the Expansion ROM
                                      no drawers; ApolloUpdate empties
                                      SYS:ApolloUpdate/Cores, /KickROM or
                                      /ExpROM and copies them there (the
                                      collision check uses that SYS: path)
    Category / Name / Info            KEY=VALUE lines, ";" comments:
        OS=ApolloOS,AmigaOS           required: the OS(es) the Name is for
        AVL=Bronze|Silver|Gold        ApolloSoftware-AVL only, required there
        OWNER=                        who maintains it
        CONTRIBUTORS=                 who else worked on it
        MINCORE=                      lowest Apollo core it runs on (number)
        MINCORE.<release>=            the same for one release
        DESCRIPTION=                  one line, at most 160 characters
    ApolloUpdate-ApolloOS.default     lookup table defaults per OS
    ApolloUpdate-AmigaOS.default
    ApolloSoftware.index              generated from the Info files: what
                                      ApolloUpdate reads (do not edit)

"Latest" must be what ApolloUpdate picks, so version_cmp() below is a
line-by-line port of Repo_VersionCmp() in ApolloUpdate's repo.c, and the
self-test uses the same cases as its hosttest.c. Change both together.
"""

import argparse
import functools
import os
import re
import sys
import textwrap
import unicodedata

OSES = ("ApolloOS", "AmigaOS")
TIERS = ("Bronze", "Silver", "Gold")                  # low to high
KEYS = ("OS", "AVL", "OWNER", "CONTRIBUTORS", "MINCORE", "DESCRIPTION")   # and MINCORE.<release>
INFO = "Info"
ROM_CATS = {"Cores": "ApolloUpdate/Cores",             # categories to flash, and
            "KickROM": "ApolloUpdate/KickROM",        # where ApolloUpdate keeps
            "ExpROM": "ApolloUpdate/ExpROM"}          # their files
INDEX = "ApolloSoftware.index"
MAX_DESC = 160                  # what fits in the bubble help ...
WRAP_DESC = 48                  # ... at this many characters per line
MARK_START = "<!-- releases:start -->"
MARK_END = "<!-- releases:end -->"
MAX_NAME = 30                   # FFS file name limit
TOP_FILES = {"README.md", ".gitattributes", ".gitignore", INDEX}
JUNK = re.compile(r"^(\.DS_Store|\._.*|Thumbs\.db|desktop\.ini)$", re.I)


# --------------------------------------------------------------------------
# release order: port of Repo_VersionCmp() (ApolloUpdate repo.c)
# --------------------------------------------------------------------------

def _digit(c):
    return "0" <= c <= "9"


def _alpha(c):
    return ("a" <= c <= "z") or ("A" <= c <= "Z")


def version_cmp(a, b):
    """<0, 0, >0 like strcmp. Digit runs compare as numbers, letter runs
    case-insensitively, separators are ignored, more runs = newer, a number
    against a letter at the same place: the number is newer."""
    i = j = 0
    while True:
        while i < len(a) and not _digit(a[i]) and not _alpha(a[i]):
            i += 1
        while j < len(b) and not _digit(b[j]) and not _alpha(b[j]):
            j += 1
        if i >= len(a) or j >= len(b):
            return (1 if i < len(a) else 0) - (1 if j < len(b) else 0)

        if _digit(a[i]) and _digit(b[j]):
            while a[i] == "0" and i + 1 < len(a) and _digit(a[i + 1]):
                i += 1
            while b[j] == "0" and j + 1 < len(b) and _digit(b[j + 1]):
                j += 1
            ea, eb = i, j
            while ea < len(a) and _digit(a[ea]):
                ea += 1
            while eb < len(b) and _digit(b[eb]):
                eb += 1
            if ea - i != eb - j:
                return -1 if ea - i < eb - j else 1
            if a[i:ea] != b[j:eb]:
                return -1 if a[i:ea] < b[j:eb] else 1
            i, j = ea, eb
        elif _alpha(a[i]) and _alpha(b[j]):
            while i < len(a) and j < len(b) and _alpha(a[i]) and _alpha(b[j]):
                ca, cb = a[i].lower(), b[j].lower()
                if ca != cb:
                    return -1 if ca < cb else 1
                i += 1
                j += 1
            if i < len(a) and _alpha(a[i]):
                return 1
            if j < len(b) and _alpha(b[j]):
                return -1
        else:
            return 1 if _digit(a[i]) else -1


def newest_first(releases):
    """The client's order: newest first, equal versions by plain strcmp."""
    def cmp(a, b):
        return -version_cmp(a, b) or ((a > b) - (a < b))
    return sorted(releases, key=functools.cmp_to_key(cmp))


def selftest():
    cases = [("4.23", "4.18", 1), ("1.60", "1.7", 1), ("26.10", "26.9R1", 1),
             ("26.9R2", "26.9R1", 1), ("1.0e", "1.0", 1), ("1.0.1", "1.0b", 1),
             ("0.63R3", "0.63R10", -1), ("2.30", "2.3", 1), ("01.2", "1.2", 0),
             ("1.4.0", "1.4.0", 0), ("0.1i", "0.1b", 1), ("2.36", "2.99", -1)]
    bad = 0
    for a, b, want in cases:
        got = version_cmp(a, b)
        got = (got > 0) - (got < 0)
        back = version_cmp(b, a)
        back = (back > 0) - (back < 0)
        if got != want or back != -want:
            print(f"selftest FAIL: {a} vs {b}: {got} (want {want}), reverse {back}")
            bad += 1
    print("selftest: %s" % ("all %d cases passed" % len(cases) if not bad else "%d FAILED" % bad))
    return bad == 0


# --------------------------------------------------------------------------
# reading the repository
# --------------------------------------------------------------------------

def is_dir(*p):
    return os.path.isdir(os.path.join(*p))


ASCII = {"\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201c": '"', "\u201d": '"',
         "\u201e": '"', "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ",
         "\u00d7": "x", "\u00df": "ss", "\u00e6": "ae", "\u00c6": "AE", "\u00f8": "o",
         "\u00d8": "O", "\u2122": "(TM)", "\u00a9": "(C)", "\u00ae": "(R)"}


def to_ascii(text):
    """Printable ASCII for the Amiga: typographic quotes and dashes become
    plain ones, accents are dropped, anything else is left out."""
    out = []
    for ch in text:
        ch = ASCII.get(ch, ch)
        if len(ch) == 1 and not (32 <= ord(ch) <= 126):
            ch = "".join(c for c in unicodedata.normalize("NFKD", ch) if 32 <= ord(c) <= 126)
        out.append(ch)
    return "".join(out)


def read_info(path, label, releases, avl, errors, warnings):
    """The Info file of a Name -> {KEY: value}, plus {"MINCORE.<rel>": value}"""
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")        # edited on the Amiga
    info = {}
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith((";", "#")):
            continue
        if "=" not in s:
            errors.append(f"{label}:{i}: not KEY=VALUE")
            continue
        key, value = s.split("=", 1)
        key, value = key.strip().upper(), value.strip()
        if key.startswith("MINCORE."):
            rel = s.split("=", 1)[0].strip()[8:]
            if rel not in releases:
                errors.append(f"{label}:{i}: MINCORE.{rel}: there is no release {rel}")
                continue
            key = "MINCORE." + rel
        elif key not in KEYS:
            errors.append(f"{label}:{i}: unknown key {key} (known: {', '.join(KEYS)}, MINCORE.<release>)")
            continue
        if key in info:
            errors.append(f"{label}:{i}: {key} given twice")
        info[key] = value
    for key in ("OWNER", "CONTRIBUTORS", "MINCORE", "DESCRIPTION"):
        info.setdefault(key, "")

    oses = [o.strip() for o in info.get("OS", "").split(",") if o.strip()]
    for o in oses:
        if o not in OSES:
            errors.append(f"{label}: OS={o}? (ApolloOS and/or AmigaOS)")
    if not oses:
        errors.append(f"{label}: no OS= line (OS=ApolloOS, OS=AmigaOS or OS=ApolloOS,AmigaOS)")
    info["OS"] = [o for o in OSES if o in oses]

    tier = info.get("AVL", "")
    if avl:
        match = [t for t in TIERS if t.lower() == tier.lower()]
        if not match:
            errors.append(f"{label}: AVL={tier or '?'} - needs AVL=Bronze, AVL=Silver or AVL=Gold")
        info["AVL"] = match[0] if match else None
    else:
        if tier:
            errors.append(f"{label}: AVL={tier} - AVL entries belong in ApolloSoftware-AVL, "
                          "not in the public repository")
        info["AVL"] = None

    for key in [k for k in info if k.startswith("MINCORE")]:
        if info[key] and not info[key].isdigit():
            errors.append(f"{label}: {key}={info[key]} is not a core number")
            info[key] = ""

    for key in ("OWNER", "CONTRIBUTORS"):
        info[key] = to_ascii(info[key]).replace("\t", " ")
    desc = to_ascii(info.get("DESCRIPTION", ""))
    if desc != info.get("DESCRIPTION", ""):
        warnings.append(f"{label}: DESCRIPTION has characters the Amiga lacks - changed to ASCII")
    desc = desc.replace("\t", " ")
    if len(desc) > MAX_DESC:
        warnings.append(f"{label}: DESCRIPTION is {len(desc)} characters - cut to {MAX_DESC}")
        desc = desc[:MAX_DESC - 3].rstrip() + "..."
    if not desc:
        warnings.append(f"{label}: no DESCRIPTION")
    info["DESCRIPTION"] = desc
    return info


def wrap(desc):
    """The description as bubble help lines; "\\n" in the text forces a break."""
    lines = []
    for part in desc.split("\\n"):
        lines += textwrap.wrap(part, WRAP_DESC) or [""]
    return lines


def scan(root, avl=False):
    """[(category, name, {os}, [releases newest first], info)], errors, warnings"""
    errors, warnings, names = [], [], []

    for entry in sorted(os.listdir(root)):
        if entry in TOP_FILES or (entry.startswith(".") and is_dir(root, entry)):
            continue        # .git, .github, .public (the workflow's checkout)
        if re.fullmatch(r"ApolloUpdate-(%s)\.default" % "|".join(OSES), entry):
            continue
        if not is_dir(root, entry) or entry.startswith("."):
            errors.append(f"{entry}: unexpected file at the top of the repository")

    cats = sorted((c for c in os.listdir(root)
                   if not c.startswith(".") and is_dir(root, c)), key=str.lower)
    for cat in cats:
        for name in sorted(os.listdir(os.path.join(root, cat)), key=str.lower):
            npath = os.path.join(root, cat, name)
            if not os.path.isdir(npath):
                errors.append(f"{cat}/{name}: a file directly in a category")
                continue
            releases, has_info = [], False
            for e in os.listdir(npath):
                if e == INFO and os.path.isfile(os.path.join(npath, e)):
                    has_info = True
                elif os.path.isdir(os.path.join(npath, e)):
                    releases.append(e)
                elif JUNK.match(e):
                    errors.append(f"{cat}/{name}/{e}: macOS/Windows metadata")
                elif e in OSES or e.startswith("AVL-"):
                    errors.append(f"{cat}/{name}/{e}: marker files are replaced by the "
                                  f"Info file - remove it")
                else:
                    errors.append(f"{cat}/{name}/{e}: only the Info file and release "
                                  "folders belong in a Name folder")
            if not releases:
                errors.append(f"{cat}/{name}: no release folder")
                continue
            if has_info:
                info = read_info(os.path.join(npath, INFO), f"{cat}/{name}/{INFO}",
                                 releases, avl, errors, warnings)
            else:
                errors.append(f"{cat}/{name}: no Info file (at least OS=ApolloOS,AmigaOS"
                              + (" and AVL=Bronze" if avl else "") + ")")
                info = {"OS": [], "AVL": None, "OWNER": "", "CONTRIBUTORS": "", "MINCORE": "",
                        "DESCRIPTION": ""}
            names.append((cat, name, set(info["OS"]), newest_first(releases), info))
    return names, errors, warnings


def release_files(root, cat, name, rel, errors=None):
    """[(path below the release, lower-case SYS path)] of one release, junk
    left out. A release of Cores, KickROM or ExpROM: its files directly in
    it, kept in SYS:ApolloUpdate/... (ROM_CATS). With errors, one that breaks
    the rules is reported."""
    rpath = os.path.join(root, cat, name, rel)
    out = []
    if cat in ROM_CATS:
        label = f"{cat}/{name}/{rel}"
        ents = sorted(e for e in os.listdir(rpath) if not JUNK.match(e))
        dirs = [e for e in ents if os.path.isdir(os.path.join(rpath, e))]
        files = [e for e in ents if e not in dirs]
        if errors is not None:
            for d in dirs:
                errors.append(f"{label}/{d}: no drawers in a {cat} release, only the "
                              "file(s) to flash")
            if cat in ("Cores", "KickROM") and len(files) > 1:
                errors.append(f"{label}: a {cat} release holds exactly one ROM file "
                              f"(has {len(files)})")
        return [(f, f"{ROM_CATS[cat]}/{f}".lower()) for f in files]
    for dirpath, dirs, fns in os.walk(rpath):
        for fn in fns:
            if not JUNK.match(fn):
                sub = os.path.relpath(os.path.join(dirpath, fn), rpath)
                out.append((sub, sub.lower()))
    return out


def sys_paths(root, names):
    """{(os, lower-case SYS path): "Cat/Name"} for every release of every Name"""
    owner = {}
    for cat, name, tags, releases, tier in names:
        for rel in releases:
            for sub, key in release_files(root, cat, name, rel):
                for o in tags:
                    owner.setdefault((o, key), f"{cat}/{name}")
    return owner


def check_public(root, names, public, errors):
    """AVL: no SYS: file shared with a public Name, unless it is the same
    Cat/Name (an AVL entry with the name of a public one replaces it)."""
    pub_names, e2, w2 = scan(public)
    pub = sys_paths(public, pub_names)
    mine = sys_paths(root, names)
    for key, who in sorted(mine.items()):
        other = pub.get(key)
        if other and other.lower() != who.lower():
            errors.append(f"SYS:{key[1]} ({key[0]}) is installed by {who} here and by "
                          f"{other} in ApolloSoftware")


def check_files(root, names, errors, warnings):
    """Per file: names, metadata junk, SYS: paths shared between Names."""
    owner = {}          # (os, lower-case SYS path) -> "Cat/Name"
    for cat, name, tags, releases, tier in names:
        for rel in releases:
            rpath = os.path.join(root, cat, name, rel)
            files = 0
            for dirpath, dirs, fns in os.walk(rpath):
                for d in dirs + fns:
                    if JUNK.match(d):
                        errors.append(f"{os.path.relpath(os.path.join(dirpath, d), root)}: "
                                      "macOS/Windows metadata")
                    if len(d) > MAX_NAME:
                        errors.append(f"{os.path.relpath(os.path.join(dirpath, d), root)}: "
                                      f"name longer than {MAX_NAME} characters")
                    if any(ord(ch) < 32 or ord(ch) > 126 for ch in d) or any(ch in d for ch in ':*?"<>|'):
                        errors.append(f"{os.path.relpath(os.path.join(dirpath, d), root)}: "
                                      "character that AmigaDOS or GitHub cannot take")
            for sub, path in release_files(root, cat, name, rel, errors):
                files += 1
                if cat not in ROM_CATS and os.sep not in sub:
                    warnings.append(f"{cat}/{name}/{rel}/{sub}: lands in the root of SYS:")
                for o in tags:
                    key = (o, path)
                    mine = f"{cat}/{name}"
                    if key in owner and owner[key] != mine:
                        errors.append(f"SYS:{path} ({o}) is installed by both "
                                      f"{owner[key]} and {mine}")
                    owner.setdefault(key, mine)
            if files == 0:
                errors.append(f"{cat}/{name}/{rel}: empty release")


def create_info(root, avl, warnings):
    """A new Name (release folders, no Info, no old markers) gets a template
    Info - for both OSes and, in ApolloSoftware-AVL, the Bronze level - and
    a line without version in both default tables. A warning asks to check
    them. Returns the "Cat/Name" made."""
    made = []
    for cat in sorted(c for c in os.listdir(root) if not c.startswith(".") and is_dir(root, c)):
        for name in sorted(os.listdir(os.path.join(root, cat)), key=str.lower):
            npath = os.path.join(root, cat, name)
            if not os.path.isdir(npath):
                continue
            ents = os.listdir(npath)
            if INFO in ents or any(e in OSES or e.startswith("AVL-") for e in ents):
                continue
            if not any(os.path.isdir(os.path.join(npath, e)) for e in ents):
                continue
            lines = [f"; {cat}/{name} - read by ApolloUpdate, see README.md",
                     "OS=" + ",".join(OSES)]
            if avl:
                lines.append("AVL=" + TIERS[0])
            lines += ["OWNER=", "CONTRIBUTORS=", "MINCORE=", "DESCRIPTION="]
            open(os.path.join(npath, INFO), "w", newline="\n").write("\n".join(lines) + "\n")
            for o in OSES:
                add_default(os.path.join(root, f"ApolloUpdate-{o}.default"), cat, name)
            made.append(f"{cat}/{name}")
            warnings.append(f"{cat}/{name}: new Name - made its Info (OS={','.join(OSES)}"
                            + (f", AVL={TIERS[0]}" if avl else "") + ") and an empty line in the "
                            "default tables: check them, fill in OWNER and DESCRIPTION")
    return made


def add_default(path, cat, name):
    """Cat/Name/ (not installed) after the last line of its category"""
    if not os.path.isfile(path):
        return
    lines = open(path, encoding="latin-1").read().splitlines()
    at = len(lines)
    for i, l in enumerate(lines):
        if l.strip().lower().startswith(cat.lower() + "/"):
            at = i + 1
    lines.insert(at, f"{cat}/{name}/")
    open(path, "w", encoding="latin-1", newline="\n").write("\n".join(lines) + "\n")


def check_defaults(root, names, errors):
    """The default tables list exactly the Names tagged for their OS."""
    for o in OSES:
        fn = f"ApolloUpdate-{o}.default"
        path = os.path.join(root, fn)
        want = {(c.lower(), n.lower()): f"{c}/{n}" for c, n, t, r, v in names if o in t}
        if not os.path.isfile(path):
            errors.append(f"{fn}: missing")
            continue
        seen = set()
        for i, line in enumerate(open(path, encoding="ascii", errors="replace").read().splitlines(), 1):
            s = line.strip()
            if not s or s.startswith((";", "#")):
                continue
            parts = s.split("/", 2)
            if len(parts) < 3:
                errors.append(f"{fn}:{i}: not Category/Name/Version")
                continue
            key = (parts[0].lower(), parts[1].lower())
            if key not in want:
                errors.append(f"{fn}:{i}: {parts[0]}/{parts[1]} is not a Name for {o}")
            if key in seen:
                errors.append(f"{fn}:{i}: {parts[0]}/{parts[1]} listed twice")
            seen.add(key)
        for key in sorted(set(want) - seen):
            errors.append(f"{fn}: no line for {want[key]}")


# --------------------------------------------------------------------------
# README table
# --------------------------------------------------------------------------

def cores(info, releases):
    """MINCORE for the table: "11000", or "11000 (0.2: 10900)" """
    per = ["%s: %s" % (r, info["MINCORE." + r]) for r in releases
           if info.get("MINCORE." + r)]
    text = info.get("MINCORE", "")
    if per:
        text = (text + " " if text else "") + "(" + ", ".join(per) + ")"
    return text


def cell(text):
    return text.replace("|", "\\|").replace("\\n", " ")


def table(names, avl=False):
    rows = [MARK_START,
            "<!-- Generated by .github/scripts/releases.py on every push - do not edit by hand. -->",
            "",
            "| Category | Name | Latest | Older releases | ApolloOS | AmigaOS |"
            + (" Level |" if avl else "") + " Owner | Contributors | Min. Core | Description |",
            "|---|---|---|---|:-:|:-:|" + ("---|" if avl else "") + "---|---|---|---|"]
    for cat, name, tags, releases, info in names:
        older = ", ".join(releases[1:])
        rows.append("| %s | %s | **%s** | %s | %s | %s |" % (
            cat, name, releases[0], older,
            "✓" if "ApolloOS" in tags else "", "✓" if "AmigaOS" in tags else "")
            + (" %s |" % (info["AVL"] or "?") if avl else "")
            + " %s | %s | %s | %s |" % (cell(info["OWNER"]), cell(info["CONTRIBUTORS"]),
                                        cores(info, releases),
                                   cell(info["DESCRIPTION"])))
    apollo = sum(1 for n in names if "ApolloOS" in n[2])
    amiga = sum(1 for n in names if "AmigaOS" in n[2])
    rows += ["", f"{len(names)} items: {apollo} for ApolloOS, {amiga} for AmigaOS.", MARK_END]
    return "\n".join(rows)


def index(names, avl=False):
    """ApolloSoftware.index: one line per Name, Cat/Name then TAB separated
    KEY=VALUE fields; the description wrapped, its line breaks as "\\n"."""
    out = [f"; {INDEX} - generated from the Info files by "
           ".github/scripts/releases.py, do not edit",
           "; Category/Name<TAB>OS=...<TAB>AVL=...<TAB>OWNER=...<TAB>CONTRIBUTORS=...<TAB>MINCORE=..."
           "<TAB>MINCORE.<release>=...<TAB>DESCRIPTION=line\\nline"]
    for cat, name, tags, releases, info in names:
        f = [f"{cat}/{name}", "OS=" + ",".join(o for o in OSES if o in tags)]
        if info["AVL"]:
            f.append("AVL=" + info["AVL"])
        if info["OWNER"]:
            f.append("OWNER=" + info["OWNER"])
        if info["CONTRIBUTORS"]:
            f.append("CONTRIBUTORS=" + info["CONTRIBUTORS"])
        if info["MINCORE"]:
            f.append("MINCORE=" + info["MINCORE"])
        for r in releases:
            if info.get("MINCORE." + r):
                f.append(f"MINCORE.{r}=" + info["MINCORE." + r])
        if info["DESCRIPTION"]:
            f.append("DESCRIPTION=" + "\\n".join(wrap(info["DESCRIPTION"])))
        out.append("\t".join(f))
    return "\n".join(out) + "\n"


def write_index(path, names, avl=False):
    new = index(names, avl)
    old = open(path, encoding="ascii").read() if os.path.exists(path) else None
    if new != old:
        open(path, "w", encoding="ascii", newline="\n").write(new)
        return True
    return False


def write_readme(path, names, avl=False):
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else "# ApolloSoftware\n"
    new = table(names, avl)
    if MARK_START in text and MARK_END in text:
        a = text.index(MARK_START)
        b = text.index(MARK_END) + len(MARK_END)
        out = text[:a] + new + text[b:]
    else:
        out = text.rstrip("\n") + "\n\n## Releases\n\n" + new + "\n"
    if out != text:
        open(path, "w", encoding="utf-8").write(out)
        return True
    return False


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--selftest", action="store_true", help="test the release order only")
    ap.add_argument("--check", action="store_true", help="fail on layout errors")
    ap.add_argument("--readme", help="README.md to update")
    ap.add_argument("--index", help=f"{INDEX} to write")
    ap.add_argument("--create-info", action="store_true",
                    help="give a new Name a template Info and default table lines")
    ap.add_argument("--root", default=".", help="top of the repository")
    ap.add_argument("--avl", action="store_true", help="ApolloSoftware-AVL rules (AVL= levels)")
    ap.add_argument("--public", help="AVL: checkout of the public ApolloSoftware to compare with")
    args = ap.parse_args()

    if args.selftest:
        return 0 if selftest() else 1

    made_warnings = []
    if args.create_info:
        create_info(args.root, args.avl, made_warnings)
    names, errors, warnings = scan(args.root, args.avl)
    warnings[:0] = made_warnings
    check_files(args.root, names, errors, warnings)
    check_defaults(args.root, names, errors)
    if args.avl and args.public:
        check_public(args.root, names, args.public, errors)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    report = []
    for w in warnings:
        print("warning:", w)
        print(f"::warning::{w}")
        report.append(f"- ⚠️ {w}")
    for e in errors:
        print("ERROR:", e)
        print(f"::error::{e}")
        report.append(f"- ❌ {e}")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## ApolloSoftware%s check\n\n" % ("-AVL" if args.avl else ""))
            f.write("\n".join(report) + "\n" if report else "All checks passed.\n")

    if args.check and errors:
        print(f"{len(errors)} error(s): README and index not updated")
        return 1

    if args.readme:
        changed = write_readme(args.readme, names, args.avl)
        print(f"{args.readme}: {'updated' if changed else 'unchanged'} ({len(names)} items)")
    if args.index:
        changed = write_index(args.index, names, args.avl)
        print(f"{args.index}: {'updated' if changed else 'unchanged'} ({len(names)} items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
