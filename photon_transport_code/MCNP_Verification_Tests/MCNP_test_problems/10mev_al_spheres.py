"""
Test problem: 10 MeV photon point source in an aluminum medium.

A monoenergetic, isotropic 10.0 MeV photon point source sits at the origin,
embedded in aluminum.  A 40 cm aluminum sphere is divided into twenty 2 cm
thick concentric regions (spheres at 2, 4, 6, ..., 40 cm):

    region 0  :  0 < r <  2 cm      (inner sphere)
    region 1  :  2 < r <  4 cm      (shell)
    ...
    region 19 : 38 < r < 40 cm      (shell, outer boundary = vacuum)

A track-length (volume / MCNP "F4"-style) flux tally is placed on each region.
MCDC accumulates sum(track_length * weight) / N_source for each cell, so this
script divides each raw tally by the cell volume to recover the scalar flux
[photons / cm^2 per source photon].

Unlike the benchmark problems, this script is fully self-contained: it runs the
simulation, reads its own results back, prints a results table to the terminal,
and writes a flux-vs-radius plot (flux PNG) into this same directory.  The
intermediate HDF5 file is removed at the end so the deliverables are just the
table and the PNG.

Modeled after benchmark_1a_const_pure_absorption/problem.py.
"""

import math
import os
import sys

# ---------------------------------------------------------------------------
# Path setup — make the local mcdc package importable
# ---------------------------------------------------------------------------
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    # photon_transport_code/MCNP_Verification_Tests/MCNP_test_problems -> MCDC root
    _ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
except NameError:
    _HERE = os.getcwd()
    _ROOT = _HERE

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import mcdc

# =============================================================================
# Problem definition
# =============================================================================
# Aluminum at standard density 2.7 g/cm^3:
#   n = (2.7 g/cm^3 * 6.022e23 /mol) / 26.982 g/mol = 0.06026 atoms/barn-cm
RADII = [float(r) for r in range(2, 41, 2)]  # 2, 4, ..., 40 cm (2 cm shells)
SOURCE_ENERGY = 10.0  # MeV
OUTPUT_NAME = "10mev_al_spheres"
PLOT_PATH = os.path.join(_HERE, "10mev_al_spheres_flux.png")

# =============================================================================
# Material: aluminum (Z = 13)
# =============================================================================
aluminum = mcdc.PhotonMaterial(
    elements=[13],
    densities=[0.06026],
    name="aluminum",
)

# =============================================================================
# Surfaces: 5 concentric spheres, outermost has a vacuum boundary
# =============================================================================
spheres = []
for r in RADII:
    bc = "vacuum" if r == RADII[-1] else "none"
    s = mcdc.Surface.Sphere(center=[0, 0, 0], radius=r, boundary_condition=bc)
    spheres.append(s)

# =============================================================================
# Cells: innermost sphere + concentric shells (one tally region each)
# =============================================================================
cells = []
cells.append(mcdc.Cell(region=-spheres[0], fill=aluminum))
for i in range(1, len(spheres)):
    cells.append(mcdc.Cell(region=+spheres[i - 1] & -spheres[i], fill=aluminum))

# =============================================================================
# Source: isotropic 10.0 MeV photon point source at the origin
# =============================================================================
mcdc.Source(position=[0.0, 0.0, 0.0], energy=SOURCE_ENERGY, particle_type="photon")

# =============================================================================
# Tallies: track-length flux in each spherical region
# =============================================================================
# Name each tally so its result can be read back in radial order.
tally_names = [f"region_{i}" for i in range(len(cells))]
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


# =============================================================================
# Post-processing helpers (geometry + results table + plot)
# =============================================================================
def shell_volumes(radii):
    """Volume of the inner sphere and each concentric shell, in cm^3."""
    volumes = []
    r_inner = 0.0
    for r_outer in radii:
        volumes.append((4.0 / 3.0) * math.pi * (r_outer**3 - r_inner**3))
        r_inner = r_outer
    return volumes


