import numba as nb
from numba import njit

####

import mcdc.transport.physics.proton as proton
import mcdc.transport.util as util
import mcdc.config as config

from mcdc.constant import PARTICLE_PROTON


def condensed_interactions_support_error(particle_type):
    raise ValueError(
        "Condensed interactions not supported for " + util.particle_name(particle_type)
    )


@nb.extending.overload(condensed_interactions_support_error, target="cpu")
def cise_cpu_overload(particle_type):
    def impl(particle_type):
        raise ValueError(
            "Condensed interactions not supported for "
            + util.particle_name(particle_type)
        )

    return impl


@nb.extending.overload(condensed_interactions_support_error, target="gpu")
def cise_cuda_overload(particle_type):
    def impl(particle_type):
        pass

    return impl


if config.ROCM_AVAILABLE:

    @nb.extending.overload(condensed_interactions_support_error, target="hip")
    def cise_rocm_overload(particle_type):
        def impl(particle_type):
            pass

        return impl


@njit
def max_condensed_step_distance(particle_container, simulation, data):
    """Return the maximum condensed step length for the particle."""
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_PROTON:
        return proton.max_condensed_step_distance(particle_container, simulation, data)
    else:
        condensed_interactions_support_error(particle["particle_type"])


@njit
def condensed_interactions(
    particle_container, interaction_data_container, distance, simulation, data
):
    """Apply condensed interactions over the traveled distance."""
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_PROTON:
        proton.condensed_interactions(
            particle_container, interaction_data_container, distance, simulation, data
        )
    else:
        condensed_interactions_support_error(particle["particle_type"])
