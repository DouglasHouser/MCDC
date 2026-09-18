# BENCHMARK 1: Infinite Medium, Constant Cross Section, Isotropic Scattering

## Quick Context
Benchmark 1 tests photon transport in an infinite homogeneous medium with energy-independent (constant) cross sections and isotropic scattering. This benchmark requires implementing constant-cross-section physics in MCDC—a new material type and collision physics that do not use real material data. Three sub-cases test varying scattering ratios: pure absorption, 30% scattering, and 90% scattering.

**Reference Theory:** Case, de Hoffman, Placzek (1953), *Introduction to the Theory of Neutron Diffusion*, Vol. 1, Tables 17 and 18.

## Architectural Update: PhotonReaction Implementation
The photon transport code has been refactored to use an **object-oriented PhotonReaction architecture** (`mcdc/object_/photon_reaction.py`) that handles collision dispatch. This refactoring:
- Moves collision physics into polymorphic reaction classes (Compton, Photoelectric, PairProduction)
- Delegates reaction selection from `interface.py` to the appropriate reaction object
- **Does NOT change physics** — preserves all existing interactions and calculations

For Benchmark 1, this means:
- The `constant_xs_collision()` function will be integrated into the material dispatch logic within `interface.py`
- When `ConstantCrossSectionMaterial` is implemented, its isotropic scattering reactions will use the same `perform_collision()` method pattern as existing reactions
- The transport loop will automatically select the correct collision handler based on material type


## READ FIRST (Documentation)
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` (Physics location and structure)
- `photon-transport-docs/VALIDATION_STRATEGY.md` (Benchmark validation approach)
- LA-12196 "MCNP: Photon Benchmark Problems" (Whalen, Hollowell, Hendricks, Los Alamos 1991) — Reference source

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon_transport_code\
```

## What Benchmark 1 Tests

Particle current at spherical surfaces in an infinite medium. A point isotropic source emits photons into a homogeneous medium where photons undergo either:
- **Pure absorption** (σ_abs = σ_tot, σ_scat = 0)
- **30% scattering** (σ_scat = 0.3 σ_tot, σ_abs = 0.7 σ_tot)  
- **90% scattering** (σ_scat = 0.9 σ_tot, σ_abs = 0.1 σ_tot)

For each case, measure particle current at spherical surfaces at distances:
0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0 MFP from the source.

**1 MFP = 1 cm** (by definition for this benchmark)

## MCDC Physics Additions Required

### 1. New Material Class: ConstantCrossSectionMaterial

**File location:** `mcdc_set/photon_material.py` (extend PhotonMaterial)

A material that accepts user-specified, energy-independent cross sections:

```python
class ConstantCrossSectionMaterial:
    """
    Photon material with constant (energy-independent) cross sections.
    
    Used for analytical benchmark testing where scattering and absorption
    are independent of photon energy.
    
    Attributes:
        sigma_total: Total cross section (cm^-1)
        sigma_scatter: Scattering cross section (cm^-1)
        sigma_absorb: Absorption cross section (cm^-1)
        name: Material identifier
    """
    
    def __init__(self, sigma_total, sigma_scatter, sigma_absorb, name=None):
        """
        Parameters:
            sigma_total (float): Total macroscopic cross section in cm^-1
            sigma_scatter (float): Scattering cross section in cm^-1
            sigma_absorb (float): Absorption cross section in cm^-1
            name (str): Optional material name for logging
        """
        pass
    
    def validate(self):
        """
        Validate cross section consistency.
        
        Returns: True if sigma_scatter + sigma_absorb == sigma_total
        Raises: ValueError if inconsistent
        """
        pass
```

### 2. New Collision Physics: Constant Cross Section Branch

**File location:** `transport/physics/photon/interface.py` (new function)

**Integration with PhotonReaction Architecture:** The `constant_xs_collision()` function samples the collision type (absorption vs. scattering) based on the material's scattering ratio. When integrated, Benchmark 1 will create reaction objects (similar to `PhotonReactionCompton`, `PhotonReactionPhotoelectric`, etc.) that handle the actual physics, delegating to their `perform_collision()` methods.

