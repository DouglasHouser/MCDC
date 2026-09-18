# BENCHMARK 2: Simple Spherical Scatterer

## Quick Context
Benchmark 2 tests photon transport around a simple spherical scatterer—a 1 cm radius sphere of absorbing/scattering material embedded in vacuum. This benchmark measures both uncollided and first-collided flux at observation points outside the sphere, validating the scattered photon contribution formula. Like Benchmark 1, it requires constant-cross-section physics, but adds the geometric complexity of a finite scattering region.

**Reference Theory:** Lent and Wilcox (LLNL), point-detector flux formula for scattering sphere.

**Status:** BLOCKED — Requires same constant-cross-section physics as Benchmark 1, plus validation of first-scatter kernel.

## Architectural Update: PhotonReaction Implementation
The photon transport code now uses an **object-oriented PhotonReaction architecture** (`mcdc/object_/photon_reaction.py`). Benchmark 2 will inherit the constant-XS infrastructure from Benchmark 1, which follows this architecture:
- Constant-XS reactions are represented as `PhotonReactionBase` subclasses
- `interface.py` dispatches to appropriate reaction objects based on material type
- Material dispatch logic in the transport loop automatically selects `ConstantCrossSectionMaterial` handlers vs. standard `PhotonMaterial` handlers

## READ FIRST (Documentation)
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` (Physics location and structure)
- `photon-transport-docs/VALIDATION_STRATEGY.md` (Benchmark validation approach)
- LA-12196 "MCNP: Photon Benchmark Problems" (Whalen, Hollowell, Hendricks, Los Alamos 1991) — Benchmark 2 section

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon_transport_code\
```

## What Benchmark 2 Tests

**Geometry:** 
- Central point isotropic source at origin
- Scattering sphere: radius = 1.0 cm, centered at origin, filled with absorbing/scattering material
- Outside the sphere: vacuum
- Observation points: 10 locations from 1.5 to 10 cm from center (outside sphere)

**Physics:**
- σ_scat = 0.3 σ_tot
- σ_abs = 0.7 σ_tot
- 1 MFP = 1 cm (σ_tot = 1 cm⁻¹)
- Isotropic scattering (no energy loss)

**Measure:** Particle current at spherical detector surfaces at distances 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0 cm from the center.

## Analytical Solution

The observed flux is the sum of two components:

$$\Phi(a) = \Phi_0(a) + \Phi_1(a)$$

**Uncollided flux** (direct from source to observer, unscattered):
$$\Phi_0(a) = \frac{\exp(-\sigma_t \cdot 1)}{4\pi a^2} = \frac{\exp(-1)}{4\pi a^2}$$

where the factor $\exp(-\sigma_t \cdot 1)$ accounts for attenuation through the 1 cm sphere.

**First-scatter contribution** (source → scatter point inside sphere → observer):

$$\Phi_1(a) = \sigma_s \int_0^1 \int_0^\pi \frac{\exp(-\sigma_t r)}{4\pi r^2} \times \frac{\exp(-\sigma_t \ell)}{4\pi \ell^2} \times 2\pi r \sin\theta \, dr \, d\theta$$

where:
- Integration radius $r \in [0, 1]$ cm (inside sphere)
- $\theta$ is the scattering angle (from source through scattering point to observer)
- $\ell$ is the distance from scattering point to observer at distance $a$

This integral is computed numerically; reference values are tabulated in Lent & Wilcox.

## Prerequisites

**Benchmark 2 depends on Benchmark 1 infrastructure:**
- ✅ ConstantCrossSectionMaterial class
- ✅ constant_xs_collision physics function
- ✅ sample_isotropic_scatter distribution

No new physics functions are required; only geometry and tally setup.

## Geometry and Source Setup

### Geometry: Scattering Sphere + Vacuum

