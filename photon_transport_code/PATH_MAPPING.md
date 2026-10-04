# Photon Transport Code: Directory Structure & Path Mapping

**Purpose**: Standalone photon transport module with MCDC-compatible structure
**Status**: Ready for Phase 1 implementation
**Date**: April 7, 2026

---

## Directory Structure

```
photon-transport-code/
├── __init__.py                          # Root package
│
├── transport/                           # Transport physics & algorithms
│   ├── __init__.py
│   ├── physics/
│   │   ├── __init__.py
│   │   └── photon/                      # ⭐ PHASE 1: Create here
│   │       ├── __init__.py              # Public API exports
│   │       ├── interface.py             # Entry point (@njit functions)
│   │       ├── cross_sections.py        # σ_total, σ_compton, σ_pe, σ_pair
│   │       ├── distributions.py         # Scattering kernels & kinematics
│   │       ├── native.py                # NIST data loader
│   │       └── util.py                  # Helper functions
│   │
│   ├── geometry/                        # (Reference only, don't modify)
│   ├── mesh/                            # (Reference only, don't modify)
│   └── tally/                           # (Reference only, don't modify)
│
├── mcdc_set/                            # User API for setup
│   ├── __init__.py
│   └── photon_material.py               # Photon material definition
│
├── mcdc_get/                            # Getters (auto-generated)
│   ├── __init__.py
│   └── photon_material.py               # Auto-generated getters
│
├── code_factory/                        # (Reference only, don't modify)
├── object_/                             # (Reference only, don't modify)
│
├── test/                                # Testing
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   └── photon/
│   │       ├── __init__.py
│   │       ├── conftest.py              # Pytest fixtures
│   │       ├── test_phase1_structure.py # Phase 1 validation
│   │       ├── test_klein_nishina.py    # Phase 2 cross-sections
│   │       ├── test_photoelectric.py    # Phase 2 cross-sections
│   │       ├── test_pair_production.py  # Phase 2 cross-sections
│   │       ├── test_total_xsec.py       # Phase 2 composition
│   │       ├── test_compton_kernel.py   # Phase 3 kinematics
│   │       ├── test_pair_production_kernel.py  # Phase 3 kinematics
│   │       ├── test_photoelectric_kernel.py    # Phase 3 kinematics
│   │       ├── test_integration_transport.py   # Phase 4 integration
│   │       └── test_docstrings.py       # Phase 5 quality
│   │
│   └── regression/
│       ├── __init__.py
│       └── photon/
│           ├── __init__.py
│           ├── conftest.py              # Fixtures
│           ├── test_absorption_slab.py  # Phase 4: Beer-Lambert
│           ├── test_compton_spectrum.py # Phase 4: Klein-Nishina spectrum
│           ├── test_pair_production_threshold.py  # Phase 4: Threshold
│           └── test_performance_benchmark.py      # Phase 5: Speed
│
├── examples/                            # Working examples
│   ├── photon_transport_absorption/
│   │   ├── input.py                     # Beam through slab
│   │   └── README.md
│   │
│   ├── photon_transport_compton/
│   │   ├── input.py                     # Isotropic scattering
│   │   └── README.md
│   │
│   └── photon_transport_pair_production/
│       ├── input.py                     # High-energy pair production
│       └── README.md
│
└── docs/                                # Documentation
    └── source/
        ├── user/
        │   └── photon/
        │       ├── photon_transport_01_overview.rst
        │       ├── photon_transport_02_physics.rst
        │       ├── photon_transport_03_usage.rst
        │       └── photon_transport_04_validation.rst
        │
        └── pythonapi/
            ├── photon_material.rst
            └── photon_reactions.rst
```

---

## File Count by Phase

| Phase | Files | Details |
|-------|-------|---------|
| **1: Foundation** | 9 | Structures + skeletons + memory files |
| **2: Cross-sections** | 14 | +5 unit tests + physics populations |
| **3: Interactions** | 17 | +3 kernel tests + distributions population |
| **4: Integration** | 24 | +8 files: 1 test + 4 regression tests + 3 examples |
| **5: Documentation** | 35 | +11 files: 2 tests + 2 regression + 6 docs + 1 auto-gen getter |

**Total final: 35 files**

---

## Component Organization

