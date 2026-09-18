# PHASE 3: Distributions - Sampling Algorithms & Kinematics

## Quick Context
Phase 3 implements sampling algorithms for each photon interaction type. Klein-Nishina scattering, pair production, and photoelectric absorption all use physics formulas to sample final state energies and angles. Energy and momentum conservation must be verified.

## READ FIRST (Documentation)
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` (Phase 3 section — sampling functions)
- `.claude/projects/c--Projects-MCDC/memory/photon_physics_reference.md` (Sampling algorithms, kinematics)
- `photon-transport-docs/VALIDATION_STRATEGY.md` (Phase 3 Acceptance Criteria section)

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon_transport_code\
```

## REFERENCE PATTERNS
- `mcdc/transport/physics/neutron/distributions.py` — Sampling function structure
- `mcdc/transport/physics/neutron/` — How to sample angles and energies with @njit

## DELIVERABLES (3 Code Files + Unit Tests)

### Core Implementation
1. `photon_transport_code/transport/physics/photon/distributions.py` (~600 LOC) — FULLY IMPLEMENTED
   - `sample_klein_nishina(E_in, rng_state)` → (E_out, direction) with proper angle/energy relation
   - `sample_pair_production(E_gamma, rng_state)` → (E_electron, E_positron, direction)
   - `sample_photoelectric_shell(E_photon, element, rng_state)` → (E_electron, direction)
   - All use inverse transform sampling or rejection sampling as appropriate

2. `photon_transport_code/transport/physics/photon/interface.py` — UPDATE (add imports from distributions.py)
   - Import: `from .distributions import sample_klein_nishina, ...`
   - Integrate sampling functions into main interface

3. `photon_transport_code/test/unit/photon/test_distributions.py` (~400 LOC) — FULLY IMPLEMENTED
   - Test energy conservation: |E_in - E_out| < 1e-10 MeV (numerical precision)
   - Test angle sampling: θ drawn from correct probability distribution
   - Test Compton kernel: verify Klein-Nishina cross-section at sampled angles
   - Test pair production: verify electron/positron energy distribution
   - Test photoelectric: verify electron energy from shell binding

### Memory Update
4. Update `.claude/projects/c--Projects-MCDC/memory/photon_physics_reference.md`
   - Add sampling algorithm details (inverse transform, rejection sampling)
   - Add energy conservation implementation notes
   - Add angle/energy correlation formulas
   - Add RNG usage patterns (Numba-compatible)

## REQUIREMENTS
✅ All sampling functions use inverse transform or rejection sampling (standard MC methods)
✅ Energy conservation: |E_input - E_output| < 1e-10 MeV
✅ Angle distributions physically realistic (cos θ for PE, Klein-Nishina for Compton, etc.)
✅ All functions remain @njit compatible
✅ All functions use RNG properly (Numba-compatible rng_state)
✅ Black formatting compliant
✅ Complete docstrings on all functions

## VALIDATION (from VALIDATION_STRATEGY.md Phase 3)
Run these tests:
```bash
# 1. Distribution sampling tests
pytest photon_transport_code/test/unit/photon/test_distributions.py -v

# 2. Energy conservation check
# Each test must verify |E_in - E_out| < 1e-10 MeV

# 3. Angle distribution validation
# Histograms should match theoretical distributions

# 4. Black formatting
black --check transport/physics/photon/distributions.py transport/physics/photon/interface.py

# 5. Integration with cross_sections
python -c "from transport.physics.photon import cross_sections, distributions; print('✓ distributions + cross_sections integrate')"
```

## SUCCESS CRITERIA
✅ `distributions.py` fully implemented with 3 sampling functions
✅ `interface.py` updated with distribution imports
✅ Unit test file created with 6+ test functions
✅ All energy conservation tests pass (ε < 1e-10 MeV)
✅ Angle distributions physically correct (visual inspection of histograms acceptable)
✅ All tests pass without warnings
✅ Black formatting passes
✅ Memory file updated with sampling algorithm details

## IMPORTANT
STOP after Phase 3 completion. Do NOT proceed to Phase 4.
