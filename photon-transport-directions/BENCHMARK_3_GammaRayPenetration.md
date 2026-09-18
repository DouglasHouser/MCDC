# BENCHMARK 3: Point Source in Infinite Material (Gamma Ray Penetration)

## Quick Context
Benchmark 3 validates MCDC photon transport physics against real gamma-ray cross sections and experimental buildup factor data. Four sub-cases measure particle flux (and energy buildup factor) at varying distances in infinite aluminum and lead at 1.0 and 10.0 MeV. Uses real NIST XCOM cross sections from reformatted HDF5 data (`data/mcdc/`) and the Goldstein & Wilkins (1954) analytical/tabulated results as ground truth. Unlike Benchmarks 1 & 2, this test uses MCDC's standard Compton + photoelectric + pair-production physics implemented via the new PhotonReaction object-oriented architecture.

**Reference Theory:** H. Goldstein and J. E. Wilkins (1954), *Calculations of the Penetration of Gamma Rays*, NYO-3075. LA-12196 "MCNP: Photon Benchmark Problems" (Whalen et al., 1991).

**Status:** READY — All required physics already implemented in MCDC via PhotonReaction classes. Data has been reformatted per FORMAT_PHOTON_DATA_MCDC.md and code has been updated per SWITCH_NATIVE_TO_DATA_MCDC.md. Ready to code and test.

## Architectural Update: PhotonReaction Implementation
Benchmark 3 directly benefits from the completed **object-oriented PhotonReaction refactoring** (`mcdc/object_/photon_reaction.py`):
- `PhotonReactionCompton` handles Klein-Nishina sampling via Kahn (1954) method
- `PhotonReactionPhotoelectric` marks photons as absorbed (alive=False)
- `PhotonReactionPairProduction` handles pair production above 1.022 MeV threshold
- `interface.py` collision() function delegates to the appropriate reaction class based on sampled reaction type
- **No changes to physics** — architecture refactoring preserves all calculations and interactions

## READ FIRST (Documentation)
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` (Cross-section loader location)
- `photon-transport-docs/VALIDATION_STRATEGY.md` (Benchmark validation approach)
- `FORMAT_PHOTON_DATA_MCDC.md` (✅ COMPLETED — Data reformatting)
- `SWITCH_NATIVE_TO_DATA_MCDC.md` (✅ COMPLETED — Code migration to HDF5)
- [Goldstein & Wilkins 1954 NYO-3075](https://www.osti.gov/biblio/4390626-calculations-penetration-gamma-rays-part-i) — Tables pp. 90-140 (four benchmark tables)

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon_transport_code\
```

## What Benchmark 3 Tests

**Overall purpose:** Validate that MCDC correctly implements Compton scattering, photoelectric absorption, and pair production using real cross sections at diagnostic energies (1.0 and 10.0 MeV).

**Geometry:** Point isotropic photon source at origin, surrounded by infinite medium (approximated by large concentric spheres with vacuum boundary).

**Measurement:** Particle flux (current) at spherical surfaces at distances of 1, 2, 4, and 7 mean free paths (MFP) from the source. Multiple MFPs test both uncollided flux (short distances) and heavily-scattered flux (long distances).

**Comparison metric:** **Particle Buildup Factor** $B_f$, defined as:

$$B_f = \frac{\text{Total particle crossing}}{\text{Uncollided particle crossing}}$$

The uncollided component is known analytically as $e^{-\mu r}$ where $\mu$ is the attenuation coefficient. If $B_f < B_e$ (energy buildup factor from tables), the code has a physics error.

## The Four Sub-Cases

| Sub-Case | Material | Energy | Status | MFP (cm) | Cross Sections |
|----------|----------|--------|--------|----------|---|
| 3a | Aluminum | 1.0 MeV | READY | 6.044 | σ_Compton=2.746, σ_PE=0.0, σ_PP=0.001 |
| 3b | Aluminum | 10.0 MeV | READY | 15.986 | σ_Compton=0.665, σ_PE=0.373, σ_PP=0.00004 |
| 3c | Lead | 1.0 MeV | READY | 1.306 | σ_Compton=17.182, σ_PE=0.0, σ_PP=6.028 |
| 3d | Lead | 10.0 MeV | READY | 1.809 | σ_Compton=4.193, σ_PE=12.401, σ_PP=0.168 |

## Implementation Notes

