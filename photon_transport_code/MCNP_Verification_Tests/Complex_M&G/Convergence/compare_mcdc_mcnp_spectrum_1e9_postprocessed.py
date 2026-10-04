"""
Compare the matched 1e9-history MC/DC and MCNP energy-binned flux results
for the multi-material concentric sphere problem
(lead -> iron -> concrete -> water). The comparison covers the 1-10 MeV
uniform isotropic point-source run.

The 12 individual shells are aggregated into 4 materials using a
volume-weighted average:

    flux_material = sum(flux_shell * shell_volume) / sum(shell_volume)

The MC/DC results file supplies the energy-bin structure, so this script
automatically uses the correct number of bins instead of assuming the older
13-bin 1 MeV setup.

Inputs:
    MC/DC: mm_spheres_1to10mev_spec_1e9_results.txt
    MCNP : multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out

Outputs:
    spectrum_mcdc_vs_mcnp_1e9_by_material.png
        1x4 grouped-bar comparison, one panel per material.

    spectrum_mcdc_vs_mcnp_1e9_percent_difference.png
        1x4 signed percent-difference plot, one panel per material.

Both plots compare the matched 1e9-history MC/DC and MCNP runs, 1-10 MeV
uniform isotropic point source.
"""

import ast
import os
import re
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


_HERE = os.path.dirname(os.path.abspath(__file__))

MCDC_RESULTS_PATH = os.path.join(
    _HERE, "mm_spheres_1to10mev_spec_1e8_results.txt"
)
MCNP_OUT_PATH = os.path.join(
    _HERE, "multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out"
)

BAR_PLOT_PATH = os.path.join(
    _HERE, "spectrum_mcdc_vs_mcnp_1e8_by_material.png"
)
PERCENT_PLOT_PATH = os.path.join(
    _HERE, "spectrum_mcdc_vs_mcnp_1e8_percent_difference.png"
)

SHELLS = [
    ("lead", 2.0), ("lead", 4.0), ("lead", 6.0),
    ("iron", 10.0), ("iron", 14.0), ("iron", 18.0),
    ("concrete", 24.0), ("concrete", 30.0), ("concrete", 36.0),
    ("water", 46.0), ("water", 56.0), ("water", 66.0),
]

MATERIALS_ORDER = ["lead", "iron", "concrete", "water"]
N_REGIONS = len(SHELLS)

_ROW_RE = re.compile(
    r"^\s*(\d+)\s+(lead|iron|concrete|water)\s+([\d.]+)\s+(.*)$",
    re.IGNORECASE,
)
_EDGES_RE = re.compile(r"Bin edges \(MeV\):\s*(\[.*\])")
_TALLY_RE = re.compile(r"^1tally\s+4\b", re.IGNORECASE)
_CELL_RE = re.compile(r"^\s*cell\s+(\d+)\s*$", re.IGNORECASE)


def shell_volumes():
    """Volume [cm^3] of each shell in region order."""
    volumes = []
    r_inner = 0.0
    for _, r_outer in SHELLS:
        volumes.append((4.0 / 3.0) * np.pi * (r_outer**3 - r_inner**3))
        r_inner = r_outer
    return np.asarray(volumes, dtype=float)


_SDEV_HEADER_RE = re.compile(r"Standard deviation of the above", re.IGNORECASE)


def parse_mcdc(path):
    """
    Parse the MC/DC results table and its bin edges.

    The results file has TWO tables that share identical row formatting
    (region, material, r_vavg, then 40 values): the mean-flux table, and
    a "Standard deviation of the above" table right below it. _ROW_RE
    matches rows in both tables, so parsing is restricted to the block
    ABOVE the "Standard deviation" header -- otherwise the sdev rows
    (appearing later in the file) silently overwrite the correct flux
    values for every region.

    Returns
    -------
    energy_edges : ndarray, shape (n_energy + 1,)
    flux         : ndarray, shape (12, n_energy)
    """
    with open(path) as f:
        lines = f.readlines()

    energy_edges = None
    for line in lines:
        match = _EDGES_RE.search(line)
        if match:
            energy_edges = np.asarray(ast.literal_eval(match.group(1)), dtype=float)
            break

    if energy_edges is None or len(energy_edges) < 2:
        raise RuntimeError(
            f"Could not parse energy-bin edges from MC/DC results file: {path}"
        )

    n_energy = len(energy_edges) - 1
    flux = np.full((N_REGIONS, n_energy), np.nan, dtype=float)

    sdev_start = next(
        (i for i, line in enumerate(lines) if _SDEV_HEADER_RE.search(line)),
        len(lines),
    )

    for line in lines[:sdev_start]:
        match = _ROW_RE.match(line)
        if not match:
            continue

        region = int(match.group(1))
        if not (0 <= region < N_REGIONS):
            continue

        values = np.asarray(
            [float(v) for v in match.group(4).split()], dtype=float
        )
        if values.size == n_energy:
            flux[region, :] = values

    missing = np.where(~np.any(np.isfinite(flux), axis=1))[0]
    if missing.size:
        raise RuntimeError(
            f"MC/DC results file is missing region rows: {missing.tolist()}"
        )

    return energy_edges, flux


