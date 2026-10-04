"""
Unit tests for total photon cross-section.

Validates:
  - total_xs == compton + photoelectric + pair at all test energies
  - Physical regime dominance (PE dominates low E, Compton mid, PP high)
  - Correct sign and ordering across elements
  - Water composite interpolation works

NOTE on "NIST comparison": this code uses the free-electron Klein-Nishina formula
for Compton (not form-factor-corrected incoherent scattering as in NIST XCOM).
Total = KN × Z + PE_NIST + PP_NIST.  The PE and PP are validated separately in
test_photoelectric.py and test_pair_production.py to ±2% of NIST XCOM tables.

Run with::

    pytest test/unit/photon/test_total_xsec.py -v
"""

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon.cross_sections import (
    klein_nishina_total,
    pair_production_xs,
    photoelectric_xs,
    total_xs,
)
from photon_transport_code.transport.physics.photon.data_loader import (
    load_photon_element,
    load_water_data,
)
from photon_transport_code.transport.physics.photon.native import (
    _loglog_interp_python,
    build_element_buffer,
)

# ======================================================================================
# Fixtures
# ======================================================================================


@pytest.fixture(scope="module")
def al_buffer():
    """Return (photon_element, flat_data) for Aluminum Z=13."""
    return build_element_buffer(13)


@pytest.fixture(scope="module")
def pb_buffer():
    """Return (photon_element, flat_data) for Lead Z=82."""
    return build_element_buffer(82)


@pytest.fixture(scope="module")
def al_data(al_buffer):
    return al_buffer[1]


@pytest.fixture(scope="module")
def pb_data(pb_buffer):
    return pb_buffer[1]


# ======================================================================================
# Additivity: total == sum of components (self-consistency, must be exact)
# ======================================================================================


@pytest.mark.parametrize("E_MeV", [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0])
def test_al_total_equals_sum(E_MeV, al_data):
    """total_xs == compton + photoelectric + pair for Al at all energies."""
    Z = 13
    sigma_C = klein_nishina_total(E_MeV) * Z
    sigma_PE = photoelectric_xs(Z, E_MeV, al_data)
    sigma_PP = pair_production_xs(Z, E_MeV, al_data)
    expected = sigma_C + sigma_PE + sigma_PP
    actual = total_xs(Z, E_MeV, al_data)
    assert (
        abs(actual - expected) / expected < 1e-12
    ), f"Al total_xs != sum at {E_MeV} MeV: {actual:.6e} vs {expected:.6e}"


@pytest.mark.parametrize("E_MeV", [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0])
def test_pb_total_equals_sum(E_MeV, pb_data):
    """total_xs == compton + photoelectric + pair for Pb at all energies."""
    Z = 82
    sigma_C = klein_nishina_total(E_MeV) * Z
    sigma_PE = photoelectric_xs(Z, E_MeV, pb_data)
    sigma_PP = pair_production_xs(Z, E_MeV, pb_data)
    expected = sigma_C + sigma_PE + sigma_PP
    actual = total_xs(Z, E_MeV, pb_data)
    assert (
        abs(actual - expected) / expected < 1e-12
    ), f"Pb total_xs != sum at {E_MeV} MeV: {actual:.6e} vs {expected:.6e}"


# ======================================================================================
# Regime dominance — physical sanity checks
# ======================================================================================


def test_pe_dominates_low_energy_pb(pb_data):
    """At 0.01 MeV, photoelectric strongly dominates total for Pb."""
    E = 0.01  # 10 keV — PE >> Compton even with pure KN formula
    Z = 82
    sigma_PE = photoelectric_xs(Z, E, pb_data)
    sigma_total = total_xs(Z, E, pb_data)
    assert (
        sigma_PE > 0.8 * sigma_total
    ), f"PE should dominate at {E} MeV for Pb: PE={sigma_PE:.4e}, total={sigma_total:.4e}"


def test_compton_dominates_mid_energy_al(al_data):
    """At 1 MeV, Compton dominates total for Al (light element, no pair)."""
    E = 1.0
    Z = 13
    sigma_C = klein_nishina_total(E) * Z
    sigma_total = total_xs(Z, E, al_data)
    assert (
        sigma_C > 0.9 * sigma_total
    ), f"Compton should dominate at {E} MeV for Al: C={sigma_C:.4e}, total={sigma_total:.4e}"


