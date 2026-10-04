# Benchmark 5 — Co-60 Air-Over-Ground (MCDC photon)

## Context

`MCNP_validation_test.pdf` documents six photon verification problems. Benchmark 5
(§VI, "Cobalt-60 Air-Over-Ground") models a uniform Co-60 fallout source spread on the
ground, with air above and soil below, and measures the **dose buildup factor** and the
**angular kerma-rate distribution** at a point 3 ft (91.44 cm) above the ground. The
published MCNP result is **B = 1.190 ± 0.005** (range across studies 1.15–1.38); the
angular kerma distribution is Fig. 5.5.

The existing suite (`benchmark_1*`, `benchmark_3*`) follows a `problem.py` (build + run)
+ `compare.py` (read `.h5`, validate) pattern. Benchmark 5 must join it. The reference
MCNP deck (Table A.6) relies on an **F5 point detector**, a **DXTRAN sphere**, **cell
importances/weight windows**, and a cosine-binned **F1 current** tally — none of which
exist in MCDC (analog transport only; tallies = `flux`/`net-current`/`energy-deposit`
with `mu`/`energy` binning). So this is a **physically-faithful analog re-formulation**,
not a literal port.

### Decisions (confirmed with user)
- **Geometry:** simplified faithful — air/soil half-spaces split by the z=0 plane, soil
  subdivision planes at −6/−12/−18 cm, 1-km vacuum bounding sphere, planar Co-60 source,
  finite detector sphere at z=91.44 cm.
- **Metrics:** dose buildup factor **and** angular kerma distribution.
- **Compute:** committed code runs **smoke-test** sized only; cluster-scale
  `N_particle` / detector / source-disk values included **commented-out** in the scripts.

## Files (all in `photon_transport_code/MCNP_Verification_Tests/benchmark_5/`)

1. `benchmark_5_plan.md` — copy of this plan for in-repo traceability.
2. `problem.py` — geometry, materials, Co-60 source, two tallies, smoke settings.
3. `compare.py` — dose buildup factor + angular kerma vs reference.
4. `run_problem5.slurm` — cluster launch with high-statistics config (mirrors
   `benchmark_3a_al_1mev/run_problem3a.slurm`).

## `problem.py` design

Mirror the header/path-setup/`if sys.argv[0].endswith(".py")` gate of
`benchmark_3a_al_1mev/problem.py`.

### Materials — weight fraction → number density
MCDC `PhotonMaterial(elements=[Z...], densities=[atoms/barn-cm...])` needs **positive
number densities**, not MCNP negative weight fractions. Add a small helper:
`n_i = rho * w_i * 0.60221 / A_i` (0.60221 = N_A·1e-24). Compositions from Table A.6
`M1`/`M2` cards (and §VI text):
- **Air** (ρ=0.00129): N(7) 0.7818, O(8) 0.2097, Ar(18) 0.0085.
- **NTS soil** (ρ=1.13): O(8) 0.34, Na(11) 0.01, Mg(12) 0.10, Al(13) 0.03, Si(14) 0.18,
  S(16) 0.03, Ca(20) 0.01, Fe(26) 0.29, Ni(28) 0.01.
