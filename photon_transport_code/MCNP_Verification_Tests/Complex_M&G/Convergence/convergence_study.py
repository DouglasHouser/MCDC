"""
Convergence study: MC/DC vs. MCNP, multi-material sphere photon problem
(lead -> iron -> concrete -> water, 1-10 MeV isotropic point source).

For each particle history count N in HISTORY_COUNTS, this script reads:
  - the MC/DC results.txt          (energy-binned flux + sdev table, as
                                     written by report_results() in
                                     multi_material_spheres_1to10mev_spectrum.py)
  - the matching MCNP .out file    (f4 track-length flux tally, per cell,
                                     printed as "1tally  4  nps = ..." blocks)

and computes, per region (shell), the total flux (summed over the 40 shared
energy bins) along with three convergence metrics:
  1. MC/DC native relative statistical error   (sdev / mean)
  2. MCNP  native relative statistical error   (from the "total" line)
  3. Cross-code relative difference            (|MC/DC - MCNP| / MCNP)

All three are plotted vs. N on a shared log-log axis per region, alongside
an N^(-1/2) reference slope anchored to the first point, which is the
expected scaling for both MC statistical error and (once both codes are
sampling the same underlying distribution) their disagreement.

USAGE
-----
Edit HISTORY_COUNTS / MCDC_DIR / MCNP_DIR / the two filename templates
below to match where your 1e5-1e9 output files live, then run:

    python convergence_study.py

Only the 1e5 pair is bundled with this script for a smoke test; point the
templates at your other four history counts to get the full plot.
"""

import os
import re
import sys

import numpy as np

# =============================================================================
# Configuration -- edit these to match your file layout
# =============================================================================
HISTORY_COUNTS = ["1e5", "1e6", "1e7", "1e8", "1e9"]

MCDC_DIR = os.path.dirname(os.path.abspath(__file__))
MCNP_DIR = os.path.dirname(os.path.abspath(__file__))

# {n} is replaced with each entry of HISTORY_COUNTS (e.g. "1e6")
MCDC_TEMPLATE = "mm_spheres_1to10mev_spec_{n}_results.txt"
MCNP_TEMPLATE = "multi_material_spheres_1to10mev_spectrum_MCNP-{n}.out"

# Regions to actually plot (0-indexed, matching the "Region" column of the
# MC/DC results.txt / MCNP cell numbers minus 1). Picking a near, mid, and
# far shell gives a good spread of count statistics.
PLOT_REGIONS = [0, 5, 11]
REGION_LABELS = {
    0: "Region 0 (lead, innermost)",
    5: "Region 5 (iron, outer)",
    11: "Region 11 (water, outermost)",
}

REGION_MATERIALS = (
    ["lead"] * 3 + ["iron"] * 3 + ["concrete"] * 3 + ["water"] * 3
)
MATERIAL_COLORS = {
    "lead": "tab:gray", "iron": "tab:orange",
    "concrete": "tab:brown", "water": "tab:blue",
}

OUT_PATH = os.path.join(MCDC_DIR, "convergence_study.png")
CROSS_DIFF_OUT_PATH = os.path.join(MCDC_DIR, "convergence_cross_diff_all_regions.png")

N_ENERGY_BINS = 40  # shared by both codes; see module docstring


