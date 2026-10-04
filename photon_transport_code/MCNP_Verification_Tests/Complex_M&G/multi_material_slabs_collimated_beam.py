"""
Multi-material planar slab stack — COLLIMATED BEAM variant.

Same lead -> water -> concrete -> air slab geometry and materials as
multi_material_slabs.py, but the source is now a mono-directional collimated
beam (mcdc.Source(direction=[0,0,1], ...), no isotropic/polar_cosine/azimuthal
spread) straight down the slab stack's axis, instead of an isotropic point
source at the face.

Why this is a better match for planar geometry: an isotropic point source
sitting at the face of an infinite slab is a slightly awkward setup (half the
source strength immediately leaves backward through the backing gap, and the
forward half arrives at each depth over a spread of angles). A collimated
beam is the cleaner test of pure 1D attenuation through each material: with
no angular spread, the uncollided-beam attenuation at each depth should
follow a simple exponential (I = I0 * exp(-sigma_t * x)) that can be checked
by hand before trusting the full (uncollided + scattered) Monte Carlo result.
It also removes the backward-emission behavior entirely, so the backing gap
should now show ~zero flux and just serves as an unambiguous birth cell for
the source (see the source-offset note below).

Everything else (materials, geometry, per-slab flux tallies) is unchanged
from multi_material_slabs.py.
"""

import math
import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Path setup — make the local mcdc package importable
# ---------------------------------------------------------------------------
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
except NameError:
    _HERE = os.getcwd()
    _ROOT = _HERE

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import mcdc

# =============================================================================
# Material composition -> number density helper
#   n_i = rho[g/cm^3] * w_i * (N_A * 1e-24) / A_i,   N_A * 1e-24 = 0.602214
# =============================================================================
_NA_BARN = 0.602214

_A = {
    1: 1.008,    # H
    7: 14.007,   # N
    8: 15.999,   # O
    11: 22.990,  # Na
    12: 24.305,  # Mg
    13: 26.982,  # Al
    14: 28.085,  # Si
    18: 39.948,  # Ar
    20: 40.078,  # Ca
    26: 55.845,  # Fe
    82: 207.200, # Pb
}


def _number_densities(rho, weight_fractions):
    """Convert {Z: weight_fraction} at bulk density rho (g/cm^3) to number
    densities in atoms/barn-cm, suitable for mcdc.PhotonMaterial(...)."""
    elements = list(weight_fractions.keys())
    densities = [rho * weight_fractions[z] * _NA_BARN / _A[z] for z in elements]
    return elements, densities


# =============================================================================
# Materials
# =============================================================================
_pb_elems, _pb_dens = _number_densities(11.34, {82: 1.0})
lead = mcdc.PhotonMaterial(elements=_pb_elems, densities=_pb_dens, name="lead")

_water_elems, _water_dens = _number_densities(1.0, {1: 0.111898, 8: 0.888102})
water = mcdc.PhotonMaterial(elements=_water_elems, densities=_water_dens, name="water")

_concrete_elems, _concrete_dens = _number_densities(
    2.3, {8: 0.529107, 11: 0.016, 12: 0.002, 13: 0.033872, 14: 0.337021,
          20: 0.044, 26: 0.014, 1: 0.010}
)
concrete = mcdc.PhotonMaterial(
    elements=_concrete_elems, densities=_concrete_dens, name="concrete"
)

_air_elems, _air_dens = _number_densities(0.00129, {7: 0.7818, 8: 0.2097, 18: 0.0085})
air = mcdc.PhotonMaterial(elements=_air_elems, densities=_air_dens, name="air")

# =============================================================================
# Problem definition
# =============================================================================
SLABS = [
    (lead, 0.0, 5.0),
    (water, 5.0, 25.0),
    (concrete, 25.0, 55.0),
    (air, 55.0, 200.0),
]
SOURCE_ENERGY = 1.0  # MeV
BEAM_DIRECTION = [0.0, 0.0, 1.0]  # straight down the slab stack's axis
Z_BACK_BOUNDARY = -1.0  # cm — thin vacuum backing behind the source face
Z_SRC = 1.0e-6           # cm — source offset just inside the first slab

