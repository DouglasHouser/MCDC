"""
Photon Slab — Output Plots
===========================

Reads photon_slab.h5 produced by problem.py and generates one labeled plot:

  flux_profile.png  — Photon flux vs. slab depth (mean ± 1σ)

Run from c:/Projects/MCDC/::

    python photon_transport_code/examples/photon_slab/plot.py
"""

import os

import h5py
import matplotlib.pyplot as plt
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(_HERE, "photon_slab.h5")

with h5py.File(output_path, "r") as f:
    x_edges = f["tallies/tracklength_tally_0/grid/x"][:]
    flux_mean = f["tallies/tracklength_tally_0/flux/mean"][:]
    flux_sdev = f["tallies/tracklength_tally_0/flux/sdev"][:]
    N_particle = int(f["settings/N_particle"][()])

x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])

# --- Plot: Photon flux profile ------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x_centers, flux_mean, color="steelblue", label="MC flux (mean)")
ax.fill_between(
    x_centers,
    flux_mean - flux_sdev,
    flux_mean + flux_sdev,
    alpha=0.35,
    color="steelblue",
    label=r"$\pm 1\sigma$",
)
ax.set_xlabel("Depth in Slab (cm)")
ax.set_ylabel("Photon Flux (arbitrary units)")
ax.set_title(
    f"Photon Flux Profile — 1 MeV Beam in 25 cm Al Slab  (N = {N_particle:,})"
)
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(_HERE, "flux_profile.png"), dpi=150)
print("Saved: flux_profile.png")
plt.show()
