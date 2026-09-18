# PHASE 6: MCDC System Integration — Geometry, Tally, Output & Slab Problem

## Quick Context
Phases 1–5 built a standalone photon physics library in `photon_transport_code/`. Phase 6 wires that library into MCDC's actual transport loop, geometry system, tally system, and HDF5 output infrastructure — the same infrastructure neutrons already use. The phase ends with a working `problem.py` that transports a mono-energetic photon beam through an aluminum slab and produces a tally-vs-depth output file readable with `h5py`.

All photon physics (cross-sections, sampling, collision handling) is already implemented. Phase 6 is purely integration: connecting the physics to the rest of MCDC.

## READ FIRST (Architecture)
- `photon-transport-docs/MCDC_FILE_ARCHITECTURE.md` — How MCDC's neutron transport is structured end-to-end (particle dispatch, material lookup, tally scoring, output). The photon integration mirrors this exactly.
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` (Phase 6 / MCDC Integration section) — Target file layout for the integrated module.
- `photon-transport-docs/VALIDATION_STRATEGY.md` (Phase 6 Acceptance Criteria) — Slab attenuation benchmark and regression test requirements.

## WORKING DIRECTORY
```
c:\Projects\MCDC\
```
All paths below are relative to this root unless otherwise noted.

## REFERENCE PATTERNS
- `mcdc/constant.py` — Particle type constants (`PARTICLE_NEUTRON = 0`, etc.); add `PARTICLE_PHOTON` here
- `mcdc/transport/physics/interface.py` — Particle-type dispatch for `particle_speed`, `macro_xs`, `collision`; add photon branches
- `mcdc/transport/physics/neutron/` — Mirror this directory structure under `mcdc/transport/physics/photon/`
- `mcdc/numba_types.py` — Flat numpy dtype definitions for all state arrays; add photon material/element dtypes here
- `mcdc/mcdc_get/native_material.py` and `mcdc/mcdc_get/nuclide.py` — Accessor function pattern to replicate for photons
- `mcdc/object_/material.py` — User-facing material class pattern for `PhotonMaterial`
- `mcdc/mcdc_set/material.py` — How a material object is registered into `mcdc` state; replicate for photons
- `mcdc/object_/source.py` — Where to add the `particle_type` keyword argument
- `mcdc/__init__.py` — Where to export `PhotonMaterial` so users can write `mcdc.PhotonMaterial(...)`

## DELIVERABLES

### Step 1 — Add `PARTICLE_PHOTON` constant
**File:** `mcdc/constant.py`

The existing sequence is:
```python
PARTICLE_NEUTRON  = 0
PARTICLE_ELECTRON = 1
PARTICLE_PROTON   = 2
```
Add immediately after:
```python
PARTICLE_PHOTON   = 3
```
Also add reaction-type constants parallel to the neutron reaction constants:
```python
PHOTON_REACTION_COMPTON        = 0
PHOTON_REACTION_PHOTOELECTRIC  = 1
PHOTON_REACTION_PAIR_PRODUCTION = 2
PHOTON_REACTION_TOTAL          = 3
```

---

### Step 2 — Copy and adapt photon physics module into MCDC
**Source:** `photon_transport_code/transport/physics/photon/` (5 files)
**Destination:** `mcdc/transport/physics/photon/` (new directory)

Files to copy and adapt:
- `interface.py` — entry point; functions `particle_speed()`, `macro_xs()`, `collision()` must match neutron signatures exactly (same arguments: `particle_container, mcdc, data`)
- `native.py` — NIST data management and log-log interpolation
- `cross_sections.py` — Klein-Nishina, photoelectric, pair production formulas
- `distributions.py` — Kahn rejection sampling, shell selection, pair production angle sampling
- `util.py` — physical constants and kinematic helpers

Adaptation required:
- Replace any standalone reaction-type integer literals with the new constants from `mcdc/constant.py` (`PHOTON_REACTION_COMPTON`, etc.)
- Ensure all `@njit` decorators are preserved
- Do **not** change physics logic; only update import paths and constant references

---

### Step 3 — Wire photon into the physics dispatch
**File:** `mcdc/transport/physics/interface.py`

This file dispatches to the correct physics module based on `particle["particle_type"]`. Add photon branches to the three dispatch functions. Example pattern:

```python
@njit
def particle_speed(particle_container, mcdc, data):
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_NEUTRON:
        return neutron.particle_speed(particle_container, mcdc, data)
    elif particle["particle_type"] == PARTICLE_PHOTON:       # ADD THIS
        return photon.particle_speed(particle_container, mcdc, data)  # ADD THIS
    return -1.0

