# MCDC Code Architecture: File Dependencies and Execution Flow

**Purpose**: Understand how files are connected when running a simulation
**Focus**: Mesh slab geometry simulation example

---

## Quick Answer: Mesh Slab Simulation File Flow

When you write this:
```python
import mcdc

# Setup
mcdc.Surface.PlaneX(x=0.0)
mcdc.Material(...)
mcdc.Cell(...)
mcdc.Tally(...)

# Run
mcdc.run()
```

Files called:

```
INPUT SCRIPT (input.py)
  ↓
mcdc/__init__.py          [main entry point]
  ├─→ mcdc/mcdc_set/       [define geometry/materials/tallies]
  │   ├─ surface.py
  │   ├─ cell.py
  │   ├─ material.py
  │   └─ tally.py
  ├─→ mcdc/main.py         [contains run() function]
  │   ├─→ mcdc/code_factory/    [generate Numba types]
  │   ├─→ mcdc/transport/mesh/  [mesh geometry handling]
  │   │   └─ structured.py
  │   ├─→ mcdc/transport/geometry/  [surface geometry]
  │   │   └─ surface/
  │   │       └─ plane*.py
  │   ├─→ mcdc/transport/simulation.py  [main transport loop]
  │   │   ├─ physics/neutron/ or physics/photon/
  │   │   ├─ particle.py
  │   │   ├─ technique.py
  │   │   └─ tally.py
  │   └─→ mcdc/output.py        [HDF5 output]
  │
  └─→ OUTPUT (output.h5)
```

---

## Deep Dive: Directory Structure

```
mcdc/
├── __init__.py                    ← Main entry point for "import mcdc"
├── main.py                        ← run() function (starts simulation)
├── config.py                      ← Command-line argument parsing
├── output.py                      ← HDF5 output generation
├── print_.py                      ← Console printing
├── visualize.py                   ← Result visualization
├── constant.py                    ← Physical constants
├── numba_types.py                 ← Numba @njit data structures
│
├── mcdc_set/                      ← USER API: Define simulation
│   ├── __init__.py                (exports: Surface, Material, Cell, etc.)
│   ├── surface.py                 (PlaneX, PlaneY, PlaneZ, Sphere, etc.)
│   ├── cell.py                    (Cell definition)
│   ├── material.py                (Material definition)
│   ├── multigroup_material.py     (Multigroup material)
│   ├── native_material.py         (Native material)
│   ├── tally.py                   (Tally definition)
│   ├── source.py                  (Source definition)
│   ├── simulation.py              (Simulation settings)
│   ├── distribution.py            (Energy/angle distributions)
│   ├── kalbach_mann_distribution.py
│   ├── tabulated_energy_angle_distribution.py
│   ├── (other distributions...)
│   └── nuclide.py                 (Nuclide data)
│
├── mcdc_get/                      ← INTERNAL: Getters for simulation objects
│   ├── surface.py
│   ├── cell.py
│   ├── material.py
│   └── (auto-generated getters)
│
├── code_factory/                  ← CODE GENERATION
│   ├── numba_objects_generator.py (generates @njit accessor functions)
│   └── gpu/                       (GPU-specific code)
│
├── object_/                       ← OBJECT DEFINITIONS
│   ├── surface.py
│   ├── cell.py
│   ├── material.py
│   ├── simulation.py
│   └── (core object definitions)
│
├── transport/                     ← TRANSPORT PHYSICS (MAIN LOOP)
│   ├── __init__.py
│   ├── main.py                    (top-level transport loop)
│   ├── simulation.py              (eigenvalue vs fixed-source)
│   ├── mpi.py                     (MPI communication)
│   ├── particle.py                (particle tracking)
│   ├── particle_bank.py           (particle banking)
│   ├── technique.py               (implicit capture, etc.)
│   ├── data.py                    (data structure management)
│   │
│   ├── physics/                   ← PHYSICS CALCULATIONS
│   │   ├── interface.py           (public physics API)
│   │   ├── util.py
│   │   └── neutron/               (NEUTRON TRANSPORT)
│   │       ├── interface.py       (cross-section lookup, scattering)
│   │       ├── native.py          (native data loading)
│   │       ├── multigroup.py      (multigroup data)
│   │       └── (reaction types)
│   │
│   ├── geometry/                  ← GEOMETRY HANDLING
│   │   ├── interface.py           (ray tracing, intersection finding)
│   │   └── surface/
│   │       ├── plane.py           (generic plane)
│   │       ├── plane_x.py         (X-aligned plane)
│   │       ├── plane_y.py         (Y-aligned plane)
│   │       ├── plane_z.py         (Z-aligned plane)
│   │       ├── sphere.py
│   │       ├── cylinder_x.py
│   │       └── (other surfaces)
│   │
│   ├── mesh/                      ← MESH GEOMETRY
│   │   ├── interface.py           (mesh cell finding, indexing)
│   │   ├── structured.py          ← USED FOR MESH SLAB
│   │   ├── uniform.py
│   │   └── (mesh types)
│   │
│   └── tally/                     ← TALLY SCORING
│       ├── interface.py           (tally scoring routines)
│       └── (tally implementations)
```