def parse_mcnp(path, n_energy):
    """
    Parse MCNP tally 4.

    Returns
    -------
    volumes : ndarray, shape (12,)
    flux    : ndarray, shape (12, n_energy)
    sigma   : ndarray, shape (12, n_energy)

    MCNP can report one extra leading energy interval (0 -> first requested
    edge). That first interval is NOT assumed to be identical to the first
    MC/DC interval. If it is present, it is retained here so main() can exclude
    the unmatched first interval from BOTH datasets before comparison.
    """
    with open(path) as f:
        lines = f.readlines()

    start = next(
        (i for i, line in enumerate(lines) if _TALLY_RE.match(line.strip())),
        None,
    )
    if start is None:
        raise RuntimeError(f"Could not find tally 4 in MCNP output: {path}")

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("===="):
            end = i
            break

    block = lines[start:end]

    # Parse MCNP-reported cell volumes where available.
    vol_by_cell = {}
    text_block = "".join(block)
    for match in re.finditer(
        r"cell:\s*((?:\d+\s*)+)\n\s*([\d.eE+\-\s]+)\n", text_block
    ):
        cell_ids = [int(v) for v in match.group(1).split()]
        values = [float(v) for v in match.group(2).split()]
        if len(cell_ids) == len(values):
            vol_by_cell.update(zip(cell_ids, values))

    flux_rows = {}
    sigma_rows = {}

    i = 0
    while i < len(block):
        match = _CELL_RE.match(block[i])
        if not match:
            i += 1
            continue

        cell = int(match.group(1))
        if not (1 <= cell <= N_REGIONS):
            i += 1
            continue

        # Find the "energy" header belonging to this cell.
        i += 1
        while i < len(block) and block[i].strip().lower() != "energy":
            if _CELL_RE.match(block[i]):
                break
            i += 1

        if i >= len(block) or block[i].strip().lower() != "energy":
            continue

        i += 1
        values = []
        rel_errors = []

        while i < len(block):
            stripped = block[i].strip()
            if not stripped:
                i += 1
                continue
            if stripped.lower().startswith("total"):
                i += 1
                break
            if _CELL_RE.match(block[i]):
                break

            parts = stripped.split()
            if len(parts) >= 3:
                try:
                    float(parts[0])  # upper energy edge
                    values.append(float(parts[1]))
                    rel_errors.append(float(parts[2]))
                except ValueError:
                    pass
            i += 1

        # Preserve an optional leading MCNP interval. It cannot safely be
        # compared directly with MC/DC's first bin unless the boundaries are
        # identical. main() handles the alignment by excluding the unmatched
        # first bin from BOTH datasets when this extra row is present.
        if len(values) not in (n_energy, n_energy + 1):
            raise RuntimeError(
                f"MCNP cell {cell} has {len(values)} energy rows; "
                f"expected {n_energy} or {n_energy + 1}."
            )

        flux_rows[cell] = np.asarray(values, dtype=float)
        sigma_rows[cell] = (
            np.asarray(values, dtype=float)
            * np.asarray(rel_errors, dtype=float)
        )

    expected = list(range(1, N_REGIONS + 1))
    missing = [cell for cell in expected if cell not in flux_rows]
    if missing:
        raise RuntimeError(
            f"Could not parse all MCNP tally cells. Missing: {missing}"
        )

    flux = np.vstack([flux_rows[cell] for cell in expected])
    sigma = np.vstack([sigma_rows[cell] for cell in expected])

    computed_volumes = shell_volumes()
    volumes = np.asarray(
        [vol_by_cell.get(cell, computed_volumes[cell - 1]) for cell in expected],
        dtype=float,
    )

    return volumes, flux, sigma


