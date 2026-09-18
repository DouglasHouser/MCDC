# MCDC Photon Transport Development

## Project Overview
Developing photon transport physics module for MCDC (Monte Carlo / Dynamic Code), a performant Python-based Monte Carlo transport framework.

**Documents**:
- **PHOTON_TRANSPORT_RESEARCH_PLAN.md** (project root) - Comprehensive development strategy (11 sections) + timeline options
  - **ACCELERATED_TIMELINE.md** (memory/) - Detailed 3-5 day AI-assisted timeline
  - **PHOTON_QUICKSTART.md** (memory/) - Quick reference + phase checklists
  - **STRATEGY_OVERVIEW.md** (memory/) - Visual roadmap + FAQ + decision matrix
  - **photon_physics_reference.md** (memory/) - Physics formulas (to create)
  - **photon_data_structures.md** (memory/) - Data layouts (to create)
  - **photon_integration_notes.md** (memory/) - Integration discoveries (to create)

## MCDC Architecture Patterns

### Core Structure
- **Framework**: Python with Numba JIT compilation for performance
- **Parallelization**: MPI for distributed computing via mpi4py
- **Physics organization**: `mcdc/transport/physics/{particle_type}/` (currently has neutron)
- **Data handling**: HDF5 via h5py for output, structured arrays for particle data
- **Code generation**: Code factory produces boilerplate setter/getter functions (@njit decorated)

### Key Modules
- `mcdc_set/`: User API for setting up simulation objects (materials, tallies, sources, distributions)
- `mcdc_get/`: Getters for simulation objects
- `transport/physics/`: Particle interaction physics
- `transport/geometry/`: Geometry handling (surfaces, mesh)
- `transport/tally/`: Tally scoring
- `code_factory/`: Auto-generates @njit accessor functions

### Neutron Transport Example
- Native and multigroup cross-section handling
- Reactions: elastic scattering, inelastic scattering, fission, capture
- Distributions: Kalbach-Mann, tabulated energy-angle, evaporation, Maxwellian, level scattering
- Bank management: active, future, census, source banks

### Testing & CI/CD
- Black code style checking
- Docker-based regression testing on GPU/CPU
- Sphinx documentation (RST format) via Read the Docs
- pytest framework for tests

## Documentation Standards
- Sphinx/RST format in `/docs/source/`
- JOSS paper cited (Morgan et al. 2024)
- Example-driven approach with working test cases
- Contribution guidelines available