---

## File Flow for Specific Simulation Types

### 1. Mesh Slab Geometry Simulation

**User writes:**
```python
import mcdc

# Create mesh
mesh = mcdc.StructuredMesh(1.0, [0.0, 1.0, 2.0, 3.0])  # 3 slabs
mesh.x = [0.0, 1.0, 2.0, 3.0]  # Slab edges

# Create cells in mesh
mcdc.Cell(mesh=(mesh, 0, 0, 0), fill=material1)  # Slab 1
mcdc.Cell(mesh=(mesh, 1, 0, 0), fill=material2)  # Slab 2
mcdc.Cell(mesh=(mesh, 2, 0, 0), fill=material3)  # Slab 3

mcdc.run()
```

**Files involved:**

1. **Input script** → calls mcdc functions
2. **mcdc/__init__.py** → imports all user-facing classes
3. **mcdc/mcdc_set/structured_mesh.py** → defines mesh structure
4. **mcdc/mcdc_set/cell.py** → defines cells with mesh reference
5. **mcdc/mcdc_set/material.py** → material properties
6. **mcdc/main.py:run()** → starts execution
   - Calls `mcdc.code_factory.numba_objects_generator` → generates Numba types
   - Calls `mcdc.transport.simulation` → main transport loop
7. **mcdc/transport/mesh/structured.py** → finds which mesh cell particle is in
8. **mcdc/transport/physics/neutron/** → cross-section lookup for that cell's material
9. **mcdc/transport/geometry/surface/** → if geometry has explicit surfaces, finds intersections
10. **mcdc/transport/tally/** → scores to tallies
11. **mcdc/output.py** → writes result to HDF5

---

### 2. Surface-Based Geometry (Sphere in Cube)

**User writes:**
```python
import mcdc

# Create surfaces
sx1 = mcdc.Surface.PlaneX(x=0.0)
sx2 = mcdc.Surface.PlaneX(x=4.0)
sphere = mcdc.Surface.Sphere(center=[2,2,2], radius=1.5)

# Define regions using boolean operations
inside_sphere = -sphere
inside_box = +sx1 & -sx2 & ...

# Create cells
mcdc.Cell(name="sphere", region=inside_sphere, fill=material1)
mcdc.Cell(name="box", region=inside_box & ~inside_sphere, fill=material2)

mcdc.run()
```

**Files involved:**

1. **mcdc/mcdc_set/surface.py** → defines all surface types (PlaneX, Sphere, etc.)
2. **mcdc/transport/geometry/surface/plane_x.py** → X-aligned plane intersection
3. **mcdc/transport/geometry/surface/sphere.py** → sphere intersection
4. **mcdc/transport/geometry/interface.py** → ray-tracing for region finding
   - For each surface, calls appropriate intersection function
   - Determines which cell/region particle is in
5. Rest follows similar pattern to mesh

---

## Detailed: What Happens When You Call `mcdc.run()`

```
mcdc.run()  [mcdc/main.py]
  │
  ├─ STEP 1: Parse settings
  │  └─ mcdc/config.py: Handle command-line arguments
  │
  ├─ STEP 2: Preparation
  │  ├─ code_factory/numba_objects_generator.py
  │  │  └─ Generates Numba @njit types:
  │  │     - Particle state struct
  │  │     - Cell data struct
  │  │     - Material data struct
  │  │     - Tally struct
  │  │     - etc.
  │  │
  │  ├─ Compile all physics modules to Numba @njit
  │  │  ├─ transport/physics/neutron/interface.py
  │  │  ├─ transport/geometry/interface.py
  │  │  ├─ transport/mesh/interface.py (if mesh used)
  │  │  ├─ transport/tally/interface.py
  │  │  └─ transport/technique.py
  │  │
  │  └─ Create data array: long 1D array storing all particle/cell/material data
  │
  ├─ STEP 3: Run transport simulation
  │  └─ transport/simulation.py
  │     ├─ if eigenvalue_mode:
  │     │  └─ eigenvalue_simulation(mcdc_container, data)
  │     └─ else:
  │        └─ fixed_source_simulation(mcdc_container, data)
  │
  │  In simulation loop:
  │  ├─ For each batch:
  │  │  └─ For each particle:
  │  │     ├─ Generate initial conditions from source
  │  │     │  └─ mcdc_set/source.py & mcdc/transport/source.py
  │  │     │
  │  │     ├─ While particle alive:
  │  │     │  ├─ Find which cell/mesh particle is in:
  │  │     │  │  ├─ If mesh: mcdc/transport/mesh/structured.py
  │  │     │  │  │  └─ Compute mesh index from coordinates
  │  │     │  │  └─ If surfaces: mcdc/transport/geometry/surface/*.py
  │  │     │  │     └─ Ray-tracing through all surfaces
  │  │     │  │
  │  │     │  ├─ Get cell's material
  │  │     │  ├─ Look up cross-section:
  │  │     │  │  └─ mcdc/transport/physics/neutron/interface.py
  │  │     │  │     ├─ native.py or multigroup.py
  │  │     │  │     └─ Returns σ_t (total), σ_s (scattering), etc.
  │  │     │  │
  │  │     │  ├─ Sample distance to collision
  │  │     │  │  └─ mcdc/transport/rng.py (random number generation)
  │  │     │  │
  │  │     │  ├─ Find distance to nearest surface/mesh boundary
  │  │     │  │  ├─ If mesh: mcdc/transport/mesh/structured.py
  │  │     │  │  │  └─ Simple grid traversal
  │  │     │  │  └─ If surfaces: mcdc/transport/geometry/surface/*.py
  │  │     │  │     └─ Ray-trace to nearest intersection
  │  │     │  │
  │  │     │  ├─ Transport particle to collision/boundary
  │  │     │  │
  │  │     │  ├─ Score to tallies:
  │  │     │  │  └─ mcdc/transport/tally/interface.py
  │  │     │  │     └─ Scores flux, reactions, etc.
  │  │     │  │
  │  │     │  ├─ Determine collision type:
  │  │     │  │  ├─ Scattering: mcdc/transport/physics/neutron/interface.py
  │  │     │  │  ├─ Capture: mcdc/transport/technique.py (implicit capture)
  │  │     │  │  └─ Fission: mcdc/transport/physics/neutron/interface.py
  │  │     │  │
  │  │     │  └─ If collision: sample new direction/energy
  │  │     │     └─ mcdc/transport/physics/neutron/distributions.py
  │  │     │        (Kalbach-Mann, tabulated, etc.)
  │  │     │
  │  │     └─ Bank produced particles (fission):
  │  │        └─ mcdc/transport/particle_bank.py
  │  │
  │  └─ Synchronize across MPI processes:
  │     └─ mcdc/transport/mpi.py
  │
  ├─ STEP 4: Output
  │  └─ mcdc/output.py
  │     ├─ Gather results from all MPI ranks
  │     ├─ Compute statistics (mean, std dev)
  │     └─ Write to HDF5 file: output.h5
  │
  └─ STEP 5: Print summary
     └─ mcdc/print_.py
```

---

## Key File Relationships for Mesh Slab

```
MESH SLAB SIMULATION:

input.py
  │
  ├─ mcdc.StructuredMesh()
  │  └─ mcdc/mcdc_set/mesh.py
  │     └─ Creates mesh object
  │
  ├─ mcdc.Cell(mesh=(mesh, i, j, k), fill=material)
  │  └─ mcdc/mcdc_set/cell.py
  │     └─ Cell references mesh
  │
  ├─ mcdc.Material()
  │  └─ mcdc/mcdc_set/material.py
  │
  ├─ mcdc.Tally()
  │  └─ mcdc/mcdc_set/tally.py
  │
  └─ mcdc.run()
     └─ mcdc/main.py
        │
        ├─ Call: mcdc/code_factory/numba_objects_generator.py
        │  └─ Compile all to Numba @njit
        │
        └─ Call: mcdc/transport/simulation.py (main loop)
           │
           ├─ For each particle history:
           │  └─ While particle alive:
           │     ├─ Find cell:
           │     │  └─ mcdc/transport/mesh/structured.py
           │     │     ├─ Use mesh → compute mesh index (i,j,k)
           │     │     └─ Return which cell particle is in
           │     │
           │     ├─ Get material from cell
           │     ├─ Cross-section lookup:
           │     │  └─ mcdc/transport/physics/neutron/interface.py
           │     │     └─ native.py (from nuclear data library)
           │     │
           │     ├─ Sample distance to collision
           │     ├─ Find distance to mesh boundary:
           │     │  └─ mcdc/transport/mesh/structured.py
           │     │     ├─ i += 1 to next mesh boundary? Distance: dx
           │     │     ├─ j += 1 to next mesh boundary? Distance: dy
           │     │     ├─ k += 1 to next mesh boundary? Distance: dz
           │     │     └─ Return: min(dx, dy, dz)
           │     │
           │     ├─ Transport to collision or boundary
           │     ├─ Score to tallies:
           │     │  └─ mcdc/transport/tally/interface.py
           │     │
           │     └─ Repeat
           │
           └─ When done: gather all results
              └─ mcdc/output.py → write output.h5
```

---

## For Photon Transport

```
Neutrons:
  mcdc/transport/physics/neutron/
    ├── interface.py
    ├── native.py
    └── multigroup.py

Photons (parallel structure):
  mcdc/transport/physics/photon/
    ├── interface.py                (Compton, PE, pair production lookup)
    ├── native.py                   (NIST data loader)
    ├── distributions.py            (Klein-Nishina, pair kinematics)
    ├── cross_sections.py           (σ_total, σ_compton, etc.)
    └── util.py

When user sets particle="photon":
  └─ Branching in transport loop
     └─ Calls mcdc/transport/physics/photon/interface.py
        instead of mcdc/transport/physics/neutron/interface.py
```

### Photon HDF5 Data Format (`data/mcdc/`)

Photon cross-section files (e.g., `H.h5`, `Al.h5`, `Pb.h5`) use a hierarchical
structure consistent with the neutron library format:

```
{Element}.h5
├── atomic_number: int64
├── atomic_weight_ratio: float64
├── element_name: string
├── excitation_level: int64          (0 = ground state)
├── fissionable: bool                (False for all photon elements)
└── photon_reactions/
    ├── xs_energy_grid: float64[N]   (shared energy grid, MeV)
    ├── elastic/MT-502/              (Coherent / Rayleigh scattering)
    │   ├── Q-value: float64 (0.0)
    │   ├── reference_frame: "LAB"
    │   └── xs: float64[N]
    ├── incoherent_scattering/MT-504/ (Compton scattering)
    │   ├── Q-value: float64 (0.0)
    │   ├── reference_frame: "LAB"
    │   └── xs: float64[N]
    ├── photoelectric_absorption/
    │   ├── MT-501/                   (total photoelectric)
    │   │   ├── Q-value: float64 (0.0)
    │   │   ├── reference_frame: "LAB"
    │   │   └── xs: float64[N]
    │   └── shell_resolved/           (per-shell cross-sections)
    │       ├── K/
    │       │   ├── binding_energy: float64
    │       │   └── xs: float64[N]
    │       └── [L1, L2, M1, ...]/
    ├── pair_production/MT-503/
    │   ├── Q-value: float64 (0.0)
    │   ├── reference_frame: "LAB"
    │   ├── nuclear_field/xs: float64[N]
    │   ├── electron_field/xs: float64[N]
    │   └── xs: float64[N]            (total = nuclear + electron)
    └── total/MT-401/
        ├── Q-value: float64 (0.0)
        ├── reference_frame: "LAB"
        └── xs: float64[N]
```

**MT codes** follow the photon reaction numbering convention:
`502` = coherent, `504` = incoherent, `501` = photoelectric, `503` = pair production, `401` = total.

**Loading photon data:**
```python
import h5py

def load_photon_element(element_name):
    """Load photon cross-sections from data/mcdc/{element_name}.h5."""
    with h5py.File(f"data/mcdc/{element_name}.h5", 'r') as f:
        pr = f['photon_reactions']
        energies = pr['xs_energy_grid'][()]
        compton   = pr['incoherent_scattering/MT-504/xs'][()]
        pe        = pr['photoelectric_absorption/MT-501/xs'][()]
        pair      = pr['pair_production/MT-503/xs'][()]
        total     = pr['total/MT-401/xs'][()]
    return energies, compton, pe, pair, total
```

The reformatting tool lives at `photon_transport_code/tools/reformat_photon_data.py`.

---

## File Dependency Summary

### Always Used (Every Simulation)
```
mcdc/__init__.py
mcdc/main.py                           [run() function]
mcdc/mcdc_set/                         [user API setup]
mcdc/transport/simulation.py           [main transport loop]
mcdc/transport/physics/neutron/        [cross-sections]
mcdc/transport/particle_bank.py        [particle tracking]
mcdc/transport/tally/interface.py      [scoring]
mcdc/output.py                         [HDF5 output]
```

### Used if Mesh Geometry
```
mcdc/mcdc_set/mesh.py                  [mesh definition]
mcdc/transport/mesh/structured.py      [mesh cell finding]
```

### Used if Surface Geometry
```
mcdc/mcdc_set/surface.py               [surface definition]
mcdc/transport/geometry/surface/       [intersection calculations]
```

### Used if Eigenvalue Mode
```
mcdc/transport/simulation.py            [eigenvalue_simulation function]
mcdc/transport/technique.py             [fission/source handling]
```

### Used if Implicit Capture
```
mcdc/transport/technique.py             [implicit capture weighting]
```

### Used if MPI
```
mcdc/transport/mpi.py                  [MPI communication]
```

---

## Example Output Files

After `mcdc.run()`, you get:
```
output.h5 (HDF5 file)
  ├─ /tally_0/               (first tally)
  │  ├─ scores/              (e.g., flux, reaction rate)
  │  ├─ mean/
  │  └─ sdev/
  ├─ /tally_1/               (second tally)
  │  └─ ...
  └─ /settings/              (simulation metadata)
     ├─ N_particle
     ├─ N_batch
     ├─ materials
     └─ ...
```

Read with:
```python
import h5py
with h5py.File('output.h5', 'r') as f:
    flux = f['/tally_0/scores'][:]
    flux_mean = f['/tally_0/mean'][:]
    flux_sdev = f['/tally_0/sdev'][:]
```

---

## Quick Reference: For Photon Transport

**Key differences when photon transport added:**

| Component | Neutron | Photon | Location |
|-----------|---------|--------|----------|
| Cross-section | mcdc/transport/physics/neutron/ | mcdc/transport/physics/photon/ | ← NEW |
| Scattering | Kalbach-Mann, etc. | Klein-Nishina | distributions/ |
| Reactions | Fission, capture, elastic | Compton, PE, pair prod | physics/ |
| Particle state | Energy group | Continuous energy | Modified struct |
| Transport loop | Same branching logic | Same branching logic | Minimal changes |

**Key photon files:**
```
data/mcdc/{Element}.h5                    ← Reformatted photon cross-section library
photon_transport_code/tools/
  reformat_photon_data.py                 ← Reformatting + validation tool
mcdc/transport/physics/photon/            ← Photon physics module
mcdc/mcdc_set/photon_material.py          ← Photon material setup API
mcdc/mcdc_get/photon_material.py          ← Photon material getter
```

Most of the transport loop stays the same!

