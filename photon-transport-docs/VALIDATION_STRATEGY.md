# Photon Transport Validation Strategy

**Version**: 1.0
**Date**: April 7, 2026
**Purpose**: Detailed validation procedures for each development phase
**Related**: PHOTON_TRANSPORT_RESEARCH_PLAN.md, ACCELERATED_TIMELINE.md

---

## Executive Summary

This document specifies **exact validation procedures, test criteria, and acceptance thresholds** for each phase of photon transport development. Each phase has:

- **What to validate** - specific code/physics to verify
- **How to validate** - test methods and procedures
- **Acceptance criteria** - pass/fail thresholds with tolerances
- **Test infrastructure** - pytest structure, fixtures, reference data
- **Success metrics** - quantifiable deliverables

**High-level validation flow:**

```
Phase 1 (Foundation)
  └─ Validate: Directory structure + imports + data definitions
     Acceptance: All files created, no import errors, type hints correct

Phase 2 (Cross-sections)
  └─ Validate: All 4 cross-sections match NIST within 1-2%
     Acceptance: Plots generated, tests pass, ±2% tolerance bands met

Phase 3 (Interactions)
  └─ Validate: Kinematics conserve energy/momentum/angle
     Acceptance: Energy conservation < 1e-10, angle distributions physical

Phase 4 (Integration)
  └─ Validate: Full system works, existing tests pass, examples run
     Acceptance: All 60+ existing neutron tests pass, 3 examples complete

Phase 5 (Documentation)
  └─ Validate: 95%+ code coverage, Sphinx builds, all tests pass
     Acceptance: Coverage report >95%, 0 doc build errors
```

---

## Phase 1: Foundation Validation

### Objective
Verify that directory structure, imports, and data structures are correctly set up and ready for physics code.

### 1.1 Structural Validation

**What to validate:**
- All required directories created
- All required Python files exist with proper `__init__.py`
- Module imports work without errors
- No circular imports

**How to validate:**

```bash
# Test 1.1: Directory structure
pytest photon-transport-code/test/unit/photon/test_phase1_structure.py::test_directory_structure -v

# Test 1.2: Module imports
python -c "import mcdc.transport.physics.photon; print('✓ photon module imports')"
python -c "import mcdc.mcdc_set.photon_material; print('✓ photon_material imports')"
python -c "import mcdc.mcdc_get.photon_material; print('✓ photon_get imports')"

# Test 1.3: No circular imports
python -m pytest photon-transport-code/test/unit/photon/test_phase1_imports.py -v
```

**Pytest structure** (`photon-transport-code/test/unit/photon/test_phase1_structure.py`):

```python
import os
import pytest

def test_photon_module_exists():
    """Verify photon physics module directory exists"""
    assert os.path.isdir('mcdc/transport/physics/photon')

def test_required_files_exist():
    """Verify all required photon module files exist"""
    required_files = [
        'photon-transport-code/transport/physics/photon/__init__.py',
        'photon-transport-code/transport/physics/photon/interface.py',
        'photon-transport-code/transport/physics/photon/native.py',
        'photon-transport-code/transport/physics/photon/distributions.py',
        'photon-transport-code/transport/physics/photon/cross_sections.py',
        'photon-transport-code/transport/physics/photon/util.py',
    ]
    for fp in required_files:
        assert os.path.isfile(fp), f"Missing: {fp}"

def test_test_directories_exist():
    """Verify test directories created"""
    assert os.path.isdir('test/unit/photon')
    assert os.path.isdir('test/regression/photon')

def test_photon_module_imports():
    """Verify photon module can be imported"""
    from mcdc.transport.physics import photon
    assert hasattr(photon, '__file__')
```

**Acceptance Criteria:**
- ✅ All 6 primary directories exist:
  1. photon-transport-code/transport/physics/photon/
  2. mcdc/mcdc_set/
  3. mcdc/mcdc_get/
  4. photon-transport-code/test/unit/photon/
  5. photon-transport-code/test/regression/photon/
  6. docs/source/user/photon/
- ✅ All 6 photon physics files present
- ✅ photon-transport-code/test/unit/photon/ and photon-transport-code/test/regression/photon/ exist
- ✅ All imports successful (0 errors)
- ✅ No circular imports detected

---

### 1.2 Data Structure Validation

**What to validate:**
- Photon particle state struct defined
- Reaction data struct defined
- Type hints present and correct
- Docstrings complete

**How to validate:**

```bash
# Test 1.4: Data structure definitions
pytest photon-transport-code/test/unit/photon/test_phase1_datastructs.py -v

# Test 1.5: Type hints
python -m mypy photon-transport-code/transport/physics/photon/ --check-untyped-defs
```

**Pytest structure** (`photon-transport-code/test/unit/photon/test_phase1_datastructs.py`):

```python
import pytest
from mcdc.transport.physics.photon import cross_sections

def test_photon_particle_state_struct():
    """Verify photon particle state struct has required fields"""
    # Check that struct is defined
    import inspect
    source = inspect.getsource(cross_sections)
    assert 'photon_state' in source or 'particle' in source.lower()

def test_reaction_data_struct():
    """Verify reaction data struct exists"""
    # Should have cross-section arrays, thresholds, etc.
    source = inspect.getsource(cross_sections)
    required_terms = ['cross_section', 'energy', 'threshold']
    for term in required_terms:
        assert term.lower() in source.lower()

def test_docstrings_present():
    """Verify all public functions have docstrings"""
    from mcdc.transport.physics.photon import interface
    funcs = [f for f in dir(interface) if not f.startswith('_')]
    for func_name in funcs:
        func = getattr(interface, func_name)
        if callable(func):
            assert func.__doc__ is not None, f"{func_name} missing docstring"
```

**Acceptance Criteria:**
- ✅ Photon particle state struct documented in code
- ✅ Reaction data struct documented
- ✅ All public functions have docstrings
- ✅ Type hints present (optional but encouraged)

---

### 1.3 Documentation Validation

**What to validate:**
- Memory files created (structure only)
- Research plan references Phase 1 deliverables
- Quick start checklist exists

**How to validate:**

```bash
# Manual check:
ls -l photon-transport/PHOTON_*.md
ls -l .claude/projects/MCDC/memory/
```