### Critical: Changes from PHOTON_REACTION_IMPLEMENTATION.md (COMPLETED)

Benchmark 3 directly benefits from the completed PhotonReaction refactoring. Key architectural changes already in place:

1. **Reaction Classes (COMPLETED):** `mcdc/object_/photon_reaction.py` contains:
   - `PhotonReactionBase` — Abstract base class
   - `PhotonReactionCompton` — Kahn (1954) sampling; updates energy and direction
   - `PhotonReactionPhotoelectric` — Sets alive=False; no secondary
   - `PhotonReactionPairProduction` — Respects 1.022 MeV threshold; sets alive=False

2. **Interface Refactoring (COMPLETED):** `photon_transport_code/transport/physics/photon/interface.py`
   - collision() function now samples reaction type (Compton, PE, PP)
   - Creates appropriate reaction object and calls perform_collision()
   - Delegates all physics to reaction classes; no inline code

3. **Data Source (COMPLETED):** Cross-section data now comes from HDF5 files in `data/mcdc/` (e.g., `data/mcdc/Al.h5`, `data/mcdc/Pb.h5`), NOT from hardcoded tables in `native.py`.

**For Benchmark 3 Implementation:**
- No physics implementation required; all reactions already coded and tested
- Focus entirely on benchmark problem setup and comparison script
- PhotonMaterial class automatically loads cross-section data from HDF5
- verify cross-section values match expected values at 1.0 and 10.0 MeV (see sub-case details below)

#### Verification Steps:
1. ✅ Verify `data/mcdc/Al.h5` exists and contains cross-sections at 1.0 and 10.0 MeV
2. ✅ Verify `data/mcdc/Pb.h5` exists and contains cross-sections at 1.0 and 10.0 MeV
3. ✅ Verify PhotonMaterial class correctly loads cross-section data from reformatted HDF5 files
4. ✅ Test that cross-section values extracted at 1.0 and 10.0 MeV match the reference values in the benchmark tables (see sub-case details below)

#### Cross-Section Verification:
Verify the following cross-sections from HDF5 files match the expected values at 1.0 and 10.0 MeV:

**Aluminum (Z=13) at 1.0 MeV:**
```
Expected cross-sections in barn/atom:
  σ_Compton ≈ 2.74582
  σ_PE ≈ 0.0
  σ_PP ≈ 0.00100
  σ_total ≈ 2.74682
```

**Aluminum at 10.0 MeV:**
```
Expected cross-sections in barn/atom:
  σ_Compton ≈ 0.66495
  σ_PE ≈ 0.37344
  σ_PP ≈ 0.00004
  σ_total ≈ 1.03843
```

**Lead (Z=82) at 1.0 MeV:**
```
Expected cross-sections in barn/atom:
  σ_Compton ≈ 17.18180
  σ_PE ≈ 0.0
  σ_PP ≈ 6.02800
  σ_total ≈ 23.20980
```

**Lead at 10.0 MeV:**
```
Expected cross-sections in barn/atom:
  σ_Compton ≈ 4.19291
  σ_PE ≈ 12.40100
  σ_PP ≈ 0.16809
  σ_total ≈ 16.76200
```

If cross-section values differ significantly from these benchmarks, check:
1. HDF5 file exists and contains correct MT codes (Compton, PE, pair production, total)
2. Energy interpolation is working correctly for 1.0 and 10.0 MeV
3. Unit conversion is correct (HDF5 stores in barn/atom; verify MCDC uses consistent units)
4. Density (atoms/barn·cm) calculation is correct

### Material Instantiation

PhotonMaterial class automatically loads cross-section data from HDF5 files (no user configuration needed):

```python
# Benchmark 3a: Aluminum at 1.0 MeV
al_3a = mcdc.PhotonMaterial(
    elements=[13],                      # Al (Z=13)
    densities=[0.06026],                # atoms/barn·cm
    name="aluminum_1mev"
)
```

The underlying cross-section loading from HDF5 happens inside PhotonMaterial automatically. Photon reactions (Compton via `PhotonReactionCompton`, PE via `PhotonReactionPhotoelectric`, PP via `PhotonReactionPairProduction`) are dispatched by the `interface.py` collision function based on sampled reaction type.

## Physics Configuration

All four cases use MCDC's standard photon physics via the PhotonReaction architecture:

