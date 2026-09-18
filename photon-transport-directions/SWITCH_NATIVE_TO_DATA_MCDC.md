# Switch Photon Cross Sections from native.py to data/mcdc HDF5 Files

## Prerequisites

⚠️ **IMPORTANT:** Before proceeding with this document, you MUST complete the reformatting step:

1. **First:** Follow [FORMAT_PHOTON_DATA_MCDC.md](FORMAT_PHOTON_DATA_MCDC.md)
   - This reformats all HDF5 files in `data/mcdc/` to match the hierarchical structure
   - Estimated time: 3-4 hours
   - Creates `data/mcdc.backup/` for safety
   
2. **Then:** Proceed with this document to update code to use reformatted data

**Dependency Chain:**
```
FORMAT_PHOTON_DATA_MCDC.md (Reformat data)
    ↓
SWITCH_NATIVE_TO_DATA_MCDC.md (Update code) ← YOU ARE HERE
    ↓
UPDATE_DOCUMENTATION.md (Update docs)
```

If you haven't run the formatting document yet, please do so first.

## Overview

This document provides instructions for migrating all photon cross-section lookups from the hardcoded tabulated data in `photon_transport_code/transport/physics/photon/native.py` to the reformatted HDF5 data files stored in `data/mcdc/`.

**Prerequisites:** Before proceeding with this document, ensure the photon data has been reformatted according to [FORMAT_PHOTON_DATA_MCDC.md](FORMAT_PHOTON_DATA_MCDC.md).

The current implementation uses in-code cross-section tables in `native.py`. The goal is to replace these with direct HDF5 file access from the `data/mcdc/` directory, which now contains reformatted elemental cross-section data for all supported elements (Z=1..92) in a hierarchical structure matching the neutron library format.

## Current Architecture

**Source of truth:** `photon_transport_code/transport/physics/photon/native.py`
- Contains hardcoded NIST XCOM reference tables
- Provides functions:
  - `get_element_data(Z)` - returns energy grid, compton, photoelectric, pair production cross-sections
  - `get_water_data()` - returns composition-weighted water cross-sections
  - `build_element_buffer(Z)` - builds flat data arrays for numba-compiled functions
  - `interpolate_xs(E, energy_grid_offset, xs_offset, N_points, data)` - performs log-log interpolation
  - `find_energy_bin(E, energy_grid_offset, N_points, data)` - finds energy bin index
  - `compton_xs(Z, E, photon_element, data)` - wrapper for Compton cross-section
  - `photoelectric_xs(Z, E, photon_element, data)` - wrapper for photoelectric cross-section
  - `pair_production_xs(Z, E, photon_element, data)` - wrapper for pair production cross-section
  - `get_element_xs(Z, reaction_type, E, photon_element, data)` - unified interface

**Target location:** `data/mcdc/` directory
- Contains HDF5 files per element: `H.h5`, `He.h5`, `Li.h5`, ..., `U.h5`
- Each file contains cross-section tables indexed by energy

## Files to Update

### 1. Production/Interface Files

#### File: `mcdc/transport/physics/photon/cross_sections.py`
**Current usage:** Calls `native.interpolate_xs()` for cross-section lookup
**Lines:** 87, 109
**Update approach:**
- Replace `native.interpolate_xs()` calls with HDF5 reads using `h5py`
- Load cross-section data from `data/mcdc/{element_symbol}.h5`
- Implement same log-log interpolation as native.py

#### File: `photon_transport_code/transport/physics/photon/cross_sections.py`
**Current usage:** Calls `native.interpolate_xs()` for cross-section lookup
**Lines:** 174, 220, 291, 321, 427, 467
**Update approach:**
- Same as above - replace with HDF5 reads
- Consolidate data loading to avoid repeated file I/O

#### File: `photon_transport_code/transport/physics/photon/interface.py`
**Current usage:** Imports native module, delegates to cross_sections functions
**Update approach:**
- No direct changes needed if cross_sections.py is updated
- May need to adjust how element data is passed

#### File: `mcdc/object_/photon_material.py`
**Current usage:** Imports `get_element_data` from native module (line 108)
**Update approach:**
- Replace `get_element_data(Z)` calls with HDF5 read from `data/mcdc/{element}.h5`
- Maintain same return format: `(energies, compton, pe, pair)`