**Acceptance Criteria:**
- ✅ PHOTON_TRANSPORT_RESEARCH_PLAN.md exists (30+ KB)
- ✅ PHOTON_QUICKSTART.md exists (checklist structure)
- ✅ Memory files created (MEMORY.md, ACCELERATED_TIMELINE.md, STRATEGY_OVERVIEW.md)
- ✅ VALIDATION_STRATEGY.md exists (this file)

---

### 1.4 Phase 1 Sign-Off Checklist

```
[ ] All 6 photon physics module files created
[ ] All tests created in photon-transport-code/test/unit/photon/ and photon-transport-code/test/regression/photon/
[ ] Directories exist: photon-transport-code/test/unit/photon/, photon-transport-code/test/regression/photon/
[ ] No import errors when running: python -c "import mcdc.transport.physics.photon"
[ ] No import errors: mcdc_set.photon_material, mcdc_get.photon_material
[ ] Docstrings present for all public functions
[ ] 5+ memory files created
[ ] Research plan updated with Phase 1 completion
[ ] Ready for Phase 2: Cross-section implementation
```

---

## Phase 2: Cross-Sections Validation

### Objective
Verify that all four cross-sections (Compton, photoelectric, pair production, total) match NIST reference data within acceptable tolerances and that formulas are correctly implemented.

### 2.1 Klein-Nishina Cross-Section Validation

**What to validate:**
- Klein-Nishina formula correctly implemented
- Numerical integration accurate
- Total cross-section matches NIST XCOM within 1-2%
- Behavior correct at limits (E→0, E→∞)

**Test data sources:**
- NIST XCOM: https://www.nist.gov/pml/xcom (water, Al, Pb for 0.1 MeV - 100 MeV)
- Reference: Evans (1955), Klein & Nishina (1929)

**Tests** (`photon-transport-code/test/unit/photon/test_klein_nishina.py`):

```python
import numpy as np
import pytest
from mcdc.transport.physics.photon.cross_sections import klein_nishina_total

class TestKleinNishina:
    """Klein-Nishina cross-section tests"""

    # NIST reference data (example values for water)
    NIST_DATA = {
        'energy_MeV': [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
        'water_xsec_cm2g': [0.2015, 0.1815, 0.1552, 0.1159, 0.0595, 0.0312],  # barns/atom
    }

    def test_klein_nishina_zero_energy(self):
        """Klein-Nishina → Thomson at E→0"""
        E = 1e-3  # Very low energy
        sigma = klein_nishina_total(E)
        thomson = 0.665e-24  # Thomson cross-section (cm²)
        # At low E, should approach Thomson
        assert sigma > 0.6e-24, "Below Thomson at low energy"

    def test_klein_nishina_high_energy(self):
        """Klein-Nishina → 0 at E→∞"""
        E_high = np.array([1e3, 1e4, 1e5])  # Very high energy (MeV)
        sigma = klein_nishina_total(E_high)
        # Should decrease monotonically
        assert np.all(np.diff(sigma) <= 0), "Not monotonically decreasing"

    def test_klein_nishina_nist_comparison(self):
        """Compare to NIST XCOM within 2% tolerance"""
        for E, nist_val in zip(self.NIST_DATA['energy_MeV'],
                               self.NIST_DATA['water_xsec_cm2g']):
            computed = klein_nishina_total(E)
            error_percent = abs(computed - nist_val) / nist_val * 100
            assert error_percent < 2.0, f"Error {error_percent}% at E={E} MeV"

    def test_klein_nishina_monotonic_decrease(self):
        """Cross-section should decrease with energy"""
        E = np.logspace(-1, 2, 100)  # 0.1 to 100 MeV
        sigma = klein_nishina_total(E)
        # Should be monotonically decreasing
        assert np.all(np.diff(sigma) <= 0), "Not monotonic"

    def test_klein_nishina_differential_integration(self):
        """Integrated differential = total"""
        E = 1.0  # MeV
        # Numerically integrate dσ/dΩ over 4π steradians
        # Should equal total cross-section
        from mcdc.transport.physics.photon.distributions import klein_nishina_diff
        # Integration test (numerical)
        pass
```

**Validation plots** (Claude generates):
```
plots/klein_nishina_comparison.png
  - X-axis: Energy (MeV, log scale)
  - Y-axis: Cross-section (barns, log scale)
  - Lines: Code result, NIST reference
  - Band: ±2% tolerance envelope
  - Acceptance: Code line within band for all energies
```

**Acceptance Criteria:**
- ✅ All 4 unit tests pass
- ✅ Error vs NIST < 2% for energies 0.1-100 MeV
- ✅ Monotonic decrease with energy
- ✅ Correct limit behavior (Thomson at low E, ~0 at high E)
- ✅ Validation plot generated

---

### 2.2 Photoelectric Cross-Section Validation

**What to validate:**
- NIST XCOM data correctly loaded
- Cross-section lookup accurate
- Shell selection statistical distribution correct
- Total photoelectric = sum of shells

**Tests** (`photon-transport-code/test/unit/photon/test_photoelectric.py`):

```python
import numpy as np
import pytest
from mcdc.transport.physics.photon.cross_sections import photoelectric_total, load_nist_xcom

class TestPhotoelectric:
    """Photoelectric cross-section tests"""

    NIST_REFERENCE = {
        'Al': {0.01: 3.16e2, 0.1: 9.74, 1.0: 0.133},  # barns
        'Pb': {0.01: 7.84e3, 0.1: 37.2, 1.0: 0.177},
    }

    def test_nist_data_loads(self):
        """NIST data file loads successfully"""
        data = load_nist_xcom()
        assert data is not None
        assert 'Al' in data
        assert 'Pb' in data

    def test_photoelectric_vs_nist(self):
        """Compare to NIST within 1% tolerance"""
        for element, element_data in self.NIST_REFERENCE.items():
            for E_MeV, nist_xsec in element_data.items():
                computed = photoelectric_total(element, E_MeV)
                error_pct = abs(computed - nist_xsec) / nist_xsec * 100
                assert error_pct < 1.0, f"{element} error {error_pct}% at {E_MeV} MeV"

    def test_photoelectric_energy_range(self):
        """Cross-section valid for 0.001 - 100 MeV"""
        for E in [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]:
            sigma = photoelectric_total('Al', E)
            assert sigma > 0, f"Non-positive at E={E}"

    def test_shell_selection_statistics(self):
        """Shell selection follows correct statistics"""
        # Sample 10000 times, check K-shell fraction
        samples = [photoelectric_select_shell('Al', 0.5) for _ in range(10000)]
        k_fraction = np.mean(np.array(samples) == 'K')
        # K-shell should dominate near K-edge
        assert k_fraction > 0.7, f"K-shell fraction too low: {k_fraction}"

    def test_total_shells_sum(self):
        """Total = sum of K, L, M shells"""
        E = 0.5  # MeV
        total = photoelectric_total('Al', E)
        from_shells = (photoelectric_k_shell('Al', E) +
                      photoelectric_l_shell('Al', E) +
                      photoelectric_m_shell('Al', E))
        error_pct = abs(total - from_shells) / total * 100
        assert error_pct < 1.0, "Shell sum doesn't match total"
```

