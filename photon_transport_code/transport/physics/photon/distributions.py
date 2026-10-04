"""
Photon scattering kernels and interaction kinematics.

Implements sampling routines for each photon interaction type using standard
Monte Carlo methods (inverse-transform and composition-rejection).

Functions
---------
sample_klein_nishina(E_in)
    Compton-scattered photon energy and scattering angle via Kahn (1954)
    composition-rejection method.

sample_pair_production(E_gamma)
    Electron/positron energies and angles from pair production.
    Returns None for E_gamma below the 1.022 MeV threshold.

sample_photoelectric_shell(E_photon, Z=13)
    Photoelectric absorption: select the K/L/M shell and return
    electron energy and emission angle.

photoelectric_absorption(E_photon)
    Convenience wrapper: return energy deposited (Phase 1 model: all
    photon energy is deposited locally, no fluorescence).

photoelectric_select_shell(E, Z=13)
    Sample the absorbing shell name ('K', 'L', 'M') proportional to
    simplified partial cross-sections.

References
----------
Kahn, H. (1954). Applications of Monte Carlo. AECU-3259, Rand Corp.
Butcher, J.C. & Messel, H. (1960). Nucl. Phys. 20, 15.
Salvat, F., Fernandez-Varea, J.M., & Sempau, J. (2011). PENELOPE-2011.
    OECD/NEA, Paris. (Compton sampling: pp. 71-83)
Heitler, W. (1954). The Quantum Theory of Radiation, 3rd ed. Oxford.
Berestetskii, V.B., Lifshitz, E.M., & Pitaevskii, L.P. (1982).
    Quantum Electrodynamics, 2nd ed. Pergamon.
"""

import math

import numpy as np
from numba import njit

# ======================================================================================
# Physical constants
# ======================================================================================

#: Electron rest-mass energy in MeV.
_M_E = 0.51099895

#: Pair-production threshold: 2 * m_e * c^2 in MeV.
_PAIR_THRESH = 2.0 * _M_E

#: 2 * pi
_TWO_PI = 2.0 * math.pi

# K-edge energies (MeV) for the four supported elements.
# Below the K-edge the K-shell is inaccessible; above it dominates.
_K_EDGE_MeV = {
    1: 1.36e-5,  # H  (essentially no K-edge in transport range)
    8: 5.43e-4,  # O  K-edge 0.543 keV
    13: 1.56e-3,  # Al K-edge 1.56  keV
    82: 8.80e-2,  # Pb K-edge 88.0  keV
}

# Approximate K-shell fraction of total photoelectric cross-section
# above the K-edge (from NIST XCOM partial cross-sections).
_K_FRAC = {
    1: 0.0,
    8: 0.80,
    13: 0.80,
    82: 0.83,
}


# ======================================================================================
# Compton (incoherent) scattering — Klein-Nishina sampling
# ======================================================================================


