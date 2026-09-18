# MC/DC Photon Transport Development: Research & Implementation Plan

**Version**: 1.0 (AI-Accelerated)
**Date**: April 7, 2026
**Status**: Planning Phase → Ready for Implementation
**Related Documentation**: See MCDC neutron transport at `mcdc/transport/physics/neutron/`

---

## ⚡ Quick Start

**For AI-accelerated development**: See [`ACCELERATED_TIMELINE.md`](photon-transport/ACCELERATED_TIMELINE.md) (3-5 working days)

**For detailed planning**: Continue reading this document (11 sections)

---

## 1. Executive Summary

This document outlines a structured approach to developing photon transport physics for MC/DC. The plan leverages the existing neutron transport architecture while adapting for photon-specific physics. It prioritizes effective documentation, systematic development tracking, and alignment with MCDC's established patterns.

**Key Success Metrics:**
- Parallel structure to neutron transport for maintainability
- Full coverage of standard photon interactions (Compton, pair production, photoelectric)
- Automated testing to 95%+ coverage
- Complete Sphinx documentation with working examples
- Integration with existing geometry/tally/output systems

**Timeline Options:**
- **Manual development**: 5-6 weeks
- **Claude Code generation**: 3-5 working days (see ACCELERATED_TIMELINE.md)

---

## 2. Architecture Analysis & Design Phase

### 2.1 Current Neutron Transport Structure Review

```
mcdc/transport/physics/neutron/
├── __init__.py
├── interface.py          # Public API
├── native.py             # Open-source data handling
├── multigroup.py         # Multigroup cross-sections
```

**Key Patterns:**
1. **Interface module** defines public functions used by simulation kernel
2. **Data handlers** (native, multigroup) abstract cross-section sources
3. **Reactions** are separate entities with distribution data
4. **Numba JIT**: All hot-path code uses `@njit` decorator
5. **Auto-generated setters/getters** in `mcdc_set/` and `mcdc_get/`

### 2.2 Photon Transport Physics Scope

**Core Processes** (in priority order):
1. **Compton Scattering** - dominant at medium energies (dominant for diagnostic energies)
2. **Photoelectric Absorption** - dominant at low energies
3. **Pair Production** - dominant above 2-3 MeV
4. **Rayleigh Scattering** - coherent scatter (minor contribution)
5. **Photonuclear Reactions** - high energy (~10+ MeV), lower priority initially

**Derived Quantities:**
- Total cross-section (sum of components)
- Interaction kinematics (Klein-Nishina for Compton, etc.)
- Energy degradation spectra

### 2.3 Design Decisions

| Decision | Rationale | Implementation |
|----------|-----------|-----------------|
| **Separate photon module** | Keeps neutron code clean, allows independent development | `photon-transport-code/transport/physics/photon/` |
| **Parallel data structure** | Leverages existing patterns, reduces cognitive load | Mirror neutron's native.py + multigroup.py |
| **Initial: native only** | Validate approach before adding multigroup complexity | Start with open-source database (NIST, Geant4) |
| **Use existing geometry** | No geometry changes needed; photons use same surfaces/mesh | `mcdc/transport/geometry/` unchanged |
| **Shared tally system** | Tallies should work for any particle type | Verify tally classes accept photon data |

---

## 3. Development Phases

### Phase 1: Foundation (0.5 days with Claude / Week 1-2 manual)
**Objective**: Establish structure and basic infrastructure

#### 1.1 Repository Structure (SKELETON FILES ONLY)

**Created in Phase 1:** Empty file stubs with docstrings (ready for Phase 2+ implementation)

```
photon-transport-code/transport/physics/photon/
├── __init__.py                          # Empty, ready for Phase 2+
├── interface.py                         # Skeleton with docstrings (filled Phase 2-3)
├── native.py                            # Skeleton (filled Phase 2)
├── distributions.py                     # Skeleton (filled Phase 3)
├── cross_sections.py                    # Skeleton (filled Phase 2)
└── util.py                              # Skeleton (filled Phase 2-3)

photon-transport-code/mcdc_set/
├── photon_material.py                   # Skeleton (filled Phase 1-2)

photon-transport-code/mcdc_get/
├── photon_material.py                   # Auto-generated (Phase 5)
```

**Key Point**: Phase 1 creates STRUCTURE only (empty files with function signatures & docstrings).
             Actual implementation begins Phase 2.

#### 1.2 Data Structure Definition
Document in memory file: `photon_data_structures.md`
- Photon particle state struct (similar to neutron but without fission flag)
- Reaction data struct (cross-sections, distribution arrays)
- Material composition mapping

#### 1.3 Memory/Documentation Files Created
- `photon_data_structures.md` - Data layout details
- `photon_physics_reference.md` - Cross-section formulas and sources
- `integration_checklist.md` - System integration tasks

