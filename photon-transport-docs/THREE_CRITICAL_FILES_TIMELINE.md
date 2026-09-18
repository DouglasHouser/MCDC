# The 3 Critical Files: Timeline & Implementation

**Question**: Are the three critical files (interface.py, cross_sections.py, distributions.py) created in Phase 1?

**Answer**: **Partially YES, with important caveats:**

---

## Simple Summary

```
PHASE 1 (Foundation - Day 0.5)
  └─ CREATE SKELETON FILES (empty stubs with docstrings)
     ├─ interface.py              [Skeleton with function signatures]
     ├─ cross_sections.py         [Skeleton - no implementation]
     └─ distributions.py          [Skeleton - no implementation]

PHASE 2 (Cross-sections - Day 1)
  └─ POPULATE cross_sections.py (Klein-Nishina, PE, pair prod formulas)

PHASE 3 (Interactions - Day 2)
  └─ POPULATE distributions.py (Compton, pair, PE kernels)

PHASE 4 (Integration - Day 2.5-3.5)
  └─ POPULATE interface.py (glue it all together, use filled modules)
```

---

## Detailed Timeline for the 3 Critical Files

### interface.py

| Phase | What Happens | Lines of Code |
|-------|---|---|
| **1** | Create skeleton with function signatures: | ~50 |
| | - `compton_scatter()` |  |
| | - `pair_production()` |  |
| | - `photoelectric_absorption()` |  |
| **2** | Import cross_sections module | +10 lines |
| **3** | Import distributions module | +10 lines |
| **4** | Fully implemented (calls cross-sections + distributions) | ~200 total |

**Status after Phase 1**: 50 lines (skeleton)
**Final**: 200 lines (Phase 4)

---

### cross_sections.py

| Phase | What Happens | Lines of Code |
|-------|---|---|
| **1** | Create skeleton with function signatures: | ~100 |
| | - `klein_nishina_total(E)` |  |
| | - `photoelectric_total(element, E)` |  |
| | - `pair_production_total(element, E)` |  |
| | - `total_cross_section(element, E)` |  |
| **2** | **FULLY IMPLEMENTED** (all formulas, NIST lookup, validation) | ~700 |
| **3** | (No changes) |  |
| **4** | (No changes) |  |
| **5** | (No changes) |  |

**Status after Phase 1**: 100 lines (skeleton)
**Final after Phase 2**: 700 lines (complete)

---

### distributions.py

| Phase | What Happens | Lines of Code |
|-------|---|---|
| **1** | Create skeleton with function signatures: | ~80 |
| | - `sample_klein_nishina(E_in)` |  |
| | - `sample_pair_production(E_gamma)` |  |
| | - `sample_photoelectric_shell(E)` |  |
| **2** | (No changes) |  |
| **3** | **FULLY IMPLEMENTED** (all scattering kernels, kinematics) | ~600 |
| **4** | (No changes) |  |
| **5** | (No changes) |  |

**Status after Phase 1**: 80 lines (skeleton)
**Final after Phase 3**: 600 lines (complete)

---

## What Phase 1 Actually Creates

### Example: interface.py skeleton created in Phase 1

```python
# photon-transport-code/transport/physics/photon/interface.py
# Created in Phase 1, populated in Phase 2-4

@njit
def compton_scatter(E_photon, xi1, xi2):
    """
    Sample Compton scattering event.

    Parameters
    ----------
    E_photon : float
        Incident photon energy [MeV]
    xi1, xi2 : float
        Random numbers in [0, 1)

    Returns
    -------
    E_out : float
        Outgoing photon energy [MeV]
    theta : float
        Scattering angle [radians]
    """
    # FILLED IN PHASE 2-3 (calls distributions.sample_klein_nishina)
    pass


@njit
def pair_production(E_photon, xi1, xi2):
    """
    Sample pair production event.

    ... (docstring)
    """
    # FILLED IN PHASE 2-3 (calls distributions.sample_pair_production)
    pass


@njit
def photoelectric_absorption(E_photon):
    """
    Sample photoelectric absorption.

    ... (docstring)
    """
    # FILLED IN PHASE 2-3 (calls distributions.sample_photoelectric_shell)
    pass
```

**After Phase 1**: Just the skeleton above
**After Phase 2**: Still mostly skeleton (cross_sections.py exists to import from)
**After Phase 3**: Fully implemented (distributions.py exists to import from)
**After Phase 4**: Complete with all integration tested

---

## How This Affects Your Workflow with Claude Code

### What this means:

✅ **Phase 1 (Day 0.5)**: Claude creates all 6 skeleton files
→ You review structure/docstrings/function signatures only

✅ **Phase 2 (Day 1)**: Claude populates cross_sections.py
→ You review physics formulas, NIST validation plots

✅ **Phase 3 (Day 2)**: Claude populates distributions.py
→ You review kinematics, energy conservation plots

✅ **Phase 4 (Day 3)**: Claude populates interface.py + integration
→ You run examples, verify system integration

---

## Why This Phasing?

```
Phase 1 can't fully populate the files because:
  ├─ Phase 2 code (cross_sections) doesn't exist yet
  ├─ Phase 3 code (distributions) doesn't exist yet
  └─ interface.py needs to import from them

So the logical order is:
  1. Create skeletons (Phase 1)
  2. Fill lowest layer (cross_sections, Phase 2)
  3. Fill middle layer (distributions, Phase 3)
  4. Fill top layer (interface, Phase 4)
```

---

## Bottom Line Answer

**Q**: Are the 3 critical files created in Phase 1?

**A**:
- ✅ YES - skeleton files are created in Phase 1
- ❌ NO - they're not fully implemented in Phase 1
- They're populated progressively: Phase 2 (cross-sections), Phase 3 (distributions), Phase 4 (interface + integration)

The research plan shows them in Phase 1's repository structure, but means as SKELETON files that serve as placeholders for the actual implementation that comes in Phases 2-4.

