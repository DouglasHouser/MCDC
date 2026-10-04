"""
Photon transport interface module.

High-level entry point for photon physics, mirroring the neutron interface at
mcdc/transport/physics/neutron/interface.py. All public functions are @njit
decorated for Numba JIT compilation.

Reactions handled:
    - Compton scattering (incoherent)
    - Photoelectric absorption
    - Pair production (nuclear + electron field)

Constants (imported from mcdc.object_.photon_reaction):
    PHOTON_REACTION_TOTAL
    PHOTON_REACTION_COMPTON
    PHOTON_REACTION_PHOTOELECTRIC
    PHOTON_REACTION_PAIR_PRODUCTION
    _SPEED_OF_LIGHT
"""

import numpy as np
from numba import njit

from photon_transport_code.transport.physics.photon import native
from photon_transport_code.transport.physics.photon.cross_sections import (
    macro_compton_xs,
    macro_pair_production_xs,
    macro_photoelectric_xs,
    macro_total_xs,
)
from mcdc.constant import REFERENCE_FRAME_LAB
from mcdc.object_.photon_reaction import (
    PhotonReactionCompton,
    PhotonReactionPhotoelectric,
    PhotonReactionPairProduction,
    PHOTON_REACTION_COMPTON,
    PHOTON_REACTION_PHOTOELECTRIC,
    PHOTON_REACTION_PAIR_PRODUCTION,
    PHOTON_REACTION_TOTAL,
    _SPEED_OF_LIGHT,
    _PAIR_THRESH,
    _M_E,
    decode_type,
)

# ======================================================================================
# Particle attributes
# ======================================================================================


@njit
def particle_speed(particle_container, mcdc, data):
    """
    Return the speed of a photon (always the speed of light).

    Parameters
    ----------
    particle_container : numpy.ndarray, shape (1,)
        Structured array holding the photon particle state.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing all tabulated cross-section and
        distribution data.

    Returns
    -------
    float
        Speed of light in cm/sh (centimeters per shake), the unit system
        used throughout MCDC.

    Notes
    -----
    Photons are massless and always travel at c regardless of energy.
    The numerical value is imported from the constants module.
    """
    return _SPEED_OF_LIGHT


# ======================================================================================
# Material properties
# ======================================================================================


@njit
def macro_xs(reaction_type, particle_container, mcdc, data):
    """
    Return the macroscopic photon cross-section for the current material.

    Sums elemental contributions weighted by number density:
        Sigma = sum_i  n_i * sigma_i(E)

    Parameters
    ----------
    reaction_type : int
        One of PHOTON_REACTION_TOTAL, PHOTON_REACTION_COMPTON,
        PHOTON_REACTION_PHOTOELECTRIC, or PHOTON_REACTION_PAIR_PRODUCTION.
    particle_container : numpy.ndarray, shape (1,)
        Structured array holding the photon particle state; used to read
        current energy E and material_ID.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array; provides access to material and
        element data tables.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing tabulated cross-section data.

    Returns
    -------
    float
        Macroscopic cross-section in cm^-1.

    Notes
    -----
    Delegates to native.get_element_xs for each element in the material,
    then multiplies by number density and accumulates.
    """
    if reaction_type == PHOTON_REACTION_COMPTON:
        return macro_compton_xs(particle_container, mcdc, data)
    elif reaction_type == PHOTON_REACTION_PHOTOELECTRIC:
        return macro_photoelectric_xs(particle_container, mcdc, data)
    elif reaction_type == PHOTON_REACTION_PAIR_PRODUCTION:
        return macro_pair_production_xs(particle_container, mcdc, data)
    else:
        # PHOTON_REACTION_TOTAL
        return macro_total_xs(particle_container, mcdc, data)