### 2. Test Files

#### File: `photon_transport_code/test/unit/photon/test_total_xsec.py`
**Current usage:** 
- `native.build_element_buffer()` (lines 39, 45)
- `native.get_water_data()` (lines 195, 208)
- `native.get_element_data()` (lines 216-218)
**Update approach:**
- Replace with direct HDF5 reads
- Mock or use actual HDF5 files in test fixtures

#### File: `photon_transport_code/test/unit/photon/test_photoelectric.py`
**Current usage:** `native.build_element_buffer()` (lines 31, 37)
**Update approach:** Replace with HDF5-based fixture

#### File: `photon_transport_code/test/unit/photon/test_pair_production.py`
**Current usage:** `native.build_element_buffer()` (lines 36, 42)
**Update approach:** Replace with HDF5-based fixture

#### File: `photon_transport_code/test/unit/photon/test_coverage_gaps.py`
**Current usage:** Direct `build_element_buffer()` calls
**Update approach:** Replace with HDF5-based data loading

#### File: `photon_transport_code/test/regression/photon/conftest.py`
**Current usage:** `native.build_element_buffer(Z=13)` (line 38)
**Update approach:** Replace with HDF5 fixture

#### File: `photon_transport_code/test/regression/photon/test_performance_benchmark.py`
**Current usage:** `build_element_buffer()` calls
**Update approach:** Replace with HDF5-based setup

### 3. Example Files

#### File: `photon_transport_code/examples/photon_transport_photoelectric/problem.py`
**Current usage:** Imports and calls `build_element_buffer(Z=Z_AL)` (line 123)
**Update approach:** Replace with HDF5 read for aluminum (Z=13)

#### File: `photon_transport_code/examples/photon_transport_pair_production/problem.py`
**Current usage:** Imports and calls `build_element_buffer(Z=Z_LEAD)` (line 99)
**Update approach:** Replace with HDF5 read for lead (Z=82)

### Phase 5: Module Initialization and Cleanup

**File: `photon_transport_code/transport/physics/photon/__init__.py`**

After all calling code is updated:
- Remove or deprecate imports of `native` module
- Add import of new `data_loader` module for public API

```python
# OLD:
# from photon_transport_code.transport.physics.photon import native

# NEW (optional - for backwards compatibility):
# Create a compatibility shim that wraps data_loader functions
from photon_transport_code.transport.physics.photon.data_loader import (
    load_photon_element,
    load_water_data,
    load_photon_shell_resolved_pe
)

# Or leave imports empty if native module is fully deprecated
```

**Optional: Deprecation Path**

If backwards compatibility is needed, create a deprecation wrapper:

```python
# photon_transport_code/transport/physics/photon/native.py (modified)
"""DEPRECATED: Use data_loader module instead."""

import warnings
from photon_transport_code.transport.physics.photon.data_loader import (
    load_photon_element,
    load_water_data
)

def get_element_data(Z):
    """DEPRECATED: Use load_photon_element() instead."""
    warnings.warn(
        "get_element_data() is deprecated, use load_photon_element() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return load_photon_element(Z)

def get_water_data():
    """DEPRECATED: Use load_water_data() instead."""
    warnings.warn(
        "get_water_data() is deprecated, use load_water_data() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return load_water_data()
```

## HDF5 Data Format

The data files in `data/mcdc/` are now structured as follows after reformatting (see [FORMAT_PHOTON_DATA_MCDC.md](FORMAT_PHOTON_DATA_MCDC.md) for details):

