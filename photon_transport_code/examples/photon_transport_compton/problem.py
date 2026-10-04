"""
Compton Scattering Spectrum — Example Problem
==============================================

Demonstrates Klein-Nishina Compton scattering using the photon transport module.

Physics background
------------------
Compton scattering is an inelastic collision between a photon and a loosely-bound
(quasi-free) electron.  The scattered photon energy is governed by the
relativistic kinematics formula::

    E' = E_0 / (1 + (E_0 / m_e c^2)(1 - cos θ))

where E_0 = 1.0 MeV is the incident energy, m_e c^2 = 0.511 MeV, and θ is the
polar scattering angle.  The Klein-Nishina differential cross-section
(dσ/dΩ, units cm²/electron/sr) sets the probability of each angle.

Key energy limits for a 1 MeV source:
  - Forward scatter (θ → 0°):  E' → E_0 = 1.000 MeV  (no energy loss)
  - Backscatter   (θ = 180°):  E' = E_0 / (1 + 2E_0/m_e c²) ≈ 0.204 MeV

The recoil electron carries the balance: T_e = E_0 - E'.
Energy conservation is exact: E' + T_e = E_0 to machine precision.

Simulation details
------------------
- Source:    100,000 monoenergetic 1 MeV photons, single scatter per history
- Material:  Water (H₂O, ρ = 1.0 g/cm³); H number density 6.692×10⁻² atoms/b-cm,
             O number density 3.346×10⁻² atoms/b-cm
- Sampler:   Klein-Nishina angular distribution via rejection sampling
- Spectrum:  50 equal-width bins from 0 to 1.1 MeV

Output plots
------------
Plot 1 — Scattered photon energy spectrum (counts vs. MeV)
    Histogram of E' over all 100,000 histories.  Shows the characteristic
    Compton continuum: roughly flat from 0.204 MeV (backscatter edge) up to
    ~1 MeV (forward scatter), with a sharp drop at the Compton edge (~0.796 MeV
    in the recoil-electron picture).  The forward peak is enhanced by the
    Klein-Nishina bias toward small angles at relativistic energies.

Plot 2 — Scattering angle distribution (counts vs. radians)
    Histogram of the polar angle θ sampled from the Klein-Nishina distribution.
    At 1 MeV the distribution is forward-peaked (majority of events have
    θ < π/2), unlike classical Thomson scattering which is symmetric.

Plot 3 — Recoil electron energy spectrum (counts vs. MeV)
    Mirror of Plot 1 shifted by E_0: T_e = E_0 - E'.  Shows the Compton plateau
    (flat from 0 up to the Compton edge at ~0.796 MeV) and confirms that the
    electron carries the remaining energy after each scatter.

Run from c:/Projects/MCDC/::

    python photon_transport_code/examples/photon_transport_compton/problem.py

Output: photon_transport_code/examples/photon_transport_compton/output.h5
"""

import math
import os
import sys

import h5py
import numpy as np

# --- Path setup (standalone execution) -----------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from photon_transport_code.mcdc_set.photon_material import photon_material
from photon_transport_code.transport.physics.photon.cross_sections import (
    klein_nishina_total,
)
from photon_transport_code.transport.physics.photon.distributions import (
    sample_klein_nishina,
)

# =============================================================================
# Problem setup
# =============================================================================

N_HISTORIES = 100_000
E_INCIDENT = 1.0  # MeV — mono-energetic source

# Water material: H2O at 1.0 g/cm^3
material = photon_material(
    elements=[1, 8],
    densities=[6.692e-2, 3.346e-2],
    name="water",
)

# Energy spectrum bins: 50 bins from 0 to 1.1 MeV
E_MIN = 0.0
E_MAX = 1.1
N_BINS = 50
energy_bins = np.linspace(E_MIN, E_MAX, N_BINS + 1)

# =============================================================================
# Monte Carlo simulation — Compton scattering
# =============================================================================

np.random.seed(42)

spectrum = np.zeros(N_BINS, dtype=np.float64)
scattered_energies = np.empty(N_HISTORIES, dtype=np.float64)
scattering_angles = np.empty(N_HISTORIES, dtype=np.float64)
electron_energies = np.empty(N_HISTORIES, dtype=np.float64)
energy_errors = np.empty(N_HISTORIES, dtype=np.float64)

