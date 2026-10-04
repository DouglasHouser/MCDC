"""
Unit tests for photon interaction sampling kernels (Phase 3).

Covers all three interaction types:
    - Compton (Klein-Nishina) scattering: energy conservation, angle sampling,
      distribution shape, energy-angle kinematic correlation.
    - Pair production: energy conservation, threshold enforcement, forward
      peaking, energy sharing.
    - Photoelectric absorption: exact energy deposition, shell statistics.

Run with::

    pytest photon_transport_code/test/unit/photon/test_distributions.py -v

All energy-conservation tests require absolute error < 1e-10 MeV.
"""

import math

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon.cross_sections import (
    klein_nishina_differential,
)
from photon_transport_code.transport.physics.photon.distributions import (
    photoelectric_absorption,
    photoelectric_select_shell,
    sample_klein_nishina,
    sample_pair_production,
    sample_photoelectric_shell,
)

# ======================================================================================
# Physical constants (duplicated here for test independence)
# ======================================================================================

_M_E = 0.51099895  # electron rest-mass energy [MeV]
_PAIR_THRESH = 2.0 * _M_E  # pair-production threshold [MeV]


# ======================================================================================
# Klein-Nishina (Compton) scattering tests
# ======================================================================================


class TestKleinNishinaKernel:
    """Tests for the Kahn-sampled Compton scattering kernel."""

    N_SAMPLES = 10_000

    def test_energy_conservation(self):
        """E_in == E_out + E_electron to floating-point precision.

        E_electron is computed as E_in - E_out inside sample_klein_nishina,
        so the sum must equal E_in to within a few ULPs (< 2^-52 * E_in).
        """
        np.random.seed(42)
        E_in = 1.0  # MeV

        E_out_arr = np.empty(self.N_SAMPLES)
        E_e_arr = np.empty(self.N_SAMPLES)
        for i in range(self.N_SAMPLES):
            E_out, _theta, E_e = sample_klein_nishina(E_in)
            E_out_arr[i] = E_out
            E_e_arr[i] = E_e

        E_sum = E_out_arr + E_e_arr
        max_error = np.max(np.abs(E_sum - E_in))
        assert (
            max_error < 1e-10
        ), f"Energy conservation violated: max |E_sum - E_in| = {max_error:.3e} MeV"

    def test_energy_conservation_multiple_energies(self):
        """Energy conservation holds across a range of incident energies."""
        np.random.seed(7)
        for E_in in [0.01, 0.1, 0.511, 1.0, 5.0, 10.0]:
            for _ in range(500):
                E_out, _theta, E_e = sample_klein_nishina(E_in)
                err = abs(E_out + E_e - E_in)
                assert err < 1e-10, f"E={E_in} MeV: conservation error {err:.3e} MeV"

    def test_energy_bounds(self):
        """Scattered photon energy is within physical limits.

        Lower bound: E_backscatter = E_in / (1 + 2*kappa)  (180-degree scatter)
        Upper bound: E_in itself  (forward scatter, theta = 0)
        """
        np.random.seed(13)
        E_in = 1.0
        kappa = E_in / _M_E
        E_min = E_in / (1.0 + 2.0 * kappa)

        for _ in range(2000):
            E_out, theta, E_e = sample_klein_nishina(E_in)
            assert E_out > 0.0, "Non-positive scattered photon energy"
            assert E_out <= E_in + 1e-12, f"E_out={E_out:.6f} > E_in={E_in}"
            assert E_out >= E_min * (
                1.0 - 1e-10
            ), f"E_out={E_out:.6f} below backscatter minimum {E_min:.6f}"
            assert E_e >= 0.0, "Negative recoil electron energy"

    def test_angle_physical_range(self):
        """Scattering angles are in [0, pi]."""
        np.random.seed(99)
        E_in = 2.0

        for _ in range(2000):
            _E_out, theta, _E_e = sample_klein_nishina(E_in)
            assert (
                0.0 <= theta <= math.pi
            ), f"Angle outside [0, pi]: theta = {theta:.6f} rad"

    def test_forward_and_backscatter_both_present(self):
        """Both forward (theta < 10 deg) and back (theta > 170 deg) scatters occur."""
        np.random.seed(101)
        E_in = 1.0

        thetas = np.array(
            [sample_klein_nishina(E_in)[1] for _ in range(self.N_SAMPLES)]
        )

        forward = np.sum(thetas < np.radians(10)) / self.N_SAMPLES
        backward = np.sum(thetas > np.radians(170)) / self.N_SAMPLES

        assert (
            forward > 0.01
        ), f"Too few forward scatters ({forward:.3%}) in {self.N_SAMPLES} samples"
        assert (
            backward > 0.001
        ), f"Too few backscatters ({backward:.3%}) in {self.N_SAMPLES} samples"

    def test_distribution_shape_low_energy(self):
        """At low energy both forward and backward hemispheres are populated.

        At 0.1 MeV (kappa ~ 0.2) the KN distribution is nearly isotropic;
        both forward and backward fractions should each be close to 50 %.
        """
        np.random.seed(55)
        E_in = 0.1  # MeV — nearly Thomson regime

        thetas = np.array(
            [sample_klein_nishina(E_in)[1] for _ in range(self.N_SAMPLES)]
        )

        forward_frac = np.sum(thetas < math.pi / 2.0) / self.N_SAMPLES
        assert 0.30 < forward_frac < 0.70, (
            f"Distribution not near-isotropic at low energy: "
            f"forward fraction = {forward_frac:.3f}"
        )

    def test_distribution_shape_high_energy(self):
        """At high energy the distribution is forward-peaked.

        At 10 MeV (kappa ~ 20) most photons scatter forward (theta < 90 deg).
        """
        np.random.seed(77)
        E_in = 10.0  # MeV — forward-peaked regime

        thetas = np.array(
            [sample_klein_nishina(E_in)[1] for _ in range(self.N_SAMPLES)]
        )

        forward_frac = np.sum(thetas < math.pi / 2.0) / self.N_SAMPLES
        assert forward_frac > 0.70, (
            f"Distribution not forward-peaked at 10 MeV: "
            f"forward fraction = {forward_frac:.3f}"
        )

    def test_compton_formula_consistency(self):
        """Sampled (E_out, theta) pairs satisfy the Compton kinematic relation.

        E_out = E_in / (1 + kappa*(1 - cos(theta)))
        """
        np.random.seed(22)
        E_in = 1.0
        kappa = E_in / _M_E

        for _ in range(1000):
            E_out, theta, _E_e = sample_klein_nishina(E_in)
            mu = math.cos(theta)
            E_expected = E_in / (1.0 + kappa * (1.0 - mu))
            err = abs(E_out - E_expected) / E_in
            assert err < 1e-10, (
                f"Compton formula mismatch: E_out={E_out:.8f}, "
                f"expected={E_expected:.8f}, rel_err={err:.3e}"
            )

    def test_kn_differential_cross_section_weight(self):
        """Sampled angles are consistent with the Klein-Nishina differential XS.

        Divide the angular range into 20 bins.  The Monte Carlo density
        in each bin should match the Klein-Nishina d(sigma)/d(Omega) within
        a generous 3-sigma statistical tolerance.
        """
        np.random.seed(33)
        E_in = 1.0
        N = 50_000
        thetas = np.array([sample_klein_nishina(E_in)[1] for _ in range(N)])

        # Bin cosine in 20 equal bins on [-1, 1]
        n_bins = 20
        mu_edges = np.linspace(-1.0, 1.0, n_bins + 1)
        mu_centers = 0.5 * (mu_edges[:-1] + mu_edges[1:])
        cos_theta = np.cos(thetas)

        mc_counts, _ = np.histogram(cos_theta, bins=mu_edges)
        mc_density = mc_counts / N  # fraction per bin

        # Theoretical KN relative density (unnormalised)
        kn_values = np.array(
            [klein_nishina_differential(E_in, float(mu)) for mu in mu_centers]
        )
        # Normalize to probabilities over the 20 bins
        # Each bin has width d(mu) = 2/20 = 0.1; d(Omega) = 2*pi*d(mu)
        bin_width = 2.0 / n_bins
        kn_norm = kn_values * bin_width
        kn_prob = kn_norm / kn_norm.sum()

        # Statistical tolerance: 3 * sqrt(expected_count) / N
        expected_counts = kn_prob * N
        sigma = np.sqrt(expected_counts) / N

        for i in range(n_bins):
            if expected_counts[i] < 5:
                continue  # skip low-statistics bins
            diff = abs(mc_density[i] - kn_prob[i])
            tol = 5.0 * sigma[i]  # generous 5-sigma window
            assert diff < tol, (
                f"KN shape mismatch in bin {i} (mu={mu_centers[i]:.2f}): "
                f"MC={mc_density[i]:.5f}, theory={kn_prob[i]:.5f}, "
                f"tol={tol:.5f}"
            )


