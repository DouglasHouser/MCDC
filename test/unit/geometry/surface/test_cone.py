import numpy as np
import pytest

import mcdc
import mcdc.numba_types as type_

from mcdc.constant import INF
from mcdc.transport.geometry.surface import cone, cone_x, cone_y, cone_z, interface

T_SQ = 0.25
HALF_ANGLE = np.degrees(np.arctan(np.sqrt(T_SQ)))
OBLIQUE_APEX = np.array([0.25, -0.5, 0.75])
OBLIQUE_AXIS = np.array([0.0, 1.0, 1.0]) / np.sqrt(2.0)
AXIS_MODULES = {"x": cone_x, "y": cone_y, "z": cone_z}
AXIS_VECTORS = {
    "x": np.array([1.0, 0.0, 0.0]),
    "y": np.array([0.0, 1.0, 0.0]),
    "z": np.array([0.0, 0.0, 1.0]),
}
RADIAL_VECTORS = {
    "x": np.array([0.0, 1.0, 0.0]),
    "y": np.array([1.0, 0.0, 0.0]),
    "z": np.array([1.0, 0.0, 0.0]),
}


@pytest.fixture
def cone_case(prepare_simulation):
    arbitrary_obj = mcdc.Surface.Cone(
        apex=[0.0, 0.0, 0.0], axis=[0.0, 0.0, 1.0], half_angle=HALF_ANGLE
    )
    reference_obj = mcdc.Surface.ConeZ(apex=[0.0, 0.0, 0.0], half_angle=HALF_ANGLE)
    oblique_obj = mcdc.Surface.Cone(
        apex=OBLIQUE_APEX, axis=[0.0, 2.0, 2.0], half_angle=HALF_ANGLE
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


@pytest.fixture
def axis_aligned_cones(prepare_simulation):
    objects = {
        "x": mcdc.Surface.ConeX(apex=OBLIQUE_APEX, half_angle=HALF_ANGLE),
        "y": mcdc.Surface.ConeY(apex=OBLIQUE_APEX, half_angle=HALF_ANGLE),
        "z": mcdc.Surface.ConeZ(apex=OBLIQUE_APEX, half_angle=HALF_ANGLE),
    }
    structure_container, data = prepare_simulation(objects=list(objects.values()))
    structure = structure_container[0]
    surfaces = {
        axis: structure["surfaces"][surface.ID] for axis, surface in objects.items()
    }
    return surfaces, data


def test_zero_axis_error():
    with pytest.raises(SystemExit):
        mcdc.Surface.Cone(axis=[0.0, 0.0, 0.0], half_angle=HALF_ANGLE)


@pytest.mark.parametrize("half_angle", [-1.0, 0.0, 90.0, 91.0])
def test_invalid_half_angle_error(half_angle):
    with pytest.raises(SystemExit):
        mcdc.Surface.Cone(half_angle=half_angle)


@pytest.mark.parametrize(
    ("constructor_name", "coefficient", "sign"),
    [
        ("ConeX", "A", -1.0),
        ("ConeY", "B", -1.0),
        ("ConeZ", "C", -1.0),
        ("Cone", "R", 1.0),
    ],
)
def test_half_angle_interface(constructor_name, coefficient, sign):
    surface = getattr(mcdc.Surface, constructor_name)(half_angle=30.0)

    assert sign * getattr(surface, coefficient) == pytest.approx(1.0 / 3.0)
    assert "Half-angle: 30 degrees" in repr(surface)


def test_evaluate_matches_cone_z(cone_case):
    arbitrary, reference, _, _ = cone_case
    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]

    for x, y, z in ((0.0, 0.0, 0.0), (1.0, 0.0, 2.0), (2.0, 0.0, 2.0)):
        particle["x"] = x
        particle["y"] = y
        particle["z"] = z
        assert cone.evaluate(particle_container, arbitrary) == pytest.approx(
            cone_z.evaluate(particle_container, reference)
        )