```python
# Physics: 
#   - Compton scattering (Klein-Nishina) via PhotonReactionCompton
#   - Photoelectric absorption via PhotonReactionPhotoelectric  
#   - Pair production via PhotonReactionPairProduction
#
# No coherent (Thomson) scattering
# No electron transport (PE electrons absorbed in place, PP annihilation ignored)
#
# Dispatch mechanism: interface.py collision() samples reaction type and delegates
# to the appropriate PhotonReaction subclass's perform_collision() method
# Cross sections: NIST XCOM (via MCDC's native cross-section loader)
```

Example material creation:

```python
# Benchmark 3a: Aluminum at 1.0 MeV
al_3a = mcdc.PhotonMaterial(
    elements=[13],                      # Al (Z=13)
    densities=[0.06026],                # atoms/barn·cm
    name="aluminum_1mev"
)

# Benchmark 3c: Lead at 1.0 MeV
pb_3c = mcdc.PhotonMaterial(
    elements=[82],                      # Pb (Z=82)
    densities=[0.03297],                # atoms/barn·cm
    name="lead_1mev"
)
```

## Geometry and Source Setup (Common to All 3a-3d)

### Geometry: Concentric Shells at MFP Intervals

Each sub-case creates 5 concentric spheres at distances 1, 2, 4, 7, and 20 MFP from the origin. The MFP distance varies by case:

```python
# Example for Benchmark 3a (MFP = 6.044 cm at 1 MeV in Al)
MFP = 6.044  # cm

s1  = mcdc.Surface.Sphere(center=[0,0,0], radius=1*MFP)
s2  = mcdc.Surface.Sphere(center=[0,0,0], radius=2*MFP)
s4  = mcdc.Surface.Sphere(center=[0,0,0], radius=4*MFP)
s7  = mcdc.Surface.Sphere(center=[0,0,0], radius=7*MFP)
s20 = mcdc.Surface.Sphere(center=[0,0,0], radius=20*MFP, boundary_condition="vacuum")

c0 = mcdc.Cell(region=-s1,         fill=material)
c1 = mcdc.Cell(region=+s1 & -s2,   fill=material)
c2 = mcdc.Cell(region=+s2 & -s4,   fill=material)
c3 = mcdc.Cell(region=+s4 & -s7,   fill=material)
c4 = mcdc.Cell(region=+s7 & -s20,  fill=material)
```

### Tallies: Surface Flux at MFP Boundaries

Record particle flux (current) crossing outward at each shell:

```python
mcdc.Tally(surface=s1,  scores=["flux"], name="flux_1mfp")
mcdc.Tally(surface=s2,  scores=["flux"], name="flux_2mfp")
mcdc.Tally(surface=s4,  scores=["flux"], name="flux_4mfp")
mcdc.Tally(surface=s7,  scores=["flux"], name="flux_7mfp")
```

### Source: Isotropic Point at Origin

```python
# Benchmark 3a/3c: 1.0 MeV
mcdc.Source(position=[0.0, 0.0, 0.0], energy=1.0, particle_type="photon")

# Benchmark 3b/3d: 10.0 MeV
mcdc.Source(position=[0.0, 0.0, 0.0], energy=10.0, particle_type="photon")
```

### Settings

```python
mcdc.settings.N_particle = 200000
mcdc.settings.N_batch    = 100
mcdc.settings.rng_seed   = 12345
mcdc.settings.output_name = "benchmark_3a"  # (or 3b, 3c, 3d)
```

## Sub-Case Details and Expected Results

### Benchmark 3a: Aluminum at 1.0 MeV

**Working Directory:** `c:\Projects\MCDC`  
**Files to Create:**
- `photon_transport_code/MCNP_Verification_Tests/benchmark_3a_al_1mev/problem.py`
- `photon_transport_code/MCNP_Verification_Tests/benchmark_3a_al_1mev/compare.py`

**Material:** Aluminum Z=13, density n=0.06026 atoms/barn·cm

**Cross Sections at 1.0 MeV:**
```
σ_Compton = 2.74582 barn/atom
σ_PE      = 0.0 barn/atom
σ_PP      = 0.00100 barn/atom
σ_total   = 2.74682 barn/atom
```

**1 MFP:** 1 / (σ_total × n) = 1 / (2.74682 × 0.06026) = **6.044 cm**

**Expected Particle Buildup Factors (Goldstein & Wilkins 1954):**

