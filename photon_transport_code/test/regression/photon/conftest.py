"""
Pytest fixtures for photon transport regression tests.

Provides reference cross-section data, benchmark material definitions, and
shared helpers for the regression test suite in test/regression/photon/.

Fixture categories:
    - Element data buffers: pre-built (photon_element, flat_data) pairs for Al and Pb
    - Benchmark materials: dict specs for Al, Pb, and water regression tests
    - NIST reference cross-sections at key benchmark energies
    - Energy grids for parametric regression sweeps
"""

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon.native import build_element_buffer


# ======================================================================================
# Element data fixtures
# ======================================================================================


@pytest.fixture(scope="session")
def al_element():
    """
    Pre-built photon_element structured array and flat data buffer for Al (Z=13).

    Returns
    -------
    tuple of (photon_element, flat_data)
        ``photon_element`` : numpy.ndarray, shape (1,), dtype=PHOTON_ELEMENT_DTYPE
            Structured array with offsets for cross-section lookup.
        ``flat_data`` : numpy.ndarray, shape (4*N,), dtype=float64
            Flat buffer: [energy_grid | compton | pe | pair].
    """
    return build_element_buffer(Z=13)


@pytest.fixture(scope="session")
def pb_element():
    """
    Pre-built photon_element structured array and flat data buffer for Pb (Z=82).

    Returns
    -------
    tuple of (photon_element, flat_data)
    """
    return build_element_buffer(Z=82)


@pytest.fixture(scope="session")
def h_element():
    """
    Pre-built photon_element structured array and flat data buffer for H (Z=1).

    Returns
    -------
    tuple of (photon_element, flat_data)
    """
    return build_element_buffer(Z=1)


@pytest.fixture(scope="session")
def o_element():
    """
    Pre-built photon_element structured array and flat data buffer for O (Z=8).

    Returns
    -------
    tuple of (photon_element, flat_data)
    """
    return build_element_buffer(Z=8)


# ======================================================================================
# Benchmark material specs
# ======================================================================================


@pytest.fixture
def material_aluminum():
    """
    Pure aluminum (Z=13) photon material dict.

    Number density n_Al = 6.026e-2 atoms/b-cm
    (from rho=2.699 g/cm^3, A=26.982 g/mol).
    """
    return {
        "name": "aluminum",
        "N_element": 1,
        "elements": [13],
        "densities": [6.026e-2],
        "fissionable": False,
    }


@pytest.fixture
def material_lead():
    """
    Pure lead (Z=82) photon material dict.

    Number density n_Pb = 3.299e-2 atoms/b-cm
    (from rho=11.35 g/cm^3, A=207.2 g/mol).
    """
    return {
        "name": "lead",
        "N_element": 1,
        "elements": [82],
        "densities": [3.299e-2],
        "fissionable": False,
    }


@pytest.fixture
def material_water():
    """
    Liquid water (H2O) photon material dict at 1.0 g/cm^3.

    Number densities:
        n_H = 6.692e-2 atoms/b-cm
        n_O = 3.346e-2 atoms/b-cm
    """
    return {
        "name": "water",
        "N_element": 2,
        "elements": [1, 8],
        "densities": [6.692e-2, 3.346e-2],
        "fissionable": False,
    }


# ======================================================================================
# NIST reference data fixtures
# ======================================================================================


@pytest.fixture
def nist_al_compton_dominated():
    """
    Energy range where Compton dominates for aluminum.

    Returns dict with reference energies (MeV) and expected Compton
    fraction > 0.5 of total cross-section.
    """
    return {
        "energies_MeV": [0.1, 0.5, 1.0, 2.0],
        "compton_fraction_min": 0.5,
        "description": "Compton-dominated regime for Al (0.1-2 MeV)",
    }


@pytest.fixture
def nist_pb_pe_dominated():
    """
    Energy range where photoelectric dominates for lead.

    Returns dict with reference energies (MeV) and expected PE
    fraction > 0.5 of total cross-section.
    """
    return {
        "energies_MeV": [0.01, 0.02, 0.05],
        "pe_fraction_min": 0.5,
        "description": "PE-dominated regime for Pb (10-50 keV)",
    }


@pytest.fixture
def pair_production_threshold():
    """
    Pair production threshold energy: 2 * m_e * c^2 = 1.02199790 MeV.

    Returns dict with threshold, just-below, and just-above energies.
    """
    threshold = 2.0 * 0.51099895  # 1.02199790 MeV
    return {
        "threshold_MeV": threshold,
        "below_MeV": [0.5, 1.0, threshold - 1e-6],
        "above_MeV": [threshold + 1e-6, 1.5, 2.0, 5.0, 10.0],
    }


# ======================================================================================
# Energy grid fixtures
# ======================================================================================


@pytest.fixture
def energy_grid_full():
    """
    Log-spaced energy grid spanning 1 keV to 100 MeV (full transport range).

    Returns
    -------
    numpy.ndarray, shape (60,)
        Energies in MeV.
    """
    return np.logspace(-3, 2, 60)


@pytest.fixture
def energy_grid_compton_regime():
    """
    Energies where Compton dominates for low-Z materials (0.1 – 10 MeV).

    Returns
    -------
    numpy.ndarray, shape (10,)
        Energies in MeV.
    """
    return np.logspace(-1, 1, 10)


@pytest.fixture
def energy_grid_pe_regime():
    """
    Energies where photoelectric dominates (0.001 – 0.1 MeV).

    Returns
    -------
    numpy.ndarray, shape (10,)
        Energies in MeV.
    """
    return np.logspace(-3, -1, 10)
