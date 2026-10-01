#!/usr/bin/env python3
"""
releases.py - checks the ApolloSoftware (or ApolloSoftware-AVL) layout and
writes the releases table in README.md. Run by .github/workflows/releases.yml
on every push, and by hand from the top of the repository:

    python3 .github/scripts/releases.py --selftest
    python3 .github/scripts/releases.py --check --readme README.md
    python3 .github/scripts/releases.py --avl --public ../ApolloSoftware --check --readme README.md

The same script serves both repositories; --avl selects the rules of
ApolloSoftware-AVL (every Name needs exactly one AVL-Bronze / AVL-Silver /
AVL-Gold tag, the minimum membership level), and --public points at a
checkout of the public repository to find SYS: files installed by both.

Layout (the contract with the ApolloUpdate client):

    Category / Name / Release / <copied 1:1 to SYS:>
    Category / Name / ApolloOS        empty marker: Name is for ApolloOS
    Category / Name / AmigaOS         empty marker: Name is for AmigaOS
    Category / Name / AVL-Bronze      ApolloSoftware-AVL only: lowest level
                    / AVL-Silver      that may see the Name
                    / AVL-Gold
    ApolloUpdate-ApolloOS.default     lookup table defaults per OS
    ApolloUpdate-AmigaOS.default

"Latest" must be what ApolloUpdate picks, so version_cmp() below is a
line-by-line port of Repo_VersionCmp() in ApolloUpdate's repo.c, and the
self-test uses the same cases as its hosttest.c. Change both together.
"""

import argparse
import functools
import os
import re
import sys

OSES = ("ApolloOS", "AmigaOS")
TIERS = ("AVL-Bronze", "AVL-Silver", "AVL-Gold")      # low to high
MARK_START = "<!-- releases:start -->"
MARK_END = "<!-- releases:end -->"
MAX_NAME = 30                   # FFS file name limit
TOP_FILES = {"README.md", ".gitattributes", ".gitignore"}
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


def scan(root, avl=False):
    """[(category, name, {os}, [releases newest first], tier)], errors, warnings"""
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
            tags, tiers, releases = set(), [], []
            for e in os.listdir(npath):
                if e in OSES and os.path.isfile(os.path.join(npath, e)):
                    tags.add(e)
                elif e in TIERS and os.path.isfile(os.path.join(npath, e)):
                    tiers.append(e)
                elif os.path.isdir(os.path.join(npath, e)):
                    releases.append(e)
                else:
                    errors.append(f"{cat}/{name}/{e}: only ApolloOS / AmigaOS"
                                  + (" / AVL-* " if avl else " ") +
                                  "markers and release folders belong in a Name folder")
            if not releases:
                errors.append(f"{cat}/{name}: no release folder")
                continue
            if not tags:
                errors.append(f"{cat}/{name}: no OS tag - add an empty ApolloOS and/or "
                              "AmigaOS file (ApolloUpdate does not show it)")
            tier = None
            if avl:
                if len(tiers) != 1:
                    errors.append(f"{cat}/{name}: needs exactly one of {', '.join(TIERS)} "
                                  f"(has {', '.join(sorted(tiers)) or 'none'})")
                else:
                    tier = tiers[0]
            elif tiers:
                errors.append(f"{cat}/{name}: {tiers[0]} tag - AVL entries belong in "
                              "ApolloSoftware-AVL, not in the public repository")
            names.append((cat, name, tags, newest_first(releases), tier))
    return names, errors, warnings


def sys_paths(root, names):
    """{(os, lower-case SYS path): "Cat/Name"} for every release of every Name"""
    owner = {}
    for cat, name, tags, releases, tier in names:
        for rel in releases:
            rpath = os.path.join(root, cat, name, rel)
            for dirpath, dirs, fns in os.walk(rpath):
                for fn in fns:
                    if not JUNK.match(fn):
                        sub = os.path.relpath(os.path.join(dirpath, fn), rpath)
                        for o in tags:
                            owner.setdefault((o, sub.lower()), f"{cat}/{name}")
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
                for fn in fns:
                    if JUNK.match(fn):
                        continue
                    files += 1
                    sub = os.path.relpath(os.path.join(dirpath, fn), rpath)
                    if os.sep not in sub:
                        warnings.append(f"{cat}/{name}/{rel}/{fn}: lands in the root of SYS:")
                    for o in tags:
                        key = (o, sub.lower())
                        mine = f"{cat}/{name}"
                        if key in owner and owner[key] != mine:
                            errors.append(f"SYS:{sub} ({o}) is installed by both "
                                          f"{owner[key]} and {mine}")
                        owner.setdefault(key, mine)
            if files == 0:
                errors.append(f"{cat}/{name}/{rel}: empty release")


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

def table(names, avl=False):
    rows = [MARK_START,
            "<!-- Generated by .github/scripts/releases.py on every push - do not edit by hand. -->",
            "",
            "| Category | Name | Latest | Older releases | ApolloOS | AmigaOS |" + (" Level |" if avl else ""),
            "|---|---|---|---|:-:|:-:|" + ("---|" if avl else "")]
    for cat, name, tags, releases, tier in names:
        older = ", ".join(releases[1:])
        rows.append("| %s | %s | **%s** | %s | %s | %s |" % (
            cat, name, releases[0], older,
            "✓" if "ApolloOS" in tags else "", "✓" if "AmigaOS" in tags else "")
            + (" %s |" % (tier[4:] if tier else "?") if avl else ""))
    apollo = sum(1 for n in names if "ApolloOS" in n[2])
    amiga = sum(1 for n in names if "AmigaOS" in n[2])
    rows += ["", f"{len(names)} items: {apollo} for ApolloOS, {amiga} for AmigaOS.", MARK_END]
    return "\n".join(rows)


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
    ap.add_argument("--root", default=".", help="top of the repository")
    ap.add_argument("--avl", action="store_true", help="ApolloSoftware-AVL rules (AVL-* tags)")
    ap.add_argument("--public", help="AVL: checkout of the public ApolloSoftware to compare with")
    args = ap.parse_args()

    if args.selftest:
        return 0 if selftest() else 1

    names, errors, warnings = scan(args.root, args.avl)
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
        print(f"{len(errors)} error(s): README not updated")
        return 1

    if args.readme:
        changed = write_readme(args.readme, names, args.avl)
        print(f"{args.readme}: {'updated' if changed else 'unchanged'} ({len(names)} items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