| Distance | B_e (analytic) | B_e (MCNP) ±σ |
|----------|---|---|
| 1 MFP | 2.01 | 2.018 ± 0.020 |
| 2 MFP | 3.29 | 3.307 ± 0.059 |
| 4 MFP | 6.52 | 6.648 ± 0.254 |
| 7 MFP | 12.95 | 12.622 ± 0.936 |

**Pass Criterion:** B_f(MCDC) ≥ B_e (analytic) at all 4 distances. (Scattered photons carry less energy, so more particles are needed for same energy crossing.)

---

### Benchmark 3b: Aluminum at 10.0 MeV

**Working Directory:** `c:\Projects\MCDC`  
**Files to Create:**
- `photon_transport_code/MCNP_Verification_Tests/benchmark_3b_al_10mev/problem.py`
- `photon_transport_code/MCNP_Verification_Tests/benchmark_3b_al_10mev/compare.py`

**Material:** Same aluminum (Z=13, n=0.06026 atoms/barn·cm)

**Cross Sections at 10.0 MeV:**
```
σ_Compton = 0.66495 barn/atom
σ_PE      = 0.37344 barn/atom (now significant!)
σ_PP      = 0.00004 barn/atom (negligible)
σ_total   = 1.03843 barn/atom
```

**1 MFP:** 1 / (1.03843 × 0.06026) = **15.986 cm**

**Expected Particle Buildup Factors:**

| Distance | B_e (analytic) | B_e (MCNP) ±σ |
|----------|---|---|
| 1 MFP | 1.22 | 1.227 ± 0.013 |
| 2 MFP | 1.45 | 1.460 ± 0.029 |
| 4 MFP | 1.91 | 1.944 ± 0.081 |
| 7 MFP | 2.64 | 2.793 ± 0.201 |

**Note:** Buildup factor is **lower at 10 MeV** because photoelectric absorption becomes important, removing photons rather than scattering them.

---

### Benchmark 3c: Lead at 1.0 MeV

**Working Directory:** `c:\Projects\MCDC`  
**Files to Create:**
- `photon_transport_code/MCNP_Verification_Tests/benchmark_3c_pb_1mev/problem.py`
- `photon_transport_code/MCNP_Verification_Tests/benchmark_3c_pb_1mev/compare.py`

**Material:** Lead Z=82, density n=0.03297 atoms/barn·cm

**Cross Sections at 1.0 MeV:**
```
σ_Compton = 17.18180 barn/atom
σ_PE      = 0.0 barn/atom
σ_PP      = 6.02800 barn/atom (significant!)
σ_total   = 23.20980 barn/atom
```

**1 MFP:** 1 / (23.20980 × 0.03297) = **1.306 cm**

**Expected Particle Buildup Factors:**

| Distance | B_e (analytic) | B_e (MCNP) ±σ |
|----------|---|---|
| 1 MFP | 1.35 | 1.361 ± 0.006 |
| 2 MFP | 1.66 | 1.650 ± 0.013 |
| 4 MFP | 2.21 | 2.186 ± 0.028 |
| 7 MFP | 2.95 | 2.901 ± 0.058 |

**Note:** Much shorter MFP due to high-Z material. Pair production contributes significantly at this energy in Pb.

---

### Benchmark 3d: Lead at 10.0 MeV

**Working Directory:** `c:\Projects\MCDC`  
**Files to Create:**
- `photon_transport_code/MCNP_Verification_Tests/benchmark_3d_pb_10mev/problem.py`
- `photon_transport_code/MCNP_Verification_Tests/benchmark_3d_pb_10mev/compare.py`

**Material:** Same lead (Z=82, n=0.03297 atoms/barn·cm)

**Cross Sections at 10.0 MeV:**
```
σ_Compton = 4.19291 barn/atom
σ_PE      = 12.40100 barn/atom (dominates!)
σ_PP      = 0.16809 barn/atom
σ_total   = 16.76200 barn/atom
```

**1 MFP:** 1 / (16.76200 × 0.03297) = **1.809 cm**

**Expected Particle Buildup Factors:**

| Distance | B_e (analytic) | B_e (MCNP) ±σ |
|----------|---|---|
| 1 MFP | 1.09 | 1.089 ± 0.0062 |
| 2 MFP | 1.19 | 1.192 ± 0.0096 |
| 4 MFP | 1.46 | 1.478 ± 0.0179 |
| 7 MFP | 2.16 | 2.255 ± 0.0438 |

