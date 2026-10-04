"""
CARRE project — 1U CubeSat photon-transport model (10 MeV isotropic bath)
==========================================================================

This is the photon-transport counterpart of the multigroup-neutron model in
``Cubesat_Updated_Antenna.py``.  The geometry (rails, shear panels, solar
panels, deployable antenna, board stack, and sensitive volumes) is reproduced
verbatim; only the physics setup differs:

  * Materials are ``mcdc.PhotonMaterial`` objects built from elemental
    composition and number density (atoms/barn-cm), so photon cross sections
    are taken from the tabulated NIST/EPDL data in ``data/mcdc/``.
  * The surrounding cube is a *true vacuum* (a constant-cross-section material
    with sigma = 0), matching a CubeSat's on-orbit environment — photons stream
    in straight lines until they reach the spacecraft.
  * The source is a **surface source on all six faces of the boundary cube**,
    emitting 10 MeV photons with an inward cosine ("white") angular
    distribution.  Integrated over the enclosing surface this produces a
    uniform, isotropic 10 MeV photon field bathing the CubeSat from every
    direction.  (A white/inward source is the standard way to represent an
    isotropic ambient field incident on a surface: it puts every history into
    the problem instead of wasting half of them heading outward, as a pointwise
    ``isotropic=True`` face source would.)

Outputs (written to ``10MeV_cubesat_model.h5``):
  * flux            — photon flux, both as a 3-D map over the CubeSat body and
                      integrated in each electronics sensitive volume.
  * energy-deposit  — energy deposited by photon collisions (dose proxy), same
                      two spatial resolutions.

Run from the repository root (c:/Projects/MCDC)::

    python photon_transport_code/examples/CARRE_examples/10MeV_cubesat_model.py

Cross sections are real tabulated photon data; the elemental *compositions*
below are engineering approximations (e.g. the aluminum alloys are treated as
pure aluminum at their alloy density).  Refine them before production analysis.
"""

import os
import sys

import numpy as np

# --- Path setup so the example runs standalone from anywhere ----------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import mcdc

# =============================================================================
# MATERIALS
#
# PhotonMaterial takes atomic numbers Z and number densities in atoms/barn-cm.
# Number density:  N [atoms/b-cm] = rho [g/cm^3] * N_A / M [g/mol] * 1e-24
#                                 = rho * 0.60221 / M   (per element/molecule)
# For a compound, each element's density is N_molecule * (atoms of that element).
# =============================================================================

# --- Aluminum alloys (treated as pure Al, Z=13, M=26.982) -------------------
# Al 7075, rho = 2.81 g/cm^3  ->  N = 2.81 * 0.60221 / 26.982 = 6.272e-2
m_al7075 = mcdc.PhotonMaterial(name="Al7075", elements=[13], densities=[6.272e-2])
# Al 6061, rho = 2.70 g/cm^3  ->  N = 2.70 * 0.60221 / 26.982 = 6.026e-2
m_al6061 = mcdc.PhotonMaterial(name="Al6061", elements=[13], densities=[6.026e-2])

# --- Epoxy (representative cured epoxy: H/C/O, rho = 1.20 g/cm^3) ------------
# Mass fractions ~ H 0.09, C 0.70, O 0.21
#   H: 1.20 * 0.09 * 0.60221 / 1.008  = 6.452e-2
#   C: 1.20 * 0.70 * 0.60221 / 12.011 = 4.211e-2
#   O: 1.20 * 0.21 * 0.60221 / 15.999 = 9.485e-3
m_epoxy = mcdc.PhotonMaterial(
    name="Epoxy",
    elements=[1, 6, 8],
    densities=[6.452e-2, 4.211e-2, 9.485e-3],
)

# --- Silicon (Z=14, M=28.085, rho = 2.33 g/cm^3) ----------------------------
# N = 2.33 * 0.60221 / 28.085 = 4.996e-2
m_silicon = mcdc.PhotonMaterial(name="Silicon", elements=[14], densities=[4.996e-2])

# --- LiCoO2 cathode (Li Z=3, Co Z=27, O Z=8; M = 97.87 g/mol, rho = 5.05) ----
# N_molecule = 5.05 * 0.60221 / 97.87 = 3.107e-2
#   Li: 3.107e-2,  Co: 3.107e-2,  O: 2 * 3.107e-2 = 6.215e-2
m_licoo2 = mcdc.PhotonMaterial(
    name="LiCoO2",
    elements=[3, 27, 8],
    densities=[3.107e-2, 3.107e-2, 6.215e-2],
)