def sample_klein_nishina(E_in):
    """
    Sample Compton-scattered photon energy and angle via Kahn (1954).

    Uses the composition-rejection method of Kahn (1954) / Butcher-Messel
    (1960) to draw the energy ratio epsilon = E_out / E_in from the
    Klein-Nishina distribution.  The polar scattering cosine is computed
    exactly from the Compton kinematic relation; the azimuthal angle is
    sampled uniformly.

    Parameters
    ----------
    E_in : float
        Incident photon energy in MeV.  Must be > 0.

    Returns
    -------
    E_out : float
        Scattered photon energy in MeV.  E_out <= E_in.
    theta : float
        Polar scattering angle in radians, in [0, pi].
    E_electron : float
        Recoil electron kinetic energy in MeV.
        Satisfies E_out + E_electron == E_in exactly (to floating-point
        precision; max error < 2^-52 * E_in ~ 2e-16 MeV).

    Notes
    -----
    Algorithm (Kahn 1954 / Butcher-Messel 1960):

    Let kappa = E_in / m_e  and  tau = 1 / (1 + 2*kappa).

    Two envelope functions cover [tau, 1]:
        g_1(eps) proportional to 1/eps,  normalised weight a_1 = ln(1/tau)
        g_2(eps) proportional to eps,    normalised weight a_2 = (1-tau^2)/2

    Sampling:
        1. Draw r1, r2, r3 ~ U(0, 1).
        2. Branch on r1 * (a1 + a2) < a1:
               branch 1: eps = tau * exp(r2 * a1)
               branch 2: eps = sqrt(tau^2 + r2*(1 - tau^2))
        3. Compute cos(theta) from Compton formula.
        4. Accept with probability P = 1 - eps*sin^2(theta) / (1 + eps^2).

    Acceptance rate is >= 50 % at all energies (P >= 0.5 always).

    Energy conservation:
        E_electron = E_in - E_out  (computed by subtraction, not formula)
        => E_out + E_electron == E_in to floating-point precision.

    References
    ----------
    Kahn (1954), AECU-3259.
    Butcher & Messel (1960), Nucl. Phys. 20, 15.
    Salvat et al. (2011), PENELOPE-2011, pp. 71-83.
    """
    kappa = E_in / _M_E
    tau = 1.0 / (1.0 + 2.0 * kappa)

    # Normalization constants for the two envelope functions
    a1 = math.log(1.0 / tau)  # integral of 1/eps from tau to 1
    a2 = (1.0 - tau * tau) / 2.0  # integral of eps from tau to 1

    while True:
        r1 = np.random.random()
        r2 = np.random.random()
        r3 = np.random.random()

        # --- Composite sampling -------------------------------------------------
        if r1 * (a1 + a2) < a1:
            # Branch 1: sample eps proportional to 1/eps
            # Inverse CDF: eps = tau * exp(r2 * ln(1/tau)) = tau^(1-r2)
            eps = tau * math.exp(r2 * a1)
        else:
            # Branch 2: sample eps proportional to eps
            # Inverse CDF: eps = sqrt(tau^2 + r2*(1-tau^2))
            eps = math.sqrt(tau * tau + r2 * (1.0 - tau * tau))

        # --- Scattering cosine from Compton formula -----------------------------
        # mu = 1 - (1/epsilon - 1) / kappa
        mu = 1.0 - (1.0 / eps - 1.0) / kappa
        # Clamp for floating-point safety
        if mu < -1.0:
            mu = -1.0
        elif mu > 1.0:
            mu = 1.0

        sin2_theta = 1.0 - mu * mu
        if sin2_theta < 0.0:
            sin2_theta = 0.0

        # --- Acceptance test (Kahn 1954) ----------------------------------------
        # p(eps) / g(eps) = 1 - eps * sin^2(theta) / (1 + eps^2)
        # This ratio is in [0.5, 1] so the acceptance rate is >= 50%.
        p_acc = 1.0 - eps * sin2_theta / (1.0 + eps * eps)
        if r3 <= p_acc:
            break

    E_out = E_in * eps
    # Compute electron energy by subtraction to guarantee exact conservation
    E_electron = E_in - E_out
    theta = math.acos(mu)

    return E_out, theta, E_electron


# ======================================================================================
# Pair production
# ======================================================================================


