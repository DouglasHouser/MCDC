"""
Multi-material planar slab stack — MESH TALLY variant.

Same lead -> water -> concrete -> air slab geometry and materials as
multi_material_slabs.py, but the four hand-built per-slab cell tallies are
replaced by a single mcdc.MeshUniform tally spanning the full domain depth
with a fine z-grid. Per tally.py, a tally with a mesh= filter and no cell=
filter attaches across every cell, so this gives one continuous flux-vs-depth
profile that cuts across all four material boundaries (and the backing gap),
instead of one flux number per material.

Everything else (materials, geometry, source) is unchanged from
multi_material_slabs.py.
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
Z_BACK_BOUNDARY = -1.0  # cm — thin vacuum backing behind the source face
Z_SRC = 1.0e-6           # cm — source offset just inside the first slab

OUTPUT_NAME = "multi_material_slabs_mesh_tally"
PLOT_PATH = os.path.join(_HERE, "multi_material_slabs_mesh_tally_flux.png")

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
# Cells: thin air-filled backing gap, then each material slab (unchanged from
# multi_material_slabs.py -- the mesh tally below scores across all of these)
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
# Source: isotropic 1.0 MeV photon point source, offset into the first slab
# =============================================================================
mcdc.Source(
    position=[0.0, 0.0, Z_SRC],
    energy=SOURCE_ENERGY,
    isotropic=True,
    particle_type="photon",
)

# =============================================================================
# Mesh + tally: one fine z-grid spanning the backing gap through the full
# slab stack. x and y are left at their default (-inf, +inf) single bin,
# matching the geometry's infinite lateral extent.
# =============================================================================
DZ = 1.0  # cm per mesh bin
N_Z = int(round((Z_BACKS[-1] - Z_BACK_BOUNDARY) / DZ))

depth_mesh = mcdc.MeshUniform(
    name="depth_mesh",
    z=(Z_BACK_BOUNDARY, DZ, N_Z),
)
mcdc.Tally(mesh=depth_mesh, scores=["flux"], name="depth_profile")

# =============================================================================
# Settings
# =============================================================================
mcdc.settings.N_particle = 100000
mcdc.settings.N_batch = 10
mcdc.settings.rng_seed = 42
mcdc.settings.output_name = OUTPUT_NAME
mcdc.settings.use_progress_bar = False

# Nominal cross-sectional area used to turn each mesh voxel's track length
# into a volume for flux normalization. The mesh's actual x/y extent is
# infinite (matching the infinite-slab geometry), so -- exactly as in
# multi_material_slabs.py's SLAB_AREA convention -- a nominal 1 cm^2 area is
# used instead; this keeps normalization consistent between the two scripts.
SLAB_AREA = 1.0  # cm^2


# =============================================================================
# Post-processing helpers (results table + plot)
# =============================================================================
def mesh_bin_edges():
    return Z_BACK_BOUNDARY + DZ * np.arange(N_Z + 1)


def mesh_bin_midpoints():
    edges = mesh_bin_edges()
    return 0.5 * (edges[:-1] + edges[1:])


def material_at_z(z):
    """Return the material name of the slab containing depth z (or
    'backing_gap' / 'outside' if beyond the modeled domain)."""
    if z < Z_FRONTS[0]:
        return "backing_gap"
    for name, zf, zb in zip(MATERIAL_NAMES, Z_FRONTS, Z_BACKS):
        if zf <= z < zb:
            return name
    return "outside"


def load_mesh_flux(h5_path):
    import h5py

    with h5py.File(h5_path, "r") as f:
        entry = f["tallies"]["depth_profile"]["flux"]
        mean = np.squeeze(entry["mean"][()])
        sdev = np.squeeze(entry["sdev"][()])
    return np.atleast_1d(mean), np.atleast_1d(sdev)


def report_results(h5_path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw_mean, raw_sdev = load_mesh_flux(h5_path)
    voxel_volume = SLAB_AREA * DZ

    flux = raw_mean / voxel_volume
    flux_sdev = raw_sdev / voxel_volume

    midpoints = mesh_bin_midpoints()
    materials_per_bin = [material_at_z(z) for z in midpoints]

    # ---- Results text file -----------------------------------------------
    txt_path = os.path.join(_HERE, OUTPUT_NAME + "_results.txt")
    with open(txt_path, "w") as f:
        f.write("\n")
        f.write("1 MeV photon point source: lead -> water -> concrete -> air slab stack\n")
        f.write(f"Mesh-tallied depth profile, dz = {DZ} cm ({N_Z} bins)\n")
        f.write("=" * 78 + "\n")
        f.write(
            f"{'z_mid':>8} {'Material':>10} {'Flux':>13} {'+/- 1 sigma':>13} {'rel err':>9}\n"
        )
        f.write(f"{'[cm]':>8} {'':>10} {'[1/cm^2]':>13} {'[1/cm^2]':>13} {'[%]':>9}\n")
        f.write("-" * 78 + "\n")
        for i in range(N_Z):
            f_val = flux[i]
            s_val = flux_sdev[i]
            rel = (s_val / f_val * 100.0) if f_val > 0 else float("nan")
            f.write(
                f"{midpoints[i]:>8.1f} {materials_per_bin[i]:>10} "
                f"{f_val:>13.4e} {s_val:>13.4e} {rel:>9.2f}\n"
            )
        f.write("-" * 78 + "\n")
        f.write(f"Source: {SOURCE_ENERGY} MeV isotropic point source at z = {Z_SRC} cm\n")
        f.write(f"Histories: {mcdc.settings.N_particle} x {mcdc.settings.N_batch} batches\n")
        f.write("\n")
    print(f"Results written to: {txt_path}")

    # ---- Flux PNG ----------------------------------------------------------
    color_by_material = {"lead": "tab:gray", "water": "tab:blue",
                          "concrete": "tab:brown", "air": "tab:cyan",
                          "backing_gap": "0.7", "outside": "0.7"}
    fig, ax = plt.subplots(figsize=(9, 5))

    # Color the curve by material in contiguous segments.
    seg_start = 0
    for i in range(1, N_Z + 1):
        if i == N_Z or materials_per_bin[i] != materials_per_bin[seg_start]:
            mat = materials_per_bin[seg_start]
            ax.plot(
                midpoints[seg_start:i], flux[seg_start:i], "-",
                color=color_by_material.get(mat, "k"), linewidth=1.5,
                label=mat if mat not in materials_per_bin[:seg_start] else None,
            )
            seg_start = i

    for z in Z_FRONTS[1:]:
        ax.axvline(z, color="k", ls=":", alpha=0.4, linewidth=1)

    ax.set_yscale("log")
    ax.set_xlabel("Depth z [cm]")
    ax.set_ylabel("Flux [photons / cm$^2$ per source photon]")
    ax.set_title("Mesh-Tallied Depth Profile: Pb -> Water -> Concrete -> Air")
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