for i in range(N_HISTORIES):
    E_out, theta, E_electron = sample_klein_nishina(E_INCIDENT)

    scattered_energies[i] = E_out
    scattering_angles[i] = theta
    electron_energies[i] = E_electron
    energy_errors[i] = abs(E_out + E_electron - E_INCIDENT)

    # Bin scattered photon energy
    bin_idx = int((E_out - E_MIN) / (E_MAX - E_MIN) * N_BINS)
    if 0 <= bin_idx < N_BINS:
        spectrum[bin_idx] += 1.0

# =============================================================================
# Physics verification
# =============================================================================

mean_scattered_energy = float(np.mean(scattered_energies))
max_energy_error = float(np.max(energy_errors))
backscatter_min = E_INCIDENT / (1.0 + 2.0 * E_INCIDENT / 0.51099895)

# Cross-section at incident energy (for reference)
sigma_kn = klein_nishina_total(E_INCIDENT)

print("=" * 60)
print("Compton Scattering Spectrum — Results")
print("=" * 60)
print(f"Incident energy:          {E_INCIDENT:.3f} MeV")
print(f"Histories:                {N_HISTORIES:,}")
print(f"Mean scattered energy:    {mean_scattered_energy:.4f} MeV")
print(f"Backscatter minimum:      {backscatter_min:.4f} MeV")
print(f"Max energy-cons. error:   {max_energy_error:.2e} MeV")
print(f"KN cross-section at 1MeV: {sigma_kn:.4e} cm^2/electron")
print(f"Forward fraction (0-90°): {np.mean(scattering_angles < math.pi/2)*100:.1f}%")

# Verify energy conservation
assert (
    max_energy_error < 1e-12
), f"Energy not conserved: max error = {max_energy_error:.2e} MeV"
# Verify backscatter minimum
assert (
    scattered_energies.min() >= backscatter_min * 0.95
), f"Scattered energy below backscatter minimum: {scattered_energies.min():.4f}"
print("\nAll physics checks passed.")

# =============================================================================
# Write HDF5 output
# =============================================================================

output_path = os.path.join(_HERE, "output.h5")
with h5py.File(output_path, "w") as f:
    ds = f.create_dataset("energy_bins", data=energy_bins)
    ds.attrs["units"] = "MeV"
    ds.attrs["description"] = "Bin edges for the scattered photon energy spectrum"
    ds.attrs["xlabel"] = "Scattered Photon Energy (MeV)"

    ds = f.create_dataset("spectrum", data=spectrum)
    ds.attrs["units"] = "counts"
    ds.attrs["description"] = "Scattered photon counts per energy bin"
    ds.attrs["xlabel"] = "Scattered Photon Energy (MeV)"
    ds.attrs["ylabel"] = "Counts"
    ds.attrs["title"] = "Compton Scattering Spectrum"

    ds = f.create_dataset("scattered_energies", data=scattered_energies)
    ds.attrs["units"] = "MeV"
    ds.attrs["description"] = "Scattered photon energy E' for each history"
    ds.attrs["xlabel"] = "Scattered Photon Energy (MeV)"
    ds.attrs["ylabel"] = "Counts"
    ds.attrs["title"] = "Scattered Photon Energy Distribution"

    ds = f.create_dataset("scattering_angles", data=scattering_angles)
    ds.attrs["units"] = "radians"
    ds.attrs["description"] = "Polar scattering angle theta for each history"
    ds.attrs["xlabel"] = "Scattering Angle \u03b8 (radians)"
    ds.attrs["ylabel"] = "Counts"
    ds.attrs["title"] = "Klein-Nishina Angular Distribution"

    ds = f.create_dataset("electron_energies", data=electron_energies)
    ds.attrs["units"] = "MeV"
    ds.attrs["description"] = "Recoil electron kinetic energy T_e = E_0 - E' for each history"
    ds.attrs["xlabel"] = "Recoil Electron Kinetic Energy (MeV)"
    ds.attrs["ylabel"] = "Counts"
    ds.attrs["title"] = "Compton Recoil Electron Spectrum"

    f.attrs["E_incident_MeV"] = E_INCIDENT
    f.attrs["N_histories"] = N_HISTORIES
    f.attrs["mean_scattered_energy_MeV"] = mean_scattered_energy
    f.attrs["backscatter_minimum_MeV"] = backscatter_min
    f.attrs["energy_conservation_max_error"] = max_energy_error
    f.attrs["klein_nishina_xs_cm2"] = sigma_kn
    f.attrs["material"] = "water (H2O, 1.0 g/cm^3)"

print(f"\nOutput written to: {output_path}")
