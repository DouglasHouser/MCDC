#!/usr/bin/env python3
"""
Compare Benchmark 5 (Co-60 air-over-ground) results between MC/DC and the
MCNP-equivalent deck, for the problem defined in problem_new_source.py.

Both codes score a mu- and energy-binned flux (F2-equivalent) on the detector
sphere, using the SAME bin edges:

    energy edges (MeV): 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.80,
                         1.00, 1.10, 1.16, 1.18, 1.30, 1.34   (14 bins)
    mu edges          : -1.0 ... 1.0 in steps of 0.1          (20 bins)

MCNP's tally table additionally prints an "underflow" energy row labeled
0.02 MeV (everything below the lowest MC/DC edge); that row is dropped so
the two 20x14 [mu, energy] arrays align bin-for-bin.

USAGE
-----
    python compare_benchmark5.py
        (uses the hardcoded DEFAULT_H5_PATH / DEFAULT_OUT_PATH below)

    python compare_benchmark5.py <h5_path> <out_path> [--outdir DIR]
        (explicit paths, overriding the defaults)

WHAT THIS SCRIPT DOES
----------------------
1. Parses the MC/DC HDF5 tally and the MCNP "tally 2" ASCII table into two
   aligned (20 mu-bins x 14 energy-bins) arrays with uncertainties.
2. Reports the raw total-flux ratio between the two codes as a diagnostic.
   NOTE: MC/DC's tally mean and MCNP's F2 tally are not guaranteed to share
   an absolute normalization convention (e.g. per-source-particle vs. raw
   accumulated score, solid-angle/bin-width factors). If the total-flux
   ratio is far from O(1), that alone does not mean the physics disagrees --
   check the MC/DC tally normalization before concluding anything from
   absolute magnitudes. This script does NOT assume or apply a fix-up
   factor.
3. Prints a dose buildup factor table (total / uncollided-line / scattered
   flux and B = total/uncollided, each with propagated uncertainty) for
   MC/DC and MCNP side by side. B is a ratio *within* a single dataset, so
   it is immune to any overall normalization mismatch and is the most
   trustworthy single-number comparison available here.
4. Compares the *shape* of the energy spectrum (summed over mu), normalized
   to its own total in each code, so shape can be judged even if absolute
   scale differs. Prints a table and writes one plot.

NOT included: an angular-distribution comparison. MC/DC currently bins mu
against the fixed global z-axis (mu = uz) rather than the local outward
normal at the detector-sphere crossing point (see filter.py's
get_direction_index -- the polar_reference rotation is an unimplemented
TODO), while MCNP's F2 sphere tally bins against the local normal. Those are
different physical quantities on curved geometry, so a mu-binned comparison
between the two codes is not meaningful until that's implemented in MC/DC --
it's intentionally left out here rather than shown as a false discrepancy.

This is a smoke-test-scale comparison (MC/DC N_particle = 1e5 in the
uploaded .h5, MCNP nps = 1e8): expect MC/DC bins to be noisy/empty at this
statistics level. Re-run with the CLUSTER CONFIG in problem_new_source.py
for a bin-by-bin statistical comparison.
"""

import argparse
import re
import sys
from pathlib import Path

import h5py
import numpy as np

# Bin index of the 1.17 MeV line (energy edges 1.16-1.18) and the 1.33 MeV
# line (energy edges 1.30-1.34) in the 14-bin energy grid, used to split
# uncollided (source-line) flux from scattered flux for the buildup factor.
UNCOLLIDED_ENERGY_BINS = (11, 13)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def load_mcdc(h5_path):
    """Load MC/DC's mu/energy-binned surface flux tally.

    Returns dict with mu_edges (21,), energy_edges (15,), mean (20,14),
    sdev (20,14).
    """
    with h5py.File(h5_path, "r") as f:
        mu_edges = f["tallies/detector/grid/mu"][:]
        energy_edges = f["tallies/detector/grid/energy"][:]
        mean = f["tallies/detector/flux/mean"][:]
        sdev = f["tallies/detector/flux/sdev"][:]
        n_particle = int(f["settings/N_particle"][()])
    return dict(
        mu_edges=mu_edges,
        energy_edges=energy_edges,
        mean=mean,
        sdev=sdev,
        n_particle=n_particle,
    )