**Note:** Very short MFP (high attenuation). Photoelectric absorption dominates, suppressing buildup.

---

## compare.py: General Algorithm (for all 3a-3d)

The comparison script is identical in structure for all four cases; only the numerical constants (MFP, material name, expected values) change.

```python
import math
import h5py

def load_tally_data(h5_file, tally_name):
    """Load flux mean and standard deviation from HDF5."""
    with h5py.File(h5_file, "r") as f:
        mean = float(f[f"tallies/{tally_name}/flux/mean"][()])
        sdev = float(f[f"tallies/{tally_name}/flux/sdev"][()])
    return mean, sdev

def compute_buildup_factor(flux_mean, flux_sdev, radius_cm, mfp_cm):
    """
    Compute particle buildup factor B_f from surface flux tally.
    
    B_f = (flux_mean × 4πr²) / exp(-r/MFP)
    
    Returns: (B_f, B_f_1sigma_uncertainty)
    """
    mu = 1.0 / mfp_cm
    area = 4.0 * math.pi * radius_cm**2
    uncollided = math.exp(-mu * radius_cm)
    
    total_crossing = flux_mean * area
    B_f = total_crossing / uncollided
    B_f_sdev = (flux_sdev * area) / uncollided
    
    return B_f, B_f_sdev

# Main comparison (example for 3a)
MFP_CM = 6.044  # Benchmark 3a: Al at 1 MeV
EXPECTED_Be = {1: 2.01, 2: 3.29, 4: 6.52, 7: 12.95}
EXPECTED_MCNP_Be = {1: 2.018, 2: 3.307, 4: 6.648, 7: 12.622}
MFP_DISTANCES = [1, 2, 4, 7]

h5_file = "benchmark_3a.h5"
results = []

for mfp_dist in MFP_DISTANCES:
    radius_cm = mfp_dist * MFP_CM
    tally_name = f"flux_{mfp_dist}mfp"
    
    flux_mean, flux_sdev = load_tally_data(h5_file, tally_name)
    B_f, B_f_sdev = compute_buildup_factor(flux_mean, flux_sdev, radius_cm, MFP_CM)
    
    results.append({
        "mfp_distance": mfp_dist,
        "radius_cm": radius_cm,
        "B_e_analytic": EXPECTED_Be[mfp_dist],
        "B_e_mcnp": EXPECTED_MCNP_Be[mfp_dist],
        "B_f_mcdc": B_f,
        "B_f_sdev": B_f_sdev,
        "pass": B_f >= EXPECTED_Be[mfp_dist],
    })

# Print table
print(f"\n{'Distance':>10} {'B_e_table':>12} {'B_f_MCDC':>12} {'±1σ':>10} {'Pass':>6}")
print("-" * 52)
for r in results:
    status = "✓" if r["pass"] else "✗"
    print(f"{r['mfp_distance']:>8} MFP {r['B_e_analytic']:>12.3f} {r['B_f_mcdc']:>12.3f} "
          f"{r['B_f_sdev']:>10.3f} {status:>6}")

all_pass = all(r["pass"] for r in results)
print("\n" + ("PASS" if all_pass else "FAIL"))
```

## Deliverables

### Code Files (8 files total: 4 problem.py + 4 compare.py)

1. `photon_transport_code/MCNP_Verification_Tests/benchmark_3a_al_1mev/problem.py`
2. `photon_transport_code/MCNP_Verification_Tests/benchmark_3a_al_1mev/compare.py`
3. `photon_transport_code/MCNP_Verification_Tests/benchmark_3b_al_10mev/problem.py`
4. `photon_transport_code/MCNP_Verification_Tests/benchmark_3b_al_10mev/compare.py`
5. `photon_transport_code/MCNP_Verification_Tests/benchmark_3c_pb_1mev/problem.py`
6. `photon_transport_code/MCNP_Verification_Tests/benchmark_3c_pb_1mev/compare.py`
7. `photon_transport_code/MCNP_Verification_Tests/benchmark_3d_pb_10mev/problem.py`
8. `photon_transport_code/MCNP_Verification_Tests/benchmark_3d_pb_10mev/compare.py`

