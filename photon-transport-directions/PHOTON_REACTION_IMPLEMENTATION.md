# PHOTON REACTION IMPLEMENTATION - Object-Oriented Architecture

## Quick Context
Refactor photon transport to use an object-oriented reaction architecture (mirroring `mcdc/object_/neutron_reaction.py`) rather than inline function-based collision handling. This improves code maintainability, extensibility, and consistency with the neutron transport module.

**Current State:** Reactions embedded in `interface.py` collision function; physics inline
**After:** Dedicated `photon_reaction.py` with polymorphic reaction classes; interface.py delegates to them
**Benefit:** Cleaner code, easier testing, enables future reaction types (coherent scattering, triplet production)

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon-transport-code\
c:\Projects\MCDC\mcdc\
```

## REFERENCE PATTERNS
- `mcdc/object_/neutron_reaction.py` — Polymorphic base class + 4 reaction subclasses + helper functions
- `mcdc/transport/physics/photon/interface.py` — Current collision logic (refactor target)
- `mcdc/object_/photon_material.py` — Material definition (no changes needed)

## DELIVERABLES (5 Code Files + Updated Tests)

### Core Reaction Module (3 Files)

**1. `mcdc/object_/photon_reaction.py` (~400 LOC) — NEW FILE**
   - `PhotonReactionBase` class
     - Attributes: `type` (int), `MT` (int), `xs` (NDArray), `xs_offset_` (int), `label` (str)
     - Methods: `__init__`, `__repr__`, `decode_type()` helper
   - `PhotonReactionCompton` subclass
     - Perform Compton scattering collision inline
     - Sample scattered energy & direction using Kahn (1954) method
     - Update particle energy, direction, alive flag
   - `PhotonReactionPhotoelectric` subclass
     - Absorb photon (set alive=False)
     - No secondary particle production
   - `PhotonReactionPairProduction` subclass
     - Absorb photon above threshold
     - Track e+/e- pair production (mark alive=False for photon, can add e+/e- tracking)
   - Helper functions:
     - `decode_type(type_)` → "Compton", "Photoelectric", "Pair Production"
     - Reaction type constants matching interface.py

**2. `mcdc/object_/photon_reaction_loader.py` (~150 LOC) — NEW FILE**
   - Load photon reaction data from HDF5 (future compatibility)
   - `load_photon_reaction(h5_group, type_) → PhotonReactionBase`
   - Stub for now; enables future data-driven reaction loading

**3. `photon_transport_code/transport/physics/photon/interface.py` (~200 LOC) — REFACTORED**
   - Replace inline collision logic with reaction object dispatch
   - Modify `collision(particle_container, mcdc, data)`:
     - Sample reaction type as before (Compton, PE, PP)
     - Create or retrieve reaction object
     - Call reaction's perform_collision() method
     - Let reaction update particle state in-place
   - Reaction constants now imported from `mcdc.object_.photon_reaction`
   - Remove ~400 lines of inline Compton/PE/PP code

### Physics Module Updates (2 Files)

**4. `photon_transport_code/transport/physics/photon/cross_sections.py` (MINOR CHANGES)**
   - Add import: `from mcdc.object_.photon_reaction import (PHOTON_REACTION_COMPTON, PHOTON_REACTION_PHOTOELECTRIC, PHOTON_REACTION_PAIR_PRODUCTION)`
   - Update `macro_compton_xs()`, `macro_photoelectric_xs()`, `macro_pair_production_xs()` function signatures to accept reaction type constants from photon_reaction
   - No functional changes to calculation logic

**5. `photon_transport_code/transport/physics/photon/native.py` (NO CHANGES)**
   - Imports remain compatible
   - Element data loading unaffected

### Material & Integration (1 File)

**6. `mcdc/object_/photon_material.py` (NO CHANGES)**
   - PhotonMaterial class unchanged
   - Flat buffer structure compatible with new reaction model

### Tests (4 Files + Extensions)

**7. `photon_transport_code/test/unit/photon/test_photon_reaction.py` (~300 LOC) — NEW FILE**
   - Test PhotonReactionBase initialization
   - Test PhotonReactionCompton:
     - Sample multiple collisions, verify energy < input
     - Verify direction updated (|𝛍| ≤ 1)
     - Test edge cases: very high/low energy
   - Test PhotonReactionPhotoelectric:
     - Verify photon marked alive=False
     - Verify weight/tally updates (if applicable)
   - Test PhotonReactionPairProduction:
     - Verify threshold behavior (E < 1.022 MeV rejected)
     - Verify E >= 1.022 MeV produces pair
     - Check photon marked alive=False
   - Test helper functions: `decode_type()`

**8. `photon_transport_code/test/integration/test_photon_reaction_collision.py` (~200 LOC) — NEW FILE**
   - Full collision cycle: sample reaction type → execute → verify particle state
   - Test energy conservation (Compton only)
   - Test direction normalization after all reactions
   - Test material loop with mixed reactions

**9. `photon_transport_code/test/unit/photon/test_interface_refactor.py` (~150 LOC) — NEW FILE**
   - Verify `collision()` function still produces same statistical results as before
   - Run same test problem (e.g., photon_slab) with old vs new; compare tally outputs
   - Regression test: ensure no physics changes, only code structure

**10. Update existing test files**
   - `photon_transport_code/test/unit/photon/test_coverage_gaps.py` — Add imports from photon_reaction
   - `photon_transport_code/MCNP_Verification_Tests/` — Re-run all benchmarks, verify results unchanged

## ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│ User API / Simulation                                       │
│ (problem.py, examples/photon_slab/problem.py)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Simulation Transport Loop                                    │
│ mcdc.main / photon_transport_code/transport/main.py         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Collision Handler (REFACTORED)                              │
│ photon_transport_code/transport/physics/photon/interface.py │
│  collision(particle, mcdc, data)                            │
│  ├─ Sample Sigma_C, Sigma_PE, Sigma_PP                     │
│  ├─ Select reaction type                                   │
│  ├─ CREATE reaction object (Compton/PE/PP)                 │
│  └─ CALL reaction.perform_collision(particle, mcdc, data)  │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ Reaction Objects (NEW)                                       │
│ mcdc/object_/photon_reaction.py                              │
│                                                              │
│ PhotonReactionBase (abstract)                               │
│  ├─ type, MT, xs, xs_offset_                               │
│  └─ __repr__()                                              │
│                                                              │
│ PhotonReactionCompton                                        │
│  ├─ perform_collision() — Kahn (1954) inline sampling      │
│  └─ __repr__()                                              │
│                                                              │
│ PhotonReactionPhotoelectric                                  │
│  ├─ perform_collision() — set alive=False                  │
│  └─ __repr__()                                              │
│                                                              │
│ PhotonReactionPairProduction                                │
│  ├─ perform_collision() — threshold check + pair production│
│  └─ __repr__()                                              │
│                                                              │
│ Helper: decode_type(type_)                                   │
└──────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ Cross-Section & Physics Support                             │
│ photon_transport_code/transport/physics/photon/              │
│  ├─ cross_sections.py (macro_compton_xs, etc.)             │
│  ├─ native.py (element data loading)                       │
│  └─ data_loader.py (reference data)                        │
└──────────────────────────────────────────────────────────────┘
```

