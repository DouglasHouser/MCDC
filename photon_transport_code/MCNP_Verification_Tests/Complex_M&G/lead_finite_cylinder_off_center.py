"""
Finite lead cylinder problem.

A 1.0 MeV isotropic point source at the origin sits inside a finite lead
cylinder built from radial CylinderZ surfaces intersected with axial PlaneZ
caps. Track-length flux is tallied in every (radial shell, axial segment)
region, giving a full 2D (r, z) flux map instead of the 1D radial profile from
the sphere problems.

Purpose: exercise the geometry engine's Boolean intersection of a quadric
surface (radial cylinder) with linear planes (axial caps) -- a genuinely more
complex geometry than nested spheres or slabs -- while keeping to a single
material (lead) so nothing new is asked of the material/cross-section
handling. Same core building blocks (surfaces, cell region algebra, cell
tallies) that MCDC's geometry engine already fully supports; no new tally
type or boundary-crossing logic is needed.
"""

import math
import os
import sys

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
# Material: lead (Z = 82), same as 1mev_pb_spheres.py
# =============================================================================
lead = mcdc.PhotonMaterial(elements=[82], densities=[0.03299], name="lead")

# =============================================================================
# Problem definition
# =============================================================================
# Radial shell outer boundaries (cm), outermost carries the vacuum boundary.
RADII = [5.0, 10.0, 15.0, 20.0]
# Axial segment boundaries (cm), centered on the source; endpoints carry the
# vacuum boundary.
Z_BOUNDS = [-20.0, -10.0, 0.0, 10.0, 20.0]

SOURCE_ENERGY = 1.0  # MeV
OUTPUT_NAME = "lead_finite_cylinder"
PLOT_PATH = os.path.join(_HERE, "lead_finite_cylinder_flux.png")

N_R = len(RADII)          # number of radial shells
N_Z = len(Z_BOUNDS) - 1    # number of axial segments

# =============================================================================
# Surfaces
# =============================================================================
# Radial cylinders (axis along z), outermost is the radial vacuum boundary.
cyl_surfaces = []
for i, r in enumerate(RADII):
    bc = "vacuum" if i == N_R - 1 else "none"
    cyl_surfaces.append(
        mcdc.Surface.CylinderZ(center=[0.0, 0.0], radius=r, boundary_condition=bc)
    )

# Axial caps, top and bottom carry the vacuum boundary.
z_surfaces = []
for i, z in enumerate(Z_BOUNDS):
    bc = "vacuum" if (i == 0 or i == len(Z_BOUNDS) - 1) else "none"
    z_surfaces.append(mcdc.Surface.PlaneZ(z=z, boundary_condition=bc))

# =============================================================================
# Cells: one per (radial shell, axial segment), all filled with lead
# =============================================================================
cells = {}  # (ir, iz) -> Cell
for ir in range(N_R):
    if ir == 0:
        radial_region = -cyl_surfaces[0]
    else:
        radial_region = +cyl_surfaces[ir - 1] & -cyl_surfaces[ir]
    for iz in range(N_Z):
        axial_region = +z_surfaces[iz] & -z_surfaces[iz + 1]
        cells[(ir, iz)] = mcdc.Cell(
            region=radial_region & axial_region,
            fill=lead,
            name=f"r{ir}_z{iz}",
        )

# =============================================================================
# Source: isotropic 1.0 MeV photon point source at the origin
# =============================================================================
mcdc.Source(position=[0.0, 0.0, -15.0], energy=SOURCE_ENERGY, particle_type="photon")

# =============================================================================
# Tallies: track-length flux in every (r, z) region
# =============================================================================
tally_names = {}
for ir in range(N_R):
    for iz in range(N_Z):
        name = f"region_r{ir}_z{iz}"
        tally_names[(ir, iz)] = name
        mcdc.Tally(cell=cells[(ir, iz)], scores=["flux"], name=name)

# =============================================================================
# Settings
# =============================================================================
mcdc.settings.N_particle = 200000
mcdc.settings.N_batch = 10
mcdc.settings.rng_seed = 42
mcdc.settings.output_name = OUTPUT_NAME
mcdc.settings.use_progress_bar = False


# =============================================================================
# Post-processing helpers (geometry + results table + heatmap)
# =============================================================================
def cell_volume(ir, iz):
    """Volume (cm^3) of the (ir, iz) cylindrical-shell segment."""
    r_in = 0.0 if ir == 0 else RADII[ir - 1]
    r_out = RADII[ir]
    z_lo, z_hi = Z_BOUNDS[iz], Z_BOUNDS[iz + 1]
    return math.pi * (r_out**2 - r_in**2) * (z_hi - z_lo)


