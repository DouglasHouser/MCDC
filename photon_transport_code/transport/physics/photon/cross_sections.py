"""
Photon cross-section calculations.

Implements all four photon interaction cross-sections:
    1. Compton (incoherent) scattering  -- Klein-Nishina formula
    2. Photoelectric absorption          -- tabulated NIST XCOM data
    3. Pair production                   -- tabulated NIST XCOM data
    4. Total cross-section               -- sum of above

All @njit functions operate on scalar energies and structured arrays
following the same conventions as mcdc/transport/physics/neutron/native.py.

References
----------
Klein, O. & Nishina, Y. (1929). Z. Phys. 52, 853-868.
NIST XCOM: https://www.nist.gov/pml/xcom
Hubbell, J.H. & Seltzer, S.M. (2004). Tables of X-Ray Mass Attenuation
    Coefficients, NIST Standard Reference Database 126.
Evans, R.D. (1955). The Atomic Nucleus. McGraw-Hill, New York.
"""

import math

from numba import njit

from photon_transport_code.transport.physics.photon import native, util

# Physical constants inlined for @njit compatibility
_R_E = 2.8179403e-13  # classical electron radius [cm]
_M_E = 0.51099895  # electron rest mass [MeV]
_PAIR_THRESH = 2.0 * _M_E  # pair production threshold [MeV]


# ======================================================================================
# Klein-Nishina (Compton) cross-sections
# ======================================================================================


@njit
def klein_nishina_total(E):
    """
    Compute the total Klein-Nishina Compton cross-section per electron.

    Uses the closed-form integration of the Klein-Nishina differential
    cross-section over all scattering angles.

    Parameters
    ----------
    E : float
        Incident photon energy in MeV.

    Returns
    -------
    float
        Total Compton cross-section per electron in cm^2/electron.

    Notes
    -----
    The dimensionless parameter alpha = E / (m_e * c^2) = E / 0.511.
    The formula (Evans 1955, p. 685) is::

        sigma_KN = 2*pi*r_e^2 * {
            [(1+alpha)/alpha^3] * [2*alpha*(1+alpha)/(1+2*alpha) - ln(1+2*alpha)]
            + ln(1+2*alpha)/(2*alpha)
            - (1+3*alpha)/(1+2*alpha)^2
        }

    where r_e = 2.8179e-13 cm is the classical electron radius.

    At low energies (alpha -> 0) sigma_KN -> sigma_T = (8/3)*pi*r_e^2 (Thomson).
    At high energies (alpha -> inf) sigma_KN ~ (ln(2*alpha) + 1/2) / alpha.

    References
    ----------
    Evans (1955), The Atomic Nucleus, p. 685.
    Klein & Nishina (1929), Z. Phys. 52, 853.
    """
    alpha = E / _M_E
    pi = math.pi
    r_e = _R_E

    if alpha < 1e-3:
        # Thomson limit avoids catastrophic cancellation in the formula
        return (8.0 / 3.0) * pi * r_e * r_e

    a2 = 2.0 * alpha
    one_plus_a2 = 1.0 + a2
    ln_term = math.log(one_plus_a2)

    term1 = ((1.0 + alpha) / (alpha * alpha * alpha)) * (
        a2 * (1.0 + alpha) / one_plus_a2 - ln_term
    )
    term2 = ln_term / a2
    term3 = (1.0 + 3.0 * alpha) / (one_plus_a2 * one_plus_a2)

    return 2.0 * pi * r_e * r_e * (term1 + term2 - term3)


@njit
def klein_nishina_differential(E, mu):
    """
    Compute the differential Klein-Nishina cross-section d(sigma)/d(Omega).

    Parameters
    ----------
    E : float
        Incident photon energy in MeV.
    mu : float
        Cosine of the scattering angle (polar), in [-1, 1].

    Returns
    -------
    float
        Differential cross-section d(sigma)/d(Omega) in cm^2/sr/electron.

    Notes
    -----
    The Klein-Nishina formula:

        d(sigma)/d(Omega) = (r_e^2 / 2) * (E'/E)^2 * (E/E' + E'/E - sin^2(theta))

    where E' = E / (1 + alpha*(1 - mu)) is the scattered photon energy,
    alpha = E / 0.511, and sin^2(theta) = 1 - mu^2.

    References
    ----------
    Klein & Nishina (1929), Z. Phys. 52, 853.
    """
    alpha = E / _M_E
    E_prime = E / (1.0 + alpha * (1.0 - mu))
    ratio = E_prime / E
    sin2_theta = 1.0 - mu * mu
    return 0.5 * _R_E * _R_E * ratio * ratio * (1.0 / ratio + ratio - sin2_theta)


# ======================================================================================
# Photoelectric cross-sections
# ======================================================================================


