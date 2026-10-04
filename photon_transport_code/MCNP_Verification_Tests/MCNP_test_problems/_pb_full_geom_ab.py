import os, sys, math
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
import numpy as np
import mcdc

RADII = [float(r) for r in range(2, 41, 2)]
lead = mcdc.PhotonMaterial(elements=[82], densities=[0.03299], name="lead")
spheres = []
for r in RADII:
    bc = "vacuum" if r == RADII[-1] else "none"
    spheres.append(mcdc.Surface.Sphere(center=[0, 0, 0], radius=r, boundary_condition=bc))
cells = [mcdc.Cell(region=-spheres[0], fill=lead)]
for i in range(1, len(spheres)):
    cells.append(mcdc.Cell(region=+spheres[i - 1] & -spheres[i], fill=lead))
mcdc.Source(position=[0.0, 0.0, 0.0], energy=10.0, particle_type="photon")
names = [f"region_{i}" for i in range(len(cells))]
for name, cell in zip(names, cells):
    mcdc.Tally(cell=cell, scores=["flux"], name=name)
mcdc.settings.N_particle = 3000
mcdc.settings.N_batch = 10
mcdc.settings.rng_seed = 42
mcdc.settings.output_name = "_pb_full_geom_ab"
mcdc.settings.use_progress_bar = False

if sys.argv[0].endswith(".py"):
    os.chdir(_HERE)
    mcdc.run()
    from mpi4py import MPI
    if MPI.COMM_WORLD.Get_rank() == 0:
        import h5py
        with h5py.File(os.path.join(_HERE, "_pb_full_geom_ab.h5"), "r") as f:
            vals = [float(np.squeeze(f["tallies"][n]["flux"]["mean"][()])) for n in names]
        tag = os.environ.get("AB_TAG", "?")
        print("AB_RESULT", tag, " ".join(f"{v:.6e}" for v in vals[:6]))
        try:
            os.remove(os.path.join(_HERE, "_pb_full_geom_ab.h5"))
        except OSError:
            pass