def test_pair_significant_high_energy_pb(pb_data):
    """At 10 MeV, pair production contributes significantly to Pb total."""
    E = 10.0
    Z = 82
    sigma_PP = pair_production_xs(Z, E, pb_data)
    sigma_total = total_xs(Z, E, pb_data)
    assert (
        sigma_PP > 0.3 * sigma_total
    ), f"PP should be >30%% at {E} MeV for Pb: PP={sigma_PP:.4e}, total={sigma_total:.4e}"


def test_pb_total_greater_than_al(al_data, pb_data):
    """Pb total cross-section always larger than Al (higher Z)."""
    for E in [0.1, 1.0, 5.0, 10.0]:
        sigma_al = total_xs(13, E, al_data)
        sigma_pb = total_xs(82, E, pb_data)
        assert (
            sigma_pb > sigma_al
        ), f"At {E} MeV: Pb total={sigma_pb:.4e} should be > Al total={sigma_al:.4e}"


# ======================================================================================
# Positivity and finiteness
# ======================================================================================


def test_total_xs_always_positive(al_data, pb_data):
    """total_xs is strictly positive and finite for all test cases."""
    energies = np.logspace(-2, 2, 30)
    for E in energies:
        for Z, data in [(13, al_data), (82, pb_data)]:
            sigma = total_xs(Z, E, data)
            assert sigma > 0.0 and np.isfinite(
                sigma
            ), f"Z={Z}, E={E}: total sigma={sigma} invalid"


# ======================================================================================
# Pair production threshold in total
# ======================================================================================


def test_total_below_pp_threshold_excludes_pair(al_data):
    """Below 1.022 MeV, total_xs equals compton + PE only (PP=0)."""
    for E in [0.5, 0.9, 1.021]:
        Z = 13
        sigma_C = klein_nishina_total(E) * Z
        sigma_PE = photoelectric_xs(Z, E, al_data)
        sigma_total = total_xs(Z, E, al_data)
        expected = sigma_C + sigma_PE
        assert (
            abs(sigma_total - expected) / expected < 1e-12
        ), f"At E={E} MeV: total={sigma_total:.6e} != C+PE={expected:.6e}"


def test_total_above_pp_threshold_includes_pair(al_data):
    """Above 1.022 MeV, total_xs is greater than compton + PE alone."""
    for E in [1.25, 2.0, 5.0, 10.0]:
        Z = 13
        sigma_C = klein_nishina_total(E) * Z
        sigma_PE = photoelectric_xs(Z, E, al_data)
        sigma_PP = pair_production_xs(Z, E, al_data)
        sigma_total = total_xs(Z, E, al_data)
        # PP is non-zero above threshold
        assert sigma_PP > 0.0, f"PP should be non-zero at E={E} MeV"
        assert (
            sigma_total > sigma_C + sigma_PE
        ), f"At E={E} MeV: total should include PP contribution"


# ======================================================================================
# Water (H2O composite)
# ======================================================================================


def test_water_total_positive():
    """Water (H2O) effective cross-section is positive at benchmark energies."""
    energies, compton, pe, pair = load_water_data()
    for E in [0.1, 1.0, 5.0, 10.0]:
        sigma_C = _loglog_interp_python(E, energies, compton)
        sigma_PE = _loglog_interp_python(E, energies, pe)
        sigma_PP = _loglog_interp_python(E, energies, pair)
        total = sigma_C + sigma_PE + sigma_PP
        assert total > 0.0 and np.isfinite(
            total
        ), f"Water total non-positive at E={E} MeV: {total}"


def test_water_data_has_two_elements():
    """Water data combines contributions from H and O."""
    energies, compton, pe, pair = load_water_data()
    e_h, _, _, _ = load_photon_element(1)
    e_o, _, _, _ = load_photon_element(8)
    assert len(energies) >= max(
        len(e_h), len(e_o)
    ), "Water energy grid too short"


def test_water_compton_between_h_and_o_scaled():
    """At 1 MeV, water compton ≈ 2*H_compton + 1*O_compton."""
    e_h, c_h, _, _ = load_photon_element(1)
    e_o, c_o, _, _ = load_photon_element(8)
    e_w, c_w, _, _ = load_water_data()

    E = 1.0
    ch_interp = _loglog_interp_python(E, e_h, c_h)
    co_interp = _loglog_interp_python(E, e_o, c_o)
    cw_interp = _loglog_interp_python(E, e_w, c_w)

    expected = 2.0 * ch_interp + co_interp
    rel_err = abs(cw_interp - expected) / expected
    assert rel_err < 1e-10, f"Water compton mismatch: {cw_interp:.4e} vs {expected:.4e}"