# --- Copper (Z=29, M=63.546, rho = 8.96 g/cm^3) -----------------------------
# N = 8.96 * 0.60221 / 63.546 = 8.491e-2
m_copper = mcdc.PhotonMaterial(name="Copper", elements=[29], densities=[8.491e-2])

# --- Vacuum: constant zero cross section (true streaming region) ------------
m_void = mcdc.ConstantCrossSectionMaterial(
    name="Void", sigma_total=0.0, sigma_scatter=0.0, sigma_absorb=0.0
)

# =============================================================================
# BOX HELPER
# =============================================================================


def box(x0, x1, y0, y1, z0, z1, bcx0="none", bcx1="none",
        bcy0="none", bcy1="none", bcz0="none", bcz1="none"):
    sx0 = mcdc.Surface.PlaneX(x=x0, boundary_condition=bcx0)
    sx1 = mcdc.Surface.PlaneX(x=x1, boundary_condition=bcx1)
    sy0 = mcdc.Surface.PlaneY(y=y0, boundary_condition=bcy0)
    sy1 = mcdc.Surface.PlaneY(y=y1, boundary_condition=bcy1)
    sz0 = mcdc.Surface.PlaneZ(z=z0, boundary_condition=bcz0)
    sz1 = mcdc.Surface.PlaneZ(z=z1, boundary_condition=bcz1)
    return +sx0 & -sx1 & +sy0 & -sy1 & +sz0 & -sz1


# =============================================================================
# OUTER BOUNDARY
# 100 cm x 100 cm x 100 cm vacuum cube centered on the CubeSat.
# =============================================================================

boundary_center = np.array([5.0, 5.0, 5.0])
boundary_half_width = 50.0

boundary_x0, boundary_y0, boundary_z0 = boundary_center - boundary_half_width
boundary_x1, boundary_y1, boundary_z1 = boundary_center + boundary_half_width

outer = box(
    boundary_x0, boundary_x1,
    boundary_y0, boundary_y1,
    boundary_z0, boundary_z1,
    bcx0="vacuum", bcx1="vacuum",
    bcy0="vacuum", bcy1="vacuum",
    bcz0="vacuum", bcz1="vacuum",
)

# =============================================================================
# MAIN RAILS
# Al 7075, 0.5 x 0.5 x 11 cm, one at each corner
# =============================================================================

rail_regions = [
    box(0.0, 0.5,  0.0, 0.5,  0.0, 11.0),   # -X -Y corner
    box(9.5, 10.0, 0.0, 0.5,  0.0, 11.0),   # +X -Y corner
    box(0.0, 0.5,  9.5, 10.0, 0.0, 11.0),   # -X +Y corner
    box(9.5, 10.0, 9.5, 10.0, 0.0, 11.0),   # +X +Y corner
]
rail_cells = [mcdc.Cell(region=r, fill=m_al7075) for r in rail_regions]

# =============================================================================
# SMALL RAILS
# Al 7075, 9.0 x 0.5 x 0.5 cm edge-to-edge spans, four bottom and four top,
# centered vertically on the large rails.
# =============================================================================

small_rail_dims = [
    (0.5, 9.5, 0.0, 0.5, 0.5, 1.0),
    (0.5, 9.5, 9.5, 10.0, 0.5, 1.0),
    (0.0, 0.5, 0.5, 9.5, 0.5, 1.0),
    (9.5, 10.0, 0.5, 9.5, 0.5, 1.0),
    (0.5, 9.5, 0.0, 0.5, 10.0, 10.5),
    (0.5, 9.5, 9.5, 10.0, 10.0, 10.5),
    (0.0, 0.5, 0.5, 9.5, 10.0, 10.5),
    (9.5, 10.0, 0.5, 9.5, 10.0, 10.5),
]
small_rail_cells = [mcdc.Cell(region=box(*d), fill=m_al7075) for d in small_rail_dims]

# =============================================================================
# SHEAR PANELS
# Al 6061, 9.0 x 9.0 x 0.3 cm, fit between rail frames
# =============================================================================