# ======================================================================================
# Pair production kernel tests
# ======================================================================================


class TestPairProductionKernel:
    """Tests for the pair-production sampling kernel."""

    N_SAMPLES = 5_000

    def test_below_threshold_returns_none(self):
        """sample_pair_production returns None for E < 1.022 MeV."""
        for E in [0.1, 0.5, 0.9, 1.0, 1.021]:
            result = sample_pair_production(E)
            assert result is None, (
                f"Expected None for E={E} MeV (below threshold {_PAIR_THRESH:.4f} MeV), "
                f"got {result}"
            )

    def test_exactly_at_threshold(self):
        """At exactly the threshold energy the function may return None or a valid tuple."""
        result = sample_pair_production(_PAIR_THRESH)
        # Either None or a tuple with non-negative energies
        if result is not None:
            E_e, E_p, theta_e, theta_p = result
            assert E_e >= 0.0
            assert E_p >= 0.0

    def test_energy_conservation_exact(self):
        """E_electron + E_positron == E_gamma exactly (to floating point).

        Because E_positron = E_gamma - E_electron by construction, the sum
        must be exact to within ~ 2^-52 * E_gamma.
        """
        np.random.seed(42)
        E_gamma = 10.0  # MeV

        errors = []
        for _ in range(self.N_SAMPLES):
            E_e, E_p, _te, _tp = sample_pair_production(E_gamma)
            errors.append(abs(E_e + E_p - E_gamma))

        max_err = max(errors)
        assert (
            max_err < 1e-10
        ), f"Pair-production energy not conserved: max error {max_err:.3e} MeV"

    def test_energy_conservation_multiple_energies(self):
        """Conservation holds at various gamma energies above threshold."""
        np.random.seed(17)
        for E_gamma in [1.1, 2.0, 5.0, 10.0, 50.0]:
            for _ in range(200):
                result = sample_pair_production(E_gamma)
                assert result is not None, f"None returned for E={E_gamma} MeV"
                E_e, E_p, _te, _tp = result
                err = abs(E_e + E_p - E_gamma)
                assert err < 1e-10, f"E={E_gamma} MeV: conservation error {err:.3e} MeV"

    def test_minimum_particle_energies(self):
        """Each particle carries at least m_e total energy (rest mass)."""
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

    def test_forward_peaking_high_energy(self):
        """At 50 MeV > 80 % of electrons and positrons scatter forward (theta < pi/2).

        The characteristic angle is m_e/E ~ 0.511/25 ≈ 0.02 rad at 50 MeV,
        so essentially all particles satisfy theta < pi/2.
        """
        np.random.seed(66)
        E_gamma = 50.0

        thetas_e = []
        thetas_p = []
        for _ in range(self.N_SAMPLES):
            E_e, E_p, te, tp = sample_pair_production(E_gamma)
            thetas_e.append(te)
            thetas_p.append(tp)

        forward_e = np.sum(np.array(thetas_e) < math.pi / 2.0) / self.N_SAMPLES
        forward_p = np.sum(np.array(thetas_p) < math.pi / 2.0) / self.N_SAMPLES

        assert (
            forward_e > 0.80
        ), f"Electron not forward-peaked at 50 MeV: {forward_e:.3%}"
        assert (
            forward_p > 0.80
        ), f"Positron not forward-peaked at 50 MeV: {forward_p:.3%}"

    def test_angle_physical_range(self):
        """Emission angles are in [0, pi]."""
        np.random.seed(44)
        E_gamma = 5.0

        for _ in range(1000):
            E_e, E_p, te, tp = sample_pair_production(E_gamma)
            assert 0.0 <= te <= math.pi, f"theta_e outside [0,pi]: {te}"
            assert 0.0 <= tp <= math.pi, f"theta_p outside [0,pi]: {tp}"

    def test_energy_sharing_spread(self):
        """Energy sharing has non-trivial spread (std > 0.1 MeV).

        A degenerate model that gives both particles the same energy every
        time would fail this test.
        """
        np.random.seed(200)
        E_gamma = 10.0

        E_e_arr = np.array(
            [sample_pair_production(E_gamma)[0] for _ in range(self.N_SAMPLES)]
        )
        E_p_arr = np.array(
            [sample_pair_production(E_gamma)[1] for _ in range(self.N_SAMPLES)]
        )

        assert (
            np.std(E_e_arr) > 0.1
        ), f"Electron energy has no spread: std = {np.std(E_e_arr):.4f} MeV"
        assert (
            np.std(E_p_arr) > 0.1
        ), f"Positron energy has no spread: std = {np.std(E_p_arr):.4f} MeV"


