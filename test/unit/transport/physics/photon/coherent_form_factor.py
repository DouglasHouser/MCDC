"""
Unit tests for the coherent (Rayleigh) form-factor angular sampler.

Covers the validation checklist from
``photon-transport-directions/COHERENT_FORMFACTOR_SAMPLER.md`` (§8):

  * F(0) = Z sanity (loader reads the correct column / unit).
  * Form factor rides through the flat-data buffer unchanged.
  * Forward-peaking: sampled mu is strongly forward-biased vs the isotropic baseline.
  * Energy trend: mean scattering angle decreases as E rises (mean mu increases).
  * Z trend: at fixed E, mean scattering angle increases with Z (mean mu decreases).
  * Elastic invariant: the sampler leaves photon energy and the cross section untouched.

Built against the real typed simulation state and the actual @njit sampler, mirroring
``test/unit/transport/physics/photon/cross_sections.py``.
"""

import numpy as np
import pytest

import mcdc.numba_types as t
from mcdc.constant import MATERIAL_PHOTON, PARTICLE_PHOTON
from mcdc.object_.photon_material import _build_flat_data
from mcdc.transport.physics.photon import cross_sections as cs
from mcdc.transport.physics.photon.distributions import sample_coherent_mu

from mcdc.transport.physics.photon.data_loader import (
    load_photon_element_coherent_form_factor,
)

_DENSITY = 0.033  # atoms/barn-cm
_N_SAMPLE = 20000


# ----------------------------------------------------------------------------
# State / particle builders
# ----------------------------------------------------------------------------


def _state(Z, density=_DENSITY):
    flat = _build_flat_data([Z], [density])
    mcdc = np.zeros(1, dtype=t.simulation)
    mcdc[0]["materials"][0]["child_type"] = MATERIAL_PHOTON
    mcdc[0]["materials"][0]["child_ID"] = 0
    mcdc[0]["photon_materials"][0]["N_element"] = 1
    mcdc[0]["photon_materials"][0]["flat_data_offset"] = 0
    mcdc[0]["photon_materials"][0]["flat_data_length"] = len(flat)
    return mcdc[0], flat


def _photon(E, seed):
    p = np.zeros(1, dtype=t.particle)
    p[0]["material_ID"] = 0
    p[0]["particle_type"] = PARTICLE_PHOTON
    p[0]["E"] = E
    p[0]["alive"] = True
    p[0]["uz"] = 1.0
    p[0]["rng_seed"] = np.uint64(seed)
    return p


def _sample_mu(mcdc, data, E, n=_N_SAMPLE):
    mus = np.empty(n, dtype=np.float64)
    for i in range(n):
        p = _photon(E, 2 * i + 1)
        mus[i] = sample_coherent_mu(p, mcdc, data)
    return mus


# ----------------------------------------------------------------------------
# Data-import / loader sanity
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("Z", [1, 8, 13, 82])
def test_form_factor_f0_equals_z(Z):
    """F(0) must equal Z — catches a wrong column or a broken loader."""
    q_grid, cumF2, F = load_photon_element_coherent_form_factor(Z)
    assert F[0] == pytest.approx(float(Z))
    assert q_grid[0] == 0.0
    assert cumF2[0] == 0.0
    assert len(q_grid) == len(cumF2) == len(F)
    # Cumulative table is monotone non-decreasing (required for invertibility).
    assert np.all(np.diff(cumF2) >= 0.0)
    # q = 2 x conversion: grid strictly increasing.
    assert np.all(np.diff(q_grid) > 0.0)


def test_form_factor_rides_flat_data():
    """The q-grid and cumF2 must round-trip through _build_flat_data unchanged."""
    Z = 82
    _, flat = _state(Z)
    N = 1
    base = 0
    nff = int(flat[base + 8 * N])
    q_off = base + int(flat[base + 9 * N])
    cum_off = base + int(flat[base + 10 * N])
    q_grid, cumF2, _F = load_photon_element_coherent_form_factor(Z)
    assert nff == len(q_grid)
    np.testing.assert_allclose(flat[q_off : q_off + nff], q_grid)
    np.testing.assert_allclose(flat[cum_off : cum_off + nff], cumF2)


# ----------------------------------------------------------------------------
# Angular-distribution behaviour
# ----------------------------------------------------------------------------


def test_mu_within_physical_range():
    mcdc, data = _state(82)
    mus = _sample_mu(mcdc, data, 0.1)
    assert mus.min() >= -1.0
    assert mus.max() <= 1.0


def test_forward_peaking_vs_isotropic():
    """
    Sampled mu is strongly forward-biased.  An isotropic sampler gives mean mu ~ 0
    and half the samples with mu > 0; the form-factor sampler must beat both by a
    wide margin at a representative energy.
    """
    mcdc, data = _state(82)
    mus = _sample_mu(mcdc, data, 0.1)  # 100 keV
    assert mus.mean() > 0.5  # isotropic baseline ~ 0.0
    assert np.mean(mus > 0.0) > 0.75  # isotropic baseline ~ 0.5


def test_mean_angle_decreases_with_energy():
    """Higher energy => more forward => larger mean mu (monotone across the grid)."""
    mcdc, data = _state(82)
    energies = [0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
    means = [_sample_mu(mcdc, data, E).mean() for E in energies]
    for lo, hi in zip(means, means[1:]):
        assert hi > lo, f"mean mu not increasing with E: {list(zip(energies, means))}"


def test_mean_angle_increases_with_Z():
    """At fixed E, higher Z scatters through larger angles => smaller mean mu."""
    E = 0.1
    mcdc_lo, data_lo = _state(13)  # Al
    mcdc_hi, data_hi = _state(82)  # Pb
    mean_al = _sample_mu(mcdc_lo, data_lo, E).mean()
    mean_pb = _sample_mu(mcdc_hi, data_hi, E).mean()
    assert mean_al > mean_pb


# ----------------------------------------------------------------------------
# Elastic invariant — the sampler must not change energy or the cross section
# ----------------------------------------------------------------------------


def test_sampler_preserves_energy_and_xs():
    mcdc, data = _state(82)
    E = 0.2
    coh_before = cs.macro_coherent_xs(_photon(E, 1), mcdc, data)
    data_snapshot = data.copy()
    p = _photon(E, 12345)
    _ = sample_coherent_mu(p, mcdc, data)
    # Sampler leaves the incident energy untouched (elastic scattering).
    assert p[0]["E"] == E
    # Sampler is read-only w.r.t. the flat data buffer / cross section.
    np.testing.assert_array_equal(data, data_snapshot)
    coh_after = cs.macro_coherent_xs(_photon(E, 1), mcdc, data)
    assert coh_after == coh_before