def aggregate_by_material(flux, volumes, sigma=None):
    """
    Volume-weight the three shells belonging to each material.

    For independent shell uncertainties:
        sigma_material =
            sqrt(sum((sigma_shell * V_shell)^2)) / sum(V_shell)
    """
    result = {}

    for material in MATERIALS_ORDER:
        idx = [
            i for i, (mat, _) in enumerate(SHELLS)
            if mat == material
        ]
        v = volumes[idx]
        v_total = v.sum()

        material_flux = (
            flux[idx, :] * v[:, None]
        ).sum(axis=0) / v_total

        material_sigma = None
        if sigma is not None:
            material_sigma = np.sqrt(
                ((sigma[idx, :] * v[:, None]) ** 2).sum(axis=0)
            ) / v_total

        result[material] = (material_flux, material_sigma)

    return result


def compare(mcdc_by_material, mcnp_by_material):
    """Build per-material flux and signed percent-difference arrays."""
    results = {}

    for material in MATERIALS_ORDER:
        mcdc_flux, _ = mcdc_by_material[material]
        mcnp_flux, mcnp_sigma = mcnp_by_material[material]

        with np.errstate(divide="ignore", invalid="ignore"):
            pct_diff = np.where(
                np.abs(mcnp_flux) > 0.0,
                (mcdc_flux - mcnp_flux) / mcnp_flux * 100.0,
                np.nan,
            )

        results[material] = {
            "f_mcdc": mcdc_flux,
            "f_mcnp": mcnp_flux,
            "s_mcnp": mcnp_sigma,
            "pct_diff": pct_diff,
        }

    return results


def print_summary(results):
    print("\nMatched 1e8-history MC/DC vs MCNP comparison")
    for material in MATERIALS_ORDER:
        pct = results[material]["pct_diff"]
        finite = pct[np.isfinite(pct)]
        print(
            f"{material:>10}: "
            f"mean signed % diff = {np.mean(finite):>8.3f}   "
            f"mean |% diff| = {np.mean(np.abs(finite)):>8.3f}   "
            f"max |% diff| = {np.max(np.abs(finite)):>8.3f}"
        )


def energy_labels(energy_edges, max_labels=10):
    """Readable x-axis labels without crowding all 40 bins."""
    n_energy = len(energy_edges) - 1
    labels = [""] * n_energy
    step = max(1, int(np.ceil(n_energy / max_labels)))

    for j in range(0, n_energy, step):
        labels[j] = f"{energy_edges[j]:.3g}–{energy_edges[j + 1]:.3g}"

    if not labels[-1]:
        labels[-1] = f"{energy_edges[-2]:.3g}–{energy_edges[-1]:.3g}"

    return labels


