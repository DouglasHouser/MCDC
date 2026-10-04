"""
Unit tests for Klein-Nishina total and differential cross-sections.

Validates the analytical formula against:
  - Thomson limit at low energy
  - Published free-electron KN values (Knoll 2010, Table B.1) at benchmark energies
  - Monotonic decrease with energy
  - Self-consistency: integral of differential == total

IMPORTANT: NIST XCOM "incoherent scattering" values are NOT the same as the
pure Klein-Nishina formula — NIST applies incoherent scattering function S(q,Z)
corrections for bound electrons.  The reference values below are for the
free-electron Klein-Nishina formula only.

Run with::

    pytest test/unit/photon/test_klein_nishina.py -v
"""

import math

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon.cross_sections import (
    klein_nishina_differential,
    klein_nishina_total,
)
from photon_transport_code.transport.physics.photon.util import (
    CLASSICAL_ELECTRON_RADIUS,
    THOMSON_CROSS_SECTION,
)

# ======================================================================================
# Reference values — free-electron Klein-Nishina per electron
# Source: Knoll (2010) "Radiation Detection and Measurement" 4th ed., Table B.1
#         and Evans (1955) "The Atomic Nucleus", Fig. 25-7
# Units: cm^2/electron
# ======================================================================================

# These are pure free-electron KN values, NOT NIST incoherent scattering
# (NIST includes incoherent scattering function S(q,Z) which reduces values for
# bound electrons, especially at lower energies for heavy elements)
_KN_REFERENCE = [
    # (E_MeV, sigma_cm2_per_electron, label)
    (0.1, 4.93e-25, "Knoll 2010 Table B.1"),
    (1.0, 2.12e-25, "Knoll 2010 Table B.1"),
    (5.0, 8.3e-26, "Knoll 2010 Table B.1"),
    (10.0, 5.1e-26, "Knoll 2010 Table B.1"),
]

_TOLERANCE = 0.02  # 2%


# ======================================================================================
# Thomson limit
# ======================================================================================


def test_thomson_limit_low_energy():
    """At 0.001 MeV KN cross-section should equal Thomson to within 0.5%."""
    sigma = klein_nishina_total(1e-3)
    sigma_T = THOMSON_CROSS_SECTION
    assert abs(sigma - sigma_T) / sigma_T < 0.005, (
        f"KN at 1e-3 MeV = {sigma:.4e}, Thomson = {sigma_T:.4e}, "
        f"diff = {abs(sigma-sigma_T)/sigma_T*100:.3f}%"
    )


def test_thomson_limit_very_low_energy():
    """KN formula alpha<1e-3 branch returns (8/3)*pi*r_e^2 exactly."""
    sigma = klein_nishina_total(1e-6)
    sigma_T = (8.0 / 3.0) * math.pi * CLASSICAL_ELECTRON_RADIUS**2
    assert abs(sigma - sigma_T) / sigma_T < 1e-10


# ======================================================================================
# Published reference values (±2%)
# ======================================================================================


@pytest.mark.parametrize(
    "E_MeV, expected, source",
    [(e, x, s) for (e, x, s) in _KN_REFERENCE],
)
def test_kn_reference_values(E_MeV, expected, source):
    """Klein-Nishina per electron is within 2% of published free-electron values."""
    sigma = klein_nishina_total(E_MeV)
    rel_err = abs(sigma - expected) / expected
    assert rel_err < _TOLERANCE, (
        f"E={E_MeV} MeV: KN={sigma:.4e}, ref ({source})={expected:.4e}, "
        f"err={rel_err*100:.2f}%"
    )


def test_kn_at_511kev_vs_evans():
    """KN at 0.511 MeV (alpha=1): sigma/sigma_T should be ~0.4307 (Evans 1955)."""
    sigma = klein_nishina_total(0.511)
    ratio = sigma / THOMSON_CROSS_SECTION
    # Evans (1955) Fig 25-7: at alpha=1, sigma/sigma_T ≈ 0.431
    assert (
        abs(ratio - 0.431) < 0.01
    ), f"sigma/sigma_T at 0.511 MeV = {ratio:.4f}, expected ~0.431"


# ======================================================================================
# Monotonic decrease
# ======================================================================================