```
{element}.h5
├── atomic_number: int64
├── atomic_weight_ratio: float64
├── element_name: string
├── excitation_level: int64 (always 0 for photons)
├── fissionable: bool (always False for photons)
└── photon_reactions/
    ├── xs_energy_grid: float64[N] - Shared energy points (log-spaced, keV)
    ├── elastic/ (Coherent/Rayleigh scattering)
    │   └── MT-502/
    │       ├── Q-value: float64 (0.0)
    │       ├── reference_frame: string ("LAB")
    │       └── xs: float64[N] - cross-section per atom (cm^2)
    ├── incoherent_scattering/ (Compton)
    │   └── MT-504/
    │       ├── Q-value: float64 (0.0)
    │       ├── reference_frame: string ("LAB")
    │       └── xs: float64[N] - cross-section per atom (cm^2)
    ├── photoelectric_absorption/
    │   ├── MT-501/ (total)
    │   │   ├── Q-value: float64 (0.0)
    │   │   ├── reference_frame: string ("LAB")
    │   │   └── xs: float64[N] - cross-section per atom (cm^2)
    │   └── shell_resolved/ (K, L1, L2, ...)
    │       ├── K/
    │       │   ├── binding_energy: float64
    │       │   └── xs: float64[N]
    │       └── [L1, L2, ...]/
    ├── pair_production/
    │   └── MT-503/
    │       ├── Q-value: float64 (0.0)
    │       ├── reference_frame: string ("LAB")
    │       ├── nuclear_field/xs: float64[N]
    │       ├── electron_field/xs: float64[N]
    │       └── xs: float64[N] (total)
    └── total/
        └── MT-401/ (total photon cross-section)
            ├── Q-value: float64 (0.0)
            ├── reference_frame: string ("LAB")
            └── xs: float64[N]
```

**Key Differences from Current Native.py:**
- Hierarchical structure with MT reaction codes
- Explicit Q-values and reference frames for each reaction
- Energy grid now at `photon_reactions/xs_energy_grid`
- Reactions organized under `photon_reactions/` with specific MT-XXX groups
- Shell information preserved under `shell_resolved/`

## Implementation Strategy

### Phase 1: Create HDF5 Data Loading Utility

Create `photon_transport_code/transport/physics/photon/data_loader.py`:

```python
import h5py
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "mcdc"

# Element symbol map for Z=1 to Z=92
ELEMENT_MAP = {
    1: "H", 2: "He", 3: "Li", 4: "Be", 5: "B", 6: "C", 7: "N", 8: "O", 9: "F", 10: "Ne",
    11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S", 17: "Cl", 18: "Ar", 19: "K", 20: "Ca",
    21: "Sc", 22: "Ti", 23: "V", 24: "Cr", 25: "Mn", 26: "Fe", 27: "Co", 28: "Ni", 29: "Cu", 30: "Zn",
    31: "Ga", 32: "Ge", 33: "As", 34: "Se", 35: "Br", 36: "Kr", 37: "Rb", 38: "Sr", 39: "Y", 40: "Zr",
    41: "Nb", 42: "Mo", 43: "Tc", 44: "Ru", 45: "Rh", 46: "Pd", 47: "Ag", 48: "Cd", 49: "In", 50: "Sn",
    51: "Sb", 52: "Te", 53: "I", 54: "Xe", 55: "Cs", 56: "Ba", 57: "La", 58: "Ce", 59: "Pr", 60: "Nd",
    61: "Pm", 62: "Sm", 63: "Eu", 64: "Gd", 65: "Tb", 66: "Dy", 67: "Ho", 68: "Er", 69: "Tm", 70: "Yb",
    71: "Lu", 72: "Hf", 73: "Ta", 74: "W", 75: "Re", 76: "Os", 77: "Ir", 78: "Pt", 79: "Au", 80: "Hg",
    81: "Tl", 82: "Pb", 83: "Bi", 84: "Po", 85: "At", 86: "Rn", 87: "Fr", 88: "Ra", 89: "Ac", 90: "Th",
    91: "Pa", 92: "U"
}

def load_photon_element(Z):
    """
    Load photon cross-section data from reformatted HDF5 file.
    
    Parameters
    ----------
    Z : int
        Atomic number (1 to 92)
    
    Returns
    -------
    tuple
        (energy_grid, compton_xs, photoelectric_xs, pair_production_xs)
        All in standard MCDC format
    """
    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1-92.")
    
    element_symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{element_symbol}.h5"
    
    if not hdf5_path.exists():
        raise FileNotFoundError(f"Photon data file not found: {hdf5_path}")
    
    with h5py.File(hdf5_path, 'r') as f:
        pr = f['photon_reactions']
        
        # Get shared energy grid
        energies = pr['xs_energy_grid'][()]
        
        # Extract individual reaction cross-sections
        # Compton (Incoherent Scattering MT-504)
        compton = pr['incoherent_scattering/MT-504/xs'][()]
        
        # Photoelectric (Total PE MT-501)
        photoelectric = pr['photoelectric_absorption/MT-501/xs'][()]
        
        # Pair Production (Total MT-503)
        pair_production = pr['pair_production/MT-503/xs'][()]
    
    return energies, compton, photoelectric, pair_production

def load_photon_element_coherent(Z):
    """Load coherent (Rayleigh) scattering cross-section."""
    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1-92.")
    
    element_symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{element_symbol}.h5"
    
    with h5py.File(hdf5_path, 'r') as f:
        pr = f['photon_reactions']
        energies = pr['xs_energy_grid'][()]
        coherent = pr['elastic/MT-502/xs'][()]
    
    return energies, coherent

def load_water_data():
    """
    Load composition-weighted water (H2O) cross-sections.
    
    Water composition: 2 hydrogen atoms + 1 oxygen atom
    Mass fraction: H ≈ 11.2%, O ≈ 88.8%
    
    Returns
    -------
    tuple
        (energy_grid, compton_xs, photoelectric_xs, pair_production_xs)
        Weighted for H2O composition
    """
    # Load H and O data
    e_h, c_h, pe_h, pp_h = load_photon_element(Z=1)  # Hydrogen
    e_o, c_o, pe_o, pp_o = load_photon_element(Z=8)  # Oxygen
    
    # Verify energy grids are identical
    if not np.allclose(e_h, e_o):
        raise ValueError("Energy grids for H and O don't match")
    
    # H2O composition weighting:
    # H: 2 atoms, mass = 2 amu, fraction = 2/(2+16) = 2/18 ≈ 0.111
    # O: 1 atom, mass = 16 amu, fraction = 16/(2+16) = 16/18 ≈ 0.889
    f_h = 2.0 / 18.0
    f_o = 16.0 / 18.0
    
    energies = e_h
    compton = f_h * c_h + f_o * c_o
    photoelectric = f_h * pe_h + f_o * pe_o
    pair_production = f_h * pp_h + f_o * pp_o
    
    return energies, compton, photoelectric, pair_production

def load_photon_shell_resolved_pe(Z):
    """
    Load shell-resolved photoelectric cross-sections.
    
    Returns
    -------
    dict
        Dictionary with keys 'energy_grid' and shell names (K, L1, L2, ...)
        Each shell contains 'xs' and 'binding_energy'
    """
    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1-92.")
    
    element_symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{element_symbol}.h5"
    
    result = {}
    
    with h5py.File(hdf5_path, 'r') as f:
        pr = f['photon_reactions']
        result['energy_grid'] = pr['xs_energy_grid'][()]
        
        # Load shell-resolved data
        if 'shell_resolved' in pr['photoelectric_absorption']:
            shells = pr['photoelectric_absorption/shell_resolved']
            for shell_name in shells.keys():
                shell_data = shells[shell_name]
                result[shell_name] = {
                    'xs': shell_data['xs'][()],
                    'binding_energy': shell_data['binding_energy'][()]
                }
    
    return result
```

**Key Features:**
- Reads from reformatted hierarchical HDF5 structure
- Uses MT codes to access specific reactions
- Element mapping Z→symbol for file lookup
- Water composition weighting
- Shell-resolved photoelectric access

### Phase 2: Update Cross-Section Functions

Replace all `native.interpolate_xs()` calls with HDF5 reads using the new `data_loader` module:

**File: `photon_transport_code/transport/physics/photon/cross_sections.py`**

Replace calls like:
```python
# OLD: Using native.interpolate_xs
sigma = native.interpolate_xs(E, eg_off, pe_off, N_pts, data)
```

With:
```python
# NEW: Using HDF5 data directly
from photon_transport_code.transport.physics.photon.data_loader import load_photon_element

def photoelectric_xs(Z, E, **kwargs):
    """Get photoelectric cross-section at energy E for element Z."""
    energies, _, photoelectric, _ = load_photon_element(Z)
    
    # Perform log-log interpolation (same as native.py)
    log_E = np.log(E)
    log_energies = np.log(energies)
    log_xs = np.log(photoelectric)
    
    xs = np.interp(log_E, log_energies, log_xs)
    return np.exp(xs)
```