## IMPLEMENTATION STEPS (for Claude)

### STEP 1: Create `mcdc/object_/photon_reaction.py`

**1a. Import statements**
```python
from typing import Annotated
from numpy import float64
import math
from numpy.typing import NDArray
import numpy as np
from numba import njit  # ← ADD THIS

from mcdc.object_.base import ObjectPolymorphic
from mcdc.print_ import print_error
from mcdc.constant import (
    REFERENCE_FRAME_LAB,
    REFERENCE_FRAME_COM,
)

# NEW: Import reaction type constants from photon interface
# (These will be defined in this file, not imported initially)
```

**1b. Define reaction type constants (matching current interface.py)**
```python
PHOTON_REACTION_COMPTON = 0
PHOTON_REACTION_PHOTOELECTRIC = 1
PHOTON_REACTION_PAIR_PRODUCTION = 2
PHOTON_REACTION_TOTAL = 3

# Physical constants
_SPEED_OF_LIGHT = 29.9792458  # cm/shake
_PAIR_THRESH = 2.0 * 0.51099895  # MeV (1.02199790)
_M_E = 0.51099895  # MeV (electron rest-mass energy)
```

**1c. Create `PhotonReactionBase` class**
- Inherit from `ObjectPolymorphic`
- Attributes: `type`, `MT`, `xs`, `xs_offset_`, `reference_frame`, `label`
- `__init__(self, type_, MT, xs, xs_offset, reference_frame)`
- `__repr__()` method returning formatted reaction info

**1d. Create `PhotonReactionCompton` class**
- Inherit from `PhotonReactionBase`
- `__init__(self, MT, xs, xs_offset, reference_frame)`
- **Key Method: `perform_collision(self, particle_container, mcdc, data)`**
  - Extract inline Compton scattering code from `interface.py` (lines ~180-240)
  - Sample scattered photon energy & direction using Kahn (1954) method
  - Update `particle_container[0]["E"]` with scattered energy
  - Update `particle_container[0]["ux"]`, `particle_container[0]["uy"]`, `particle_container[0]["uz"]` with new direction
  - Return None (modify particle in-place)

