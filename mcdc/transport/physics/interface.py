import math

from numba import njit

###

import mcdc.transport.rng as rng
import mcdc.transport.physics.neutron as neutron
import mcdc.transport.physics.photon as photon

from mcdc.constant import *

# ======================================================================================
# Particle attributes
# ======================================================================================


@njit
def particle_speed(particle_container, mcdc, data):
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_NEUTRON:
        return neutron.particle_speed(particle_container, mcdc, data)
    elif particle["particle_type"] == PARTICLE_PHOTON:
        return photon.particle_speed(particle_container, mcdc, data)
    return -1.0


# ======================================================================================
# Material properties
# ======================================================================================


@njit
def macro_xs(reaction_type, particle_container, mcdc, data):
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_NEUTRON:
        return neutron.macro_xs(reaction_type, particle_container, mcdc, data)
    elif particle["particle_type"] == PARTICLE_PHOTON:
        return photon.macro_xs(reaction_type, particle_container, mcdc, data)
    return -1.0


@njit
def neutron_production_xs(reaction_type, particle_container, mcdc, data):
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_NEUTRON:
        return neutron.neutron_production_xs(
            reaction_type, particle_container, mcdc, data
        )
    elif particle["particle_type"] == PARTICLE_PHOTON:
        return photon.photon_production_xs(
            reaction_type, particle_container, mcdc, data
        )
    return -1.0


# ======================================================================================
# Collision
# ======================================================================================


@njit
def collision_distance(particle_container, mcdc, data):
    # Get total cross-section — reaction constant differs by particle type
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_PHOTON:
        reaction_total = PHOTON_REACTION_TOTAL
    else:
        reaction_total = NEUTRON_REACTION_TOTAL
    SigmaT = macro_xs(reaction_total, particle_container, mcdc, data)

    # Vacuum material?
    if SigmaT == 0.0:
        return INF

    # Sample collision distance
    xi = rng.lcg(particle_container)
    distance = -math.log(xi) / SigmaT
    return distance


@njit
def collision(particle_container, mcdc, data):
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_NEUTRON:
        neutron.collision(particle_container, mcdc, data)
        return 0.0  # neutrons: unchanged, no deposition tally
    elif particle["particle_type"] == PARTICLE_PHOTON:
        return photon.collision(particle_container, mcdc, data)
    return 0.0
