# Photon Transport Development: Strategy Overview

## 📋 The Plan at a Glance

### 5-Phase Development Roadmap

```
Phase 1: Foundation     Phase 2: Physics        Phase 3: Reactions     Phase 4: Integration   Phase 5: Finish
(Wk 1-2)              (Wk 2-3)                (Wk 3-4)               (Wk 4-5)               (Wk 5-6)

├─ Structure          ├─ Compton σ(E)        ├─ Klein-Nishina       ├─ Transport loop      ├─ Sphinx docs
├─ Data layout        ├─ Photoelectric σ(E)  │  kernel              ├─ Tally system        ├─ 95%+ coverage
├─ Memory files       ├─ Pair production σ(E)├─ Pair production     ├─ Geometry/mesh test  ├─ Final testing
└─ GitHub tracking    └─ Total σ(E)          │  kinematics          ├─ Example sims        └─ Validation
                                             └─ Photoelectric       └─ Regression tests
                                                effects
```

### Key Deliverables

| Component | Deliverable | Lines | Tests | Docs |
|-----------|-------------|-------|-------|------|
| **Physics module** | `mcdc/transport/physics/photon/` | ~5 KLoC | 20+ | 4 chapters |
| **Material setup** | `mcdc/mcdc_set/photon_*.py` | ~500 LoC | 5+ | API auto-gen |
| **Interactions** | Cross-sections & kernels | ~2 KLoC | 10+ | Physics ref |
| **Examples** | 3 working simulations | ~500 LoC | - | Walkthroughs |

---

## 🎯 Why This Approach?

### Benefits of This Strategy

| Strategy | Benefit | How |
|----------|---------|-----|
| **Modular design** | Keeps neutron code clean | Separate `photon/` directory |
| **Incremental testing** | Early error detection | Unit tests in Phase 2, integration Phase 4 |
| **Documentation-first** | Easier maintenance | Memory files + Sphinx docs created as code develops |
| **Reference validation** | High confidence | Every formula validated against NIST |
| **Clear phases** | Trackable progress | 5 phases with specific deliverables |
| **Integration last** | Risk mitigation | Validate photon physics before touching core transport |

---

## 📊 Tracking & Documentation

### Three-Tier Documentation System

```
TIER 1: RESEARCH PLAN
└─ PHOTON_TRANSPORT_RESEARCH_PLAN.md
   └─ 11 sections: architecture, phases, validation, risks, timeline
   └─ Reference during planning & decision-making

TIER 2: QUICK REFERENCE (Memory Files)
├─ PHOTON_QUICKSTART.md (checklists, status)
├─ photon_physics_reference.md (formulas, sources)
├─ photon_data_structures.md (struct definitions)
├─ photon_integration_notes.md (integration discoveries)
└─ photon_validation_results.md (benchmark data)

TIER 3: USER-FACING DOCS
├─ docs/source/user/photon/ (Sphinx RST)
└─ Docstrings in code (@njit functions)
```

### Progress Tracking Methods

**Option A: GitHub Issues + Project Board** (Recommended)
- Issue: Link to research plan
- Project board: 5 phase milestones
- Subtasks: Link memory files

**Option B: Spreadsheet**
- Columns: Task ID, Phase, Status, Owner, Notes
- Rows: Each checklist item from QUICKSTART

**Option C: Memory File Updates**
- Update `PHOTON_QUICKSTART.md` checkboxes
- Add implementation notes to memory files
- Keep running log of decisions

---

## 🔍 Key Architectural Decisions

| Decision | Rationale | Implication |
|----------|-----------|-------------|
| **Separate physics module** | Isolates photon from neutron code | New `mcdc/transport/physics/photon/` |
| **Parallel data structure** | Matches existing patterns | Mirror neutron material/reaction design |
| **NIST cross-section validation** | Ensures accuracy | Add XCOM comparison for every formula |
| **Compton first** | Dominant process at diagnostic energies | Priorities: Compton > Photoelectric > Pair production |
| **Ignore secondary electrons (Phase 1)** | Scope containment | Photon disappears on interaction; electrons in Phase 2+ |
| **Use existing geometry** | No changes needed | Photons work with existing surfaces/mesh |
| **Phase-based integration** | Risk mitigation | Validate photon physics before full system integration |

---

## 🚀 Getting Started (When Ready)

### Immediate Next Steps
1. **Create directory structure** (Phase 1.1a)
2. **Create memory files** (Phase 1.1b)
3. **Define data structures** (Phase 1.2)
4. **Open GitHub issue** with link to research plan (Phase 1.3)
5. **Begin Phase 2**: Implement Klein-Nishina cross-section

### Tools You'll Need
- **Language**: Python 3.10+
- **Performance**: Numba (@njit decorator)
- **Parallelization**: MPI (already in MCDC)
- **Testing**: pytest
- **Docs**: Sphinx
- **Data**: NIST XCOM database (online or local CSV)