### 1. Core Physics Module
**Location**: `transport/physics/photon/`
**Files**: 6 (interface.py, cross_sections.py, distributions.py, native.py, util.py, __init__.py)
**Responsibility**: All photon interaction physics @njit decorated

### 2. User API
**Location**: `mcdc_set/` + `mcdc_get/`
**Files**: 2 (photon_material.py in each)
**Responsibility**: User-facing material definitions + auto-generated getters

### 3. Unit Tests
**Location**: `test/unit/photon/`
**Files**: 11 (conftest.py + 10 test_*.py files)
**Responsibility**: Component-level testing (cross-sections, kernels, integration)

### 4. Regression Tests
**Location**: `test/regression/photon/`
**Files**: 5 (conftest.py + 4 test_*.py files)
**Responsibility**: System-level benchmarks (Beer-Lambert, Klein-Nishina, thresholds, performance)

### 5. Examples
**Location**: `examples/`
**Files**: 3 (one subdirectory per example)
**Responsibility**: Working simulations demonstrating photon transport

### 6. Documentation
**Location**: `docs/source/`
**Files**: 6 (4 user guide RST + 2 API reference RST)
**Responsibility**: User-facing documentation + API reference

---

## How This Maps to MCDC

This structure **mirrors MCDC exactly**:

```
MCDC Structure:
  mcdc/transport/physics/neutron/ ──> Photon equivalent:
  mcdc/mcdc_set/ ──────────────────> Photon equivalent:
  mcdc/mcdc_get/ ──────────────────> Photon equivalent:
  test/unit/neutron/ ──────────────> Photon equivalent:
  test/regression/ ────────────────> Photon equivalent:
  examples/ ───────────────────────> Photon equivalent:
  docs/source/ ────────────────────> Photon equivalent:
```

**Key insight**: This standalone structure can be:
1. Used independently for development & testing
2. Integrated into MCDC later by copying transport/physics/photon/ into mcdc/transport/physics/
3. Kept as reference implementation

---

## Phase 1 Creation (When Claude Starts)

Claude will create these files in Phase 1:

```
transport/physics/photon/
├── __init__.py           ← Skeleton
├── interface.py          ← Skeleton (function signatures + docstrings)
├── cross_sections.py     ← Skeleton (function signatures + docstrings)
├── distributions.py      ← Skeleton (function signatures + docstrings)
├── native.py             ← Skeleton (function signatures + docstrings)
└── util.py               ← Skeleton (function signatures + docstrings)

mcdc_set/
├── __init__.py
└── photon_material.py    ← Skeleton

test/unit/photon/
├── __init__.py
└── conftest.py           ← Fixtures for testing

test/regression/photon/
├── __init__.py
└── conftest.py           ← Reference data fixtures
```

---

## File References for Claude Code

When Claude Code runs, it should:

1. **Read** (reference patterns):
   - `mcdc/transport/physics/neutron/` - for physics module pattern
   - `mcdc/mcdc_set/material.py` - for user API pattern
   - `mcdc/mcdc_get/` - for getter pattern

2. **Write** (create in this repo):
   - All files listed under "Phase 1 Creation" above
   - Follow structure exactly as shown

3. **Validate against**:
   - FILE_STRUCTURE_GUIDE.md - file naming & organization
   - VALIDATION_STRATEGY.md - phase-specific acceptance criteria
   - THREE_CRITICAL_FILES_TIMELINE.md - when each file gets populated

---

## Using This Structure

### For Development
```bash
cd photon-transport-code/
# All work happens here
# Test: pytest test/unit/photon/
# Examples: python examples/photon_transport_absorption/input.py
```

### For Integration into MCDC (Later)
```bash
# Copy photon physics module
cp -r photon-transport-code/transport/physics/photon/ \
      mcdc/transport/physics/photon/

# Copy user API
cp photon-transport-code/mcdc_set/photon_material.py \
   mcdc/mcdc_set/

# Copy tests (if needed)
cp -r photon-transport-code/test/unit/photon/ \
      mcdc/test/unit/
```

---

## Ready for Phase 1 ✓

This structure is now ready for Claude Code to generate Phase 1 code.

**All directories exist**: ✓
**All __init__.py files created**: ✓
**Path mapping documented**: ✓
**Ready to implement**: ✓

