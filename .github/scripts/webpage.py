"""
webpage.py - the ApolloSoftware web page, published by GitHub Pages from
.github/workflows/releases.yml (releases.py --site DIR):

    https://apolloteam-dev.github.io/ApolloSoftware/

Made for the Amiga browsers first - IBrowse, AWeb, NetSurf - on a 1280x720
screen, and fine in any other:

- no JavaScript: every sort order and filter is a page of its own, made
  here, and the controls are plain links between them
- the layout is HTML 3.2 tables with bgcolor / cellpadding / width, and
  bold and colours as <b> and <font color>: IBrowse 3.0 has no CSS. The
  little CSS here only refines it where a browser has it
- ISO-8859-1, no characters beyond it; the logo and the download icon
  are PNGs on the dark band (no SVG, no transparency)
- the typeface is Inter (SIL OFL, published beside it) for browsers with
  web fonts. IBrowse 3.0 ignores both CSS and <font face> (fonttest.html
  showed every name in its default serif font): there the font is the
  one set in its own preferences
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
CHIPLINE = "#c4c4c0"        # the hairline around a filter box
DIM = "#6b6b70"
INK = "#1c1c1e"
HEAD = "#131417"            # the logo band, as in the ApolloUpdate window

# the categories by priority: the filter and the "by category" order
CATEGORY_ORDER = ("Cores", "ROM", "Resources", "Drivers", "Libraries", "FileSystems",
                  "Tools", "Icons")


def cat_rank(cat):
    """Sort key of a category: its place in CATEGORY_ORDER, any other after
    them by name"""
    for i, c in enumerate(CATEGORY_ORDER):
        if c.lower() == cat.lower():
            return (i, "")
    return (len(CATEGORY_ORDER), cat.lower())


OSES = (("all", "All"), ("apolloos", "ApolloOS"), ("amigaos", "AmigaOS"))
SORTS = (("category", "Category"), ("name", "Name"))

FONTS = ('Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
         '"Helvetica Neue", "DejaVu Sans", Helvetica, Arial, sans-serif')
SITE_FILES = ("ApolloUpdate-logo.png", "ApolloUpdate-icon.png", "Offline-icon.png", "Inter-latin.woff2",
              "Inter-LICENSE.txt")

CSS = """
@font-face { font-family: Inter; font-style: normal; font-weight: 400 700;
             font-display: swap; src: url(Inter-latin.woff2) format("woff2"); }
body { margin: 0; background: %(PAGE)s; color: %(INK)s;
       font-family: %(FONTS)s; font-size: 14px;
       font-feature-settings: "calt" 0; }      /* Inter: 680x0 stays x, not a times sign */
