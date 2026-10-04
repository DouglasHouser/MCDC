"""
Unit tests for pair production cross-section.

Validates:
  - Hard zero below 1.022 MeV threshold (exact)
  - Hard zero at exactly 1.022 MeV
  - Non-zero above threshold
  - Within ±2% of NIST XCOM at benchmark energies for Al and Pb
  - Increasing with energy above threshold
  - Z^2 scaling: Pb >> Al

Run with::

    pytest test/unit/photon/test_pair_production.py -v
"""

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon.cross_sections import (
    pair_production_xs,
)
from photon_transport_code.transport.physics.photon.native import build_element_buffer
from photon_transport_code.transport.physics.photon.util import (
    PAIR_PRODUCTION_THRESHOLD,
)

# ======================================================================================
# Fixtures
# ======================================================================================


@pytest.fixture(scope="module")
def al_buffer():
    """Return (photon_element, flat_data) for Aluminum Z=13."""
    return build_element_buffer(13)


@pytest.fixture(scope="module")
def pb_buffer():
    """Return (photon_element, flat_data) for Lead Z=82."""
    return build_element_buffer(82)


@pytest.fixture(scope="module")
def al_data(al_buffer):
    """Flat data array for Al."""
    return al_buffer[1]


@pytest.fixture(scope="module")
def pb_data(pb_buffer):
    """Flat data array for Pb."""
    return pb_buffer[1]


# ======================================================================================
# NIST reference values
# Source: NIST XCOM Z=13 and Z=82, pair production (nuclear + electron field)
# Units: cm^2/atom
# ======================================================================================

_AL_PP_NIST = [
    # (E_MeV, sigma_cm2_per_atom)
    (2.0, 2.870e-27),
    (5.0, 1.566e-26),
    (10.0, 2.929e-26),
]

_PB_PP_NIST = [
    # (E_MeV, sigma_cm2_per_atom)
    (2.0, 3.388e-25),
    (5.0, 1.838e-24),
    (10.0, 3.434e-24),
]

_TOLERANCE = 0.02  # 2%


# ======================================================================================
# Threshold tests — critical correctness checks
# ======================================================================================


def test_pair_production_zero_below_threshold_al(al_data):
    """pair_production_xs returns exactly 0.0 for E < 1.022 MeV (Al)."""
    for E in [0.1, 0.5, 1.0, 1.021]:
        sigma = pair_production_xs(13, E, al_data)
        assert (
            sigma == 0.0
        ), f"Al pair production non-zero below threshold at E={E} MeV: {sigma}"


def test_pair_production_zero_at_threshold_al(al_data):
    """pair_production_xs returns exactly 0.0 at E = 1.022 MeV (at threshold)."""
    sigma = pair_production_xs(13, 1.022, al_data)
    assert sigma == 0.0, f"Al pair production non-zero at threshold: {sigma}"


def test_pair_production_zero_below_threshold_pb(pb_data):
    """pair_production_xs returns exactly 0.0 for E < 1.022 MeV (Pb)."""
    for E in [0.1, 0.5, 1.0, 1.021]:
        sigma = pair_production_xs(82, E, pb_data)
        assert (
            sigma == 0.0
        ), f"Pb pair production non-zero below threshold at E={E} MeV: {sigma}"


def test_pair_production_zero_at_threshold_pb(pb_data):
    """pair_production_xs returns exactly 0.0 at E = 1.022 MeV (at threshold)."""
    sigma = pair_production_xs(82, 1.022, pb_data)
    assert sigma == 0.0, f"Pb pair production non-zero at threshold: {sigma}"


def test_pair_production_nonzero_above_threshold_al(al_data):
    """pair_production_xs is positive for E > 1.022 MeV (Al)."""
    for E in [1.25, 1.5, 2.0, 5.0, 10.0]:
        sigma = pair_production_xs(13, E, al_data)
        assert sigma > 0.0, f"Al pair production zero above threshold at E={E}: {sigma}"


