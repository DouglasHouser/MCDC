import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import mcdc

# =============================================================================
# Materials
# =============================================================================
# Aluminum at standard density 2.7 g/cm3
# Atomic density: (2.7 g/cm3 * 6.022e23 atoms/mol) / 26.982 g/mol = 0.06026 atoms/barn-cm
aluminum = mcdc.PhotonMaterial(
    elements=[13],
    densities=[0.06026],
    name="aluminum",
)

# =============================================================================
# Surfaces
# =============================================================================
s_left = mcdc.Surface.PlaneX(x=0.0, boundary_condition="vacuum")
s_right = mcdc.Surface.PlaneX(x=25.0, boundary_condition="vacuum")

# =============================================================================
# Cells
# =============================================================================
slab = mcdc.Cell(region=+s_left & -s_right, fill=aluminum)

# =============================================================================
# Source
# =============================================================================
# Mono-energetic 1 MeV photon beam entering from the left face in the +x direction.
# At 1 MeV, Compton scattering dominates in aluminum (photoelectric < 0.1 MeV,
# pair production > 1.022 MeV), giving a mean free path of ~6 cm (~4 mfp in 25 cm).
mcdc.Source(
    position=[0.0, 0.0, 0.0],
    direction=[1.0, 0.0, 0.0],
    energy=1.0,
    particle_type="photon",
)

# =============================================================================
# Tallies
# =============================================================================
# Photon flux as a function of depth: 50 equal bins of 0.5 cm each, 0 to 25 cm
mesh = mcdc.MeshStructured(x=np.linspace(0.0, 25.0, 51))
mcdc.Tally(mesh=mesh, scores=["flux"])

# =============================================================================
# Settings
# =============================================================================
mcdc.settings.N_particle = 10000
mcdc.settings.N_batch = 10
mcdc.settings.rng_seed = 42
os.chdir(_HERE)
mcdc.settings.output_name = "photon_slab"

# =============================================================================
# Run
# =============================================================================
mcdc.run()