def load_mcnp(out_path, tally_id="2"):
    """Parse an MCNP F2 mu/energy-binned surface flux tally from a .out file.

    Returns dict with mu (20,) bin-upper-edge labels, energy (15,) bin-
    upper-edge labels (incl. the underflow row), flux (20,15), relerr
    (20,15, fractional), and nps.
    """
    text = Path(out_path).read_text()

    start_marker = f"1tally      {tally_id:>2}        nps ="
    start = text.find(start_marker)
    if start == -1:
        # fall back to a looser match
        m = re.search(rf"\n1tally\s+{tally_id}\s+nps\s*=\s*(\d+)", text)
        if not m:
            raise ValueError(f"Could not find tally {tally_id} block in {out_path}")
        start = m.start()
        nps = int(m.group(1))
    else:
        nps = int(text[start:].split("nps =")[1].split()[0])

    end = text.find("1analysis of the results", start)
    if end == -1:
        end = len(text)
    block = text[start:end]

    angle_blocks = re.split(r"\n\s*angle\s*:\s*", block)[1:]

    all_mu = []
    energy_labels = None
    flux_cols = []
    relerr_cols = []

    for ab in angle_blocks:
        lines = ab.splitlines()
        mu_vals = [float(x) for x in lines[0].split()]
        ncols = len(mu_vals)
        all_mu.extend(mu_vals)

        cols_flux = [[] for _ in range(ncols)]
        cols_relerr = [[] for _ in range(ncols)]
        energies = []
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue
            if line.startswith("total"):
                break
            parts = line.split()
            energies.append(float(parts[0]))
            vals = parts[1:]
            for i in range(ncols):
                cols_flux[i].append(float(vals[2 * i]))
                cols_relerr[i].append(float(vals[2 * i + 1]))
        if energy_labels is None:
            energy_labels = energies
        flux_cols.extend(cols_flux)
        relerr_cols.extend(cols_relerr)

    return dict(
        mu=np.array(all_mu),
        energy=np.array(energy_labels),
        flux=np.array(flux_cols),
        relerr=np.array(relerr_cols),
        nps=nps,
    )


def align(mcdc, mcnp):
    """Align the MCNP (20,15) table to MC/DC's (20,14) grid by dropping the
    MCNP underflow energy row (label 0.02 MeV, everything below MC/DC's
    lowest edge). Sanity-checks mu and energy labels agree with MC/DC's
    bin upper edges.
    """
    mu_upper = mcdc["mu_edges"][1:]
    en_upper = mcdc["energy_edges"][1:]

    if not np.allclose(mcnp["mu"], mu_upper, atol=1e-9):
        raise ValueError(
            f"MCNP angle bins {mcnp['mu']} do not match MC/DC mu edges {mu_upper}"
        )
    if not np.allclose(mcnp["energy"][1:], en_upper, atol=1e-9):
        raise ValueError(
            f"MCNP energy bins {mcnp['energy'][1:]} do not match MC/DC edges {en_upper}"
        )

    mcnp_flux = mcnp["flux"][:, 1:]
    mcnp_abs_err = mcnp["relerr"][:, 1:] * mcnp_flux
    return mcnp_flux, mcnp_abs_err


# ---------------------------------------------------------------------------
# Derived quantities
# ---------------------------------------------------------------------------
def buildup_factor(flux, err):
    """B = total flux / uncollided flux, with 1-sigma propagated uncertainty.
    Also reports scattered flux (= total - uncollided) with its own
    independently-summed uncertainty (not derived from total & uncollided,
    which are correlated).

    flux, err: (20, 14) arrays (err = absolute 1-sigma stdev per bin).
    """
    total = flux.sum()
    total_err = np.sqrt((err**2).sum())

    unc_mask = np.zeros(flux.shape[1], dtype=bool)
    for i in UNCOLLIDED_ENERGY_BINS:
        unc_mask[i] = True
    uncollided = flux[:, unc_mask].sum()
    uncollided_err = np.sqrt((err[:, unc_mask] ** 2).sum())

    scat_mask = ~unc_mask
    scattered = flux[:, scat_mask].sum()
    scattered_err = np.sqrt((err[:, scat_mask] ** 2).sum())

    if uncollided <= 0:
        return dict(total=total, total_err=total_err, uncollided=uncollided,
                    uncollided_err=uncollided_err, scattered=scattered,
                    scattered_err=scattered_err, B=np.nan, B_err=np.nan)

    B = total / uncollided
    # standard error propagation for a ratio of two (assumed independent) sums
    B_err = B * np.sqrt(
        (total_err / total) ** 2 + (uncollided_err / uncollided) ** 2
    )
    return dict(total=total, total_err=total_err, uncollided=uncollided,
                uncollided_err=uncollided_err, scattered=scattered,
                scattered_err=scattered_err, B=B, B_err=B_err)