**Validation plot:**
```
plots/photoelectric_comparison.png
  - X-axis: Energy (MeV, log scale)
  - Y-axis: Cross-section (barns, log scale)
  - Lines: Code result, NIST reference (Al, Pb, Water)
  - Band: ±1% tolerance
  - Acceptance: All within band
```

**Acceptance Criteria:**
- ✅ All 5 unit tests pass
- ✅ Error vs NIST < 1% for 0.01-100 MeV
- ✅ NIST data file correctly loaded
- ✅ Shell statistics correct (K-shell weighted properly)
- ✅ Total from shell sum agrees with total

---

### 2.3 Pair Production Cross-Section Validation

**What to validate:**
- 2.044 MeV threshold enforced
- Above threshold matches NIST within 2%
- Below threshold = 0
- Reasonable high-energy tail

**Tests** (`photon-transport-code/test/unit/photon/test_pair_production.py`):

```python
import numpy as np
import pytest
from mcdc.transport.physics.photon.cross_sections import pair_production_total

class TestPairProduction:
    """Pair production cross-section tests"""

    THRESHOLD = 2.044  # MeV
    NIST_ABOVE_THRESHOLD = {
        'Pb': {2.1: 3.e-3, 5.0: 0.0213, 10.0: 0.0409, 100.0: 0.0592},  # barns
    }

    def test_threshold_enforced(self):
        """Cross-section zero below threshold"""
        E_below = np.array([1.0, 1.5, 2.0, 2.04])
        sigma = pair_production_total('Pb', E_below)
        assert np.all(sigma == 0), "Non-zero below threshold"

    def test_threshold_sharp_transition(self):
        """Sharp rise at threshold (within numerical precision)"""
        E_just_below = 2.043
        E_just_above = 2.045
        sigma_below = pair_production_total('Pb', E_just_below)
        sigma_above = pair_production_total('Pb', E_just_above)
        assert sigma_below == 0, "Non-zero just below threshold"
        assert sigma_above > 0, "Zero just above threshold"

    def test_pair_production_vs_nist(self):
        """Compare to NIST within 2% above threshold"""
        for E, nist_val in self.NIST_ABOVE_THRESHOLD['Pb'].items():
            computed = pair_production_total('Pb', E)
            error_pct = abs(computed - nist_val) / nist_val * 100
            assert error_pct < 2.0, f"Error {error_pct}% at E={E} MeV"

    def test_pair_production_monotonic_increase(self):
        """Cross-section increases above threshold"""
        E = np.linspace(2.1, 100, 50)
        sigma = pair_production_total('Pb', E)
        # Should be monotonically increasing above threshold
        assert np.all(np.diff(sigma) >= -1e-6), "Not monotonically increasing"
```

**Validation plot:**
```
plots/pair_production_comparison.png
  - X-axis: Energy (MeV, log scale)
  - Y-axis: Cross-section (barns, log scale)
  - Lines: Code result, NIST reference, threshold line at 2.044 MeV
  - Band: ±2% tolerance above threshold
  - Acceptance: All above threshold within band, zero below
```

**Acceptance Criteria:**
- ✅ All 4 unit tests pass
- ✅ Threshold = 2.044 MeV (exact)
- ✅ Error vs NIST < 2% for E > 2.1 MeV
- ✅ Zero cross-section enforced below threshold
- ✅ Validation plot generated

---

### 2.4 Total Cross-Section Validation

**What to validate:**
- Total = Compton + photoelectric + pair production
- Composition correct at all energies
- Dominance regions correct (PE at low E, Compton mid, pair at high E)

**Tests** (`photon-transport-code/test/unit/photon/test_total_xsec.py`):

```python
import numpy as np
import pytest
from mcdc.transport.physics.photon.cross_sections import (
    total_cross_section, klein_nishina_total, photoelectric_total,
    pair_production_total
)

class TestTotalXsec:
    """Total cross-section composition tests"""

    def test_total_composition(self):
        """Total = Compton + Photoelectric + Pair Production"""
        energies = np.logspace(-2, 3, 50)  # 0.01 to 1000 MeV
        for E in energies:
            total = total_cross_section('Al', E)
            compton = klein_nishina_total(E)
            pe = photoelectric_total('Al', E)
            pair = pair_production_total('Al', E)
            computed_sum = compton + pe + pair
            error_pct = abs(total - computed_sum) / computed_sum * 100
            assert error_pct < 0.1, f"Sum mismatch {error_pct}% at E={E}"

    def test_dominance_regions(self):
        """Verify dominance regions at different energies"""
        # Low energy: photoelectric should dominate
        E_low = 0.01  # MeV
        total_low = total_cross_section('Pb', E_low)
        pe_low = photoelectric_total('Pb', E_low)
        assert pe_low > 0.5 * total_low, "PE not dominant at low energy"

        # Mid energy: Compton should dominate
        E_mid = 1.0  # MeV
        total_mid = total_cross_section('Pb', E_mid)
        compton_mid = klein_nishina_total(E_mid)
        assert compton_mid > 0.5 * total_mid, "Compton not dominant at mid energy"

        # High energy: pair production should dominate
        E_high = 50.0  # MeV
        total_high = total_cross_section('Pb', E_high)
        pair_high = pair_production_total('Pb', E_high)
        assert pair_high > 0.5 * total_high, "Pair prod not dominant at high energy"

    def test_total_positive_everywhere(self):
        """Total cross-section always positive"""
        E = np.logspace(-2, 3, 100)
        for element in ['Al', 'Pb', 'Fe']:
            total = total_cross_section(element, E)
            assert np.all(total > 0), f"{element} has non-positive cross-section"
```