def test_pair_production_nonzero_above_threshold_pb(pb_data):
    """pair_production_xs is positive for E > 1.022 MeV (Pb)."""
    for E in [1.25, 2.0, 5.0, 10.0]:
        sigma = pair_production_xs(82, E, pb_data)
        assert sigma > 0.0, f"Pb pair production zero above threshold at E={E}: {sigma}"


def test_threshold_constant_matches_util():
    """PAIR_PRODUCTION_THRESHOLD constant is 2 * m_e * c^2 = 1.02199790 MeV."""
    assert abs(PAIR_PRODUCTION_THRESHOLD - 1.02199790) < 1e-5


# ======================================================================================
# NIST reference values (±2%)
# ======================================================================================


@pytest.mark.parametrize("E_MeV, expected", _AL_PP_NIST)
def test_al_pair_production_nist(E_MeV, expected, al_data):
    """Al pair production within 2% of NIST XCOM at benchmark energies."""
    sigma = pair_production_xs(13, E_MeV, al_data)
    rel_err = abs(sigma - expected) / expected
    assert rel_err < _TOLERANCE, (
        f"Al PP at {E_MeV} MeV: got {sigma:.4e}, NIST {expected:.4e}, "
        f"err={rel_err*100:.2f}%"
    )


@pytest.mark.parametrize("E_MeV, expected", _PB_PP_NIST)
def test_pb_pair_production_nist(E_MeV, expected, pb_data):
    """Pb pair production within 2% of NIST XCOM at benchmark energies."""
    sigma = pair_production_xs(82, E_MeV, pb_data)
    rel_err = abs(sigma - expected) / expected
    assert rel_err < _TOLERANCE, (
        f"Pb PP at {E_MeV} MeV: got {sigma:.4e}, NIST {expected:.4e}, "
        f"err={rel_err*100:.2f}%"
    )


# ======================================================================================
# Physical behavior
# ======================================================================================


def test_al_pair_production_increases_with_energy(al_data):
    """Al pair production cross-section increases with energy above threshold."""
    energies = [1.25, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0]
    values = [pair_production_xs(13, E, al_data) for E in energies]
    for i in range(len(values) - 1):
        assert values[i] < values[i + 1], (
            f"Al PP not increasing: sigma({energies[i]})={values[i]:.4e} "
            f">= sigma({energies[i+1]})={values[i+1]:.4e}"
        )


def test_pb_larger_than_al(al_data, pb_data):
    """Pb pair production >> Al at same energy (Z^2 scaling)."""
    for E in [2.0, 5.0, 10.0]:
        sigma_al = pair_production_xs(13, E, al_data)
        sigma_pb = pair_production_xs(82, E, pb_data)
        # Z^2 ratio = (82/13)^2 ≈ 39.8; expect at least 20x
        assert (
            sigma_pb > 20.0 * sigma_al
        ), f"At {E} MeV: Pb PP={sigma_pb:.4e} should be >>20x Al PP={sigma_al:.4e}"


def test_pair_production_above_threshold_all_positive(al_data, pb_data):
    """All pair production values positive above threshold for both elements."""
    energies = np.array([1.25, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0, 100.0])
    for E in energies:
        for Z, data in [(13, al_data), (82, pb_data)]:
            sigma = pair_production_xs(Z, E, data)
            assert sigma > 0.0 and np.isfinite(
                sigma
            ), f"Z={Z}, E={E}: PP sigma={sigma} invalid"


# ======================================================================================
# Structured-array API consistency
# ======================================================================================


def test_element_api_matches_flat_al(al_buffer):
    """pair_production_xs_element gives same result as flat buffer for Al."""
    photon_element, flat_data = al_buffer
    from transport.physics.photon.cross_sections import pair_production_xs_element

    for E in [2.0, 5.0, 10.0]:
        sigma_flat = pair_production_xs(13, E, flat_data)
        sigma_elem = pair_production_xs_element(13, E, photon_element, flat_data)
        assert (
            abs(sigma_flat - sigma_elem) / sigma_flat < 1e-12
        ), f"API mismatch at E={E}: flat={sigma_flat:.6e}, elem={sigma_elem:.6e}"