```python
@njit
def constant_xs_collision(particle, material, rng_state):
    """
    Sample collision type and parameters for constant cross section material.
    
    Determines whether collision is scattering or absorption based on
    scattering ratio (sigma_scatter / sigma_total).
    
    Parameters:
        particle: Photon particle state (position, direction, energy, etc.)
        material: ConstantCrossSectionMaterial with sigma_total, sigma_scatter
        rng_state: Random number generator state
    
    Returns:
        collision_type: 0=absorption, 1=isotropic_scatter, 2=...
        collision_params: Dict with energy, direction, etc. post-collision
    
    Notes:
        - Distance to collision: -ln(rand()) / sigma_total
        - Collision type probability: sigma_scatter / sigma_total for scattering
        - If scattering: sample isotropic scattering (uniform direction)
        - If absorption: particle absorbed (no secondary)
        - This function will eventually be wrapped in PhotonReaction subclasses
          following the pattern established by PhotonReactionCompton, etc.
    """
    pass
```

### 3. New Scattering Distribution: Isotropic Scatter

**File location:** `transport/physics/photon/distributions.py` (new function)

```python
@njit
def sample_isotropic_scatter(incident_energy, rng_state):
    """
    Sample isotropic scattering (no energy loss).
    
    Photon energy is unchanged; only direction is randomized uniformly
    over 4π steradians (cos(theta) uniform on [-1, 1]).
    
    Parameters:
        incident_energy (float): Photon energy (MeV) — not changed
        rng_state: Random number generator state
    
    Returns:
        (new_energy, new_direction_mu, new_direction_phi):
            - new_energy: Same as incident_energy
            - new_direction_mu: cos(theta), uniform on [-1, 1]
            - new_direction_phi: Azimuthal angle, uniform on [0, 2π)
    
    Notes:
        - This is NOT Compton scattering (no energy loss to recoil)
        - Used only for constant-XS analytical benchmarks
    """
    pass
```

## Geometry and Source Setup

### Geometry: Concentric Spheres

An infinite medium is approximated by a series of concentric shells with tallies on the boundaries:

```python
# Example for Benchmark 1a (pure absorption case)
sigma_total = 1.0  # cm^-1, normalized for this benchmark

c_medium = ConstantCrossSectionMaterial(
    sigma_total=sigma_total,
    sigma_scatter=0.0,     # 1a: pure absorption
    sigma_absorb=1.0,
    name="infinite_medium_1a"
)

# Concentric spheres at distances 0.5, 0.8, 1.0, 1.5, ..., 25.0 cm
distances = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0]

# Create spheres and tallies
spheres = []
cells = []
previous_radius = 0

for r in distances:
    s = mcdc.Surface.Sphere(center=[0,0,0], radius=r, boundary_condition="vacuum" if r == distances[-1] else None)
    spheres.append(s)
    
    c = mcdc.Cell(region=+spheres[i-1] & -s if i > 0 else -s, fill=c_medium)
    cells.append(c)
    
    tally = mcdc.Tally(surface=s, scores=["flux"], name=f"flux_{r}cm")
```

### Source

Isotropic point source at origin:

```python
mcdc.Source(position=[0.0, 0.0, 0.0], energy=1.0, particle_type="photon")
```

## Three Sub-Cases

### Benchmark 1a: Pure Absorption

```python
sigma_total = 1.0      # cm^-1
sigma_scatter = 0.0
sigma_absorb = 1.0

# Expected flux (analytical):
# Φ(r) = (1 / 4π r²) × exp(-σ_total × r)
#      = (1 / 4π r²) × exp(-r)  [since σ_total = 1.0]
```

**Analytical Solution:**
```
Particle current at radius r: I(r) = exp(-r)
```

### Benchmark 1b: 30% Scattering

```python
sigma_total = 1.0
sigma_scatter = 0.3
sigma_absorb = 0.7
```

**Requires numerical solution** — repeated scattering affects flux profile.

### Benchmark 1c: 90% Scattering

```python
sigma_total = 1.0
sigma_scatter = 0.9
sigma_absorb = 0.1
```

**Highly scattering case** — significant buildup of multiple-scattered photons.

## Deliverables (Code Files + Comparison Script)

### 1. Modified Material Class
`mcdc_set/photon_material.py` — Add ConstantCrossSectionMaterial class with sigma_total, sigma_scatter, sigma_absorb attributes.

### 2. Physics Functions
Three functions in new files or extensions:
- `transport/physics/photon/interface.py::constant_xs_collision` (@njit, ~30 LOC)
- `transport/physics/photon/distributions.py::sample_isotropic_scatter` (@njit, ~20 LOC)
- Collision sampling/lookup integrated with main transport loop

### 3. Test Suite (3 problem.py files)

One for each sub-case:
- `photon_transport_code/MCNP_Verification_Tests/benchmark_1a_const_pure_absorption/problem.py`
- `photon_transport_code/MCNP_Verification_Tests/benchmark_1b_const_30pct_scatter/problem.py`
- `photon_transport_code/MCNP_Verification_Tests/benchmark_1c_const_90pct_scatter/problem.py`