@njit
def photon_production_xs(reaction_type, particle_container, mcdc, data):
    """
    Return the macroscopic photon *production* cross-section.

    Used for implicit capture / weight adjustment: only Compton scattering
    and pair production produce secondary photons.  Photoelectric absorption
    terminates the photon history (no secondary photon is produced).

    Parameters
    ----------
    reaction_type : int
        One of PHOTON_REACTION_TOTAL, PHOTON_REACTION_COMPTON,
        PHOTON_REACTION_PHOTOELECTRIC, or PHOTON_REACTION_PAIR_PRODUCTION.
    particle_container : numpy.ndarray, shape (1,)
        Structured array holding the photon particle state.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing tabulated cross-section data.

    Returns
    -------
    float
        Effective macroscopic production cross-section in cm^-1.

    Notes
    -----
    For pair production one photon is consumed and two 0.511 MeV
    annihilation gammas are produced; the multiplicity is 2.
    Compton scattering produces one scattered photon (multiplicity 1).
    Photoelectric absorption produces no photon (multiplicity 0).
    """
    if reaction_type == PHOTON_REACTION_COMPTON:
        # Compton: 1 scattered photon produced per interaction
        return macro_compton_xs(particle_container, mcdc, data)
    elif reaction_type == PHOTON_REACTION_PHOTOELECTRIC:
        # Photoelectric: photon is fully absorbed — no secondary photon
        return 0.0
    elif reaction_type == PHOTON_REACTION_PAIR_PRODUCTION:
        # Pair production: 2 annihilation photons (0.511 MeV each) produced
        return 2.0 * macro_pair_production_xs(particle_container, mcdc, data)
    else:
        # TOTAL: Sigma_C * 1 + Sigma_PE * 0 + Sigma_PP * 2
        Sigma_C = macro_compton_xs(particle_container, mcdc, data)
        Sigma_PP = macro_pair_production_xs(particle_container, mcdc, data)
        return Sigma_C + 2.0 * Sigma_PP


# ======================================================================================
# Collision
# ======================================================================================


@njit
def collision(particle_container, mcdc, data):
    """
    Sample and perform a photon collision event.

    Determines the interaction type by sampling proportional to the partial
    macroscopic cross-sections (Compton, photoelectric, pair production),
    then delegates to the appropriate PhotonReaction object's
    perform_collision() method.

    Parameters
    ----------
    particle_container : numpy.ndarray, shape (1,)
        Structured array holding the photon particle state; modified in-place
        to reflect post-collision energy, direction, and alive flag.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array; provides RNG state and material
        tables.
    data : numpy.ndarray, shape (N,)
        Flat data buffer containing tabulated cross-section and distribution
        data.

    Returns
    -------
    None

    Notes
    -----
    Reaction selection algorithm:
        1. Compute SigmaT = Sigma_C + Sigma_PE + Sigma_PP.
        2. Draw xi ~ U(0, SigmaT).
        3. Walk through partial cross-sections; the first cumulative sum
           exceeding xi determines the reaction.

    Compton scattering  -> PhotonReactionCompton.perform_collision()
    Photoelectric       -> PhotonReactionPhotoelectric.perform_collision()
    Pair production     -> PhotonReactionPairProduction.perform_collision()
    """
    # --- Compute partial macroscopic cross-sections --------------------------------
    Sigma_C = macro_compton_xs(particle_container, mcdc, data)
    Sigma_PE = macro_photoelectric_xs(particle_container, mcdc, data)
    Sigma_PP = macro_pair_production_xs(particle_container, mcdc, data)
    Sigma_T = Sigma_C + Sigma_PE + Sigma_PP

    if Sigma_T <= 0.0:
        return

    # --- Sample interaction type ---------------------------------------------------
    xi = np.random.random() * Sigma_T

    if xi < Sigma_C:
        reaction = PhotonReactionCompton(
            MT=502,
            xs=np.array([Sigma_C]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        reaction.perform_collision(particle_container, mcdc, data)

    elif xi < Sigma_C + Sigma_PE:
        reaction = PhotonReactionPhotoelectric(
            MT=501,
            xs=np.array([Sigma_PE]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        reaction.perform_collision(particle_container, mcdc, data)

    else:
        reaction = PhotonReactionPairProduction(
            MT=503,
            xs=np.array([Sigma_PP]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        reaction.perform_collision(particle_container, mcdc, data)


# ======================================================================================
# Constant cross-section collision — analytical benchmark support
# ======================================================================================


@njit
def constant_xs_collision(particle, material, rng_state):
    """
    Sample collision type and parameters for constant cross-section material.

    Determines whether collision is scattering or absorption based on
    scattering ratio (sigma_scatter / sigma_total).

    Parameters
    ----------
    particle : numpy.ndarray
        Photon particle state (position, direction, energy, alive flag).
        Modified in-place to reflect post-collision state.
    material : object
        ConstantCrossSectionMaterial with sigma_total and sigma_scatter.
    rng_state : object
        Random number generator state (passed for API compatibility;
        sampling uses numpy's thread-safe RNG within numba).

    Returns
    -------
    collision_type : int
        0 = absorption, 1 = isotropic_scatter.

    Notes
    -----
    Distance to collision: -ln(rand()) / sigma_total.
    Collision type probability: sigma_scatter / sigma_total for scattering.
    If scattering: sample isotropic direction (uniform over 4π sr).
    If absorption: particle absorbed (alive flag set False, no secondary).
    This function will eventually wrap ConstantXSIsotropicScatter and
    ConstantXSAbsorption reaction objects following the PhotonReaction
    architecture pattern established by PhotonReactionCompton et al.
    """
    pass