def plot_grouped_bars(results, energy_edges, path):
    """Grouped MC/DC/MCNP flux bars for the matched 1e8-history runs.

    Laid out as a 2x2 grid (one panel per material) rather than 1x4, so it
    reads better at paper column width.
    """
    n_energy = len(energy_edges) - 1
    x = np.arange(n_energy)
    width = 0.40
    labels = energy_labels(energy_edges)

    fig, axes = plt.subplots(2, 2, figsize=(14, 11), sharex=True)
    axes = axes.flatten()

    for panel_idx, (ax, material) in enumerate(zip(axes, MATERIALS_ORDER)):
        r = results[material]
        mcdc = np.where(r["f_mcdc"] > 0, r["f_mcdc"], np.nan)
        mcnp = np.where(r["f_mcnp"] > 0, r["f_mcnp"], np.nan)
        sigma = r["s_mcnp"]
        pct = r["pct_diff"]

        ax.bar(x - width / 2, mcdc, width, label="MC/DC 1e8")
        ax.bar(
            x + width / 2,
            mcnp,
            width,
            yerr=sigma,
            capsize=1.5,
            label="MCNP 1e8",
        )

        ax.set_yscale("log")
        ax.set_xticks(x)
        # Only the bottom row needs x-tick labels/xlabel; top row stays clean.
        is_bottom_row = panel_idx >= 2
        if is_bottom_row:
            ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
            ax.set_xlabel("Energy bin [MeV]")
        else:
            ax.set_xticklabels([])
        ax.set_title(material.capitalize())
        ax.grid(True, which="major", axis="y", alpha=0.25)

        finite = np.concatenate([
            mcdc[np.isfinite(mcdc)],
            mcnp[np.isfinite(mcnp)],
        ])
        if finite.size:
            ax.set_ylim(top=np.nanmax(finite) * 8)

        # Label only meaningful bins to keep the 40-bin plot readable.
        label_step = max(1, int(np.ceil(n_energy / 20)))
        for j in range(0, n_energy, label_step):
            if not np.isfinite(pct[j]):
                continue
            top = np.nanmax([mcdc[j], mcnp[j]])
            if np.isfinite(top) and top > 0:
                ax.text(
                    j,
                    top * 1.18,
                    f"{pct[j]:+.0f}%",
                    ha="center",
                    va="bottom",
                    fontsize=5.5,
                    rotation=90,
                )

    # Both left-column panels get the y-axis label; legend on the first panel.
    axes[0].set_ylabel(r"Flux [1/cm$^2$ per source photon]")
    axes[2].set_ylabel(r"Flux [1/cm$^2$ per source photon]")
    axes[0].legend(loc="upper left", fontsize=9)

    fig.suptitle(
        "MC/DC vs. MCNP Energy Spectrum by Material — Matched 1e8-History Runs\n"
        "1-10 MeV Uniform Isotropic Point Source, Pb → Fe → Concrete → Water; "
        "material flux volume-weighted over 3 shells",
        fontsize=13,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(path, dpi=220)
    plt.close(fig)
    print(f"Grouped flux comparison written to: {path}")


def plot_percent_difference(results, energy_edges, path):
    """Signed MC/DC-relative-to-MCNP percent difference for all energy bins."""
    n_energy = len(energy_edges) - 1
    x = np.arange(n_energy)
    labels = energy_labels(energy_edges)

    fig, axes = plt.subplots(1, 4, figsize=(24, 6), sharex=True)

    for ax, material in zip(axes, MATERIALS_ORDER):
        pct = results[material]["pct_diff"]

        ax.axhline(0.0, linewidth=1.0)
        ax.bar(x, pct, width=0.80)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
        ax.set_xlabel("Energy bin [MeV]")
        ax.set_title(material.capitalize())
        ax.grid(True, axis="y", alpha=0.25)

    axes[0].set_ylabel("MC/DC − MCNP [% of MCNP]")

    fig.suptitle(
        "Signed Energy-Bin Difference: MC/DC 1e8 vs. MCNP 1e8\n"
        "1-10 MeV Uniform Isotropic Point Source; Positive = MC/DC higher; negative = MC/DC lower",
        fontsize=13,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(path, dpi=220)
    plt.close(fig)
    print(f"Percent-difference comparison written to: {path}")


def main():
    energy_edges, mcdc_flux = parse_mcdc(MCDC_RESULTS_PATH)
    n_energy = len(energy_edges) - 1

    mcnp_volumes, mcnp_flux, mcnp_sigma = parse_mcnp(
        MCNP_OUT_PATH, n_energy
    )

    # Post-processing-only energy-bin alignment. If MCNP reports an extra
    # leading interval (typically 0 -> first requested edge), it is not equal
    # to MC/DC's first interval. Exclude that MCNP interval AND the first MC/DC
    # interval, leaving only bins whose boundaries match exactly. No transport
    # input or simulation result is modified.
    if mcnp_flux.shape[1] == n_energy + 1:
        print(
            "MCNP has one unmatched leading energy interval. Excluding the "
            "first MCNP bin and the first MC/DC bin for exact post-processing "
            "alignment."
        )
        mcnp_flux = mcnp_flux[:, 1:]
        mcnp_sigma = mcnp_sigma[:, 1:]
        mcdc_flux = mcdc_flux[:, 1:]
        energy_edges = energy_edges[1:]
        n_energy = len(energy_edges) - 1
    elif mcnp_flux.shape[1] != n_energy:
        raise RuntimeError(
            "MCNP and MC/DC energy-bin counts could not be aligned: "
            f"MC/DC={n_energy}, MCNP={mcnp_flux.shape[1]}"
        )

    mcdc_volumes = shell_volumes()

    if not np.allclose(
        mcdc_volumes, mcnp_volumes, rtol=1e-3, equal_nan=False
    ):
        print(
            "WARNING: MCNP-reported shell volumes differ from the geometry "
            "volumes used for MC/DC aggregation."
        )

    mcdc_by_material = aggregate_by_material(
        mcdc_flux, mcdc_volumes
    )
    mcnp_by_material = aggregate_by_material(
        mcnp_flux, mcnp_volumes, mcnp_sigma
    )

    results = compare(mcdc_by_material, mcnp_by_material)

    print(f"Exactly matched energy bins compared: {n_energy}")
    print(f"Energy range: {energy_edges[0]:.6g} to {energy_edges[-1]:.6g} MeV")
    print_summary(results)

    plot_grouped_bars(results, energy_edges, BAR_PLOT_PATH)
    plot_percent_difference(results, energy_edges, PERCENT_PLOT_PATH)


if __name__ == "__main__":
    main()
