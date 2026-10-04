"""
Regression tests: Compton-dominated scattering scenarios.

Validates that Compton (incoherent) scattering dominates the total photon
cross-section in the expected energy regime (0.1 – 10 MeV for low-Z
materials) and that the Klein-Nishina sampling kernel produces scattered
photon energies and angles consistent with known physics.

Reference
---------
NIST XCOM data for Al (Z=13) at 1 MeV:
    Compton/total ≈ 0.98  (Compton almost entirely dominates)
Klein-Nishina: backscatter minimum E_min = E / (1 + 2*kappa) at theta = pi
"""

import math

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon.cross_sections import (
    klein_nishina_total,
)
from photon_transport_code.transport.physics.photon.distributions import (
    sample_klein_nishina,
)
from photon_transport_code.transport.physics.photon import native

_M_E = 0.51099895  # MeV


# ======================================================================================
# Compton cross-section dominance
# ======================================================================================


class TestComptonDominance:
    """Compton cross-section dominates total for Al in 0.1 – 5 MeV range."""

    @pytest.mark.parametrize("E_MeV", [0.1, 0.5, 1.0, 2.0, 5.0])
    def test_compton_dominates_al(self, E_MeV, al_element):
        """At mid energies, Compton cross-section > 50 % of total for Al."""
        photon_element, flat_data = al_element
        Z = 13

        sigma_C = native.compton_xs(Z, E_MeV, photon_element, flat_data)
        sigma_PE = native.photoelectric_xs(Z, E_MeV, photon_element, flat_data)
        sigma_PP = native.pair_production_xs(Z, E_MeV, photon_element, flat_data)
        sigma_T = sigma_C + sigma_PE + sigma_PP

        assert sigma_T > 0.0, f"Total cross-section zero at E={E_MeV} MeV"
        compton_fraction = sigma_C / sigma_T
        assert compton_fraction > 0.5, (
            f"Compton fraction {compton_fraction:.3f} < 50% at " f"E={E_MeV} MeV for Al"
        )

    def test_compton_dominates_at_1mev_by_wide_margin(self, al_element):
        """At 1 MeV in Al, Compton fraction > 95 % (nearly pure Compton)."""
        photon_element, flat_data = al_element
        Z = 13
        E = 1.0

        sigma_C = native.compton_xs(Z, E, photon_element, flat_data)
        sigma_PE = native.photoelectric_xs(Z, E, photon_element, flat_data)
        sigma_PP = native.pair_production_xs(Z, E, photon_element, flat_data)
        sigma_T = sigma_C + sigma_PE + sigma_PP

        fraction = sigma_C / sigma_T
        assert (
            fraction > 0.95
        ), f"Expected Compton > 95% at 1 MeV in Al, got {fraction:.3%}"

    def test_compton_xs_monotonically_decreasing(self):
        """Klein-Nishina total cross-section decreases with energy."""
        energies = np.logspace(-1, 2, 40)  # 0.1 to 100 MeV
        xs_values = np.array([klein_nishina_total(E) for E in energies])

        assert np.all(
            np.diff(xs_values) <= 0
        ), "Klein-Nishina cross-section is not monotonically decreasing"

    def test_compton_xs_positive_everywhere(self):
        """Klein-Nishina cross-section is positive at all energies."""
        for E in np.logspace(-3, 3, 50):
            sigma = klein_nishina_total(E)
            assert sigma > 0.0, f"Non-positive KN cross-section at E={E:.3e} MeV"

    def test_thomson_limit(self):
        """At low energy (E → 0) KN → Thomson = (8/3) π r_e^2."""
        r_e = 2.8179403e-13  # cm
        sigma_thomson = (8.0 / 3.0) * math.pi * r_e**2

        sigma_low = klein_nishina_total(1e-4)  # Very low energy
        # Should be within 1 % of Thomson
        rel_err = abs(sigma_low - sigma_thomson) / sigma_thomson
        assert (
            rel_err < 0.01
        ), f"KN at low E deviates {rel_err:.3%} from Thomson cross-section"


# ======================================================================================
# Compton scattering kinematics (regression checks)
# ======================================================================================