**Validation plot:**
```
plots/total_xsec_composition.png
  - X-axis: Energy (MeV, log scale)
  - Y-axis: Cross-section (barns, log scale)
  - Stacked area: Compton (red), Photoelectric (blue), Pair Production (green)
  - Overlay: Total (black line)
  - Acceptance: All components positive, total = sum, dominance regions correct
```

**Acceptance Criteria:**
- ✅ All 3 unit tests pass
- ✅ Total composition accurate to 0.1%
- ✅ Dominance regions correct (PE→Compton→Pair with increasing E)
- ✅ All cross-sections positive everywhere
- ✅ Composition plot generated

---

### 2.5 Phase 2 Sign-Off Checklist

```
[ ] Klein-Nishina: 4 tests pass, NIST error < 2%, plot generated
[ ] Photoelectric: 5 tests pass, NIST error < 1%, plot generated
[ ] Pair Production: 4 tests pass, NIST error < 2%, threshold exact, plot generated
[ ] Total composition: 3 tests pass, sum correct, dominance regions verified
[ ] All 16+ unit tests in photon-transport-code/test/unit/photon/ pass
[ ] photon_physics_reference.md created with formulas + sources
[ ] NIST validation plots in plots/ directory
[ ] Test coverage for cross_sections.py > 90%
[ ] Ready for Phase 3: Interaction physics
```

---

## Phase 3: Interaction Physics Validation

### Objective
Verify that scattering kernels correctly implement kinematics, conserve energy/momentum/angle, and produce physically plausible distributions.

### 3.1 Klein-Nishina Scattering Kernel Validation

**What to validate:**
- Energy conservation: E_photon_in = E_photon_out + E_electron
- Angle conservation: Scattering angles physical (0 to π)
- Distribution matches Klein-Nishina formula
- Edge cases handled (forward scattering, backscattering)

**Tests** (`photon-transport-code/test/unit/photon/test_compton_kernel.py`):

```python
import numpy as np
import pytest
from mcdc.transport.physics.photon.distributions import sample_klein_nishina

class TestKleinNishinaKernel:
    """Klein-Nishina scattering kernel tests"""

    def test_energy_conservation(self):
        """E_in = E_out + E_electron (within floating point)"""
        np.random.seed(42)
        E_in = 1.0  # MeV
        n_samples = 10000

        E_out_list, E_e_list, theta_list = [], [], []
        for _ in range(n_samples):
            E_out, theta, E_e = sample_klein_nishina(E_in)
            E_out_list.append(E_out)
            theta_list.append(theta)
            E_e_list.append(E_e)

        E_out_arr = np.array(E_out_list)
        E_e_arr = np.array(E_e_list)

        # Energy conservation: E_in = E_out + E_e
        E_sum = E_out_arr + E_e_arr
        error = np.abs(E_sum - E_in)
        max_error = np.max(error)
        assert max_error < 1e-10, f"Energy not conserved, max error: {max_error}"

    def test_energy_bounds(self):
        """Outgoing photon energy within physical bounds"""
        E_in = 1.0  # MeV
        E_backscatter_min = E_in / (1 + 2*E_in)  # Minimum energy (backscatter)

        for _ in range(1000):
            E_out, _, _ = sample_klein_nishina(E_in)
            assert E_out > 0, "Negative energy"
            assert E_out < E_in, "Energy > input"
            assert E_out >= E_backscatter_min * 0.99, "Below backscatter minimum"

    def test_angle_physical(self):
        """Scattering angles between 0 and π"""
        for _ in range(1000):
            E_out, theta, _ = sample_klein_nishina(1.0)
            assert 0 <= theta <= np.pi, f"Angle outside [0, π]: {theta}"

    def test_forward_backscatter_extremes(self):
        """Forward (θ≈0) and backscatter (θ≈π) cases handled"""
        E_in = 2.0

        # Sample many times to find forward and backward scatters
        samples = [sample_klein_nishina(E_in) for _ in range(10000)]
        theta_arr = np.array([s[1] for s in samples])

        # Forward scatters (θ < 10°)
        forward_mask = theta_arr < np.radians(10)
        assert np.any(forward_mask), "No forward scatters in 10k samples"

        # Backward scatters (θ > 170°)
        backward_mask = theta_arr > np.radians(170)
        assert np.any(backward_mask), "No backward scatters in 10k samples"

    def test_distribution_shape(self):
        """Distribution follows Klein-Nishina shape"""
        E_in = 1.0
        samples = [sample_klein_nishina(E_in) for _ in range(10000)]
        theta_arr = np.array([s[1] for s in samples])

        # Compute angle histogram
        hist, bins = np.histogram(theta_arr, bins=50, range=(0, np.pi))

        # Klein-Nishina: more backscatter at lower energies, more forward at higher
        # General shape: should have samples throughout range (not all forward)
        forward_fraction = np.sum(theta_arr < np.pi/2) / len(theta_arr)
        backward_fraction = np.sum(theta_arr > np.pi/2) / len(theta_arr)

        # Both should be significant (not all forward or all backward)
        assert 0.3 < forward_fraction < 0.7, f"Forward fraction skewed: {forward_fraction}"
```

**Validation plots:**
```
plots/compton_energy_conservation.png
  - X-axis: Energy in (MeV)
  - Y-axis: Energy out + Electron energy
  - Expected: y = x line
  - Acceptance: Points on line within numerical precision

plots/compton_angle_distribution.png
  - X-axis: Scattering angle θ (degrees)
  - Y-axis: Probability/count
  - Overlay: Theoretical Klein-Nishina (ksn_formula(θ))
  - Acceptance: Histogram matches theory curve

plots/compton_energy_angle_correlation.png
  - X-axis: Angle θ (degrees)
  - Y-axis: Outgoing energy (MeV)
  - Scatter: Sample points
  - Upper bound: E_in line
  - Lower bound: E_backscatter line
  - Acceptance: All points within bounds, correlation visible
```

