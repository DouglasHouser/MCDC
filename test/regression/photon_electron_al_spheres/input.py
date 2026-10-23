"""1 MeV photon point source in aluminium, with photon-electron coupling.

A monoenergetic isotropic 1 MeV photon point source sits at the origin of an
aluminium medium. A 10 cm sphere is divided into five 2 cm concentric regions,
each carrying photon and electron track-length flux tallies and an
energy-deposition tally. Photon and electron transport are both active, so
Compton, photoelectric, and Auger electrons are transported, and their
bremsstrahlung photons in turn.
"""

import os

import mcdc

# Set the XS library directory
os.environ["MCDC_LIB"] = "../mcdc-regression_test_data/"

# Create MC/DC simulation
simulation = mcdc.Simulation("1 MeV coupled photon-electron source in aluminium")

# ======================================================================================
# Set model
# ======================================================================================

# Aluminium at 2.70 g/cm^3:
#   n = 2.70 g/cm^3 * 6.022e23 /mol / 26.98 g/mol * 1e-24 = 0.06026 atoms/barn-cm
aluminium = mcdc.Material(element_composition={"Al": 0.06026}, name="aluminium")

RADII = [2.0, 4.0, 6.0, 8.0, 10.0]

spheres = []
for radius in RADII:
    boundary_condition = "vacuum" if radius == RADII[-1] else "none"
    spheres.append(
        mcdc.Surface.Sphere(
            center=[0.0, 0.0, 0.0],
            radius=radius,
            boundary_condition=boundary_condition,
        )
    )

cells = [mcdc.Cell(region=-spheres[0], fill=aluminium)]
for index in range(1, len(spheres)):
    cells.append(
        mcdc.Cell(region=+spheres[index - 1] & -spheres[index], fill=aluminium)
    )

simulation.set_model(cells)

# ======================================================================================
# Set source
# ======================================================================================

source = mcdc.Source(
    x=0.0,
    y=0.0,
    z=0.0,
    energy=1.0e6,
    isotropic=True,
    particle_type="photon",
)
simulation.set_sources([source])

# ======================================================================================
# Set tallies, settings, and run mcdc
# ======================================================================================

tallies = []
for index, cell in enumerate(cells):
    for particle_type in ["photon", "electron"]:
        tallies.append(
            mcdc.Tally(
                cell=cell,
                scores=["flux"],
                particle_type=particle_type,
                name=f"region_{index}_{particle_type}_flux",
            )
        )
    tallies.append(
        mcdc.Tally(cell=cell, scores=["energy_deposition"], name=f"region_{index}_edep")
    )
simulation.set_tallies(tallies)

simulation.settings.N_particle = 2
simulation.settings.N_batch = 2
simulation.settings.rng_seed = 42
simulation.settings.photon_transport.active = True
simulation.settings.electron_transport.active = True

simulation.run()