**1e. Create `PhotonReactionPhotoelectric` class**
- Inherit from `PhotonReactionBase`
- `__init__(self, MT, xs, xs_offset, reference_frame)`
- **Key Method: `perform_collision(self, particle_container, mcdc, data)`**
  - Set `particle_container[0]["alive"] = False`
  - (No secondary particles yet)

**1f. Create `PhotonReactionPairProduction` class**
- Inherit from `PhotonReactionBase`
- `__init__(self, MT, xs, xs_offset, reference_frame)`
- **Key Method: `perform_collision(self, particle_container, mcdc, data)`**
  - Check energy threshold: if E < 1.022 MeV, return early
  - Otherwise, set `particle_container[0]["alive"] = False`
  - (Future: track e+/e- pair production)

**1g. Add helper function**
```python
def decode_type(type_):
    """Return human-readable reaction type string."""
    if type_ == PHOTON_REACTION_COMPTON:
        return "Photon Compton scattering"
    elif type_ == PHOTON_REACTION_PHOTOELECTRIC:
        return "Photon photoelectric absorption"
    elif type_ == PHOTON_REACTION_PAIR_PRODUCTION:
        return "Photon pair production"
    elif type_ == PHOTON_REACTION_TOTAL:
        return "Photon total"
    return "Unknown"
```

### STEP 2: Refactor `photon_transport_code/transport/physics/photon/interface.py`

**2a. Update imports**
```python
from mcdc.object_.photon_reaction import (
    PhotonReactionCompton,
    PhotonReactionPhotoelectric,
    PhotonReactionPairProduction,
    PHOTON_REACTION_COMPTON,
    PHOTON_REACTION_PHOTOELECTRIC,
    PHOTON_REACTION_PAIR_PRODUCTION,
    PHOTON_REACTION_TOTAL,
    _SPEED_OF_LIGHT,
    _PAIR_THRESH,
    _M_E,
    decode_type,
)
```

**2b. Remove reaction type constants (now imported)**
- Delete lines defining PHOTON_REACTION_* constants (replace with imports)
- Delete inline constants _SPEED_OF_LIGHT, _PAIR_THRESH, _M_E

**2c. Refactor `collision()` function**

OLD STRUCTURE (current):
```python
@njit
def collision(particle_container, mcdc, data):
    # Compute partial xs
    Sigma_C = macro_compton_xs(...)
    Sigma_PE = macro_photoelectric_xs(...)
    Sigma_PP = macro_pair_production_xs(...)
    
    # Sample reaction
    xi = np.random.random() * Sigma_T
    
    if xi < Sigma_C:
        # [~100 lines of Compton inline code]
    elif xi < Sigma_C + Sigma_PE:
        # [~20 lines of Photoelectric inline code]
    else:
        # [~20 lines of Pair Production inline code]
```

NEW STRUCTURE (post-refactor):
```python
@njit
def collision(particle_container, mcdc, data):
    # Compute partial xs (UNCHANGED)
    Sigma_C = macro_compton_xs(particle_container, mcdc, data)
    Sigma_PE = macro_photoelectric_xs(particle_container, mcdc, data)
    Sigma_PP = macro_pair_production_xs(particle_container, mcdc, data)
    Sigma_T = Sigma_C + Sigma_PE + Sigma_PP

    if Sigma_T <= 0.0:
        return

    # Sample reaction type (UNCHANGED)
    xi = np.random.random() * Sigma_T

    # REFACTORED: Delegate to reaction object
    if xi < Sigma_C:
        reaction = PhotonReactionCompton(
            MT=502,  # ENDF MT for Compton
            xs=np.array([Sigma_C]),  # Simplified for now
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        reaction.perform_collision(particle_container, mcdc, data)
    elif xi < Sigma_C + Sigma_PE:
        reaction = PhotonReactionPhotoelectric(
            MT=501,  # ENDF MT for PE
            xs=np.array([Sigma_PE]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        reaction.perform_collision(particle_container, mcdc, data)
    else:
        reaction = PhotonReactionPairProduction(
            MT=503,  # ENDF MT for PP
            xs=np.array([Sigma_PP]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        reaction.perform_collision(particle_container, mcdc, data)
```

**2d. Extract Compton inline code → `PhotonReactionCompton.perform_collision()`**
- Move ~100 lines of Kahn rejection sampling logic into reaction class
- Keep physics identical; only reorganize