# NOTE: MC/DC silently truncates settings.output_name to 32 characters
# somewhere in its jitted settings storage. Keeping this <=32 chars avoids
# a mismatch between the file MC/DC actually writes and the path this
# script tries to reopen for post-processing.
OUTPUT_NAME = "mm_slabs_collimated_beam"
PLOT_PATH = os.path.join(_HERE, "multi_material_slabs_collimated_beam_flux.png")

MATERIALS = [m for m, _, _ in SLABS]
Z_FRONTS = [zf for _, zf, _ in SLABS]
Z_BACKS = [zb for _, _, zb in SLABS]
MATERIAL_NAMES = [m.name for m in MATERIALS]

# =============================================================================
# Surfaces: one PlaneZ per slab boundary, plus the backing and outer boundary
# =============================================================================
z_back_bound = mcdc.Surface.PlaneZ(z=Z_BACK_BOUNDARY, boundary_condition="vacuum")
z_planes = [mcdc.Surface.PlaneZ(z=Z_FRONTS[0])]  # z = 0.0, source face
for i, z_back in enumerate(Z_BACKS):
    bc = "vacuum" if i == len(Z_BACKS) - 1 else "none"
    z_planes.append(mcdc.Surface.PlaneZ(z=z_back, boundary_condition=bc))

# =============================================================================
# Cells: thin air-filled backing gap (bounded by the vacuum backing plane),
# then each material slab. With a forward-only beam this gap is never
# actually populated in steady state -- it only exists so the source's
# birth-cell locate at z = Z_SRC (a hair inside the first slab, not exactly
# on the z=0 boundary) remains unambiguous, matching the source-offset fix
# used throughout these problems.
# =============================================================================
cells = []
backing_cell = mcdc.Cell(
    region=+z_back_bound & -z_planes[0], fill=air, name="backing_gap"
)
for i in range(len(SLABS)):
    cells.append(
        mcdc.Cell(region=+z_planes[i] & -z_planes[i + 1], fill=MATERIALS[i])
    )

# =============================================================================
# Source: mono-directional 1.0 MeV collimated beam, straight into the stack.
# No isotropic/polar_cosine/azimuthal spread -- every particle starts with
# the same direction, giving a clean uncollided-beam attenuation profile.
# =============================================================================
mcdc.Source(
    position=[0.0, 0.0, Z_SRC],
    direction=BEAM_DIRECTION,
    energy=SOURCE_ENERGY,
    particle_type="photon",
)

# =============================================================================
# Tallies: track-length flux in each slab (single region per material here;
# subdivide further if a finer depth profile is needed within a thick slab)
# =============================================================================
tally_names = [f"slab_{i}_{name}" for i, name in enumerate(MATERIAL_NAMES)]
for name, cell in zip(tally_names, cells):
    mcdc.Tally(cell=cell, scores=["flux"], name=name)

# =============================================================================
# Settings
# =============================================================================
mcdc.settings.N_particle = 100000
mcdc.settings.N_batch = 10
mcdc.settings.rng_seed = 42
mcdc.settings.output_name = OUTPUT_NAME
mcdc.settings.use_progress_bar = False

# Slab cross-sectional area used to turn each cell's track length into a
# volume (needed to volume-normalize flux the same way as the sphere/cylinder
# problems). Since the geometry is infinite in x/y, this is a bookkeeping
# choice only -- pick any convenient value; 1 cm^2 keeps flux and "areal
# flux per unit area" numerically identical.
SLAB_AREA = 1.0  # cm^2


# =============================================================================
# Post-processing helpers (results table + plot)
# =============================================================================
def slab_volumes():
    """Volume (cm^3) of each slab, assuming unit cross-sectional area."""
    return [SLAB_AREA * (zb - zf) for zf, zb in zip(Z_FRONTS, Z_BACKS)]


def slab_midpoints():
    return [0.5 * (zf + zb) for zf, zb in zip(Z_FRONTS, Z_BACKS)]


