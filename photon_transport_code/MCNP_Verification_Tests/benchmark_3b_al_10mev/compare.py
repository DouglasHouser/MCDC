"""
Comparison script for Benchmark 3b: Aluminum at 10.0 MeV.

Reads benchmark_3b.h5, extracts surface flux tallies at 1, 2, 4, 7 MFP, and
computes the particle buildup factor:

    B_f = flux_mean / exp(-r / MFP)

See benchmark_3a/compare.py for justification of the no-area convention used
by MCDC's surface flux tally.

Reference values (Goldstein & Wilkins 1954, NYO-3075):
    1 MFP: B_e = 1.22      (MCNP: 1.227 +/- 0.013)
    2 MFP: B_e = 1.45      (MCNP: 1.460 +/- 0.029)
    4 MFP: B_e = 1.91      (MCNP: 1.944 +/- 0.081)
    7 MFP: B_e = 2.64      (MCNP: 2.793 +/- 0.201)
"""

import os
import sys
import math

import h5py
import numpy as np

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.getcwd()

# ---------------------------------------------------------------------------
# Reference data (Goldstein & Wilkins 1954, NYO-3075)
# ---------------------------------------------------------------------------
MFP_CM = 15.986  # cm, Al at 10 MeV
MFP_DISTANCES = [1, 2, 4, 7]

EXPECTED_BE_ANALYTIC = {1: 1.22, 2: 1.45, 4: 1.91, 7: 2.64}
EXPECTED_BE_MCNP = {1: 1.227, 2: 1.460, 4: 1.944, 7: 2.793}


def load_surface_flux(h5_path):
    """
    Read surface flux tallies from an MCDC HDF5 output file in radial order.

    Parameters
    ----------
    h5_path : str
        Path to the HDF5 output file produced by the benchmark problem.

    Returns
    -------
    flux_means : list of float
        Mean flux at each of the four surface tallies (1, 2, 4, 7 MFP).
    flux_stds : list of float
        Standard deviation (statistical uncertainty) for each flux.
    """
    flux_means = []
    flux_stds = []

    with h5py.File(h5_path, "r") as f:
        tally_group = f["tallies"]
        keys = sorted(tally_group.keys(), key=lambda k: int(k.split("_")[-1]))

        for key in keys:
            entry = tally_group[key]
            if "flux" in entry:
                mean = float(np.squeeze(entry["flux"]["mean"][()]))
                std = float(np.squeeze(entry["flux"]["sdev"][()]))
                flux_means.append(mean)
                flux_stds.append(std)

    return flux_means, flux_stds


def compute_buildup_factor(flux_mean, flux_sdev, mfp_distance):
    """
    Compute particle buildup factor B_f from surface flux tally.

    Parameters
    ----------
    flux_mean : float
        Mean surface flux tally value at distance r = mfp_distance * MFP_CM.
    flux_sdev : float
        Standard deviation of the flux tally.
    mfp_distance : int
        Integer mean-free-path distance from the source.

    Returns
    -------
    B_f : float
        Particle buildup factor = flux_mean / exp(-mfp_distance).
    B_f_sdev : float
        Propagated 1-sigma uncertainty on B_f.
    """
    uncollided = math.exp(-mfp_distance)
    B_f = flux_mean / uncollided
    B_f_sdev = flux_sdev / uncollided
    return B_f, B_f_sdev


def run_comparison(h5_path):
    """
    Load tally data, compute buildup factors, and print pass/fail table.

    Parameters
    ----------
    h5_path : str
        Path to benchmark_3b.h5.

    Returns
    -------
    bool
        True if B_f >= B_e (analytic) at every diagnostic distance.
    """
    flux_means, flux_stds = load_surface_flux(h5_path)

    if len(flux_means) < len(MFP_DISTANCES):
        print(
            f"ERROR: expected at least {len(MFP_DISTANCES)} surface tallies, "
            f"got {len(flux_means)}"
        )
        sys.exit(1)

    print()
    print("Benchmark 3b: Aluminum at 10.0 MeV — Particle Buildup Factor")
    print("=" * 76)
    print(
        f"{'Distance':>10} {'B_e (G&W)':>12} {'B_e (MCNP)':>12} "
        f"{'B_f (MCDC)':>12} {'+/- 1 sigma':>14} {'Pass':>6}"
    )
    print("-" * 76)

    all_pass = True
    for i, mfp_dist in enumerate(MFP_DISTANCES):
        B_f, B_f_sdev = compute_buildup_factor(flux_means[i], flux_stds[i], mfp_dist)
        b_e = EXPECTED_BE_ANALYTIC[mfp_dist]
        b_mcnp = EXPECTED_BE_MCNP[mfp_dist]
        passed = B_f >= b_e
        if not passed:
            all_pass = False
        status = "PASS" if passed else "FAIL"
        print(
            f"{mfp_dist:>7} MFP {b_e:>12.3f} {b_mcnp:>12.3f} "
            f"{B_f:>12.3f} {B_f_sdev:>14.3f} {status:>6}"
        )

    print("-" * 76)
    overall = "ALL PASS" if all_pass else "FAIL"
    print(f"Overall: {overall}")
    print()
    return all_pass


if __name__ == "__main__" and sys.argv[0].endswith(".py"):
    h5_file = (
        sys.argv[1] if len(sys.argv) > 1 else os.path.join(_HERE, "benchmark_3b.h5")
    )
    passed = run_comparison(h5_file)
    sys.exit(0 if passed else 1)
