"""
Regression tests: Photoelectric-absorption-dominated scenarios.

Validates that:
  1. Photoelectric absorption dominates at low energies for high-Z materials.
  2. The cross-section lookup returns correct relative magnitudes.
  3. The Phase 1 model deposits all photon energy locally (no secondaries).
  4. Shell selection statistics are physically reasonable.

Reference
---------
NIST XCOM: photoelectric cross-section for Pb (Z=82) at 10 keV ≈ 8.05e-21 cm^2/atom,
compared to Compton ≈ 5.24e-23 cm^2/atom; PE/total ≈ 99 %.
"""

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon import native
from photon_transport_code.transport.physics.photon.distributions import (
    photoelectric_absorption,
    photoelectric_select_shell,
    sample_photoelectric_shell,
)


# ======================================================================================
# Photoelectric dominance at low energies
# ======================================================================================


class TestPhotoelectricDominance:
    """Photoelectric cross-section dominates for high-Z at low energies."""

    @pytest.mark.parametrize("E_MeV", [0.01, 0.02])
    def test_pe_dominates_lead(self, E_MeV, pb_element):
        """At 10 – 20 keV, photoelectric fraction > 50 % for lead."""
        photon_element, flat_data = pb_element
        Z = 82

        sigma_C = native.compton_xs(Z, E_MeV, photon_element, flat_data)
        sigma_PE = native.photoelectric_xs(Z, E_MeV, photon_element, flat_data)
        sigma_PP = native.pair_production_xs(Z, E_MeV, photon_element, flat_data)
        sigma_T = sigma_C + sigma_PE + sigma_PP

        pe_fraction = sigma_PE / sigma_T
        assert pe_fraction > 0.5, (
            f"Photoelectric fraction {pe_fraction:.3%} < 50 % "
            f"at E={E_MeV} MeV for Pb"
        )

    def test_pe_dominates_lead_at_10kev(self, pb_element):
        """At 10 keV, photoelectric fraction > 95 % for lead."""
        photon_element, flat_data = pb_element
        Z = 82
        E = 0.010  # 10 keV

        sigma_C = native.compton_xs(Z, E, photon_element, flat_data)
        sigma_PE = native.photoelectric_xs(Z, E, photon_element, flat_data)
        sigma_PP = native.pair_production_xs(Z, E, photon_element, flat_data)
        sigma_T = sigma_C + sigma_PE + sigma_PP

        pe_fraction = sigma_PE / sigma_T
        assert (
            pe_fraction > 0.95
        ), f"Photoelectric fraction {pe_fraction:.3%} < 95 % at 10 keV for Pb"

    @pytest.mark.parametrize("E_MeV", [0.001, 0.005, 0.010])
    def test_pe_dominates_aluminum(self, E_MeV, al_element):
        """At 1 – 10 keV, photoelectric fraction > 50 % for aluminum."""
        photon_element, flat_data = al_element
        Z = 13

        sigma_C = native.compton_xs(Z, E_MeV, photon_element, flat_data)
        sigma_PE = native.photoelectric_xs(Z, E_MeV, photon_element, flat_data)
        sigma_PP = native.pair_production_xs(Z, E_MeV, photon_element, flat_data)
        sigma_T = sigma_C + sigma_PE + sigma_PP

        pe_fraction = sigma_PE / sigma_T
        assert pe_fraction > 0.5, (
            f"Photoelectric fraction {pe_fraction:.3%} < 50 % "
            f"at E={E_MeV} MeV for Al"
        )

    def test_pe_decreases_with_energy(self, pb_element):
        """Photoelectric cross-section decreases monotonically (away from edges)."""
        photon_element, flat_data = pb_element
        Z = 82

        # Sample at points that avoid the K-edge jump (0.088 MeV)
        energies = [0.1, 0.15, 0.2, 0.3, 0.5]
        xs_values = [
            native.photoelectric_xs(Z, E, photon_element, flat_data) for E in energies
        ]

        # Should decrease monotonically above the K-edge
        for i in range(len(xs_values) - 1):
            assert xs_values[i] >= xs_values[i + 1], (
                f"PE XS not decreasing: {xs_values[i]:.3e} at "
                f"E={energies[i]} MeV, {xs_values[i+1]:.3e} at "
                f"E={energies[i+1]} MeV"
            )

    def test_pe_positive_across_energy_range(self, al_element):
        """Photoelectric cross-section is positive across the full range."""
        photon_element, flat_data = al_element
        Z = 13

        for E in np.logspace(-3, 0, 20):  # 0.001 to 1 MeV
            sigma_PE = native.photoelectric_xs(Z, float(E), photon_element, flat_data)
            assert (
                sigma_PE > 0.0
            ), f"Photoelectric XS non-positive ({sigma_PE:.3e}) at E={E:.4f} MeV"