# =============================================================================
# MC/DC results.txt parser
# =============================================================================
def parse_mcdc_results(path):
    """Return (flux, sdev), each shape (N_region, N_ENERGY_BINS), parsed from
    a results.txt written by report_results()."""
    with open(path, "r") as f:
        lines = f.readlines()

    # There are two tables: flux, then sdev. Both are bounded by
    # "----" separator lines and start right after the column header row
    # (which begins with "Region").
    tables = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("Region"):
            header_idx = i
            # Data rows start two lines after the header (header, units line,
            # then a "----" separator, then rows) -- walk forward to the
            # separator, then collect rows until the next separator.
            j = header_idx + 1
            while not lines[j].strip().startswith("----"):
                j += 1
            j += 1  # skip the separator
            rows = []
            while not lines[j].strip().startswith("----"):
                if lines[j].strip():
                    rows.append(lines[j])
                j += 1
            tables.append(rows)
            i = j
        else:
            i += 1

    if len(tables) < 2:
        raise ValueError(f"Expected a flux table and a sdev table in {path}, "
                          f"found {len(tables)}")

    def rows_to_array(rows):
        arr = np.zeros((len(rows), N_ENERGY_BINS))
        for r, row in enumerate(rows):
            parts = row.split()
            # columns: region, material, r_vavg, then N_ENERGY_BINS floats
            values = [float(x) for x in parts[3:]]
            if len(values) != N_ENERGY_BINS:
                raise ValueError(
                    f"Expected {N_ENERGY_BINS} energy bins in {path}, "
                    f"got {len(values)} on row: {row!r}"
                )
            arr[r, :] = values
        return arr

    flux = rows_to_array(tables[0])
    sdev = rows_to_array(tables[1])
    return flux, sdev


# =============================================================================
# MCNP .out parser
# =============================================================================
_CELL_HEADER_RE = re.compile(r"^\s*cell\s+(\d+)\s*$")
_ENERGY_ROW_RE = re.compile(
    r"^\s*([\d.]+E[+-]\d+)\s+([\d.]+E[+-]\d+)\s+([\d.]+)\s*$"
)
_TOTAL_ROW_RE = re.compile(r"^\s*total\s+([\d.]+E[+-]\d+)\s+([\d.]+)\s*$")


def parse_mcnp_out(path):
    """Return (flux, relerr, total_flux, total_relerr) for the f4 tally in an
    MCNP .out file. flux/relerr have shape (N_region, N_ENERGY_BINS);
    total_flux/total_relerr have shape (N_region,).

    MCNP implicitly prepends a 0-0.01 MeV bin that MC/DC does not report;
    per the generating script's note, that bin is dropped here so bin index
    i lines up between the two codes. Each per-cell block prints
    N_ENERGY_BINS energy rows followed by a "total" row -- if a block has
    N_ENERGY_BINS + 1 energy rows, the first (the implicit low bin) is
    stripped.
    """
    with open(path, "r") as f:
        lines = f.readlines()

    # Find the start of the (first/only) f4 flux tally block.
    start = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("1tally") and "nps" in line:
            start = i
            break
    if start is None:
        raise ValueError(f"Could not find a '1tally ... nps = ...' block in {path}")

    cells = {}  # cell_number -> (energies, relerrs, total, total_relerr)
    i = start
    while i < len(lines):
        m = _CELL_HEADER_RE.match(lines[i])
        if m:
            cell_num = int(m.group(1))
            i += 1
            # skip the "energy" sub-header
            while lines[i].strip() != "energy":
                i += 1
            i += 1
            fluxes, relerrs = [], []
            total, total_relerr = None, None
            while True:
                row = lines[i]
                tm = _TOTAL_ROW_RE.match(row)
                if tm:
                    total = float(tm.group(1))
                    trelerr_val = float(tm.group(2))
                    total_relerr = trelerr_val if trelerr_val > 0.0 else np.nan
                    i += 1
                    break
                em = _ENERGY_ROW_RE.match(row)
                if not em:
                    # blank line or end of block without an explicit total
                    break
                fluxes.append(float(em.group(2)))
                relerr_val = float(em.group(3))
                # MCNP prints relative error to only 4 decimal places. Once a
                # tally is well-converged, that column genuinely prints
                # "0.0000" -- not because the error is truly zero, but
                # because it's below print resolution. Treat that as missing
                # (NaN) rather than a literal zero, or it silently corrupts
                # any log-scale convergence plot (log(0) = -inf).
                relerrs.append(relerr_val if relerr_val > 0.0 else np.nan)
                i += 1
            fluxes = np.array(fluxes)
            relerrs = np.array(relerrs)
            if len(fluxes) == N_ENERGY_BINS + 1:
                # drop MCNP's implicit 0-0.01 MeV bin (see docstring)
                fluxes = fluxes[1:]
                relerrs = relerrs[1:]
            elif len(fluxes) != N_ENERGY_BINS:
                raise ValueError(
                    f"Cell {cell_num} in {path}: expected {N_ENERGY_BINS} or "
                    f"{N_ENERGY_BINS + 1} energy rows, got {len(fluxes)}"
                )
            cells[cell_num] = (fluxes, relerrs, total, total_relerr)
        else:
            i += 1
        # stop once we've moved past the per-cell blocks into the next
        # major output section (a new "1..." page header that isn't a cell
        # tally continuation)
        if i < len(lines) and lines[i].startswith("1") and "tally" not in lines[i]:
            break

    if not cells:
        raise ValueError(f"No per-cell tally blocks parsed from {path}")

    n_region = max(cells.keys())
    flux = np.zeros((n_region, N_ENERGY_BINS))
    relerr = np.zeros((n_region, N_ENERGY_BINS))
    total_flux = np.zeros(n_region)
    total_relerr = np.zeros(n_region)
    for cell_num, (fluxes, relerrs, total, trelerr) in cells.items():
        r = cell_num - 1  # MCNP cells are 1-indexed; skip the graveyard (99)
        if r >= n_region:
            continue
        flux[r, :] = fluxes
        relerr[r, :] = relerrs
        total_flux[r] = total
        total_relerr[r] = trelerr

    return flux, relerr, total_flux, total_relerr


