"""
Compton Scattering — Output Plots
==================================

Reads output.h5 produced by problem.py and generates three labeled plots:

  spectrum.png          — Scattered photon energy spectrum (Compton continuum)
  angle_distribution.png — Klein-Nishina angular distribution
  electron_spectrum.png — Recoil electron energy spectrum (Compton plateau)

Axis labels and titles are read directly from the HDF5 dataset attributes.

Run from c:/Projects/MCDC/::

    python photon_transport_code/examples/photon_transport_compton/plot.py
"""

import math
import os

import h5py
import matplotlib.pyplot as plt
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(_HERE, "output.h5")

with h5py.File(output_path, "r") as f:
    energy_bins = f["energy_bins"][:]
    spectrum = f["spectrum"][:]
    scattered_energies = f["scattered_energies"][:]
    scattering_angles = f["scattering_angles"][:]
    electron_energies = f["electron_energies"][:]

    E_incident = float(f.attrs["E_incident_MeV"])
    N_histories = int(f.attrs["N_histories"])
    backscatter_min = float(f.attrs["backscatter_minimum_MeV"])

    spec_xlabel = f["spectrum"].attrs["xlabel"]
    spec_ylabel = f["spectrum"].attrs["ylabel"]
    spec_title = f["spectrum"].attrs["title"]

    ang_xlabel = f["scattering_angles"].attrs["xlabel"]
    ang_ylabel = f["scattering_angles"].attrs["ylabel"]
    ang_title = f["scattering_angles"].attrs["title"]

    elec_xlabel = f["electron_energies"].attrs["xlabel"]
    elec_ylabel = f["electron_energies"].attrs["ylabel"]
    elec_title = f["electron_energies"].attrs["title"]

bin_centers = 0.5 * (energy_bins[:-1] + energy_bins[1:])
compton_edge = E_incident - backscatter_min

# --- Plot 1: Scattered photon energy spectrum --------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
ax.step(bin_centers, spectrum, where="mid")
ax.axvline(backscatter_min, color="red", linestyle="--",
           label=f"Backscatter min = {backscatter_min:.3f} MeV")
ax.set_xlabel(spec_xlabel)
ax.set_ylabel(spec_ylabel)
ax.set_title(f"{spec_title}  (E\u2080 = {E_incident} MeV, N = {N_histories:,})")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "spectrum.png"), dpi=150)
print("Saved: spectrum.png")
plt.show()

# --- Plot 2: Scattering angle distribution -----------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(scattering_angles, bins=60, edgecolor="none")
ax.axvline(math.pi / 2, color="red", linestyle="--", label="\u03b8 = \u03c0/2")
ax.set_xlabel(ang_xlabel)
ax.set_ylabel(ang_ylabel)
ax.set_title(f"{ang_title}  (E\u2080 = {E_incident} MeV)")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "angle_distribution.png"), dpi=150)
print("Saved: angle_distribution.png")
plt.show()

# --- Plot 3: Recoil electron energy spectrum ---------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(electron_energies, bins=50, edgecolor="none")
ax.axvline(compton_edge, color="red", linestyle="--",
           label=f"Compton edge = {compton_edge:.3f} MeV")
ax.set_xlabel(elec_xlabel)
ax.set_ylabel(elec_ylabel)
ax.set_title(f"{elec_title}  (E\u2080 = {E_incident} MeV)")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "electron_spectrum.png"), dpi=150)
print("Saved: electron_spectrum.png")
plt.show()
