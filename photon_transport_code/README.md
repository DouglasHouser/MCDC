# Photon Transport Code - Ready for Development

**Status**: ✅ Directory structure created and ready for Phase 1 implementation
**Created**: April 7, 2026
**Location**: `photon-transport-code/`

---

## Quick Start for Claude Code

When implementing Phase 1, create files in this structure:

```
transport/physics/photon/          ← All core physics files here
├── __init__.py
├── interface.py                   ← Entry point
├── cross_sections.py              ← Cross-section formulas
├── distributions.py               ← Scattering kernels
├── native.py                      ← Data loading
└── util.py                        ← Helpers

mcdc_set/photon_material.py        ← User API

test/unit/photon/                  ← Unit tests
test/regression/photon/            ← Regression tests

examples/photon_transport_*/       ← Working examples

docs/source/user/photon/           ← Documentation
```

---

## Key Documents to Reference

**READ FIRST**:
1. `../photon-transport/THREE_CRITICAL_FILES_TIMELINE.md` - When files are created/populated
2. `../photon-transport/FILE_STRUCTURE_GUIDE.md` - File naming conventions
3. `PATH_MAPPING.md` (this directory) - This exact folder structure

**For Validation**:
4. `../photon-transport/VALIDATION_STRATEGY.md` - Phase 1 acceptance criteria

**For Architecture**:
5. `../photon-transport/ACCELERATED_TIMELINE.md` - Daily targets
6. `../photon-transport/MCDC_FILE_ARCHITECTURE.md` - How to integrate

---

## Total Files to Create: 35

- **Core physics**: 6 files (transport/physics/photon/)
- **User API**: 2 files (mcdc_set/ + mcdc_get/)
- **Unit tests**: 11 files (test/unit/photon/)
- **Regression tests**: 5 files (test/regression/photon/)
- **Examples**: 3 files (examples/)
- **Documentation**: 6 files (docs/)
- **Auto-generated**: 1 file (mcdc_get/photon_material.py in Phase 5)

**Total: 35 files, ~8,600 lines of code**

---

## Phases Overview

| Phase | Days | Focus | Files |
|-------|------|-------|-------|
| **1** | 0.5 | Foundation + skeletons | 9 |
| **2** | 1 | Cross-sections + NIST validation | 14 |
| **3** | 1 | Interaction kernels + kinematics | 17 |
| **4** | 1.5 | System integration + examples | 24 |
| **5** | 0.5-1 | Documentation + polish | 35 |

---

## Phase 1: What Gets Created

**Skeleton Files** (empty functions with docstrings):
```
transport/physics/photon/
├── interface.py           ~50 LOC (function signatures)
├── cross_sections.py      ~100 LOC (function signatures)
├── distributions.py       ~80 LOC (function signatures)
├── native.py              ~50 LOC (function signatures)
└── util.py                ~30 LOC (helpers skeleton)

mcdc_set/photon_material.py       ~50 LOC

test/unit/photon/conftest.py      ~30 LOC (fixtures)
```

**Expected After Phase 1**:
- ✅ All directories exist
- ✅ All skeleton files created with proper @njit decorators
- ✅ All function signatures present
- ✅ All docstrings complete (Parameters/Returns)
- ✅ No implementation yet (functions just `pass`)
- ✅ All imports work without error

---

## Validation Checklist (After Phase 1)

```bash
# Directory check
ls -la transport/physics/photon/        # Should show 6 files
ls -la test/unit/photon/                # Should show conftest.py

# Import check
python -c "import transport.physics.photon; print('✓')"

# File check
test -f transport/physics/photon/interface.py && echo "✓ interface.py"
test -f transport/physics/photon/cross_sections.py && echo "✓ cross_sections.py"
test -f transport/physics/photon/distributions.py && echo "✓ distributions.py"

# Pytest check
pytest test/unit/photon/test_phase1_structure.py -v  # Should pass
```

---

## Integration Later

To integrate this into MCDC after Phase 5:

```bash
# Copy photon physics into MCDC
cp -r transport/physics/photon/ ../mcdc/transport/physics/

# Copy user API
cp mcdc_set/photon_material.py ../mcdc/mcdc_set/

# Then modify mcdc/transport/simulation.py to branch on particle type
```

---

## Notes

- This is a **standalone development environment**
- All files created here should mirror MCDC structure for easy integration
- Phase 1 only creates skeletons (no implementation)
- Phase 2-5 progressively populate the files
- No modifications needed to MCDC project during Phases 1-4
- Integration into MCDC can happen after Phase 5 if desired

---

