from numba import njit

####

import mcdc.transport.physics.proton.condensed_history as proton
import mcdc.transport.util as util

from mcdc.constant import PARTICLE_PROTON


@njit
def distance(particle_container, simulation, data):
    """Return the maximum condensed-history step length for the particle."""
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_PROTON:
        return proton.distance(particle_container, simulation, data)
    raise ValueError(
        "Condensed history not supported for "
        + util.particle_name(particle["particle_type"])
    )


@njit
def apply(particle_container, collision_data_container, distance, simulation, data):
    """Apply condensed interactions over the traveled distance."""
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_PROTON:
        proton.apply(
            particle_container, collision_data_container, distance, simulation, data
        )
    else:
        raise ValueError(
            "Condensed history not supported for "
            + util.particle_name(particle["particle_type"])
        )
