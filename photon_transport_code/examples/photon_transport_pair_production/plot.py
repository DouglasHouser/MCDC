"""
Pair Production — Output Plots
================================

Reads output.h5 produced by problem.py and generates three labeled plots:

  pair_xs.png           — Cross-section vs. photon energy (log-log, threshold visible)
  energy_sharing.png    — Electron / positron energy sharing at 10 MeV
  angle_distributions.png — Forward-peaked angular distributions of e- and e+

Axis labels and titles are read directly from the HDF5 dataset attributes.

Run from c:/Projects/MCDC/::

    python photon_transport_code/examples/photon_transport_pair_production/plot.py
"""

import os

import h5py
import matplotlib.pyplot as plt
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(_HERE, "output.h5")

with h5py.File(output_path, "r") as f:
    energies = f["energies_MeV"][:]
    pair_xs = f["pair_xs_cm2_per_atom"][:]
    E_electron = f["kinematics/E_electron_MeV"][:]
    E_positron = f["kinematics/E_positron_MeV"][:]
    theta_electron = f["kinematics/theta_electron_rad"][:]
    theta_positron = f["kinematics/theta_positron_rad"][:]

    threshold = float(f.attrs["threshold_MeV"])
    E_kin = float(f.attrs["kinematic_energy_MeV"])
    N_kin = int(f.attrs["N_kinematic_samples"])

    xs_xlabel = f["pair_xs_cm2_per_atom"].attrs["xlabel"]
    xs_ylabel = f["pair_xs_cm2_per_atom"].attrs["ylabel"]
    xs_title = f["pair_xs_cm2_per_atom"].attrs["title"]

    ee_xlabel = f["kinematics/E_electron_MeV"].attrs["xlabel"]
    ee_ylabel = f["kinematics/E_electron_MeV"].attrs["ylabel"]

    ang_xlabel = f["kinematics/theta_electron_rad"].attrs["xlabel"]
    ang_ylabel = f["kinematics/theta_electron_rad"].attrs["ylabel"]

# --- Plot 1: Pair production cross-section vs. energy (log-log) -------------
fig, ax = plt.subplots(figsize=(7, 4))
above = pair_xs > 0
ax.loglog(energies[above], pair_xs[above], "o-", label="\u03c3_pair (Pb, Z=82)")
ax.axvline(threshold, color="red", linestyle="--",
           label=f"Threshold = {threshold:.3f} MeV")
ax.set_xlabel(xs_xlabel)
ax.set_ylabel(xs_ylabel)
ax.set_title(xs_title)
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "pair_xs.png"), dpi=150)
print("Saved: pair_xs.png")
plt.show()

# --- Plot 2: Electron / positron energy sharing ------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
bins = np.linspace(0, E_kin, 60)
ax.hist(E_electron, bins=bins, alpha=0.6, label="Electron")
ax.hist(E_positron, bins=bins, alpha=0.6, label="Positron")
ax.set_xlabel(ee_xlabel.replace("Electron", "Particle"))
ax.set_ylabel(ee_ylabel)
ax.set_title(f"Electron / Positron Energy Sharing  (E\u2080 = {E_kin} MeV, N = {N_kin:,})")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "energy_sharing.png"), dpi=150)
print("Saved: energy_sharing.png")
plt.show()

# --- Plot 3: Angular distributions of electron and positron -----------------
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(theta_electron, bins=60, alpha=0.6, label="Electron")
ax.hist(theta_positron, bins=60, alpha=0.6, label="Positron")
ax.set_xlabel(ang_xlabel)
ax.set_ylabel(ang_ylabel)
ax.set_title(f"Pair Production Angular Distributions  (E\u2080 = {E_kin} MeV)")
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "angle_distributions.png"), dpi=150)
print("Saved: angle_distributions.png")
plt.show()
