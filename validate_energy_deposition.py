"""
Validation for the photon energy-deposit mesh tally (analog collision estimator).

The tally accumulates MeV deposited locally per source particle, summed per voxel
(recoil electrons, photoelectrons/Auger, pair kinetic energy). Annihilation and
fluorescence photons carry energy away and deposit it at their own later sites.

Cases (one mcdc.run() per subprocess, selected by env var CASE):

  * smoke : Al slab, 1 MeV beam, mesh scores=["flux","energy-deposit"].
            Confirms the dataset appears, shaped like the mesh, alongside flux.
  * pe    : thick Pb slab, 0.1 MeV beam (below pair threshold, fluorescence off).
            The slab is many mfp thick so leakage ~ 0: every source photon deposits
            essentially all of its 0.1 MeV via Compton recoils + photoelectric.
            => sum(energy-deposit) per source particle ~= 0.1 MeV. This is both the
            photoelectric hand-calc and the energy-balance closure.
  * fluor_on / fluor_off : Pb slab, 0.15 MeV (above the Pb K-edge). Local deposition
            must be LOWER with fluorescence ON (characteristic X-rays escape/relocate).

Usage:
    python validate_energy_deposition.py --mode numba --no-progress_bar
(the driver spawns the individual cases as subprocesses, matching validate_fluorescence.py)
"""

import os
import subprocess
import sys

import numpy as np

_SRC_E_PE = 0.1     # MeV, below pair threshold
_SRC_E_FL = 0.15    # MeV, above Pb K-edge (~88 keV)


def _run_case(case):
    import mcdc

    if case == "smoke":
        mat = mcdc.PhotonMaterial(elements=[13], densities=[0.06026], name="aluminum")
        s_left = mcdc.Surface.PlaneX(x=0.0, boundary_condition="vacuum")
        s_right = mcdc.Surface.PlaneX(x=25.0, boundary_condition="vacuum")
        mcdc.Cell(region=+s_left & -s_right, fill=mat)
        mcdc.Source(
            position=[0.0, 0.0, 0.0], direction=[1.0, 0.0, 0.0],
            energy=1.0, particle_type="photon",
        )
        mesh = mcdc.MeshStructured(x=np.linspace(0.0, 25.0, 51))
        mcdc.Tally(mesh=mesh, scores=["flux", "energy-deposit"])
        mcdc.settings.N_particle = 20000
        mcdc.settings.N_batch = 5
        mcdc.settings.rng_seed = 42
        mcdc.settings.output_name = "edep_smoke"

    elif case == "pe":
        # Lead: strong photoelectric at 0.1 MeV, short mfp. 8 cm >> mfp -> ~no leakage.
        pb = mcdc.PhotonMaterial(elements=[82], densities=[0.03297], name="lead")
        s_left = mcdc.Surface.PlaneX(x=0.0, boundary_condition="vacuum")
        s_right = mcdc.Surface.PlaneX(x=8.0, boundary_condition="vacuum")
        mcdc.Cell(region=+s_left & -s_right, fill=pb)
        mcdc.Source(
            position=[0.0, 0.0, 0.0], direction=[1.0, 0.0, 0.0],
            energy=_SRC_E_PE, particle_type="photon",
        )
        mesh = mcdc.MeshStructured(x=np.linspace(0.0, 8.0, 41))
        mcdc.Tally(mesh=mesh, scores=["energy-deposit"])
        mcdc.settings.N_particle = 40000
        mcdc.settings.N_batch = 5
        mcdc.settings.rng_seed = 7
        mcdc.settings.photon_fluorescence = False
        mcdc.settings.output_name = "edep_pe"

    elif case in ("fluor_on", "fluor_off"):
        pb = mcdc.PhotonMaterial(elements=[82], densities=[0.03297], name="lead")
        s_left = mcdc.Surface.PlaneX(x=0.0, boundary_condition="vacuum")
        s_right = mcdc.Surface.PlaneX(x=8.0, boundary_condition="vacuum")
        mcdc.Cell(region=+s_left & -s_right, fill=pb)
        mcdc.Source(
            position=[0.0, 0.0, 0.0], direction=[1.0, 0.0, 0.0],
            energy=_SRC_E_FL, particle_type="photon",
        )
        mesh = mcdc.MeshStructured(x=np.linspace(0.0, 8.0, 41))
        mcdc.Tally(mesh=mesh, scores=["energy-deposit"])
        mcdc.settings.N_particle = 40000
        mcdc.settings.N_batch = 5
        mcdc.settings.rng_seed = 99
        mcdc.settings.photon_fluorescence = (case == "fluor_on")
        mcdc.settings.output_name = "edep_" + case
    else:
        raise SystemExit(f"unknown CASE={case}")

    mcdc.settings.use_progress_bar = False
    mcdc.run()


