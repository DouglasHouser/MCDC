"""
To test the photon transport code with the exact same setup for neutrons. 
With constant cross-section, pure absorption, and an isotropic point source at the origin, 
the photon transport problem should yield the same results as the neutron transport problem. 
This serves as a verification test for the photon transport code against known analytical solutions for neutrons.

Benchmark 1a: Infinite Medium, Pure Absorption, Constant Cross Section.

Reference: Case, de Hoffman & Placzek (1953), Introduction to the Theory of
Neutron Diffusion, Vol. 1, Tables 17 and 18.

Configuration:
    sigma_total   = 1.0 cm^-1  (1 MFP = 1 cm)
    sigma_scatter = 0.0 cm^-1  (pure absorption)
    sigma_absorb  = 1.0 cm^-1

Analytical solution for particle current at radius r:
    I(r) = exp(-sigma_total * r) / (4 * pi * r^2)
    => normalized current: C(r) = exp(-r)   [since sigma_total = 1.0]

Geometry: 14 concentric spheres at radii 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0,
    5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0 MFP, approximating an infinite medium.
"""

import os
import sys

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
# Material: constant cross-section, pure absorption
# =============================================================================
c_medium = mcdc.ConstantCrossSectionMaterial(
    sigma_total=1.0,
    sigma_scatter=0.0,
    sigma_absorb=1.0,
    name="infinite_medium_1a",
)

# =============================================================================
# Surfaces: 14 concentric spheres, outermost has vacuum BC
# =============================================================================
distances = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0]

spheres = []
for r in distances:
    bc = "vacuum" if r == distances[-1] else "none"
    s = mcdc.Surface.Sphere(center=[0, 0, 0], radius=r, boundary_condition=bc)
    spheres.append(s)

# =============================================================================
# Cells: innermost sphere + concentric shells
# =============================================================================
mcdc.Cell(region=-spheres[0], fill=c_medium)
for i in range(1, len(spheres)):
    mcdc.Cell(region=+spheres[i - 1] & -spheres[i], fill=c_medium)

# =============================================================================
# Source: isotropic point source at origin
# =============================================================================
mcdc.Source(position=[0.0, 0.0, 0.0], energy=1.0, particle_type="neutron")

# =============================================================================
# Tallies: surface flux at each concentric sphere
# =============================================================================
for s in spheres:
    mcdc.Tally(surface=s, scores=["flux"])

# =============================================================================
# Settings
# =============================================================================
mcdc.settings.N_particle = 200000
mcdc.settings.N_batch = 100
mcdc.settings.rng_seed = 42
mcdc.settings.output_name = "benchmark_1a_neutron"
mcdc.settings.use_progress_bar = False

# =============================================================================
# Run — only when invoked directly as a script, not when exec()'d inline
# =============================================================================
if sys.argv[0].endswith(".py"):
    try:
        os.chdir(_HERE)
    except Exception:
        pass
    mcdc.run()