"""Photoelectric atomic relaxation and characteristic X-ray emission.

These tests carry real weight: fluorescence photons are the only photoelectric
product that is transported -- every charged product deposits locally -- so this
is the only check on the one photoelectric branch that creates a particle.
Ported from the pre-refactor ``fluorescence.py``.
"""

import numpy as np
import pytest

import mcdc.transport.physics.photon.native as native

from conftest import (
    K_ALPHA_ENERGY,
    K_BINDING_ENERGY,
    L_BINDING_ENERGY,
    make_interaction_data,
    make_photon,
)

#: Above the K edge, so the K shell can be ionized.
E_ABOVE_K_EDGE = 1.0e6

#: Between the L and K binding energies, so only the L shell is accessible.
E_BELOW_K_EDGE = 5.0e4


def _element(simulation):
    return simulation["elements"][0]


def _sample(simulation, data, E, seed):
    return native.sample_fluorescence_energy(
        make_photon(E, seed=seed), _element(simulation), simulation, data
    )


# ======================================================================================
# The relaxation data loads
# ======================================================================================


def test_relaxation_data_loads(photon_model):
    simulation, data = photon_model()
    element = _element(simulation)
    assert element["photon_relaxation_subshell_count_length"] == 2
    assert element["photon_relaxation_transition_energy_length"] > 0


def test_binding_energies_load_in_ev(photon_model):
    # eV, not MeV: the library declares its unit and read_energy honours it.
    import mcdc.mcdc_get as mcdc_get

    simulation, data = photon_model()
    element = _element(simulation)
    binding = [
        mcdc_get.element.photon_photoelectric_subshell_binding_energy(i, element, data)
        for i in range(element["photon_photoelectric_subshell_binding_energy_length"])
    ]
    assert binding == pytest.approx([K_BINDING_ENERGY, L_BINDING_ENERGY])


def test_element_without_relaxation_emits_nothing(photon_model):
    # An element whose library carries no atomic_relaxation group is still
    # valid; photoelectric absorption simply produces no fluorescence.
    simulation, data = photon_model(include_relaxation=False)
    assert _sample(simulation, data, E_ABOVE_K_EDGE, seed=7) == 0.0


def test_outer_subshell_with_no_transitions_emits_nothing(photon_model):
    # The L shell has nothing above it to fill the vacancy, so its transition
    # count is zero and sampling it must return zero rather than index past the
    # end of the shared transition array.
    simulation, data = photon_model()
    element = _element(simulation)
    import mcdc.mcdc_get as mcdc_get

    counts = [
        int(mcdc_get.element.photon_relaxation_subshell_count(i, element, data))
        for i in range(2)
    ]
    assert counts[0] > 0
    assert counts[1] == 0


# ======================================================================================
# Line energies
# ======================================================================================


def test_k_line_appears_above_the_edge(photon_model):
    simulation, data = photon_model()
    seen = {
        _sample(simulation, data, E_ABOVE_K_EDGE, seed=seed) for seed in range(1, 40)
    }
    assert K_ALPHA_ENERGY in seen


def test_no_k_line_below_the_edge(photon_model):
    # Below the K edge the K shell cannot be ionized, so its line can never be
    # emitted. Only the L shell is accessible, and it has no transitions.
    simulation, data = photon_model()
    for seed in range(1, 40):
        assert _sample(simulation, data, E_BELOW_K_EDGE, seed=seed) != K_ALPHA_ENERGY


def test_emitted_energy_never_exceeds_the_incident_energy(photon_model):
    simulation, data = photon_model()
    for E in (E_BELOW_K_EDGE, E_ABOVE_K_EDGE, 1.0e7):
        for seed in range(1, 30):
            assert _sample(simulation, data, E, seed=seed) <= E


def test_line_energy_is_below_the_binding_energy_that_produced_it(photon_model):
    # This is what makes the cascade terminate: a line energy is the difference
    # of two binding energies, so an emitted photon can never re-ionize the
    # shell it came from. Approximating the line by the binding energy instead
    # produces an infinite loop.
    simulation, data = photon_model()
    for seed in range(1, 30):
        E_line = _sample(simulation, data, E_ABOVE_K_EDGE, seed=seed)
        if E_line > 0.0:
            assert E_line < K_BINDING_ENERGY


def test_fluorescence_can_be_suppressed_by_yield(photon_model):
    # With the radiative probability at zero, every de-excitation is
    # non-radiative, so nothing is emitted and all of it deposits locally.
    simulation, data = photon_model(fluorescence_yield=0.0)
    for seed in range(1, 40):
        assert _sample(simulation, data, E_ABOVE_K_EDGE, seed=seed) == 0.0


def test_partial_yield_gives_both_outcomes(photon_model):
    simulation, data = photon_model(fluorescence_yield=0.5)
    outcomes = {
        _sample(simulation, data, E_ABOVE_K_EDGE, seed=seed) > 0.0
        for seed in range(1, 60)
    }
    assert outcomes == {True, False}


# ======================================================================================
# Deposition balance
# ======================================================================================


def test_fluorescence_lowers_local_deposition(photon_model):
    """A transported line carries energy away from the collision site."""
    simulation, data = photon_model(fluorescence_yield=1.0)
    no_fluorescence, _ = photon_model(fluorescence_yield=0.0)

    def deposition(sim, dat, seed):
        container = make_photon(E_ABOVE_K_EDGE, seed=seed)
        interaction = make_interaction_data()
        native.photoelectric(container, interaction, _element(sim), sim, dat)
        return interaction[0]["energy_deposition"]

    with_line = deposition(simulation, data, seed=11)
    assert with_line == pytest.approx(E_ABOVE_K_EDGE - K_ALPHA_ENERGY)
    assert with_line < E_ABOVE_K_EDGE


def test_photoelectric_without_a_line_deposits_everything(photon_model):
    simulation, data = photon_model(fluorescence_yield=0.0)
    container = make_photon(E_ABOVE_K_EDGE, seed=5)
    interaction = make_interaction_data()
    native.photoelectric(container, interaction, _element(simulation), simulation, data)

    assert interaction[0]["energy_deposition"] == pytest.approx(E_ABOVE_K_EDGE)
    assert not container[0]["alive"]
    assert container[0]["E"] == 0.0


def test_photoelectric_with_a_line_revives_the_history(photon_model):
    simulation, data = photon_model(fluorescence_yield=1.0)
    container = make_photon(E_ABOVE_K_EDGE, seed=5)
    interaction = make_interaction_data()
    native.photoelectric(container, interaction, _element(simulation), simulation, data)

    assert container[0]["alive"]
    assert container[0]["E"] == pytest.approx(K_ALPHA_ENERGY)
    # Emitted isotropically, so the direction is renormalized but not preserved.
    direction = np.array([container[0]["ux"], container[0]["uy"], container[0]["uz"]])
    assert np.linalg.norm(direction) == pytest.approx(1.0)


def test_photoelectric_conserves_energy_with_weight(photon_model):
    # Deposition is weight-included, which is what the tally consumes.
    simulation, data = photon_model(fluorescence_yield=1.0)
    weight = 0.25
    container = make_photon(E_ABOVE_K_EDGE, seed=5, weight=weight)
    interaction = make_interaction_data()
    native.photoelectric(container, interaction, _element(simulation), simulation, data)

    deposited = interaction[0]["energy_deposition"]
    carried = container[0]["E"] * weight
    assert deposited + carried == pytest.approx(E_ABOVE_K_EDGE * weight)