**Acceptance Criteria:**
- ✅ All 5 unit tests pass
- ✅ Energy conservation < 1e-10 MeV
- ✅ All angles in [0, π]
- ✅ Forward and backscatter samples present
- ✅ Distribution shape matches Klein-Nishina
- ✅ Energy-angle correlation plots generated

---

### 3.2 Pair Production Kinematics Validation

**What to validate:**
- Energy conservation: E_photon = E_electron + E_positron + E_nuclear
- Momentum conservation (approximately, nuclear recoil small)
- Angle constraints: Electrons/positrons forward-peaked
- Threshold behavior at 2.044 MeV

**Tests** (`photon-transport-code/test/unit/photon/test_pair_production_kernel.py`):

```python
import numpy as np
import pytest
from mcdc.transport.physics.photon.distributions import sample_pair_production

class TestPairProductionKernel:
    """Pair production kinematics tests"""

    def test_energy_conservation(self):
        """E_γ ≈ E_e+ + E_e- (+ small nuclear recoil)"""
        E_gamma = 10.0  # MeV
        n_samples = 10000

        E_e_plus, E_e_minus, theta_plus, theta_minus = zip(*[
            sample_pair_production(E_gamma) for _ in range(n_samples)
        ])
        E_e_plus = np.array(E_e_plus)
        E_e_minus = np.array(E_e_minus)

        E_sum = E_e_plus + E_e_minus
        error = np.abs(E_sum - E_gamma) / E_gamma

        # Should be within ~0.1% (nuclear recoil ~MeV/100)
        assert np.mean(error) < 0.01, f"Mean energy error too large: {np.mean(error)}"
        assert np.max(error) < 0.05, f"Max energy error too large: {np.max(error)}"

    def test_threshold_below_2044(self):
        """Below 2.044 MeV returns None or raises"""
        E_below_threshold = 2.0  # MeV
        result = sample_pair_production(E_below_threshold)
        assert result is None or np.isnan(result[0]), "Non-physical result below threshold"

    def test_forward_peaking(self):
        """Electrons/positrons mostly forward (θ < 90°)"""
        E_gamma = 50.0  # MeV
        samples = [sample_pair_production(E_gamma) for _ in range(1000)]
        theta_e_plus = np.array([s[2] for s in samples])
        theta_e_minus = np.array([s[3] for s in samples])

        forward_plus = np.sum(theta_e_plus < np.pi/2) / len(theta_e_plus)
        forward_minus = np.sum(theta_e_minus < np.pi/2) / len(theta_e_minus)

        # At 50 MeV, should be mostly forward
        assert forward_plus > 0.8, f"Not forward-peaked: {forward_plus}"
        assert forward_minus > 0.8, f"Not forward-peaked: {forward_minus}"

    def test_energy_sharing(self):
        """Electron and positron share energy"""
        E_gamma = 10.0
        samples = [sample_pair_production(E_gamma) for _ in range(1000)]
        E_plus_arr = np.array([s[0] for s in samples])
        E_minus_arr = np.array([s[1] for s in samples])

        # Both should have non-trivial distributions
        # (not all energy to one particle)
        assert np.std(E_plus_arr) > 0.1, "No energy spread for e+"
        assert np.std(E_minus_arr) > 0.1, "No energy spread for e-"
```

**Validation plots:**
```
plots/pair_production_energy_conservation.png
  - X-axis: E_electron + E_positron (MeV)
  - Y-axis: E_photon (MeV)
  - Expected: y = x line
  - Tolerance: ±1% band
  - Acceptance: Points within band

plots/pair_production_angle_distribution.png
  - Subplots: e+ angles, e- angles (both forward peaked)
  - X-axis: θ (degrees)
  - Y-axis: Count
  - Acceptance: Peaks near 0°, most < 90°

plots/pair_production_energy_sharing.png
  - X-axis: E_positron (MeV)
  - Y-axis: E_electron (MeV)
  - Scatter: Sample points
  - Diagonal: E_positron + E_electron = E_photon
  - Acceptance: Points distribute along diagonal
```

**Acceptance Criteria:**
- ✅ All 4 unit tests pass
- ✅ Energy conservation < 1% error
- ✅ Threshold enforced at 2.044 MeV
- ✅ Forward peaking verified (>80% for E > 5 MeV)
- ✅ Energy sharing distribution plots generated

---

### 3.3 Photoelectric Absorption Validation

**What to validate:**
- Shell selection statistics correct (K-shell weights)
- Energy deposition = photon energy
- No secondary particles created (Phase 1 model)

**Tests** (`photon-transport-code/test/unit/photon/test_photoelectric_kernel.py`):

```python
import numpy as np
import pytest
from mcdc.transport.physics.photon.distributions import photoelectric_absorption

class TestPhotoelectricKernel:
    """Photoelectric absorption tests"""

    def test_energy_deposition(self):
        """Photon energy fully absorbed"""
        E_photon = 0.5  # MeV
        n_samples = 1000

        for _ in range(n_samples):
            E_deposited = photoelectric_absorption(E_photon)
            assert np.isclose(E_deposited, E_photon, rtol=1e-10), \
                f"Energy not conserved: {E_deposited} vs {E_photon}"

    def test_no_secondary_particles_phase1(self):
        """Phase 1: No secondary electrons/X-rays returned"""
        E_photon = 0.05  # MeV
        result = photoelectric_absorption(E_photon)

        # Should return single value (energy deposited), not tuple
        assert isinstance(result, (int, float, np.number)), \
            "Should return scalar in Phase 1"

    def test_shell_selection_statistics(self):
        """K-shell dominates (weighted selection)"""
        shell_samples = []
        for _ in range(10000):
            # Sample shell selection
            E = 0.1  # MeV
            shell = photoelectric_select_shell_internal(E)
            shell_samples.append(shell)

        k_fraction = np.array(shell_samples) == 'K'
        assert np.mean(k_fraction) > 0.7, "K-shell not dominant"
```

**Validation plots:**
```
plots/photoelectric_shell_statistics.png
  - Bar chart: K, L, M shell selection fractions
  - Multiple energies: 0.01, 0.05, 0.1, 0.5 MeV
  - Expected: K-shell > 70% at all energies
  - Acceptance: K-shell most frequent
```