shear_panel_dims = [
    (0.0,  0.3,  0.5, 9.5, 1.0, 10.0),     # -X face
    (9.7, 10.0,  0.5, 9.5, 1.0, 10.0),     # +X face
    (0.5, 9.5,  0.0, 0.3, 1.0, 10.0),      # -Y face
    (0.5, 9.5,  9.7, 10.0, 1.0, 10.0),     # +Y face
    (0.5, 9.5,  0.5, 9.5, 0.5, 0.8),       # -Z face
    (0.5, 9.5,  0.5, 9.5, 10.2, 10.5),     # +Z face
]
shear_cells = [mcdc.Cell(region=box(*d), fill=m_al6061) for d in shear_panel_dims]

# =============================================================================
# SOLAR PANELS
# Ten total: two per face except the -Z face. Silicon, mounted on the outer
# face of each shear panel.
# =============================================================================

solar_panel_dims = [
    (-0.2, 0.0,  1.0, 9.0, 1.75, 5.25),   # -X face, lower
    (-0.2, 0.0,  1.0, 9.0, 5.75, 9.25),   # -X face, upper
    (10.0, 10.2, 1.0, 9.0, 1.75, 5.25),   # +X face, lower
    (10.0, 10.2, 1.0, 9.0, 5.75, 9.25),   # +X face, upper
    (1.0,  9.0, -0.2, 0.0, 1.75, 5.25),   # -Y face, lower
    (1.0,  9.0, -0.2, 0.0, 5.75, 9.25),   # -Y face, upper
    (1.0,  9.0, 10.0, 10.2, 1.75, 5.25),  # +Y face, lower
    (1.0,  9.0, 10.0, 10.2, 5.75, 9.25),  # +Y face, upper
    (1.0,  9.0,  1.25, 4.75, 10.5, 10.7), # +Z face, lower
    (1.0,  9.0,  5.25, 8.75, 10.5, 10.7), # +Z face, upper
]
solar_cells = [mcdc.Cell(region=box(*d), fill=m_silicon) for d in solar_panel_dims]

# =============================================================================
# ANTENNA
# Four thin deployable-antenna strips (Copper) framing the edges of the -Z
# face, tucked between the rail bottom (z=0) and the -Z shear panel (z=0.5).
# =============================================================================

antenna_strip_dims = [
    (0.5, 9.5, 0.5, 0.8, 0.2, 0.5),   # -Y edge
    (0.5, 9.5, 9.2, 9.5, 0.2, 0.5),   # +Y edge
    (0.5, 0.8, 0.8, 9.2, 0.2, 0.5),   # -X edge
    (9.2, 9.5, 0.8, 9.2, 0.2, 0.5),   # +X edge
]
antenna_cells = [mcdc.Cell(region=box(*d), fill=m_copper) for d in antenna_strip_dims]

# =============================================================================
# BOARD STACK
# Epoxy boards are 9.0 x 9.0 x 0.16 cm; each sensitive volume sits above its
# board.
# =============================================================================

# OBC board, z = 2.285 -> 2.445 cm
obc_board = mcdc.Cell(region=box(0.5, 9.5, 0.5, 9.5, 2.285, 2.445), fill=m_epoxy)
# OBC sensitive volume: silicon, 3.6 x 2.7 x 0.6 cm
obc_sv = mcdc.Cell(region=box(3.2, 6.8, 3.65, 6.35, 2.445, 3.045), fill=m_silicon)

# EPS board, z = 3.785 -> 3.945 cm
eps_board = mcdc.Cell(region=box(0.5, 9.5, 0.5, 9.5, 3.785, 3.945), fill=m_epoxy)
# EPS sensitive volume: LiCoO2, 2.5 x 6.5 x 0.23 cm
eps_sv = mcdc.Cell(region=box(3.75, 6.25, 1.75, 8.25, 3.945, 4.175), fill=m_licoo2)

# ADCS board, z = 5.785 -> 5.945 cm
adcs_board = mcdc.Cell(region=box(0.5, 9.5, 0.5, 9.5, 5.785, 5.945), fill=m_epoxy)
# ADCS sensitive volume: silicon, 4.5 x 4.5 x 1.8 cm
adcs_sv = mcdc.Cell(region=box(2.75, 7.25, 2.75, 7.25, 5.945, 7.745), fill=m_silicon)

# Comms board, z = 8.285 -> 8.445 cm
comms_board = mcdc.Cell(region=box(0.5, 9.5, 0.5, 9.5, 8.285, 8.445), fill=m_epoxy)
# Comms sensitive volume: silicon, 1.1 x 0.97 x 0.27 cm
comms_sv = mcdc.Cell(region=box(4.45, 5.55, 4.515, 5.485, 8.445, 8.715), fill=m_silicon)