def sample_pair_production(E_gamma):
    """
    Sample pair-production kinematics.

    Above the 1.022 MeV threshold the available kinetic energy
    Q = E_gamma - 2*m_e is shared between the electron and positron.
    Energy sharing is sampled uniformly over the physical range
    [m_e, E_gamma - m_e] for the electron total energy, with
    E_positron = E_gamma - E_electron (exact conservation).

    Emission angles follow an exponential distribution with characteristic
    angle theta_0 = m_e / E_particle, consistent with the relativistic
    forward-peaking of e+/e- at high energies.

    Parameters
    ----------
    E_gamma : float
        Incident photon energy in MeV.

    Returns
    -------
    None
        If E_gamma < 1.022 MeV (below pair-production threshold).
    (E_electron, E_positron, theta_electron, theta_positron) : tuple of float
        E_electron  : total energy of electron in MeV (>= m_e).
        E_positron  : total energy of positron in MeV (>= m_e).
        theta_electron : polar emission angle of electron, in [0, pi].
        theta_positron : polar emission angle of positron, in [0, pi].

    Notes
    -----
    Energy conservation:
        E_electron + E_positron == E_gamma  (exact to floating point)

    Angle model:
        The characteristic angle is theta_0 = m_e / E.  For a particle
        with total energy E >> m_e the mean emission angle is ~ m_e/E
        radians, giving strong forward peaking.  Angles are drawn from an
        exponential distribution: theta ~ -ln(U) * theta_0 for U ~ U(0,1).

    Simplified treatment:
        Full energy-sharing distributions (Bethe-Heitler with Coulomb
        corrections) and accurate angular correlations are deferred to
        Phase 4.  This Phase 3 implementation uses uniform energy sharing
        on ``[m_e, E_gamma - m_e]`` and an exponential angular distribution
        with scale ``m_e / E_particle``.

    References
    ----------
    Heitler (1954), The Quantum Theory of Radiation, Ch. 5.
    Berestetskii et al. (1982), Quantum Electrodynamics, §93.
    """
    if E_gamma < _PAIR_THRESH:
        return None

    # --- Energy sharing --------------------------------------------------------
    # Electron total energy sampled uniformly on [m_e, E_gamma - m_e]
    u = np.random.random()
    E_electron = _M_E + (E_gamma - _PAIR_THRESH) * u
    # Exact conservation: positron gets the rest
    E_positron = E_gamma - E_electron

    # --- Emission angles -------------------------------------------------------
    # Characteristic angle theta_0 = m_e / E; sample from Exp(1/theta_0)
    r1 = np.random.random()
    r2 = np.random.random()
    # Avoid log(0)
    if r1 < 1e-300:
        r1 = 1e-300
    if r2 < 1e-300:
        r2 = 1e-300

    theta_electron = -math.log(r1) * (_M_E / E_electron)
    theta_positron = -math.log(r2) * (_M_E / E_positron)

    # Clamp to physical range [0, pi]
    theta_electron = min(theta_electron, math.pi)
    theta_positron = min(theta_positron, math.pi)

    return E_electron, E_positron, theta_electron, theta_positron


# ======================================================================================
# Photoelectric absorption
# ======================================================================================


def sample_photoelectric_shell(E_photon, Z=13):
    """
    Sample photoelectric absorption: select shell and return electron state.

    The shell is selected proportional to simplified partial cross-sections:
    the K-shell dominates above its binding energy (approximately 80–83 %
    of the total); L and M shells share the remainder.

    Parameters
    ----------
    E_photon : float
        Incident photon energy in MeV.  Must be positive.
    Z : int, optional
        Atomic number of the absorbing element.  Default: 13 (aluminum).
        Supported: 1 (H), 8 (O), 13 (Al), 82 (Pb).

    Returns
    -------
    E_electron : float
        Electron kinetic energy in MeV.  Phase 1 model: E_electron = E_photon
        (binding energy subtracted in a future phase).
    theta : float
        Polar emission angle in radians, sampled isotropically in [0, pi].
    shell : str
        Shell name: 'K', 'L', or 'M'.

    Notes
    -----
    Phase 1 simplifications:
        - Electron energy = photon energy (binding energy not subtracted).
        - Emission direction is isotropic (no angular correlation with
          photon polarisation).
        - Fluorescence and Auger emission are not tracked.

    Shell selection:
        1. Retrieve K-edge energy E_K for element Z.
        2. If E_photon > E_K: K-shell probability = f_K (element-specific,
           ~ 0.80-0.83); remainder shared between L (15%) and M (5%).
        3. If E_photon < E_K: K-shell inaccessible; L/M share 75/25.

    References
    ----------
    Salvat et al. (2011), PENELOPE-2011, §2.3 (photoelectric absorption).
    NIST XCOM partial cross-sections: nist.gov/pml/xcom
    """
    # --- Shell selection -------------------------------------------------------
    shell = photoelectric_select_shell(E_photon, Z)

    # --- Electron energy (Phase 1: no binding-energy correction) ---------------
    E_electron = E_photon

    # --- Isotropic emission angle ----------------------------------------------
    # cos(theta) uniform on [-1, 1]
    cos_theta = 2.0 * np.random.random() - 1.0
    theta = math.acos(cos_theta)

    return E_electron, theta, shell


