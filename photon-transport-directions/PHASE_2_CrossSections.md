# PHASE 2: Cross-Sections - Formula Implementation & NIST Validation

## Quick Context
Phase 2 implements actual cross-section formulas for three photon interaction processes. Phase 1 created skeleton files; now populate with real physics calculations. Native.py loads and caches NIST XCOM reference data for validation.

**Previous:** Phase 1 skeletons complete
**Now:** Implement Klein-Nishina, photoelectric, pair production formulas
**Next:** Phase 3 (interaction sampling/distributions)

## VALIDATION CRITERIA (EMBEDDED from VALIDATION_STRATEGY.md Phase 2)

**Tolerance:** ±1-2% vs NIST XCOM reference data
**Test energies:** 0.1 MeV, 1.0 MeV, 5.0 MeV, 10.0 MeV
**Test elements:** Aluminum (Z=13), Lead (Z=82), Water (H₂O composite)
**Threshold check:** Pair production must be exactly 0 below 1.022 MeV

## PHYSICS FORMULAS (EMBEDDED from photon_physics_reference.md)

### Klein-Nishina Compton Cross-Section

```
σ_KN(E) = 2π × r_e² × (m_e c²)² / E² ×
  [1/(1+α) × (1 + α/(1+2α)) +
   (α/(1+2α)²)² × (2α(1+α)/(1+2α) - ln(1+2α)) +
   ln(1+2α)/(2α) - (1+3α)/((1+2α)²)]

Constants:
- r_e = 2.818e-15 m (classical electron radius)
- m_e c² = 0.511 MeV
- α = E / (m_e c²)
- Energy range: 0.01 - 100 MeV
- Result in barns (1 barn = 1e-24 cm²)
```

### Photoelectric Absorption Cross-Section

```
σ_PE(E, Z) depends on K-shell K-edge energy:
- For E > K_edge: σ_PE ∝ Z^3.8 / E^3.2
- For E < K_edge: σ_PE ∝ Z^4 / E^3.1

K-edge energies for test elements:
- Al (Z=13): 1.560 keV
- Pb (Z=82): 88.0 keV
- H (Z=1): ~0.014 keV
- O (Z=8): 0.543 keV

Energy range: 0.01 - 100 MeV
Implementation: Use NIST tabulated data or apply parameterization
```

### Pair Production Cross-Section

```
σ_PP(E, Z) = 0                           for E < 1.022 MeV (THRESHOLD)
           ∝ Z² × (ln(2E/(m_e c²)) - 1/9)  for E > 1.022 MeV

Constants:
- PAIR_THRESHOLD = 1.022 MeV (exactly 2 × m_e c²)
- m_e c² = 0.511 MeV
- Energy range: 1.022 - 100 MeV
- Z² dependence for screening

Implementation: Use Bethe-Heitler formula or NIST approximation
```

### Total Cross-Section

```
σ_total(element, E) = σ_KN(E) + σ_PE(E, element) + σ_PP(E, element)

This is the sum of all three interaction processes.
```

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon-transport-code\
```

## REFERENCE PATTERNS
- `mcdc/transport/physics/neutron/cross_sections.py` — Implementation structure for cross-section functions
- Query NIST XCOM database or use local reference data for aluminum, lead, water

## DELIVERABLES (3 Code Files + Unit Tests)

### Core Implementation
1. `transport/physics/photon/cross_sections.py` (~700 LOC) — FULLY IMPLEMENTED
   - `klein_nishina_total(E)` → must match NIST reference ±1-2%
   - `photoelectric_total(element, E)` → must match NIST reference ±1-2%
   - `pair_production_total(element, E)` → must match NIST reference ±1-2%
   - `total_cross_section(element, E)` → combines all three

2. `transport/physics/photon/native.py` (~200 LOC) — FULLY IMPLEMENTED
   - `load_nist_xcom(element_name, energy_range)` → fetches/caches reference data
   - Data caching mechanism (avoid repeated external calls)
   - Reference values for: aluminum (Z=13), lead (Z=82), water (H₂O composite)

3. `test/unit/photon/test_cross_sections.py` (~300 LOC) — FULLY IMPLEMENTED
   - Test fixtures: aluminum, lead, water at standard energies [0.1, 1.0, 5.0, 10.0] MeV
   - Test Klein-Nishina, photoelectric, pair production individually
   - All cross-sections must validate ±1-2% against NIST reference

### Memory Update
4. Update `.claude/projects/c--Projects-MCDC/memory/photon_physics_reference.md`
   - Add Klein-Nishina formula with derivation reference
   - Add photoelectric shell model references
   - Add pair production threshold notes (2.044 MeV)
   - Add validation results from Phase 2 tests

## REQUIREMENTS
✅ All cross-sections match NIST reference within ±1-2% tolerance for test cases
✅ Energy ranges: Klein-Nishina (0.01-20 MeV), photoelectric (0.01-100 MeV), pair production (1.022-100 MeV)
✅ NIST data efficiently cached/loaded (minimize external API calls)
✅ All functions remain @njit compatible
✅ Black formatting compliant (line length 88)
✅ Complete docstrings on all new functions

## VALIDATION (from VALIDATION_STRATEGY.md Phase 2)
Run these tests:
```bash
# 1. Cross-section validation tests
pytest test/unit/photon/test_cross_sections.py -v

# 2. Check NIST accuracy
# All tests must pass with cross-sections within ±1-2% of reference

# 3. Black formatting
black --check transport/physics/photon/cross_sections.py transport/physics/photon/native.py

# 4. Import check
python -c "from transport.physics.photon import cross_sections; print('✓ cross_sections fully implemented')"
```

## SUCCESS CRITERIA
✅ `cross_sections.py` fully implemented and tested
✅ `native.py` loads NIST data without errors
✅ Unit test file created with 4+ test functions
✅ All cross-section values ±1-2% of NIST reference at [0.1, 1, 5, 10] MeV
✅ All tests pass without warnings
✅ Black formatting passes
✅ Memory file updated with formulas and validation results

## IMPORTANT
STOP after Phase 2 completion. Do NOT proceed to Phase 3.

---

## TOKEN OPTIMIZATION NOTE

**This prompt is designed to minimize token usage:**
- ✅ Formulas embedded (saves reading photon_physics_reference.md)
- ✅ Validation criteria embedded (saves reading VALIDATION_STRATEGY.md Phase 2)
- ✅ Energy ranges and test elements specified directly
- ✅ Only reference FILE_STRUCTURE_GUIDE.md if "what files" questions arise
- **Estimated token savings:** ~25K tokens vs standard doc-reference approach

**If token limits are hit, use sub-tasks:**
1. **Phase 2a:** Implement `cross_sections.py` formulas only (~10K tokens)
2. **Phase 2b:** Implement `native.py` data loading (~8K tokens)
3. **Phase 2c:** Implement unit tests (~8K tokens)