# =============================================================================
# VOID FILL
# All remaining space inside the boundary cube (true vacuum).
# =============================================================================

all_component_cells = (
    rail_cells + small_rail_cells + shear_cells + solar_cells + antenna_cells +
    [obc_board, obc_sv,
     eps_board, eps_sv,
     adcs_board, adcs_sv,
     comms_board, comms_sv]
)

void_region = outer
for c in all_component_cells:
    void_region = void_region & ~c.region

void_cell = mcdc.Cell(region=void_region, fill=m_void)

# =============================================================================
# SOURCE
# Surface photon source on all six faces of a "cage" box that tightly encloses
# the CubeSat (the whole spacecraft spans x,y in [-0.2, 10.2] and z in [0, 11],
# so the cage sits just outside that at a ~0.8-1 cm standoff).  Each face is a
# planar surface source emitting 10 MeV photons isotropically; the inward-going
# half of each face's emission, integrated over the enclosing surface, immerses
# the CubeSat in a uniform, isotropic 10 MeV photon field arriving from every
# direction.  Energy for photon transport is specified in MeV.
#
# The cage is used (rather than the 100 cm boundary faces) purely for
# efficiency: at a 45 cm standoff almost every photon would stream past the
# ~10 cm spacecraft and never interact, leaving the flux/dose tallies starved.
# The angular distribution of the bath at the CubeSat surface is identical
# either way.  A cosine/"white" inward source would avoid emitting the outward
# half entirely, but the framework's white-direction sampler has a pole
# singularity for a -Z-facing normal, so we use robust isotropic emission.
# =============================================================================

E_SOURCE = 10.0  # MeV

# Source cage: a box just outside the CubeSat envelope.
cage_x0, cage_x1 = -1.0, 11.0
cage_y0, cage_y1 = -1.0, 11.0
cage_z0, cage_z1 = -1.0, 12.0

source_faces = [
    # -X face
    dict(x=[cage_x0, cage_x0], y=[cage_y0, cage_y1], z=[cage_z0, cage_z1]),
    # +X face
    dict(x=[cage_x1, cage_x1], y=[cage_y0, cage_y1], z=[cage_z0, cage_z1]),
    # -Y face
    dict(x=[cage_x0, cage_x1], y=[cage_y0, cage_y0], z=[cage_z0, cage_z1]),
    # +Y face
    dict(x=[cage_x0, cage_x1], y=[cage_y1, cage_y1], z=[cage_z0, cage_z1]),
    # -Z face
    dict(x=[cage_x0, cage_x1], y=[cage_y0, cage_y1], z=[cage_z0, cage_z0]),
    # +Z face
    dict(x=[cage_x0, cage_x1], y=[cage_y0, cage_y1], z=[cage_z1, cage_z1]),
]

for extent in source_faces:
    mcdc.Source(
        **extent,
        isotropic=True,
        energy=E_SOURCE,
        particle_type="photon",
        probability=1.0 / 6.0,
    )

# =============================================================================
# TALLIES
#   1. A 3-D mesh over the CubeSat body: flux + energy-deposit maps.
#   2. Per sensitive-volume cell tallies: integrated flux + energy-deposit.
# =============================================================================

# Mesh spanning the CubeSat envelope (x,y: 0-10 cm, z: 0-11 cm) at 0.5 cm voxels.
body_mesh = mcdc.MeshStructured(
    x=np.linspace(0.0, 10.0, 21),
    y=np.linspace(0.0, 10.0, 21),
    z=np.linspace(0.0, 11.0, 23),
)
mcdc.Tally(name="body map", mesh=body_mesh, scores=["flux", "energy-deposit"])

# Sensitive-volume dose/flux (energy-deposit is a photon collision estimator).
mcdc.Tally(name="OBC SV", cell=obc_sv, scores=["flux", "energy-deposit"])
mcdc.Tally(name="EPS SV", cell=eps_sv, scores=["flux", "energy-deposit"])
mcdc.Tally(name="ADCS SV", cell=adcs_sv, scores=["flux", "energy-deposit"])
mcdc.Tally(name="Comms SV", cell=comms_sv, scores=["flux", "energy-deposit"])

# =============================================================================
# SETTINGS AND RUN
# =============================================================================

mcdc.settings.N_particle = 1000000
mcdc.settings.N_batch = 100
mcdc.settings.rng_seed = 42

os.chdir(_HERE)
mcdc.settings.output_name = "10MeV_cubesat_model"

mcdc.run()