# =============================================================================
# Convergence metrics
# =============================================================================
def load_history(n_label):
    """Load and reduce both codes' results for one history count. Returns a
    dict with per-region total flux, native relative error (both codes), and
    cross-code relative difference."""
    mcdc_path = os.path.join(MCDC_DIR, MCDC_TEMPLATE.format(n=n_label))
    mcnp_path = os.path.join(MCNP_DIR, MCNP_TEMPLATE.format(n=n_label))

    mcdc_flux, mcdc_sdev = parse_mcdc_results(mcdc_path)
    _, _, mcnp_total, mcnp_total_relerr = parse_mcnp_out(mcnp_path)

    # Reduce MC/DC to a total (energy-integrated) flux per region, matching
    # MCNP's "total" row: sum the per-bin means; propagate the per-bin sdevs
    # in quadrature (bins are independent tallies of the same history set).
    mcdc_total = mcdc_flux.sum(axis=1)
    mcdc_total_sdev = np.sqrt((mcdc_sdev ** 2).sum(axis=1))
    mcdc_total_relerr = mcdc_total_sdev / mcdc_total

    mcnp_total_sdev = mcnp_total_relerr * mcnp_total

    n_region = min(len(mcdc_total), len(mcnp_total))
    abs_diff = np.abs(mcdc_total[:n_region] - mcnp_total[:n_region])
    cross_diff = abs_diff / mcnp_total[:n_region]
    total_abs_diff = abs_diff.sum()

    # Statistical significance of the disagreement: how many combined-sigma
    # apart are the two codes, per region? If this GROWS with N even as
    # each code's own relative error shrinks, the disagreement is a
    # systematic bias, not statistical noise -- and more histories will
    # never make it go away.
    combined_sigma = np.sqrt(
        mcdc_total_sdev[:n_region] ** 2 + mcnp_total_sdev[:n_region] ** 2
    )
    z_score = abs_diff / combined_sigma

    return {
        "mcdc_total": mcdc_total[:n_region],
        "mcnp_total": mcnp_total[:n_region],
        "mcdc_sdev": mcdc_total_sdev[:n_region],
        "mcnp_sdev": mcnp_total_sdev[:n_region],
        "mcdc_relerr": mcdc_total_relerr[:n_region],
        "mcnp_relerr": mcnp_total_relerr[:n_region],
        "cross_diff": cross_diff,
        "total_abs_diff": total_abs_diff,
        "z_score": z_score,
    }


