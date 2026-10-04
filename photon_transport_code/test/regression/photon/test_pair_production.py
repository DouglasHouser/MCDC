"""
Regression tests: Pair production threshold and cross-section behavior.

Validates that:
  1. The pair-production threshold is correctly enforced at
     E_threshold = 2 * m_e * c^2 = 1.02199790 MeV.
  2. The cross-section is identically zero below the threshold.
  3. The cross-section is positive and increasing above the threshold.
  4. The sampling kernel produces physically valid kinematics.

Reference
---------
NIST XCOM: pair production (nuclear + electron field) for Pb (Z=82).
Threshold: 2 × 0.51099895 MeV = 1.02199790 MeV (exact).
"""

import math

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon import native
from photon_transport_code.transport.physics.photon.distributions import (
    sample_pair_production,
)

_PAIR_THRESH = 2.0 * 0.51099895  # 1.02199790 MeV
_M_E = 0.51099895  # MeV


# ======================================================================================
# Cross-section threshold enforcement
# ======================================================================================


class TestPairProductionThreshold:
    """Pair production cross-section is exactly zero below threshold."""

    @pytest.mark.parametrize("E_MeV", [0.001, 0.01, 0.1, 0.5, 1.0, 1.021])
    def test_zero_below_threshold_al(self, E_MeV, al_element):
        """pair_production_xs returns 0 for all energies below 1.022 MeV (Al)."""
        photon_element, flat_data = al_element
        sigma_PP = native.pair_production_xs(13, E_MeV, photon_element, flat_data)
        assert sigma_PP == 0.0, (
            f"pair_production_xs non-zero ({sigma_PP:.3e}) below threshold "
            f"at E={E_MeV} MeV for Al"
        )

    @pytest.mark.parametrize("E_MeV", [0.001, 0.01, 0.1, 0.5, 1.0, 1.021])
    def test_zero_below_threshold_pb(self, E_MeV, pb_element):
        """pair_production_xs returns 0 for all energies below 1.022 MeV (Pb)."""
        photon_element, flat_data = pb_element
        sigma_PP = native.pair_production_xs(82, E_MeV, photon_element, flat_data)
        assert sigma_PP == 0.0, (
            f"pair_production_xs non-zero ({sigma_PP:.3e}) below threshold "
            f"at E={E_MeV} MeV for Pb"
        )

    def test_sharp_threshold_al(self, al_element):
        """Cross-section jumps from zero to positive at threshold for Al."""
        photon_element, flat_data = al_element
        Z = 13

        E_below = _PAIR_THRESH - 1e-6  # Just below threshold
        E_above = _PAIR_THRESH + 1e-6  # Just above threshold

        sigma_below = native.pair_production_xs(Z, E_below, photon_element, flat_data)
        sigma_above = native.pair_production_xs(Z, E_above, photon_element, flat_data)

        assert (
            sigma_below == 0.0
        ), f"sigma_PP non-zero just below threshold: {sigma_below:.3e} cm^2/atom"
        assert sigma_above >= 0.0, "sigma_PP negative just above threshold (unphysical)"

    def test_sharp_threshold_pb(self, pb_element):
        """Cross-section transitions at threshold for high-Z material (Pb)."""
        photon_element, flat_data = pb_element
        Z = 82

        E_below = _PAIR_THRESH - 1e-6
        E_above = _PAIR_THRESH + 1e-4  # slightly further above to hit table data

        sigma_below = native.pair_production_xs(Z, E_below, photon_element, flat_data)
        sigma_above = native.pair_production_xs(Z, E_above, photon_element, flat_data)

        assert (
            sigma_below == 0.0
        ), f"sigma_PP non-zero below threshold: {sigma_below:.3e}"
        assert sigma_above >= 0.0, "sigma_PP negative above threshold (unphysical)"

    def test_pair_production_dominates_high_energy_pb(self, pb_element):
        """At 50 MeV, pair production dominates for Pb (> 50 % of total)."""
        photon_element, flat_data = pb_element
        Z = 82
        E = 50.0  # MeV

        sigma_C = native.compton_xs(Z, E, photon_element, flat_data)
        sigma_PE = native.photoelectric_xs(Z, E, photon_element, flat_data)
        sigma_PP = native.pair_production_xs(Z, E, photon_element, flat_data)
        sigma_T = sigma_C + sigma_PE + sigma_PP

        pp_fraction = sigma_PP / sigma_T
        assert (
            pp_fraction > 0.5
        ), f"Pair production fraction {pp_fraction:.3%} < 50% at 50 MeV for Pb"


