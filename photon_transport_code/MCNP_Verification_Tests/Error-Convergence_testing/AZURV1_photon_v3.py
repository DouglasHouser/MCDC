import os
import numpy as np
import mcdc

# ======================================================================================
# Photon transport AZURV1 benchmark (Ganapol LA-UR-01-1854)
# Infinite medium, isotropic planar pulse source, scatter + capture only, c < 1.
# Replicates the neutron input.py setup using ConstantCrossSectionMaterial instead
# of MaterialMG, since photon XS here should be energy-independent and isotropic
# to match Ganapol's assumptions.
# ======================================================================================
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Photon speed MC/DC actually uses internally (see interface.py:particle_speed,
# _SPEED_OF_LIGHT). The value 29.9792458 is cm/ns (despite being commented as
# cm/shake in that file -- 2.99792458e10 cm/s * 1e-9 s/ns = 29.9792458 cm/ns,
# confirmed against particle.py's move(): t += distance / particle_speed()).
# particle["t"] therefore accumulates in nanoseconds, not seconds.
SPEED_OF_LIGHT = 29.9792458  # cm/ns

# ======================================================================================
# Set model
# ======================================================================================
# sigma_total = 1 cm^-1  (1 unit = 1 mean free path, matches AZURV1 normalization)
# c = sigma_scatter / sigma_total = 0.5  (subcritical; change as needed, keep c < 1)

sigma_t = 1.0
c = 0.5
sigma_s = c * sigma_t
sigma_a = sigma_t - sigma_s

m = mcdc.ConstantCrossSectionMaterial(
    sigma_total=sigma_t,
    sigma_scatter=sigma_s,
    sigma_absorb=sigma_a,
    name="AZURV1_photon_medium",
)

# Set surfaces (same reflective bounding box as the neutron problem)
s1 = mcdc.Surface.PlaneX(x=-1e10, boundary_condition="reflective")
s2 = mcdc.Surface.PlaneX(x=1e10, boundary_condition="reflective")

# Set cells
mcdc.Cell(region=+s1 & -s2, fill=m)

# ======================================================================================
# Set source
# ======================================================================================
# Isotropic pulse at x=t=0. Energy value is arbitrary since XS is energy-independent,
# but the field is required -- use 1 MeV as a placeholder.

mcdc.Source(
    position=[0.0, 0.0, 0.0],
    isotropic=True,
    energy=1.0,
    particle_type="photon",
    time=0.0,
)

# ======================================================================================
# Set tallies, settings, and run MC/DC
# ======================================================================================

# Ganapol's tally grid is in mean-free-times (dimensionless, speed=1, sigma_t=1
# assumed). Since sigma_t=1 cm^-1 here (1 mfp = 1 cm), dividing by the real cm/ns
# speed converts directly to the nanoseconds particle["t"] uses -- no extra
# seconds<->ns step needed.
T_MFT = np.linspace(0.0, 20.0, 21)
t_ns = T_MFT / SPEED_OF_LIGHT

mesh = mcdc.MeshStructured(x=np.linspace(-20.5, 20.5, 202))
mcdc.Tally(mesh=mesh, scores=["flux"], time=t_ns)

# Settings
mcdc.settings.N_particle = 1000
mcdc.settings.N_batch = 10
mcdc.settings.output_name = "AZURV1_photon_1e4"  # kept under 32-char truncation limit

# Run
mcdc.run()
