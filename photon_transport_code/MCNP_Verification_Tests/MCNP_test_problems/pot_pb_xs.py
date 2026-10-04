"""
Plot photon interaction cross sections for Pb from an OpenMC-format HDF5
photon cross section library (e.g. Pb.h5 from an OpenMC photon_data library).

NOTE: Set XS_FILE_PATH below to the location of your Pb.h5 cross section
file (e.g. the path to your OpenMC photon cross section library, something
like ".../photon_data/Pb.h5").
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ---------------------------------------------------------------------
# Paths to the Pb cross section files -- UPDATE THESE PATHS IF NEEDED
# ---------------------------------------------------------------------
XS_FILE_PATH = Path(r"C:\Projects\MCDC\data\mcdc\Pb.h5")
MCPLIB84_FILE_PATH = (
    Path(__file__).resolve().parent
    / "mcplib84"
    / "mcplib84"
    / "mcplib84"
    / "mcplib84"
)
MCPLIB84_PB_TABLE = "82000.84p"


def read_mcplib84_photon_xs(path, table_id):
    """Read the photon cross section table from an ASCII MCNP ACE file."""
    with path.open() as ace_file:
        for line in ace_file:
            if line.split() and line.split()[0] == table_id:
                header = [line] + [next(ace_file) for _ in range(11)]
                break
        else:
            raise ValueError(f"Could not find {table_id} in {path}")

        nxs = [int(value) for value in " ".join(header[6:8]).split()]
        jxs = [int(value) for value in " ".join(header[8:12]).split()]
        xss = []

        for line in ace_file:
            values = line.split()
            if values and values[0].endswith(".84p"):
                break
            xss.extend(float(value) for value in values)

    energy_count = nxs[2]
    eszg_start = jxs[0] - 1
    eszg_stop = jxs[1] - 1
    eszg = np.array(xss[eszg_start:eszg_stop]).reshape((5, energy_count))

    energy_mev = np.exp(eszg[0])
    incoherent = np.exp(eszg[1])
    coherent = np.exp(eszg[2])
    photoelectric = np.exp(eszg[3])

    # MCPLIB84 stores zero pair-production cross sections as log values of 0.
    pair_log = eszg[4]
    pair_production = np.where(pair_log == 0.0, 0.0, np.exp(pair_log))

    scattering = coherent + incoherent
    total = scattering + photoelectric + pair_production

    return {
        "energy_mev": energy_mev,
        "total": total,
        "pair_production": pair_production,
        "photoelectric": photoelectric,
        "scattering": scattering,
    }

with h5py.File(XS_FILE_PATH, "r") as f:
    rxn = f["photon_reactions"]

    energy = rxn["xs_energy_grid"][()]                                  # eV
    total = rxn["total/MT-401/xs"][()]
    pair_production = rxn["pair_production/MT-503/xs"][()]
    photoelectric = rxn["photoelectric_absorption/MT-501/xs"][()]
    incoherent = rxn["incoherent_scattering/MT-504/xs"][()]              # Compton
    coherent = rxn["elastic/MT-502/xs"][()]                              # Rayleigh

# Combine coherent + incoherent scattering into a single "scattering" curve
scattering = coherent + incoherent

# Convert energy grid from eV to MeV for plotting
energy_MeV = energy / 1.0e6
mcplib84 = read_mcplib84_photon_xs(MCPLIB84_FILE_PATH, MCPLIB84_PB_TABLE)

energy_min_MeV = 1.0
energy_max_MeV = 10.0
mcdc_energy_window = (energy_MeV >= energy_min_MeV) & (energy_MeV <= energy_max_MeV)
mcplib84_energy_window = (
    (mcplib84["energy_mev"] >= energy_min_MeV)
    & (mcplib84["energy_mev"] <= energy_max_MeV)
)

# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6))

curves = [
    ("Total", total, mcplib84["total"], "black", "-"),
    ("Pair Production", pair_production, mcplib84["pair_production"], "tab:blue", "--"),
    ("Photoelectric", photoelectric, mcplib84["photoelectric"], "tab:orange", "-."),
    ("Scattering (Coherent + Incoherent)", scattering, mcplib84["scattering"], "tab:green", ":"),
]

for label, mcdc_values, mcplib84_values, color, linestyle in curves:
    ax.plot(
        energy_MeV[mcdc_energy_window],
        mcdc_values[mcdc_energy_window],
        label=f"MCDC {label}",
        color=color,
        linestyle=linestyle,
        linewidth=2,
    )
    ax.plot(
        mcplib84["energy_mev"][mcplib84_energy_window],
        mcplib84_values[mcplib84_energy_window],
        label=f"MCPLIB84 {label}",
        color=color,
        linestyle=linestyle,
        linewidth=1,
        alpha=0.55,
    )

ax.set_xlim(energy_min_MeV, energy_max_MeV)
ax.set_xlabel("Photon Energy (MeV)")
ax.set_ylabel("Cross Section (barns)")
ax.set_title("Photon Interaction Cross Sections for Pb: 1-10 MeV")
ax.legend()
ax.grid(True, linestyle=":", linewidth=0.5)

fig.tight_layout()
fig.savefig("Pb_cross_sections.png", dpi=300)
plt.show()