def shape(flux, err):
    """Normalize a (20,14) flux array to its own total (a probability-like
    shape), propagating uncertainty, for the spectrum shape comparison.
    """
    total = flux.sum()
    if total <= 0:
        return np.zeros_like(flux), np.zeros_like(err)
    return flux / total, err / total


def print_buildup_table(b_mcdc, b_mcnp):
    """Print total / uncollided / scattered flux and buildup factor B for
    MC/DC and MCNP side by side, in a fixed-width table.
    """
    rows = [
        ("Total flux", "total", "total_err"),
        ("Uncollided flux", "uncollided", "uncollided_err"),
        ("Scattered flux", "scattered", "scattered_err"),
        ("Buildup factor B", "B", "B_err"),
    ]

    col_w = 24
    print("-- Dose buildup factor table (B = total flux / uncollided-line flux) --")
    header = f"  {'Quantity':<20} {'MC/DC':>{col_w}} {'MCNP':>{col_w}}"
    print(header)
    print("  " + "-" * (20 + 2 * col_w + 2))
    for label, key, err_key in rows:
        if key == "B":
            mcdc_str = f"{b_mcdc[key]:.4f} +/- {b_mcdc[err_key]:.4f}"
            mcnp_str = f"{b_mcnp[key]:.4f} +/- {b_mcnp[err_key]:.4f}"
        else:
            mcdc_str = f"{b_mcdc[key]:.4e} +/- {b_mcdc[err_key]:.1e}"
            mcnp_str = f"{b_mcnp[key]:.4e} +/- {b_mcnp[err_key]:.1e}"
        print(f"  {label:<20} {mcdc_str:>{col_w}} {mcnp_str:>{col_w}}")

    if np.isfinite(b_mcdc["B"]) and np.isfinite(b_mcnp["B"]):
        diff = b_mcdc["B"] - b_mcnp["B"]
        sigma = np.sqrt(b_mcdc["B_err"] ** 2 + b_mcnp["B_err"] ** 2)
        nsig = abs(diff) / sigma if sigma > 0 else float("inf")
        print("  " + "-" * (20 + 2 * col_w + 2))
        diff_str = f"{diff:+.4f} ({nsig:.2f} sigma)"
        print(f"  {'B difference':<20} {diff_str:>{2 * col_w + 1}}")
    print(
        "\n  (LA-12196 plane-source reference: B = 1.190 +/- 0.005. This SMOKE\n"
        "  geometry is not expected to reproduce that value -- see the\n"
        "  docstring in problem_new_source.py -- but MC/DC and MCNP should\n"
        "  agree with each other since they model the identical simplified\n"
        "  geometry.)"
    )
    print()


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def print_report(mcdc, mcnp_flux, mcnp_err, energy_edges):
    mcdc_flux, mcdc_err = mcdc["mean"], mcdc["sdev"]

    print("=" * 78)
    print("BENCHMARK 5 COMPARISON: MC/DC vs MCNP-equivalent deck")
    print("=" * 78)
    print(f"MC/DC N_particle : {mcdc['n_particle']:,}")
    print()

    # --- raw totals / normalization diagnostic ---
    mcdc_total = mcdc_flux.sum()
    mcnp_total = mcnp_flux.sum()
    print("-- Raw total flux (sum over all mu & energy bins) --")
    print(f"  MC/DC : {mcdc_total:.6e}")
    print(f"  MCNP  : {mcnp_total:.6e}")
    ratio = mcdc_total / mcnp_total if mcnp_total else float("nan")
    print(f"  MC/DC / MCNP ratio: {ratio:.6e}")
    if not (0.1 < ratio < 10):
        print(
            "  NOTE: ratio is far from 1 -- before drawing conclusions, verify\n"
            "  whether MC/DC's tally mean uses the same normalization\n"
            "  convention as MCNP's per-source-particle F2 flux (e.g. division\n"
            "  by N_particle, bin width, or solid angle). This script does not\n"
            "  assume or correct for a normalization factor."
        )
    print()

    # --- buildup factor (self-normalized, robust to overall scale) ---
    b_mcdc = buildup_factor(mcdc_flux, mcdc_err)
    b_mcnp = buildup_factor(mcnp_flux, mcnp_err)
    print_buildup_table(b_mcdc, b_mcnp)

    # --- energy spectrum shape (summed over mu) ---
    mcdc_spec, mcdc_spec_err = shape(mcdc_flux, mcdc_err)
    mcnp_spec, mcnp_spec_err = shape(mcnp_flux, mcnp_err)
    mcdc_e = mcdc_spec.sum(axis=0)
    mcnp_e = mcnp_spec.sum(axis=0)
    mcdc_e_err = np.sqrt((mcdc_spec_err**2).sum(axis=0))
    mcnp_e_err = np.sqrt((mcnp_spec_err**2).sum(axis=0))

    print("-- Energy spectrum shape (fraction of total flux, summed over mu) --")
    header = f"  {'E_upper[MeV]':>12} {'MC/DC':>12} {'+/-':>10} {'MCNP':>12} {'+/-':>10}"
    print(header)
    for i, e in enumerate(energy_edges[1:]):
        print(
            f"  {e:12.4f} {mcdc_e[i]:12.4e} {mcdc_e_err[i]:10.1e} "
            f"{mcnp_e[i]:12.4e} {mcnp_e_err[i]:10.1e}"
        )
    print()

    return dict(
        mcdc_spec=mcdc_e, mcdc_spec_err=mcdc_e_err,
        mcnp_spec=mcnp_e, mcnp_spec_err=mcnp_e_err,
    )


