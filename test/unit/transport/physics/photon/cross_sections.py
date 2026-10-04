"""
Unit tests for photon macroscopic cross sections and collision-channel sampling.

Verifies that the photon transport path:
  * includes coherent (Rayleigh) scattering in the total cross section,
  * uses the *tabulated* incoherent (Compton) cross section (not Klein-Nishina)
    for the interaction probability,
  * keeps pair production zero below the 1.022 MeV threshold,
  * preserves constant-XS material behavior.

These tests build the real typed ``simulation`` state and exercise the actual
@njit transport functions.
"""

import numpy as np
import pytest

import mcdc.numba_types as t
from mcdc.constant import (
    MATERIAL_CONSTANT_XS,
    MATERIAL_PHOTON,
    PARTICLE_PHOTON,
    PHOTON_REACTION_COHERENT,
    PHOTON_REACTION_COMPTON,
    PHOTON_REACTION_PHOTOELECTRIC,
    PHOTON_REACTION_PAIR_PRODUCTION,
    PHOTON_REACTION_TOTAL,
)
from mcdc.object_.photon_material import _build_flat_data
from mcdc.transport.physics.photon import cross_sections as cs
from mcdc.transport.physics.photon import interface as itf
from mcdc.transport.physics.photon.cross_sections import klein_nishina_total

from mcdc.transport.physics.photon.data_loader import (
    load_photon_element,
    load_photon_element_coherent,
)

_Z = 82          # Pb
_DENSITY = 0.033  # atoms/barn-cm
_PAIR_THRESH = 2.0 * 0.51099895


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


def _photon(E):
    p = np.zeros(1, dtype=t.particle)
    p[0]["material_ID"] = 0
    p[0]["particle_type"] = PARTICLE_PHOTON
    p[0]["E"] = E
    p[0]["alive"] = True
    p[0]["uz"] = 1.0
    return p


def test_total_is_sum_of_four_channels(pb_state):
    mcdc, data = pb_state
    for E in [0.02, 0.1, 1.0, 8.0]:
        p = _photon(E)
        coh = cs.macro_coherent_xs(p, mcdc, data)
        inc = cs.macro_compton_xs(p, mcdc, data)
        pe = cs.macro_photoelectric_xs(p, mcdc, data)
        pp = cs.macro_pair_production_xs(p, mcdc, data)
        tot = cs.macro_total_xs(p, mcdc, data)
        assert tot == pytest.approx(coh + inc + pe + pp, rel=1e-12)


def test_total_includes_coherent(pb_state):
    """Total must exceed (incoherent + pe + pair); coherent is non-negligible."""
    mcdc, data = pb_state
    p = _photon(0.05)  # 50 keV: coherent is sizeable for Pb
    coh = cs.macro_coherent_xs(p, mcdc, data)
    assert coh > 0.0
    tot = cs.macro_total_xs(p, mcdc, data)
    without_coh = (
        cs.macro_compton_xs(p, mcdc, data)
        + cs.macro_photoelectric_xs(p, mcdc, data)
        + cs.macro_pair_production_xs(p, mcdc, data)
    )
    assert tot > without_coh
    assert tot == pytest.approx(without_coh + coh, rel=1e-12)


def test_channels_match_tabulated_hdf5(pb_state):
    """Macroscopic XS == density * tabulated cm^2/atom * 1e24 (log-log interp)."""
    mcdc, data = pb_state
    energies, compton_ref, pe_ref, pair_ref = load_photon_element(_Z)
    _, coherent_ref = load_photon_element_coherent(_Z)

    def ref(xs_arr, E):
        with np.errstate(divide="ignore"):
            log_xs = np.log(xs_arr)
        sigma = np.exp(np.interp(np.log(E), np.log(energies), log_xs))
        return _DENSITY * sigma * 1.0e24

    for E in [0.03, 0.5, 5.0]:
        p = _photon(E)
        assert cs.macro_coherent_xs(p, mcdc, data) == pytest.approx(ref(coherent_ref, E), rel=1e-9)
        assert cs.macro_compton_xs(p, mcdc, data) == pytest.approx(ref(compton_ref, E), rel=1e-9)
        assert cs.macro_photoelectric_xs(p, mcdc, data) == pytest.approx(ref(pe_ref, E), rel=1e-9)


def test_incoherent_is_tabulated_not_klein_nishina(pb_state):
    """The Compton channel must use tabulated incoherent XS, not Z*KN."""
    mcdc, data = pb_state
    E = 0.1  # 100 keV — binding effects make tabulated incoherent < Z*KN for Pb
    p = _photon(E)
    tabulated = cs.macro_compton_xs(p, mcdc, data)
    kn_based = _DENSITY * klein_nishina_total(E) * _Z * 1.0e24
    # They must differ appreciably (incoherent scattering function suppression).
    assert abs(tabulated - kn_based) / kn_based > 0.05


def test_pair_zero_below_threshold(pb_state):
    mcdc, data = pb_state
    p = _photon(_PAIR_THRESH * 0.9)
    assert cs.macro_pair_production_xs(p, mcdc, data) == 0.0
    p = _photon(_PAIR_THRESH * 2.0)
    assert cs.macro_pair_production_xs(p, mcdc, data) > 0.0


def test_macro_xs_dispatch(pb_state):
    mcdc, data = pb_state
    p = _photon(1.0)
    assert itf.macro_xs(PHOTON_REACTION_COHERENT, p, mcdc, data) == cs.macro_coherent_xs(p, mcdc, data)
    assert itf.macro_xs(PHOTON_REACTION_COMPTON, p, mcdc, data) == cs.macro_compton_xs(p, mcdc, data)
    assert itf.macro_xs(PHOTON_REACTION_PHOTOELECTRIC, p, mcdc, data) == cs.macro_photoelectric_xs(p, mcdc, data)
    assert itf.macro_xs(PHOTON_REACTION_PAIR_PRODUCTION, p, mcdc, data) == cs.macro_pair_production_xs(p, mcdc, data)
    assert itf.macro_xs(PHOTON_REACTION_TOTAL, p, mcdc, data) == cs.macro_total_xs(p, mcdc, data)


# ----------------------------------------------------------------------------
# Constant-XS material behavior must be unchanged
# ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def const_state():
    mcdc = np.zeros(1, dtype=t.simulation)
    mcdc[0]["materials"][0]["child_type"] = MATERIAL_CONSTANT_XS
    mcdc[0]["materials"][0]["child_ID"] = 0
    cxs = mcdc[0]["constant_xs_materials"][0]
    cxs["sigma_total"] = 2.0
    cxs["sigma_scatter"] = 1.5
    cxs["sigma_absorb"] = 0.5
    return mcdc[0], np.zeros(1, dtype=np.float64)


def test_constant_xs_unchanged(const_state):
    mcdc, data = const_state
    p = _photon(1.0)
    assert cs.macro_total_xs(p, mcdc, data) == pytest.approx(2.0)
    assert cs.macro_compton_xs(p, mcdc, data) == pytest.approx(1.5)
    assert cs.macro_photoelectric_xs(p, mcdc, data) == pytest.approx(0.5)
    # Constant-XS materials have no separate coherent or pair channel.
    assert cs.macro_coherent_xs(p, mcdc, data) == 0.0
    assert cs.macro_pair_production_xs(p, mcdc, data) == 0.0
