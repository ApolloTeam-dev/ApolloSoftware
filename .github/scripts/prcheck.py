#!/usr/bin/env python3
"""
prcheck.py - the check of a Pull Request on ApolloSoftware (or
ApolloSoftware-AVL): the ApolloSoftware-Manager and anyone else propose
changes as Pull Requests, a Maintainer merges them. Run by
.github/workflows/prcheck.yml with the base of the Pull Request checked out
in .base:

    python3 .github/scripts/prcheck.py --base .base [--avl [--public .public]]

First the full layout check of releases.py on the proposed tree (as the
push workflow does after the merge, but without making a missing Info file:
a Pull Request brings its own). Then what only a comparison with the base
shows:

  errors     generated files edited (README.md, ApolloSoftware.index,
             ApolloUpdate.lha: the workflow writes them after the merge);
             a version folder with a space; an ApolloROM version that is
             not Rx.y-RCz (optionally -beta); a file over 95 MB (GitHub
             takes 100 MB at most)
  warnings   a SYS: drawer no Name used before (C, Devs, Libs ...); a file
             that lands elsewhere than in the newest release before it
             (Devs/x.device after Devs/Networks/x.device); a new version
             lower than the newest; an existing release changed (normally a
             new version is added instead); a whole Name or its newest
             release removed; a file over 50 MB; changes in .github

The result is the job summary: the errors and warnings, what the Pull
Request adds, changes and removes, and the README rows as they will be.
The script shares the rules of releases.py (same folder, imported).
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import releases as R                    # noqa: E402

GENERATED = {"README.md", R.INDEX, R.PACKAGE}
WARN_SIZE = 50 * 1024 * 1024
MAX_SIZE = 95 * 1024 * 1024
APOLLOROM_VER = re.compile(r"^R\d+\.\d+(-RC\d+)?(-beta)?$")
# the drawers of a standard SYS:, plus the ROM module drawers
SYS_DRAWERS = {"c", "classes", "devs", "expansion", "fonts", "help", "l", "libs", "locale",
               "prefs", "rexxc", "s", "storage", "system", "tools", "utilities", "wbstartup",
               "amigarom", "apollorom"}


def tree(root, avl, public=None):
    """{(cat, name): {"releases": [newest first], "info": {...}, "files":
    {rel: {sub: size}}}}, errors, warnings - releases.py's scan and checks"""
    names, errors, warnings = R.scan(root, avl)
    R.check_files(root, names, errors, warnings)
    R.check_modules(root, names, errors)
    if avl and public:
        R.check_public(root, names, public, errors)
    out = {}
    for cat, name, tags, rels, info in names:
        files = {}
        for rel in rels:
            files[rel] = {sub: os.path.getsize(os.path.join(root, cat, name, rel, sub))
                          for sub, key in R.release_files(root, cat, name, rel)}
        out[(cat, name)] = {"releases": rels, "info": info, "files": files, "row": (cat, name, tags, rels, info)}
    return out, names, errors, warnings


def changed_top(base, head):
    """Top-level files and .github files that differ between base and head"""
    out = []
    for f in sorted(GENERATED):
        a, b = os.path.join(base, f), os.path.join(head, f)
        if os.path.isfile(a) != os.path.isfile(b) or (
                os.path.isfile(a) and open(a, "rb").read() != open(b, "rb").read()):
            out.append(f)
    gh = []
    for root in (base, head):
        for dirpath, dirs, fns in os.walk(os.path.join(root, ".github")):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in fns:
                gh.append(os.path.relpath(os.path.join(dirpath, fn), root))
    for f in sorted(set(gh)):
        a, b = os.path.join(base, f), os.path.join(head, f)
        if not (os.path.isfile(a) and os.path.isfile(b) and open(a, "rb").read() == open(b, "rb").read()):
            out.append(f)
    return out


def drawers_in(t):
    """Lower-case first drawers of the SYS: paths used by the Names of t"""
    used = set()
    for (cat, name), n in t.items():
        if cat in R.ROM_CATS:
            continue
        for rel, files in n["files"].items():
            for sub in files:
                if os.sep in sub:
                    used.add(sub.split(os.sep)[0].lower())
    return used


