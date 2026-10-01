import numpy as np
import pytest

import mcdc
import mcdc.numba_types as type_
from mcdc.constant import ELECTRON_CUTOFF_ENERGY, PARTICLE_ELECTRON
from mcdc.object_.tally import TallyCollision
from mcdc.transport.physics.interface import collision as collide
from mcdc.transport.tally.score import collision as score_collision


def test_collision_tally_with_mesh_filter():
    mesh = mcdc.MeshUniform(
        "mesh",
        x=(-1.0, 0.5, 2),
        y=(-1.0, 1.0, 1),
        z=(-1.0, 1.0, 1),
    )
    tally = mcdc.Tally(mesh=mesh, scores=["energy_deposition"])
    simulation = mcdc.Simulation()
    simulation.set_model([mcdc.Cell()])
    simulation.set_tallies([tally])
    simulation.compile()

    assert isinstance(tally, TallyCollision)
    assert not tally.cell_filtered
    assert tally.cell_filter_ID == -1
    assert tally.mesh_filtered
    assert tally.mesh_filter_ID == mesh.ID


def test_collision_tally_without_spatial_filter():
    tally = mcdc.Tally(scores=["energy_deposition"])

    assert isinstance(tally, TallyCollision)
    assert not tally.cell_filtered
    assert tally.cell_filter_ID == -1
    assert not tally.mesh_filtered
    assert tally.mesh_filter_ID == -1


@pytest.mark.parametrize(
    "outgoing_energy",
    [12000.0, 0.0],
    ids=["energy-loss", "stopped"],
)
def test_collision_tally_uses_incident_energy(prepare_simulation, outgoing_energy):
    tally_object = mcdc.Tally(
        scores=["energy_deposition"],
        particle_type="electron",
        energy=[0.0, 15000.0, 30000.0],
    )
    simulation_container, data = prepare_simulation(tallies=[tally_object])
    simulation = simulation_container[0]
    tally = simulation["tallies"][tally_object.ID]

    particle_container = np.zeros(1, dtype=type_.particle)
    particle = particle_container[0]
    particle["particle_type"] = PARTICLE_ELECTRON
    particle["E"] = outgoing_energy
    particle["w"] = 2.0
    particle["alive"] = outgoing_energy > 0.0

    collision_container = np.zeros(1, dtype=type_.collision_data)
    collision_data = collision_container[0]
    collision_data["incident_particle"]["E"] = 20000.0
    collision_data["incident_particle"]["particle_type"] = PARTICLE_ELECTRON
    collision_data["incident_particle"]["w"] = 2.0
    deposited_energy = (20000.0 - outgoing_energy) * particle["w"]
    collision_data["energy_deposition"] = deposited_energy

    score_collision(collision_container, tally, simulation, data)

    offset = tally["bin_offset"]
    stride = tally["stride_energy"]
    np.testing.assert_allclose(
        [data[offset], data[offset + stride]],
        [0.0, deposited_energy],
    )
    assert particle["E"] == outgoing_energy


def test_collision_captures_energy_before_electron_cutoff(
    prepare_simulation, material_mg
):
    incident_energy = 0.5 * ELECTRON_CUTOFF_ENERGY
    tally_object = mcdc.Tally(
        scores=["energy_deposition"],
        particle_type="electron",
        energy=[
            0.0,
            0.25 * ELECTRON_CUTOFF_ENERGY,
            ELECTRON_CUTOFF_ENERGY,
        ],
    )

    # Provide a valid material record. The cutoff path returns before
    # consulting any material cross sections.
    cell = mcdc.Cell(fill=material_mg)
    simulation_container, data = prepare_simulation(
        cells=[cell], tallies=[tally_object]
    )
    simulation = simulation_container[0]
    tally = simulation["tallies"][tally_object.ID]

    particle_container = np.zeros(1, dtype=type_.particle)
    particle = particle_container[0]
    particle["particle_type"] = PARTICLE_ELECTRON
    particle["material_ID"] = material_mg.ID
    particle["cell_ID"] = cell.ID
    particle["E"] = incident_energy
    particle["w"] = 2.0
    particle["alive"] = True

    collision_container = np.zeros(1, dtype=type_.collision_data)

    collide(particle_container, collision_container, simulation, data)

    incident = collision_container[0]["incident_particle"]
    assert incident["E"] == incident_energy
    assert incident["particle_type"] == PARTICLE_ELECTRON
    assert incident["w"] == 2.0
    assert particle["E"] == 0.0
    assert not particle["alive"]
    assert collision_container[0]["energy_deposition"] == pytest.approx(
        incident_energy * 2.0
    )

    score_collision(collision_container, tally, simulation, data)

    offset = tally["bin_offset"]
    stride = tally["stride_energy"]
    np.testing.assert_allclose(
        [data[offset], data[offset + stride]],
        [0.0, incident_energy * 2.0],
    )