@njit
def macro_xs(reaction_type, particle_container, mcdc, data):
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_NEUTRON:
        return neutron.macro_xs(reaction_type, particle_container, mcdc, data)
    elif particle["particle_type"] == PARTICLE_PHOTON:       # ADD THIS
        return photon.macro_xs(reaction_type, particle_container, mcdc, data)  # ADD THIS
    return -1.0

@njit
def collision(particle_container, mcdc, data):
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_NEUTRON:
        neutron.collision(particle_container, mcdc, data)
    elif particle["particle_type"] == PARTICLE_PHOTON:       # ADD THIS
        photon.collision(particle_container, mcdc, data)     # ADD THIS
```

Add the photon module import at the top of `interface.py` alongside the neutron import:
```python
from mcdc.transport.physics import photon
```

---

### Step 4 — Add photon data structures to Numba types
**File:** `mcdc/numba_types.py`

Find the section defining neutron material and nuclide dtype definitions (around lines 644–659). Add two new dtypes immediately after, following the same flat-array-with-offset pattern:

```python
photon_element_dtype = np.dtype([
    ("Z",                  np.int32),
    ("N_points",           np.int32),
    ("energy_grid_offset", np.int64),
    ("compton_offset",     np.int64),
    ("pe_offset",          np.int64),
    ("pair_offset",        np.int64),
])

photon_material_dtype = np.dtype([
    ("N_element",          np.int32),
    ("element_IDs_offset", np.int64),
    ("densities_offset",   np.int64),
])
```

Then in the main `mcdc` state struct definition, add two new array fields alongside the existing neutron arrays:
```python
("photon_materials", photon_material_dtype, (0,)),
("photon_elements",  photon_element_dtype,  (0,)),
("photon_data",      np.float64,            (0,)),   # flat data buffer for cross-section grids
```

---

### Step 5 — Create photon data accessor functions
**New files:**
- `mcdc/mcdc_get/photon_material.py`
- `mcdc/mcdc_get/photon_element.py`

**Pattern:** Copy `mcdc/mcdc_get/native_material.py` and `mcdc/mcdc_get/nuclide.py` as templates and adapt for photon fields.

`mcdc/mcdc_get/photon_material.py` must expose:
```python
@njit
def N_element(material):
    return material["N_element"]

@njit
def element_ID(i, material, data):
    # Returns the i-th element ID stored at element_IDs_offset in the data buffer
    return int(data[material["element_IDs_offset"] + i])

@njit
def density(i, material, data):
    # Returns the i-th element number density (atoms/barn-cm)
    return data[material["densities_offset"] + i]
```

`mcdc/mcdc_get/photon_element.py` must expose:
```python
@njit
def N_points(element):
    return element["N_points"]

@njit
def energy_grid(element, data):
    n = element["N_points"]
    return data[element["energy_grid_offset"] : element["energy_grid_offset"] + n]

@njit
def compton_xs(element, data):
    n = element["N_points"]
    return data[element["compton_offset"] : element["compton_offset"] + n]

@njit
def photoelectric_xs(element, data):
    n = element["N_points"]
    return data[element["pe_offset"] : element["pe_offset"] + n]

@njit
def pair_production_xs(element, data):
    n = element["N_points"]
    return data[element["pair_offset"] : element["pair_offset"] + n]
```

---

### Step 6 — Integrate PhotonMaterial into the simulation builder

**6a. User-facing class — `mcdc/object_/photon_material.py`**
Copy `photon_transport_code/mcdc_set/photon_material.py` (the `PhotonMaterial` class) to `mcdc/object_/photon_material.py`. Keep the constructor signature:
```python
class PhotonMaterial:
    def __init__(self, elements, densities, name=""):
        ...
