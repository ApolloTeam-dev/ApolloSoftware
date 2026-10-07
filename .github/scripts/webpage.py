"""
webpage.py - the ApolloSoftware web page, published by GitHub Pages from
.github/workflows/releases.yml (releases.py --site DIR):

    https://apolloteam-dev.github.io/ApolloSoftware/

Made for the Amiga browsers first - IBrowse, AWeb, NetSurf - on a 1280x720
screen, and fine in any other:

- no JavaScript: every sort order and filter is a page of its own, made
  here, and the controls are plain links between them
- the layout is HTML 3.2 tables with bgcolor / cellpadding / width; a
  little CSS1 refines it where a browser has it, nothing depends on it
- ISO-8859-1, no characters beyond it; the logo is a PNG on its own dark
  band (no SVG)
- the colours of the ApolloCD32 game list: #f6f6f4 page, white rows,
  #7a5cff accent
"""

import html
import os
import shutil

ACCENT = "#7a5cff"
PAGE = "#f6f6f4"
CARD = "#ffffff"
ALT = "#fbfaff"
LINE = "#e2e2df"
DIM = "#6b6b70"
INK = "#1c1c1e"
HEAD = "#131417"            # the logo band, as in the ApolloUpdate window
OLDER = 3                   # older releases shown before "... (n more)"

OSES = (("all", "All"), ("apolloos", "ApolloOS"), ("amigaos", "AmigaOS"))
SORTS = (("category", "Category"), ("name", "Name"), ("owner", "Owner"))

CSS = """
body { margin: 0; background: %(PAGE)s; color: %(INK)s;
       font-family: Helvetica, Arial, sans-serif; font-size: 13px; }
td, th { font-family: Helvetica, Arial, sans-serif; font-size: 13px; }
a { color: %(ACCENT)s; text-decoration: none; }
a:hover { text-decoration: underline; }
.dim { color: %(DIM)s; }
.small { font-size: 11px; }
.th { color: %(DIM)s; font-size: 11px; font-weight: bold; text-transform: uppercase;
      letter-spacing: 1px; }
.th a { color: %(DIM)s; }
.on, .on a { color: #ffffff; font-weight: bold; }
.dl, .dl a { color: #ffffff; font-weight: bold; font-size: 14px; }
h1 { font-size: 20px; margin: 0; }
""" % dict(PAGE=PAGE, INK=INK, ACCENT=ACCENT, DIM=DIM)


def esc(s):
    return html.escape(s or "", quote=True).encode("latin-1", "replace").decode("latin-1")


def page_name(os_key, cat_key, sort_key):
    if (os_key, cat_key, sort_key) == ("all", "all", "category"):
        return "index.html"
    return f"{os_key}-{cat_key.lower()}-{sort_key}.html"


def chips(label, items, active, link):
    """One row of filter choices: the chosen one a purple cell, the others links."""
    cells = [f'<td nowrap class="dim"><b>{esc(label)}</b>&nbsp;</td>']
    for key, text in items:
        if key == active:
            cells.append(f'<td nowrap bgcolor="{ACCENT}" class="on">&nbsp;{esc(text)}&nbsp;</td>')
        else:
            cells.append(f'<td nowrap bgcolor="{CARD}">&nbsp;<a href="{link(key)}">'
                         f'{esc(text)}</a>&nbsp;</td>')
        cells.append('<td width="4"></td>')
    return ('<table border="0" cellspacing="0" cellpadding="3"><tr>'
            + "".join(cells) + "</tr></table>")


def older(releases):
    rest = releases[1:]
    if len(rest) <= OLDER:
        return esc(", ".join(rest))
    return (esc(", ".join(rest[:OLDER]))
            + f' <span class="dim">... ({len(rest) - OLDER} more)</span>')


def build(names, outdir, logo, package, cores, version, stamp):
    """names: [(cat, name, {os}, [releases newest first], info)] as releases.py
    reads them; logo, package: files copied next to the pages (package may
    be None); cores(info, releases) -> the Min. Core text; version: of the
    ApolloUpdate in the package. Returns the number of pages written."""
    os.makedirs(outdir, exist_ok=True)
    shutil.copyfile(logo, os.path.join(outdir, "ApolloUpdate-logo.png"))
    size = 0
    if package and os.path.exists(package):
        shutil.copyfile(package, os.path.join(outdir, "ApolloUpdate.lha"))
        size = os.path.getsize(package)
    with open(os.path.join(outdir, "style.css"), "w", encoding="latin-1") as f:
        f.write(CSS)

    cats = sorted({n[0] for n in names}, key=str.lower)
    cat_items = [("all", "All")] + [(c, c) for c in cats]
    written = 0
    for os_key, os_text in OSES:
        for cat_key, cat_text in cat_items:
            for sort_key, sort_text in SORTS:
                rows = [n for n in names
                        if (os_key == "all" or os_text in n[2])
                        and (cat_key == "all" or n[0] == cat_key)]
                if sort_key == "name":
                    rows.sort(key=lambda n: (n[1].lower(), n[0].lower()))
                elif sort_key == "owner":
                    rows.sort(key=lambda n: ((n[4].get("OWNER") or "~").lower(), n[1].lower()))
                else:
                    rows.sort(key=lambda n: (n[0].lower(), n[1].lower()))
                text = one_page(names, rows, os_key, cat_key, sort_key, cat_items,
                                size, cores, version, stamp)
                with open(os.path.join(outdir, page_name(os_key, cat_key, sort_key)), "w",
                          encoding="latin-1", newline="\n") as f:
                    f.write(text)
                written += 1
    return written