def make_plots(energy_edges, shapes, outdir):
    import matplotlib.pyplot as plt

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    e_centers = 0.5 * (energy_edges[:-1] + energy_edges[1:])

    # Energy spectrum shape
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.errorbar(e_centers, shapes["mcdc_spec"], yerr=shapes["mcdc_spec_err"],
                marker="o", ls="-", label="MC/DC", capsize=3)
    ax.errorbar(e_centers, shapes["mcnp_spec"], yerr=shapes["mcnp_spec_err"],
                marker="s", ls="--", label="MCNP", capsize=3)
    ax.set_xlabel("Energy [MeV]")
    ax.set_ylabel("Fraction of total flux")
    ax.set_yscale("log")
    ax.set_title("Benchmark 5 detector energy spectrum shape")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outdir / "benchmark5_energy_spectrum_shape.png", dpi=150)
    plt.close(fig)

    print(f"Plot written to: {outdir}/")


# ---------------------------------------------------------------------------
# Default file paths -- edit these if your files move, or override on the
# command line: compare_benchmark5.py <h5_path> <out_path>
DEFAULT_H5_PATH = r"C:\Projects\MCDC\photon_transport_code\MCNP_Verification_Tests\benchmark_5\benchmark_5.h5"
DEFAULT_OUT_PATH = r"C:\Projects\MCDC\photon_transport_code\MCNP_Verification_Tests\benchmark_5\Benchmark5-noTTB.out"


def autodetect(pattern, kind):
    """Find the single file matching *pattern in the current directory.

    Errors out with a clear message if none or more than one is found, so
    the user can pass an explicit path instead.
    """
    candidates = sorted(Path(".").glob(pattern))
    if len(candidates) == 0:
        raise SystemExit(
            f"No {kind} file ({pattern}) found in the current directory.\n"
            f"Pass it explicitly: compare_benchmark5.py <h5_path> <out_path>"
        )
    if len(candidates) > 1:
        raise SystemExit(
            f"Found multiple {kind} files: {[str(c) for c in candidates]}\n"
            f"Pass the one you want explicitly: compare_benchmark5.py <h5_path> <out_path>"
        )
    return candidates[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("h5_path", nargs="?", default=None,
                     help="MC/DC output HDF5 file. If omitted, uses DEFAULT_H5_PATH.")
    ap.add_argument("out_path", nargs="?", default=None,
                     help="MCNP output file. If omitted, uses DEFAULT_OUT_PATH.")
    ap.add_argument("--tally-id", default="2", help="MCNP tally number (default: 2)")
    ap.add_argument("--outdir",
                     default=r"C:\Projects\MCDC\photon_transport_code\MCNP_Verification_Tests\benchmark_5",
                     help="directory for output plots (default: the benchmark_5 project folder)")
    ap.add_argument("--no-plots", action="store_true", help="skip plot generation")
    args = ap.parse_args()

    h5_path = args.h5_path or DEFAULT_H5_PATH
    out_path = args.out_path or DEFAULT_OUT_PATH
    print(f"MC/DC file : {h5_path}")
    print(f"MCNP file  : {out_path}")
    print()

    mcdc = load_mcdc(h5_path)
    mcnp = load_mcnp(out_path, tally_id=args.tally_id)
    mcnp_flux, mcnp_err = align(mcdc, mcnp)

    shapes = print_report(mcdc, mcnp_flux, mcnp_err, mcdc["energy_edges"])

    if not args.no_plots:
        make_plots(mcdc["energy_edges"], shapes, args.outdir)


if __name__ == "__main__":
    sys.exit(main())