```
The class should validate: element atomic numbers are in [1, 92], densities are positive floats.

**6b. Export from mcdc namespace — `mcdc/__init__.py`**
Add alongside `Material` and `MaterialMG`:
```python
from mcdc.object_.photon_material import PhotonMaterial
```

**6c. State registration — `mcdc/mcdc_set/photon_material.py`**
New file. Mirroring `mcdc/mcdc_set/material.py`, write a function that takes a `PhotonMaterial` instance and registers it into the `mcdc` state arrays:
1. Build element data buffers using `photon_transport_code/transport/physics/photon/native.py`'s `build_element_buffer(Z)` function (copy it into `mcdc/transport/physics/photon/native.py` in Step 2)
2. Append to `mcdc["photon_elements"]` and `mcdc["photon_data"]` for each element
3. Append to `mcdc["photon_materials"]` recording the element count and offsets

This function must be called by the MCDC simulation builder when it encounters a cell filled with a `PhotonMaterial`.

**6d. Simulation builder hookup — `mcdc/mcdc_set/` simulation builder**
Find where the simulation builder iterates over cell fills to register materials (look in `mcdc/mcdc_set/` for where `mcdc_set.material.set_material(...)` is called). Add an analogous branch:
```python
if isinstance(cell.fill, PhotonMaterial):
    mcdc_set.photon_material.set_photon_material(cell.fill, mcdc)
```

---

### Step 7 — Add `particle_type` to Source
**File:** `mcdc/object_/source.py`

Add an optional `particle_type` keyword argument to `Source.__init__()`:
```python
def __init__(self, ..., particle_type="neutron"):
    ...
    if particle_type == "photon":
        self._particle_type = PARTICLE_PHOTON
    else:
        self._particle_type = PARTICLE_NEUTRON
```

Ensure the source struct field `particle_type` is set when a source particle is initialized in the source loop (find where the particle container is populated in `mcdc/transport/simulation.py` or `mcdc/mcdc_set/source.py` and ensure `particle["particle_type"]` is assigned from the source's `_particle_type`).

---

### Step 8 — Write the slab problem.py
**File:** `photon_transport_code/examples/photon_slab/problem.py`

This is the first end-to-end photon transport problem using MCDC's geometry and tally systems. Write it exactly as shown below:

```python
import numpy as np
import mcdc

# =============================================================================
# Materials
# =============================================================================
# Aluminum at standard density 2.7 g/cm³
# Atomic density: (2.7 g/cm³ × 6.022e23 atoms/mol) / 26.982 g/mol = 0.06026 atoms/barn-cm
aluminum = mcdc.PhotonMaterial(
    elements=[13],        # Atomic number for aluminum
    densities=[0.06026],  # atoms/barn-cm
    name="aluminum",
)

# =============================================================================
# Surfaces
# =============================================================================
s_left  = mcdc.Surface.PlaneX(x=0.0,  boundary_condition="vacuum")
s_right = mcdc.Surface.PlaneX(x=20.0, boundary_condition="vacuum")

# =============================================================================
# Cells
# =============================================================================
slab = mcdc.Cell(region=+s_left & -s_right, fill=aluminum)

# =============================================================================
# Source
# =============================================================================
# Mono-energetic 1 MeV photon beam entering from the left face in the +x direction.
# At 1 MeV, Compton scattering dominates in aluminum (photoelectric < 0.1 MeV,
# pair production > 1.022 MeV), giving a mean free path of ~8 cm.
mcdc.Source(
    x=0.0,
    direction=[1.0, 0.0, 0.0],
    energy=1.0,              # MeV
    particle_type="photon",
)

# =============================================================================
# Tallies
# =============================================================================
# Photon flux as a function of depth: 40 equal bins of 0.5 cm each, 0 to 20 cm
mesh = mcdc.MeshStructured(x=np.linspace(0.0, 20.0, 41))
mcdc.Tally(mesh=mesh, scores=["flux"])

# =============================================================================
# Settings
# =============================================================================
mcdc.settings.N_particle  = 10000
mcdc.settings.N_batch     = 10
mcdc.settings.rng_seed    = 42
mcdc.settings.output_name = "photon_slab"

