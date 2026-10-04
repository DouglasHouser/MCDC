"""
Photon cross-section data management.

Data loading is now delegated to the ``data_loader`` module, which reads
from the reformatted HDF5 files in ``data/mcdc/`` (see
FORMAT_PHOTON_DATA_MCDC.md).  This module retains:

  - ``get_element_data(Z)``  / ``get_water_data()``  — thin wrappers that
    delegate to ``data_loader`` (kept for backward compatibility)
  - ``_loglog_interp_python``                         — pure-Python helper
  - ``interpolate_xs`` / ``find_energy_bin``          — @njit interpolators
  - ``get_element_xs`` / ``compton_xs`` / …           — @njit accessors
  - ``PHOTON_ELEMENT_DTYPE`` / ``build_element_buffer``  — buffer helpers

All @njit functions operate on the flat ``data`` numpy array via integer
offsets stored in the photon_element structured array, matching the MCDC
pattern for nuclide data access.

References
----------
NIST XCOM: https://www.nist.gov/pml/xcom
Berger, M.J. et al. (2010). XCOM: Photon Cross Sections Database,
    NIST Standard Reference Database 8 (XGAM).
"""

import math

import numpy as np
from numba import njit

from photon_transport_code.transport.physics.photon import util

# ======================================================================================
# Reaction type constants
# ======================================================================================

REACTION_COMPTON = 0
REACTION_PHOTOELECTRIC = 1
REACTION_PAIR = 2

# ======================================================================================
# Data loading — delegates to data_loader (HDF5-backed)
# ======================================================================================


def get_element_data(Z: int):
    """
    Return photon cross-section data arrays for element Z.

    Delegates to ``data_loader.load_photon_element(Z)``, which reads from the
    reformatted HDF5 files in ``data/mcdc/``.

    Parameters
    ----------
    Z : int
        Atomic number (1–92).

    Returns
    -------
    tuple of (energies, compton_xs, photoelectric_xs, pair_xs)
        Each is a 1-D float64 array sorted by energy (MeV).
        Cross-sections in cm²/atom.
    """
    from photon_transport_code.transport.physics.photon.data_loader import (
        load_photon_element,
    )
    return load_photon_element(Z)


def get_water_data():
    """
    Return composition-weighted cross-sections for water (H₂O).

    Delegates to ``data_loader.load_water_data()``.

    Returns
    -------
    tuple of (energies, compton_xs, photoelectric_xs, pair_xs)
        Energies in MeV; cross-sections in cm²/atom, mass-fraction weighted.
    """
    from photon_transport_code.transport.physics.photon.data_loader import (
        load_water_data,
    )
    return load_water_data()


# ======================================================================================
# Pure-Python log-log interpolation (data-preparation / test helper)
# ======================================================================================


def _loglog_interp_python(x, xp, fp):
    """
    Pure-Python log-log interpolation for data preparation and tests.

    Parameters
    ----------
    x : float
        Query energy (MeV).
    xp : numpy.ndarray
        Tabulated energies, sorted ascending.
    fp : numpy.ndarray
        Tabulated cross-section values (cm²/atom).

    Returns
    -------
    float
        Interpolated cross-section value.
    """
    n = len(xp)
    if x <= xp[0]:
        idx = 0
    elif x >= xp[-1]:
        idx = n - 2
    else:
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xp[mid] <= x:
                lo = mid
            else:
                hi = mid
        idx = lo

    x0, x1 = xp[idx], xp[idx + 1]
    y0, y1 = fp[idx], fp[idx + 1]

    if y0 <= 0.0 or y1 <= 0.0:
        t = (x - x0) / (x1 - x0)
        return float(y0 + t * (y1 - y0))

    log_alpha = (math.log(y1) - math.log(y0)) / (math.log(x1) - math.log(x0))
    return float(math.exp(math.log(y0) + log_alpha * (math.log(x) - math.log(x0))))


# ======================================================================================
# @njit cross-section interpolation (operates on pre-extracted numpy arrays)
# ======================================================================================


