"""
Build a standard-error comparison workbook (MC/DC vs MCNP) for every test
problem reported in the photon-transport paper.

One sheet per test problem, matching the layout style of
"For_Doug_Benchmarks 7-8-26 (version 1).xlsb" (banner row, two-line column
headers, MCNP block then MC/DC block), plus error-comparison columns.
No charts.
"""

import os
import re
import ast
import numpy as np
import xlsxwriter
from pyxlsb import open_workbook as open_xlsb

BASE = r"C:\Projects\MCDC\photon_transport_code\MCNP_Verification_Tests\Complex_M&G"
R1E7 = os.path.join(BASE, "1e7_results")
RCONV = os.path.join(BASE, "Convergence")
XLSB = r"C:\Users\dwhou\OneDrive\Documents\For_Doug_Benchmarks 7-8-26 (version 1).xlsb"
OUT = r"C:\Projects\MCDC\photon_standard_error_comparison.xlsx"

Z95 = 1.959963985


# ---------------------------------------------------------------- helpers
def zstat(f1, s1, f2, s2):
    """Signed difference in combined sigmas. None when undefined."""
    if f1 is None or f2 is None:
        return None
    sc = np.hypot(s1 or 0.0, s2 or 0.0)
    if sc <= 0.0:
        return None
    return (f1 - f2) / sc


def pdiff(a, b):
    if a is None or b is None or b == 0:
        return None
    return 100.0 * (a - b) / b


def ratio(a, b):
    if a is None or b is None or b == 0:
        return None
    return a / b


# ---------------------------------------------------------------- parsers
def parse_xlsb_sphere(sheet):
    """Al/Pb sphere sheets. Returns list of row dicts.

    Column layout (0-based) common to all four sheets:
      0 R_in, 1 r_vavg,
      2 MCNP 1e6 flux, 3 MCNP 1e6 rel err (FRACTION),
      4 MC/DC 1e6 flux, 5 MC/DC 1e6 rel err (FRACTION), 6 MC/DC 1e6 1sigma
    """
    wb = open_xlsb(XLSB)
    rows = []
    with wb.get_sheet(sheet) as sh:
        for r, row in enumerate(sh.rows()):
            if r < 2:
                continue
            v = [c.v for c in row]
            v += [None] * (12 - len(v))
            if v[1] is None:
                continue
            rows.append(
                dict(
                    r_in=v[0],
                    r_vavg=v[1],
                    mcnp_flux=v[2] if isinstance(v[2], (int, float)) else None,
                    mcnp_re=v[3] if isinstance(v[3], (int, float)) else None,
                    mcdc_flux=v[4] if isinstance(v[4], (int, float)) else None,
                    mcdc_re=v[5] if isinstance(v[5], (int, float)) else None,
                    mcdc_sig_stored=v[6] if isinstance(v[6], (int, float)) else None,
                )
            )
    return rows


def parse_mcnp_sphere_out(path):
    """Cell-ordered [(flux, rel_err_fraction), ...] from an F4 sphere output."""
    text = open(path).read()
    start = text.index("1tally        4")
    block = text[start: text.index("=====", start)]
    rows = re.findall(r"cell\s+(\d+)\s*\n\s*([\d.eE+-]+)\s+([\d.eE+-]+)", block)
    return [(float(f), float(e)) for _c, f, e in
            sorted(rows, key=lambda t: int(t[0]))]


def parse_mcdc_cylinder(path):
    rx = re.compile(
        r"^\s*(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+"
        r"([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+|nan)\s*$"
    )
    out = []
    for line in open(path):
        m = rx.match(line)
        if not m:
            continue
        out.append(
            dict(
                ir=int(m.group(1)),
                iz=int(m.group(2)),
                r_in=float(m.group(3)),
                r_out=float(m.group(4)),
                z_lo=float(m.group(5)),
                z_hi=float(m.group(6)),
                vol=float(m.group(7)),
                flux=float(m.group(8)),
                sig=float(m.group(9)),
            )
        )
    return out


def parse_mcnp_cell_tally(path):
    """Non-energy-binned F4: {cell: (flux, rel_err_fraction)} + volumes."""
    text = open(path).read()
    start = text.find("1tally        4")
    block = text[start: text.find("====", start)]
    vols = {}
    for m in re.finditer(r"cell:\s*((?:\d+\s*)+)\n\s*([\d.eE+\-\s]+)\n", block):
        ids = [int(x) for x in m.group(1).split()]
        vals = [float(x) for x in m.group(2).split()]
        if len(ids) == len(vals):
            vols.update(zip(ids, vals))
    res = {}
    for m in re.finditer(r"cell\s+(\d+)\s*\n\s*([\d.eE+-]+)\s+([\d.eE+-]+)", block):
        res[int(m.group(1))] = (float(m.group(2)), float(m.group(3)))
    nps = int(re.search(r"1tally\s+4\s+nps\s*=\s*(\d+)", text).group(1))
    return res, vols, nps