td, th { font-family: %(FONTS)s; font-size: 14px; font-feature-settings: "calt" 0; }
a { color: %(ACCENT)s; text-decoration: none; }
a:hover { text-decoration: underline; }
.dim { color: %(DIM)s; }
.grid td { padding: 3px 8px; }          /* compact rows; more room at the sides */
.small { font-size: 11px; }
.th { color: #ffffff; font-weight: bold; }
.th a { color: #ffffff; text-decoration: underline; }
.on, .on a { color: #ffffff; font-weight: bold; }
.dl, .dl a { color: #ffffff; font-weight: 600; font-size: 15px; }
""" % dict(PAGE=PAGE, INK=INK, ACCENT=ACCENT, DIM=DIM, FONTS=FONTS)


def pixel(colour):
    """A 1x1 PNG of that colour, a spacer IBrowse keeps at its size"""
    import struct, zlib
    rgb = bytes(int(colour[i:i + 2], 16) for i in (1, 3, 5))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\0" + rgb)) + chunk(b"IEND", b""))


def esc(s):
    return html.escape(s or "", quote=True).encode("latin-1", "replace").decode("latin-1")


def page_name(os_key, cat_key, sort_key):
    if (os_key, cat_key, sort_key) == ("all", "all", "category"):
        return "index.html"
    return f"{os_key}-{cat_key.lower()}-{sort_key}.html"


def chip(content, bg):
    """A filter box with a 1 pixel hairline: a table whose 1 pixel cell
    spacing shows its grey background around the one cell"""
    return (f'<table border="0" cellspacing="1" cellpadding="2" bgcolor="{CHIPLINE}"><tr>'
            f'<td nowrap bgcolor="{bg}">&nbsp;{content}&nbsp;</td></tr></table>')


def chips(label, items, active, link):
    """One row of filter choices: the chosen one a purple box, the others links."""
    cells = [f'<td nowrap class="dim"><b>{esc(label)}</b>&nbsp;</td>']
    for key, text in items:
        if key == active:
            cells.append('<td class="on">' + chip(f'<font color="#ffffff"><b>{esc(text)}</b></font>',
                                                  ACCENT) + '</td>')
        else:
            cells.append('<td>' + chip(f'<a href="{link(key)}">{esc(text)}</a>', CARD) + '</td>')
        cells.append('<td nowrap>&nbsp;</td>')
    return ('<table border="0" cellspacing="0" cellpadding="0"><tr>'
            + "".join(cells) + "</tr></table>")


def release_beta(releases):
    """(newest release, newest beta newer than it) of releases newest first;
    "-" for none. A release folder ending in -beta is a beta."""
    rel = next((r for r in releases if not r.endswith("-beta")), "-")
    beta = "-"
    for r in releases:
        if not r.endswith("-beta"):
            break                       # the release comes first: no newer beta
        beta = r
        break
    return rel, beta


def shown(releases):
    """the version the overviews describe: the newest release, else the beta"""
    rel, beta = release_beta(releases)
    return rel if rel != "-" else beta


def min_core(info, latest):
    """The minimal core of the latest release: its own MINCORE.<release>,
    else the Name's MINCORE; empty when neither applies."""
    return info.get("MINCORE." + latest) or info.get("MINCORE") or ""


def build(names, outdir, assets, package, version, stamp, downloads=None, offline=0):
    """names: [(cat, name, {os}, [releases newest first], info)] as releases.py
    reads them; assets: the folder with SITE_FILES (.github/site), copied
    next to the pages, as is package (may be None); version: of the
    ApolloUpdate in the package; downloads: {(cat, name, release): link}
    for the Release and Beta cells (releases.py write_downloads); offline:
    the size of ApolloSoftware-Offline.lha beside the pages, 0 for none.
    Returns the number of pages written."""
    os.makedirs(outdir, exist_ok=True)
    for f in SITE_FILES:
        shutil.copyfile(os.path.join(assets, f), os.path.join(outdir, f))
    size = 0
    if package and os.path.exists(package):
        shutil.copyfile(package, os.path.join(outdir, "ApolloUpdate.lha"))
        size = os.path.getsize(package)
    with open(os.path.join(outdir, "style.css"), "w", encoding="latin-1") as f:
        f.write(CSS)
    with open(os.path.join(outdir, "px.png"), "wb") as f:
        f.write(pixel(PAGE))

    with open(os.path.join(outdir, "fonttest.html"), "w", encoding="latin-1", newline="\n") as f:
        f.write(font_test())

    cats = sorted({n[0] for n in names}, key=cat_rank)
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
                else:
                    rows.sort(key=lambda n: (cat_rank(n[0]), n[1].lower()))
                text = one_page(names, rows, os_key, cat_key, sort_key, cat_items,
                                size, version, stamp, downloads or {}, offline)
                with open(os.path.join(outdir, page_name(os_key, cat_key, sort_key)), "w",
                          encoding="latin-1", newline="\n") as f:
                    f.write(text)
                written += 1
    return written


def one_page(names, rows, os_key, cat_key, sort_key, cat_items, size, version, stamp, downloads, offline=0):
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

    # the logo band, the download (icon and words) on its right
    dl = ""
    if size:
        tip = f"ApolloUpdate {esc(version)}, ApolloUpdate.lha, {(size + 1023) // 1024} KB"
        dl = ('<table border="0" cellspacing="0" cellpadding="0"><tr>'
              f'<td valign="middle"><a href="ApolloUpdate.lha"><img src="ApolloUpdate-icon.png" '
              f'width="48" height="48" border="0" alt="Download" title="{tip}"></a></td>'
              f'<td width="10"></td><td valign="middle" class="dl" nowrap>'
              '<table border="0" cellspacing="0" cellpadding="0">'
              f'<tr><td nowrap><a href="ApolloUpdate.lha" title="{tip}">'
              f'<font color="#ffffff"><b>Download, Unpack and Execute</b></font></a></td></tr>'
              '<tr><td height="6"></td></tr>'                  # a little air between the lines
              f'<tr><td nowrap><font color="#a9a9a8"><b>{esc(stamp)}</b></font></td></tr>'
              '</table></td>'
              '</tr></table>')
    if offline:
        otip = (f"ApolloSoftware-Offline.lha, {(offline + 524288) // 1048576} MB: every Release and Beta, "
                "for ApolloUpdate without a network")
        off = ('<table border="0" cellspacing="0" cellpadding="0"><tr>'
               f'<td valign="middle"><a href="ApolloSoftware-Offline.lha"><img src="Offline-icon.png" '
               f'width="48" height="48" border="0" alt="Offline Archive" title="{otip}"></a></td>'
               f'<td width="10"></td><td valign="middle" class="dl" nowrap>'
               '<table border="0" cellspacing="0" cellpadding="0">'
               f'<tr><td nowrap><a href="ApolloSoftware-Offline.lha" title="{otip}">'
               f'<font color="#ffffff"><b>Offline Archive</b></font></a></td></tr>'
               '<tr><td height="6"></td></tr>'
               '<tr><td nowrap><font color="#a9a9a8"><b>(Only if you have NO network)</b></font></td></tr>'
               '</table></td></tr></table>')
        dl = ('<table border="0" cellspacing="0" cellpadding="0"><tr>'
              f'<td valign="middle">{off}</td><td width="24"></td><td valign="middle">{dl}</td></tr></table>')
    out.append(f'<table width="100%" border="0" cellspacing="0" cellpadding="12" bgcolor="{HEAD}">'
               f'<tr><td valign="middle"><img src="ApolloUpdate-logo.png" width="545" height="44" '
               f'alt="ApolloUpdate" border="0"></td>'
               f'<td align="right" valign="middle">{dl}</td></tr></table>')

    # filters
    # below the band: 10 pixels left and right. No empty spacer rows: IBrowse
    # gives an empty cell a whole text line, whatever its height says.
    out.append('<table width="100%" border="0" cellspacing="0" cellpadding="0"><tr>'
               '<td width="10"></td><td>')

    # one pixel more above the filters than the padding gives: an image, as
    # IBrowse makes an empty cell a whole text line high
    out.append('<table border="0" cellspacing="0" cellpadding="0"><tr><td>'
               '<img src="px.png" width="1" height="1" alt="" border="0"></td></tr></table>')

    # filters: OS and Category on one line, the count on the right; the
    # padding gives the same small space above and below in every browser
    out.append('<table width="100%" border="0" cellspacing="0" cellpadding="3"><tr>')
    out.append('<td valign="middle" nowrap>' + chips("OS:", OSES, os_key, lambda k: link(o=k)) + '</td>')
    out.append('<td nowrap>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>')      # gap; an empty cell gets squeezed
    out.append('<td valign="middle" nowrap>'
               + chips("Category:", cat_items, cat_key, lambda k: link(c=k)) + '</td>')
    out.append(f'<td align="right" valign="middle" class="dim small" nowrap width="100%">'
               f'{len(rows)} of {len(names)} items</td>')
    out.append("</tr></table>")

    # the table
    cols = [("Category", "category", ""), ("Name", "name", ""), ("Release", None, ""),
            ("Beta", None, ""),
            ("ApolloOS", None, "center"), ("AmigaOS", None, "center"),
            ("Minimal Core", None, ""), ("Description", None, "")]
    out.append(f'<table class="grid" width="100%" border="0" cellspacing="1" cellpadding="3" '
               f'bgcolor="{LINE}">')
    head = []
    for title, key, align in cols:
        al = f' align="{align}"' if align else ""
        # all white on black; a title to sort by is an underlined link,
        # the one sorted by now is not (clicking it would change nothing)
        if key and key != sort_key:
            head.append(f'<td nowrap bgcolor="{HEAD}" class="th"{al}>'
                        f'<a href="{link(s=key)}"><font color="#ffffff"><b><u>{esc(title)}'
                        f'</u></b></font></a></td>')
        else:
            head.append(f'<td nowrap bgcolor="{HEAD}" class="th"{al}>'
                        f'<font color="#ffffff"><b>{esc(title)}</b></font></td>')
    out.append("<tr>" + "".join(head) + "</tr>")
    def version_cell(cat, name, rel, bold):
        # a version links to its download (an .lha, or the core / ROM file)
        text = f"<b>{esc(rel)}</b>" if bold else esc(rel)
        href = downloads.get((cat, name, rel))
        if href:
            text = f'<a href="{esc(href)}" title="Download {esc(name)} {esc(rel)}">{text}</a>'
        return f"<td nowrap>{text}</td>"

    for i, (cat, name, tags, releases, info) in enumerate(rows):
        bg = CARD if i % 2 == 0 else ALT
        rel, beta = release_beta(releases)
        out.append(f'<tr bgcolor="{bg}">'
                   f'<td nowrap class="dim">{esc(cat)}</td>'
                   f'<td nowrap><b>{esc(name)}</b></td>'
                   + version_cell(cat, name, rel, True) + version_cell(cat, name, beta, False) +
                   f'<td align="center">{"Yes" if "ApolloOS" in tags else "-"}</td>'
                   f'<td align="center">{"Yes" if "AmigaOS" in tags else "-"}</td>'
                   f'<td nowrap>{esc(min_core(info, shown(releases)))}</td>'
                   f'<td>{esc(info.get("DESCRIPTION") or "").replace(chr(92) + "n", " ")}</td>'
                   "</tr>")
    if not rows:
        out.append(f'<tr bgcolor="{CARD}"><td colspan="{len(cols)}" class="dim">'
                   "No entries match these filters</td></tr>")
    out.append("</table><br>")
    out.append('</td><td width="10"></td></tr></table>')

    out.append("</body></html>")
    return "\n".join(out) + "\n"


# fonttest.html (not linked): which <font face> names a browser resolves -
# each row asks for one name; a row in the default serif font is a name
# the browser did not find
FONT_TESTS = ("Inter", "Work Sans Regular", "Work Sans", "WorkSans", "Vera Sans",
              "Vera Sans.font", "Barlow Regular", "Barlow", "DejaVu Sans", "CGTriumvirate",
              "helvetica", "Helvetica", "Arial", "XHelvetica", "sans-serif", "Sans")


def font_test():
    rows = "".join(f'<tr><td nowrap><tt>{esc(face)}</tt></td>'
                   f'<td><font face="{esc(face)}">Apollo Update 0123456789 '
                   f'<b>Bold sagasd.device</b></font></td></tr>\n' for face in FONT_TESTS)
    return ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
            '<html><head><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">'
            '<title>Font test</title></head><body bgcolor="#ffffff">\n'
            '<p>Each row asks for the font named on the left. A row shown in the '
            'default (serif) font is a name this browser did not find.</p>\n'
            '<table border="1" cellspacing="0" cellpadding="6">\n'
            '<tr><td><b>face=</b></td><td><b>Sample</b></td></tr>\n'
            f'<tr><td nowrap><tt>(none)</tt></td><td>Apollo Update 0123456789 '
            '<b>Bold sagasd.device</b></td></tr>\n' + rows +
            '</table></body></html>\n')
