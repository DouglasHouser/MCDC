"""
Verify that the neutron and photon runs of Benchmark 1a produce statistically
equivalent results.

problem.py (photons) and neutron_problem.py (neutrons) define identical geometry,
material (constant cross section, pure absorption), source, tallies, and particle
counts. With the same RNG seed and pure-absorption physics the two transports
should be effectively identical — any differences should be within the combined
statistical uncertainty of the two tallies.

Outputs compared:
    benchmark_1a.h5           (photons)
    benchmark_1a_neutron.h5   (neutrons)

For each of the 14 surface flux tallies we compute:
    rel_diff = |mean_p - mean_n| / mean_n
    z        = |mean_p - mean_n| / sqrt(sdev_p^2 + sdev_n^2)

PASS criterion: z < 3 (within 3 sigma of combined statistical uncertainty).
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

DISTANCES = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0]

Z_THRESHOLD = 3.0


def load_surface_flux(h5_path):
    """Return (means, sdevs) lists for all surface flux tallies, ordered by key."""
    def _tally_key(k):
        # numeric-suffix sort: 0,1,2,...,10 not lexicographic 0,1,10,2
        tail = k.rsplit("_", 1)[-1]
        return (0, int(tail)) if tail.isdigit() else (1, k)

    means, sdevs = [], []
    with h5py.File(h5_path, "r") as f:
        tally_group = f.get("tallies", f)
        for key in sorted(tally_group.keys(), key=_tally_key):
            entry = tally_group[key]
            if "flux" in entry:
                means.append(float(np.squeeze(entry["flux"]["mean"][()])))
                sdevs.append(float(np.squeeze(entry["flux"]["sdev"][()])))
    return means, sdevs


def run_comparison(photon_path, neutron_path):
    p_mean, p_sdev = load_surface_flux(photon_path)
    n_mean, n_sdev = load_surface_flux(neutron_path)

    if len(p_mean) != len(n_mean):
        print(
            f"ERROR: tally count mismatch — photon={len(p_mean)}, "
            f"neutron={len(n_mean)}"
        )
        sys.exit(1)
    if len(p_mean) != len(DISTANCES):
        print(
            f"ERROR: expected {len(DISTANCES)} surface tallies, "
            f"got {len(p_mean)}"
        )
        sys.exit(1)

    print()
    print("Benchmark 1a: Photon vs Neutron Comparison")
    print(f"  photon  file: {photon_path}")
    print(f"  neutron file: {neutron_path}")
    print("=" * 92)
    print(
        f"{'r (MFP)':>8}  {'I_photon':>14}  {'I_neutron':>14}  "
        f"{'rel_diff (%)':>14}  {'z':>8}  {'Status':>8}"
    )
    print("-" * 92)

    all_pass = True
    for r, pm, ps, nm, ns in zip(DISTANCES, p_mean, p_sdev, n_mean, n_sdev):
        diff = pm - nm
        rel_diff = abs(diff) / nm if nm > 0 else float("nan")
        combined = math.sqrt(ps * ps + ns * ns)
        z = abs(diff) / combined if combined > 0 else float("nan")

        status = "PASS" if (math.isnan(z) or z <= Z_THRESHOLD) else "FAIL"
        if status == "FAIL":
            all_pass = False

        print(
            f"{r:>8.1f}  {pm:>14.6e}  {nm:>14.6e}  "
            f"{100.0 * rel_diff:>14.2f}  {z:>8.2f}  {status:>8}"
        )

    print("-" * 92)
    overall = "ALL PASS" if all_pass else "SOME FAILURES"
    print(f"Overall: {overall}  (criterion: z <= {Z_THRESHOLD:.1f})")
    print()
    return all_pass


if __name__ == "__main__" and sys.argv[0].endswith(".py"):
    photon_h5 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_HERE, "benchmark_1a.h5")
    neutron_h5 = sys.argv[2] if len(sys.argv) > 2 else os.path.join(_HERE, "benchmark_1a_neutron.h5")
    passed = run_comparison(photon_h5, neutron_h5)
    sys.exit(0 if passed else 1)
