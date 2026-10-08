"""
Finite lead cylinder problem — ENERGY DEPOSITION variant.

Same finite-cylinder geometry (radial CylinderZ shells intersected with axial
PlaneZ caps, single lead material) as lead_finite_cylinder.py, but each (r, z)
region now carries a second tally in addition to flux: scores=["energy_deposition"]
triggers MC/DC's collision-estimator tally family (SUPPORTED_SCORES_COLLISION
in constant.py), which scores deposited energy per collision rather than
track length. Dividing by cell volume gives an energy-deposition density -- a
dose/KERMA-like quantity -- directly, without needing a separate flux-to-dose
response-function conversion.

Everything else (materials, geometry, source) is unchanged from
lead_finite_cylinder.py.

NOTE ON ENERGY UNITS: as in the other _energy_spectrum/_energy_deposition
variants, verify whether your local photon branch reports energy_deposition
in eV or MeV -- the mainline (neutron) API's docstrings are in eV, but the
validated 1mev_pb_spheres.py script's source energy is passed in MeV.
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
RADII = [5.0, 10.0, 15.0, 20.0]
Z_BOUNDS = [-20.0, -10.0, 0.0, 10.0, 20.0]

SOURCE_ENERGY = 1.0  # MeV
OUTPUT_NAME = "lead_finite_cylinder_energy_deposition"
FLUX_PLOT_PATH = os.path.join(_HERE, "lead_finite_cylinder_energy_deposition_flux.png")
EDEP_PLOT_PATH = os.path.join(_HERE, "lead_finite_cylinder_energy_deposition_edep.png")

N_R = len(RADII)
N_Z = len(Z_BOUNDS) - 1

# =============================================================================
# Surfaces
# =============================================================================
cyl_surfaces = []
for i, r in enumerate(RADII):
    bc = "vacuum" if i == N_R - 1 else "none"
    cyl_surfaces.append(
        mcdc.Surface.CylinderZ(center=[0.0, 0.0], radius=r, boundary_condition=bc)
    )

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
mcdc.Source(position=[0.0, 0.0, 0.0], energy=SOURCE_ENERGY, particle_type="photon")

# =============================================================================
# Tallies: track-length flux AND collision-estimator energy deposition in
# every (r, z) region -- two separate named tallies per cell.
# =============================================================================
flux_tally_names = {}
edep_tally_names = {}
for ir in range(N_R):
    for iz in range(N_Z):
        flux_name = f"flux_r{ir}_z{iz}"
        edep_name = f"edep_r{ir}_z{iz}"
        flux_tally_names[(ir, iz)] = flux_name
        edep_tally_names[(ir, iz)] = edep_name
        mcdc.Tally(cell=cells[(ir, iz)], scores=["flux"], name=flux_name)
        mcdc.Tally(cell=cells[(ir, iz)], scores=["energy_deposition"], name=edep_name)

# =============================================================================
# Settings
# =============================================================================
mcdc.settings.N_particle = 200000
mcdc.settings.N_batch = 10
mcdc.settings.rng_seed = 42
mcdc.settings.output_name = OUTPUT_NAME
mcdc.settings.use_progress_bar = False


# =============================================================================
# Post-processing helpers (geometry + results table + heatmaps)
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
    if r_out**2 - r_in**2 > 0:
        r_vavg = (2.0 / 3.0) * (r_out**3 - r_in**3) / (r_out**2 - r_in**2)
    else:
        r_vavg = 0.0
    z_lo, z_hi = Z_BOUNDS[iz], Z_BOUNDS[iz + 1]
    z_mid = 0.5 * (z_lo + z_hi)
    return r_in, r_out, r_vavg, z_lo, z_hi, z_mid


def load_cell_data(h5_path, names):
    """Read raw tallies (mean, sdev) for the given score into (N_R, N_Z) grids."""
    import h5py
    import numpy as np

    means = np.zeros((N_R, N_Z))
    sdevs = np.zeros((N_R, N_Z))
    with h5py.File(h5_path, "r") as f:
        for ir in range(N_R):
            for iz in range(N_Z):
                tally_name = names[(ir, iz)]
                score_name = "flux" if tally_name.startswith("flux_") else "energy_deposition"
                entry = f["tallies"][tally_name][score_name]
                means[ir, iz] = float(np.squeeze(entry["mean"][()]))
                sdevs[ir, iz] = float(np.squeeze(entry["sdev"][()]))
    return means, sdevs


def report_results(h5_path):
    """Print a results table and save flux + energy-deposition heatmaps."""
    import numpy as np
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw_flux_means, raw_flux_sdevs = load_cell_data(h5_path, flux_tally_names)
    raw_edep_means, raw_edep_sdevs = load_cell_data(h5_path, edep_tally_names)

    volumes = np.array([[cell_volume(ir, iz) for iz in range(N_Z)] for ir in range(N_R)])

    flux = raw_flux_means / volumes
    flux_sdev = raw_flux_sdevs / volumes
    # Energy-deposition density: deposited energy per unit volume per source
    # particle (MeV/cm^3 per source photon, matching the source-energy unit
    # convention noted in the module docstring).
    edep = raw_edep_means / volumes
    edep_sdev = raw_edep_sdevs / volumes

    # ---- Results text file -----------------------------------------------
    txt_path = os.path.join(_HERE, OUTPUT_NAME + "_results.txt")
    with open(txt_path, "w") as f:
        f.write("\n")
        f.write("1 MeV photon point source in a finite lead cylinder\n")
        f.write("Track-length flux and collision-estimator energy deposition\n")
        f.write("=" * 118 + "\n")
        f.write(
            f"{'r-shell':>7} {'z-seg':>6} {'r_in':>7} {'r_out':>7} {'z_lo':>7} {'z_hi':>7} "
            f"{'Flux':>13} {'flux 1sig':>13} {'Edep dens':>13} {'edep 1sig':>13}\n"
        )
        f.write(f"{'':>7} {'':>6} {'[cm]':>7} {'[cm]':>7} {'[cm]':>7} {'[cm]':>7} "
                f"{'[1/cm^2]':>13} {'[1/cm^2]':>13} {'[MeV/cm^3]':>13} {'[MeV/cm^3]':>13}\n")
        f.write("-" * 118 + "\n")
        for ir in range(N_R):
            for iz in range(N_Z):
                r_in, r_out, r_vavg, z_lo, z_hi, z_mid = cell_bounds(ir, iz)
                f.write(
                    f"{ir:>7} {iz:>6} {r_in:>7.1f} {r_out:>7.1f} {z_lo:>7.1f} {z_hi:>7.1f} "
                    f"{flux[ir, iz]:>13.4e} {flux_sdev[ir, iz]:>13.4e} "
                    f"{edep[ir, iz]:>13.4e} {edep_sdev[ir, iz]:>13.4e}\n"
                )
        f.write("-" * 118 + "\n")
        f.write(f"Source: {SOURCE_ENERGY} MeV isotropic point source at the origin\n")
        f.write(f"Histories: {mcdc.settings.N_particle} x {mcdc.settings.N_batch} batches\n")
        f.write("\n")
    print(f"Results written to: {txt_path}")

    # ---- (r, z) heatmaps ----------------------------------------------------
    r_edges = [0.0] + RADII
    z_edges = Z_BOUNDS

    def _heatmap(data, title, cbar_label, path):
        log_data = np.log10(np.where(data > 0, data, np.nan))
        fig, ax = plt.subplots(figsize=(8, 6))
        mesh = ax.pcolormesh(z_edges, r_edges, log_data, shading="flat", cmap="viridis")
        cbar = fig.colorbar(mesh, ax=ax)
        cbar.set_label(cbar_label)
        ax.set_xlabel("z [cm]")
        ax.set_ylabel("r [cm]")
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"Wrote: {path}")

    _heatmap(
        flux,
        f"{SOURCE_ENERGY} MeV Point Source in Finite Lead Cylinder — Flux",
        "log$_{10}$(Flux) [photons / cm$^2$ per source photon]",
        FLUX_PLOT_PATH,
    )
    _heatmap(
        edep,
        f"{SOURCE_ENERGY} MeV Point Source in Finite Lead Cylinder — Energy Deposition",
        "log$_{10}$(Energy deposition density) [MeV / cm$^3$ per source photon]",
        EDEP_PLOT_PATH,
    )
    print()

    return flux, flux_sdev, edep, edep_sdev


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