**File: `mcdc/transport/physics/photon/cross_sections.py`**

Similar updates - replace `native.interpolate_xs()` with data loader:

```python
from photon_transport_code.transport.physics.photon.data_loader import load_photon_element

# Replace: sigma = native.interpolate_xs(...)
# With:
energies, _, photoelectric, _ = load_photon_element(Z)
sigma = np.interp(np.log(E), np.log(energies), np.log(photoelectric))
sigma = np.exp(sigma)  # convert back from log space
```

**File: `mcdc/object_/photon_material.py`**

Replace `get_element_data` import (line 108) with data loader:

```python
# OLD:
# from photon_transport_code.transport.physics.photon.native import get_element_data
# energies, compton, pe, pair = get_element_data(Z)

# NEW:
from photon_transport_code.transport.physics.photon.data_loader import load_photon_element
energies, compton, pe, pair = load_photon_element(Z)
```

**Benefits:**
- Direct HDF5 access eliminates native.py dependency
- Log-log interpolation logic unchanged
- Consistent return format with old `get_element_data()`

### Phase 3: Update Test Fixtures

Replace all `native.build_element_buffer()` and `native.get_element_data()` calls with data loader:

**File: `photon_transport_code/test/unit/photon/test_total_xsec.py`**

Replace fixture (lines 39, 45):
```python
# OLD:
# @pytest.fixture
# def al_element():
#     return native.build_element_buffer(13)

# NEW:
@pytest.fixture
def al_element():
    """Load aluminum cross-section data from HDF5."""
    from photon_transport_code.transport.physics.photon.data_loader import load_photon_element
    return load_photon_element(Z=13)

@pytest.fixture
def pb_element():
    """Load lead cross-section data from HDF5."""
    from photon_transport_code.transport.physics.photon.data_loader import load_photon_element
    return load_photon_element(Z=82)
```

Replace direct calls (lines 195, 208, 216-218):
```python
# OLD:
# energies, compton, pe, pair = native.get_water_data()
# e_h, c_h, _, _ = native.get_element_data(1)

# NEW:
from photon_transport_code.transport.physics.photon.data_loader import load_water_data, load_photon_element
energies, compton, pe, pair = load_water_data()
e_h, c_h, _, _ = load_photon_element(Z=1)
```

**File: `photon_transport_code/test/unit/photon/test_photoelectric.py`**

Replace fixtures (lines 31, 37):
```python
@pytest.fixture
def al_element():
    from photon_transport_code.transport.physics.photon.data_loader import load_photon_element
    return load_photon_element(Z=13)
```

**Files to Update (Similar Pattern):**
- `photon_transport_code/test/unit/photon/test_pair_production.py` (lines 36, 42)
- `photon_transport_code/test/unit/photon/test_coverage_gaps.py` (all `build_element_buffer()` calls)
- `photon_transport_code/test/regression/photon/conftest.py` (line 38)
- `photon_transport_code/test/regression/photon/test_performance_benchmark.py` (all calls)

**Pattern for All Updates:**
```python
# OLD: native.build_element_buffer(Z) or native.get_element_data(Z)
# NEW: load_photon_element(Z)
```

### Phase 4: Update Example Files

Replace `build_element_buffer()` calls with data loader:

**File: `photon_transport_code/examples/photon_transport_photoelectric/problem.py`**

Replace (line 99, 123):
```python
# OLD:
# from photon_transport_code.transport.physics.photon.native import build_element_buffer
# al_element, al_data = build_element_buffer(Z=Z_AL)

# NEW:
from photon_transport_code.transport.physics.photon.data_loader import load_photon_element
al_energies, al_compton, al_pe, al_pair = load_photon_element(Z=Z_AL)
# or use unpacking if needed for existing code structure
al_data = (al_energies, al_compton, al_pe, al_pair)
```

**File: `photon_transport_code/examples/photon_transport_pair_production/problem.py`**