def _read(path, tally_name="tracklength_tally_0"):
    import h5py

    with h5py.File(path, "r") as f:
        t = f["tallies/" + tally_name]
        scores = list(t.keys())
        out = {"scores": scores}
        if "energy-deposit" in t:
            out["edep_mean"] = np.asarray(t["energy-deposit/mean"][()])
            out["edep_sdev"] = np.asarray(t["energy-deposit/sdev"][()])
        if "flux" in t:
            out["flux_mean"] = np.asarray(t["flux/mean"][()])
        if "grid" in t and "x" in t["grid"]:
            out["x"] = np.asarray(t["grid/x"][()])
    return out


def _drive():
    here = os.path.dirname(os.path.abspath(__file__))
    cases = ["smoke", "pe", "fluor_off", "fluor_on"]
    for c in cases:
        env = dict(os.environ, CASE=c)
        subprocess.run(
            [sys.executable, __file__, "--mode", "numba", "--no-progress_bar"],
            cwd=here, env=env, check=True,
        )

    ok = True

    # --- 1. Smoke: dataset exists, shaped like the mesh, next to flux ---------
    print("\n================ 1. Smoke test ================")
    s = _read("edep_smoke.h5")
    print(f"scores present: {s['scores']}")
    assert "energy-deposit" in s["scores"], "energy-deposit dataset missing!"
    assert "flux" in s["scores"], "flux dataset missing (co-tally broke)!"
    print(f"energy-deposit mean shape: {s['edep_mean'].shape}  (mesh has 50 x-bins)")
    assert s["edep_mean"].shape == s["flux_mean"].shape
    assert s["edep_mean"].size == 50
    assert np.all(s["edep_mean"] >= 0.0)
    assert s["edep_mean"].sum() > 0.0
    print("PASS: energy-deposit {mean,sdev} present, mesh-shaped, non-negative.")

    # --- 2. Photoelectric / energy-balance closure ---------------------------
    print("\n================ 2. Photoelectric hand-calc / energy balance ===========")
    pe = _read("edep_pe.h5")
    total = float(pe["edep_mean"].sum())
    frac = total / _SRC_E_PE
    print(f"source energy      : {_SRC_E_PE:.4f} MeV/particle")
    print(f"total deposited    : {total:.4f} MeV/particle")
    print(f"deposited fraction : {frac:.4f}   (expect ~1.0: thick Pb, no pair, fluor off)")
    assert 0.95 <= frac <= 1.0 + 1e-6, f"energy balance not closed: fraction={frac}"
    print("PASS: essentially all source energy deposited (leakage negligible).")

    # --- 3. Fluorescence A/B --------------------------------------------------
    print("\n================ 3. Fluorescence A/B ================")
    on = _read("edep_fluor_on.h5")
    off = _read("edep_fluor_off.h5")
    dep_on = float(on["edep_mean"].sum())
    dep_off = float(off["edep_mean"].sum())
    print(f"total local deposit  ON = {dep_on:.5f} MeV   OFF = {dep_off:.5f} MeV")
    print("Expected: ON < OFF (characteristic X-rays escape / deposit elsewhere).")
    assert dep_on < dep_off, "fluorescence did not reduce local deposition!"
    print("PASS: local deposition is lower with fluorescence ON.")

    print("\nAll energy-deposition validations passed.")
    return ok


if __name__ == "__main__":
    case = os.environ.get("CASE", "")
    if case:
        _run_case(case)
    else:
        _drive()