```python
# Scattering material
material_sphere = ConstantCrossSectionMaterial(
    sigma_total=1.0,
    sigma_scatter=0.3,
    sigma_absorb=0.7,
    name="scattering_sphere"
)

# Sphere surfaces
s_sphere = mcdc.Surface.Sphere(center=[0,0,0], radius=1.0, name="sphere_boundary")
s_detector_1p5 = mcdc.Surface.Sphere(center=[0,0,0], radius=1.5, name="detector_1p5")
s_detector_2p0 = mcdc.Surface.Sphere(center=[0,0,0], radius=2.0, name="detector_2p0")
s_detector_2p5 = mcdc.Surface.Sphere(center=[0,0,0], radius=2.5, name="detector_2p5")
s_detector_3p0 = mcdc.Surface.Sphere(center=[0,0,0], radius=3.0, name="detector_3p0")
s_detector_4p0 = mcdc.Surface.Sphere(center=[0,0,0], radius=4.0, name="detector_4p0")
s_detector_5p0 = mcdc.Surface.Sphere(center=[0,0,0], radius=5.0, name="detector_5p0")
s_detector_6p0 = mcdc.Surface.Sphere(center=[0,0,0], radius=6.0, name="detector_6p0")
s_detector_7p0 = mcdc.Surface.Sphere(center=[0,0,0], radius=7.0, name="detector_7p0")
s_detector_8p0 = mcdc.Surface.Sphere(center=[0,0,0], radius=8.0, name="detector_8p0")
s_detector_10p0 = mcdc.Surface.Sphere(center=[0,0,0], radius=10.0, name="detector_10p0", boundary_condition="vacuum")

# Cells
c_sphere = mcdc.Cell(region=-s_sphere, fill=material_sphere)
c_vacuum = mcdc.Cell(region=+s_sphere & -s_detector_10p0)

# Tallies at each detector surface
detector_radii = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]
for i, r in enumerate(detector_radii):
    tally = mcdc.Tally(
        surface=s_detector_list[i], 
        scores=["flux"], 
        name=f"flux_{r}cm"
    )
```

### Source

Isotropic point source at origin:

```python
mcdc.Source(position=[0.0, 0.0, 0.0], energy=1.0, particle_type="photon")
```

## Comparison Script: Expected Results

The compare.py script must:

1. Read `benchmark_2.h5`
2. For each tally radius $a$ in [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]:
   - Extract flux_mean and flux_sdev from HDF5
   - Compute total crossing: `crossing_MCDC = flux_mean × 4π a²`
   - Compute uncollided crossing (analytical): `crossing_0 = exp(-1) / (4π a²) × 4π a² = exp(-1)`
   - Compute first-scatter crossing (reference): `crossing_1 = reference_value[a]` (hardcoded from Lent & Wilcox or MCNP)
   - Expected total: `crossing_expected = crossing_0 + crossing_1`
   - Compute ratio: `R_MCDC = crossing_MCDC / crossing_expected`

3. Print table:
   ```
   | Radius (cm) | Flux_uncollided | Flux_1scatter | Flux_MCDC ±1σ | Ratio R |
   |-------------|-----------------|----------------|--------------|---------|
   | 1.5         | 0.0632          | ...            | ...          | ...     |
   ```

4. **Pass criterion:** All ratios R within ±10% of 1.0 (i.e., 0.90 ≤ R ≤ 1.10)

## Deliverables (Code Files)

### 1. Test Problem
`photon_transport_code/MCNP_Verification_Tests/benchmark_2_spherical_scatterer/problem.py`

Must:
- Define ConstantCrossSectionMaterial with σ_total=1.0, σ_scatter=0.3, σ_absorb=0.7
- Create sphere geometry (scattering region + vacuum + detector shells)
- Create tallies at 10 detector radii
- Set 200,000 particles × 100 batches
- Output to `benchmark_2.h5`
- Disable the progress bar for outputs (`mcdc.settings.use_progress_bar = False`)

### 2. Comparison Script
`photon_transport_code/MCNP_Verification_Tests/benchmark_2_spherical_scatterer/compare.py`

Must:
- Read benchmark_2.h5
- Compute uncollided and first-scatter contributions
- Compare MCDC result vs. expected (uncollided + first-scatter)
- Print pass/fail verdict

### 3. Reference Data
Hardcoded in compare.py — first-scatter flux values at each detector radius (from Lent & Wilcox tables or MCNP run):

```python
# Expected uncollided crossing at any detector radius:
UNCOLLIDED_CROSSING = math.exp(-1.0)  # ~0.3679

# Expected first-scatter crossing (from reference):
FIRST_SCATTER_REFERENCE = {
    1.5: 0.0XXX,  # To be filled from Lent & Wilcox or MCNP
    2.0: 0.0XXX,
    2.5: 0.0XXX,
    3.0: 0.0XXX,
    4.0: 0.0XXX,
    5.0: 0.0XXX,
    6.0: 0.0XXX,
    7.0: 0.0XXX,
    8.0: 0.0XXX,
    10.0: 0.0XXX,
}
```

## Requirements