@njit
def photoelectric_xs(Z, E, data):
    """
    Return the photoelectric cross-section for element Z at energy E.

    Uses log-log interpolation on tabulated NIST XCOM data stored in the
    flat data buffer.

    Parameters
    ----------
    Z : int
        Atomic number of the element (informational only).
    E : float
        Incident photon energy in MeV.
    data : numpy.ndarray, shape (4*N,)
        Flat data buffer laid out as [energy_grid(N) | compton(N) | pe(N) | pair(N)].

    Returns
    -------
    float
        Photoelectric cross-section per atom in cm^2/atom.

    Notes
    -----
    Shell-edge discontinuities are preserved: the NIST table includes paired
    energy entries at each K-edge (just below and just above), so log-log
    interpolation naturally steps across the discontinuity.

    Energy range: 1 keV to 100 MeV (NIST XCOM).
    """
    N = len(data) // 4
    eg_off = 0
    pe_off = 2 * N
    return native.interpolate_xs(E, eg_off, pe_off, N, data)


# ======================================================================================
# Pair production cross-sections
# ======================================================================================


@njit
def pair_production_xs(Z, E, data):
    """
    Return the pair production cross-section for element Z at energy E.

    Combines nuclear-field and electron-field (triplet) contributions using
    tabulated NIST XCOM data.

    Parameters
    ----------
    Z : int
        Atomic number of the element.
    E : float
        Incident photon energy in MeV.  Returns 0.0 for E < 1.022 MeV.
    data : numpy.ndarray, shape (4*N,)
        Flat data buffer laid out as [energy_grid | compton | pe | pair].

    Returns
    -------
    float
        Pair production cross-section per atom in cm^2/atom.
        Returns 0.0 for E < 1.022 MeV (below threshold).

    Notes
    -----
    Threshold energy: E_threshold = 2 * m_e * c^2 = 1.02199790 MeV.
    This is a hard zero — no approximation or rounding applied at threshold.

    References
    ----------
    NIST XCOM: https://www.nist.gov/pml/xcom
    Bethe & Heitler (1934), Proc. R. Soc. London A 146, 83.
    """
    if E < _PAIR_THRESH:
        return 0.0
    N = len(data) // 4
    eg_off = 0
    pair_off = 3 * N
    return native.interpolate_xs(E, eg_off, pair_off, N, data)


# ======================================================================================
# Total photon cross-section
# ======================================================================================


@njit
def total_xs(Z, E, data):
    """
    Return the total photon cross-section for element Z at energy E.

    Sum of Compton (Klein-Nishina * Z), photoelectric, and pair production
    cross-sections.

    Parameters
    ----------
    Z : int
        Atomic number of the element.
    E : float
        Incident photon energy in MeV.
    data : numpy.ndarray, shape (4*N,)
        Flat data buffer laid out as [energy_grid | compton | pe | pair].

    Returns
    -------
    float
        Total photon cross-section per atom in cm^2/atom.

    Notes
    -----
    Coherent (Rayleigh) scattering is neglected in this implementation.
    Compton contribution is computed analytically (Klein-Nishina * Z);
    photoelectric and pair production use tabulated NIST XCOM data.
    """
    sigma_C = klein_nishina_total(E) * float(Z)
    sigma_PE = photoelectric_xs(Z, E, data)
    sigma_PP = pair_production_xs(Z, E, data)
    return sigma_C + sigma_PE + sigma_PP


# ======================================================================================
# Structured-array variants (use photon_element offsets directly)
# ======================================================================================


@njit
def photoelectric_xs_element(Z, E, photon_element, flat_data):
    """
    Compute photoelectric cross-section using photon_element structured array.

    Parameters
    ----------
    Z : int
        Atomic number of the element.
    E : float
        Incident photon energy in MeV.
    photon_element : numpy.ndarray (structured), shape (1,)
        Structured array with offset fields; see native.PHOTON_ELEMENT_DTYPE.
    flat_data : numpy.ndarray, shape (N,)
        Flat data buffer.

    Returns
    -------
    float
        Photoelectric cross-section per atom in cm^2/atom.
    """
    N = photon_element[0]["N_points"]
    eg_off = photon_element[0]["energy_grid_offset"]
    pe_off = photon_element[0]["pe_offset"]
    return native.interpolate_xs(E, eg_off, pe_off, N, flat_data)


@njit
def pair_production_xs_element(Z, E, photon_element, flat_data):
    """
    Compute pair production cross-section using photon_element structured array.

    Parameters
    ----------
    Z : int
        Atomic number of the element.
    E : float
        Incident photon energy in MeV.
    photon_element : numpy.ndarray (structured), shape (1,)
        Structured array with offset fields.
    flat_data : numpy.ndarray, shape (N,)
        Flat data buffer.

    Returns
    -------
    float
        Pair production cross-section per atom in cm^2/atom.
        Returns 0.0 for E < 1.022 MeV.
    """
    if E < _PAIR_THRESH:
        return 0.0
    N = photon_element[0]["N_points"]
    eg_off = photon_element[0]["energy_grid_offset"]
    pair_off = photon_element[0]["pair_offset"]
    return native.interpolate_xs(E, eg_off, pair_off, N, flat_data)