Each problem.py must:
- Define PhotonMaterial with correct element, density, and name
- Create concentric sphere geometry (5 shells at 1, 2, 4, 7, 20 MFP)
- Place isotropic source at origin (1.0 or 10.0 MeV depending on case)
- Create 4 surface flux tallies at 1, 2, 4, 7 MFP
- Set 200,000 particles, 100 batches, seed=12345
- Output to benchmark_3{a|b|c|d}.h5
- Disable the progress bar for outputs (`mcdc.settings.use_progress_bar = False`)

Each compare.py must:
- Read benchmark_3{a|b|c|d}.h5
- Extract flux tallies at all 4 distances
- Compute particle buildup factor B_f for each distance
- Compare against EXPECTED_Be table
- Print pass/fail table and final verdict

## Requirements

✅ Use MCDC's PhotonMaterial class (not constant-XS material)  
✅ Uses real NIST XCOM cross sections (automatically loaded by PhotonMaterial)  
✅ Geometry: 5-shell concentric spheres at correct MFP intervals  
✅ Source: isotropic point source at origin, correct energy  
✅ Tallies: surface flux at 4 diagnostic distances  
✅ Each problem.py runs without error (syntax check)  
✅ Each compare.py reads HDF5, computes B_f, compares vs. expected  
✅ All docstrings present and complete  
✅ Black formatting (88 char line length)  
✅ Cross-section values hardcoded in comments for traceability  

## Validation (from VALIDATION_STRATEGY.md)

After creating all files, run:

```bash
# 1. Syntax checks
for sub in 3a 3b 3c 3d; do
  python -c "exec(open('photon_transport_code/MCNP_Verification_Tests/benchmark_${sub}_*/problem.py').read()); print('✓ problem.py ${sub} syntax OK')"
  python -c "exec(open('photon_transport_code/MCNP_Verification_Tests/benchmark_${sub}_*/compare.py').read()); print('✓ compare.py ${sub} syntax OK')"
done

# 2. After running simulations:
python photon_transport_code/MCNP_Verification_Tests/benchmark_3a_al_1mev/compare.py
python photon_transport_code/MCNP_Verification_Tests/benchmark_3b_al_10mev/compare.py
python photon_transport_code/MCNP_Verification_Tests/benchmark_3c_pb_1mev/compare.py
python photon_transport_code/MCNP_Verification_Tests/benchmark_3d_pb_10mev/compare.py

# Expected output: All four should print PASS if physics is correct
```

## Success Criteria

✅ All 8 files created in correct directories  
✅ All problem.py files define PhotonMaterial correctly  
✅ All geometries have 5 concentric shells at correct MFP intervals  
✅ All sources are isotropic points at origin with correct energy  
✅ All tallies record surface flux at 4 distances  
✅ All compare.py files read HDF5 without error  
✅ All compare.py files compute B_f and compare vs. EXPECTED_Be  
✅ No syntax errors or import errors  
✅ All cross-section values match NIST XCOM at correct energies  
✅ All expected Be values match Goldstein & Wilkins 1954 tables  
✅ Files ready for end-to-end MCDC test (problem.py → compare.py)  

## Integration Dependencies

### Benchmark 3 Requires:
✅ MCDC photon physics already implemented (Compton, PE, PP)  
✅ PhotonMaterial class with element/density specification  
✅ NIST XCOM cross-section loader (mcdc.PhotonMaterial)  
✅ Surface flux tally capability  
✅ HDF5 output and reading (h5py)  

### Provides:
✅ End-to-end validation of MCDC photon transport  
✅ Ground truth comparison vs. Goldstein & Wilkins  
✅ Tests both low-energy (1 MeV) and high-energy (10 MeV) regimes  
✅ Tests both high-Z (Pb) and low-Z (Al) materials  
✅ Validates Compton scattering, PE absorption, and pair production in realistic scenarios  

## IMPORTANT

**Benchmark 3 is ready to code NOW.** No new physics functions are required—only problem setup and comparison script.

**All four sub-cases use identical code structure;** only numeric constants change. Create 3a first, then copy and modify for 3b, 3c, 3d.

**The pass criterion (B_f ≥ B_e) is strict by design.** If any case fails, it indicates a physics bug or cross-section error. Check:
1. Cross-section values match NIST XCOM at the correct energy
2. Material density is correct
3. Source energy matches the case (1.0 or 10.0 MeV)
4. Geometry creates shells at the correct MFP distances

**Do NOT use constant-cross-section materials for Benchmark 3.** Use MCDC's standard PhotonMaterial with real element numbers.