✅ Uses ConstantCrossSectionMaterial (from Benchmark 1)  
✅ Geometry: 1 cm scattering sphere + vacuum + 10 detector spheres  
✅ Source: isotropic point source at origin  
✅ Tallies: surface flux on 10 detector surfaces  
✅ problem.py syntax correct and runs without error  
✅ compare.py reads HDF5 and computes flux components  
✅ compare.py compares vs. analytical + reference formulas  
✅ All docstrings present in compare.py helper functions  
✅ Black formatting passes (88 char line length)  
✅ No hardcoded paths; uses relative paths from working directory  

## Validation (from VALIDATION_STRATEGY.md)

Run these checks after creating files:

```bash
# 1. Problem file syntax
python -c "exec(open('photon_transport_code/MCNP_Verification_Tests/benchmark_2_spherical_scatterer/problem.py').read()); print('✓ problem.py syntax OK')"

# 2. Compare script syntax
python -c "exec(open('photon_transport_code/MCNP_Verification_Tests/benchmark_2_spherical_scatterer/compare.py').read()); print('✓ compare.py syntax OK')"

# 3. Geometry sanity check (after benchmark runs):
#    - Ensure 10 tallies are created
#    - Verify each tally has flux/mean and flux/sdev datasets
python -c "import h5py; f = h5py.File('photon_transport_code/MCNP_Verification_Tests/benchmark_2_spherical_scatterer/benchmark_2.h5', 'r'); print(f'Tallies: {list(f[\"tallies\"].keys())}')" 
```

## Success Criteria

✅ `problem.py` created in correct directory  
✅ `compare.py` created in correct directory  
✅ problem.py defines scattering material with σ_t=1.0, σ_s=0.3, σ_a=0.7  
✅ Geometry has scattering sphere (r=1.0 cm) + 10 detector shells  
✅ Source is isotropic point source at origin  
✅ Tallies record surface flux on all 10 detectors  
✅ compare.py reads benchmark_2.h5 without error  
✅ compare.py computes uncollided + first-scatter + total fluxes  
✅ compare.py prints PASS/FAIL table with ratios  
✅ No syntax errors or import errors  
✅ Files ready for MCDC simulation after Benchmark 1 physics integration  

## Implementation Notes

### Updates from PHOTON_REACTION_IMPLEMENTATION.md

Benchmark 2 uses the same constant-cross-section infrastructure as Benchmark 1. With the PhotonReaction refactoring now complete:
- `interface.py` has the refactored collision dispatch that delegates to reaction objects
- `PhotonReactionBase` and subclasses are available for implementation of constant-XS reactions
- Material type dispatch is in place for differentiating `ConstantCrossSectionMaterial` from `PhotonMaterial`

**For Benchmark 2:**
1. ✅ Constant-XS physics infrastructure (isotropic scattering, absorption) from Benchmark 1 is reused
2. Focus on geometry implementation: concentric spheres, scattering sphere + vacuum regions
3. No new physics functions required; only geometry and tally setup

### Before Benchmark 2 Can Run:

#### Dependencies (from Benchmark 1):
1. ✅ `ConstantCrossSectionMaterial` class fully implemented
2. ✅ Constant-XS reaction classes in place (isotropic scattering, absorption)
3. ✅ `sample_isotropic_scatter()` function implemented
4. ✅ Material dispatch logic in transport loop correctly routes to constant-XS reactions

#### Code Changes for Benchmark 2 Only:
1. Create `problem.py` with sphere geometry + vacuum + 10 detector tallies (no new physics required)
2. Create `compare.py` to read HDF5 and compute buildup factors vs. analytical formula

#### Verification After PHOTON_REACTION_IMPLEMENTATION:
- Confirm `interface.py` dispatch logic works for `ConstantCrossSectionMaterial`
- Verify Benchmark 1 still passes after refactoring
- Then create and test Benchmark 2 geometry and tallies

**Key point:** Benchmark 2 uses **ConstantCrossSectionMaterial** (same as Benchmark 1), NOT HDF5 data. The physics functions do not depend on `native.py` or HDF5; they use user-specified cross-sections.

## IMPORTANT

**Do NOT run Benchmark 2 until Benchmark 1 infrastructure is complete.** Both tests depend on ConstantCrossSectionMaterial and isotropic scattering physics.

**The uncollided component has a closed-form solution** (`exp(-1)`) that can be checked independently. If MCDC uncollided flux differs significantly from this, debug geometry/source/tally setup before troubleshooting scatter physics.

**First-scatter reference values must be obtained from either:**
1. Lent & Wilcox tables (if available in literature)
2. MCNP run with same problem geometry (provides ground truth)
3. Numerical integration of Lent & Wilcox formula with high precision

