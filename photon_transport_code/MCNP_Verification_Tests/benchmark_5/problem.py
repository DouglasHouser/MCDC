"""
Benchmark 5: Cobalt-60 Air-Over-Ground Problem.

Reference: "MCNP: Photon Benchmark Problems" (MCNP_validation_test.pdf, section VI).
A uniform Co-60 fallout source is spread on the ground; air fills the space above and
soil the space below. The published MCNP result is the dose buildup factor

    B = 1.190 +/- 0.005   (historical range across studies: 1.15 - 1.38)

measured at a point 3 ft (91.44 cm) above the ground, together with the angular
kerma-rate distribution there (Fig. 5.5).

------------------------------------------------------------------------------------
WHY THIS IS AN ANALOG RE-FORMULATION (not a literal port of MCNP Table A.6)
------------------------------------------------------------------------------------
The reference MCNP deck uses an F5 point detector, a DXTRAN sphere, cell importances /
weight windows, and a cosine-binned F1 current tally. MCDC supports none of these: it
does analog transport with surface/cell/mesh tallies (flux, net-current, energy-deposit)
that can be binned in energy and polar cosine (mu). So this benchmark is a physically
faithful *analog* model of the same problem:

  * air / soil half-spaces split by the z = 0 plane (the air/ground interface),
  * soil subdivision planes at z = -6, -12, -18 cm (one MFP each for 1.33 MeV in soil),
  * a 1-km vacuum bounding sphere (~10 MFP of air for Co-60),
  * a planar Co-60 disk (here, square patch) source on the ground, isotropic in 4pi,
  * a finite detector sphere at z = 91.44 cm.

The dose buildup factor is recovered from the energy-resolved fluence in the detector
cell (compare.py), and the angular distribution from the mu-binned current on the
detector sphere surface.

------------------------------------------------------------------------------------
COMPUTE SIZING
------------------------------------------------------------------------------------
Analog MC of a 1-km geometry with a small detector converges slowly. The committed
configuration is a fast SMOKE TEST (correctness check, B accurate only to ~10-20%).
For a statistically converged run on a cluster, use the values in the CLUSTER CONFIG
comment block near the settings below (and run via run_problem5.slurm).
"""

import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Path setup — works whether run as a script or exec()'d inline
# ---------------------------------------------------------------------------
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
except NameError:
    _HERE = os.getcwd()
    _ROOT = _HERE

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import mcdc

# =============================================================================
# Materials — MCNP weight fractions -> MCDC number densities (atoms/barn-cm)
#
#   n_i = rho[g/cm^3] * w_i * (N_A * 1e-24) / A_i,   N_A * 1e-24 = 0.602214
#
# Compositions taken from MCNP Table A.6 (M1 = soil, M2 = air) and section VI.
# =============================================================================
_NA_BARN = 0.602214  # Avogadro's number * 1e-24 (barn conversion)

# Atomic masses (g/mol) for the constituent elements.
_A = {
    7: 14.007,   # N
    8: 15.999,   # O
    18: 39.948,  # Ar
    11: 22.990,  # Na
    12: 24.305,  # Mg
    13: 26.982,  # Al
    14: 28.085,  # Si
    16: 32.060,  # S
    20: 40.078,  # Ca
    26: 55.845,  # Fe
    28: 58.693,  # Ni
}


def _number_densities(rho, weight_fractions):
    """Convert {Z: weight_fraction} at bulk density rho (g/cm^3) to number densities.

    Returns (elements, densities) with densities in atoms/barn-cm, suitable for
    ``mcdc.PhotonMaterial(elements=..., densities=...)``.
    """
    elements = list(weight_fractions.keys())
    densities = [rho * weight_fractions[z] * _NA_BARN / _A[z] for z in elements]
    return elements, densities


# Air: rho = 0.00129 g/cm^3; N 0.7818, O 0.2097, Ar 0.0085  (sums to 1.0000)
_air_elems, _air_dens = _number_densities(
    0.00129, {7: 0.7818, 8: 0.2097, 18: 0.0085}
)
air = mcdc.PhotonMaterial(elements=_air_elems, densities=_air_dens, name="air")

# NTS soil: rho = 1.13 g/cm^3
#   O 0.34, Na 0.01, Mg 0.10, Al 0.03, Si 0.18, S 0.03, Ca 0.01, Fe 0.29, Ni 0.01
_soil_elems, _soil_dens = _number_densities(
    1.13,
    {8: 0.34, 11: 0.01, 12: 0.10, 13: 0.03, 14: 0.18, 16: 0.03, 20: 0.01, 26: 0.29, 28: 0.01},
)
soil = mcdc.PhotonMaterial(elements=_soil_elems, densities=_soil_dens, name="soil")

# =============================================================================
# Geometry parameters
# =============================================================================
DETECTOR_HEIGHT = 91.44  # cm — 3 ft above the ground
R_BOUND = 1.0e5          # cm — 1 km bounding sphere (~10 MFP of air for Co-60)