def collect_convergence_data():
    """Load every available history count; skip (with a warning) any pair of
    files that isn't present yet."""
    n_values, results = [], []
    for n_label in HISTORY_COUNTS:
        mcdc_path = os.path.join(MCDC_DIR, MCDC_TEMPLATE.format(n=n_label))
        mcnp_path = os.path.join(MCNP_DIR, MCNP_TEMPLATE.format(n=n_label))
        if not (os.path.exists(mcdc_path) and os.path.exists(mcnp_path)):
            print(f"[skip] {n_label}: missing "
                  f"{'MC/DC' if not os.path.exists(mcdc_path) else 'MCNP'} file")
            continue
        n_values.append(float(n_label))
        results.append(load_history(n_label))
        print(f"[ok]   {n_label}: loaded {mcdc_path} and {mcnp_path}")
    return np.array(n_values), results


# =============================================================================
# Plot + summary table
# =============================================================================
def plot_convergence(n_values, results, regions=PLOT_REGIONS, out_path=OUT_PATH):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if len(n_values) < 2:
        print("Need at least two history counts with both files present to "
              "plot convergence trends; only found:", n_values)
        return

    order = np.argsort(n_values)
    n_values = n_values[order]
    results = [results[i] for i in order]

    fig, axes = plt.subplots(1, len(regions), figsize=(5.5 * len(regions), 5),
                              sharey=False)
    if len(regions) == 1:
        axes = [axes]

    for ax, region in zip(axes, regions):
        mcdc_relerr = np.array([r["mcdc_relerr"][region] for r in results])
        mcnp_relerr = np.array([r["mcnp_relerr"][region] for r in results])

        ax.loglog(n_values, mcdc_relerr, "o-", label="MC/DC native rel. error", color="tab:blue")
        ax.loglog(n_values, mcnp_relerr, "s-", label="MCNP native rel. error", color="tab:orange")

        # N^(-1/2) reference slope, anchored to the first MC/DC point
        ref_mcdc = mcdc_relerr[0] * np.sqrt(n_values[0] / n_values)
        ax.loglog(n_values, ref_mcdc, "k--", alpha=0.5, label=r"$N^{-1/2}$ reference")

        ax.set_xlabel("Particle histories, N")
        ax.set_ylabel("Relative error / difference")
        ax.set_title(REGION_LABELS.get(region, f"Region {region}"))
        ax.grid(True, which="both", ls=":", alpha=0.6)
        ax.legend(fontsize=8)

    fig.suptitle("Convergence: native statistical error, MC/DC vs. MCNP")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"\nNative-error convergence plot written to: {out_path}")


def plot_cross_diff_all_regions(n_values, results, out_path=CROSS_DIFF_OUT_PATH):
    """Single plot: MC/DC-vs-MCNP relative difference in total flux,
    averaged across all regions into one line per N, with the region-to-
    region spread shown as a shaded band."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if len(n_values) < 2:
        print("Need at least two history counts with both files present to "
              "plot convergence trends; only found:", n_values)
        return

    order = np.argsort(n_values)
    n_values = n_values[order]
    results = [results[i] for i in order]

    # (N_hist, N_region) matrix of cross-code relative differences
    cross_diff_matrix = np.array([r["cross_diff"] for r in results])

    mean_diff = np.nanmean(cross_diff_matrix, axis=1)
    min_diff = np.nanmin(cross_diff_matrix, axis=1)
    max_diff = np.nanmax(cross_diff_matrix, axis=1)

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.fill_between(n_values, min_diff, max_diff, color="tab:green", alpha=0.15,
                     label="min-max across regions")
    ax.loglog(n_values, mean_diff, "o-", color="tab:green",
              label="Mean rel. diff. across all regions")

    # N^(-1/2) reference slope, anchored to the first averaged point
    ref = mean_diff[0] * np.sqrt(n_values[0] / n_values)
    ax.loglog(n_values, ref, "k--", alpha=0.6, label=r"$N^{-1/2}$ reference")

    ax.set_xlabel("Particle histories, N")
    ax.set_ylabel("MC/DC vs. MCNP relative difference (total flux)")
    ax.set_title("Cross-code relative difference, averaged over all regions")
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Cross-code difference plot written to: {out_path}")


DIRECT_DIFF_OUT_PATH = os.path.join(MCDC_DIR, "direct_difference_convergence.png")


def plot_direct_difference(n_values, results, out_path=DIRECT_DIFF_OUT_PATH):
    """Single line: total absolute difference |MC/DC - MCNP|, summed over
    all regions, vs. N -- reproduces the earlier "direct convergence"
    style (unnormalized, not averaged/relative) with an N^(-1/2) reference."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if len(n_values) < 2:
        print("Need at least two history counts with both files present to "
              "plot convergence trends; only found:", n_values)
        return

    order = np.argsort(n_values)
    n_sorted = n_values[order]
    results_sorted = [results[i] for i in order]

    total_abs_diff = np.array([r["total_abs_diff"] for r in results_sorted])

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.loglog(n_sorted, total_abs_diff, "o-", color="tab:green", linewidth=2,
              markersize=8, label="Total absolute difference |MC/DC - MCNP|")

    # N^(-1/2) reference slope, anchored to the first point
    ref = total_abs_diff[0] * np.sqrt(n_sorted[0] / n_sorted)
    ax.loglog(n_sorted, ref, "--", color="tab:green", alpha=0.6,
              label=r"$N^{-1/2}$ reference")

    ax.set_xlabel("N (total source particles)")
    ax.set_ylabel(r"Total absolute difference [1/cm$^2$ per source photon]")
    ax.set_title("Direct MC/DC vs MCNP Difference Convergence\n"
                  "1-10 MeV uniform source, multi-material spheres")
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Direct difference convergence plot written to: {out_path}")


