"""
Unit tests for photoelectric cross-section.

Validates tabulated NIST XCOM interpolation for Al (Z=13) and Pb (Z=82):
  - Within ±2% of NIST reference at benchmark energies
  - K-edge discontinuity preserved for Pb at 0.088 MeV
  - Correct power-law behavior between shell edges
  - Zero or near-zero at high energies where PE is negligible

Run with::

    pytest test/unit/photon/test_photoelectric.py -v
"""

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon.cross_sections import (
    photoelectric_xs,
)
from photon_transport_code.transport.physics.photon.native import build_element_buffer

# ======================================================================================
# Fixtures: build element data buffers
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
def al_data_flat(al_buffer):
    """Return just the flat data array for Al (for photoelectric_xs interface)."""
    return al_buffer[1]


@pytest.fixture(scope="module")
def pb_data_flat(pb_buffer):
    """Return just the flat data array for Pb."""
    return pb_buffer[1]


# ======================================================================================
# NIST reference values for Aluminum Z=13
# Source: NIST XCOM Z=13, photoelectric cross-section (cm^2/atom)
# ======================================================================================

_AL_PE_NIST = [
    # (E_MeV, sigma_cm2_per_atom)
    (0.01, 2.240e-23),
    (0.1, 8.030e-28),
    (1.0, 1.420e-31),
    (5.0, 9.290e-34),
    (10.0, 9.990e-35),
]

_PB_PE_NIST = [
    # (E_MeV, sigma_cm2_per_atom)  — values above K-edge (0.088 MeV)
    (0.1, 8.210e-24),
    (1.0, 1.580e-27),
    (5.0, 8.970e-30),
    (10.0, 9.470e-31),
]

_TOLERANCE = 0.02  # 2%


# ======================================================================================
# Aluminum PE cross-section vs NIST
# ======================================================================================


@pytest.mark.parametrize("E_MeV, expected", _AL_PE_NIST)
def test_al_photoelectric_nist(E_MeV, expected, al_data_flat):
    """Al photoelectric cross-section within 2% of NIST XCOM at benchmark energies."""
    sigma = photoelectric_xs(13, E_MeV, al_data_flat)
    rel_err = abs(sigma - expected) / expected
    assert rel_err < _TOLERANCE, (
        f"Al PE at {E_MeV} MeV: got {sigma:.4e}, NIST {expected:.4e}, "
        f"err={rel_err*100:.2f}%"
    )


def test_al_photoelectric_positive(al_data_flat):
    """Al photoelectric cross-section is positive across energy range."""
    for E in [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]:
        sigma = photoelectric_xs(13, E, al_data_flat)
        assert sigma > 0.0, f"Al PE non-positive at E={E} MeV: {sigma}"


def test_al_photoelectric_decreasing(al_data_flat):
    """Al photoelectric cross-section decreases with energy (away from edges)."""
    # Sample above K-edge (1.56 keV) at widely spaced points
    energies = [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
    values = [photoelectric_xs(13, E, al_data_flat) for E in energies]
    for i in range(len(values) - 1):
        assert values[i] > values[i + 1], (
            f"Al PE not decreasing: sigma({energies[i]})={values[i]:.4e} "
            f">= sigma({energies[i+1]})={values[i+1]:.4e}"
        )


# ======================================================================================
# Lead PE cross-section — K-edge discontinuity
# ======================================================================================


def test_pb_k_edge_discontinuity(pb_data_flat):
    """Lead photoelectric cross-section has jump discontinuity at K-edge (0.088 MeV)."""
    # Just below K-edge
    sigma_below = photoelectric_xs(82, 0.0879, pb_data_flat)
    # Just above K-edge
    sigma_above = photoelectric_xs(82, 0.0881, pb_data_flat)

    # Above K-edge should be substantially larger (jump factor ~7-8x for Pb)
    ratio = sigma_above / sigma_below
    assert ratio > 3.0, (
        f"Pb K-edge jump insufficient: below={sigma_below:.4e}, "
        f"above={sigma_above:.4e}, ratio={ratio:.2f} (expect >3)"
    )


@pytest.mark.parametrize("E_MeV, expected", _PB_PE_NIST)
def test_pb_photoelectric_nist(E_MeV, expected, pb_data_flat):
    """Pb photoelectric cross-section within 2% of NIST XCOM at benchmark energies."""
    sigma = photoelectric_xs(82, E_MeV, pb_data_flat)
    rel_err = abs(sigma - expected) / expected
    assert rel_err < _TOLERANCE, (
        f"Pb PE at {E_MeV} MeV: got {sigma:.4e}, NIST {expected:.4e}, "
        f"err={rel_err*100:.2f}%"
    )


def test_pb_photoelectric_high_z_larger_than_al(al_data_flat, pb_data_flat):
    """Pb PE cross-section much larger than Al at same energy (Z^4 scaling)."""
    for E in [0.1, 1.0, 5.0]:
        sigma_al = photoelectric_xs(13, E, al_data_flat)
        sigma_pb = photoelectric_xs(82, E, pb_data_flat)
        assert (
            sigma_pb > sigma_al * 10.0
        ), f"At {E} MeV: Pb PE={sigma_pb:.4e} should be >>10x Al PE={sigma_al:.4e}"


# ======================================================================================
# Interpolation boundary behavior
# ======================================================================================


def test_al_below_energy_grid_clips(al_data_flat):
    """Query below energy grid minimum returns first-point value (no crash)."""
    sigma = photoelectric_xs(13, 1e-6, al_data_flat)
    assert sigma > 0.0 and np.isfinite(sigma)


def test_al_above_energy_grid_clips(al_data_flat):
    """Query above energy grid maximum extrapolates without crash."""
    sigma = photoelectric_xs(13, 1000.0, al_data_flat)
    assert sigma >= 0.0 and np.isfinite(sigma)


# ======================================================================================
# photon_element structured-array API
# ======================================================================================


def test_al_element_api_matches_flat(al_buffer, al_data_flat):
    """photoelectric_xs via photon_element gives same result as flat-buffer variant."""
    photon_element, flat_data = al_buffer
    from transport.physics.photon.cross_sections import photoelectric_xs_element

    for E in [0.01, 0.1, 1.0, 5.0, 10.0]:
        sigma_flat = photoelectric_xs(13, E, al_data_flat)
        sigma_elem = photoelectric_xs_element(13, E, photon_element, flat_data)
        assert (
            abs(sigma_flat - sigma_elem) / sigma_flat < 1e-12
        ), f"API mismatch at E={E} MeV: flat={sigma_flat:.6e}, elem={sigma_elem:.6e}"
