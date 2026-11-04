"""The Klein-Nishina sampler used for incoherent scattering.

Ported from the pre-refactor ``test_klein_nishina.py`` and
``test_distributions.py``. These check the sampler against the analytic
distribution rather than against a stored answer, so they fail if the
kinematics or the rejection envelope is wrong.
"""

import numpy as np
import pytest

import mcdc.transport.physics.photon.native as native

from mcdc.constant import ELECTRON_MASS

from conftest import make_photon


def _sample(E, count=4000, first_seed=1):
    """Return ``(eps, mu)`` arrays sampled at incident energy ``E``.

    Every draw comes from **one** advancing RNG stream, which is how transport
    uses it. Seeding each draw with a fresh consecutive integer instead would
    make the samples correlated -- an LCG's first output is a near-linear
    function of its seed -- and a correlated sample does not obey the Poisson
    statistics the distribution test below relies on.
    """
    container = make_photon(E, seed=first_seed)
    eps = np.empty(count)
    mu = np.empty(count)
    for index in range(count):
        eps[index], mu[index] = native.sample_klein_nishina(E, container)
    return eps, mu


def _epsilon_min(E):
    """The lowest possible energy ratio, at backscatter."""
    kappa = E / ELECTRON_MASS
    return 1.0 / (1.0 + 2.0 * kappa)


# ======================================================================================
# Kinematics
# ======================================================================================


@pytest.mark.parametrize("E", [1.0e4, 1.0e6, 1.0e7])
def test_compton_relation_ties_energy_to_angle(E):
    """``eps`` and ``mu`` must satisfy Compton kinematics exactly.

    ``1 / eps = 1 + kappa (1 - mu)``. The sampler draws ``eps`` and derives
    ``mu`` from it, so a violation here means the derivation is wrong, not that
    the distribution is misshapen.
    """
    eps, mu = _sample(E, count=1500)
    kappa = E / ELECTRON_MASS

    # Exclude samples the sampler clamped at the ends of the cosine range.
    interior = (mu > -1.0 + 1e-12) & (mu < 1.0 - 1e-12)
    assert interior.sum() > 100

    predicted = 1.0 + kappa * (1.0 - mu[interior])
    assert np.allclose(1.0 / eps[interior], predicted, rtol=1e-10)


# ======================================================================================
# The distribution itself
# ======================================================================================


def _klein_nishina_pdf(eps, E):
    """The Klein-Nishina differential cross section in ``eps``, up to a constant.

    ``d(sigma)/d(eps) ~ 1/eps + eps - (1 - mu^2) ... `` expressed through
    ``eps`` alone, which is the form the Kahn envelope is built around:

        f(eps) = (1/eps + eps) - (1 - mu^2) ,  mu = 1 - (1/eps - 1)/kappa
    """
    kappa = E / ELECTRON_MASS
    mu = 1.0 - (1.0 / eps - 1.0) / kappa
    return (1.0 / eps + eps) - (1.0 - mu**2)


@pytest.mark.parametrize("E", [1.0e5, 1.0e6, 5.0e6])
def test_sampled_spectrum_matches_the_klein_nishina_formula(E):
    """A histogram of sampled ``eps`` must follow the analytic shape.

    This is the test that would catch a wrong rejection probability: the
    samples would still be in range and still satisfy kinematics, but their
    density would be wrong. Compared as a shape, normalised on the histogram,
    so no overall constant is needed.
    """
    eps, _ = _sample(E, count=20000)

    edges = np.linspace(_epsilon_min(E), 1.0, 13)
    counts, _ = np.histogram(eps, bins=edges)

    # Integrate the density over each bin rather than sampling it at the bin
    # centre. The density goes as 1/eps, which varies steeply across the
    # lowest bin, and a midpoint estimate there is biased by more than the
    # Poisson error this test is trying to measure.
    expected = np.array(
        [
            np.trapezoid(
                _klein_nishina_pdf(np.linspace(lo, hi, 200), E),
                np.linspace(lo, hi, 200),
            )
            for lo, hi in zip(edges[:-1], edges[1:])
        ]
    )
    expected = expected / expected.sum() * counts.sum()

    # Poisson tolerance: every well-populated bin within four sigma.
    populated = expected > 30
    assert populated.sum() >= 8
    deviation = np.abs(counts[populated] - expected[populated]) / np.sqrt(
        expected[populated]
    )
    assert deviation.max() < 4.0


# ======================================================================================
# Binding: the incoherent scattering function
# ======================================================================================


def test_bound_sampler_follows_klein_nishina_times_scattering_function(photon_model):
    """``<mu>`` matches the Klein-Nishina density weighted by ``S(x, Z)``.

    The library's incoherent cross section integrates Klein-Nishina against
    ``S``, so the angle must follow the same product. With ``S`` rising
    linearly to ``Z`` at ``x = 1`` per angstrom and ``k = 1`` per angstrom,
    free-electron sampling gives ``<mu> = 0.019`` and the bound density
    ``-0.232``, some 25 standard errors apart.
    """
    Z = 82
    simulation, data = photon_model(
        atomic_number=Z,
        scattering_function=(np.array([0.0, 1.0, 1.0e9]), np.array([0.0, Z, Z])),
    )
    k = 1.0  # inverse angstroms
    E = k * native.PLANCK_LIGHT_SPEED_EV_ANGSTROM
    count = 4000
    container = make_photon(E, seed=1)
    element = simulation["elements"][0]
    mu = np.array(
        [
            native.sample_klein_nishina_with_binding(
                E, element, container, simulation, data
            )[1]
            for _ in range(count)
        ]
    )

    grid = np.linspace(-1.0, 1.0, 200001)
    eps = 1.0 / (1.0 + E / ELECTRON_MASS * (1.0 - grid))
    weight = eps**2 * (eps + 1.0 / eps - (1.0 - grid**2))
    weight *= np.interp(k * np.sqrt(0.5 * (1.0 - grid)), [0.0, 1.0, 1.0e9], [0, Z, Z])
    expected = np.sum(grid * weight) / np.sum(weight)

    # One advancing stream of 4000 draws; four standard errors of the mean.
    assert abs(mu.mean() - expected) < 4.0 * mu.std() / np.sqrt(count)