Each should:
- Define ConstantCrossSectionMaterial with appropriate σ_total, σ_scatter, σ_absorb
- Create concentric sphere geometry with 14 tally surfaces
- Run with 200,000 particles × 100 batches
- Output to benchmark_1{a|b|c}.h5
- Disable the progress bar for outputs (`mcdc.settings.use_progress_bar = False`)

### 4. Comparison Script
`photon_transport_code/MCNP_Verification_Tests/benchmark_1{a|b|c}/compare.py`

For each sub-case:
1. Read benchmark_1{a|b|c}.h5
2. Extract flux tallies at each radius
3. Compute particle current: I = flux_mean × 4π r²
4. Compare vs. analytical/reference solutions
5. Print pass/fail table

## Requirements

✅ ConstantCrossSectionMaterial class inherits from or parallels PhotonMaterial  
✅ constant_xs_collision function uses @njit decorator  
✅ sample_isotropic_scatter uses @njit decorator  
✅ All functions include complete docstrings (Parameters, Returns, Notes)  
✅ Functions contain only pass statements or minimal logic stubs  
✅ No imports from external libraries in physics functions (NumPy/Numba compiled code)  
✅ Cross section validation: sigma_scatter + sigma_absorb == sigma_total  
✅ All problem.py files create geometry + source + tallies correctly  
✅ All compare.py files read H5 output and validate results  

## Validation (from VALIDATION_STRATEGY.md)

Run these checks after creating all files:

```bash
# 1. Material class instantiation
python -c "from mcdc_set.photon_material import ConstantCrossSectionMaterial; m = ConstantCrossSectionMaterial(1.0, 0.3, 0.7); print('✓ ConstantCrossSectionMaterial instantiates')"

# 2. Physics function imports
python -c "from transport.physics.photon.interface import constant_xs_collision; print('✓ constant_xs_collision imports')"
python -c "from transport.physics.photon.distributions import sample_isotropic_scatter; print('✓ sample_isotropic_scatter imports')"

# 3. Test problem.py files for syntax
python -c "exec(open('photon_transport_code/MCNP_Verification_Tests/benchmark_1a_const_pure_absorption/problem.py').read()); print('✓ problem.py 1a syntax OK')"
python -c "exec(open('photon_transport_code/MCNP_Verification_Tests/benchmark_1b_const_30pct_scatter/problem.py').read()); print('✓ problem.py 1b syntax OK')"
python -c "exec(open('photon_transport_code/MCNP_Verification_Tests/benchmark_1c_const_90pct_scatter/problem.py').read()); print('✓ problem.py 1c syntax OK')"

# 4. Compare script syntax
python -c "exec(open('photon_transport_code/MCNP_Verification_Tests/benchmark_1a_const_pure_absorption/compare.py').read()); print('✓ compare.py 1a syntax OK')"
```

## Success Criteria

✅ ConstantCrossSectionMaterial class created and importable  
✅ constant_xs_collision function with @njit decorator  
✅ sample_isotropic_scatter function with @njit decorator  
✅ All docstrings complete (Parameters/Returns/Notes)  
✅ Three benchmark directories created with problem.py + compare.py  
✅ problem.py files define geometry, source, and tallies correctly  
✅ compare.py files read H5 and compute current vs. reference  
✅ No import errors or syntax errors in any file  
✅ Black formatting passes (88 char line length)  
✅ All files ready for MCDC implementation integration  

## Implementation Notes

### Updates from PHOTON_REACTION_IMPLEMENTATION.md

The photon transport module has been refactored with an object-oriented reaction architecture (`mcdc/object_/photon_reaction.py`). Key classes now available:
- `PhotonReactionBase` — Abstract base class for all photon reactions
- `PhotonReactionCompton` — Compton scattering with Kahn (1954) sampling
- `PhotonReactionPhotoelectric` — Photoelectric absorption  
- `PhotonReactionPairProduction` — Pair production above 1.022 MeV threshold

**For Benchmark 1:**
1. `interface.py` already has refactored collision dispatch logic (delegates to reaction objects)
2. When implementing `ConstantCrossSectionMaterial`, follow the same pattern:
   - Create a constant-XS scattering reaction class that inherits from `PhotonReactionBase`
   - Implement `perform_collision()` method for isotropic scattering
   - Create an absorption reaction class for the absorption component
3. Update material type dispatch in `interface.py` to recognize `ConstantCrossSectionMaterial` and call the appropriate reaction handler