SIGNIFICANCE_OUT_PATH = os.path.join(MCDC_DIR, "significance_convergence.png")


def plot_significance(n_values, results, regions=PLOT_REGIONS, out_path=SIGNIFICANCE_OUT_PATH):
    """Plot the disagreement's statistical significance (z-score = |MC/DC -
    MCNP| / combined sigma) vs. N. If z-score GROWS with N, the disagreement
    is a systematic bias that will not go away with more histories -- it is
    NOT statistical noise, even though both codes' own relative errors are
    shrinking as expected."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if len(n_values) < 2:
        print("Need at least two history counts with both files present to "
              "plot convergence trends; only found:", n_values)
        return

    order = np.argsort(n_values)
    n_sorted = n_values[order]
    results_sorted = [results[i] for i in order]

    fig, ax = plt.subplots(figsize=(8, 6))
    for region in regions:
        z = np.array([r["z_score"][region] for r in results_sorted])
        ax.semilogx(n_sorted, z, "o-", label=REGION_LABELS.get(region, f"Region {region}"))

    ax.axhline(1.0, color="gray", ls=":", alpha=0.7, label="1-sigma agreement")
    ax.axhline(3.0, color="gray", ls="--", alpha=0.7, label="3-sigma agreement")
    ax.set_xlabel("Particle histories, N")
    ax.set_ylabel(r"Significance of disagreement, $|\Delta| / \sigma_{combined}$")
    ax.set_title("Is the MC/DC-MCNP disagreement statistical noise or a systematic bias?")
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Significance plot written to: {out_path}")


DIFF_VS_UNCERTAINTY_OUT_PATH = os.path.join(MCDC_DIR, "mcdc_vs_mcnp_uncertainty.png")


def plot_diff_vs_uncertainty(n_values, results, out_path=DIFF_VS_UNCERTAINTY_OUT_PATH):
    """Single plot, aggregated across all regions: MC/DC's and MCNP's own
    statistical uncertainty, each shrinking as N^(-1/2) as expected, each
    with its own reference slope anchored to its first point."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if len(n_values) < 2:
        print("Need at least two history counts with both files present to "
              "plot convergence trends; only found:", n_values)
        return

    order = np.argsort(n_values)
    n_sorted = n_values[order]
    results_sorted = [results[i] for i in order]

    # Aggregate each code's own statistical uncertainty: quadrature sum
    # across regions (independent tallies).
    mcdc_agg_sigma = np.array(
        [np.sqrt((r["mcdc_sdev"] ** 2).sum()) for r in results_sorted]
    )
    mcnp_agg_sigma = np.array(
        [np.sqrt(np.nansum(r["mcnp_sdev"] ** 2)) for r in results_sorted]
    )

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.loglog(n_sorted, mcdc_agg_sigma, "o-", color="tab:blue",
              label=r"MC/DC statistical uncertainty ($1\sigma$, all regions)")
    ax.loglog(n_sorted, mcnp_agg_sigma, "s-", color="tab:orange",
              label=r"MCNP statistical uncertainty ($1\sigma$, all regions)")

    # N^(-1/2) reference, anchored to each code's own first point
    ref_mcdc = mcdc_agg_sigma[0] * np.sqrt(n_sorted[0] / n_sorted)
    ax.loglog(n_sorted, ref_mcdc, "--", color="tab:blue", alpha=0.5,
              label=r"$N^{-1/2}$ reference (MC/DC)")
    ref_mcnp = mcnp_agg_sigma[0] * np.sqrt(n_sorted[0] / n_sorted)
    ax.loglog(n_sorted, ref_mcnp, "--", color="tab:orange", alpha=0.5,
              label=r"$N^{-1/2}$ reference (MCNP)")

    ax.set_xlabel("N (total source particles)")
    ax.set_ylabel(r"Statistical uncertainty [1/cm$^2$ per source photon]")
    ax.set_title("MC/DC and MCNP statistical uncertainty, summed over all regions\n"
                  "1-10 MeV uniform source, multi-material spheres")
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Difference-vs-uncertainty plot written to: {out_path}")