**Acceptance Criteria:**
- ✅ All 3 unit tests pass
- ✅ Energy deposition = photon energy (exact)
- ✅ Phase 1: No secondary particles
- ✅ Shell selection statistics correct
- ✅ Shell selection plot generated

---

### 3.4 Phase 3 Sign-Off Checklist

```
[ ] Compton kernel: 5 tests pass, energy conserved < 1e-10 MeV
[ ] Compton: All angles in [0, π], forward and backscatter present
[ ] Compton: Distribution shape matches Klein-Nishina
[ ] Pair production: 4 tests pass, energy < 1% error
[ ] Pair production: Threshold enforced, forward peaking verified
[ ] Photoelectric: 3 tests pass, energy deposition exact
[ ] Photoelectric: Shell statistics correct
[ ] All 12+ tests in photon-transport-code/test/unit/photon/test_*_kernel.py pass
[ ] 5+ validation plots generated and reviewed
[ ] Test coverage for distributions.py > 90%
[ ] Ready for Phase 4: Integration testing
```

---

## Phase 4: Integration Validation

### Objective
Verify full system integration: transport loop works with photons, existing neutron tests pass, examples run and produce correct physics.

### 4.1 Transport Loop Integration Validation

**What to validate:**
- Photon/neutron branching works
- Photon particles tracked correctly
- No exceptions or crashes

**Tests** (`photon-transport-code/test/unit/photon/test_integration_transport.py`):

```python
import pytest
import mcdc

class TestTransportLoopIntegration:
    """Transport loop integration tests"""

    def test_photon_neutron_branching(self):
        """Transport loop correctly branches on particle type"""
        # Simple setup: 1 photon, 1 neutron, check both transported
        sp = mcdc.MultiplicityDistribution([0, 1], [0.5, 0.5])

        # Verify branching calls correct physics
        assert True  # Placeholder - depends on internal structure

    def test_photon_simulation_runs_without_crash(self):
        """Basic photon simulation completes without error"""
        import mcdc.type_

        # Setup
        mcdc.reset()
        mcdc.particle("photon")
        mcdc.material(sigma_t=np.array([1.0]))
        mcdc.cell([-1])
        # ... source, tally, etc.

        # Should run without exception
        try:
            mcdc.run()
            success = True
        except Exception as e:
            success = False

        assert success, "Photon simulation crashed"
```

**Acceptance Criteria:**
- ✅ Transport loop detects photon particle type
- ✅ Photon physics functions called correctly
- ✅ No crashes or exceptions
- ✅ Simulation completes without hang

---

### 4.2 Existing Test Suite Validation

**What to validate:**
- All existing neutron tests still pass
- No regression in neutron physics

**Tests:**
```bash
# Run full existing test suite
pytest test/unit/neutron/ -v
pytest test/regression/ -v

# Expected: 100% pass, 0 new failures
```

**Acceptance Criteria:**
- ✅ All pre-existing tests pass
- ✅ 0 new failures
- ✅ No performance regression (benchmark timing)

---

### 4.3 Example Validation

**Example 1: Photon Absorption in Slab**

**Setup:**
- Photon beam through Al slab (5 cm thick)
- Energy: 1 MeV
- Material: Al (density 2.7 g/cm³)

**Expected behavior:**
- Transmitted flux decays exponentially: I(x) = I₀ exp(-μx)
- Total cross-section μ ≈ 0.1 cm⁻¹ (from NIST)
- Expected transmission: exp(-0.1 × 5) ≈ 60%

**Test** (`photon-transport-code/test/regression/photon/test_absorption_slab.py`):

```python
import pytest
import mcdc
import numpy as np

def test_absorption_slab():
    """Beer-Lambert law validation"""
    mcdc.reset()

    # Setup geometry
    mcdc.surface("plane_x", 0.0, (1, 0, 0))
    mcdc.surface("plane_x", 5.0, (1, 0, 0))
    mcdc.cell([-1], [1])  # Between planes

    # Setup material - Al
    mcdc.material(
        nuclide=[("Al-27", 1.0)],
        density=2.7  # g/cm³
    )

    # Source: monodirectional photon beam
    mcdc.source(
        x=0.5, y=0, z=0,  # Start at surface
        ux=1, uy=0, uz=0,  # Forward direction
        E=1.0,  # 1 MeV
        particle="photon"
    )

    # Tally transmitted flux
    mcdc.tally(
        name="transmitted_flux",
        x_grid=np.linspace(4, 6, 2),
        particle="photon"
    )

    # Run
    mcdc.run(histories=100000, mpi_processes=1)

    # Extract results
    tally = mcdc.get("tally", 0)
    transmitted_flux = tally["transmitted_flux"][1]  # Beyond slab

    # Expected: exp(-μx) ≈ 0.606 (60%)
    # NIST: μ ≈ 0.1 cm⁻¹ at 1 MeV for Al
    mu = 0.1  # cm⁻¹
    x = 5.0  # cm
    expected_transmission = np.exp(-mu * x)

    # Check within 5% (accounting for Monte Carlo noise)
    error = abs(transmitted_flux - expected_transmission) / expected_transmission
    assert error < 0.05, f"Transmission error {error*100:.1f}% > 5%"
```

**Validation:**
```
Output file: photon-transport-code/examples/photon_absorption_slab/output.h5
Plot: Flux attenuation vs depth
Expected: Exponential decay matching Beer-Lambert
Acceptance: Error < 5% vs theoretical
```

**Example 2: Compton Scattering Spectrum**

**Setup:**
- Isotropic photon source in water
- Energy: 1 MeV (mono-energetic)
- Score: Energy spectrum of scattered photons

**Expected behavior:**
- Scattered photons have continuous spectrum
- Peak near incident energy (Thomson limit at low energies)
- Extend down to backscatter minimum (~0.25 MeV for 1 MeV incident)

**Test** (`photon-transport-code/test/regression/photon/test_compton_spectrum.py`):