### STEP 3: Update tests

**3a. Create `photon_transport_code/test/unit/photon/test_photon_reaction.py`**
- Test each reaction class initialization
- Test Compton collision: sample 100 collisions, verify energy decrease
- Test PE collision: verify particle marked inactive
- Test PP collision: verify threshold, verify particle marked inactive
- Test helper functions

**3b. Create `photon_transport_code/test/integration/test_photon_reaction_collision.py`**
- Full integration: run collision() function → verify particle state
- Compare statistical results with reference

**3c. Update `photon_transport_code/MCNP_Verification_Tests/`**
- Re-run all benchmarks with refactored code
- Verify results unchanged (within tolerance)

**3d. Update `photon_transport_code/test/unit/photon/test_coverage_gaps.py`**
- Add imports: `from mcdc.object_.photon_reaction import ...`
- Existing tests should continue to pass

## INTEGRATION CHECKLIST

- [ ] Create `mcdc/object_/photon_reaction.py` with 3 reaction classes
- [ ] Reaction classes inherit from `ObjectPolymorphic`
- [ ] `perform_collision()` method signature: `(self, particle_container, mcdc, data)`
- [ ] Extract Compton sampling from `interface.py` into `PhotonReactionCompton.perform_collision()`
- [ ] Update `interface.py` to import reaction classes & delegate
- [ ] Remove inline Compton/PE/PP code from `interface.py` (~400 lines)
- [ ] Verify imports in `cross_sections.py` still resolve
- [ ] Create unit test file for reaction classes
- [ ] Create integration test file for full collision cycle
- [ ] Re-run existing tests: `test_coverage_gaps.py`, MCNP benchmarks
- [ ] Verify no regression in tally outputs or physics results
- [ ] Update documentation (docstrings in reaction classes)

## ACCEPTANCE CRITERIA

### Code Quality
✅ All reaction classes follow neutron_reaction.py polymorphic pattern
✅ All classes have complete docstrings (Parameters, Returns, Notes)
✅ Code follows Black formatting (88-char line length)
✅ All imports resolve correctly (relative + absolute)
✅ No circular import issues

### Physics Preservation
✅ Compton scattering produces identical results (bit-for-bit deterministic with same RNG seed? NO — acceptable: same statistics, different realization)
✅ Photoelectric absorption still terminates photon (alive=False)
✅ Pair production still respects 1.022 MeV threshold
✅ Total cross-section unchanged

### Testing
✅ All existing tests pass unchanged (test_coverage_gaps.py, benchmarks)
✅ New unit tests cover all reaction types
✅ Integration test verifies collision() function behavior
✅ MCNP benchmark tally outputs match original (within ±0.1% statistical noise)

### Integration
✅ `photon_transport_code/` examples run without errors
✅ `photon_transport_code/examples/photon_slab/problem.py` produces valid output
✅ Material definition & loading unchanged
✅ Cross-section functions compatible with new structure

## MIGRATION PATH (If Needed Later)

If data-driven reaction loading becomes necessary:
- `photon_reaction_loader.py` provides `load_photon_reaction_from_h5()`
- Reactions initialized from HDF5 groups (matching `neutron_reaction.from_h5_group()`)
- No API changes required; only internal implementation

## FUTURE EXTENSIONS

This structure enables:
1. **Coherent scattering** — Add `PhotonReactionCoherent` class
2. **Triplet production** — Add `PhotonReactionTriplet` class
3. **Fluorescence cascades** — Add secondary photon emission to PE
4. **Data-driven reactions** — Load distributions from nuclear data files

All without modifying the core collision dispatch logic.

## RISKS & MITIGATIONS

| Risk | Mitigation |
|------|-----------|
| Physics changes due to refactoring | Preserve Compton sampling code exactly; test vs. reference |
| Performance regression (Numba) | Keep all hot-path code in `perform_collision()`; avoid allocations |
| Import circular dependencies | Use absolute imports from `mcdc.object_`; test imports early |
| Existing code breakage | Run all existing tests; verify benchmarks produce identical results |
| Reaction object creation overhead | Consider caching reaction instances in simulation state (optional optimization) |

---

## AUTHOR NOTES

This document is designed to guide Claude through a complete refactoring. The key insight is **PRESERVE PHYSICS, RESTRUCTURE CODE**. Every physics calculation remains identical; only the code organization changes.

The inline Compton sampling is the most complex part. Extract it carefully into `PhotonReactionCompton.perform_collision()`, testing against reference data at each step.
