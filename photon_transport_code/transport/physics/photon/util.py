"""
Photon physics helper functions and constants.

Provides numerical utilities and physical constants used across the photon
transport module.  Mirrors mcdc/transport/physics/util.py in role.

All computational helpers are @njit decorated so they can be called from
other JIT-compiled functions.  Pure Python module-level constants are
defined as floats (not @njit) so they are available at import time.

Physical constants (SI, then converted to MCDC units MeV / cm):
    ELECTRON_REST_MASS_ENERGY  = 0.51099895 MeV  (m_e c^2)
    CLASSICAL_ELECTRON_RADIUS  = 2.8179403e-13 cm (r_e)
    THOMSON_CROSS_SECTION      = 6.6524587e-25 cm^2  (sigma_T = (8/3)*pi*r_e^2)
    PAIR_PRODUCTION_THRESHOLD  = 1.02199790 MeV  (2 * m_e c^2)
    FINE_STRUCTURE_CONSTANT    = 7.2973526e-3    (alpha ~ 1/137)
"""

import math

from numba import njit

# ======================================================================================
# Module-level physical constants (MeV, cm)
# ======================================================================================

#: Electron rest-mass energy in MeV.
ELECTRON_REST_MASS_ENERGY = 0.51099895

#: Classical electron radius in cm.
CLASSICAL_ELECTRON_RADIUS = 2.8179403e-13

#: Thomson cross-section in cm^2.  = (8/3) * pi * r_e^2
THOMSON_CROSS_SECTION = (8.0 / 3.0) * math.pi * CLASSICAL_ELECTRON_RADIUS**2

#: Pair production threshold energy in MeV.  = 2 * m_e * c^2
PAIR_PRODUCTION_THRESHOLD = 2.0 * ELECTRON_REST_MASS_ENERGY

#: Fine structure constant (dimensionless).
FINE_STRUCTURE_CONSTANT = 7.2973526e-3

#: Avogadro's number in mol^-1.
AVOGADRO = 6.02214076e23

#: Conversion: 1 barn = 1e-24 cm^2.
BARN_PER_CM2 = 1.0e24


# ======================================================================================
# Compton kinematics
# ======================================================================================


@njit
def compton_scattered_energy(E_in, mu):
    """
    Compute the Compton-scattered photon energy.

    Parameters
    ----------
    E_in : float
        Incident photon energy in MeV.
    mu : float
        Cosine of the photon scattering angle theta, in [-1, 1].

    Returns
    -------
    float
        Scattered photon energy E' in MeV.

    Notes
    -----
    Compton formula:
        E' = E / (1 + kappa * (1 - mu))

    where kappa = E / (m_e * c^2) = E / 0.511.

    At mu = 1 (forward scatter) E' = E (no energy loss).
    At mu = -1 (back scatter)   E' = E / (1 + 2*kappa).
    """
    kappa = E_in / 0.51099895
    return E_in / (1.0 + kappa * (1.0 - mu))


@njit
def compton_scattering_cosine(E_in, E_out):
    """
    Compute the Compton scattering cosine from incident and scattered energies.

    Parameters
    ----------
    E_in : float
        Incident photon energy in MeV.
    E_out : float
        Scattered photon energy in MeV.

    Returns
    -------
    float
        Cosine of the scattering angle mu, in [-1, 1].

    Notes
    -----
    Inverted Compton formula:
        mu = 1 - (1/kappa) * (E_in/E_out - 1)

    where kappa = E_in / 0.511.
    """
    kappa = E_in / 0.51099895
    return 1.0 - (1.0 / kappa) * (E_in / E_out - 1.0)


# ======================================================================================
# Energy/threshold helpers
# ======================================================================================


@njit
def pair_production_threshold():
    """
    Return the pair production threshold energy.

    Parameters
    ----------
    None

    Returns
    -------
    float
        Threshold energy 2 * m_e * c^2 = 1.022 MeV.

    Notes
    -----
    Below this energy pair production cannot occur kinematically.
    """
    return 2.0 * 0.51099895


@njit
def electron_rest_mass_energy():
    """
    Return the electron rest-mass energy.

    Parameters
    ----------
    None

    Returns
    -------
    float
        Electron rest-mass energy m_e * c^2 = 0.511 MeV.
    """
    return 0.51099895


# ======================================================================================
# Numerical utilities
# ======================================================================================


@njit
def log_log_interpolation(x, x0, x1, y0, y1):
    """
    Perform log-log linear interpolation between two tabulated points.

    Parameters
    ----------
    x : float
        Query point (e.g., energy in MeV).  Must be in (x0, x1].
    x0 : float
        Lower tabulated abscissa value.  Must be > 0.
    x1 : float
        Upper tabulated abscissa value.  Must be > x0.
    y0 : float
        Tabulated ordinate at x0 (e.g., cross-section).  Must be > 0.
    y1 : float
        Tabulated ordinate at x1.  Must be > 0.

    Returns
    -------
    float
        Interpolated value at x.

    Notes
    -----
    Formula:
        log(y) = log(y0) + [log(y1/y0) / log(x1/x0)] * log(x/x0)

    Equivalent to a power-law interpolation y = y0 * (x/x0)^alpha where
    alpha = log(y1/y0) / log(x1/x0).  Appropriate for photon cross-sections
    which are smooth power-law functions between shell edges.
    """
    if y0 <= 0.0 or y1 <= 0.0:
        # Linear fallback when cross-section passes through zero
        t = (x - x0) / (x1 - x0)
        return y0 + t * (y1 - y0)
    log_x0 = math.log(x0)
    log_x1 = math.log(x1)
    log_y0 = math.log(y0)
    log_y1 = math.log(y1)
    alpha = (log_y1 - log_y0) / (log_x1 - log_x0)
    return math.exp(log_y0 + alpha * (math.log(x) - log_x0))


@njit
def scatter_direction(ux, uy, uz, mu, azi):
    """
    Rotate a direction vector (ux, uy, uz) by polar cosine mu and azimuth azi.

    Parameters
    ----------
    ux : float
        x-component of the incident direction unit vector.
    uy : float
        y-component of the incident direction unit vector.
    uz : float
        z-component of the incident direction unit vector.
    mu : float
        Cosine of the polar scattering angle.
    azi : float
        Azimuthal scattering angle in radians, sampled uniformly in [0, 2*pi].

    Returns
    -------
    ux_new : float
        x-component of the post-scatter direction unit vector.
    uy_new : float
        y-component of the post-scatter direction unit vector.
    uz_new : float
        z-component of the post-scatter direction unit vector.

    Notes
    -----
    Uses the standard rotation formula from mcdc/transport/physics/util.py::
    scatter_direction, reproduced here for self-contained use within the
    photon module (avoids cross-package import in JIT context).

    If uz == 1.0 the y and z axes are interchanged to avoid division by zero.
    """
    sin_theta = math.sqrt(max(0.0, 1.0 - mu * mu))
    cos_azi = math.cos(azi)
    sin_azi = math.sin(azi)

    if abs(uz) < 1.0 - 1e-10:
        sin_polar = math.sqrt(max(0.0, 1.0 - uz * uz))
        ux_new = mu * ux + sin_theta * (ux * uz * cos_azi - uy * sin_azi) / sin_polar
        uy_new = mu * uy + sin_theta * (uy * uz * cos_azi + ux * sin_azi) / sin_polar
        uz_new = mu * uz - sin_theta * sin_polar * cos_azi
    else:
        ux_new = sin_theta * cos_azi
        uy_new = sin_theta * sin_azi
        uz_new = mu * (1.0 if uz > 0.0 else -1.0)

    return ux_new, uy_new, uz_new