**Key point:** Benchmark 1 uses **ConstantCrossSectionMaterial** (user-specified cross-sections), NOT HDF5 data. The collision physics do not depend on HDF5 files or `native.py`; they are standalone implementations.

### Before Benchmark 1 Can Run:

#### Implementation Steps:
1. Create `ConstantCrossSectionMaterial` class in `mcdc_set/photon_material.py` (or `mcdc/object_/photon_material.py`)
   - Accept `sigma_total`, `sigma_scatter`, `sigma_absorb` as constructor parameters
   - Validate that `sigma_scatter + sigma_absorb == sigma_total`
   
2. Create constant-XS reaction classes in a new file (e.g., `mcdc/object_/photon_reaction_constant_xs.py`) or add to existing `photon_reaction.py`:
   - `ConstantXSIsotropicScatter` — Samples uniform direction, preserves energy
   - `ConstantXSAbsorption` — Marks photon as not alive
   
3. Update `interface.py` to dispatch to constant-XS reactions based on material type
4. Implement `sample_isotropic_scatter()` distribution function

#### Verification After PHOTON_REACTION_IMPLEMENTATION:
- Confirm `PhotonReactionCompton` and other classes are properly imported in `interface.py`
- Verify that `interface.py` collision() function correctly delegates to reaction objects
- Benchmark 1 infrastructure (ConstantCrossSectionMaterial + constant-XS reactions) follows the same architecture

### Updates from SWITCH_NATIVE_TO_DATA_MCDC

The code restructuring from `SWITCH_NATIVE_TO_DATA_MCDC.md` has been completed. Key impacts on Benchmark 1:

1. **Module organization:** `interface.py` has been refactored to use PhotonReaction dispatch mechanism
2. **Imports in interface.py:** Now imports reaction classes from `mcdc.object_.photon_reaction`
3. **Constant XS physics integration:** The `constant_xs_collision()` function will be added to `interface.py` and dispatched based on material type (ConstantCrossSectionMaterial vs. PhotonMaterial)

**Key point:** Benchmark 1 uses **ConstantCrossSectionMaterial** (user-specified cross-sections), NOT HDF5 data. The `constant_xs_collision()` and `sample_isotropic_scatter()` functions do not depend on HDF5 files or `native.py`; they are standalone physics implementations that follow the same PhotonReaction pattern as existing reactions.

### Before Benchmark 1 Can Run:

#### Code Changes Needed:
1. Create `ConstantCrossSectionMaterial` class in `mcdc_set/photon_material.py`
2. Create `constant_xs_collision()` in `transport/physics/photon/interface.py` (or new module)
3. Create `sample_isotropic_scatter()` in `transport/physics/photon/distributions.py`
4. Update transport loop to dispatch `constant_xs_collision()` when material is ConstantCrossSectionMaterial
5. **Verify** that the updated `interface.py` from `SWITCH_NATIVE_TO_DATA_MCDC` doesn't break the material type dispatch logic

#### Tests Must Pass:
- Material class instantiation: `ConstantCrossSectionMaterial(1.0, 0.3, 0.7)`
- Physics function imports after `SWITCH_NATIVE_TO_DATA_MCDC` refactoring
- Problem.py files syntax-check after any interface reorganization

## Integration Dependencies

### Before Benchmark 1 Can Run:
1. ✅ Core MCDC transport loop (`mcdc/transport/main.py`) must support custom material physics
2. ✅ Material lookup in main transport must call `constant_xs_collision` for ConstantCrossSectionMaterial objects
3. ✅ RNG state management compatible with isotropic sampling
4. ✅ Tally system must record surface flux correctly (particles crossing outward)

### Files Modified:
- `mcdc_set/photon_material.py` — Add ConstantCrossSectionMaterial
- `transport/physics/photon/interface.py` — Add constant_xs_collision entry point
- `transport/physics/photon/distributions.py` — Add sample_isotropic_scatter
- `mcdc/transport/main.py` — Add material type dispatch for constant cross sections
- `examples/benchmark_1{a|b|c}/` — Add problem.py + compare.py

## IMPORTANT

**Benchmark 1 must be complete before moving to Benchmark 2.** Both require the same ConstantCrossSectionMaterial infrastructure.

**Do NOT implement real physics (Compton, photoelectric) for this benchmark.** This test isolates scattering/absorption behavior only.

**Test pure absorption first (1a)**, which has analytical solution: `I(r) = exp(-r)`. This validates the geometry, source, and tally system before attempting the multi-scatter cases.
