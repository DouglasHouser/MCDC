# Photon Transport Development: Quick Start

**For Claude Code-assisted timelines (3-5 days)**: See `ACCELERATED_TIMELINE.md`
**For manual development timelines (5-6 weeks)**: Use checklists below
**For detailed planning**: See `PHOTON_TRANSPORT_RESEARCH_PLAN.md`

## Quick Links
- **Research Plan**: `PHOTON_TRANSPORT_RESEARCH_PLAN.md`
- **Physics Formulas**: (create `memory/photon_physics_reference.md`)
- **Data Structures**: (create `memory/photon_data_structures.md`)
- **Integration**: (create `memory/photon_integration_notes.md`)

## Development Checklist

### Phase 1: Foundation (Manual: Weeks 1-2 | Claude: 0.5 days) [0/8]
- [ ] **1.1a** Create directory structure
  - [ ] Create `photon-transport-code/transport/physics/photon/`
  - [ ] Add `__init__.py`, `interface.py`, `native.py`, `distributions.py`, `cross_sections.py`, `util.py`
  - [ ] Create test directories
  - [ ] Create docs skeleton

- [ ] **1.1b** Create memory files
  - [ ] `photon_data_structures.md` - Struct definitions
  - [ ] `photon_physics_reference.md` - Formulas & sources
  - [ ] `photon_integration_checklist.md` - System tasks

- [ ] **1.2** Data structure definition
  - [ ] Define photon particle state struct
  - [ ] Define reaction data struct
  - [ ] Document offsets and alignment

- [ ] **1.3** Setup GitHub infrastructure
  - [ ] Create issue "Photon Transport Development"
  - [ ] Create project board with phases
  - [ ] Link research plan in issue

### Phase 2: Cross-Sections (Manual: Weeks 2-3 | Claude: 1 day) [0/4]
- [ ] Klein-Nishina cross-section (Compton)
  - [ ] Implement formula
  - [ ] Validate vs NIST
  - [ ] Create unit test
  - [ ] Add to reference data

- [ ] Photoelectric cross-section
  - [ ] Data loader (NIST CSV)
  - [ ] Validate vs NIST
  - [ ] Create unit test

- [ ] Pair production cross-section
  - [ ] Implement threshold (2 MeV)
  - [ ] Validate vs NIST
  - [ ] Create unit test

- [ ] Total cross-section composition
  - [ ] Implement sum logic
  - [ ] Validate against components
  - [ ] Add caching if needed

### Phase 3: Interactions (Manual: Weeks 3-4 | Claude: 1 day) [0/3]
- [ ] Compton scattering kernel
  - [ ] Implement Klein-Nishina sampling
  - [ ] Test kinematics (energy/angle conservation)
  - [ ] Create distribution plots for validation

- [ ] Pair production kinematics
  - [ ] Implement electron/positron distribution
  - [ ] Test energy conservation
  - [ ] Validation plots

- [ ] Photoelectric absorption
  - [ ] Shell selection model
  - [ ] Energy deposition logic
  - [ ] Test energy conservation

### Phase 4: Integration (Manual: Weeks 4-5 | Claude: 1.5 days) [0/5]
- [ ] Transport loop integration
  - [ ] Modify main transport loop for photons
  - [ ] Add photon/neutron branching
  - [ ] Test existing neutron tests still pass

- [ ] Tally system compatibility
  - [ ] Verify tallies work with photons
  - [ ] Add photon-specific tallies if needed
  - [ ] Test scoring

- [ ] Geometry/mesh system
  - [ ] Test photon in various geometries
  - [ ] Verify intersection logic works
  - [ ] Add regression tests

- [ ] Example simulations
  - [ ] Basic absorption example
  - [ ] Compton scattering example
  - [ ] Pair production example

- [ ] Test suite completeness
  - [ ] Unit tests (11 total)
  - [ ] Regression tests (5 total)
  - [ ] Coverage >95%

### Phase 5: Documentation (Manual: Weeks 5-6 | Claude: 0.5-1 days) [0/4]
- [ ] Sphinx documentation
  - [ ] Overview chapter
  - [ ] Physics reference chapter
  - [ ] Usage guide chapter
  - [ ] Validation chapter

- [ ] API documentation
  - [ ] Photon material class
  - [ ] Reaction classes
  - [ ] Auto-generated from docstrings

- [ ] Memory/reference files
  - [ ] Update all memory files
  - [ ] Add implementation notes
  - [ ] Document lessons learned

- [ ] Final review
  - [ ] All tests passing
  - [ ] Coverage report
  - [ ] Code style (Black)
  - [ ] Sphinx builds cleanly

---

## Key Implementation Questions

**Address during development:**
1. [ ] How does photon particle state differ from neutron?
2. [ ] Should secondary electrons be tracked immediately?
3. [ ] What's the positron annihilation model (if any)?
4. [ ] Are existing tallies compatible with photons?
5. [ ] Data format: separate photon files or integrate with neutron?

## File Organization

```
.claude/projects/MCDC/memory/
├── MEMORY.md                          # This file + arch overview
├── photon_data_structures.md          # Struct definitions
├── photon_physics_reference.md        # Formulas & sources
├── photon_integration_notes.md        # Integration discoveries
├── photon_validation_results.md       # Benchmark data
└── photon_debugging_notes.md          # Issues & solutions
```

## Current Status

**Phase**: Foundation (1/5)
**Completion**: 0%
**Last Updated**: 2026-04-07
**Owner**: [Your name]

---

## How to Use This Document

1. **Start development**: Copy task checklists to GitHub issues
2. **During development**: Update memory files with discoveries
3. **After each phase**: Mark tasks complete, update status
4. **Cross-reference**: Link memory files from PHOTON_TRANSPORT_RESEARCH_PLAN.md

---