```python
def test_compton_spectrum():
    """Klein-Nishina spectrum validation"""
    mcdc.reset()

    # Simple geometry: water sphere
    mcdc.material(nuclide=[("H", 2), ("O", 1)])
    mcdc.cell([1, -1])

    # Isotropic 1 MeV photon source
    mcdc.source(
        x=0, y=0, z=0,
        E=1.0,
        particle="photon",
        isotropic=True
    )

    # Tally energy spectrum
    E_bins = np.linspace(0, 1.0, 51)
    mcdc.tally(
        name="energy_spectrum",
        E_grid=E_bins,
        particle="photon",
        quantity="flux"
    )

    mcdc.run(histories=100000)

    # Extract spectrum
    spectrum = mcdc.get("tally", 0)["energy_spectrum"]

    # Validate:
    # 1. Continuous distribution (not discrete peaks)
    # 2. Extends from 0.25 to 1.0 MeV
    # 3. Peak near incident energy

    assert spectrum.min() > 0.2, "Spectrum extends below backscatter minimum"
    assert spectrum.max() < 1.1, "Spectrum exceeds incident energy"
    assert np.argmax(spectrum) > len(spectrum) // 2, "Peak not near incident energy"
```

**Example 3: Pair Production Threshold**

**Setup:**
- Photon beam at various energies
- 2 MeV (below threshold) vs 2.5 MeV (above threshold)
- Verify pair production cross-section jumps

**Test** (`photon-transport-code/test/regression/photon/test_pair_production_threshold.py`):

```python
def test_pair_production_threshold():
    """Pair production threshold validation"""

    # Test below threshold: 2.0 MeV
    mcdc.reset()
    mcdc.source(E=2.0, particle="photon")  # Below threshold
    mcdc.tally(name="positrons_created")
    mcdc.run(histories=10000)
    tally_below = mcdc.get("positron_count", 0)

    # Test above threshold: 2.5 MeV
    mcdc.reset()
    mcdc.source(E=2.5, particle="photon")  # Above threshold
    mcdc.tally(name="positrons_created")
    mcdc.run(histories=10000)
    tally_above = mcdc.get("positron_count", 0)

    # Verification:
    # Below threshold: very few (only from other processes)
    # Above threshold: significant number

    assert tally_below < tally_above / 10, "Threshold not enforced"
```

**Acceptance Criteria:**
- ✅ Example 1: Absorption follows Beer-Lambert within 5%
- ✅ Example 2: Compton spectrum continuous, correct range
- ✅ Example 3: Pair production threshold sharp at 2.044 MeV
- ✅ All 3 examples run without error
- ✅ Output files created and readable
- ✅ Plots generated showing physical behavior

---

### 4.4 Phase 4 Sign-Off Checklist

```
[ ] Transport loop tests pass (no branching issues)
[ ] All existing 60+ neutron tests still pass
[ ] 0 new test failures vs baseline
[ ] Example 1 (absorption): Error < 5% vs Beer-Lambert
[ ] Example 2 (Compton spectrum): Continuous, correct range, correct peak
[ ] Example 3 (pair threshold): Threshold at 2.044 MeV enforced
[ ] 3+ example scripts run without error
[ ] Output files (HDF5) created and readable
[ ] Example visualization plots generated
[ ] 20+ regression tests total pass
[ ] Integration documentation updated
[ ] Ready for Phase 5: Documentation & polishing
```

---

## Phase 5: Documentation and Final Validation

### Objective
Verify complete documentation, test coverage > 95%, and overall code quality. Final sign-off.

### 5.1 Code Coverage Validation

**What to validate:**
- Test coverage > 95% for photon physics code
- All branches covered
- Edge cases tested

**Tests:**
```bash
# Run coverage report
pytest test/ --cov=mcdc.transport.physics.photon --cov-report=html

# Expected: > 95%, all modules
```

**Acceptance Criteria:**
- ✅ Overall coverage > 95%
- ✅ cross_sections.py > 95%
- ✅ distributions.py > 95%
- ✅ interface.py > 95%
- ✅ All branches covered (no dead code)

---

### 5.2 Documentation Build Validation

**What to validate:**
- Sphinx builds without errors
- All photon transport pages render
- API docs auto-generated from docstrings

**Tests:**
```bash
# Build docs
cd docs/
make clean html

# Expected: 0 errors, 0 warnings
```

**Acceptance Criteria:**
- ✅ Sphinx build succeeds
- ✅ 0 build errors
- ✅ 0 warnings (or acceptable warnings)
- ✅ photon_transport_01_overview.rst renders
- ✅ photon_transport_02_physics.rst renders
- ✅ photon_transport_03_usage.rst renders
- ✅ photon_transport_04_validation.rst renders

---

### 5.3 Full Test Suite Validation

**What to validate:**
- All 50+ photon unit tests pass
- All 20+ photon regression tests pass
- All 60+ neutron tests still pass
- Total test time < 2 minutes

**Tests:**
```bash
# Run full test suite
pytest test/ -v --tb=short

# Expected: 130+ tests pass, 0 failures
```

**Acceptance Criteria:**
- ✅ 50+ photon unit tests pass
- ✅ 20+ photon regression tests pass
- ✅ 60+ neutron tests pass (no regression)
- ✅ 0 failures / xfails
- ✅ Test suite runs in < 5 minutes

---

### 5.4 Code Quality Validation

**What to validate:**
- Black formatting compliance
- No Numba incompatibilities
- Docstrings complete
- Type hints present

**Tests:**
```bash
# Black formatting
black --check photon-transport-code/transport/physics/photon/

# Type hints (optional)
mypy photon-transport-code/transport/physics/photon/

# Docstring coverage
pytest photon-transport-code/test/unit/photon/test_docstrings.py
```

**Pytest structure** (`photon-transport-code/test/unit/photon/test_docstrings.py`):

```python
import pytest
from mcdc.transport.physics import photon

def test_all_functions_have_docstrings():
    """All public functions documented"""
    modules = [photon.interface, photon.cross_sections,
               photon.distributions, photon.native]

    for module in modules:
        for name in dir(module):
            if not name.startswith('_'):
                obj = getattr(module, name)
                if callable(obj):
                    assert obj.__doc__ is not None, f"{name} missing docstring"
```

**Acceptance Criteria:**
- ✅ Black formatting passes (0 reformatting needed)
- ✅ No mypy type errors
- ✅ All public functions have docstrings
- ✅ All docstrings use NPDoc format

---

### 5.5 Performance Validation

**What to validate:**
- Photon transport performance comparable to neutron
- No major slowdowns from branching logic

