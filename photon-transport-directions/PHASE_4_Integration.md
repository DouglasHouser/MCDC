# PHASE 4: Integration - Full Interface & System Testing

## Quick Context
Phase 4 fully implements the interface.py entry point that ties together cross-sections and distributions. The photon transport loop is integrated with MCDC's transport framework. All existing neutron regression tests must still pass.

## READ FIRST (Documentation)
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` (Phase 4 section — interface full impl)
- `photon-transport-docs/MCDC_FILE_ARCHITECTURE.md` (how neutron code integrates, mesh slab example)
- `photon-transport-docs/VALIDATION_STRATEGY.md` (Phase 4 Acceptance Criteria section)

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon-transport-code\
```

## REFERENCE PATTERNS
- `mcdc/transport/physics/neutron/interface.py` — Full implementation showing all interaction types
- `mcdc/transport/tally/interface.py` — Tally scoring integration
- `mcdc/output.py` — How results are output

## DELIVERABLES (2 Code Files + Regression Tests)

### Core Implementation
1. `transport/physics/photon/interface.py` (~200 LOC) — FULLY IMPLEMENTED
   - `compton_scatter(photon_energy, rng_state)` → complete logic with cross-section lookup + sampling
   - `pair_production(photon_energy, element, rng_state)` → complete with threshold check
   - `photoelectric_absorption(photon_energy, element, shell, rng_state)` → complete with binding energy
   - Integrate: call cross_sections.py, then distributions.py
   - Add: interaction type selection logic based on probabilities

2. `mcdc_set/photon_material.py` — FULLY IMPLEMENT
   - Complete PhotonMaterial class with all setter methods
   - Ensure compatibility with MCDC's material registration system
   - Add validation (element exists, density > 0, etc.)

### Regression Tests (from neutron examples)
3. `test/regression/photon/test_compton_scattering.py` — Compton-dominated scenario
4. `test/regression/photon/test_pair_production.py` — Pair production threshold testing
5. `test/regression/photon/test_photoelectric_absorption.py` — Absorption-dominated scenario
6. `test/regression/photon/test_mixed_interactions.py` — All three interaction types
7. `test/regression/photon/test_neutron_compatibility.py` — Verify neutron tests still pass

### Integration File
8. `mcdc_get/photon_material.py` — AUTO-GENERATED (copy neutron pattern)
   - Auto-generated getters from PhotonMaterial class
   - Use code_factory pattern if available, else manual getters

## REQUIREMENTS
✅ Interface.py calls cross-sections.py and distributions.py correctly
✅ All 3 photon interactions (Compton, pair prod, photoelectric) functional
✅ Photon material class integrates with MCDC setter/getter pattern
✅ MCDC compatibility: all 60+ existing neutron tests still pass
✅ No circular imports between cross_sections, distributions, interface
✅ All @njit decorators present and functional
✅ Black formatting compliant

## VALIDATION (from VALIDATION_STRATEGY.md Phase 4)
Run these tests:
```bash
# 1. Regression tests
pytest test/regression/photon/ -v

# 2. Confirm neutron compatibility (all neutron tests must still pass)
pytest test/regression/neutron/ -v

# 3. Integration test
python -c "from mcdc_set.photon_material import PhotonMaterial; from mcdc_get.photon_material import get_element; print('✓ Full integration')"

# 4. Black formatting
black --check transport/physics/photon/ mcdc_set/photon_material.py mcdc_get/photon_material.py
```

## SUCCESS CRITERIA
✅ `interface.py` fully implemented with all 3 interaction types functional
✅ `photon_material.py` (mcdc_set) fully implemented with validation
✅ `photon_material.py` (mcdc_get) auto-generated successfully
✅ All 5 regression tests pass
✅ All 60+ existing neutron tests still pass (no breakage)
✅ No circular imports
✅ All Black formatting passes
✅ System-level integration successful

## IMPORTANT
STOP after Phase 4 completion. Do NOT proceed to Phase 5.