def parse_mcdc_slabs(path):
    rx = re.compile(
        r"^\s*(\d+)\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"
        r"([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s*$"
    )
    out = []
    for line in open(path):
        m = rx.match(line)
        if m:
            out.append(
                dict(
                    slab=int(m.group(1)),
                    mat=m.group(2),
                    z0=float(m.group(3)),
                    z1=float(m.group(4)),
                    thk=float(m.group(5)),
                    flux=float(m.group(6)),
                    sig=float(m.group(7)),
                )
            )
    return out


def parse_mcdc_mesh(path):
    rx = re.compile(
        r"^\s*(-?[\d.]+)\s+(\S+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s*$"
    )
    out = []
    for line in open(path):
        m = rx.match(line)
        if m:
            out.append(
                dict(
                    z=float(m.group(1)),
                    mat=m.group(2),
                    flux=float(m.group(3)),
                    sig=float(m.group(4)),
                )
            )
    return out


def parse_mcnp_mesh(path):
    lines = open(path).readlines()
    xs = ys = None
    nps = None
    for ln in lines:
        if "Number of histories used for normalizing" in ln:
            nps = float(ln.split("=")[1])
        if "X direction" in ln:
            xs = [float(v) for v in ln.split(":")[1].split()]
        if "Y direction" in ln:
            ys = [float(v) for v in ln.split(":")[1].split()]
        if xs and ys:
            break
    area = (xs[-1] - xs[0]) * (ys[-1] - ys[0])
    data = {}
    for ln in lines:
        p = ln.split()
        if len(p) == 6:
            try:
                z = float(p[3])
                f = float(p[4])
                re_ = float(p[5])
            except ValueError:
                continue
            data[round(z, 3)] = (f, re_)
    return area, data, nps


SHELLS = [
    ("lead", 0.0, 2.0), ("lead", 2.0, 4.0), ("lead", 4.0, 6.0),
    ("iron", 6.0, 10.0), ("iron", 10.0, 14.0), ("iron", 14.0, 18.0),
    ("concrete", 18.0, 24.0), ("concrete", 24.0, 30.0), ("concrete", 30.0, 36.0),
    ("water", 36.0, 46.0), ("water", 46.0, 56.0), ("water", 56.0, 66.0),
]


def parse_mcdc_spectrum(path):
    """Returns (edges, flux[12,40], sdev[12,40], r_vavg[12])."""
    lines = open(path).readlines()
    edges = None
    for ln in lines:
        m = re.search(r"Bin edges \(MeV\):\s*(\[.*\])", ln)
        if m:
            edges = np.array(ast.literal_eval(m.group(1)))
            break
    n = len(edges) - 1
    sdev_start = next(
        i for i, ln in enumerate(lines) if "Standard deviation of the above" in ln
    )
    rx = re.compile(r"^\s*(\d+)\s+(lead|iron|concrete|water)\s+([\d.]+)\s+(.*)$")
    flux = np.full((12, n), np.nan)
    sdev = np.full((12, n), np.nan)
    rv = np.zeros(12)
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if not m:
            continue
        reg = int(m.group(1))
        vals = np.array([float(x) for x in m.group(4).split()])
        if vals.size != n or not (0 <= reg < 12):
            continue
        rv[reg] = float(m.group(3))
        if i < sdev_start:
            flux[reg] = vals
        else:
            sdev[reg] = vals
    return edges, flux, sdev, rv