def compare(base, head, errors, warnings, changes):
    known = SYS_DRAWERS | drawers_in(base)
    for key in sorted(set(base) | set(head), key=lambda k: (k[0].lower(), k[1].lower())):
        cat, name = key
        b, h = base.get(key), head.get(key)
        label = f"{cat}/{name}"
        if not h:
            changes.append(f"removed: **{label}** (all of it: {', '.join(b['releases'])})")
            warnings.append(f"{label}: the whole item is removed")
            continue
        if not b:
            changes.append(f"new item: **{label}** {', '.join(h['releases'])}")
        else:
            gone = [r for r in b["releases"] if r not in h["releases"]]
            for r in gone:
                changes.append(f"removed: {label} **{r}**")
            if b["releases"] and b["releases"][0] in gone:
                warnings.append(f"{label}: its newest release {b['releases'][0]} is removed")
            if b["info"] != h["info"]:
                diff = [k for k in sorted(set(b["info"]) | set(h["info"])) if b["info"].get(k) != h["info"].get(k)]
                changes.append(f"Info changed: {label} ({', '.join(diff)})")

        newest_before = b["releases"][0] if b and b["releases"] else None
        before_paths = {}           # file name -> where the newest release had it
        if newest_before:
            for sub in b["files"][newest_before]:
                before_paths.setdefault(os.path.basename(sub).lower(), sub)

        for rel in h["releases"]:
            files = h["files"][rel]
            new = not b or rel not in b["releases"]
            rlabel = f"{label}/{rel}"
            if " " in rel:
                errors.append(f"{rlabel}: a version has no spaces")
            if cat == "ROM" and name == "ApolloROM" and not APOLLOROM_VER.match(rel):
                errors.append(f"{rlabel}: an ApolloROM version is Rx.y-RCz (e.g. R9.6-RC06, R9.6)")
            if new:
                if b:
                    changes.append(f"new version: {label} **{rel}**")
                if newest_before and R.version_cmp(rel, newest_before) < 0:
                    warnings.append(f"{rlabel}: lower than the newest version {newest_before}")
            elif b["files"][rel] != files:
                changes.append(f"changed: {rlabel} (files of an existing release)")
                warnings.append(f"{rlabel}: an existing release is changed - normally a new "
                                "version is added instead")
            if not new and b["files"][rel] == files:
                continue
            for sub, size in sorted(files.items()):
                flabel = f"{rlabel}/{sub}"
                if size > MAX_SIZE:
                    errors.append(f"{flabel}: {size // (1024 * 1024)} MB - GitHub takes at most 100 MB")
                elif size > WARN_SIZE:
                    warnings.append(f"{flabel}: {size // (1024 * 1024)} MB - a big file")
                if cat in R.ROM_CATS:
                    continue
                if os.sep in sub:
                    top = sub.split(os.sep)[0]
                    if top.lower() not in known:
                        warnings.append(f"{flabel}: SYS:{top}/ is a drawer no item used before")
                was = before_paths.get(os.path.basename(sub).lower())
                if was and was.lower() != sub.lower() and rel != newest_before:
                    warnings.append(f"{flabel}: lands in SYS:{os.path.dirname(sub) or ''} - "
                                    f"{newest_before} had it in SYS:{os.path.dirname(was) or ''}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--base", required=True, help="checkout of the Pull Request's base")
    ap.add_argument("--root", default=".", help="the proposed tree")
    ap.add_argument("--avl", action="store_true", help="ApolloSoftware-AVL rules")
    ap.add_argument("--public", help="AVL: checkout of the public ApolloSoftware")
    args = ap.parse_args()

    head, hnames, errors, warnings = tree(args.root, args.avl, args.public)
    base, bnames, berr, bwarn = tree(args.base, args.avl)
    changes = []
    for f in changed_top(args.base, args.root):
        if f in GENERATED:
            errors.append(f"{f}: generated - the workflow writes it after the merge; "
                          "leave it out of the Pull Request")
        else:
            warnings.append(f"{f}: a workflow or script changes - review it with care")
    compare(base, head, errors, warnings, changes)

    rows = [head[k]["row"] for k in sorted(head) if k not in base or base[k]["info"] != head[k]["info"]
            or base[k]["releases"] != head[k]["releases"]]

    for w in warnings:
        print("warning:", w)
        print(f"::warning::{w}")
    for e in errors:
        print("ERROR:", e)
        print(f"::error::{e}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## Pull Request check%s\n\n" % (" (ApolloSoftware-AVL)" if args.avl else ""))
            f.write(("❌ %d error(s) - this cannot be merged as it is\n\n" % len(errors)) if errors
                    else "✅ No errors - a Maintainer may merge it\n\n")
            if errors or warnings:
                f.write("\n".join([f"- ❌ {e}" for e in errors] + [f"- ⚠️ {w}" for w in warnings]) + "\n\n")
            f.write("### Changes\n\n")
            f.write("\n".join(f"- {c}" for c in changes) + "\n\n" if changes else "None in the software folders.\n\n")
            if rows:
                f.write("### README rows after the merge\n\n")
                table = [l for l in R.table(rows, args.avl).splitlines() if l.startswith("|")]
                f.write("\n".join(table) + "\n")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s), {len(changes)} change(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