# =============================================================================
# Run
# =============================================================================
mcdc.run()
```

**Expected physics:** A 1 MeV photon in aluminum has a total macroscopic cross-section of approximately 0.166 cm⁻¹ (from NIST XCOM; Compton dominant at 0.126 cm⁻¹, photoelectric ~0.005 cm⁻¹). The mean free path is ~1/0.166 ≈ 6 cm. Across 20 cm the uncollided flux falls by e^{−20/6} ≈ 0.036. Including scattered photons that survive, the total flux at 20 cm should be roughly 5–15% of the entrance flux.

**Reading the output:**
```python
import h5py
import numpy as np

with h5py.File("photon_slab.h5", "r") as f:
    flux_mean = f["tally/flux/mean"][:]
    flux_std  = f["tally/flux/std"][:]

x_centers = np.linspace(0.25, 19.75, 40)  # bin centers at 0.5 cm spacing
```

---

### Step 9 — Regression check
Before marking Phase 6 complete, run both checks in sequence:

```bash
# 1. All existing neutron tests must pass with zero failures
pytest mcdc/tests/ -v

# 2. Slab problem must run to completion and write output
python photon_transport_code/examples/photon_slab/problem.py

# 3. Verify output file exists and has the expected tally structure
python -c "
import h5py, numpy as np
with h5py.File('photon_slab.h5', 'r') as f:
    flux = f['tally/flux/mean'][:]
entrance = flux[0]
exit_    = flux[-1]
ratio    = exit_ / entrance
print(f'Entrance flux: {entrance:.4f}')
print(f'Exit flux:     {exit_:.4f}')
print(f'Exit/entrance: {ratio:.4f}')
assert 0.03 < ratio < 0.25, f'Attenuation ratio {ratio:.4f} out of expected range [0.03, 0.25]'
print('Attenuation check PASSED')
"

# 4. Verify PhotonMaterial is importable from the mcdc namespace
python -c "import mcdc; m = mcdc.PhotonMaterial(elements=[13], densities=[0.06026]); print('PhotonMaterial import PASSED')"

# 5. Verify particle_type keyword works on Source
python -c "import mcdc; mcdc.Source(x=0.0, direction=[1,0,0], energy=1.0, particle_type='photon'); print('Source particle_type PASSED')"
```

---

## REQUIREMENTS
- All photon physics functions in `mcdc/transport/physics/photon/` carry `@njit` decorators
- All accessor functions in `mcdc/mcdc_get/photon_*.py` carry `@njit` decorators
- `mcdc.PhotonMaterial(elements=[...], densities=[...])` is importable and functional
- `mcdc.Source(..., particle_type="photon")` works without error
- No neutron tests break (zero regressions)
- `problem.py` produces `photon_slab.h5` with a `tally/flux` dataset
- Attenuation ratio (exit flux / entrance flux) is between 3% and 25%
- Black formatting compliant on all new/modified files

## VALIDATION
```bash
# Full validation sequence
pytest mcdc/tests/ -v --tb=short
python photon_transport_code/examples/photon_slab/problem.py
python -c "
import h5py, numpy as np
with h5py.File('photon_slab.h5') as f:
    flux = f['tally/flux/mean'][:]
ratio = flux[-1] / flux[0]
assert 0.03 < ratio < 0.25, f'ratio={ratio:.3f} out of range'
print(f'PASS — attenuation ratio {ratio:.3f}')
"
black --check mcdc/transport/physics/photon/ mcdc/mcdc_get/photon_material.py mcdc/mcdc_get/photon_element.py mcdc/object_/photon_material.py mcdc/mcdc_set/photon_material.py
```

## SUCCESS CRITERIA
- `pytest mcdc/tests/` passes with zero failures
- `python photon_transport_code/examples/photon_slab/problem.py` runs to completion
- `photon_slab.h5` contains a valid `tally/flux/mean` dataset with 40 spatial bins
- Exit-to-entrance flux ratio is in the range [0.03, 0.25]
- `mcdc.PhotonMaterial` importable from `mcdc` namespace
- `mcdc.Source(..., particle_type="photon")` accepted without error
- All new files pass Black formatting check
- No circular imports between `mcdc/transport/physics/photon/` and `mcdc/mcdc_get/`

## IMPORTANT
Phase 6 modifies files in the main `mcdc/` package (not just `photon_transport_code/`). Test neutron regression first, before running the photon problem, so that any breakage is caught early.

STOP after Phase 6 completion. Do NOT proceed to further phases without a new prompt.