def test_oblique_operations(cone_case):
    _, _, oblique, data = cone_case
    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]
    axial_position = OBLIQUE_APEX + 2.0 * OBLIQUE_AXIS

    particle["x"] = axial_position[0] + 2.0
    particle["y"] = axial_position[1]
    particle["z"] = axial_position[2]
    particle["ux"] = -1.0
    assert cone.evaluate(particle_container, oblique) == pytest.approx(3.0)
    assert cone.get_distance(particle_container, oblique) == pytest.approx(1.0)
    assert interface.get_distance(
        particle_container, 1.0, oblique, data
    ) == pytest.approx(1.0)

    particle["x"] = axial_position[0] + 1.0
    gradient = np.array([1.0, -0.5 * OBLIQUE_AXIS[1], -0.5 * OBLIQUE_AXIS[2]])
    normal = gradient / np.linalg.norm(gradient)
    particle["ux"], particle["uy"], particle["uz"] = -normal
    assert cone.get_normal_component(particle_container, oblique) == pytest.approx(-1.0)
    cone.reflect(particle_container, oblique)
    np.testing.assert_allclose([particle["ux"], particle["uy"], particle["uz"]], normal)


def test_get_distance_rejects_current_cone_root(cone_case):
    arbitrary, _, _, data = cone_case
    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]
    particle["x"] = 0.5
    particle["z"] = 1.0
    particle["uz"] = 1.0

    assert cone.get_distance(particle_container, arbitrary) == INF
    assert interface.get_distance(particle_container, 1.0, arbitrary, data) == INF


@pytest.mark.parametrize("axis_name", ["x", "y", "z"])
def test_axis_aligned_operations(axis_aligned_cones, axis_name):
    surfaces, data = axis_aligned_cones
    surface = surfaces[axis_name]
    module = AXIS_MODULES[axis_name]
    axis = AXIS_VECTORS[axis_name]
    radial = RADIAL_VECTORS[axis_name]

    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]

    position = OBLIQUE_APEX + 2.0 * axis + 2.0 * radial
    particle["x"], particle["y"], particle["z"] = position
    particle["ux"], particle["uy"], particle["uz"] = -radial

    assert module.evaluate(particle_container, surface) == pytest.approx(3.0)
    assert interface.evaluate(particle_container, surface, data) == pytest.approx(3.0)
    assert module.get_distance(particle_container, surface) == pytest.approx(1.0)
    assert interface.get_distance(
        particle_container, 1.0, surface, data
    ) == pytest.approx(1.0)

    position = OBLIQUE_APEX + 2.0 * axis + radial
    particle["x"], particle["y"], particle["z"] = position
    normal = radial - 2.0 * T_SQ * axis
    normal /= np.linalg.norm(normal)
    particle["ux"], particle["uy"], particle["uz"] = -normal

    assert module.get_normal_component(particle_container, surface) == pytest.approx(
        -1.0
    )
    interface.reflect(particle_container, surface)
    np.testing.assert_allclose([particle["ux"], particle["uy"], particle["uz"]], normal)


@pytest.mark.parametrize("axis_name", ["x", "y", "z"])
def test_axis_aligned_distance_rejects_current_root(axis_aligned_cones, axis_name):
    surfaces, data = axis_aligned_cones
    surface = surfaces[axis_name]
    module = AXIS_MODULES[axis_name]
    axis = AXIS_VECTORS[axis_name]
    radial = RADIAL_VECTORS[axis_name]

    particle_container = np.zeros(1, dtype=type_.particle_data)
    particle = particle_container[0]
    position = OBLIQUE_APEX + axis + np.sqrt(T_SQ) * radial
    particle["x"], particle["y"], particle["z"] = position
    particle["ux"], particle["uy"], particle["uz"] = axis

    assert module.get_distance(particle_container, surface) == INF
    assert interface.get_distance(particle_container, 1.0, surface, data) == INF
