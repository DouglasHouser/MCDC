"""
Comparison script for Benchmark 1a: Pure Absorption, Constant Cross Section.

Reads benchmark_1a.h5, extracts surface flux tallies, and compares to the
analytical solution I_analytic(r) = exp(-r) for sigma_total = 1.0 cm^-1.

MCDC's surface "flux" tally accumulates Σ(w/|μ|) / N_particle without dividing
by surface area, so the reported value is already the per-source-particle
current crossing the sphere — directly comparable to exp(-r). No 4πr² factor.

Usage:
    cd photon_transport_code/MCNP_Verification_Tests/benchmark_1a_const_pure_absorption/
    python compare.py [benchmark_1a.h5]

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
# Reference data: analytical current I(r) = exp(-sigma_total * r)
# with sigma_total = 1.0 cm^-1
# ---------------------------------------------------------------------------

# INITIAL_DISTANCES = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0]
# DISTANCES = [x / 10 for x in INITIAL_DISTANCES]

DISTANCES = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0]
I_ANALYTIC = [math.exp(-r) for r in DISTANCES]

PASS_THRESHOLD = 0.05  # 5 % relative error


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

    def _tally_key(k):
        # "surface_tally_10" -> 10 ; falls back to string for odd names so that
        # tallies sort numerically (0,1,2,...,10) not lexicographically (0,1,10,2).
        tail = k.rsplit("_", 1)[-1]
        return (0, int(tail)) if tail.isdigit() else (1, k)

    with h5py.File(h5_path, "r") as f:
        tally_group = f.get("tallies", f)
        keys = sorted(tally_group.keys(), key=_tally_key)

        for key in keys:
            entry = tally_group[key]
            if "flux" in entry:
                mean = float(np.squeeze(entry["flux"]["mean"][()]))
                std = float(np.squeeze(entry["flux"]["sdev"][()]))
                flux_means.append(mean)
                flux_stds.append(std)

    return flux_means, flux_stds


def load_n_history(h5_path):
    """Total simulated histories (N_particle * N_batch), or None if unavailable."""
    with h5py.File(h5_path, "r") as f:
        s = f.get("settings")
        if s is None or "N_particle" not in s:
            return None
        n_particle = int(np.squeeze(s["N_particle"][()]))
        n_batch = int(np.squeeze(s["N_batch"][()])) if "N_batch" in s else 1
        return n_particle * max(n_batch, 1)


def run_comparison(h5_path):
    """
    Load results, compute currents, compare to analytic, print pass/fail table.

    Parameters
    ----------
    h5_path : str
        Path to benchmark_1a.h5.
    """
    flux_means, flux_stds = load_surface_flux(h5_path)

    if len(flux_means) != len(DISTANCES):
        print(
            f"ERROR: expected {len(DISTANCES)} surface tallies, "
            f"got {len(flux_means)}"
        )
        sys.exit(1)

    # Per-particle statistical resolution floor: a single source particle carries
    # weight 1, so the smallest current MC can resolve is ~1 / N_history. Analytic
    # values below this floor (e.g. exp(-25) ~ 1.4e-11) are physically unmeasurable
    # and must not be scored as failures.
    n_history = load_n_history(h5_path)
    floor = (1.0 / n_history) if n_history else 0.0

    print()
    print("Benchmark 1a: Pure Absorption — Comparison to Analytical Solution")
    print("=" * 72)
    print(
        f"{'r (MFP)':>8}  {'I_sim':>12}  {'I_analytic':>12}  "
        f"{'rel_err (%)':>12}  {'Status':>8}"
    )
    print("-" * 72)

    all_pass = True
    for r, flux, std, i_ref in zip(DISTANCES, flux_means, flux_stds, I_ANALYTIC):
        i_sim = flux
        rel_err = abs(i_sim - i_ref) / i_ref if i_ref > 0 else float("nan")
        if i_ref < floor:
            # Below the MC resolution floor — unmeasurable, not a pass/fail point.
            status = "N/A"
        elif rel_err <= PASS_THRESHOLD:
            status = "PASS"
        else:
            status = "FAIL"
            all_pass = False
        print(
            f"{r:>8.1f}  {i_sim:>12.6e}  {i_ref:>12.6e}  "
            f"{100.0 * rel_err:>12.2f}  {status:>8}"
        )

    print("-" * 72)
    overall = "ALL PASS" if all_pass else "SOME FAILURES"
    print(f"Overall: {overall}")
    print()
    return all_pass


if __name__ == "__main__" and sys.argv[0].endswith(".py"):
    h5_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_HERE, "benchmark_1a.h5")
    passed = run_comparison(h5_file)
    sys.exit(0 if passed else 1)
