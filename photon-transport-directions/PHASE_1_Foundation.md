# PHASE 1: Foundation - Skeleton Files & Structure

## Quick Context
Phase 1 creates the directory structure and skeleton files with complete docstrings and function signatures. No physics implementation—only `pass` statements. All 9 primary code files are created, plus 3 memory files.

## READ FIRST (Documentation)
- `photon-transport-docs/FILE_STRUCTURE_GUIDE.md` (Phase 1 section — core physics location, 6 files)
- `photon-transport-docs/THREE_CRITICAL_FILES_TIMELINE.md` (interface.py, cross_sections.py, distributions.py timing)
- `photon-transport-docs/VALIDATION_STRATEGY.md` (Phase 1 Acceptance Criteria section)

## WORKING DIRECTORY
```
c:\Projects\MCDC\photon-transport-code\
```

## REFERENCE PATTERNS
- `mcdc/transport/physics/neutron/interface.py` — Function signature pattern with @njit decorators
- `mcdc/transport/physics/neutron/cross_sections.py` — Cross-section function structure
- `mcdc/mcdc_set/material.py` — User API class pattern

## DELIVERABLES (9 Code Files + 3 Memory Files)

### Core Physics Module (6 files)
1. `transport/physics/photon/__init__.py` — Public API exports
2. `transport/physics/photon/interface.py` (~50 LOC) — Three @njit entry points: compton_scatter, pair_production, photoelectric_absorption
3. `transport/physics/photon/cross_sections.py` (~100 LOC) — Four @njit stubs: klein_nishina_total, photoelectric_total, pair_production_total, total_cross_section
4. `transport/physics/photon/distributions.py` (~80 LOC) — Three @njit stubs: sample_klein_nishina, sample_pair_production, sample_photoelectric_shell
5. `transport/physics/photon/native.py` (~50 LOC) — load_nist_xcom function stub, data caching sketch
6. `transport/physics/photon/util.py` (~30 LOC) — Helper functions, constants (MeV_to_keV, PAIR_THRESHOLD_MeV, etc.)

### User API (2 files)
7. `mcdc_set/photon_material.py` (~50 LOC) — PhotonMaterial class with @njit decorators, setters for element/density/cross-section type
8. `test/unit/photon/conftest.py` (~30 LOC) — Pytest fixtures: photon_energies, materials, nist_data

### Test Structure (1 file)
9. `test/regression/photon/__init__.py` — Empty package marker

### Memory Files (in `.claude/projects/c--Projects-MCDC/memory/`)
10. `photon_data_structures.md` — Skeleton: particle state fields, cross-section table format, tally structure compatibility
11. `photon_physics_reference.md` — Skeleton: placeholder for formulas, reference links (Evans, NIST, ICRU)
12. `integration_checklist.md` — Skeleton: Phase 2-5 integration tasks, file dependencies, testing checkpoints

## REQUIREMENTS
✅ All functions use @njit decorator (from numba import njit)
✅ All functions have complete docstrings: Parameters, Returns, Notes sections
✅ All functions contain only `pass` statement (no implementation)
✅ Follow Black code formatting (line length 88)
✅ All imports work (use relative imports within package)
✅ All existing __init__.py files remain untouched
✅ Memory file skeletons have placeholder text (full content in Phase 2+)

## VALIDATION (from VALIDATION_STRATEGY.md Phase 1)
Run these checks:
```bash
# 1. Import checks
python -c "from transport.physics.photon import interface; print('✓ interface imports')"
python -c "from transport.physics.photon import cross_sections; print('✓ cross_sections imports')"
python -c "from transport.physics.photon import distributions; print('✓ distributions imports')"
python -c "import mcdc_set.photon_material; print('✓ photon_material imports')"

# 2. Black formatting
black --check transport/physics/photon/ mcdc_set/photon_material.py test/unit/photon/

# 3. Pytest fixture discovery
pytest test/unit/photon/conftest.py --collect-only -q
```

## SUCCESS CRITERIA
✅ All 9 code files created with correct structure
✅ All 3 memory files created in correct location
✅ All function signatures present with @njit decorators
✅ All docstrings complete (Parameters/Returns/Notes present)
✅ All functions contain only `pass` statements (no logic)
✅ All imports work without error
✅ Black formatting passes with no warnings
✅ File line counts ±10% of targets (interface ~50, cross_sections ~100, distributions ~80, etc.)

## IMPORTANT
STOP after Phase 1 completion. Do NOT proceed to Phase 2.
