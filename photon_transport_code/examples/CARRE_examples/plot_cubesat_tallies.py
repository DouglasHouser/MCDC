"""
Plot mean flux and energy deposition from an MC/DC cubesat output file.

Handles two tally structures found in the file:
  1. "body map"  - a 3D mesh tally (flux/mean, energy-deposit/mean) with grid/x,y,z edges
  2. named subvolumes (e.g. "ADCS SV", "Comms SV", "EPS SV", "OBC SV") - scalar
     flux/mean and energy-deposit/mean with associated sdev

Usage:
    python plot_cubesat_tallies.py path/to/output.h5
"""

import os
import sys
import h5py
import numpy as np
import matplotlib.pyplot as plt


def load_data(filepath):
    with h5py.File(filepath, "r") as f:
        tallies = f["tallies"]

        # Identify the mesh tally (has a "grid/x" dataset) vs scalar SV tallies
        mesh_name = None
        sv_names = []
        for name in tallies.keys():
            if "grid" in tallies[name] and "x" in tallies[name]["grid"]:
                mesh_name = name
            else:
                sv_names.append(name)

        mesh = None
        if mesh_name is not None:
            g = tallies[mesh_name]
            mesh = {
                "name": mesh_name,
                "x": g["grid/x"][:],
                "y": g["grid/y"][:],
                "z": g["grid/z"][:],
                "flux_mean": g["flux/mean"][:],
                "flux_sdev": g["flux/sdev"][:],
                "edep_mean": g["energy-deposit/mean"][:],
                "edep_sdev": g["energy-deposit/sdev"][:],
            }

        svs = {}
        for name in sv_names:
            g = tallies[name]
            svs[name] = {
                "flux_mean": g["flux/mean"][()],
                "flux_sdev": g["flux/sdev"][()],
                "edep_mean": g["energy-deposit/mean"][()],
                "edep_sdev": g["energy-deposit/sdev"][()],
            }

        label = f["settings/output_name"][()].decode()
        n_particle = f["settings/N_particle"][()]
        n_batch = f["settings/N_batch"][()]
        # MC/DC's batch loop runs N_particle histories in EACH of N_batch batches;
        # closeout.py normalizes by dividing by N_particle per batch, then averaging
        # over N_batch batches. So the stored "mean" is per-history over the TOTAL
        # number of histories actually simulated: N_particle * N_batch.
        n_total = n_particle * max(n_batch, 1)

    return label, mesh, svs, n_total


def plot_mesh_slices(label, mesh):
    """Central-plane slices (XY, XZ, YZ) through the mesh mean flux and energy deposit."""
    x, y, z = mesh["x"], mesh["y"], mesh["z"]
    flux = mesh["flux_mean"]      # shape (nx, ny, nz)
    edep = mesh["edep_mean"]

    ix, iy, iz = flux.shape[0] // 2, flux.shape[1] // 2, flux.shape[2] // 2

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle(f"{label} — mesh tally \"{mesh['name']}\" (central-plane slices)", fontsize=13)

    slice_defs = [
        ("XY @ z-mid", flux[:, :, iz].T, edep[:, :, iz].T, x, y, "x [cm]", "y [cm]"),
        ("XZ @ y-mid", flux[:, iy, :].T, edep[:, iy, :].T, x, z, "x [cm]", "z [cm]"),
        ("YZ @ x-mid", flux[ix, :, :].T, edep[ix, :, :].T, y, z, "y [cm]", "z [cm]"),
    ]

    for col, (title, fslice, eslice, gx, gy, xlabel, ylabel) in enumerate(slice_defs):
        im0 = axes[0, col].pcolormesh(gx, gy, fslice, shading="flat", cmap="viridis")
        axes[0, col].set_title(f"Flux — {title}")
        axes[0, col].set_xlabel(xlabel)
        axes[0, col].set_ylabel(ylabel)
        axes[0, col].set_aspect("equal")
        fig.colorbar(im0, ax=axes[0, col], label="mean flux [a.u.]")

        im1 = axes[1, col].pcolormesh(gx, gy, eslice, shading="flat", cmap="magma")
        axes[1, col].set_title(f"Energy deposit — {title}")
        axes[1, col].set_xlabel(xlabel)
        axes[1, col].set_ylabel(ylabel)
        axes[1, col].set_aspect("equal")
        fig.colorbar(im1, ax=axes[1, col], label="mean energy deposit [a.u.]")

    fig.tight_layout()
    return fig


def plot_sv_bars(label, svs, n_total):
    """
    Combined figure: mean flux [a.u.], mean energy deposit [a.u.], and total
    energy deposit [MeV] (= mean * n_total, undoing MC/DC's per-history
    normalization) for each named subvolume, all as one 1x3 panel figure.
    """
    names = list(svs.keys())
    flux_mean = [svs[n]["flux_mean"] for n in names]
    flux_sdev = [svs[n]["flux_sdev"] for n in names]
    edep_mean = [svs[n]["edep_mean"] for n in names]
    edep_sdev = [svs[n]["edep_sdev"] for n in names]
    edep_MeV = [svs[n]["edep_mean"] * n_total for n in names]
    edep_MeV_sdev = [svs[n]["edep_sdev"] * n_total for n in names]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(f"{label} — subvolume tallies", fontsize=13)

    axes[0].bar(names, flux_mean, yerr=flux_sdev, capsize=5, color="steelblue")
    axes[0].set_title("Mean flux")
    axes[0].set_ylabel("flux [a.u.]")
    axes[0].tick_params(axis="x", rotation=30)

    axes[1].bar(names, edep_mean, yerr=edep_sdev, capsize=5, color="firebrick")
    axes[1].set_title("Mean energy deposit")
    axes[1].set_ylabel("energy deposit [a.u.]")
    axes[1].tick_params(axis="x", rotation=30)

    axes[2].bar(names, edep_MeV, yerr=edep_MeV_sdev, capsize=5, color="darkorange")
    axes[2].set_title(f"Total energy deposited\n({n_total:,} source particles)")
    axes[2].set_ylabel("energy deposit [MeV]")
    axes[2].tick_params(axis="x", rotation=30)

    fig.tight_layout()
    return fig


def main():
    default_name = "10MeV_cubesat_model.h5"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(script_dir, default_name)

    filepath = sys.argv[1] if len(sys.argv) > 1 else default_path

    if not os.path.isfile(filepath):
        sys.exit(
            f"Could not find h5 file at:\n  {filepath}\n\n"
            f"Pass the path explicitly, e.g.:\n"
            f'  python plot_cubesat_tallies.py "C:\\Projects\\MCDC\\photon_transport_code\\'
            f'examples\\CARRE_examples\\{default_name}"'
        )

    label, mesh, svs, n_total = load_data(filepath)

    figs = []
    if mesh is not None:
        figs.append(plot_mesh_slices(label, mesh))
    if svs:
        figs.append(plot_sv_bars(label, svs, n_total))

    for i, fig in enumerate(figs):
        out_path = os.path.join(script_dir, f"{label}_tallies_{i}.png")
        fig.savefig(out_path, dpi=200, bbox_inches="tight")
        print(f"Saved {out_path}")

    plt.show()


if __name__ == "__main__":
    main()
