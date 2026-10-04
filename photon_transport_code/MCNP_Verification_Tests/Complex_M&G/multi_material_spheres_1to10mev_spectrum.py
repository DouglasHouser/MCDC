"""
Multi-material concentric sphere problem — 1-10 MeV UNIFORM SOURCE variant.

Same lead -> iron -> concrete -> water shell geometry, materials, and
energy-binned tallies as multi_material_spheres_energy_spectrum.py, but the
source is no longer mono-energetic at 1 MeV. Instead it isotropically emits
photons with energy sampled uniformly at random between ENERGY_MIN and
ENERGY_MAX (1-10 MeV by default), using mcdc's native tabulated-PDF source
support rather than a hand-rolled discrete multi-source approximation.

NATIVE CONTINUOUS-ENERGY SOURCE (see source.py, class Source):
    Source.__init__ checks `type(energy) == float` to decide between a
    mono-energetic source and a tabulated PDF. Passing anything else
    (e.g. a 2-element list [grid_array, pdf_array]) routes to:
        self.energy_pdf = DistributionTabulated(energy[0], energy[1])
    The class's own default mono-energetic source is actually implemented
    internally as a *narrow* tabulated PDF -- a 2-point table
    ([1.0e6 - 1, 1.0e6 + 1], [1.0, 1.0]) that is uniform across a 2 eV-wide
    band, i.e. a delta function in practice. This script does the exact same
    thing but stretches that flat 2-point table across the full 1-10 MeV
    range: energy=[[ENERGY_MIN, ENERGY_MAX], [1.0, 1.0]] gives a uniform PDF
    (via linear interpolation between the two equal-height table points)
    over the whole interval. No extra machinery needed.

*** UNITS: MeV ***
source.py's docstring and default (self.energy = 1.0e6 <-> comment
"mono-energetic at 1 MeV") describe `energy` as being in eV, which is the
opposite of the working assumption in multi_material_spheres_energy_spectrum.py,
where the previously-validated 1mev_pb_spheres.py script used energy=1.0 and
reproduced a 1 MeV source. This script goes with the MeV convention to stay
consistent with your other validated scripts. If tally results look off by
a factor of 1e6 (or photons look effectively unattenuated / fully absorbed
right at the surface), that mismatch is the first thing to check.

Everything else (materials, geometry, cell/tally structure) is unchanged
from multi_material_spheres_energy_spectrum.py.
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
    8: 15.999,   # O
    11: 22.990,  # Na
    12: 24.305,  # Mg
    13: 26.982,  # Al
    14: 28.085,  # Si
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

_fe_elems, _fe_dens = _number_densities(7.874, {26: 1.0})
iron = mcdc.PhotonMaterial(elements=_fe_elems, densities=_fe_dens, name="iron")

_concrete_elems, _concrete_dens = _number_densities(
    2.3, {8: 0.529107, 11: 0.016, 12: 0.002, 13: 0.033872, 14: 0.337021,
          20: 0.044, 26: 0.014, 1: 0.010}
)
concrete = mcdc.PhotonMaterial(
    elements=_concrete_elems, densities=_concrete_dens, name="concrete"
)

_water_elems, _water_dens = _number_densities(1.0, {1: 0.111898, 8: 0.888102})
water = mcdc.PhotonMaterial(elements=_water_elems, densities=_water_dens, name="water")

# =============================================================================
# Problem definition
# =============================================================================
SHELLS = [
    (lead, 2.0), (lead, 4.0), (lead, 6.0),
    (iron, 10.0), (iron, 14.0), (iron, 18.0),
    (concrete, 24.0), (concrete, 30.0), (concrete, 36.0),
    (water, 46.0), (water, 56.0), (water, 66.0),
]

# ---------------------------------------------------------------------------
# Source energy range and unit convention
# ---------------------------------------------------------------------------
ENERGY_MIN_MEV = 1.0
ENERGY_MAX_MEV = 10.0

# Energy values passed to mcdc.Source/mcdc.Tally are in MeV -- see the
# UNITS note in the module docstring.
ENERGY_MIN = ENERGY_MIN_MEV
ENERGY_MAX = ENERGY_MAX_MEV

# NOTE: MC/DC silently truncates settings.output_name to 32 characters
# somewhere in its jitted settings storage. Keeping this <=32 chars avoids
# a mismatch between the file MC/DC actually writes and the path this
# script tries to reopen for post-processing.
# Deliberately distinct from multi_material_spheres_energy_spectrum.py's
# "mm_spheres_energy_spectrum" so the two problems never collide on disk.
OUTPUT_NAME = "mm_spheres_1to10mev_spec"
PLOT_PATH = os.path.join(_HERE, "multi_material_spheres_1to10mev_spectrum_flux.png")

MATERIALS = [m for m, _ in SHELLS]
RADII = [r for _, r in SHELLS]
MATERIAL_NAMES = [m.name for m in MATERIALS]

# Energy bin edges, log-spaced from just above 0 up to the top of the source
# range, so both the down-scattered Compton continuum (near 0) and the
# uncollided/near-uncollided photons (up to 10 MeV) are resolved. In the
# same units as ENERGY_MIN/ENERGY_MAX above.
ENERGY_EDGES = np.logspace(np.log10(0.01), np.log10(ENERGY_MAX_MEV), 41)
N_ENERGY = len(ENERGY_EDGES) - 1
ENERGY_MID = 0.5 * (ENERGY_EDGES[:-1] + ENERGY_EDGES[1:])
ENERGY_MID_MEV = ENERGY_MID  # already MeV; kept as a separate name for the reporting/plot code below

# =============================================================================
# Surfaces: concentric spheres, outermost has a vacuum boundary
# =============================================================================
spheres = []
for r in RADII:
    bc = "vacuum" if r == RADII[-1] else "none"
    s = mcdc.Surface.Sphere(center=[0, 0, 0], radius=r, boundary_condition=bc)
    spheres.append(s)

# =============================================================================
# Cells: innermost sphere + concentric shells, each filled with its own material
# =============================================================================
cells = []
cells.append(mcdc.Cell(region=-spheres[0], fill=MATERIALS[0]))
for i in range(1, len(spheres)):
    cells.append(
        mcdc.Cell(region=+spheres[i - 1] & -spheres[i], fill=MATERIALS[i])
    )

# =============================================================================
# Source: isotropic photon point source, energy sampled uniformly in
# [ENERGY_MIN, ENERGY_MAX] via a flat 2-point tabulated PDF (native support
# in Source -- see the DistributionTabulated note in the module docstring).
# =============================================================================
mcdc.Source(
    position=[0.0, 0.0, 0.0],
    energy=[np.array([ENERGY_MIN, ENERGY_MAX]), np.array([1.0, 1.0])],
    particle_type="photon",
)

# =============================================================================
# Tallies: energy-binned track-length flux in each spherical region
# =============================================================================
tally_names = [f"region_{i}" for i in range(len(cells))]
for name, cell in zip(tally_names, cells):
    mcdc.Tally(cell=cell, scores=["flux"], energy=ENERGY_EDGES, name=name)

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
    volumes = []
    r_inner = 0.0
    for r_outer in radii:
        volumes.append((4.0 / 3.0) * math.pi * (r_outer**3 - r_inner**3))
        r_inner = r_outer
    return volumes


def region_bounds(radii):
    bounds = []
    r_inner = 0.0
    for r_outer in radii:
        r_vavg = 0.75 * (r_outer**4 - r_inner**4) / (r_outer**3 - r_inner**3)
        bounds.append((r_inner, r_outer, r_vavg))
        r_inner = r_outer
    return bounds


def load_cell_flux_spectrum(h5_path, names):
    """Read energy-binned track-length flux tallies (mean, sdev) for each
    region, returned as (N_region, N_energy) arrays."""
    import h5py

    means = np.zeros((len(names), N_ENERGY))
    sdevs = np.zeros((len(names), N_ENERGY))
    with h5py.File(h5_path, "r") as f:
        for i, name in enumerate(names):
            entry = f["tallies"][name]["flux"]
            means[i, :] = np.squeeze(entry["mean"][()])
            sdevs[i, :] = np.squeeze(entry["sdev"][()])
    return means, sdevs


def report_results(h5_path):
    """Print an energy-resolved results table and save the spectrum PNG."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw_means, raw_sdevs = load_cell_flux_spectrum(h5_path, tally_names)
    volumes = shell_volumes(RADII)
    bounds = region_bounds(RADII)

    # Volume-normalize each energy bin's tally to a scalar flux.
    flux = raw_means / np.array(volumes)[:, None]
    flux_sdev = raw_sdevs / np.array(volumes)[:, None]

    # ---- Results text file -----------------------------------------------
    txt_path = os.path.join(_HERE, OUTPUT_NAME + "_results.txt")
    with open(txt_path, "w") as f:
        f.write("\n")
        f.write(
            f"{ENERGY_MIN_MEV:.1f}-{ENERGY_MAX_MEV:.1f} MeV uniform isotropic photon "
            "point source: lead -> iron -> concrete -> water\n"
        )
        f.write("Energy-binned track-length flux per shell\n")
        f.write("=" * 100 + "\n")
        header = f"{'Region':>6} {'Material':>10} {'r_vavg':>7} "
        header += "".join(f"{e:>11.3f}" for e in ENERGY_MID_MEV) + "\n"
        f.write(header)
        f.write(f"{'':>6} {'':>10} {'[cm]':>7} " + "  MeV bin  " * 0 + "\n")
        f.write("-" * 100 + "\n")
        for i, (r_in, r_out, r_vavg) in enumerate(bounds):
            row = f"{i:>6} {MATERIAL_NAMES[i]:>10} {r_vavg:>7.2f} "
            row += "".join(f"{flux[i, j]:>11.3e}" for j in range(N_ENERGY))
            f.write(row + "\n")
        f.write("-" * 100 + "\n")
        f.write(f"Columns are flux [1/cm^2 per source photon] in each energy bin (MeV):\n")
        f.write(f"  Bin edges (MeV): {ENERGY_EDGES.tolist()}\n")
        f.write("\n")

        # ---- Standard deviation table -----------------------------------
        # Same shape/units as the flux table above (volume-normalized, per
        # source photon), so each run's own statistical error can be pulled
        # directly from its results.txt rather than needing a separate
        # reference run for a run-to-run proxy.
        f.write("=" * 100 + "\n")
        f.write("Standard deviation of the above (same shape/units as the flux table)\n")
        f.write("=" * 100 + "\n")
        f.write(header)
        f.write(f"{'':>6} {'':>10} {'[cm]':>7} " + "  MeV bin  " * 0 + "\n")
        f.write("-" * 100 + "\n")
        for i, (r_in, r_out, r_vavg) in enumerate(bounds):
            row = f"{i:>6} {MATERIAL_NAMES[i]:>10} {r_vavg:>7.2f} "
            row += "".join(f"{flux_sdev[i, j]:>11.3e}" for j in range(N_ENERGY))
            f.write(row + "\n")
        f.write("-" * 100 + "\n")
        f.write("Columns are the sdev of flux [1/cm^2 per source photon] in each energy bin (MeV):\n")
        f.write(
            f"Source: uniform random energy in [{ENERGY_MIN_MEV}, {ENERGY_MAX_MEV}] MeV, "
            "isotropic point source\n"
        )
        f.write("Energy input units passed to mcdc.Source: MeV\n")
        f.write(f"Histories: {mcdc.settings.N_particle} x {mcdc.settings.N_batch} batches\n")
        f.write("\n")
    print(f"Results written to: {txt_path}")

    # ---- Spectrum PNG: one line per shell, energy on x-axis ---------------
    color_by_material = {"lead": "tab:gray", "iron": "tab:orange",
                          "concrete": "tab:brown", "water": "tab:blue"}
    fig, ax = plt.subplots(figsize=(8, 5))
    for i in range(len(bounds)):
        mat = MATERIAL_NAMES[i]
        ax.plot(
            ENERGY_MID_MEV, flux[i, :], "-o", markersize=3,
            color=color_by_material[mat], alpha=0.3 + 0.7 * (i % 3) / 2.0,
            label=f"{mat} (r_vavg={bounds[i][2]:.1f} cm)" if i % 3 == 2 else None,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Energy [MeV]")
    ax.set_ylabel("Flux [photons / cm$^2$ per source photon]")
    ax.set_title(
        f"Energy Spectrum by Shell: Pb -> Fe -> Concrete -> Water "
        f"({ENERGY_MIN_MEV:.0f}-{ENERGY_MAX_MEV:.0f} MeV uniform source)"
    )
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150)
    plt.close(fig)
    print(f"Spectrum plot written to: {PLOT_PATH}")
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