def cell_bounds(ir, iz):
    """(r_in, r_out, r_vavg, z_lo, z_hi, z_mid) for the (ir, iz) region."""
    r_in = 0.0 if ir == 0 else RADII[ir - 1]
    r_out = RADII[ir]
    # Area-averaged radius of an annulus: (2/3)*(r_out^3-r_in^3)/(r_out^2-r_in^2)
    if r_out**2 - r_in**2 > 0:
        r_vavg = (2.0 / 3.0) * (r_out**3 - r_in**3) / (r_out**2 - r_in**2)
    else:
        r_vavg = 0.0
    z_lo, z_hi = Z_BOUNDS[iz], Z_BOUNDS[iz + 1]
    z_mid = 0.5 * (z_lo + z_hi)
    return r_in, r_out, r_vavg, z_lo, z_hi, z_mid


def load_cell_flux(h5_path):
    """Read raw track-length flux tallies (mean, sdev) into (N_R, N_Z) grids."""
    import h5py
    import numpy as np

    means = np.zeros((N_R, N_Z))
    sdevs = np.zeros((N_R, N_Z))
    with h5py.File(h5_path, "r") as f:
        for ir in range(N_R):
            for iz in range(N_Z):
                entry = f["tallies"][tally_names[(ir, iz)]]["flux"]
                means[ir, iz] = float(np.squeeze(entry["mean"][()]))
                sdevs[ir, iz] = float(np.squeeze(entry["sdev"][()]))
    return means, sdevs


def report_results(h5_path):
    """Print a results table and save the (r, z) flux heatmap. Returns flux grid."""
    import numpy as np
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw_means, raw_sdevs = load_cell_flux(h5_path)

    volumes = np.array([[cell_volume(ir, iz) for iz in range(N_Z)] for ir in range(N_R)])
    flux = raw_means / volumes
    flux_sdev = raw_sdevs / volumes

    # ---- Results text file -----------------------------------------------
    txt_path = os.path.join(_HERE, OUTPUT_NAME + "_results.txt")
    with open(txt_path, "w") as f:
        f.write("\n")
        f.write("1 MeV photon point source in a finite lead cylinder\n")
        f.write("=" * 96 + "\n")
        f.write(
            f"{'r-shell':>7} {'z-seg':>6} {'r_in':>7} {'r_out':>7} {'z_lo':>7} {'z_hi':>7} "
            f"{'Volume':>13} {'Flux':>13} {'+/- 1 sigma':>13} {'rel err':>9}\n"
        )
        f.write(f"{'':>7} {'':>6} {'[cm]':>7} {'[cm]':>7} {'[cm]':>7} {'[cm]':>7} "
                f"{'[cm^3]':>13} {'[1/cm^2]':>13} {'[1/cm^2]':>13} {'[%]':>9}\n")
        f.write("-" * 96 + "\n")
        for ir in range(N_R):
            for iz in range(N_Z):
                r_in, r_out, r_vavg, z_lo, z_hi, z_mid = cell_bounds(ir, iz)
                f_val = flux[ir, iz]
                s_val = flux_sdev[ir, iz]
                rel = (s_val / f_val * 100.0) if f_val > 0 else float("nan")
                f.write(
                    f"{ir:>7} {iz:>6} {r_in:>7.1f} {r_out:>7.1f} {z_lo:>7.1f} {z_hi:>7.1f} "
                    f"{volumes[ir, iz]:>13.4e} {f_val:>13.4e} {s_val:>13.4e} {rel:>9.2f}\n"
                )
        f.write("-" * 96 + "\n")
        f.write(f"Source: {SOURCE_ENERGY} MeV isotropic point source at the origin\n")
        f.write(f"Histories: {mcdc.settings.N_particle} x {mcdc.settings.N_batch} batches\n")
        f.write("\n")
    print(f"Results written to: {txt_path}")

    # ---- (r, z) flux heatmap ----------------------------------------------
    r_edges = [0.0] + RADII
    z_edges = Z_BOUNDS
    log_flux = np.log10(np.where(flux > 0, flux, np.nan))

    fig, ax = plt.subplots(figsize=(8, 6))
    mesh = ax.pcolormesh(
        z_edges, r_edges, log_flux, shading="flat", cmap="viridis"
    )
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label("log$_{10}$(Flux) [photons / cm$^2$ per source photon]")
    ax.set_xlabel("z [cm]")
    ax.set_ylabel("r [cm]")
    ax.set_title(f"{SOURCE_ENERGY} MeV Point Source in Finite Lead Cylinder — (r, z) Flux Map")
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    plt.close(fig)
    print(f"Flux map written to: {PLOT_PATH}")
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