---

## 4. Physics & Implementation Details

### 4.1 Cross-Section Implementation

**Klein-Nishina (Compton)**
- Formula: Evans, "Technique of Gamma-Ray Spectroscopy"
- Validation: Compare to NIST XCOM database
- Expected accuracy: Within 1-2% of tabulated values

**Photoelectric Effect**
- Source: NIST XCOM tabulated data
- Implementation: Energetic lookup + shell selection
- Expected accuracy: Within 1% of NIST

**Pair Production**
- Threshold: 2.044 MeV (2 me c²)
- Above threshold: Bethe-Heitler or Tsai parameterization
- Validation: Compare to NIST XCOM

### 4.2 Interaction Kinematics

**Energy Conservation**: All scattering kernels must conserve energy
**Angle Constraints**: Scattering angles must be physical
**Secondary Particles**: Determine phase for electron/positron tracking

---

## 5. Documentation Strategy

### 5.1 Documentation Locations & Types

| Type | Location | Format | Purpose |
|------|----------|--------|---------|
| **Research Plan** | `photon-transport/` | Markdown | Overall strategy & phasing |
| **Memory/Reference** | `.claude/projects/c--Projects-MCDC/memory/photon_*.md` | Markdown | Quick-reference during development |
| **Physics Reference** | `memory/photon_physics_reference.md` | Markdown | Formulas, sources, validation data |
| **User Guide** | `photon-transport-code/docs/source/user/photon/` | RST | User-facing documentation |
| **API Reference** | `photon-transport-code/docs/source/pythonapi/` | Auto-generated + RST | API docs |
| **Code Comments** | In source files | Python docstrings | Implementation details |

### 5.2 Memory File Structure

Each interaction, update memory files:
- `photon_*.md` - Topic-specific details
- Link from `MEMORY.md` entry

Example memory files to create:
```
✓ ACCELERATED_TIMELINE.md          - 3-5 day timeline with Claude
✓ FILE_STRUCTURE_GUIDE.md          - 35 files organized by phase
✓ THREE_CRITICAL_FILES_TIMELINE.md - When each critical file is created/populated
✓ photon_data_structures.md        - Struct layouts, offsets
✓ photon_physics_reference.md      - Formulas, cross-sections
- photon_integration_notes.md      - System integration discoveries
- photon_validation_results.md     - Benchmark data
- photon_debugging_notes.md        - Issues & solutions
```

---

## 6. Validation & Reference Data

### 6.1 External Data Sources
1. **NIST XCOM Database** (https://www.nist.gov/pml/xcom)
   - Total, Compton, photoelectric, pair production cross-sections
   - Energy range: 1 keV - 100 GeV
   - Tissues, elements from 1-92

2. **ICRU Reports**
   - ICRU Report 90 (Photon cross-sections)
   - ICRU Report 49 (Stopping power)

3. **Geant4 Reference Data**
   - OpenDOCS physics library
   - Useful for validation & comparison

### 6.2 Validation Approach
**For each interaction type:**
1. **Formula validation**: Cross-check against reference (Evans, Knoll, etc.)
2. **Tabulated data**: Compare code output to NIST XCOM
3. **Integration checks**: Total cross-section = sum of components
4. **Kinematic checks**: Energy/momentum/angle conservation
5. **Benchmark**: Simple test problem with known solution

---

## 7. Risk Mitigation & Decision Points

### 7.1 Potential Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Cross-section accuracy** | High | Validate every formula against NIST; create validation tests |
| **Performance regression** | Medium | Profile Numba code; benchmark vs neutron |
| **Integration complexity** | Medium | Incremental integration testing; keep photon module isolated initially |
| **Lack of photon-specific data** | Medium | Use existing databases (NIST, Geant4); document sources |
| **GPU/Numba compatibility** | Low | Coordinate with Phase 1 structure review |

### 7.2 Decision Points

| Decision Point | Trigger | Options | Recommendation |
|---|---|---|---|
| **Include electrons in Phase 1?** | During Compton impl | A) Track electrons | B) Ignore electrons | **B** - Validate photon physics first |
| **Implement positron annihilation?** | During pair production | A) Annihilation model | B) Treat as regular particles | **B** - Photon validation first |
| **Multigroup vs native only?** | After Phase 2 | A) Add multigroup | B) Keep native only | **A if interest exists** - leverage neutron code |
| **Secondary particle tracking** | During Phase 3 | A) Phase 2 feature | B) Defer to Phase 2+ | **B** - scope containment |

---

## 8. Success Criteria & Deliverables

### 8.1 Phase-by-Phase Success Criteria

