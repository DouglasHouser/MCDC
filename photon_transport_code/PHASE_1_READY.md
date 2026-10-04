# Phase 1 Ready Checklist

**Status**: ✅ All preparation complete - ready for Claude Code Phase 1
**Date**: April 7, 2026
**Location**: `photon-transport-code/`

---

## Pre-Phase 1 Verification

Run these to confirm everything is ready:

```bash
# Navigate to the repo
cd /c/Projects/MCDC/photon-transport-code

# Check directory structure
echo "=== Checking directories ==="
test -d transport/physics/photon && echo "✓ transport/physics/photon/"
test -d mcdc_set && echo "✓ mcdc_set/"
test -d mcdc_get && echo "✓ mcdc_get/"
test -d test/unit/photon && echo "✓ test/unit/photon/"
test -d test/regression/photon && echo "✓ test/regression/photon/"
test -d examples && echo "✓ examples/"
test -d docs/source && echo "✓ docs/source/"

# Check __init__.py files
echo "=== Checking __init__.py files ==="
test -f transport/physics/photon/__init__.py && echo "✓ photon/__init__.py"
test -f mcdc_set/__init__.py && echo "✓ mcdc_set/__init__.py"
test -f mcdc_get/__init__.py && echo "✓ mcdc_get/__init__.py"
test -f test/__init__.py && echo "✓ test/__init__.py"
test -f test/unit/photon/__init__.py && echo "✓ test/unit/photon/__init__.py"
test -f test/regression/photon/__init__.py && echo "✓ test/regression/photon/__init__.py"

# Check documentation
echo "=== Checking documentation ==="
test -f PATH_MAPPING.md && echo "✓ PATH_MAPPING.md (directory documentation)"
test -f README.md && echo "✓ README.md (quick start)"

echo "=== READY FOR PHASE 1 ==="
```

---

## Documentation Ready

**In photon-transport-code/**:
- ✅ `PATH_MAPPING.md` - Complete directory structure explained
- ✅ `README.md` - Quick start guide for Phase 1

**In photon-transport/**:
- ✅ `THREE_CRITICAL_FILES_TIMELINE.md` - When files created/populated
- ✅ `FILE_STRUCTURE_GUIDE.md` - File naming & naming conventions
- ✅ `VALIDATION_STRATEGY.md` - Phase 1 acceptance criteria
- ✅ `PHOTON_TRANSPORT_RESEARCH_PLAN.md` - Overall strategy
- ✅ `ACCELERATED_TIMELINE.md` - Daily targets
- ✅ `MCDC_FILE_ARCHITECTURE.md` - Integration guidance

**New: Contradiction Analysis**:
- ✅ `CONTRADICTION_ANALYSIS_&_FIXES.md` - Audit trail of fixes

---

## What Claude Code Will Create in Phase 1

**Skeleton Files** (6 files in `transport/physics/photon/`):
```
interface.py              @njit function signatures (no impl, just pass)
cross_sections.py         @njit function signatures (no impl, just pass)
distributions.py          @njit function signatures (no impl, just pass)
native.py                 @njit function signatures (no impl, just pass)
util.py                   Helper functions skeleton
__init__.py               Empty or simple exports
```

**User API** (1 file):
```
mcdc_set/photon_material.py    Material class definition
```

**Test Infrastructure** (2 files):
```
test/unit/photon/conftest.py         Pytest fixtures
test/unit/photon/__init__.py         Package marker
test/regression/photon/__init__.py   Package marker
```

**Memory Files** (3 files in `.claude/projects/c--Projects-MCDC/memory/`):
```
photon_data_structures.md      Struct definitions
photon_physics_reference.md    Physics formulas & references
integration_checklist.md       System integration tasks
```

---

## After Phase 1 Completion

**You should verify**:
1. Run import tests:
   ```bash
   python -c "import transport.physics.photon; print('✓')"
   ```

2. Run Phase 1 validation:
   ```bash
   pytest test/unit/photon/test_phase1_structure.py -v
   ```

3. Check Black formatting:
   ```bash
   black --check transport/physics/photon/
   ```

4. Review file contents:
   - [ ] interface.py has @njit decorated functions
   - [ ] cross_sections.py has @njit decorated functions
   - [ ] All functions have complete docstrings (Parameters/Returns)
   - [ ] All functions have pass statements (no implementation yet)

**Sign-off items**:
- [ ] All 6 core physics files created ✓
- [ ] All __init__.py files in place ✓
- [ ] Memory files created ✓
- [ ] Imports work ✓
- [ ] Tests pass ✓

**Then proceed to Phase 2**: Cross-sections implementation

---

## File Locations Summary

```
photon-transport-code/
  ├── Source code (Phases 1-5)
  ├── PATH_MAPPING.md (directory guide)
  └── README.md (quick start)

photon-transport/
  ├── PHOTON_TRANSPORT_RESEARCH_PLAN.md (strategy)
  ├── THREE_CRITICAL_FILES_TIMELINE.md (file creation phases)
  ├── FILE_STRUCTURE_GUIDE.md (file organization)
  ├── VALIDATION_STRATEGY.md (testing & validation)
  ├── ACCELERATED_TIMELINE.md (daily targets)
  ├── MCDC_FILE_ARCHITECTURE.md (MCDC integration)
  ├── CONTRADICTION_ANALYSIS_&_FIXES.md (audit trail)
  ├── STRATEGY_OVERVIEW.md (visual roadmap)
  ├── PHOTON_QUICKSTART.md (phase checklists)
  └── DOCUMENTATION_GUIDE.md (how to use docs)

.claude/projects/c--Projects-MCDC/memory/
  ├── MEMORY.md (architecture overview)
  ├── ACCELERATED_TIMELINE.md (referenced copy)
  └── (memory files will be created by Claude Phase 1)
```

---

## Ready Status

✅ **Directory structure created**
✅ **All __init__.py files in place**
✅ **Documentation complete**
✅ **PATH_MAPPING.md explains everything**
✅ **README.md provides quick start**
✅ **Contradictions identified & fixed**
✅ **Ready for Phase 1 generation**

---

**Next Step**: Provide Claude Code with the prompt from README.md to begin Phase 1

