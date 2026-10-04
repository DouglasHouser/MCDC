"""
Pytest fixtures for photon transport unit tests.

Provides reusable test materials, reference cross-section values, and
helper objects shared across all unit test files in test/unit/photon/.

Fixture categories:
    - Simple materials (single-element) for isolated cross-section testing
    - Compound materials (multi-element) for integration testing
    - NIST XCOM reference data at benchmark energies (Phase 2+)
    - Energy grids for parametric tests
"""

import numpy as np
import pytest


# ======================================================================================
# Material fixtures
# ======================================================================================


@pytest.fixture
def photon_material_aluminum():
    """
    Return a single-element aluminum photon material specification.

    Provides a pure aluminum material (Z=13) at standard conditions for
    isolated cross-section testing.  Number density corresponds to
    rho = 2.699 g/cm^3, A = 26.982 g/mol.

    Returns
    -------
    dict
        Photon material dict with keys: name, N_element, elements, densities,
        fissionable.  Compatible with photon_material() return format.

    Notes
    -----
    Reference number density:
        n_Al = (2.699 g/cm^3 * 6.022e23 mol^-1) / (26.982 g/mol * 1e24)
             = 6.026e-2 atoms/b-cm
    """
    return {
        "name": "aluminum",
        "N_element": 1,
        "elements": [13],
        "densities": [6.026e-2],
        "fissionable": False,
    }


@pytest.fixture
def photon_material_water():
    """
    Return a two-element liquid water photon material specification.

    Provides H2O at standard conditions (rho = 1.0 g/cm^3) for
    multi-element cross-section and transport tests.

    Returns
    -------
    dict
        Photon material dict with keys: name, N_element, elements, densities,
        fissionable.

    Notes
    -----
    Elemental number densities for H2O at 1.0 g/cm^3:
        n_H = 6.692e-2 atoms/b-cm  (2 H atoms per molecule)
        n_O = 3.346e-2 atoms/b-cm  (1 O atom per molecule)
    """
    return {
        "name": "water",
        "N_element": 2,
        "elements": [1, 8],
        "densities": [6.692e-2, 3.346e-2],
        "fissionable": False,
    }


@pytest.fixture
def photon_material_lead():
    """
    Return a single-element lead photon material specification.

    High-Z material (Z=82) for pair production and photoelectric testing.
    Number density corresponds to rho = 11.35 g/cm^3, A = 207.2 g/mol.

    Returns
    -------
    dict
        Photon material dict compatible with photon_material() return format.

    Notes
    -----
    Reference number density:
        n_Pb = (11.35 * 6.022e23) / (207.2 * 1e24) = 3.299e-2 atoms/b-cm
    """
    return {
        "name": "lead",
        "N_element": 1,
        "elements": [82],
        "densities": [3.299e-2],
        "fissionable": False,
    }


# ======================================================================================
# Energy grid fixtures
# ======================================================================================


@pytest.fixture
def energy_grid_decades():
    """
    Return a log-spaced energy grid spanning 1 keV to 100 MeV.

    Useful for parametric cross-section tests across the full photon
    transport energy range.

    Returns
    -------
    numpy.ndarray, shape (60,)
        Photon energies in MeV, 10 points per decade from 1e-3 to 1e2.
    """
    return np.logspace(-3, 2, 60)


@pytest.fixture
def energy_grid_compton():
    """
    Return benchmark energies for Compton cross-section validation.

    Covers the range where Compton scattering dominates (0.1–10 MeV) with
    additional points at the Thomson limit (low E) and relativistic regime.

    Returns
    -------
    numpy.ndarray, shape (7,)
        Photon energies in MeV at standard NIST validation points.
    """
    return np.array([0.01, 0.1, 0.5, 1.022, 2.0, 5.0, 10.0])


@pytest.fixture
def energy_grid_pair_production():
    """
    Return benchmark energies for pair production cross-section validation.

    Includes the threshold (1.022 MeV), just-above-threshold, and high-energy
    points where pair production dominates.

    Returns
    -------
    numpy.ndarray, shape (6,)
        Photon energies in MeV spanning the pair production regime.
    """
    return np.array([1.022, 1.1, 2.0, 5.0, 10.0, 100.0])


# ======================================================================================
# NIST XCOM reference data (Phase 2 - placeholders for now)
# ======================================================================================


@pytest.fixture
def nist_compton_aluminum():
    """
    NIST XCOM Compton cross-section reference data for aluminum.

    Used in Phase 2 cross-section validation tests.  Values are the
    incoherent scattering cross-section (cm^2/atom) at selected energies.

    Returns
    -------
    dict
        Keys: "energies" (MeV), "xs" (cm^2/atom).  NIST XCOM Z=13.

    Notes
    -----
    Values populated in Phase 2.  This fixture is a structural placeholder
    so test files can reference it from Phase 1 onward.
    """
    return {
        "energies": np.array([0.1, 0.5, 1.0, 5.0, 10.0]),
        "xs": np.zeros(5),  # Populated in Phase 2
        "source": "NIST XCOM Z=13",
        "tolerance": 0.02,  # 2% tolerance
    }


@pytest.fixture
def nist_total_water():
    """
    NIST XCOM total photon cross-section reference data for water.

    Used in Phase 2 total cross-section composition tests.

    Returns
    -------
    dict
        Keys: "energies" (MeV), "mu_rho" (cm^2/g mass attenuation).

    Notes
    -----
    Mass attenuation coefficient mu/rho in cm^2/g.  Values populated in
    Phase 2; this fixture is a structural placeholder.
    """
    return {
        "energies": np.array([0.1, 0.5, 1.0, 5.0, 10.0]),
        "mu_rho": np.zeros(5),  # Populated in Phase 2
        "source": "NIST XCOM H2O",
        "tolerance": 0.02,
    }