DIFF_TABLE_OUT_PATH = os.path.join(MCDC_DIR, "difference_table.png")


def plot_difference_table(n_values, results, out_path=DIFF_TABLE_OUT_PATH):
    """Render a table image: for each N, the aggregate MC/DC-vs-MCNP
    percent difference in total flux, summed over all regions."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    order = np.argsort(n_values)
    n_sorted = n_values[order]
    results_sorted = [results[i] for i in order]

    rows = []
    for n, r in zip(n_sorted, results_sorted):
        mcnp_sum = r["mcnp_total"].sum()
        pct_diff = 100.0 * r["total_abs_diff"] / mcnp_sum
        rows.append([f"{n:.0e}", f"{pct_diff:.3f}%"])

    fig, ax = plt.subplots(figsize=(4.5, 0.6 + 0.45 * len(rows)))
    ax.axis("off")
    table = ax.table(
        cellText=rows,
        colLabels=["N (histories)", "MC/DC vs. MCNP difference"],
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.8)
    ax.set_title("Aggregate MC/DC vs. MCNP difference in total flux\n"
                  "(summed over all regions)", fontsize=11, pad=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Difference table written to: {out_path}")


def print_summary_table(n_values, results, regions=PLOT_REGIONS):
    order = np.argsort(n_values)
    n_sorted = n_values[order]
    results_sorted = [results[i] for i in order]

    for region in regions:
        print(f"\n{REGION_LABELS.get(region, f'Region {region}')}")
        print(f"{'N':>12} {'MC/DC flux':>14} {'MC/DC relerr':>14} "
              f"{'MCNP flux':>14} {'MCNP relerr':>14} {'cross-code diff':>16} "
              f"{'z-score':>10}")
        for n, r in zip(n_sorted, results_sorted):
            print(f"{n:>12.0e} {r['mcdc_total'][region]:>14.5e} "
                  f"{r['mcdc_relerr'][region]:>14.4f} "
                  f"{r['mcnp_total'][region]:>14.5e} "
                  f"{r['mcnp_relerr'][region]:>14.4f} "
                  f"{r['cross_diff'][region]:>16.4f} "
                  f"{r['z_score'][region]:>10.2f}")


# =============================================================================
if __name__ == "__main__":
    n_values, results = collect_convergence_data()
    if len(n_values) == 0:
        print("No matching MC/DC + MCNP file pairs found. Check MCDC_DIR / "
              "MCNP_DIR / the filename templates at the top of this script.")
        sys.exit(1)

    print_summary_table(n_values, results)
    plot_convergence(n_values, results)
    plot_cross_diff_all_regions(n_values, results)
    plot_direct_difference(n_values, results)
    plot_significance(n_values, results)
    plot_diff_vs_uncertainty(n_values, results)
    plot_difference_table(n_values, results)