@njit
def total_xs_element(Z, E, photon_element, flat_data):
    """
    Compute total photon cross-section using photon_element structured array.

    Parameters
    ----------
    Z : int
        Atomic number of the element.
    E : float
        Incident photon energy in MeV.
    photon_element : numpy.ndarray (structured), shape (1,)
        Structured array with offset fields.
    flat_data : numpy.ndarray, shape (N,)
        Flat data buffer.

    Returns
    -------
    float
        Total cross-section per atom in cm^2/atom.
    """
    sigma_C = klein_nishina_total(E) * float(Z)
    sigma_PE = photoelectric_xs_element(Z, E, photon_element, flat_data)
    sigma_PP = pair_production_xs_element(Z, E, photon_element, flat_data)
    return sigma_C + sigma_PE + sigma_PP


# ======================================================================================
# Macroscopic cross-sections (material level)
# ======================================================================================


@njit
def macro_compton_xs(particle_container, mcdc, data):
    """
    Compute the macroscopic Compton cross-section for the current material.

    Parameters
    ----------
    particle_container : numpy.ndarray, shape (1,)
        Structured array holding the photon particle state; reads E and
        material_ID.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array; provides element tables and
        number densities.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing tabulated cross-section data.

    Returns
    -------
    float
        Macroscopic Compton cross-section Sigma_C in cm^-1.

    Notes
    -----
    Compton cross-section per atom uses Klein-Nishina per-electron times
    the number of electrons per atom (Z).  The macroscopic value sums over
    all elements i:  Sigma_C = sum_i n_i * Z_i * sigma_KN(E).
    """
    E = particle_container[0]["E"]
    material_ID = particle_container[0]["material_ID"]
    material = mcdc[0]["materials"][material_ID]

    sigma_KN = klein_nishina_total(E)
    Sigma = 0.0
    for i in range(material[0]["N_nuclide"]):
        Z = material[0]["nuclides"][i]["Z"]
        n = material[0]["nuclides"][i]["N"]
        Sigma += n * sigma_KN * float(Z)
    return Sigma


@njit
def macro_photoelectric_xs(particle_container, mcdc, data):
    """
    Compute the macroscopic photoelectric cross-section for the current material.

    Parameters
    ----------
    particle_container : numpy.ndarray, shape (1,)
        Structured array holding the photon particle state; reads E and
        material_ID.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing tabulated photoelectric cross-sections.

    Returns
    -------
    float
        Macroscopic photoelectric cross-section Sigma_PE in cm^-1.
    """
    E = particle_container[0]["E"]
    material_ID = particle_container[0]["material_ID"]
    material = mcdc[0]["materials"][material_ID]

    Sigma = 0.0
    for i in range(material[0]["N_nuclide"]):
        n = material[0]["nuclides"][i]["N"]
        element = mcdc[0]["photon_elements"][i]
        N_pts = element[0]["N_points"]
        eg_off = element[0]["energy_grid_offset"]
        pe_off = element[0]["pe_offset"]
        sigma = native.interpolate_xs(E, eg_off, pe_off, N_pts, data)
        Sigma += n * sigma
    return Sigma


@njit
def macro_pair_production_xs(particle_container, mcdc, data):
    """
    Compute the macroscopic pair production cross-section for the current material.

    Parameters
    ----------
    particle_container : numpy.ndarray, shape (1,)
        Structured array holding the photon particle state; reads E and
        material_ID.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing tabulated pair production cross-sections.

    Returns
    -------
    float
        Macroscopic pair production cross-section Sigma_PP in cm^-1.
        Returns 0.0 for E < 1.022 MeV.
    """
    if particle_container[0]["E"] < _PAIR_THRESH:
        return 0.0

    E = particle_container[0]["E"]
    material_ID = particle_container[0]["material_ID"]
    material = mcdc[0]["materials"][material_ID]

    Sigma = 0.0
    for i in range(material[0]["N_nuclide"]):
        n = material[0]["nuclides"][i]["N"]
        element = mcdc[0]["photon_elements"][i]
        N_pts = element[0]["N_points"]
        eg_off = element[0]["energy_grid_offset"]
        pair_off = element[0]["pair_offset"]
        sigma = native.interpolate_xs(E, eg_off, pair_off, N_pts, data)
        Sigma += n * sigma
    return Sigma


@njit
def macro_total_xs(particle_container, mcdc, data):
    """
    Compute the total macroscopic photon cross-section for the current material.

    Parameters
    ----------
    particle_container : numpy.ndarray, shape (1,)
        Structured array holding the photon particle state.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing all tabulated cross-section data.

    Returns
    -------
    float
        Total macroscopic cross-section Sigma_T = Sigma_C + Sigma_PE + Sigma_PP
        in cm^-1.

    Notes
    -----
    Equivalent to calling macro_xs(PHOTON_REACTION_TOTAL, ...) from
    interface.py; provided here as a convenience for internal use.
    """
    return (
        macro_compton_xs(particle_container, mcdc, data)
        + macro_photoelectric_xs(particle_container, mcdc, data)
        + macro_pair_production_xs(particle_container, mcdc, data)
    )