def load_cell_flux(h5_path, names):
    import h5py

    means, sdevs = [], []
    with h5py.File(h5_path, "r") as f:
        for name in names:
            entry = f["tallies"][name]["flux"]
            means.append(float(np.squeeze(entry["mean"][()])))
            sdevs.append(float(np.squeeze(entry["sdev"][()])))
    return means, sdevs


def report_results(h5_path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw_means, raw_sdevs = load_cell_flux(h5_path, tally_names)
    volumes = slab_volumes()
    midpoints = slab_midpoints()

    flux = [m / v for m, v in zip(raw_means, volumes)]
    flux_sdev = [s / v for s, v in zip(raw_sdevs, volumes)]

    # ---- Results text file -----------------------------------------------
    txt_path = os.path.join(_HERE, OUTPUT_NAME + "_results.txt")
    with open(txt_path, "w") as f:
        f.write("\n")
        f.write("1 MeV collimated photon beam: lead -> water -> concrete -> air slab stack\n")
        f.write("=" * 92 + "\n")
        f.write(
            f"{'Slab':>4} {'Material':>10} {'z_front':>9} {'z_back':>9} {'thickness':>10} "
            f"{'Flux':>13} {'+/- 1 sigma':>13} {'rel err':>9}\n"
        )
        f.write(f"{'':>4} {'':>10} {'[cm]':>9} {'[cm]':>9} {'[cm]':>10} "
                f"{'[1/cm^2]':>13} {'[1/cm^2]':>13} {'[%]':>9}\n")
        f.write("-" * 92 + "\n")
        for i in range(len(SLABS)):
            rel = (flux_sdev[i] / flux[i] * 100.0) if flux[i] > 0 else float("nan")
            f.write(
                f"{i:>4} {MATERIAL_NAMES[i]:>10} {Z_FRONTS[i]:>9.1f} {Z_BACKS[i]:>9.1f} "
                f"{Z_BACKS[i] - Z_FRONTS[i]:>10.1f} {flux[i]:>13.4e} {flux_sdev[i]:>13.4e} "
                f"{rel:>9.2f}\n"
            )
        f.write("-" * 92 + "\n")
        f.write(
            f"Source: {SOURCE_ENERGY} MeV mono-directional beam, "
            f"direction={BEAM_DIRECTION}, at z = {Z_SRC} cm\n"
        )
        f.write(f"Histories: {mcdc.settings.N_particle} x {mcdc.settings.N_batch} batches\n")
        f.write("\n")
    print(f"Results written to: {txt_path}")

    # ---- Flux PNG --------------------------------------------------------
    color_by_material = {"lead": "tab:gray", "water": "tab:blue",
                          "concrete": "tab:brown", "air": "tab:cyan"}
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(midpoints, flux, "-", color="0.6", zorder=1, linewidth=1)
    for i in range(len(SLABS)):
        ax.errorbar(
            [midpoints[i]], [flux[i]], yerr=[flux_sdev[i]],
            fmt="o", capsize=4, color=color_by_material[MATERIAL_NAMES[i]],
            label=MATERIAL_NAMES[i] if MATERIAL_NAMES[i] not in
            [MATERIAL_NAMES[j] for j in range(i)] else None,
            zorder=2,
        )
    for z in Z_FRONTS[1:]:
        ax.axvline(z, color="k", ls=":", alpha=0.4, linewidth=1)

    ax.set_yscale("log")
    ax.set_xlabel("Depth z [cm]")
    ax.set_ylabel("Flux [photons / cm$^2$ per source photon]")
    ax.set_title("1 MeV Collimated Beam: Pb -> Water -> Concrete -> Air Slab Stack")
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    plt.close(fig)
    print(f"Flux plot written to: {PLOT_PATH}")
    print()

    return flux, flux_sdev


# =============================================================================
# Run — only when invoked directly as a script, not when exec()'d inline
# =============================================================================
if sys.argv[0].endswith(".py"):
    try:
        os.chdir(_HERE)
    except Exception:
        pass

    mcdc.run()

    from mpi4py import MPI

    if MPI.COMM_WORLD.Get_rank() == 0:
        h5_path = os.path.join(_HERE, OUTPUT_NAME + ".h5")
        report_results(h5_path)

        try:
            os.remove(h5_path)
        except OSError:
            pass