---

## 📚 Physics at a Glance

### Core Processes

**1. Compton Scattering** (Klein-Nishina)
- Formula: Differential cross-section dσ/dΩ
- Energy range: All energies (most important ~100 keV - 10 MeV)
- Sampling: Acceptance-rejection or analytical inversion
- Test: Compare histogram to Klein-Nishina curve

**2. Photoelectric Absorption**
- Process: Photon absorbed → K-shell ionization
- Energy range: Dominant <100 keV
- Data source: NIST XCOM (tabulated)
- Test: Cross-section vs NIST within 1%

**3. Pair Production**
- Process: γ → e+e- (3-body interaction with nucleus)
- Threshold: 2 MeV
- Energy range: Dominant >5 MeV
- Test: Cross-section vs NIST, energy conservation

**4. Rayleigh Scattering** (Lower priority)
- Process: Coherent elastic scattering
- Approximation: Thomson or dipole form
- Energy range: <100 keV (low cross-section)

---

## ❓ FAQ: Planning Phase

**Q: How long will this take?**
A: 5-6 weeks for core implementation. Maintenance ongoing. Can extend phases if needed.

**Q: Do I need to modify existing neutron code?**
A: Minimal impact initially. Transport loop branching in Phase 4, but neutron code remains unchanged.

**Q: What if I find integration issues later?**
A: Documented in "Decision Points" section of research plan. Triggers for revisiting scoping decisions (e.g., secondary electrons).

**Q: Where do I find cross-section formulas?**
A: `photon_physics_reference.md` (create during Phase 2) + research plan Appendix A references.

**Q: Can I parallelize (GPU/MPI)?**
A: Yes! Use existing Numba/MPI infrastructure. Photon code follows same @njit patterns as neutron.

**Q: What's the success metric?**
A: Simple photon transport test reproduces known physics within 2-5% of reference.

---

## 📞 When to Update This Documentation

| Event | Update | Where |
|-------|--------|-------|
| **New discovery** | Add to relevant memory file | `photon_*.md` |
| **Phase complete** | Mark checklist ✓ | `PHOTON_QUICKSTART.md` |
| **Physics formula added** | Document + reference | `photon_physics_reference.md` |
| **Integration issue** | Decision record | `photon_integration_notes.md` |
| **Validation benchmark** | Add to results | `photon_validation_results.md` |
| **Major decision** | Document rationale | All affected files |

---

## 📖 Full Documentation Map

```
Your Project Root: c:\Projects\MCDC\

Research & Planning:
├── PHOTON_TRANSPORT_RESEARCH_PLAN.md ← START HERE (11 sections, comprehensive)
├── .claude/projects/MCDC/memory/
│   ├── MEMORY.md (this project overview)
│   ├── PHOTON_QUICKSTART.md (checklists + quick ref)
│   ├── photon_physics_reference.md (TO CREATE: formulas)
│   ├── photon_data_structures.md (TO CREATE: struct layouts)
│   ├── photon_integration_notes.md (TO CREATE: integration discoveries)
│   └── photon_validation_results.md (TO CREATE: benchmark data)

Code Development:
├── mcdc/transport/physics/photon/ (NEW MODULE)
├── mcdc/mcdc_set/ (add photon_material.py, photon_reaction.py)
├── mcdc/mcdc_get/ (add photon getters)
└── test/
    ├── unit/photon/ (NEW: unit tests)
    └── regression/photon/ (NEW: benchmark tests)

Documentation (Sphinx):
└── docs/source/
    ├── user/photon/ (NEW: 4 chapters)
    └── pythonapi/ (add photon_*.rst)

GitHub:
└── Issues & Project board (linked to research plan)
```

---

## 🎓 How to Read the Research Plan

1. **First time?** → Read Section 1 (Summary) + Section 3 (Phases)
2. **Architecture questions?** → Sections 2.1-2.3
3. **Technical details?** → Sections 4-6 (physics, integration, validation)
4. **Stuck on task?** → Section 5 (conventions), Section 8 (risks/decisions)
5. **Reference?** → Appendices, Section 11 (physics references)

---

## ✅ Validation Checklist

Before starting development, confirm:
- [ ] You've read Section 1-3 of PHOTON_TRANSPORT_RESEARCH_PLAN.md
- [ ] You understand the 5 phases and their goals
- [ ] You have access to NIST XCOM data
- [ ] MCDC is already set up and working on your machine
- [ ] You're familiar with the neutron transport code patterns
- [ ] You have GitHub issue template ready
- [ ] You've created memory file directory structure

---

**Last Updated**: 2026-04-07
**Next Review**: After Phase 1 completion
**Owner**: [Your name]

This is a living document—update as you learn more!

