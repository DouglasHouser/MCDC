"""
Rebuild the 2x2 Al/Pb sphere flux comparison figure (paper Fig. 5) with
1-sigma statistical error bands.

Data sources
------------
Al 1 MeV, Al 10 MeV, Pb 1 MeV
    For_Doug_Benchmarks 7-8-26 (version 1).xlsb, the 1x10^6-history MC/DC
    and MCNP column pairs.

Pb 10 MeV
    MC/DC  : same .xlsb sheet (1x10^6 histories; the output file for this run
             is not in the repository, but the .xlsb column is the record).
    MCNP   : bench3-nobrem.out  -- nps = 1x10^6 with "phys:p j 1", so
             thick-target bremsstrahlung is OFF (0 brem tracks, 813,670
             pair-production events). All 20 of its fluxes match the .xlsb
             column exactly, which identifies it as the run behind those
             numbers; it additionally supplies the real relative-error
             column, running 0.03 % to 100 %.

             This REPLACES the .xlsb's own MCNP rel-err column for this
             problem, which stayed flat at 0.05-0.21 % across 9.8 decades of
             flux falloff and quoted 0.19-0.21 % error on shells of exactly
             zero flux -- it was not this problem's error column.

Band construction matches the published figure: 1 sigma = flux x Rel Err,
fill alpha 0.45 and edge alpha 0.70 over base colours #2C73B6 (MCNP, drawn
first) and #6FAD47 (MC/DC, drawn second); shells whose relative error reaches
RELERR_CUTOFF are not plotted.
"""

import os
import re

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pyxlsb import open_workbook as open_xlsb

# --------------------------------------------------------------------------
XLSB = os.path.join(os.path.expanduser("~"), "OneDrive", "Documents",
                    "For_Doug_Benchmarks 7-8-26 (version 1).xlsb")
BENCH3_NOBREM = os.path.join(os.path.expanduser("~"), "Downloads",
                             "bench3-nobrem.out")
HERE = os.path.dirname(os.path.abspath(__file__))

C_MCNP = "#2C73B6"
C_MCDC = "#6FAD47"
FILL_ALPHA = 0.45
EDGE_ALPHA = 0.70
RELERR_CUTOFF = 0.50          # drop shells at/above this relative error

PANELS = [
    ("Al 1 MeV",  "1 MeV Photon in Aluminum",   r"1\times10^6", r"1\times10^6"),
    ("Al 10 MeV", "10 MeV Photon in Aluminum",  r"1\times10^6", r"1\times10^6"),
    ("Pb 1 MeV",  "1 MeV Photon in Lead",       r"1\times10^6", r"1\times10^6"),
    ("Pb 10 MeV", "10 MeV Photon in Lead",      r"1\times10^6", r"1\times10^6"),
]


# --------------------------------------------------------------------------
def read_sheet(sheet):
    """r_vavg, MCNP flux, MCNP rel err, MC/DC flux, MC/DC rel err."""
    wb = open_xlsb(XLSB)
    rows = []
    with wb.get_sheet(sheet) as sh:
        for i, row in enumerate(sh.rows()):
            if i < 2:
                continue
            v = [c.v for c in row] + [None] * 12
            if v[1] is None:
                continue
            rows.append(v)
    num = (int, float)
    g = lambda v, j: v[j] if isinstance(v[j], num) else np.nan
    return (np.array([g(v, 1) for v in rows]),
            np.array([g(v, 2) for v in rows]), np.array([g(v, 3) for v in rows]),
            np.array([g(v, 4) for v in rows]), np.array([g(v, 5) for v in rows]))


def read_mcnp_out(path, n):
    """Cell-ordered flux and rel err from an F4 sphere output."""
    text = open(path).read()
    start = text.index("1tally        4")
    block = text[start: text.index("=====", start)]
    hits = re.findall(r"cell\s+(\d+)\s*\n\s*([\d.eE+-]+)\s+([\d.eE+-]+)", block)
    hits.sort(key=lambda t: int(t[0]))
    if len(hits) != n:
        raise RuntimeError("expected %d cells, found %d" % (n, len(hits)))
    flux = np.array([float(f) for _c, f, _e in hits])
    rerr = np.array([float(e) for _c, _f, e in hits])
    rerr[flux <= 0] = np.nan            # zero flux -> error is undefined
    return flux, rerr


