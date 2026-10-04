import h5py
import matplotlib.pyplot as plt
import numpy as np
import os

OUTPUT_FILE = "output.h5"

SCORES = ["flux", "collision", "net-current", "fission", "total"]
AXES = ["x", "y", "z", "t", "mu", "energy", "azi"]

with h5py.File(OUTPUT_FILE, "r") as f:
    tallies = f["tallies"]
    tally_names = list(tallies.keys())
    print(f"Found {len(tally_names)} tally/tallies: {tally_names}\n")

    for tally_name in tally_names:
        tally = tallies[tally_name]

        # Find available scores
        scores_found = [s.replace("-", "_") for s in SCORES if s in tally or s.replace("-", "_") in tally]
        raw_scores = [s for s in SCORES if s in tally or s.replace("-", "_") in tally]

        # Find grid axes
        grid = tally.get("grid", {})
        spatial_axes = [ax for ax in AXES if ax in grid and len(grid[ax]) > 2]

        print(f"--- {tally_name} ---")
        print(f"  Scores : {raw_scores}")
        print(f"  Axes   : {list(grid.keys())}")

        for score in raw_scores:
            score_key = score if score in tally else score.replace("-", "_")
            mean = tally[score_key]["mean"][:]
            sdev = tally[score_key]["sdev"][:]
            print(f"  {score} shape: {mean.shape}")

            if mean.ndim == 0 or mean.size == 1:
                print(f"  {score} = {mean.flat[0]:.6e} +/- {sdev.flat[0]:.6e}")
                continue

            # Pick best spatial axis to plot against
            plot_axis = None
            for ax in ["z", "x", "y", "t"]:
                if ax in grid and len(grid[ax]) > 2:
                    plot_axis = ax
                    break

            if plot_axis is None:
                print(f"  No spatial axis found to plot {score}, skipping.")
                continue

            grid_edges = grid[plot_axis][:]
            centers = 0.5 * (grid_edges[:-1] + grid_edges[1:])

            # Find which axis index corresponds to the spatial axis
            # Grid axes order matches array dimensions
            grid_keys = list(grid.keys())
            spatial_axes_ordered = [k for k in grid_keys if len(grid[k]) > 2]

            try:
                ax_idx = spatial_axes_ordered.index(plot_axis)
            except ValueError:
                ax_idx = 0

            # Sum over all axes except the plot axis
            sum_axes = tuple(i for i in range(mean.ndim) if i != ax_idx)
            if sum_axes:
                mean_1d = mean.sum(axis=sum_axes)
                sdev_1d = np.sqrt((sdev**2).sum(axis=sum_axes))
            else:
                mean_1d = mean.flatten()
                sdev_1d = sdev.flatten()

            if len(centers) != len(mean_1d):
                # Fallback: just flatten and use index
                mean_1d = mean.flatten()
                sdev_1d = sdev.flatten()
                centers = np.arange(len(mean_1d))
                plot_axis = "index"

            plt.figure(figsize=(7, 4))
            plt.plot(centers, mean_1d, label=score)
            plt.fill_between(centers, mean_1d - sdev_1d, mean_1d + sdev_1d,
                             alpha=0.3, label="1 std dev")
            plt.xlabel(plot_axis)
            plt.ylabel(score)
            plt.title(f"{tally_name} — {score}")
            plt.legend()
            plt.tight_layout()

            fname = f"{tally_name}_{score.replace('-','_')}.png"
            plt.savefig(fname)
            print(f"  Saved plot: {fname}")
            plt.show()

print("\nDone.")