# --- SMOKE TEST values (committed) -----------------------------------------
# The detector is enlarged (MCNP used 0.5 cm) and the source patch is shrunk to a
# near-field 40 m x 40 m square so that a modest history count still delivers many
# detector crossings. This compressed geometry DISTORTS the scattered/direct balance
# (e.g. it over-weights near-field soil backscatter), so the smoke buildup factor is
# NOT quantitatively comparable to the plane-source value 1.19 (observed B ~ 4). The
# smoke run only proves the transport, materials, and tally wiring are correct; use
# the cluster config for the quantitative 1.19 comparison.
R_DET = 50.0             # cm — detector sphere radius (must stay < DETECTOR_HEIGHT)
R_SRC = 2.0e3            # cm — half-width of the square source patch (near field)
# --- CLUSTER CONFIG (uncomment for a converged run; see run_problem5.slurm) -
# R_DET = 5.0            # cm — closer to the MCNP 0.5 cm point-like detector
# R_SRC = 1.0e5          # cm — full 1-km source disk (true plane-source limit)

# =============================================================================
# Surfaces
# =============================================================================
z0 = mcdc.Surface.PlaneZ(z=0.0)      # air/ground interface
z6 = mcdc.Surface.PlaneZ(z=-6.0)     # soil layer boundaries (1 MFP each in soil)
z12 = mcdc.Surface.PlaneZ(z=-12.0)
z18 = mcdc.Surface.PlaneZ(z=-18.0)

bound = mcdc.Surface.Sphere(
    center=[0.0, 0.0, 0.0], radius=R_BOUND, boundary_condition="vacuum"
)
detector = mcdc.Surface.Sphere(
    center=[0.0, 0.0, DETECTOR_HEIGHT], radius=R_DET
)

# =============================================================================
# Cells
# =============================================================================
# Air: above the ground, inside the boundary, outside the detector sphere.
mcdc.Cell(region=+z0 & -bound & +detector, fill=air)
# Detector: the small air sphere 3 ft above the ground.
detector_cell = mcdc.Cell(region=-detector, fill=air)

# Soil: below the ground, subdivided by the -6/-12/-18 cm planes (same material).
mcdc.Cell(region=-z0 & +z6 & -bound, fill=soil)
mcdc.Cell(region=-z6 & +z12 & -bound, fill=soil)
mcdc.Cell(region=-z12 & +z18 & -bound, fill=soil)
mcdc.Cell(region=-z18 & -bound, fill=soil)

# =============================================================================
# Source — Co-60 planar patch on the ground (z = 0), isotropic in 4pi.
#   Two gamma lines at 1.17 and 1.33 MeV, equal probability. Energy in MeV.
# =============================================================================
mcdc.Source(
    x=[-R_SRC, R_SRC],
    y=[-R_SRC, R_SRC],
    z=[0.0, 0.0],
    isotropic=True,
    energy=[np.array([1.17, 1.33]), np.array([0.5, 0.5])],
    particle_type="photon",
)

# =============================================================================
# Tally — a single surface tally on the detector sphere, binned in BOTH energy and
# polar cosine (mu), giving flux[mu, energy]. compare.py derives:
#   * dose buildup factor  — sum over mu, split uncollided (source-line bins) vs total,
#   * angular kerma-rate    — sum over energy weighted by the air kerma response,
#                             reported vs cos(theta) = -mu.
#
# WHY ONE SURFACE TALLY (not a cell flux + a surface current): MCDC currently stores a
# surface/cell's tally-ID list using the *global* tally ID but indexes the per-type
# child array at run time (numba_objects_generator.py:587-591 vs
# geometry/interface.py:451, simulation.py:329). Mixing a tracklength (cell) tally with
# a surface tally therefore indexes out of bounds. Keeping to a single surface tally
# stays on the exercised code path. mu = u_z; polar_reference is intentionally NOT
# passed (tally.py:159 mishandles it; the direction filter supports only +z).
ENERGY_EDGES = np.array(
    [
        0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.80, 1.00, 1.10,
        1.16, 1.18,   # -> bin [1.16, 1.18] captures the 1.17 MeV line (uncollided)
        1.30, 1.34,   # -> bin [1.30, 1.34] captures the 1.33 MeV line (uncollided)
    ]
)
MU_EDGES = np.linspace(-1.0, 1.0, 21)  # 20 cosine bins, matches Fig. 5.5 binning
mcdc.Tally(
    surface=detector,
    scores=["flux"],
    energy=ENERGY_EDGES,
    mu=MU_EDGES,
    name="detector",
)

# =============================================================================
# Settings — SMOKE TEST
# =============================================================================
mcdc.settings.photon_transport = True
mcdc.settings.N_particle = 100_000_000
mcdc.settings.N_batch = 10
mcdc.settings.rng_seed = 12345
mcdc.settings.output_name = "benchmark_5"
mcdc.settings.use_progress_bar = False
# --- CLUSTER CONFIG (uncomment for a converged run) ------------------------
# mcdc.settings.N_particle = 1_000_000_000   # ~1e9 for B to <1-2% with R_DET=5
# mcdc.settings.N_batch = 100

# =============================================================================
# Run — only when invoked directly as a script, not when exec()'d inline
# =============================================================================
if sys.argv[0].endswith(".py"):
    try:
        os.chdir(_HERE)
    except Exception:
        pass
    mcdc.run()