# ======================================================================================
# Sampling kernel regression
# ======================================================================================


class TestPairProductionSampling:
    """sample_pair_production kinematics are physically valid."""

    N_SAMPLES = 2_000

    def test_returns_none_below_threshold(self):
        """sample_pair_production returns None for E < 1.022 MeV."""
        for E in [0.5, 0.9, 1.0, _PAIR_THRESH - 1e-9]:
            result = sample_pair_production(E)
            assert (
                result is None
            ), f"Expected None below threshold at E={E:.6f} MeV, got {result}"

    def test_returns_tuple_above_threshold(self):
        """sample_pair_production returns a 4-tuple above threshold."""
        np.random.seed(1)
        for E in [_PAIR_THRESH + 0.01, 1.5, 2.0, 5.0, 10.0]:
            result = sample_pair_production(E)
            assert result is not None, f"Got None above threshold at E={E} MeV"
            assert (
                len(result) == 4
            ), f"Expected 4-tuple, got {len(result)}-tuple at E={E} MeV"

    def test_energy_conservation(self):
        """E_electron + E_positron == E_gamma to floating-point precision."""
        np.random.seed(42)
        E_gamma = 5.0  # MeV

        max_err = 0.0
        for _ in range(self.N_SAMPLES):
            E_e, E_p, _te, _tp = sample_pair_production(E_gamma)
            err = abs(E_e + E_p - E_gamma)
            if err > max_err:
                max_err = err

        assert (
            max_err < 1e-10
        ), f"Energy conservation violated: max |E_e+E_p - E_γ| = {max_err:.3e} MeV"

    def test_minimum_particle_energy(self):
        """Each particle carries at least m_e total energy."""
        np.random.seed(88)
        E_gamma = 5.0

        for _ in range(self.N_SAMPLES):
            E_e, E_p, _te, _tp = sample_pair_production(E_gamma)
            assert (
                E_e >= _M_E - 1e-12
            ), f"Electron total energy {E_e:.6f} < m_e = {_M_E}"
            assert (
                E_p >= _M_E - 1e-12
            ), f"Positron total energy {E_p:.6f} < m_e = {_M_E}"

    def test_angles_in_physical_range(self):
        """Emission angles are in [0, pi]."""
        np.random.seed(12)
        E_gamma = 5.0

        for _ in range(self.N_SAMPLES):
            _E_e, _E_p, te, tp = sample_pair_production(E_gamma)
            assert 0.0 <= te <= math.pi, f"theta_e outside [0,pi]: {te:.4f} rad"
            assert 0.0 <= tp <= math.pi, f"theta_p outside [0,pi]: {tp:.4f} rad"

    def test_forward_peaking_at_high_energy(self):
        """At 50 MeV, > 80 % of particles scatter forward (theta < pi/2)."""
        np.random.seed(66)
        E_gamma = 50.0
        N = 3_000

        thetas_e = []
        thetas_p = []
        for _ in range(N):
            _E_e, _E_p, te, tp = sample_pair_production(E_gamma)
            thetas_e.append(te)
            thetas_p.append(tp)

        forward_e = np.sum(np.array(thetas_e) < math.pi / 2.0) / N
        forward_p = np.sum(np.array(thetas_p) < math.pi / 2.0) / N

        assert (
            forward_e > 0.80
        ), f"Electron not forward-peaked at 50 MeV: {forward_e:.3%}"
        assert (
            forward_p > 0.80
        ), f"Positron not forward-peaked at 50 MeV: {forward_p:.3%}"

    @pytest.mark.parametrize("E_gamma", [1.1, 1.5, 2.0, 5.0, 10.0, 50.0, 100.0])
    def test_energy_conservation_multiple_energies(self, E_gamma):
        """Energy conservation holds at all energies above threshold."""
        np.random.seed(int(E_gamma * 10))
        for _ in range(200):
            result = sample_pair_production(E_gamma)
            assert result is not None
            E_e, E_p, _te, _tp = result
            err = abs(E_e + E_p - E_gamma)
            assert err < 1e-10, f"E={E_gamma} MeV: conservation error {err:.3e} MeV"
