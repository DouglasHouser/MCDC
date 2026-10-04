"""
Benchmark 3c: Point Source in Infinite Lead at 1.0 MeV.

Reference: H. Goldstein & J. E. Wilkins (1954), Calculations of the Penetration
of Gamma Rays, NYO-3075.

Material: Lead (Z = 82), number density n = 0.03297 atoms/barn-cm.

Cross sections at 1.0 MeV (NIST XCOM, hardcoded for traceability):
    sigma_Compton = 17.18180 barn/atom
    sigma_PE      =  6.02800 barn/atom (significant)
    sigma_PP      =  0.0     barn/atom (below 1.022 MeV threshold)
    sigma_total   = 23.20980 barn/atom

One mean free path:
    MFP = 1 / (sigma_total * n) = 1 / (23.20980 * 0.03297) = 1.306 cm

The MFP is much shorter than in aluminum because of the high-Z scaling of
photoelectric absorption. Strong Compton scattering still drives meaningful
particle buildup at long distances.

Geometry: Five concentric spheres at 1, 2, 4, 7, and 20 MFP from the origin.

Physics: Standard photon transport via the PhotonReaction architecture
(Compton + photoelectric + pair production).
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
# Material: Lead at 1.0 MeV
# =============================================================================
pb_3c = mcdc.PhotonMaterial(
    elements=[82],
    densities=[0.03297],
    name="lead_1mev",
)

# =============================================================================
# Surfaces: 5 concentric spheres at 1, 2, 4, 7, 20 MFP
# =============================================================================
MFP = 1.306  # cm — Pb at 1 MeV
MFP_DISTANCES = [1, 2, 4, 7, 20]

spheres = []
for i, n_mfp in enumerate(MFP_DISTANCES):
    bc = "vacuum" if i == len(MFP_DISTANCES) - 1 else "none"
    s = mcdc.Surface.Sphere(center=[0, 0, 0], radius=n_mfp * MFP, boundary_condition=bc)
    spheres.append(s)

# =============================================================================
# Cells: innermost sphere + concentric shells
# =============================================================================
mcdc.Cell(region=-spheres[0], fill=pb_3c)
for i in range(1, len(spheres)):
    mcdc.Cell(region=+spheres[i - 1] & -spheres[i], fill=pb_3c)

# =============================================================================
# Source: isotropic point source at origin, 1.0 MeV
# =============================================================================
mcdc.Source(position=[0.0, 0.0, 0.0], energy=1.0, particle_type="photon")

# =============================================================================
# Tallies: surface flux at 1, 2, 4, 7 MFP shells
# =============================================================================
for s in spheres[:-1]:
    mcdc.Tally(surface=s, scores=["flux"])

# =============================================================================
# Settings
# =============================================================================
mcdc.settings.N_particle = 200000
mcdc.settings.N_batch = 100
mcdc.settings.rng_seed = 12345
mcdc.settings.output_name = "benchmark_3c"
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
