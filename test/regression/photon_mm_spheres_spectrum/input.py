"""Energy spectrum in concentric multi-material spheres.

A 1-10 MeV uniform source spectrum, tallied into 40 logarithmic energy
bins per region. The energy filter is what makes this deck a test of the
scattered spectrum rather than just the total flux, so it is sensitive
to the Klein-Nishina sampling in a way the integral decks are not.

Migrated from ``photon_transport_code/MCNP_Verification_Tests/Complex_M&G/multi_material_spheres_1to10mev_spectrum.py``.
The physics is unchanged; the API is not. Energies are eV rather than MeV,
times are seconds rather than nanoseconds, materials are element compositions
rather than ``PhotonMaterial``, and settings hang off the ``Simulation``.
"""

import numpy as np
import os

import mcdc

# Set the XS library directory
os.environ["MCDC_LIB"] = "../mcdc-regression_test_data/"

simulation = mcdc.Simulation("Multi-material sphere spectrum")

# ======================================================================================
# Material compositions
# ======================================================================================
# The same four materials as the photon_mm_slabs_* decks, with the same atom
# densities. MCNP renormalizes weight fractions that do not sum to one (this
# concrete's sum to 0.986) and converts with its own atomic weights, so each
# element density is MCNP's total atom density (atoms/b-cm, print table 60 of
# the slab-stack reference outputs) split in proportion to w_i / A_i. The
# comments give the MCNP mass densities.

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

RADII = [5.0, 10.0, 15.0, 20.0, 25.0]
SHELL_MATERIALS = [lead, water, concrete, air, concrete]

spheres = [
    mcdc.Surface.Sphere(
        center=[0.0, 0.0, 0.0],
        radius=radius,
        boundary_condition="vacuum" if index == len(RADII) - 1 else "none",
    )
    for index, radius in enumerate(RADII)
]

cells = [mcdc.Cell(region=-spheres[0], fill=SHELL_MATERIALS[0])]
for index in range(1, len(spheres)):
    cells.append(
        mcdc.Cell(
            region=+spheres[index - 1] & -spheres[index],
            fill=SHELL_MATERIALS[index],
        )
    )

simulation.set_model(cells)

# ======================================================================================
# Set source
# ======================================================================================

ENERGY_MIN = 1.0e6
ENERGY_MAX = 1.0e7

source = mcdc.Source(
    x=0.0,
    y=0.0,
    z=0.0,
    energy=np.array([[ENERGY_MIN, ENERGY_MAX], [1.0, 1.0]]),
    isotropic=True,
    particle_type="photon",
)
simulation.set_sources([source])

# ======================================================================================
# Set tallies, settings, and run mcdc
# ======================================================================================

ENERGY_EDGES = np.logspace(np.log10(1.0e4), np.log10(ENERGY_MAX), 41)

simulation.set_tallies(
    [
        mcdc.Tally(
            cell=cell,
            scores=["flux"],
            energy=ENERGY_EDGES,
            name=f"region_{index}",
            particle_type="photon",
        )
        for index, cell in enumerate(cells)
    ]
)

simulation.settings.N_particle = 1000
simulation.settings.N_batch = 2
simulation.settings.rng_seed = 42

simulation.run()