Replace (line 79, 99):
```python
# OLD:
# from photon_transport_code.transport.physics.photon.native import build_element_buffer
# pb_element, pb_data = build_element_buffer(Z=Z_LEAD)

# NEW:
from photon_transport_code.transport.physics.photon.data_loader import load_photon_element
pb_energies, pb_compton, pb_pe, pb_pair = load_photon_element(Z=Z_LEAD)
```

Both examples can now use the tuple directly since `load_photon_element()` returns the same format as `get_element_data()`.

## Advantages of This Migration

1. **Reduced Code Complexity** - No embedded cross-section tables in Python code
2. **Unified Data Format** - Uses same HDF5 structure as neutron library (after reformatting per [FORMAT_PHOTON_DATA_MCDC.md](FORMAT_PHOTON_DATA_MCDC.md))
3. **Easier Updates** - Update cross-section data by replacing HDF5 files, not code
4. **Scalability** - Support for additional elements without modifying code
5. **Data Consistency** - Single source of truth in data files
6. **Reduced Binary Size** - Native.py becomes lighter or deprecated
7. **Better Maintainability** - Separation of data from logic
8. **Explicit Metadata** - Q-values, reference frames, MT codes clearly documented
9. **Shell Resolution** - Easy access to shell-resolved photoelectric data
10. **Tool Integration** - Compatible with nuclear data tools designed for HDF5 libraries

## Disadvantages and Mitigations

| Issue | Mitigation |
|-------|-----------|
| File I/O overhead | Cache loaded data in memory during runs; use lazy loading |
| Dependency on data files | Validate data files exist and are readable at startup |
| Reformatted data compatibility | Run [FORMAT_PHOTON_DATA_MCDC.md](FORMAT_PHOTON_DATA_MCDC.md) before this step |
| HDF5 library dependency | h5py already required; ensure it's in environment.yml |
| Performance regression | Run benchmarks to verify speed meets requirements |

## Validation Checklist

### Pre-Migration (Data Reformatting)
- [ ] [FORMAT_PHOTON_DATA_MCDC.md](FORMAT_PHOTON_DATA_MCDC.md) has been completed
- [ ] All HDF5 files in `data/mcdc/` have new reformatted structure
- [ ] Reformatted files validated against originals (energy grids, cross-sections match)
- [ ] HDF5 files contain all required MT codes (502, 504, 501, 503, 401)

### Pre-Migration (Code Updates)
- [ ] `data_loader.py` module created with all loader functions
- [ ] Import statements updated in all 13 files identified
- [ ] Existing cross-section functions modified to use `data_loader`
- [ ] Test fixtures updated to use new data loading

### Post-Migration (Validation)
- [ ] All tests pass with new implementation
- [ ] Examples run correctly with new data source
- [ ] Photon transport calculations produce identical results to native.py
- [ ] Performance meets requirements (< 10% regression if any)
- [ ] Documentation updated to reference `data_loader` instead of `native`
- [ ] Data files are accessible from all expected code paths

## Rollback Plan

### If Reformatting (FORMAT_PHOTON_DATA_MCDC.md) Fails
1. Keep `data/mcdc.backup/` directory (created in Phase 3 of FORMAT_PHOTON_DATA_MCDC.md)
2. Restore: `rm -r data/mcdc && mv data/mcdc.backup data/mcdc`
3. Continue using native.py with original data

### If Code Migration (This Document) Fails
1. Revert all file changes: `git checkout photon_transport_code/transport/physics/photon/ mcdc/`
2. Restore native.py imports in affected files
3. Keep reformatted data in place (can be reverted later if needed)
4. Re-attempt migration after fixing issues

### If Performance Regression Occurs
1. Implement data caching in `data_loader.py`:
   ```python
   _ELEMENT_CACHE = {}
   
   def load_photon_element(Z):
       if Z not in _ELEMENT_CACHE:
           # Load and cache
           _ELEMENT_CACHE[Z] = _load_from_hdf5(Z)
       return _ELEMENT_CACHE[Z]
   ```
2. Profile code to identify bottlenecks
3. Consider memmapped HDF5 access for large files
4. If still unacceptable, revert to native.py

### Git History Recovery
- Original format preserved in git history: `git show HEAD~1:data/mcdc/H.h5`
- Can always recreate original data from NIST XCOM source if needed