def test_monotonically_decreasing():
    """Klein-Nishina total cross-section decreases with increasing energy."""
    energies = np.logspace(-2, 2, 50)
    values = np.array([klein_nishina_total(E) for E in energies])
    diffs = np.diff(values)
    assert np.all(diffs < 0), (
        "KN cross-section is not monotonically decreasing; "
        f"first non-decreasing index: {np.where(diffs >= 0)[0][0]}"
    )


def test_positive_at_all_energies():
    """Klein-Nishina total is strictly positive across full energy range."""
    energies = np.logspace(-3, 2, 100)
    for E in energies:
        sigma = klein_nishina_total(E)
        assert sigma > 0.0, f"KN cross-section non-positive at E={E} MeV: {sigma}"


# ======================================================================================
# Differential cross-section
# ======================================================================================


def test_differential_forward_scatter():
    """Forward scatter (mu=1) gives maximum differential cross-section."""
    E = 1.0
    ds_forward = klein_nishina_differential(E, mu=1.0)
    ds_back = klein_nishina_differential(E, mu=-1.0)
    assert ds_forward > ds_back, "Forward scatter should exceed back scatter at 1 MeV"


def test_differential_positive():
    """Differential cross-section is positive for all mu in [-1, 1]."""
    E = 1.0
    for mu in np.linspace(-1.0, 1.0, 20):
        ds = klein_nishina_differential(E, mu)
        assert ds > 0.0, f"Differential KN non-positive at mu={mu}: {ds}"


def test_differential_thomson_limit():
    """At very low energy, differential KN approaches (r_e^2/2)(1+cos^2(theta))."""
    E = 1e-4  # effectively Thomson
    r_e = CLASSICAL_ELECTRON_RADIUS
    for mu in np.linspace(-1.0, 1.0, 10):
        ds_kn = klein_nishina_differential(E, mu)
        ds_thomson = 0.5 * r_e**2 * (1.0 + mu**2)
        rel_err = abs(ds_kn - ds_thomson) / ds_thomson
        assert rel_err < 0.01, (
            f"mu={mu}: KN_diff={ds_kn:.4e}, Thomson_diff={ds_thomson:.4e}, "
            f"err={rel_err*100:.2f}%"
        )


def test_differential_integration_matches_total():
    """Numerical integration of differential KN matches total KN within 1%."""
    E = 1.0
    n_pts = 10000
    mu_vals = np.linspace(-1.0, 1.0, n_pts)
    ds_vals = np.array([klein_nishina_differential(E, mu) for mu in mu_vals])
    # sigma = 2*pi * integral_{-1}^{1} (d_sigma/d_Omega) d(mu)
    sigma_numerical = 2.0 * math.pi * np.trapz(ds_vals, mu_vals)
    sigma_analytic = klein_nishina_total(E)
    rel_err = abs(sigma_numerical - sigma_analytic) / sigma_analytic
    assert rel_err < 0.01, (
        f"Numerical integral={sigma_numerical:.4e}, "
        f"analytic={sigma_analytic:.4e}, err={rel_err*100:.2f}%"
    )


# ======================================================================================
# High-energy asymptotic and relative behavior
# ======================================================================================


def test_high_energy_asymptotic():
    """At 100 MeV, KN cross-section is well below Thomson/10 (relativistic)."""
    sigma_100 = klein_nishina_total(100.0)
    sigma_T = THOMSON_CROSS_SECTION
    # At alpha=196, sigma_KN << sigma_T.  sigma_KN/sigma_T ~ 0.012
    assert (
        sigma_100 < sigma_T / 10.0
    ), f"At 100 MeV KN={sigma_100:.4e} should be < sigma_T/10={sigma_T/10:.4e}"


def test_ratio_10_to_1_mev():
    """sigma(1 MeV) > 4 × sigma(10 MeV) — cross-section decreases significantly."""
    sigma_1 = klein_nishina_total(1.0)
    sigma_10 = klein_nishina_total(10.0)
    ratio = sigma_1 / sigma_10
    assert ratio > 4.0, (
        f"sigma(1 MeV)={sigma_1:.4e}, sigma(10 MeV)={sigma_10:.4e}, "
        f"ratio={ratio:.2f} should be > 4"
    )