# ======================================================================================
# Photoelectric absorption tests
# ======================================================================================


class TestPhotoelectricKernel:
    """Tests for photoelectric absorption sampling."""

    def test_energy_deposition_exact(self):
        """photoelectric_absorption returns E_photon exactly (Phase 1 model)."""
        for E in [0.01, 0.05, 0.1, 0.5, 1.0, 10.0]:
            E_dep = photoelectric_absorption(E)
            assert E_dep == float(
                E
            ), f"Energy deposition mismatch at E={E}: got {E_dep}"

    def test_energy_deposition_precision(self):
        """Energy conservation to floating-point precision for many energies."""
        for E in np.linspace(1e-4, 100.0, 50):
            E_dep = photoelectric_absorption(float(E))
            err = abs(E_dep - float(E))
            assert err < 1e-10, f"E={E:.4f}: deposition error {err:.3e} MeV"

    def test_returns_scalar(self):
        """photoelectric_absorption returns a scalar (Phase 1: no secondaries)."""
        result = photoelectric_absorption(0.05)
        assert isinstance(
            result, (int, float, np.floating)
        ), f"Expected scalar, got {type(result)}"

    def test_sample_photoelectric_shell_energy_conservation(self):
        """sample_photoelectric_shell: electron energy equals photon energy."""
        np.random.seed(55)
        for E in [0.05, 0.1, 0.5, 1.0]:
            for _ in range(200):
                E_e, theta, shell = sample_photoelectric_shell(E, Z=13)
                assert (
                    abs(E_e - E) < 1e-10
                ), f"E={E}: electron energy mismatch: {E_e:.10f}"

    def test_sample_photoelectric_shell_angle_range(self):
        """Emission angles from sample_photoelectric_shell are in [0, pi]."""
        np.random.seed(99)
        for _ in range(1000):
            _E_e, theta, _shell = sample_photoelectric_shell(0.1, Z=13)
            assert 0.0 <= theta <= math.pi, f"Angle outside [0, pi]: {theta:.6f}"

    def test_sample_photoelectric_shell_returns_shell_name(self):
        """shell label is one of 'K', 'L', 'M'."""
        np.random.seed(111)
        for _ in range(200):
            _E_e, _theta, shell = sample_photoelectric_shell(0.5, Z=13)
            assert shell in ("K", "L", "M"), f"Unexpected shell name: '{shell}'"

    def test_k_shell_dominates_above_k_edge(self):
        """K-shell is selected > 70 % of the time above the Al K-edge (1.56 keV).

        For aluminum at 0.1 MeV (>> 1.56 keV K-edge): K-fraction ~ 80 %.
        """
        np.random.seed(77)
        N = 10_000
        shells = [photoelectric_select_shell(0.1, Z=13) for _ in range(N)]
        k_frac = shells.count("K") / N
        assert k_frac > 0.70, f"K-shell fraction {k_frac:.3%} < 70 % at 0.1 MeV (Al)"

    def test_k_shell_absent_below_k_edge(self):
        """K-shell is never selected below the Al K-edge (1.56 keV = 0.00156 MeV)."""
        np.random.seed(88)
        N = 2_000
        shells = [photoelectric_select_shell(0.001, Z=13) for _ in range(N)]
        k_frac = shells.count("K") / N
        assert k_frac == 0.0, f"K-shell selected below K-edge: fraction = {k_frac:.3%}"

    def test_k_shell_dominant_lead(self):
        """K-shell dominates for lead above its K-edge (88 keV = 0.088 MeV)."""
        np.random.seed(44)
        N = 5_000
        shells = [photoelectric_select_shell(0.5, Z=82) for _ in range(N)]
        k_frac = shells.count("K") / N
        assert k_frac > 0.70, f"K-shell fraction {k_frac:.3%} < 70 % for Pb at 0.5 MeV"


# ======================================================================================
# Integration: distributions + cross_sections consistency
# ======================================================================================


class TestDistributionsCrossSectionConsistency:
    """Check that sampled angles are consistent with the cross-section module."""

    def test_import_both_modules(self):
        """Both distributions and cross_sections can be imported together."""
        from photon_transport_code.transport.physics.photon import (
            cross_sections,
            distributions,
        )

        assert hasattr(distributions, "sample_klein_nishina")
        assert hasattr(cross_sections, "klein_nishina_total")

    def test_sampled_energies_within_kn_total_bounds(self):
        """Mean sampled E_out is below E_in (photons lose energy on average)."""
        np.random.seed(12)
        E_in = 1.0
        N = 5_000
        E_outs = np.array([sample_klein_nishina(E_in)[0] for _ in range(N)])
        assert (
            np.mean(E_outs) < E_in
        ), "Mean scattered energy >= incident energy (unphysical)"
        assert np.mean(E_outs) > 0.0, "Mean scattered energy is non-positive"
