"""
A/B validation for photoelectric characteristic X-ray fluorescence.

A small lead sphere is driven by a mono-energetic isotropic point source above
the Pb K-edge (150 keV).  The escaping-photon energy spectrum is tallied on the
outer surface with fine (1 keV) energy bins.

Usage
-----
    python validate_fluorescence.py --mode numba          # run both + report
    FLUOR=on  python validate_fluorescence.py --mode numba # one case -> fluor_on.h5
    FLUOR=off python validate_fluorescence.py --mode numba # one case -> fluor_off.h5

The on/off case is selected by the ``FLUOR`` environment variable (not argv, so
mcdc's own ``--mode``/``--no-progress_bar`` CLI flags pass through untouched).

With fluorescence ON, sharp peaks appear near the Pb K-alpha (~75 keV) and
K-beta (~85 keV) lines; with it OFF those peaks are absent.
"""

import os
import subprocess
import sys

import numpy as np

_SRC_E = 0.15          # MeV, above the Pb K-edge (~88 keV)
_RADIUS = 0.08         # cm  (~2 mfp at 150 keV in Pb)
_E_BINS = np.linspace(0.01, 0.16, 151)  # 1 keV bins
_N_PARTICLE = 400000
_N_BATCH = 20


def build_and_run(fluorescence):
    import mcdc

    pb = mcdc.PhotonMaterial(elements=[82], densities=[0.03297], name="lead")

    inner = mcdc.Surface.Sphere(center=[0, 0, 0], radius=_RADIUS, boundary_condition="none")
    outer = mcdc.Surface.Sphere(
        center=[0, 0, 0], radius=_RADIUS * 1.001, boundary_condition="vacuum"
    )
    mcdc.Cell(region=-inner, fill=pb)
    mcdc.Cell(region=+inner & -outer, fill=pb)

    mcdc.Source(position=[0.0, 0.0, 0.0], energy=_SRC_E, particle_type="photon")

    mcdc.Tally(surface=inner, scores=["flux"], energy=_E_BINS)

    mcdc.settings.N_particle = _N_PARTICLE
    mcdc.settings.N_batch = _N_BATCH
    mcdc.settings.rng_seed = 12345
    mcdc.settings.photon_fluorescence = fluorescence
    mcdc.settings.output_name = "fluor_on" if fluorescence else "fluor_off"
    mcdc.settings.use_progress_bar = False

    mcdc.run()


def read_spectrum(path):
    import h5py

    with h5py.File(path, "r") as f:
        tally = f["tallies/surface_tally_0"]
        e_grid = tally["grid/energy"][()]
        flux = tally["flux/mean"][()]
    return e_grid, np.asarray(flux).ravel()


def compare():
    here = os.path.dirname(os.path.abspath(__file__))
    for flag in ("on", "off"):
        env = dict(os.environ, FLUOR=flag)
        subprocess.run(
            [sys.executable, __file__, "--mode", "numba", "--no-progress_bar"],
            cwd=here,
            env=env,
            check=True,
        )

    e_on, s_on = read_spectrum("fluor_on.h5")
    e_off, s_off = read_spectrum("fluor_off.h5")
    centers = 0.5 * (e_on[:-1] + e_on[1:])

    def band(centers, spec, lo, hi):
        m = (centers > lo) & (centers < hi)
        return spec[m].sum()

    ka_on = band(centers, s_on, 0.072, 0.077)
    ka_off = band(centers, s_off, 0.072, 0.077)
    kb_on = band(centers, s_on, 0.083, 0.087)
    kb_off = band(centers, s_off, 0.083, 0.087)

    print("\n================ Fluorescence A/B ================")
    print(f"Source energy: {_SRC_E*1e3:.0f} keV   (Pb K-edge ~88 keV)")
    print(f"K-alpha band (72-77 keV):  ON={ka_on:.4e}   OFF={ka_off:.4e}")
    print(f"K-beta  band (83-87 keV):  ON={kb_on:.4e}   OFF={kb_off:.4e}")
    print("--------------------------------------------------")
    print("Expected: ON >> OFF in both bands (characteristic lines present).")
    # Peaks near the source energy should be comparable (unaffected).
    print("==================================================\n")


if __name__ == "__main__":
    fluor = os.environ.get("FLUOR", "")
    if fluor == "on":
        build_and_run(True)
    elif fluor == "off":
        build_and_run(False)
    else:
        compare()
