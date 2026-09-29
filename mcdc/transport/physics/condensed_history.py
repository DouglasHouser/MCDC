from numba import njit

####

import mcdc.transport.physics.proton as proton
import mcdc.transport.util as util

from mcdc.constant import PARTICLE_PROTON


@njit
def max_condensed_history_distance(particle_container, simulation, data):
    """Return the maximum condensed-history step length for the particle."""
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_PROTON:
        return proton.max_condensed_history_distance(
            particle_container, simulation, data
        )
    raise ValueError(
        "Condensed history not supported for "
        + util.particle_name(particle["particle_type"])
    )


@njit
def condensed_history(
    particle_container, collision_data_container, distance, simulation, data
):
    """Apply condensed interactions over the traveled distance."""
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_PROTON:
        proton.condensed_history(
            particle_container, collision_data_container, distance, simulation, data
        )
    else:
        raise ValueError(
            "Condensed history not supported for "
            + util.particle_name(particle["particle_type"])
        )