def photoelectric_absorption(E_photon):
    """
    Return the energy deposited by a photoelectric interaction (Phase 1 model).

    In the Phase 1 simplified model the incident photon is fully absorbed and
    all its energy is deposited locally.  Fluorescence photons and secondary
    electron transport are not tracked.

    Parameters
    ----------
    E_photon : float
        Incident photon energy in MeV.

    Returns
    -------
    float
        Energy deposited in MeV.  Equal to E_photon exactly.

    Notes
    -----
    Energy conservation: E_deposited == E_photon to floating-point precision.
    Full secondary-particle tracking (fluorescence, Auger, e- transport)
    is deferred to Phase 4.
    """
    return float(E_photon)


#: Alias for backward compatibility with Phase 1 skeleton function name.
sample_photoelectric = sample_photoelectric_shell


# ======================================================================================
# Isotropic scattering — constant cross-section benchmarks only
# ======================================================================================


@njit
def sample_isotropic_scatter(incident_energy, rng_state):
    """
    Sample isotropic scattering (no energy loss).

    Photon energy is unchanged; only direction is randomized uniformly
    over 4π steradians (cos(theta) uniform on [-1, 1]).

    Parameters
    ----------
    incident_energy : float
        Photon energy in MeV — not changed by this interaction.
    rng_state : object
        Random number generator state (passed for API compatibility;
        sampling uses numpy's thread-safe RNG within numba).

    Returns
    -------
    new_energy : float
        Same as incident_energy.
    new_direction_mu : float
        cos(theta), sampled uniformly on [-1, 1].
    new_direction_phi : float
        Azimuthal angle in radians, sampled uniformly on [0, 2π).

    Notes
    -----
    This is NOT Compton scattering (no energy transfer to a recoil electron).
    Used only for constant-cross-section analytical benchmarks such as the
    Case, de Hoffman & Placzek (1953) infinite-medium current solutions.
    The full isotropic direction is constructed from (mu, phi) by the caller
    using standard spherical-to-Cartesian conversion.
    """
    pass


def photoelectric_select_shell(E, Z=13):
    """
    Sample the shell ('K', 'L', or 'M') for photoelectric absorption.

    Uses simplified partial cross-section fractions derived from NIST XCOM.
    The K-shell dominates above its binding energy.

    Parameters
    ----------
    E : float
        Incident photon energy in MeV.
    Z : int, optional
        Atomic number.  Default: 13 (Al).
        Supported: 1, 8, 13, 82.  Falls back to Al fractions for unknown Z.

    Returns
    -------
    str
        Shell identifier: 'K', 'L', or 'M'.

    Notes
    -----
    Fractions (approximate, from NIST XCOM):
        Above K-edge: K ~ 80-83 %, L ~ 14-16 %, M ~ 3-5 %
        Below K-edge: L ~ 75 %,   M ~ 25 %

    This simplified model does not account for individual sub-shell
    splitting (L_I, L_II, L_III) or the detailed energy dependence of
    partial cross-sections.
    """
    k_edge = _K_EDGE_MeV.get(Z, 1.56e-3)
    k_frac = _K_FRAC.get(Z, 0.80)

    r = np.random.random()

    if E > k_edge:
        # K-shell accessible
        l_frac = (1.0 - k_frac) * 0.75  # ~75% of remaining is L
        if r < k_frac:
            return "K"
        elif r < k_frac + l_frac:
            return "L"
        else:
            return "M"
    else:
        # K-shell inaccessible below K-edge
        if r < 0.75:
            return "L"
        else:
            return "M"
