"""
Photoelectric Absorption — Output Plots
=========================================

Reads output.h5 produced by problem.py and generates three labeled plots:

  path_lengths.png      — Photon path length distribution (exponential + Beer-Lambert)
  shell_fractions.png   — Shell ionization fractions (K/L/M bar chart)
  deposited_energy.png  — Deposited energy spectrum (delta spike at E_photon)

Axis labels and titles are read directly from the HDF5 dataset attributes.

Run from c:/Projects/MCDC/::

    python photon_transport_code/examples/photon_transport_photoelectric/plot.py
"""

import os

import h5py
import matplotlib.pyplot as plt
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(_HERE, "output.h5")

with h5py.File(output_path, "r") as f:
    deposited = f["deposited_energies_MeV"][:]
    shells_raw = f["shell_selections"][:]
    path_lengths = f["path_lengths_cm"][:]

    slab_thickness = float(f.attrs["slab_thickness_cm"])
    E_photon = float(f.attrs["E_photon_MeV"])
    N_histories = int(f.attrs["N_histories"])
    beer_lambert = float(f.attrs["beer_lambert_prediction"])
    Sigma_T = float(f.attrs["Sigma_T_per_cm"])
    k_frac = float(f.attrs["k_shell_fraction"])

    dep_xlabel = f["deposited_energies_MeV"].attrs["xlabel"]
    dep_ylabel = f["deposited_energies_MeV"].attrs["ylabel"]
    dep_title = f["deposited_energies_MeV"].attrs["title"]

    sh_xlabel = f["shell_selections"].attrs["xlabel"]
    sh_ylabel = f["shell_selections"].attrs["ylabel"]
    sh_title = f["shell_selections"].attrs["title"]

    pl_xlabel = f["path_lengths_cm"].attrs["xlabel"]
    pl_ylabel = f["path_lengths_cm"].attrs["ylabel"]
    pl_title = f["path_lengths_cm"].attrs["title"]

# Decode shell labels (stored as 1-byte ASCII)
shells = [s.decode("ascii") for s in shells_raw]

# --- Plot 1: Path length distribution ----------------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(path_lengths, bins=60, edgecolor="none", density=True, label="MC")
# Overlay Beer-Lambert exponential (truncated at slab thickness)
x_plot = np.linspace(0, slab_thickness * 0.999, 300)
ax.plot(x_plot, Sigma_T * np.exp(-Sigma_T * x_plot), "r--",
        label=f"Beer-Lambert: \u03a3_T = {Sigma_T:.3f} cm\u207b\u00b9")
ax.set_xlabel(pl_xlabel)
ax.set_ylabel("Probability Density (cm\u207b\u00b9)")
ax.set_title(pl_title)
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "path_lengths.png"), dpi=150)
print("Saved: path_lengths.png")
plt.show()

# --- Plot 2: Shell ionization fractions (bar chart) --------------------------
shell_labels = ["K", "L", "M"]
counts = [shells.count(s) for s in shell_labels]
total = sum(counts)
fractions = [c / total if total > 0 else 0.0 for c in counts]

fig, ax = plt.subplots(figsize=(5, 4))
bars = ax.bar(shell_labels, fractions, color=["steelblue", "darkorange", "green"])
for bar, frac in zip(bars, fractions):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{frac*100:.1f}%", ha="center", va="bottom", fontsize=10)
ax.set_xlabel(sh_xlabel)
ax.set_ylabel(sh_ylabel)
ax.set_title(f"{sh_title}  (E\u03b3 = {E_photon*1000:.0f} keV, Al Z=13)")
ax.set_ylim(0, 1.1)
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "shell_fractions.png"), dpi=150)
print("Saved: shell_fractions.png")
plt.show()

# --- Plot 3: Deposited energy spectrum ---------------------------------------
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(deposited * 1000, bins=40, edgecolor="none")  # convert to keV for readability
ax.set_xlabel(dep_xlabel.replace("(MeV)", "(keV)"))
ax.set_ylabel(dep_ylabel)
ax.set_title(f"{dep_title}  (E\u03b3 = {E_photon*1000:.0f} keV)")
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "deposited_energy.png"), dpi=150)
print("Saved: deposited_energy.png")
plt.show()
