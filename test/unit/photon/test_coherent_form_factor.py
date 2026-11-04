"""Coherent (Rayleigh) scattering from the tabulated atomic form factor.

Ported from the pre-refactor ``coherent_form_factor.py``. The physics being
checked is the shape of the angular distribution: coherent scattering peaks
forward, more sharply as energy rises and as Z rises, and it is elastic.
"""

import numpy as np
import pytest

import mcdc.transport.physics.photon.native as native

from conftest import make_interaction_data, make_photon


def _element(simulation):
    return simulation["elements"][0]


def _sample_cosines(simulation, data, E, count=400, first_seed=1):
    """Sample ``count`` scattering cosines from one advancing RNG stream.

    One stream, not one fresh seed per draw: an LCG's first output is a
    near-linear function of its seed, so consecutive seeds give correlated
    samples whose mean is biased and whose spread is not Poisson.
    """
    container = make_photon(E, seed=first_seed)
    element = _element(simulation)
    return np.array(
        [
            native.sample_coherent_scattering_cosine(
                container, element, simulation, data
            )
            for _ in range(count)
        ]
    )


# ======================================================================================
# The form factor itself
# ======================================================================================


@pytest.mark.parametrize("Z", [1, 13, 82])
def test_form_factor_forward_value_equals_z(photon_model, Z):
    """``F(q = 0, Z) = Z``: every electron scatters in phase in the forward direction."""
    from mcdc.transport.data import evaluate_data

    simulation, data = photon_model(atomic_number=Z)
    element = _element(simulation)
    reaction_ID = int(
        np.asarray(
            __import__(
                "mcdc.mcdc_get", fromlist=["element"]
            ).element.photon_coherent_scattering_reaction_IDs(0, element, data)
        )
    )
    reaction_base = simulation["photon_reactions"][reaction_ID]
    reaction = simulation["photon_coherent_scattering_reactions"][
        reaction_base["sub_ID"]
    ]
    form_factor = simulation["data"][reaction["form_factor_ID"]]

    assert evaluate_data(0.0, form_factor, simulation, data) == pytest.approx(float(Z))


# ======================================================================================
# The sampled angular distribution
# ======================================================================================


def test_sampled_cosine_follows_the_form_factor_distribution(photon_model):
    """``<mu>`` matches ``(1 + mu^2) F(x)^2`` with ``x = k sqrt((1 - mu) / 2)``.

    ``x = sin(theta / 2) / lambda`` is the variable the library tabulates ``F``
    against. Looking ``F`` up at ``2 x`` instead moves the mean at this energy
    from 0.244 to 0.500, some 25 standard errors away.
    """
    from mcdc.mcdc_get import table_data

    simulation, data = photon_model()
    k = 4.0  # inverse angstroms
    count = 4000
    mu = _sample_cosines(
        simulation, data, k * native.PLANCK_LIGHT_SPEED_EV_ANGSTROM, count=count
    )

    reaction = simulation["photon_coherent_scattering_reactions"][0]
    table = simulation["table_data"][
        simulation["data"][reaction["form_factor_ID"]]["sub_ID"]
    ]
    x_table = table_data.x_all(table, data)
    F_table = table_data.y_all(table, data)
    grid = np.linspace(-1.0, 1.0, 200001)
    weight = (1.0 + grid**2) * np.interp(
        k * np.sqrt(0.5 * (1.0 - grid)), x_table, F_table
    ) ** 2
    expected = np.sum(grid * weight) / np.sum(weight)

    # One advancing stream of 4000 draws; four standard errors of the mean.
    assert abs(mu.mean() - expected) < 4.0 * mu.std() / np.sqrt(count)


def test_forward_peaking_sharpens_with_energy(photon_model):
    # Higher energy means larger accessible momentum transfer, so the form
    # factor cuts off the large angles more aggressively.
    simulation, data = photon_model()
    low = _sample_cosines(simulation, data, 1.0e4, count=600).mean()
    high = _sample_cosines(simulation, data, 1.0e6, count=600).mean()
    assert high > low


# ======================================================================================
# Coherent scattering is elastic
# ======================================================================================


def test_scattering_preserves_energy_and_deposits_nothing(photon_model):
    simulation, data = photon_model()
    E = 1.0e5
    container = make_photon(E, seed=3)
    interaction = make_interaction_data()

    native.coherent_scattering(container, _element(simulation), simulation, data)

    assert container[0]["E"] == E
    assert container[0]["alive"]
    assert interaction[0]["energy_deposition"] == 0.0