@njit
def interpolate_xs(E, energy_grid_offset, xs_offset, N_points, data):
    """
    Perform log-log interpolation on a tabulated cross-section.

    Locates the energy bin containing E via binary search, then
    interpolates log(sigma) vs log(E) linearly.

    Parameters
    ----------
    E : float
        Incident photon energy in MeV.
    energy_grid_offset : int
        Starting index in ``data`` for the energy grid of this element/reaction.
    xs_offset : int
        Starting index in ``data`` for the cross-section values.
    N_points : int
        Number of tabulated energy/cross-section points.
    data : numpy.ndarray, shape (N,)
        Flat data buffer; both the energy grid and cross-section arrays are
        stored here at their respective offsets.

    Returns
    -------
    float
        Interpolated cross-section in cm²/atom.
    """
    idx = find_energy_bin(E, energy_grid_offset, N_points, data)
    x0 = data[energy_grid_offset + idx]
    x1 = data[energy_grid_offset + idx + 1]
    y0 = data[xs_offset + idx]
    y1 = data[xs_offset + idx + 1]
    return util.log_log_interpolation(E, x0, x1, y0, y1)


@njit
def find_energy_bin(E, energy_grid_offset, N_points, data):
    """
    Binary search for the index of the energy bin containing E.

    Parameters
    ----------
    E : float
        Incident photon energy in MeV.
    energy_grid_offset : int
        Starting index in ``data`` for the energy grid.
    N_points : int
        Number of tabulated energy points.
    data : numpy.ndarray, shape (N,)
        Flat data buffer.

    Returns
    -------
    int
        Index ``idx`` such that data[energy_grid_offset + idx] <= E
        < data[energy_grid_offset + idx + 1].
        Returns 0 if E is below the grid minimum.
        Returns N_points - 2 if E is above the grid maximum.
    """
    if E <= data[energy_grid_offset]:
        return 0
    if E >= data[energy_grid_offset + N_points - 1]:
        return N_points - 2

    lo = 0
    hi = N_points - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if data[energy_grid_offset + mid] <= E:
            lo = mid
        else:
            hi = mid
    return lo


# ======================================================================================
# Element cross-section accessors (pure-Python wrappers for test convenience)
# ======================================================================================


@njit
def get_element_xs(Z, reaction_type, E, photon_element, data):
    """
    Return the microscopic photon cross-section for a single element.

    Parameters
    ----------
    Z : int
        Atomic number (informational; offsets are in photon_element).
    reaction_type : int
        One of REACTION_COMPTON (0), REACTION_PHOTOELECTRIC (1),
        or REACTION_PAIR (2).
    E : float
        Incident photon energy in MeV.
    photon_element : numpy.ndarray (structured)
        Structured array for this element.
    data : numpy.ndarray, shape (N,)
        Flat data buffer.

    Returns
    -------
    float
        Microscopic cross-section in cm²/atom.
    """
    N = photon_element[0]["N_points"]
    eg_off = photon_element[0]["energy_grid_offset"]

    if reaction_type == 0:  # Compton
        xs_off = photon_element[0]["compton_offset"]
    elif reaction_type == 1:  # Photoelectric
        xs_off = photon_element[0]["pe_offset"]
    else:  # Pair production
        if E < 1.02199790:
            return 0.0
        xs_off = photon_element[0]["pair_offset"]

    return interpolate_xs(E, eg_off, xs_off, N, data)


