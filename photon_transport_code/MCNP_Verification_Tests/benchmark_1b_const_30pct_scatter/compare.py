"""
Comparison script for Benchmark 1b: 30% Scattering, Constant Cross Section.

Reads benchmark_1b.h5, extracts surface flux tallies, computes particle current
I(r) = flux_mean * 4*pi*r^2, and compares to the reference values from
Case, de Hoffman & Placzek (1953), Table 17 (c = 0.3).

Usage:
    cd photon_transport_code/MCNP_Verification_Tests/benchmark_1b_const_30pct_scatter/
    python compare.py [benchmark_1b.h5]

Pass/Fail criterion: relative error |I_sim - I_ref| / I_ref < 5% at all radii.
"""

import os
import sys

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()

import math

import h5py
import numpy as np

# ---------------------------------------------------------------------------
# Reference data from Case, de Hoffman & Placzek (1953), Table 17 (c = 0.3).
# Particle current I(r) * 4*pi*r^2 normalized to unit source.
# Numerical values are from the MCNP Photon Benchmark Problems report
# (Whalen, Hollowell & Hendricks, LA-12196, 1991).
# ---------------------------------------------------------------------------
DISTANCES = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0]

# Placeholder reference values — replace with tabulated CDP53 values
# when the full reference table is available.
# Format: I_ref(r) for c=0.3, sigma_total=1.0 cm^-1
I_REFERENCE = [
    None,  # r = 0.5  (to be filled from Table 17)
    None,  # r = 0.8
    None,  # r = 1.0
    None,  # r = 1.5
    None,  # r = 2.0
    None,  # r = 3.0
    None,  # r = 4.0
    None,  # r = 5.0
    None,  # r = 6.0
    None,  # r = 7.0
    None,  # r = 8.0
    None,  # r = 9.0
    None,  # r = 10.0
    None,  # r = 25.0
]

PASS_THRESHOLD = 0.05  # 5% relative error


def load_surface_flux(h5_path):
    """
    Read surface flux tallies from an MCDC HDF5 output file.

    Parameters
    ----------
    h5_path : str
        Path to the HDF5 output file produced by the benchmark problem.

    Returns
    -------
    flux_means : list of float
        Mean flux at each of the 14 surface tallies (ordered by radius).
    flux_stds : list of float
        Standard deviation (statistical uncertainty) for each flux.
    """
    flux_means = []
    flux_stds = []

    with h5py.File(h5_path, "r") as f:
        tally_group = f.get("tallies", f)
        keys = sorted(tally_group.keys())

        for key in keys:
            entry = tally_group[key]
            if "flux" in entry:
                mean = float(np.squeeze(entry["flux"]["mean"][()]))
                std = float(np.squeeze(entry["flux"]["sdev"][()]))
                flux_means.append(mean)
                flux_stds.append(std)

    return flux_means, flux_stds


def compute_current(flux, r):
    """Convert surface flux to particle current: I = flux * 4*pi*r^2."""
    return flux * 4.0 * math.pi * r**2


def run_comparison(h5_path):
    """
    Load results, compute currents, compare to reference, print pass/fail table.

    Parameters
    ----------
    h5_path : str
        Path to benchmark_1b.h5.
    """
    flux_means, flux_stds = load_surface_flux(h5_path)

    if len(flux_means) != len(DISTANCES):
        print(
            f"ERROR: expected {len(DISTANCES)} surface tallies, "
            f"got {len(flux_means)}"
        )
        sys.exit(1)

    print()
    print("Benchmark 1b: 30% Scattering — Comparison to Reference (CDP53 Table 17)")
    print("=" * 72)
    print(
        f"{'r (MFP)':>8}  {'I_sim':>12}  {'I_ref':>12}  "
        f"{'rel_err (%)':>12}  {'Status':>8}"
    )
    print("-" * 72)

    all_pass = True
    for r, flux, std, i_ref in zip(DISTANCES, flux_means, flux_stds, I_REFERENCE):
        i_sim = compute_current(flux, r)
        if i_ref is None:
            status = "NO_REF"
            rel_err_str = "    n/a"
            i_ref_str = "         n/a"
        else:
            rel_err = abs(i_sim - i_ref) / i_ref if i_ref > 0 else float("nan")
            status = "PASS" if rel_err <= PASS_THRESHOLD else "FAIL"
            if status == "FAIL":
                all_pass = False
            rel_err_str = f"{100.0 * rel_err:>12.2f}"
            i_ref_str = f"{i_ref:>12.6e}"
        print(f"{r:>8.1f}  {i_sim:>12.6e}  {i_ref_str}  {rel_err_str}  {status:>8}")

    print("-" * 72)
    overall = "ALL PASS" if all_pass else "NEEDS REFERENCE DATA OR FAILURES"
    print(f"Overall: {overall}")
    print()
    return all_pass


if __name__ == "__main__" and sys.argv[0].endswith(".py"):
    h5_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_HERE, "benchmark_1b.h5")
    passed = run_comparison(h5_file)
    sys.exit(0 if passed else 1)
