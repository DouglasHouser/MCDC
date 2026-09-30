import pytest

import mcdc

from mcdc.object_.settings import Settings


def test_transport_settings_are_independent():
    first, second = Settings(), Settings()
    assert not first.neutron_transport.active
    assert not first.electron_transport.active
    first.electron_transport.prioritize_low_energy = True
    assert not first.neutron_transport.prioritize_low_energy
    assert not second.electron_transport.prioritize_low_energy


def test_transport_settings_are_packed(prepare_simulation):
    def configure(simulation):
        simulation.settings.electron_transport.active = True
        simulation.settings.electron_transport.prioritize_low_energy = True

    container, _ = prepare_simulation(configure=configure)
    settings = container[0]["settings"]
    assert not settings["neutron_transport"]["active"]
    assert not settings["neutron_transport"]["prioritize_low_energy"]
    assert settings["electron_transport"]["active"]
    assert settings["electron_transport"]["prioritize_low_energy"]


@pytest.mark.parametrize(
    "species,explicit_neutron,explicit_electron,expected_neutron,expected_electron",
    [
        ([], False, False, False, False),
        (["neutron"], False, False, True, False),
        (["electron"], False, False, False, True),
        (["neutron", "electron"], False, False, True, True),
        (["electron"], True, False, True, True),
        (["neutron"], False, True, True, True),
    ],
)
def test_finalization_activates_source_species(
    prepare_simulation,
    species,
    explicit_neutron,
    explicit_electron,
    expected_neutron,
    expected_electron,
):
    def configure(simulation):
        simulation.settings.neutron_transport.active = explicit_neutron
        simulation.settings.electron_transport.active = explicit_electron

    sources = [mcdc.Source(particle_type=particle) for particle in species]
    container, _ = prepare_simulation(sources=sources, configure=configure)
    settings = container[0]["settings"]
    assert settings["neutron_transport"]["active"] == expected_neutron
    assert settings["electron_transport"]["active"] == expected_electron
