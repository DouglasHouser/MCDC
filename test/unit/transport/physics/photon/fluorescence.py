"""
Unit tests for photoelectric characteristic X-ray fluorescence.

Covers the fluorescence plan (see the plan file / photon-transport-directions):

  * Atomic-relaxation data loads from the reformatted HDF5 (Pb K lines, omega).
  * The per-shell binding/omega/line tables round-trip through _build_flat_data.
  * The @njit emission sampler produces the Pb K-alpha (~75 keV) and K-beta
    (~85 keV) characteristic lines above the K-edge.
  * Below the K-edge the K lines vanish (binding-energy / shell-XS gating).
  * The K->L cascade can emit a second (soft) photon.
  * Emitted line energies never exceed the incident photon energy.

Built against the real typed simulation state and the actual @njit sampler,
mirroring ``coherent_form_factor.py`` in this directory.
"""

import numpy as np
import pytest

import mcdc.numba_types as t
from mcdc.constant import MATERIAL_PHOTON, PARTICLE_PHOTON
from mcdc.object_.photon_material import _build_flat_data, _N_SHELL
from mcdc.transport.physics.photon.distributions import sample_photoelectric_emission

from mcdc.transport.physics.photon.data_loader import (
    load_photon_relaxation,
)

_DENSITY = 0.033  # atoms/barn-cm
_N_SAMPLE = 40000

# Pb characteristic K lines (MeV), for binning assertions.
_PB_KA = 0.075   # K-alpha ~ 73–75 keV
_PB_KB = 0.085   # K-beta  ~ 85 keV
_PB_K_EDGE = 0.088


# ----------------------------------------------------------------------------
# State / particle builders (mirror coherent_form_factor.py)
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


def _sample_emissions(mcdc, data, E, n=_N_SAMPLE):
    """Return a flat list of all emitted fluorescence-photon energies (MeV)."""
    energies = []
    for i in range(n):
        p = _photon(E, 2 * i + 1)
        n_ph, e1, e2 = sample_photoelectric_emission(p, mcdc, data)
        if n_ph >= 1:
            energies.append(e1)
        if n_ph == 2:
            energies.append(e2)
    return np.asarray(energies, dtype=np.float64)


# ----------------------------------------------------------------------------
# Data-import / loader sanity
# ----------------------------------------------------------------------------


def test_relaxation_data_loads_pb():
    """Pb K shell: binding ~88 keV, omega ~0.96, K-alpha lines near 73/75 keV."""
    relax = load_photon_relaxation(82)
    assert set([1, 2, 3, 4]).issubset(relax.keys())  # K, L1, L2, L3 present
    K = relax[1]
    assert K["binding_energy"] == pytest.approx(0.088011, rel=1e-3)
    assert K["fluorescence_yield"] == pytest.approx(0.961, abs=0.02)
    # Cumulative table is normalized and monotone.
    assert K["line_cumprob"][-1] == pytest.approx(1.0)
    assert np.all(np.diff(K["line_cumprob"]) >= 0.0)
    # The two strongest K lines are K-alpha at ~73 and ~75 keV.
    assert np.any(np.isclose(K["line_energy"], 0.073039, atol=5e-4))
    assert np.any(np.isclose(K["line_energy"], 0.075250, atol=5e-4))


def test_hydrogen_has_no_fluorescence():
    """H has a single K electron and cannot fluoresce (omega = 0, no lines)."""
    relax = load_photon_relaxation(1)
    if 1 in relax:  # K may be present but empty
        assert relax[1]["fluorescence_yield"] == pytest.approx(0.0)
        assert len(relax[1]["line_energy"]) == 0


# ----------------------------------------------------------------------------
# flat_data plumbing
# ----------------------------------------------------------------------------