def region_bounds(radii):
    """(r_inner, r_outer, r_volume_averaged) for each region.

    The reporting radius is the volume-averaged radius of the spherical
    shell, i.e. the integral of r weighted by the differential volume:

        r_vavg = int(r * 4*pi*r^2 dr) / int(4*pi*r^2 dr)
               = (3/4) * (r_out^4 - r_in^4) / (r_out^3 - r_in^3)

    This is where the volume-integrated track-length flux is best
    represented, rather than the geometric midpoint.
    """
    bounds = []
    r_inner = 0.0
    for r_outer in radii:
        r_vavg = 0.75 * (r_outer**4 - r_inner**4) / (r_outer**3 - r_inner**3)
        bounds.append((r_inner, r_outer, r_vavg))
        r_inner = r_outer
    return bounds


def load_cell_flux(h5_path, names):
    """Read raw track-length flux tallies (mean, sdev) in the given order."""
    import h5py
    import numpy as np

    means, sdevs = [], []
    with h5py.File(h5_path, "r") as f:
        for name in names:
            entry = f["tallies"][name]["flux"]
            means.append(float(np.squeeze(entry["mean"][()])))
            sdevs.append(float(np.squeeze(entry["sdev"][()])))
    return means, sdevs


def report_results(h5_path):
    """Print a results table and save the flux PNG. Returns flux arrays."""
    import matplotlib

    matplotlib.use("Agg")  # headless / no display
    import matplotlib.pyplot as plt

    raw_means, raw_sdevs = load_cell_flux(h5_path, tally_names)
    volumes = shell_volumes(RADII)
    bounds = region_bounds(RADII)

    # Volume-normalize to a scalar flux (MCNP F4 convention).
    flux = [m / v for m, v in zip(raw_means, volumes)]
    flux_sdev = [s / v for s, v in zip(raw_sdevs, volumes)]

    # ---- Results text file -----------------------------------------------
    txt_path = os.path.join(_HERE, OUTPUT_NAME + "_results.txt")
    with open(txt_path, "w") as f:
        f.write("\n")
        f.write("10 MeV photon point source in aluminum - track-length flux\n")
        f.write("=" * 84 + "\n")
        f.write(
            f"{'Region':>6} {'r_in':>7} {'r_out':>7} {'r_vavg':>7} "
            f"{'Volume':>13} {'Flux':>13} {'+/- 1 sigma':>13} {'rel err':>9}\n"
        )
        f.write(f"{'':>6} {'[cm]':>7} {'[cm]':>7} {'[cm]':>7} {'[cm^3]':>13} "
                f"{'[1/cm^2]':>13} {'[1/cm^2]':>13} {'[%]':>9}\n")
        f.write("-" * 84 + "\n")
        for i, (r_in, r_out, r_vavg) in enumerate(bounds):
            rel = (flux_sdev[i] / flux[i] * 100.0) if flux[i] > 0 else float("nan")
            f.write(
                f"{i:>6} {r_in:>7.1f} {r_out:>7.1f} {r_vavg:>7.2f} "
                f"{volumes[i]:>13.4e} {flux[i]:>13.4e} {flux_sdev[i]:>13.4e} {rel:>9.2f}\n"
            )
        f.write("-" * 84 + "\n")
        f.write(f"Source: {SOURCE_ENERGY} MeV isotropic point source\n")
        f.write(f"Histories: {mcdc.settings.N_particle} x {mcdc.settings.N_batch} batches\n")
        f.write("\n")
    print(f"Results written to: {txt_path}")

    # ---- Flux PNG --------------------------------------------------------
    r_vavg = [b[2] for b in bounds]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(
        r_vavg,
        flux,
        yerr=flux_sdev,
        fmt="o-",
        capsize=4,
        color="tab:blue",
        label="MCDC track-length flux",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Radius (volume-averaged) [cm]")
    ax.set_ylabel("Flux [photons / cm$^2$ per source photon]")
    ax.set_title(f"{SOURCE_ENERGY} MeV Photon Point Source in Aluminum")
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

    # Results live in the HDF5 file MCDC just wrote next to this script.
    from mpi4py import MPI

    if MPI.COMM_WORLD.Get_rank() == 0:
        h5_path = os.path.join(_HERE, OUTPUT_NAME + ".h5")
        report_results(h5_path)

        # Drop the intermediate HDF5 — deliverables are the table + PNG only.
        try:
            os.remove(h5_path)
        except OSError:
            pass