**Phase 1**: ✓ Structure created, data layouts defined, memory docs complete
**Phase 2**: ✓ Cross-sections match NIST within 1-2%, all formulas tested
**Phase 3**: ✓ Interaction kernels pass kinematics tests, examples run
**Phase 4**: ✓ Full system integration, all existing tests still pass
**Phase 5**: ✓ 95%+ line coverage, >20 regression tests, Sphinx docs built

### 8.2 Deliverables Checklist

```
Code:
  [ ] photon-transport-code/transport/physics/photon/ module (5 KLoC estimated)
  [ ] photon-transport-code/mcdc_set/ photon material classes (500 LoC)
  [ ] photon-transport-code/mcdc_get/ photon getters (auto-generated)

Tests:
  [ ] photon-transport-code/test/unit/photon/ (20+ tests)
  [ ] photon-transport-code/test/regression/photon/ (5+ benchmark tests)
  [ ] Example simulations (3 working examples)

Documentation:
  [ ] photon-transport-code/docs/source/user/photon/ (4 chapters)
  [ ] photon-transport-code/docs/source/pythonapi/photon* (auto-generated)
  [ ] PHOTON_TRANSPORT_PHYSICS_REFERENCE.md
  [ ] This research plan + updates

Infrastructure:
  [ ] GitHub issue
  [ ] Project board with phases
  [ ] CI/CD integration (Docker tests)
  [ ] Memory files (.claude/)
```

---

## 9. Timeline & Milestones

**See also**: [`ACCELERATED_TIMELINE.md`](photon-transport/ACCELERATED_TIMELINE.md) for Claude Code-assisted development (3-5 days)

### Standard Timeline (Manual Development)

| Phase | Duration | Milestones | Owner |
|-------|----------|-----------|-------|
| **1: Foundation** | Week 1-2 | Module structure, data layout | Lead dev |
| **2: Cross-sections** | Week 2-3 | NIST validation, formulas tested | Physics expert |
| **3: Interactions** | Week 3-4 | Kinematics working, examples run | Lead dev |
| **4: Integration** | Week 4-5 | Full system test, existing tests pass | Integration lead |
| **5: Documentation** | Week 5-6 | Sphinx built, 95%+ test coverage | Doc lead |
| **Maintenance** | Ongoing | Issue tracking, bug fixes, updates | Team |

### AI-Accelerated Timeline (Claude Code)

| Phase | Duration | Daily Deliverables |
|-------|----------|---|
| **1: Foundation** | 0.5 days | Directory structure + data definitions |
| **2: Cross-sections** | 1 day | All 4 cross-sections + NIST validation |
| **3: Interactions** | 1 day | Scattering kernels + kinematics tests |
| **4: Integration** | 1.5 days | System integration + 3 examples + 20+ tests |
| **5: Documentation** | 0.5-1 days | Sphinx docs + 95%+ coverage |
| **Total** | **3-5 days** | Full photon transport module |

**Contingency**: If complex, extend each phase by 1 week (manual) or 1-2 days (Claude).

---

## 10. References & Resources

### Physics References
- **Evans, R.D.** (1955). "The Atomic Nucleus" - Classic Klein-Nishina reference
- **Knoll, G.F.** (2010). "Radiation Detection and Measurement" - Standard text
- **ICRU Report 90** - Photon cross-sections (free online)
- **IAEA Reports** - Radiation physics in matter
- **NIST XCOM** - Database of photon cross-sections (https://www.nist.gov/pml/xcom)

### Code References
- **Existing neutron transport**: `mcdc/transport/physics/neutron/`
- **MCDC GitHub**: https://github.com/CEMeNT-PSAAP/MCDC
- **Geant4 Physics**: https://geant4.web.cern.ch/ (reference implementation)

### Tools & Standards
- **Sphinx documentation**: https://www.sphinx-doc.org/
- **Numba documentation**: https://numba.readthedocs.io/
- **pytest**: https://docs.pytest.org/
- **Black code style**: https://black.readthedocs.io/

---

## Appendix A: Quick Reference - Key Files to Modify

| File | Change | Phase |
|------|--------|-------|
| `mcdc/__init__.py` | Import photon module | 1 |
| `mcdc/transport/__init__.py` | Add photon physics | 1 |
| `photon-transport-code/mcdc_set/__init__.py` | Export photon classes | 1 |
| `photon-transport-code/mcdc_get/__init__.py` | Export photon getters | 1 |
| `mcdc/transport/main.py` or transport loop | Add photon handling | 4 |
| `photon-transport-code/docs/source/index.rst` | Link to photon docs | 5 |
| `photon-transport-code/test/` conftest.py | Add photon fixtures | 5 |
| `.github/workflows/` | Add photon regression tests | 4-5 |

---

**Document Version History:**
- v1.0 (2026-04-07): Initial comprehensive research plan + AI-accelerated timeline reference