@njit
def compton_xs(Z, E, photon_element, data):
    """
    Return the Compton (incoherent) cross-section per atom for element Z.

    Uses the free-electron Klein-Nishina formula × Z.

    Parameters
    ----------
    Z : int
        Atomic number of the element.
    E : float
        Incident photon energy in MeV.
    photon_element : numpy.ndarray (structured)
        Not used for Compton; included for API consistency.
    data : numpy.ndarray, shape (N,)
        Not used for Compton; included for API consistency.

    Returns
    -------
    float
        Compton cross-section per atom in cm²/atom.
    """
    alpha = E / 0.51099895
    r_e = 2.8179403e-13
    pi = 3.141592653589793

    if alpha < 1e-6:
        sigma_per_e = (8.0 / 3.0) * pi * r_e * r_e
    else:
        a2 = 2.0 * alpha
        ln_term = math.log(1.0 + a2)
        term1 = (1.0 + alpha) / (alpha * alpha * alpha)
        term2 = a2 * (1.0 + alpha) / (1.0 + a2) - ln_term
        term3 = ln_term / (2.0 * alpha)
        term4 = (1.0 + 3.0 * alpha) / ((1.0 + a2) * (1.0 + a2))
        sigma_per_e = 2.0 * pi * r_e * r_e * (term1 * term2 + term3 - term4)

    return sigma_per_e * float(Z)


@njit
def photoelectric_xs(Z, E, photon_element, data):
    """
    Return the photoelectric cross-section per atom for element Z at energy E.

    Parameters
    ----------
    Z : int
        Atomic number of the element.
    E : float
        Incident photon energy in MeV.
    photon_element : numpy.ndarray (structured)
        Structured array containing offsets for PE cross-section table.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing the PE cross-section table.

    Returns
    -------
    float
        Photoelectric cross-section per atom in cm²/atom.
    """
    N = photon_element[0]["N_points"]
    eg_off = photon_element[0]["energy_grid_offset"]
    xs_off = photon_element[0]["pe_offset"]
    return interpolate_xs(E, eg_off, xs_off, N, data)


@njit
def pair_production_xs(Z, E, photon_element, data):
    """
    Return the pair production cross-section per atom for element Z at energy E.

    Parameters
    ----------
    Z : int
        Atomic number of the element.
    E : float
        Incident photon energy in MeV.
    photon_element : numpy.ndarray (structured)
        Structured array containing offsets for PP cross-section table.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing the PP cross-section table.

    Returns
    -------
    float
        Pair production cross-section per atom in cm²/atom.
        Returns 0.0 for E < 1.022 MeV (below threshold).
    """
    if E < 1.02199790:
        return 0.0
    N = photon_element[0]["N_points"]
    eg_off = photon_element[0]["energy_grid_offset"]
    xs_off = photon_element[0]["pair_offset"]
    return interpolate_xs(E, eg_off, xs_off, N, data)


# ======================================================================================
# Data buffer builder (Python-level, called once at startup)
# ======================================================================================

PHOTON_ELEMENT_DTYPE = np.dtype(
    [
        ("Z", np.int32),
        ("N_points", np.int32),
        ("energy_grid_offset", np.int32),
        ("compton_offset", np.int32),
        ("pe_offset", np.int32),
        ("pair_offset", np.int32),
    ]
)


def build_element_buffer(Z: int):
    """
    Build a flat data buffer and photon_element structured array for element Z.

    Data is loaded from the reformatted HDF5 files via ``get_element_data``.

    Parameters
    ----------
    Z : int
        Atomic number (1–92).

    Returns
    -------
    photon_element : numpy.ndarray, shape (1,), dtype=PHOTON_ELEMENT_DTYPE
        Structured array with offsets into the flat data buffer.
    data : numpy.ndarray, shape (4*N,), dtype=float64
        Flat buffer: [energy_grid | compton_xs | pe_xs | pair_xs].
    """
    energies, compton, pe, pair = get_element_data(Z)
    N = len(energies)

    data = np.concatenate([energies, compton, pe, pair])

    photon_element = np.zeros(1, dtype=PHOTON_ELEMENT_DTYPE)
    photon_element[0]["Z"] = Z
    photon_element[0]["N_points"] = N
    photon_element[0]["energy_grid_offset"] = 0
    photon_element[0]["compton_offset"] = N
    photon_element[0]["pe_offset"] = 2 * N
    photon_element[0]["pair_offset"] = 3 * N

    return photon_element, data