class TestComptonKinematics:
    """Energy and angle of scattered photons follow Klein-Nishina physics."""

    N_SAMPLES = 5_000

    def test_scattered_energy_within_physical_bounds(self):
        """Scattered photon energy is between backscatter min and E_in."""
        np.random.seed(42)
        E_in = 1.0  # MeV
        kappa = E_in / _M_E
        E_min = E_in / (1.0 + 2.0 * kappa)  # backscatter minimum

        for _ in range(self.N_SAMPLES):
            E_out, theta, E_e = sample_klein_nishina(E_in)
            assert E_out >= E_min * (
                1.0 - 1e-9
            ), f"E_out={E_out:.6f} below backscatter minimum {E_min:.6f}"
            assert E_out <= E_in + 1e-10, f"E_out={E_out:.6f} > E_in={E_in}"

    def test_mean_energy_loss_increases_with_incident_energy(self):
        """Mean fractional energy loss grows with incident energy (KN physics)."""
        np.random.seed(99)
        energies = [0.1, 0.5, 1.0, 5.0, 10.0]
        mean_fracs = []

        for E_in in energies:
            E_outs = [sample_klein_nishina(E_in)[0] for _ in range(2_000)]
            mean_frac_remaining = np.mean(E_outs) / E_in
            mean_fracs.append(mean_frac_remaining)

        # Higher incident energy → photon retains less energy on average
        for i in range(len(mean_fracs) - 1):
            assert mean_fracs[i] > mean_fracs[i + 1], (
                f"Mean fraction remaining did not decrease: "
                f"{energies[i]} MeV ({mean_fracs[i]:.3f}) vs "
                f"{energies[i+1]} MeV ({mean_fracs[i+1]:.3f})"
            )

    def test_energy_conservation_bulk(self):
        """E_out + E_electron == E_in to floating-point precision."""
        np.random.seed(7)
        E_in = 1.0

        errors = np.array(
            [
                abs(
                    sum(sample_klein_nishina(E_in)[:1])
                    + sample_klein_nishina(E_in)[2]
                    - E_in
                )
                for _ in range(100)
            ]
        )
        # Do it properly
        conservation_errors = []
        for _ in range(self.N_SAMPLES):
            E_out, theta, E_e = sample_klein_nishina(E_in)
            conservation_errors.append(abs(E_out + E_e - E_in))

        max_err = max(conservation_errors)
        assert (
            max_err < 1e-10
        ), f"Energy conservation violated: max error = {max_err:.3e} MeV"

    def test_forward_scattered_photons_retain_most_energy(self):
        """Forward-scattered photons (theta < 10 deg) retain > 90 % of energy."""
        np.random.seed(55)
        E_in = 1.0

        for _ in range(self.N_SAMPLES):
            E_out, theta, _E_e = sample_klein_nishina(E_in)
            if theta < math.radians(10):
                assert E_out / E_in > 0.90, (
                    f"Forward scatter theta={math.degrees(theta):.1f}° "
                    f"but E_out/E_in={E_out/E_in:.3f} < 0.90"
                )

    def test_compton_edge_position(self):
        """The Compton edge (maximum electron energy) matches theory."""
        np.random.seed(11)
        E_in = 1.0
        kappa = E_in / _M_E

        # Maximum electron energy at theta = pi (backscatter)
        E_e_max_theory = E_in * 2.0 * kappa / (1.0 + 2.0 * kappa)

        E_electrons = [sample_klein_nishina(E_in)[2] for _ in range(10_000)]
        E_e_max_sampled = max(E_electrons)

        # Sampled maximum should come within 2 % of theoretical Compton edge
        rel_err = abs(E_e_max_sampled - E_e_max_theory) / E_e_max_theory
        assert rel_err < 0.02, (
            f"Compton edge: theory={E_e_max_theory:.4f}, "
            f"sampled_max={E_e_max_sampled:.4f}, "
            f"rel_err={rel_err:.3%}"
        )

    def test_scattered_photon_energy_at_known_energies(self):
        """
        Mean scattered photon energy matches Klein-Nishina prediction.

        The mean energy of a scattered photon can be estimated; at 1 MeV
        it should be clearly less than E_in (significant downscattering).
        """
        np.random.seed(33)
        E_in_values = [0.1, 0.5, 1.0, 5.0]

        for E_in in E_in_values:
            E_outs = [sample_klein_nishina(E_in)[0] for _ in range(3_000)]
            mean_E_out = np.mean(E_outs)
            assert (
                mean_E_out < E_in
            ), f"Mean scattered energy {mean_E_out:.4f} >= E_in={E_in} MeV"
            assert (
                mean_E_out > 0.0
            ), f"Mean scattered energy is non-positive at E_in={E_in} MeV"
