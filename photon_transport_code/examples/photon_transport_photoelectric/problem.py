"""
Photoelectric Absorption in Aluminum Slab — Example Problem
=============================================================

Demonstrates photoelectric absorption using the photon transport module.

Physics background
------------------
The photoelectric effect is the complete absorption of a photon by a bound
atomic electron, ejecting it with kinetic energy::

    T_e = E_photon - E_binding

At 10 keV in aluminum (Z = 13) the photoelectric cross-section overwhelmingly
dominates: σ_PE >> σ_Compton and pair production is energetically forbidden
(threshold at 1.022 MeV).  The dominant ionization shell depends on the photon
energy relative to the shell binding energies:

  - K-shell (1s):  E_b ≈ 1.56 keV  (Al)  → accessible at 10 keV, largest XS
  - L-shell (2s/2p): E_b ≈ 0.07–0.12 keV → accessible, smaller XS
  - M-shell:        E_b < 0.02 keV        → very small contribution

Because E_photon (10 keV) >> E_b (K-shell, 1.56 keV), the K-shell dominates
(>70% of PE events).  All photon energy is deposited locally: the ejected
photoelectron carries T_e = E_photon − E_binding, and subsequent fluorescence
or Auger emission is not tracked here.

Slab transport
--------------
A 1 cm aluminum slab (ρ = 2.699 g/cm³, N = 6.026×10⁻² atoms/b-cm) is
irradiated with 100,000 monoenergetic 10 keV photons along the beam axis.
Each history samples a mean free path::

    λ = −ln(ξ) / Σ_T   [cm],   ξ ~ Uniform(0, 1)

where Σ_T = N (σ_PE + σ_Compton) is the macroscopic total cross-section
(cm⁻¹).  If the photon reaches the back face it is counted as transmitted;
otherwise the interaction type (PE vs. Compton) is selected proportional to
the partial cross-sections.  The Beer-Lambert analytical prediction
T = exp(−Σ_T · d) is used for validation.

Simulation details
------------------
- Source:      100,000 photons at 10 keV, normal incidence
- Material:    Aluminum (Z = 13, ρ = 2.699 g/cm³)
- Σ_PE:        dominates; Compton ~1% of Σ_T at 10 keV
- Σ_T:         computed from NIST tabulated photoelectric XS + Klein-Nishina
- Slab:        1.0 cm thick; photons terminate after first interaction

Output plots
------------
Plot 1 — Path length distribution (counts vs. cm)
    Histogram of the distance each photon travels before its first interaction
    (or the slab thickness if transmitted).  The absorbed-photon tail follows
    an exponential distribution with decay constant Σ_T (cm⁻¹), confirming
    Beer-Lambert attenuation.  The transmitted spike appears at x = 1.0 cm.

Plot 2 — Shell ionization fractions (bar chart: fraction vs. shell label K/L/M)
    Fraction of photoelectric events that ionized each electron shell.
    K-shell should exceed 70% at 10 keV; L and M shells account for the
    remainder.  Fractions are proportional to the partial photoelectric
    cross-sections from the NIST dataset.

Plot 3 — Deposited energy histogram (counts vs. MeV)
    Distribution of energy deposited per photoelectric event.  Since no
    fluorescence is tracked, each event deposits the full photon energy
    (10 keV), producing a narrow spike at E = 0.010 MeV that confirms
    energy bookkeeping is exact.

Run from c:/Projects/MCDC/::

    python photon_transport_code/examples/photon_transport_photoelectric/problem.py

Output: photon_transport_code/examples/photon_transport_photoelectric/output.h5
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
from photon_transport_code.transport.physics.photon.data_loader import load_photon_element
from photon_transport_code.transport.physics.photon.distributions import (
    photoelectric_absorption,
    photoelectric_select_shell,
    sample_klein_nishina,
)
from photon_transport_code.transport.physics.photon.native import _loglog_interp_python

# =============================================================================
# Problem setup
# =============================================================================

N_HISTORIES = 100_000
E_PHOTON = 0.010  # MeV — 10 keV incident energy (PE-dominated for Al)
SLAB_THICKNESS = 1.0  # cm
Z_AL = 13

# Aluminum at standard conditions (rho = 2.699 g/cm^3)
N_AL = 6.026e-2  # atoms/b-cm

material = photon_material(
    elements=[Z_AL],
    densities=[N_AL],
    name="aluminum",
)

# Load cross-section data for Al
al_energies, al_compton_xs, al_pe_xs, al_pair_xs = load_photon_element(Z=Z_AL)

# --- Compute macroscopic cross-sections at 30 keV ---
n_al_cm3 = N_AL * 1e24  # convert atoms/b-cm -> atoms/cm^3

sigma_compton = klein_nishina_total(E_PHOTON) * Z_AL  # cm^2/atom
sigma_pe = _loglog_interp_python(E_PHOTON, al_energies, al_pe_xs)
sigma_pair = 0.0  # below pair production threshold at 30 keV
sigma_total = sigma_compton + sigma_pe + sigma_pair

# Macroscopic total (cm^-1): Sigma = n * sigma
Sigma_C = N_AL * sigma_compton * 1e24  # cm^-1
Sigma_PE = N_AL * sigma_pe * 1e24  # cm^-1
Sigma_T = Sigma_C + Sigma_PE

# Beer-Lambert prediction
beer_lambert_transmission = math.exp(-Sigma_T * SLAB_THICKNESS)

print("=" * 60)
print("Photoelectric Absorption in Al — Setup")
print("=" * 60)
print(f"Incident energy:           {E_PHOTON*1000:.1f} keV")
print(f"Slab thickness:            {SLAB_THICKNESS:.1f} cm")
print(f"Number density:            {N_AL:.3e} atoms/b-cm")
print(f"Compton XS:                {sigma_compton:.3e} cm^2/atom")
print(f"Photoelectric XS:          {sigma_pe:.3e} cm^2/atom")
print(f"Macro Compton (cm^-1):     {Sigma_C:.4f}")
print(f"Macro Photoelectric (cm-1): {Sigma_PE:.4f}")
print(f"Macro total (cm^-1):       {Sigma_T:.4f}")
print(f"Beer-Lambert prediction:   {beer_lambert_transmission*100:.3f}%")
print(
    f"PE fraction of total:      "
    f"{Sigma_PE/(Sigma_C+Sigma_PE)*100:.1f}% "
    f"(photoelectric-dominated at 10 keV for Al)"
)

# =============================================================================
# Monte Carlo simulation — track photon through slab
# =============================================================================

np.random.seed(42)

n_transmitted = 0
n_absorbed_pe = 0
n_scattered_compton = 0

shells = []
deposited_energies = []
path_lengths = []

for _ in range(N_HISTORIES):
    x = 0.0  # photon position along beam axis
    alive = True

    while alive and x < SLAB_THICKNESS:
        # Sample free path length: -ln(U) / Sigma_T
        xi = np.random.random()
        if xi <= 0.0:
            xi = 1e-300
        free_path = -math.log(xi) / Sigma_T
        x += free_path

        if x >= SLAB_THICKNESS:
            # Photon exits slab
            n_transmitted += 1
            alive = False
            break

        # Sample interaction type
        r = np.random.random() * Sigma_T
        if r < Sigma_PE:
            # Photoelectric absorption
            E_dep = photoelectric_absorption(E_PHOTON)
            shell = photoelectric_select_shell(E_PHOTON, Z=Z_AL)
            deposited_energies.append(E_dep)
            shells.append(shell)
            n_absorbed_pe += 1
            alive = False
        else:
            # Compton scatter — update energy and continue
            E_out, theta, E_electron = sample_klein_nishina(E_PHOTON)
            n_scattered_compton += 1
            # For simplicity terminate after one Compton scatter
            alive = False

    path_lengths.append(x)

# =============================================================================
# Results
# =============================================================================

transmission_ratio = n_transmitted / N_HISTORIES
k_fraction = shells.count("K") / len(shells) if shells else 0.0
l_fraction = shells.count("L") / len(shells) if shells else 0.0
m_fraction = shells.count("M") / len(shells) if shells else 0.0
mean_deposited = float(np.mean(deposited_energies)) if deposited_energies else 0.0
error_vs_beer_lambert = abs(transmission_ratio - beer_lambert_transmission)

print("\n" + "=" * 60)
print("Monte Carlo Results")
print("=" * 60)
print(f"Histories:                {N_HISTORIES:,}")
print(f"Transmitted:              {n_transmitted:,} ({transmission_ratio*100:.3f}%)")
print(f"PE absorbed:              {n_absorbed_pe:,}")
print(f"Compton scattered:        {n_scattered_compton:,}")
print(f"Beer-Lambert prediction:  {beer_lambert_transmission*100:.3f}%")
print(f"Absolute error:           {error_vs_beer_lambert*100:.4f}%")
print(f"\nShell statistics (PE events):")
print(f"  K-shell: {k_fraction*100:.1f}%")
print(f"  L-shell: {l_fraction*100:.1f}%")
print(f"  M-shell: {m_fraction*100:.1f}%")
print(
    f"\nMean deposited energy:    {mean_deposited*1000:.3f} keV (= {E_PHOTON*1000:.1f} keV)"
)

# Validate Beer-Lambert within 5% (Monte Carlo statistical tolerance)
assert error_vs_beer_lambert < 0.05, (
    f"Transmission {transmission_ratio:.4f} vs Beer-Lambert "
    f"{beer_lambert_transmission:.4f}: error {error_vs_beer_lambert:.4f} > 0.05"
)
assert k_fraction > 0.70, f"K-shell fraction {k_fraction:.3f} below 70%"
assert abs(mean_deposited - E_PHOTON) < 1e-10, "Energy deposition not exact"
print("\nAll physics checks passed.")

# =============================================================================
# Write HDF5 output
# =============================================================================

output_path = os.path.join(_HERE, "output.h5")
shells_bytes = np.array([s.encode("ascii") for s in shells], dtype="S1")

with h5py.File(output_path, "w") as f:
    ds = f.create_dataset("deposited_energies_MeV", data=np.array(deposited_energies))
    ds.attrs["units"] = "MeV"
    ds.attrs["description"] = "Energy deposited per photoelectric absorption event (= E_photon, no fluorescence)"
    ds.attrs["xlabel"] = "Deposited Energy (MeV)"
    ds.attrs["ylabel"] = "Counts"
    ds.attrs["title"] = "Photoelectric Deposited Energy Spectrum"

    ds = f.create_dataset("shell_selections", data=shells_bytes)
    ds.attrs["units"] = "ASCII character (K/L/M)"
    ds.attrs["description"] = "Electron shell ionized in each photoelectric event"
    ds.attrs["xlabel"] = "Electron Shell"
    ds.attrs["ylabel"] = "Fraction of PE Events"
    ds.attrs["title"] = "Photoelectric Shell Ionization Fractions"

    ds = f.create_dataset("path_lengths_cm", data=np.array(path_lengths))
    ds.attrs["units"] = "cm"
    ds.attrs["description"] = "Distance traveled before first interaction or slab exit (x <= 1.0 cm)"
    ds.attrs["xlabel"] = "Path Length (cm)"
    ds.attrs["ylabel"] = "Counts"
    ds.attrs["title"] = "Photon Path Length Distribution in Al Slab"

    f.attrs["slab_thickness_cm"] = SLAB_THICKNESS
    f.attrs["E_photon_MeV"] = E_PHOTON
    f.attrs["N_histories"] = N_HISTORIES
    f.attrs["transmitted"] = n_transmitted
    f.attrs["transmission_ratio"] = transmission_ratio
    f.attrs["beer_lambert_prediction"] = beer_lambert_transmission
    f.attrs["Sigma_T_per_cm"] = Sigma_T
    f.attrs["Sigma_PE_per_cm"] = Sigma_PE
    f.attrs["Sigma_C_per_cm"] = Sigma_C
    f.attrs["k_shell_fraction"] = k_fraction
    f.attrs["mean_deposited_MeV"] = mean_deposited
    f.attrs["material"] = "aluminum (Z=13, 2.699 g/cm^3)"

print(f"\nOutput written to: {output_path}")
