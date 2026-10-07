import numpy as np
import pytest

import mcdc.numba_types as type_
import mcdc.transport.physics.neutron.native as neutron
import mcdc.transport.physics.proton.native as proton
from mcdc.constant import NEUTRON_MASS, PROTON_MASS


@pytest.mark.parametrize(
    "physics, mass",
    [(neutron, NEUTRON_MASS), (proton, PROTON_MASS)],
)
def test_low_speed_has_nonzero_energy(physics, mass):
    # This is the outgoing speed that exposed cancellation in an OKTAVIAN
    # neutron history: direct evaluation of mass * (gamma - 1) returned zero.
    speed = 60.78200508599138

    energy = physics.particle_energy_from_speed(speed)

    assert energy > 0.0
    assert energy == pytest.approx(1.931104021856582e-9 * mass / NEUTRON_MASS)


@pytest.mark.parametrize("physics", [neutron, proton])
@pytest.mark.parametrize("energy", [1.0e-9, 1.0e-3, 1.0e6, 1.0e9])
def test_speed_energy_round_trip(physics, energy):
    particle_container = np.zeros(1, dtype=type_.particle)
    particle_container[0]["E"] = energy

    speed = physics.particle_speed(particle_container)

    assert physics.particle_energy_from_speed(speed) == pytest.approx(
        energy, rel=1.0e-12
    )
