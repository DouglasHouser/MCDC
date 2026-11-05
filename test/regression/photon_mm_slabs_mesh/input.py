"""Depth profile across a lead-water-concrete-air slab stack.

One fine z mesh spans the whole stack, so a single tally resolves the
flux across every material boundary rather than giving one number per
slab. Four materials with very different Z exercise the per-element
density weighting in macro_xs.

Migrated from ``photon_transport_code/MCNP_Verification_Tests/Complex_M&G/multi_material_slabs_mesh_tally.py``.
The physics is unchanged; the API is not. Energies are eV rather than MeV,
times are seconds rather than nanoseconds, materials are element compositions
rather than ``PhotonMaterial``, and settings hang off the ``Simulation``.
"""

import numpy as np
import os

import mcdc

# Set the XS library directory
os.environ["MCDC_LIB"] = "../mcdc-regression_test_data/"

simulation = mcdc.Simulation("Slab stack depth profile")

# ======================================================================================
# Material compositions
# ======================================================================================
# The MCNP m cards give each material as a mass density plus weight fractions.
# MCNP renormalizes fractions that do not sum to one (this concrete's sum to
# 0.986) and converts with its own atomic weights. To give both codes identical
# materials, each element density here is MCNP's total atom density
# (atoms/b-cm, print table 60 of the reference output) split in proportion to
# w_i / A_i. The comments give the MCNP cell mass densities.

MOLAR_MASS = {
    "H": 1.008,
    "N": 14.007,
    "O": 15.999,
    "Na": 22.990,
    "Mg": 24.305,
    "Al": 26.982,
    "Si": 28.085,
    "Ar": 39.948,
    "Ca": 40.078,
    "Fe": 55.845,
    "Pb": 207.200,
}


def composition(atom_density, weight_fractions):
    """Split a total atom density over elements in proportion to w_i / A_i."""
    moles = {
        symbol: fraction / MOLAR_MASS[symbol]
        for symbol, fraction in weight_fractions.items()
    }
    total = sum(moles.values())
    return {symbol: atom_density * mole / total for symbol, mole in moles.items()}


lead = mcdc.Material(  # 11.34 g/cm^3
    number_density=composition(3.29558e-02, {"Pb": 1.0}), name="lead"
)
water = mcdc.Material(  # 1.0 g/cm^3
    number_density=composition(1.00280e-01, {"H": 0.111898, "O": 0.888102}),
    name="water",
)
concrete = mcdc.Material(  # 2.3 g/cm^3
    number_density=composition(
        8.19993e-02,
        {
            "O": 0.529107,
            "Na": 0.016,
            "Mg": 0.002,
            "Al": 0.033872,
            "Si": 0.337021,
            "Ca": 0.044,
            "Fe": 0.014,
            "H": 0.010,
        },
    ),
    name="concrete",
)
air = mcdc.Material(  # 0.00129 g/cm^3
    number_density=composition(5.37076e-05, {"N": 0.7818, "O": 0.2097, "Ar": 0.0085}),
    name="air",
)

# ======================================================================================
# Set model
# ======================================================================================
# Lead, water, concrete and air slabs, with a thin vacuum-bounded air backing
# behind the source face.

SLABS = [
    (lead, 0.0, 5.0),
    (water, 5.0, 25.0),
    (concrete, 25.0, 55.0),
    (air, 55.0, 200.0),
]
Z_BACK_BOUNDARY = -1.0
Z_SOURCE = 1.0e-6

materials = [material for material, _, _ in SLABS]
z_backs = [z_back for _, _, z_back in SLABS]

z_back_bound = mcdc.Surface.PlaneZ(z=Z_BACK_BOUNDARY, boundary_condition="vacuum")
z_planes = [mcdc.Surface.PlaneZ(z=SLABS[0][1])]
for index, z_back in enumerate(z_backs):
    z_planes.append(
        mcdc.Surface.PlaneZ(
            z=z_back,
            boundary_condition="vacuum" if index == len(z_backs) - 1 else "none",
        )
    )

backing = mcdc.Cell(region=+z_back_bound & -z_planes[0], fill=air, name="backing_gap")
cells = [
    mcdc.Cell(region=+z_planes[index] & -z_planes[index + 1], fill=materials[index])
    for index in range(len(SLABS))
]

simulation.set_model([backing] + cells)

# ======================================================================================
# Set source
# ======================================================================================

source = mcdc.Source(
    x=0.0,
    y=0.0,
    z=Z_SOURCE,
    energy=1.0e6,
    isotropic=True,
    particle_type="photon",
)
simulation.set_sources([source])

# ======================================================================================
# Set tallies, settings, and run mcdc
# ======================================================================================

DZ = 1.0
N_MESH_Z = int(round((z_backs[-1] - Z_BACK_BOUNDARY) / DZ))
depth_mesh = mcdc.MeshUniform(name="depth_mesh", z=(Z_BACK_BOUNDARY, DZ, N_MESH_Z))

simulation.set_tallies(
    [
        mcdc.Tally(
            mesh=depth_mesh,
            scores=["flux"],
            name="depth_profile",
            particle_type="photon",
        )
    ]
)

simulation.settings.N_particle = 1000
simulation.settings.N_batch = 2
simulation.settings.rng_seed = 42

simulation.run()