**Tests:**
```bash
# Benchmark test
pytest photon-transport-code/test/regression/photon/test_performance_benchmark.py

# Expected: Photon tracking ~5-10% slower than neutron (branching overhead)
```

**Test structure** (`photon-transport-code/test/regression/photon/test_performance_benchmark.py`):

```python
import time
import pytest
import mcdc

def test_photon_performance_vs_neutron():
    """Photon parsing speed comparable to neutron"""

    # Neutron benchmark
    start = time.time()
    # Run typical neutron simulation
    mcdc.run(histories=10000, mpi_processes=1)
    neutron_time = time.time() - start

    # Photon benchmark (same histories)
    mcdc.reset()
    mcdc.source(particle="photon")
    start = time.time()
    mcdc.run(histories=10000, mpi_processes=1)
    photon_time = time.time() - start

    # Photon should be within 2x of neutron (overhead acceptable)
    speedup_ratio = photon_time / neutron_time
    assert speedup_ratio < 2.0, f"Photon {speedup_ratio:.1f}x slower than neutron"
```

**Acceptance Criteria:**
- ✅ Photon tracking < 2x slower than neutron
- ✅ Branching logic overhead minimal
- ✅ No memory leaks (can run 100k histories)

---

### 5.6 Final Review Checklist

**Code Quality:**
```
[ ] Black formatting passes
[ ] Mypy type hints pass (0 errors)
[ ] All docstrings present and correct
[ ] No dead/unreachable code
[ ] All functions have type hints (recommended)
```

**Testing:**
```
[ ] Photon unit tests: 50+ pass
[ ] Photon regression tests: 20+ pass
[ ] Neutron tests: 60+ still pass (no regression)
[ ] Coverage: > 95% across photon module
[ ] Performance: < 2x vs neutron
```

**Documentation:**
```
[ ] Sphinx builds: 0 errors, 0 warnings
[ ] 4 user guide chapters complete
[ ] API docs auto-generated
[ ] Example walkthroughs complete
[ ] Physics reference formulas documented
[ ] Installation instructions updated
```

**Examples:**
```
[ ] Example 1 (absorption): Runs, produces correct output
[ ] Example 2 (Compton): Runs, produces correct output
[ ] Example 3 (pair production): Runs, produces correct output
[ ] All 3 examples have README with expected results
[ ] Output plots generated and committed (or .gitignore'd)
```

**Deliverables:**
```
[ ] photon-transport-code/transport/physics/photon/ (6 files, ~5 KLoC)
[ ] mcdc/mcdc_set/photon_*.py (2 files, ~500 LoC)
[ ] mcdc/mcdc_get/photon_*.py (auto-generated)
[ ] photon-transport-code/test/unit/photon/ (10+ files, ~50 tests)
[ ] photon-transport-code/test/regression/photon/ (5+ files, ~20 tests)
[ ] docs/source/user/photon/ (4 RST files)
[ ] docs/source/pythonapi/photon*.rst (2+ files, auto-generated)
[ ] photon-transport-code/examples/photon_transport_*/Notebooks or scripts (3 examples)
[ ] PHOTON_TRANSPORT_RESEARCH_PLAN.md (updated)
[ ] VALIDATION_STRATEGY.md (this file, updated)
[ ] PHOTON_PHYSICS_REFERENCE.md (complete)
```

---

### 5.7 Phase 5 Sign-Off Checklist

```
[ ] Code Coverage: 95%+ overall, all modules > 90%
[ ] Sphinx Documentation: Builds cleanly, 0 errors
[ ] Full Test Suite: 130+ tests pass, 0 failures
[ ] Code Quality: Black + mypy pass, docstrings complete
[ ] Performance: Photon < 2x slower than neutron
[ ] All 3 examples run and produce correct physics
[ ] Output HDF5 files readable and formatted correctly
[ ] GitHub issue marked complete with summary
[ ] All documentation files updated
[ ] Memory files updated with lessons learned
[ ] Ready for publication/deployment
```

---

## Final Validation Summary

### Quick Reference: All Acceptance Criteria

| Phase | Metric | Target | How to Verify |
|-------|--------|--------|---------------|
| **1** | Directory structure | 7+ dirs created | `ls -la photon-transport-code/transport/physics/photon/` |
| **1** | Module imports | 0 errors | `python -c "import mcdc.transport.physics.photon"` |
| **2** | Cross-section accuracy | < 2% vs NIST | `pytest photon-transport-code/test/unit/photon/test_*xsec*.py` + plots |
| **2** | Photoelectric accuracy | < 1% vs NIST | `pytest photon-transport-code/test/unit/photon/test_photoelectric.py` |
| **3** | Energy conservation | < 1e-10 MeV | `pytest photon-transport-code/test/unit/photon/test_*_kernel.py` |
| **3** | Angle distributions | physical [0,π] | Validation plots + histogram tests |
| **4** | Neutron regression | 0 new failures | `pytest test/` (full suite) |
| **4** | Examples | correct physics | Run 3 examples, compare to hand calc |
| **5** | Test coverage | > 95% | `pytest --cov` report |
| **5** | Sphinx build | 0 errors | `cd docs && make clean html` |
| **5** | Code quality | Black pass | `black --check photon-transport-code/transport/physics/photon/` |

---

## How to Use This Document

**During Phase 1:**
- Read Section "Phase 1: Foundation Validation"
- Create tests listed under 1.1-1.3
- Run tests after each task
- Mark complete in checklist

**During Phase 2:**
- Read "Phase 2: Cross-Sections Validation"
- Generate NIST reference data
- Create pytest files for each cross-section
- Generate validation plots
- Verify all < 2% error before proceeding

**During Phase 3:**
- Read "Phase 3: Interaction Physics Validation"
- Create kernel validation tests
- Generate energy conservation plots
- Verify kinematics before proceeding

**During Phase 4:**
- Read "Phase 4: Integration Validation"
- Verify transport loop works
- Run existing test suite (should pass 100%)
- Create example scripts
- Compare examples to hand-calculated results

**During Phase 5:**
- Read "Phase 5: Documentation and Final Validation"
- Build Sphinx docs
- Generate coverage reports
- Review all deliverables checklist
- Final sign-off

---

**Version History:**
- v1.0 (2026-04-07): Initial comprehensive validation strategy for all 5 phases

