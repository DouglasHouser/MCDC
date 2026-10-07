import numpy as np
import pytest

import mcdc
import mcdc.numba_types as type_

from mcdc.constant import COINCIDENCE_TOLERANCE, INF
from mcdc.transport.geometry.surface import interface, quadric


@pytest.fixture
def quadric_case(prepare_simulation):
    cone_obj = mcdc.Surface.Quadric(A=1.0, B=1.0, C=-1.0)
    sphere_obj = mcdc.Surface.Quadric(A=1.0, B=1.0, C=1.0, J=-1.0)
    structure_container, data = prepare_simulation(objects=[cone_obj, sphere_obj])
    structure = structure_container[0]
    return (
        structure["surfaces"][cone_obj.ID],
        structure["surfaces"][sphere_obj.ID],
        data,
    )


def test_get_distance_rejects_zero_cone_root(quadric_case):
    cone, _, data = quadric_case
    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]

    # The particle is within the geometry tolerance of
    # x^2 + y^2 - z^2 = 0 and moving into the cone.  Both ray roots are at,
    # within tolerance of, or behind the particle, so there is no future crossing.
    particle["x"] = 1.0 + 0.25 * COINCIDENCE_TOLERANCE
    particle["z"] = 1.0
    particle["uz"] = 1.0

    assert quadric.get_distance(particle_container, cone) == INF
    assert interface.get_distance(particle_container, 1.0, cone, data) == INF


def test_get_distance_keeps_future_quadric_root(quadric_case):
    _, sphere, data = quadric_case
    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]

    # Starting on the unit sphere and moving inward must discard the current
    # zero root while retaining the crossing on the opposite side.
    particle["x"] = 1.0
    particle["ux"] = -1.0

    assert quadric.get_distance(particle_container, sphere) == pytest.approx(2.0)
    assert interface.get_distance(
        particle_container, 1.0, sphere, data
    ) == pytest.approx(2.0)