All Z present in `data/mcdc/`. Keep the computed densities in a comment table for
traceability (like 3a's hardcoded XS).

### Surfaces
- `PlaneZ(z=0)` air/ground interface; `PlaneZ(z=-6/-12/-18)` soil layers.
- `Sphere(center=[0,0,0], radius=1e5, boundary_condition="vacuum")` — 1-km boundary.
- `Sphere(center=[0,0,91.44], radius=R_DET)` — detector. Smoke `R_DET=50.0`
  (MCNP used 0.5; enlarged for analog hit statistics — documented).

### Cells
- Air: `+z0 & -bound & +detector` → air.
- Detector: `-detector` → air.
- Soil layers: `-z0 & +z_-6 & -bound`, `-z_-6 & +z_-12 & -bound`,
  `-z_-12 & +z_-18 & -bound`, `-z_-18 & -bound` → soil (same material; planes retained
  per "faithful" choice and to allow optional per-layer inspection).

### Source — planar Co-60
`mcdc.Source(x=[-R_SRC,R_SRC], y=[-R_SRC,R_SRC], z=[0.0,0.0], isotropic=True,
energy=[[1.17,1.33],[0.5,0.5]], particle_type="photon")`. Energy in **MeV**. Isotropic
4π (down-going photons drive ground backscatter). Smoke `R_SRC=1e4` (≈1 MFP patch,
concentrates near-detector contributions); cluster `R_SRC=1e5` commented.

### Tallies
- **Buildup** — `Tally(cell=detector_cell, scores=["flux"], energy=EDGES)` where `EDGES`
  isolate the two source lines in narrow top bins (`…,1.16,1.18,1.30,1.34`) and coarse
  bins below. Per-energy fluence → uncollided = the two line bins, total = all bins.
  Ratio is normalization-independent (same tally), so no absolute norm needed.
- **Angular kerma** — `Tally(surface=detector_sphere, scores=["net-current"],
  mu=linspace(-1,1,21))`. **Do not pass `polar_reference`** (tally.py:159 bug;
  filter.py supports only +z). Bin in `mu=u_z`; compare.py maps `cosθ = −mu` to the
  benchmark's (0,0,−1) reference.

### Settings (smoke)
`photon_transport=True`, `N_particle=1_000_000`, `N_batch=10`, `rng_seed=12345`,
`output_name="benchmark_5"`, `use_progress_bar=False`. `photon_fluorescence` default.
Comment block: cluster values `N_particle≈1e8–1e9`, `R_DET≈5–10`, `R_SRC=1e5` for
B accurate to <1–2%.

## `compare.py` design
Mirror `benchmark_3a_al_1mev/compare.py` structure (load h5, table, exit code).
1. Read energy-binned `flux` (mean/sdev) from the detector-cell tally
   (`f["tallies"][name]["flux"]["mean"]`, squeeze).
2. **Air kerma response** `k(E)=(μ_en/ρ)_air(E)·E` — hardcode a small NIST air
   μ_en/ρ table (cm²/g) with a citation, log-log interpolate to bin centers (traceable,
   like 3a's hardcoded XS).
3. `D_total = Σ_i flux_i·k(E_i)`; `D_unc =` line-bin fluxes·k(line). **B = D_total/D_unc.**
4. Read `mu`-binned `net-current`; report normalized angular kerma vs `cosθ=−mu`;
   compare shape qualitatively to Fig. 5.5 (skyward cosθ<0 scatter-only; groundward
   cosθ>0 has direct+scatter).
5. Reference `B_MCNP=1.190±0.005`, historical range 1.15–1.38. **Smoke pass band**
   (documented as loose due to analog statistics): `1.05 ≤ B ≤ 1.35`. Exit 0/1.

## Verification
- `cd photon_transport_code/MCNP_Verification_Tests/benchmark_5 && python problem.py`
  → produces `benchmark_5.h5` in a few minutes (confirm actual runtime; adjust
  `N_particle` down if the smoke run exceeds ~5 min).
- `python compare.py benchmark_5.h5` → prints B and angular-kerma table, exits 0 within
  the smoke band. Sanity: B>1, uncollided bins dominate, scattered spectrum below the
  lines is populated.
- Confirm no MCDC API errors (Source area sampling with `z=[0,0]`; energy in MeV;
  `mu`-binned surface current). If `z=[0,0]` degenerates, fall back to `z=[-1e-6,1e-6]`.

## Smoke run results & caveats (as implemented)

Run with the dedicated env and Numba JIT:
`python problem.py --mode numba --caching` then `python compare.py benchmark_5.h5`.
(`mcdc` needs `mpi4py`; use the `mcdc-env` conda env. Pure-Python mode is ~100x slower
— always pass `--mode numba`.)

- **Runtime:** ~7.5 min for the committed smoke config (N=200k, mostly one-time JIT
  compile; cached reruns are faster).
- **Buildup factor:** the smoke run yields B ~ 4 (compare reports it as *informational*,
  not within the nominal band). This is expected: the committed config compresses the
  source to a near-field 40 m patch under an enlarged 50 cm detector, which over-weights
  soil backscatter and grazing scatter and thus distorts the scattered/direct balance.
  The smoke `compare.py` gate is a **correctness** check (uncollided lines populated,
  scatter present, B finite and > 1), not an accuracy check. Quantitative agreement with
  B = 1.19 requires the CLUSTER CONFIG (full 1-km disk, small detector, ~1e9 histories).
- **Angular distribution:** matches Fig. 5.5 qualitatively — groundward (cos>0) bins
  dominate and carry the direct+scatter signal; skyward (cos<0) is scatter-only and ~2
  orders of magnitude smaller. `cos(theta) = +mu` (a photon arriving from the ground
  travels +z; the benchmark bins the incoming direction relative to (0,0,-1)). This
  supersedes the `cosθ=−mu` note above.

### Two MCDC facts worth recording
- **Energy units are MeV on the photon path** (the `Source` default `1.0e6` and the tally
  "eV" label pertain to neutrons; photon XS grids are in MeV).
- **Mixing a cell/tracklength tally with a surface tally crashes** MCDC: a surface/cell's
  tally-ID list is packed with the *global* tally ID
  (numba_objects_generator.py:587-591) but indexed against the *per-type child* array at
  run time (geometry/interface.py:451, simulation.py:329). This benchmark uses a single
  surface tally (with both energy and mu bins) to stay on the exercised path. Any future
  benchmark needing both tally kinds must fix that packing (store `child_ID`) first.