# ======================================================================================
# Energy deposition (Phase 1 model)
# ======================================================================================


class TestPhotoelectricEnergyDeposition:
    """Phase 1 model: entire photon energy is deposited locally."""

    def test_energy_deposition_exact(self):
        """photoelectric_absorption returns E_photon exactly."""
        for E in [0.001, 0.005, 0.010, 0.050, 0.100, 0.500, 1.0]:
            E_dep = photoelectric_absorption(E)
            assert E_dep == float(
                E
            ), f"Energy deposition mismatch: E={E}, E_dep={E_dep}"

    def test_energy_deposition_no_secondaries(self):
        """Phase 1: function returns scalar (no secondary particles)."""
        result = photoelectric_absorption(0.05)
        assert isinstance(
            result, (int, float)
        ), f"Expected scalar, got {type(result).__name__}"

    def test_energy_deposition_range(self):
        """Energy deposition is correct across full energy range."""
        for E in np.linspace(1e-3, 100.0, 30):
            E_dep = photoelectric_absorption(float(E))
            err = abs(E_dep - float(E))
            assert err < 1e-10, f"Energy conservation error {err:.3e} at E={E:.4f} MeV"


# ======================================================================================
# Shell selection statistics
# ======================================================================================


class TestShellSelection:
    """K-shell dominates above K-edge; K-shell absent below K-edge."""

    N_SAMPLES = 5_000

    def test_k_shell_dominates_al_above_k_edge(self):
        """K-shell fraction > 70 % for Al at 0.1 MeV (well above K-edge ~1.56 keV)."""
        np.random.seed(42)
        shells = [photoelectric_select_shell(0.1, Z=13) for _ in range(self.N_SAMPLES)]
        k_frac = shells.count("K") / self.N_SAMPLES
        assert k_frac > 0.70, f"K-shell fraction {k_frac:.3%} < 70 % for Al at 0.1 MeV"

    def test_k_shell_absent_al_below_k_edge(self):
        """K-shell never selected for Al at 1 keV (below K-edge ~1.56 keV)."""
        np.random.seed(77)
        shells = [
            photoelectric_select_shell(0.001, Z=13) for _ in range(self.N_SAMPLES)
        ]
        k_frac = shells.count("K") / self.N_SAMPLES
        assert k_frac == 0.0, f"K-shell selected {k_frac:.3%} below K-edge for Al"

    def test_shell_names_valid(self):
        """All returned shell names are 'K', 'L', or 'M'."""
        np.random.seed(11)
        for E in [0.001, 0.01, 0.1, 1.0]:
            for Z in [1, 8, 13, 82]:
                shell = photoelectric_select_shell(E, Z=Z)
                assert shell in (
                    "K",
                    "L",
                    "M",
                ), f"Invalid shell name '{shell}' for Z={Z}, E={E} MeV"

    def test_k_shell_dominates_pb_above_k_edge(self):
        """K-shell fraction > 70 % for Pb at 0.5 MeV (above K-edge ~88 keV)."""
        np.random.seed(33)
        shells = [photoelectric_select_shell(0.5, Z=82) for _ in range(self.N_SAMPLES)]
        k_frac = shells.count("K") / self.N_SAMPLES
        assert k_frac > 0.70, f"K-shell fraction {k_frac:.3%} < 70 % for Pb at 0.5 MeV"

    def test_sample_photoelectric_shell_energy_conservation(self):
        """Electron energy equals photon energy (Phase 1: no binding correction)."""
        np.random.seed(99)
        for E in [0.01, 0.05, 0.1, 0.5]:
            for _ in range(200):
                E_e, _theta, _shell = sample_photoelectric_shell(E, Z=13)
                assert (
                    abs(E_e - E) < 1e-10
                ), f"E={E}: electron energy {E_e:.10f} != {E:.10f}"