def series(r, flux, rerr, cutoff):
    """Shells carrying a usable relative error, as (r, flux, sigma)."""
    keep = np.isfinite(flux) & np.isfinite(rerr) & (flux > 0)
    if cutoff is not None:
        keep &= rerr < cutoff
    return r[keep], flux[keep], flux[keep] * rerr[keep]


def band(ax, r, flux, sigma, colour, floor):
    """1-sigma band. A shell whose flux - sigma <= 0 is statistically
    consistent with zero, so its band is drawn down to the axis floor."""
    lo = np.clip(flux - sigma, floor, None)
    ax.fill_between(r, lo, flux + sigma, facecolor=colour, alpha=FILL_ALPHA,
                    edgecolor="none", zorder=2)
    ax.plot(r, lo, color=colour, alpha=EDGE_ALPHA, lw=0.7, zorder=3)
    ax.plot(r, flux + sigma, color=colour, alpha=EDGE_ALPHA, lw=0.7, zorder=3)


def make_figure(cutoff, out_path, subtitle=None):
    fig, axes = plt.subplots(2, 2, figsize=(14.6, 10.6))
    for ax, (sheet, title, n_mcnp, n_mcdc) in zip(axes.ravel(), PANELS):
        r, nf, nre, mf, mre = read_sheet(sheet)
        if sheet == "Pb 10 MeV":
            nf, nre = read_mcnp_out(BENCH3_NOBREM, len(r))

        sN = series(r, nf, nre, cutoff)
        sM = series(r, mf, mre, cutoff)

        # Axis floor: one decade below the smallest positive quantity shown,
        # so a band that reaches zero runs to the bottom instead of forcing
        # the log axis down to an absurd decade.
        smallest = min(np.min(s[1]) for s in (sN, sM) if len(s[1]))
        pos_lo = [np.min(s[1] - s[2]) for s in (sN, sM)
                  if len(s[1]) and np.all(s[1] - s[2] > 0)]
        floor = min([smallest] + pos_lo) / 3.0

        ax.set_yscale("log")
        ax.set_ylim(bottom=floor)
        band(ax, *sN, C_MCNP, floor)              # MCNP first
        band(ax, *sM, C_MCDC, floor)              # MC/DC second
        ax.set_title(title, fontsize=15, fontweight="bold", pad=12)
        ax.set_xlabel(r"Distance from source, $r_{vavg}$ [cm]", fontsize=12)
        ax.set_ylabel(r"Flux per source particle [1/cm$^2$]", fontsize=12)
        ax.grid(which="major", ls=":", lw=0.6, color="0.75")
        ax.grid(which="minor", ls=":", lw=0.4, color="0.88")
        ax.tick_params(labelsize=11)
        ax.legend(handles=[
            Patch(facecolor=C_MCNP, alpha=FILL_ALPHA, edgecolor=C_MCNP,
                  label=r"MCNP (1$\sigma$, $%s$)" % n_mcnp),
            Patch(facecolor=C_MCDC, alpha=FILL_ALPHA, edgecolor=C_MCDC,
                  label=r"MC/DC (1$\sigma$, $%s$)" % n_mcdc),
        ], fontsize=12, loc="upper right", framealpha=0.95)

    if subtitle:
        fig.suptitle(subtitle, fontsize=12, y=0.998)
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    print("wrote", out_path)


if __name__ == "__main__":
    # Primary: same 50 % relative-error cutoff as the published figure.
    make_figure(RELERR_CUTOFF,
                os.path.join(HERE, "v3_sphere_benchmark_comparison.png"))
    # Variant: every shell with a nonzero flux, so the full error growth shows.
    make_figure(None,
                os.path.join(HERE,
                             "v3_sphere_benchmark_comparison_allshells.png"))