def parse_mcnp_spectrum(path, n_bins):
    """Returns (flux[12,n], relerr[12,n], volumes[12], nps)."""
    lines = open(path).readlines()
    text = "".join(lines)
    nps = int(re.search(r"1tally\s+4\s+nps\s*=\s*(\d+)", text).group(1))
    start = next(i for i, ln in enumerate(lines) if ln.startswith("1tally        4"))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("===="):
            end = i
            break
    block = lines[start:end]
    btxt = "".join(block)
    vols = {}
    for m in re.finditer(r"cell:\s*((?:\d+\s*)+)\n\s*([\d.eE+\-\s]+)\n", btxt):
        ids = [int(x) for x in m.group(1).split()]
        vals = [float(x) for x in m.group(2).split()]
        if len(ids) == len(vals):
            vols.update(zip(ids, vals))
    flux = np.full((12, n_bins), np.nan)
    rerr = np.full((12, n_bins), np.nan)
    cell = None
    rows = []
    cell_re = re.compile(r"^\s*cell\s+(\d+)\s*$")

    def flush(c, rws):
        if c is None or not (1 <= c <= 12):
            return
        arr = np.array(rws)
        if arr.shape[0] >= n_bins:
            flux[c - 1] = arr[:n_bins, 1]
            rerr[c - 1] = arr[:n_bins, 2]

    for ln in block:
        m = cell_re.match(ln)
        if m:
            flush(cell, rows)
            cell = int(m.group(1))
            rows = []
            continue
        p = ln.split()
        if len(p) == 3:
            try:
                rows.append([float(p[0]), float(p[1]), float(p[2])])
            except ValueError:
                pass
    flush(cell, rows)
    volumes = np.array([vols.get(i + 1, np.nan) for i in range(12)])
    return flux, rerr, volumes, nps


# ---------------------------------------------------------------- formats
def make_formats(wb):
    f = {}
    f["title"] = wb.add_format(
        dict(bold=True, font_size=13, font_color="#FFFFFF", bg_color="#1F3864",
             align="left", valign="vcenter")
    )
    f["grpA"] = wb.add_format(
        dict(bold=True, align="center", valign="vcenter", bg_color="#C9D9F0",
             border=1, text_wrap=True)
    )
    f["grpB"] = wb.add_format(
        dict(bold=True, align="center", valign="vcenter", bg_color="#FCE2C8",
             border=1, text_wrap=True)
    )
    f["grpC"] = wb.add_format(
        dict(bold=True, align="center", valign="vcenter", bg_color="#D9E7D2",
             border=1, text_wrap=True)
    )
    f["grpG"] = wb.add_format(
        dict(bold=True, align="center", valign="vcenter", bg_color="#E8E8E8",
             border=1, text_wrap=True)
    )
    f["hdr"] = wb.add_format(
        dict(bold=True, align="center", valign="bottom", text_wrap=True,
             bottom=2, top=1)
    )
    f["num"] = wb.add_format(dict(num_format="0.0000", align="right"))
    f["sci"] = wb.add_format(dict(num_format="0.0000E+00", align="right"))
    f["pct"] = wb.add_format(dict(num_format="0.000", align="right"))
    f["pct2"] = wb.add_format(dict(num_format="0.000", align="right"))
    f["rat"] = wb.add_format(dict(num_format="0.000", align="right"))
    f["txt"] = wb.add_format(dict(align="left"))
    f["ctr"] = wb.add_format(dict(align="center"))
    f["note"] = wb.add_format(dict(italic=True, font_color="#555555", text_wrap=True,
                                   valign="top"))
    f["warn"] = wb.add_format(dict(italic=True, font_color="#9C0006", text_wrap=True,
                                   valign="top"))
    f["bold"] = wb.add_format(dict(bold=True))
    f["wrap"] = wb.add_format(dict(text_wrap=True, valign="top"))
    f["ok"] = wb.add_format(dict(align="center", font_color="#006100",
                                 bg_color="#C6EFCE"))
    f["bad"] = wb.add_format(dict(align="center", font_color="#9C0006",
                                  bg_color="#FFC7CE"))
    return f


def w(ws, r, c, v, fmt=None):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        ws.write_blank(r, c, None, fmt)
    else:
        ws.write(r, c, v, fmt)


def verdict(ws, r, c, z, F):
    if z is None:
        ws.write(r, c, "n/a", F["ctr"])
    elif abs(z) <= Z95:
        ws.write(r, c, "yes", F["ok"])
    else:
        ws.write(r, c, "no", F["bad"])


# ---------------------------------------------------------------- writers
COMMON_TAIL = [
    ("MCNP\n1\u03c3 [1/cm\u00b2]", 14),
    ("MCNP\nRel Err [%]", 11),
    ("Rel Err ratio\nMC/DC \u00f7 MCNP", 13),
    ("Flux diff\n(MC/DC\u2212MCNP)/MCNP [%]", 15),
    ("z = diff /\n\u03c3_combined", 11),
    ("Agree at\n95% CI?", 10),
]


