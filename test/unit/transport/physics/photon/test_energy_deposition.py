"""
Unit tests for the per-branch locally-deposited energy (``E_dep``) returned by the
photon ``collision()`` used by the ``energy-deposit`` tally.

Physics table (see photon-transport-directions/ENERGY_DEPOSITION_TALLY.md):

  | Reaction              | Deposited locally      |
  |-----------------------|------------------------|
  | Coherent (Rayleigh)   | 0.0                    |
  | Compton (incoherent)  | E_in * (1 - eps)       |
  | Photoelectric         | E_in - E1 - E2         |
  | Pair production       | E_in - 2*m_e (= -1.022)|
  | Constant-XS absorb    | E_in                   |
  | Constant-XS scatter   | 0.0                    |

Unifying rule (checked directly here for every branch):
  ``E_dep == E_in - (energy of the primary photon still alive)
                   - (energy of any banked secondary photon)``

These build the real typed ``simulation`` state and exercise the actual @njit
``collision()`` (JIT disabled in test mode), mirroring ``cross_sections.py``.
"""

import numpy as np
import pytest

import mcdc.numba_types as t
import mcdc.transport.particle_bank as particle_bank_module
from mcdc.constant import (
    MATERIAL_CONSTANT_XS,
    MATERIAL_PHOTON,
    PARTICLE_PHOTON,
)
from mcdc.object_.photon_material import _build_flat_data
from mcdc.transport.physics.photon import interface as itf

_Z = 82           # Pb
_DENSITY = 0.033  # atoms/barn-cm
_M_E = 0.51099895
_PAIR_THRESH = 2.0 * _M_E


# ----------------------------------------------------------------------------
# State / particle builders (mirror cross_sections.py)
# ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pb_state():
    """A Pb PhotonMaterial wired into a minimal typed simulation state."""
    flat = _build_flat_data([_Z], [_DENSITY])
    mcdc = np.zeros(1, dtype=t.simulation)
    mcdc[0]["materials"][0]["child_type"] = MATERIAL_PHOTON
    mcdc[0]["materials"][0]["child_ID"] = 0
    mcdc[0]["photon_materials"][0]["N_element"] = 1
    mcdc[0]["photon_materials"][0]["flat_data_offset"] = 0
    mcdc[0]["photon_materials"][0]["flat_data_length"] = len(flat)
    return mcdc[0], flat


@pytest.fixture
def const_state():
    mcdc = np.zeros(1, dtype=t.simulation)
    mcdc[0]["materials"][0]["child_type"] = MATERIAL_CONSTANT_XS
    mcdc[0]["materials"][0]["child_ID"] = 0
    return mcdc[0], np.zeros(1, dtype=np.float64)


def _photon(E, seed=1):
    p = np.zeros(1, dtype=t.particle)
    p[0]["material_ID"] = 0
    p[0]["particle_type"] = PARTICLE_PHOTON
    p[0]["E"] = E
    p[0]["w"] = 1.0
    p[0]["alive"] = True
    p[0]["uz"] = 1.0
    p[0]["rng_seed"] = np.uint64(seed)
    return p


def _energy_carried_away(p, mcdc):
    """Energy that leaves the collision site: live primary + banked secondaries."""
    e = p[0]["E"] if p[0]["alive"] else 0.0
    n = particle_bank_module.get_bank_size(mcdc["bank_active"])
    for i in range(n):
        e += mcdc["bank_active"]["particles"][i]["E"]
    return e


def _collide(p, mcdc, data):
    """Run one collision with an empty secondary bank; return (E_dep, away)."""
    particle_bank_module.set_bank_size(mcdc["bank_active"], 0)
    E_dep = itf.collision(p, mcdc, data)
    return E_dep, _energy_carried_away(p, mcdc)


# ----------------------------------------------------------------------------
# Constant-XS material branches (deterministic)
# ----------------------------------------------------------------------------


def test_constant_xs_absorb_deposits_full_energy(const_state):
    mcdc, data = const_state
    cxs = mcdc["constant_xs_materials"][0]
    cxs["sigma_total"] = 2.0
    cxs["sigma_absorb"] = 2.0  # xi < sigma_a always -> analog capture
    for E in (0.5, 2.0, 8.0):
        p = _photon(E, seed=7)
        E_dep = itf.collision(p, mcdc, data)
        assert not p[0]["alive"]
        assert E_dep == pytest.approx(E)