def test_flat_data_carries_relaxation():
    """K binding/omega/line-count/line-table round-trip through _build_flat_data."""
    Z = 82
    _, flat = _state(Z)
    N = 1
    base = 0
    relax = load_photon_relaxation(Z)
    K = relax[1]
    # Section 15 = binding, 19 = omega, 23 = n_lines, 27 = line-table offset (shell 0 = K).
    assert flat[base + 15 * N] == pytest.approx(K["binding_energy"])
    assert flat[base + 19 * N] == pytest.approx(K["fluorescence_yield"])
    n_lines = int(flat[base + 23 * N])
    assert n_lines == len(K["line_energy"])
    line_off = base + int(flat[base + 27 * N])
    # First line triple: (energy, cumprob, final_idx).
    assert flat[line_off] == pytest.approx(K["line_energy"][0])
    assert flat[line_off + 1] == pytest.approx(K["line_cumprob"][0])


def test_shell_pe_xs_present_in_flat_data():
    """The four shell PE-XS arrays (K,L1,L2,L3) are non-trivial for Pb."""
    _, flat = _state(82)
    N = 1
    base = 0
    np_ = int(flat[base + 2 * N])
    for s in range(_N_SHELL):
        off = base + int(flat[base + (11 + s) * N])
        assert np.max(flat[off : off + np_]) > 0.0


# ----------------------------------------------------------------------------
# Sampler behaviour — characteristic lines
# ----------------------------------------------------------------------------


def test_pb_k_lines_appear_above_edge():
    """Above the Pb K-edge, emission spectrum shows K-alpha and K-beta peaks."""
    mcdc, data = _state(82)
    energies = _sample_emissions(mcdc, data, 0.15)  # 150 keV, above K-edge
    assert len(energies) > 0
    # K-alpha band (72–76 keV) and K-beta band (83–87 keV) both populated.
    ka = np.sum((energies > 0.072) & (energies < 0.076))
    kb = np.sum((energies > 0.083) & (energies < 0.087))
    assert ka > 0.1 * _N_SAMPLE, f"too few K-alpha events: {ka}"
    assert kb > 0.01 * _N_SAMPLE, f"too few K-beta events: {kb}"
    # K-alpha is the dominant characteristic line.
    assert ka > kb


def test_no_k_lines_below_edge():
    """Below the Pb K-edge the K lines must be absent (K shell inaccessible)."""
    mcdc, data = _state(82)
    energies = _sample_emissions(mcdc, data, 0.070)  # 70 keV < 88 keV K-edge
    if len(energies) > 0:
        # No photons near the K lines; any emission is soft (L) fluorescence.
        assert np.max(energies) < _PB_K_EDGE
        assert np.sum((energies > 0.072) & (energies < 0.087)) == 0


def test_emitted_energy_never_exceeds_incident():
    """A fluorescence line can never carry more than the incident photon energy."""
    mcdc, data = _state(82)
    for E in (0.09, 0.12, 0.2):
        energies = _sample_emissions(mcdc, data, E, n=5000)
        if len(energies) > 0:
            assert np.max(energies) <= E + 1e-12


def test_cascade_can_emit_two_photons():
    """A K radiative transition to an L shell can trigger a second (L) photon."""
    mcdc, data = _state(82)
    two = 0
    for i in range(_N_SAMPLE):
        p = _photon(0.15, 2 * i + 1)
        n_ph, _e1, _e2 = sample_photoelectric_emission(p, mcdc, data)
        if n_ph == 2:
            two += 1
    assert two > 0, "expected some K->L cascade double emissions"


def test_fluorescence_can_be_effectively_disabled_by_low_z():
    """Low-Z (Al) yields negligible high-energy fluorescence (tiny omega)."""
    mcdc, data = _state(13)  # Al
    energies = _sample_emissions(mcdc, data, 0.05, n=10000)
    # Al K fluorescence yield is ~0.04 and lines are ~1.5 keV; no hard X-rays.
    if len(energies) > 0:
        assert np.max(energies) < 0.01
