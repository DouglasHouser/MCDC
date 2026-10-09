import os
import numpy as np
import mcdc


# ======================================================================================
# Photon transport verification test for AZURV1 benchmark
# ======================================================================================
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ======================================================================================
# Set model
# ======================================================================================
# Infinite medium with isotropic plane surface at the center
# Based on Ganapol LA-UR-01-1854 (AZURV1 benchmark)
# Effective scattering ratio c = 1.1

# Set materials
m = mcdc.MaterialMG(
    capture=np.array([1.0 / 2.0]),
    scatter=np.array([[1.0 / 2.0]]),
)

# Set surfaces
s1 = mcdc.Surface.PlaneX(x=-1e10, boundary_condition="reflective")
s2 = mcdc.Surface.PlaneX(x=1e10, boundary_condition="reflective")

# Set cells
mcdc.Cell(region=+s1 & -s2, fill=m)

# ======================================================================================
# Set source
# ======================================================================================
# Isotropic pulse at x=t=0

mcdc.Source(
    position=[0.0, 0.0, 0.0],
    isotropic=True,
    energy_group=0,
    particle_type="photon",
    time=0.0,
)

# ======================================================================================
# Set tallies, settings, and run MC/DC
# ======================================================================================

# Tallies
mesh = mcdc.MeshStructured(x=np.linspace(-20.5, 20.5, 202))
mcdc.Tally(mesh=mesh, scores=["flux"], time=np.linspace(0.0, 20.0, 21))

# Settings
mcdc.settings.N_particle = 10000
mcdc.settings.N_batch = 10
mcdc.settings.output_name = "AZURV1_1e5_V2"

# Run
mcdc.run()