def test_constant_xs_scatter_deposits_zero(const_state):
    mcdc, data = const_state
    cxs = mcdc["constant_xs_materials"][0]
    cxs["sigma_total"] = 2.0
    cxs["sigma_absorb"] = 0.0  # never absorb -> isotropic elastic scatter
    for E in (0.5, 2.0):
        p = _photon(E, seed=3)
        E_dep = itf.collision(p, mcdc, data)
        assert p[0]["alive"]
        assert p[0]["E"] == pytest.approx(E)  # elastic: energy unchanged
        assert E_dep == 0.0


def test_constant_xs_zero_total_returns_float_zero(const_state):
    mcdc, data = const_state
    mcdc["constant_xs_materials"][0]["sigma_total"] = 0.0
    p = _photon(1.0, seed=5)
    result = itf.collision(p, mcdc, data)
    assert result == 0.0
    assert isinstance(float(result), float)


# ----------------------------------------------------------------------------
# Tabulated-XS branches: unifying-rule invariant + per-branch formulas
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("fluorescence", [False, True])
def test_energy_conservation_invariant(pb_state, fluorescence):
    """For every sampled branch: E_dep + energy-carried-away == E_in, 0 <= E_dep <= E_in."""
    mcdc, data = pb_state
    mcdc["settings"]["photon_fluorescence"] = fluorescence
    for i in range(1500):
        for E in (0.05, 0.5, 3.0, 8.0):
            p = _photon(E, seed=2 * i + 1)
            E_dep, away = _collide(p, mcdc, data)
            assert E_dep >= -1e-12
            assert E_dep <= E + 1e-9
            assert E_dep + away == pytest.approx(E, rel=1e-9, abs=1e-9)


def test_all_tabulated_branches_match_their_formula(pb_state):
    """Classify each collision by outcome and check the matching E_dep formula.

    Also asserts all four tabulated branches (coherent, Compton, photoelectric,
    pair) are exercised across the chosen energies.
    """
    mcdc, data = pb_state
    mcdc["settings"]["photon_fluorescence"] = False

    saw_coherent = saw_compton = saw_pe = saw_pair = False
    for i in range(4000):
        for E in (0.05, 0.5, 6.0, 10.0):
            p = _photon(E, seed=2 * i + 1)
            E_dep, _away = _collide(p, mcdc, data)
            n_bank = particle_bank_module.get_bank_size(mcdc["bank_active"])
            alive = p[0]["alive"]
            E_out = p[0]["E"]

            if not alive and n_bank == 0:
                # Photoelectric absorption (fluorescence off): full deposit.
                saw_pe = True
                assert E_dep == pytest.approx(E)
            elif alive and n_bank == 1 and E_out == pytest.approx(_M_E):
                # Pair production: two 0.511 MeV annihilation photons.
                saw_pair = True
                assert mcdc["bank_active"]["particles"][0]["E"] == pytest.approx(_M_E)
                assert E_dep == pytest.approx(E - _PAIR_THRESH)
            elif alive and n_bank == 0 and E_out == pytest.approx(E):
                # Coherent (Rayleigh): elastic, no deposition.
                saw_coherent = True
                assert E_dep == 0.0
            elif alive and n_bank == 0:
                # Compton (incoherent): recoil-electron energy deposits locally.
                saw_compton = True
                assert E_dep == pytest.approx(E - E_out)
                assert 0.0 < E_dep < E

    assert saw_coherent, "coherent branch never sampled"
    assert saw_compton, "Compton branch never sampled"
    assert saw_pe, "photoelectric branch never sampled"
    assert saw_pair, "pair-production branch never sampled"


def test_fluorescence_lowers_local_deposition(pb_state):
    """A/B: mean local deposit at 0.15 MeV (above Pb K-edge) is lower with
    fluorescence ON, because characteristic X-rays carry energy away."""
    mcdc, data = pb_state
    E = 0.15
    N = 8000

    def mean_deposit(fluor):
        mcdc["settings"]["photon_fluorescence"] = fluor
        total = 0.0
        for i in range(N):
            p = _photon(E, seed=2 * i + 1)
            E_dep, _ = _collide(p, mcdc, data)
            total += E_dep
        return total / N

    off = mean_deposit(False)
    on = mean_deposit(True)
    assert on < off