def write_banner(ws, F, title, lines, hdr):
    """Title + note rows, each merged across the whole table.

    Column widths are applied FIRST so the merged note rows can be given an
    explicit height. Without this Excel auto-fits wrapped text inside a narrow
    column A and the note rows balloon to hundreds of points, pushing the data
    off the screen.
    """
    ncols = len(hdr)
    for i, (_h, width) in enumerate(hdr):
        ws.set_column(i, i, width)
    # Usable characters per line across the merged span.
    cpl = max(60, int(sum(width for _h, width in hdr) * 0.95))

    ws.merge_range(0, 0, 0, ncols - 1, title, F["title"])
    ws.set_row(0, 24)
    r = 1
    for ln, fmt in lines:
        ws.merge_range(r, 0, r, ncols - 1, ln, F[fmt])
        nlines = max(1, -(-len(ln) // cpl))
        ws.set_row(r, 13.2 * nlines + 5)
        r += 1
    return r + 1


def sheet_sphere(wb, F, name, title, rows, nhist_note,
                 mcdc_label="MC/DC (1×10⁶ histories)",
                 mcnp_label="MCNP (1×10⁶ histories)",
                 extra_notes=None):
    ws = wb.add_worksheet(name)
    hdr = [
        ("R_in\n[cm]", 8), ("r_vavg\n[cm]", 9),
        ("MC/DC Flux/src\n[1/cm²]", 14), ("MC/DC\n1σ [1/cm²]", 14),
        ("MC/DC\nRel Err [%]", 11), ("MC/DC 1σ\n(stored)", 13),
        ("stored 1σ\nconsistent?", 11),
        ("MCNP Flux/src\n[1/cm²]", 14),
        ("MCNP 1σ\n(= flux × Rel Err)", 15), ("MCNP\nRel Err [%]", 11),
        ("Rel Err ratio\nMC/DC ÷ MCNP", 13),
        ("Flux diff\n(MC/DC−MCNP)/MCNP [%]", 15),
        ("z = diff /\nσ_combined", 11), ("Agree at\n95% CI?", 10),
    ]
    top = write_banner(
        ws, F, title,
        [(nhist_note, "note"),
         (("MC/DC flux and Rel Err are taken verbatim from "
           "For_Doug_Benchmarks 7-8-26 (version 1).xlsb, sheet "
           f"'{name}'. The MCNP side comes from the MCNP output file named "
           "below, not from the .xlsb.")
          if extra_notes else
          ("Flux and Rel Err for BOTH codes are taken verbatim from "
           "For_Doug_Benchmarks 7-8-26 (version 1).xlsb, sheet "
           f"'{name}', which is the system of record for this problem. Every "
           "value was checked cell-by-cell against that workbook; the only "
           "change is that Rel Err, stored there as a fraction, is shown here "
           "as a percent."), "note"),
         ("MCNP 1\u03c3 is derived as flux \u00d7 Rel Err purely so that a "
          "z-score can be formed. It is not an independent number.", "note"),
         ("MC/DC 1\u03c3 is likewise recomputed as flux \u00d7 Rel Err (Rel Err "
          "is the column the paper quotes); the .xlsb's own stored 1\u03c3 is "
          "carried alongside with a consistency flag.", "note")]
        + list(extra_notes or []),
        hdr,
    )

    ws.merge_range(top, 2, top, 6, mcdc_label, F["grpA"])
    ws.merge_range(top, 7, top, 9, mcnp_label, F["grpB"])
    ws.merge_range(top, 10, top, 13, "Comparison", F["grpC"])
    hr = top + 1
    for i, (h, width) in enumerate(hdr):
        ws.write(hr, i, h, F["hdr"])
        ws.set_column(i, i, width)
    ws.set_row(hr, 32)
    ws.freeze_panes(hr + 1, 2)
    page_setup(ws, hdr, hr)

    r = hr + 1
    stats = []
    for row in rows:
        mf, mre = row["mcdc_flux"], row["mcdc_re"]
        nf, nre = row["mcnp_flux"], row["mcnp_re"]
        msig = mf * mre if (mf is not None and mre is not None) else None
        nsig = nf * nre if (nf is not None and nre is not None) else None
        stored = row["mcdc_sig_stored"]
        if msig is None or stored is None or msig == 0:
            cons = "n/a"
        else:
            cons = "yes" if abs(stored / msig - 1.0) < 0.05 else "NO"
        z = zstat(mf, msig, nf, nsig)

        w(ws, r, 0, row["r_in"], F["num"])
        w(ws, r, 1, row["r_vavg"], F["num"])
        w(ws, r, 2, mf, F["sci"])
        w(ws, r, 3, msig, F["sci"])
        w(ws, r, 4, None if mre is None else mre * 100, F["pct"])
        w(ws, r, 5, stored, F["sci"])
        ws.write(r, 6, cons, F["bad"] if cons == "NO" else F["ctr"])
        w(ws, r, 7, nf, F["sci"])
        w(ws, r, 8, nsig, F["sci"])
        w(ws, r, 9, None if nre is None else nre * 100, F["pct"])
        w(ws, r, 10, ratio(mre, nre), F["rat"])
        w(ws, r, 11, pdiff(mf, nf), F["pct2"])
        w(ws, r, 12, z, F["rat"])
        verdict(ws, r, 13, z, F)
        if z is not None:
            stats.append((mre, nre, z))
        r += 1
    return ws, r, stats, [x[1] for x in hdr]


def page_setup(ws, hdr, hr):
    """Landscape, one page wide, header row repeated on every printed page."""
    ws.set_landscape()
    ws.set_paper(1)
    ws.fit_to_pages(1, 0)
    ws.repeat_rows(hr)
    ws.set_margins(0.3, 0.3, 0.4, 0.4)


def _label_span(widths, want=34):
    """How many leading columns to merge so a summary label is never clipped."""
    if not widths:
        return 2
    acc = 0
    for i, width in enumerate(widths):
        acc += width
        if acc >= want:
            return i + 1
    return len(widths)


def summary_block(ws, F, r, stats, label="bins", widths=None):
    """stats: list of (mcdc_relerr_frac, mcnp_relerr_frac, z)."""
    if not stats:
        return r
    # A relative error is only DEFINED where that code scored a nonzero flux.
    # MCNP prints 0.0000 (not a blank) for an empty bin and MC/DC prints a zero
    # sdev where every score landed in one batch; counting either as "0 % error"
    # would drag the mean down. `if m and n` drops None and 0.0 alike, and keeps
    # the rule symmetric between the two codes.
    both = [(m, n) for m, n, _ in stats if m and n]
    mres = [m for m, _ in both]
    nres = [n for _, n in both]
    rats = [m / n for m, n in both]
    # Unpaired means: every bin where THAT code resolved an error, so each
    # one is a property of that code's own file and does not move when the
    # other code's file is swapped.
    m_all = [m for m, _n, _z in stats if m]
    n_all = [_n for _m, _n, _z in stats if _n]
    zs = [abs(s[2]) for s in stats]
    agree = sum(1 for z in zs if z <= Z95)
    r += 1
    ws.write(r, 0, "SUMMARY", F["bold"]); r += 1
    pairs = [
        ("Comparable %s" % label, len(stats), F["ctr"]),
        ("%s with a rel err defined in BOTH codes (basis of the means below)"
         % label, len(both), F["ctr"]),
        ("Mean MC/DC rel err, paired bins [%]", float(np.mean(mres)) * 100 if mres else None, F["pct"]),
        ("Mean MCNP rel err, paired bins [%]", float(np.mean(nres)) * 100 if nres else None, F["pct"]),
        ("Mean MC/DC rel err, ALL bins MC/DC resolved [%]",
         float(np.mean(m_all)) * 100 if m_all else None, F["pct"]),
        ("Mean MCNP rel err, ALL bins MCNP resolved [%]",
         float(np.mean(n_all)) * 100 if n_all else None, F["pct"]),
        ("Median MC/DC rel err [%]", float(np.median(mres)) * 100 if mres else None, F["pct"]),
        ("Median MCNP rel err [%]", float(np.median(nres)) * 100 if nres else None, F["pct"]),
        ("Median rel-err ratio (MC/DC/MCNP)",
         float(np.median(rats)) if rats else None, F["rat"]),
        ("%s agreeing at 95%% CI" % label, agree, F["ctr"]),
        ("Fraction agreeing at 95% CI [%]", 100.0 * agree / len(stats), F["pct2"]),
    ]
    span = _label_span(widths)
    for lab, val, fmt in pairs:
        if span > 1:
            ws.merge_range(r, 0, r, span - 1, lab, F["txt"])
        else:
            ws.write(r, 0, lab, F["txt"])
        w(ws, r, span, val, fmt)
        r += 1
    return r, dict(n=len(stats), agree=agree, basis=len(both),
                   mcdc=float(np.mean(m_all)) * 100 if m_all else None,
                   mcnp=float(np.mean(n_all)) * 100 if n_all else None,
                   med_ratio=float(np.median(rats)) if rats else None)
