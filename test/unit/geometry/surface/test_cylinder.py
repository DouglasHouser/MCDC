import numpy as np
import pytest

import mcdc
import mcdc.numba_types as type_

from mcdc.constant import INF
from mcdc.transport.geometry.surface import cylinder, cylinder_z, interface

OBLIQUE_POINT = np.array([0.25, -0.5, 0.75])
OBLIQUE_AXIS = np.array([0.0, 1.0, 1.0]) / np.sqrt(2.0)


@pytest.fixture
def cylinder_case(prepare_simulation):
    arbitrary_obj = mcdc.Surface.Cylinder(
        point=[0.0, 0.0, 0.0], axis=[0.0, 0.0, 1.0], radius=1.0
    )
    reference_obj = mcdc.Surface.CylinderZ(center=[0.0, 0.0], radius=1.0)
    oblique_obj = mcdc.Surface.Cylinder(
        point=OBLIQUE_POINT, axis=[0.0, 2.0, 2.0], radius=1.0
    )
    structure_container, data = prepare_simulation(
        objects=[arbitrary_obj, reference_obj, oblique_obj]
    )
    structure = structure_container[0]
    return (
        structure["surfaces"][arbitrary_obj.ID],
        structure["surfaces"][reference_obj.ID],
        structure["surfaces"][oblique_obj.ID],
        data,
    )


def test_zero_axis_error():
    with pytest.raises(SystemExit):
        mcdc.Surface.Cylinder(axis=[0.0, 0.0, 0.0], radius=1.0)


def test_evaluate_matches_cylinder_z(cylinder_case):
    arbitrary, reference, _, _ = cylinder_case
    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]

    for x, y, z in ((0.0, 0.0, 0.0), (1.0, 0.0, 2.0), (2.0, 0.0, 0.0)):
        particle["x"] = x
        particle["y"] = y
        particle["z"] = z
        assert cylinder.evaluate(particle_container, arbitrary) == pytest.approx(
            cylinder_z.evaluate(particle_container, reference)
        )


def test_oblique_operations(cylinder_case):
    _, _, oblique, data = cylinder_case
    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]
    axial_position = OBLIQUE_POINT + 2.0 * OBLIQUE_AXIS

    particle["x"] = axial_position[0] + 2.0
    particle["y"] = axial_position[1]
    particle["z"] = axial_position[2]
    particle["ux"] = -1.0
    assert cylinder.evaluate(particle_container, oblique) == pytest.approx(3.0)
    assert cylinder.get_distance(particle_container, oblique) == pytest.approx(1.0)
    assert interface.get_distance(
        particle_container, 1.0, oblique, data
    ) == pytest.approx(1.0)

    particle["x"] = axial_position[0] + 1.0
    assert cylinder.get_normal_component(particle_container, oblique) == pytest.approx(
        -1.0
    )
    cylinder.reflect(particle_container, oblique)
    assert particle["ux"] == pytest.approx(1.0)

    particle["x"] = axial_position[0] + 2.0
    assert cylinder.get_distance(particle_container, oblique) == INF