def one_page(names, rows, os_key, cat_key, sort_key, cat_items, size, cores, version, stamp):
    def link(o=os_key, c=cat_key, s=sort_key):
        return page_name(o, c, s)

    out = ['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">',
           "<html><head>",
           '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">',
           "<title>ApolloUpdate - ApolloSoftware Library</title>",
           '<link rel="stylesheet" type="text/css" href="style.css">',
           "</head>",
           f'<body bgcolor="{PAGE}" text="{INK}" link="{ACCENT}" vlink="{ACCENT}" '
           'leftmargin="0" topmargin="0" marginwidth="0" marginheight="0">']

    # the logo band, the download on its right
    dl = ""
    if size:
        dl = (f'<table border="0" cellspacing="0" cellpadding="8"><tr>'
              f'<td bgcolor="{ACCENT}" class="dl" nowrap>'
              f'<a href="ApolloUpdate.lha">Download ApolloUpdate {esc(version)}</a></td></tr></table>'
              f'<font color="#a9a9a8" class="small">ApolloUpdate.lha, {(size + 1023) // 1024} KB'
              f' - unpack with LhA, start ApolloUpdate</font>')
    out.append(f'<table width="100%" border="0" cellspacing="0" cellpadding="12" bgcolor="{HEAD}">'
               f'<tr><td valign="middle"><img src="ApolloUpdate-logo.png" width="545" height="44" '
               f'alt="ApolloUpdate" border="0"></td>'
               f'<td align="right" valign="middle">{dl}</td></tr></table>')

    # welcome
    out.append(f'<table width="100%" border="0" cellspacing="0" cellpadding="12" bgcolor="{CARD}">'
               '<tr><td><h1>Welcome to ApolloUpdate</h1>'
               '<span class="dim">Current status for ApolloSoftware Library</span></td>'
               f'<td align="right" valign="bottom" class="dim small">{esc(stamp)}</td></tr></table>')
    out.append(f'<table width="100%" border="0" cellspacing="0" cellpadding="0">'
               f'<tr><td bgcolor="{LINE}" height="1"></td></tr></table>')

    # filters
    out.append('<table width="100%" border="0" cellspacing="0" cellpadding="10"><tr><td>')
    out.append(chips("OS:", OSES, os_key, lambda k: link(o=k)))
    out.append(chips("Category:", cat_items, cat_key, lambda k: link(c=k)))
    out.append(f'<span class="dim small">{len(rows)} of {len(names)} items'
               f' - click a column title to sort</span>')
    out.append("</td></tr></table>")

    # the table
    cols = [("Category", "category", ""), ("Name", "name", ""), ("Latest", None, ""),
            ("Older releases", None, ""), ("ApolloOS", None, "center"),
            ("AmigaOS", None, "center"), ("Owner", "owner", ""),
            ("Contributors", None, ""), ("Min. Core", None, ""), ("Description", None, "")]
    out.append('<table width="100%" border="0" cellspacing="0" cellpadding="10"><tr><td>')
    out.append(f'<table width="100%" border="0" cellspacing="1" cellpadding="6" bgcolor="{LINE}">')
    head = []
    for title, key, align in cols:
        al = f' align="{align}"' if align else ""
        if key and key == sort_key:
            head.append(f'<td nowrap bgcolor="{ACCENT}" class="on"{al}>{esc(title.upper())}</td>')
        elif key:
            head.append(f'<td nowrap bgcolor="{PAGE}" class="th"{al}>'
                        f'<a href="{link(s=key)}">{esc(title.upper())}</a></td>')
        else:
            head.append(f'<td nowrap bgcolor="{PAGE}" class="th"{al}>{esc(title.upper())}</td>')
    out.append("<tr>" + "".join(head) + "</tr>")
    for i, (cat, name, tags, releases, info) in enumerate(rows):
        bg = CARD if i % 2 == 0 else ALT
        out.append(f'<tr bgcolor="{bg}">'
                   f'<td nowrap class="dim">{esc(cat)}</td>'
                   f'<td nowrap><b>{esc(name)}</b></td>'
                   f'<td nowrap><b>{esc(releases[0])}</b></td>'
                   f'<td>{older(releases)}</td>'
                   f'<td align="center">{"Yes" if "ApolloOS" in tags else "-"}</td>'
                   f'<td align="center">{"Yes" if "AmigaOS" in tags else "-"}</td>'
                   f'<td nowrap>{esc(info.get("OWNER") or "")}</td>'
                   f'<td>{esc(info.get("CONTRIBUTORS") or "")}</td>'
                   f'<td>{esc(cores(info, releases))}</td>'
                   f'<td>{esc(info.get("DESCRIPTION") or "").replace(chr(92) + "n", " ")}</td>'
                   "</tr>")
    if not rows:
        out.append(f'<tr bgcolor="{CARD}"><td colspan="{len(cols)}" class="dim">'
                   "No entries match these filters</td></tr>")
    out.append("</table></td></tr></table>")

    out.append('<table width="100%" border="0" cellspacing="0" cellpadding="10"><tr>'
               '<td class="dim small">Generated from the '
               '<a href="https://github.com/ApolloTeam-dev/ApolloSoftware">ApolloSoftware</a>'
               ' repository on every change. Members of Apollo Vampire Lair see more in '
               'ApolloUpdate itself.</td></tr></table>')
    out.append("</body></html>")
    return "\n".join(out) + "\n"
