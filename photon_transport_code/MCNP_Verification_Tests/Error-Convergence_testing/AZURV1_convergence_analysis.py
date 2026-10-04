"""
AZURV1 convergence study: MC/DC vs. Ganapol's semi-analytical solution.

Reads every AZURV1_N*.h5 result file sitting next to this script, computes
the exact planar-pulse Green's function scalar flux (Ganapol, LA-UR-01-1854,
"Homogeneous Infinite Medium Time-Dependent Analytical Benchmarks for X-TM
Transport Methods Development"; restated explicitly in Bennett & McClarren,
2022, arXiv:2205.15783) on the same (x, t) mesh MC/DC tallied on, and plots

    error(x, t) = flux_mean_MCDC(x, t) - phi_analytical(x, t)

as a function of particle count, to show convergence of the MC/DC estimator
to the true solution.

Problem: infinite medium, isotropic pulse at x=t=0, S(x,t) = delta(x)delta(t).
Scattering ratio c = (sigma_s + nu_p*sigma_f) / sigma_t = (1/3 + 2.3/3) / 1
                   = 1.1
(from the MaterialMG definition: capture = scatter = fission = 1/3,
nu_p = 2.3, so sigma_t = 1 and c = 1.1). This matches AZURV1_photon.py.
"""

import glob
import os
import re

import h5py
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ======================================================================================
# Problem parameter
# ======================================================================================
C_SCATTERING_RATIO = 1.1

# ======================================================================================
# Analytical AZURV1 planar-pulse Green's function (Ganapol 2001)
#
#   phi_u(x,t) = e^{-t} / (2t) * Theta(1 - |eta|),                eta = x/t
#
#   phi_c(x,t) = c * e^{-t}/(8*pi) * (1-eta^2) *
#                Int_0^pi du sec^2(u/2) Re[ xi^2 exp( c*t/2*(1-eta^2)*xi ) ]
#                * Theta(1 - |eta|)
#
#   xi(u,eta) = (log(q) + i*u) / (eta + i*tan(u/2)),   q = (1+eta)/(1-eta)
#
# phi(x,t) = phi_u(x,t) + phi_c(x,t). Zero outside the causal wavefront |x|>t.
# ======================================================================================

N_QUAD = 200  # Gauss-Legendre order for the u-integral

_gl_nodes, _gl_weights = np.polynomial.legendre.leggauss(N_QUAD)
# Map nodes/weights from [-1, 1] to [0, pi]
_U_NODES = (_gl_nodes + 1.0) * (np.pi / 2.0)
_U_WEIGHTS = _gl_weights * (np.pi / 2.0)


def analytical_flux(x_grid, t_grid, c):
    """
    Compute phi(x,t) = phi_u + phi_c on the full outer product of x_grid and
    t_grid, vectorized over all (x,t) pairs at once via fixed-order
    Gauss-Legendre quadrature.

    Returns an array of shape (len(t_grid), len(x_grid)) -- same convention
    as MC/DC's mesh-tally flux/mean, i.e. (time, space).

    Points within ~1e-6 of the causal wavefront |x|=t are flagged NaN: the
    exact solution has an (integrable) singularity there and neither the
    analytical evaluation nor a finite-N Monte Carlo tally is meaningful at
    that exact point.
    """
    T, X = np.meshgrid(t_grid, x_grid, indexing="ij")  # both (nt, nx)
    shape = T.shape
    t_flat = T.ravel()
    x_flat = X.ravel()

    with np.errstate(divide="ignore", invalid="ignore"):
        eta = x_flat / t_flat

    inside = np.abs(eta) < (1.0 - 1e-6)
    near_front = (np.abs(eta) >= (1.0 - 1e-6)) & (np.abs(eta) <= (1.0 + 1e-6))

    phi = np.zeros_like(eta)
    phi[~inside] = 0.0
    phi[near_front] = np.nan

    idx = np.where(inside)[0]
    if idx.size > 0:
        t_i = t_flat[idx]
        eta_i = eta[idx]

        # ---- Uncollided term ----
        phi_u = np.exp(-t_i) / (2.0 * t_i)

        # ---- Collided term (vectorized quadrature over u) ----
        u = _U_NODES  # (N_QUAD,)
        w = _U_WEIGHTS  # (N_QUAD,)

        tan_half_u = np.tan(u / 2.0)  # (N_QUAD,)
        sec2_half_u = 1.0 / np.cos(u / 2.0) ** 2  # (N_QUAD,)

        q = (1.0 + eta_i) / (1.0 - eta_i)  # (M,)
        logq = np.log(q)  # (M,)

        # Broadcast to (M, N_QUAD)
        numerator = logq[:, None] + 1j * u[None, :]
        denominator = eta_i[:, None] + 1j * tan_half_u[None, :]
        xi = numerator / denominator

        exponent = (C_SCATTERING_RATIO * t_i[:, None] / 2.0) * (1.0 - eta_i[:, None] ** 2) * xi
        integrand = sec2_half_u[None, :] * xi**2 * np.exp(exponent)
        integral = (integrand.real) @ w  # (M,)

        prefactor = (
            C_SCATTERING_RATIO
            * np.exp(-t_i)
            / (8.0 * np.pi)
            * (1.0 - eta_i**2)
        )
        phi_c = prefactor * integral

        phi[idx] = phi_u + phi_c

    return phi.reshape(shape)


# ======================================================================================
# Load MC/DC result files
# ======================================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))
h5_files = sorted(glob.glob(os.path.join(script_dir, "AZURV1_N*.h5")))

if not h5_files:
    raise FileNotFoundError(
        f"No AZURV1_N*.h5 files found in {script_dir}. "
        "This script expects the MC/DC output files next to it."
    )

runs = []
for path in h5_files:
    with h5py.File(path, "r") as f:
        flux_mean = f["tallies/tracklength_tally_0/flux/mean"][:]
        flux_sdev = f["tallies/tracklength_tally_0/flux/sdev"][:]
        x_edges = f["tallies/tracklength_tally_0/grid/x"][:]
        t_edges = f["tallies/tracklength_tally_0/grid/time"][:]
        N_particle = int(f["settings/N_particle"][()])
        N_batch = int(f["settings/N_batch"][()])

    m = re.search(r"AZURV1_N(\d+)", os.path.basename(path))
    n_tag = int(m.group(1)) if m else N_particle

    runs.append(
        {
            "path": path,
            "name": os.path.basename(path),
            "flux_mean": flux_mean,
            "flux_sdev": flux_sdev,
            "x_edges": x_edges,
            "t_edges": t_edges,
            "N_particle": N_particle,
            "N_batch": N_batch,
            "N_total": N_particle * N_batch,
            "N_tag": n_tag,
        }
    )

runs.sort(key=lambda r: r["N_total"])

# Sanity check: all runs must share the same mesh
ref_x_edges = runs[0]["x_edges"]
ref_t_edges = runs[0]["t_edges"]
for r in runs[1:]:
    if not (np.allclose(r["x_edges"], ref_x_edges) and np.allclose(r["t_edges"], ref_t_edges)):
        raise ValueError(
            f"{r['name']} has a different tally mesh than {runs[0]['name']}; "
            "cannot compare errors point-by-point across runs."
        )

X_MID = 0.5 * (ref_x_edges[:-1] + ref_x_edges[1:])
T_MID = 0.5 * (ref_t_edges[:-1] + ref_t_edges[1:])
N_X = len(X_MID)
N_T = len(T_MID)

print(f"Found {len(runs)} runs:")
for r in runs:
    print(f"  {r['name']:28s}  N_particle={r['N_particle']:>10d}  N_batch={r['N_batch']:>3d}  N_total={r['N_total']:>12d}")

# ======================================================================================
# Analytical reference solution (same mesh for every run, computed once)
# ======================================================================================
print("Computing analytical reference solution on the tally mesh...")
PHI_TRUE = analytical_flux(X_MID, T_MID, C_SCATTERING_RATIO)  # shape (N_T, N_X)

valid_mask = ~np.isnan(PHI_TRUE)  # excludes exact-wavefront points

# ======================================================================================
# Per-run error and summary statistics
# ======================================================================================
for r in runs:
    err = r["flux_mean"] - PHI_TRUE  # (N_T, N_X), NaN where analytical is NaN
    r["error"] = err

    valid_err = err[valid_mask]
    r["mean_abs_error"] = np.nanmean(np.abs(valid_err))
    r["rms_error"] = np.sqrt(np.nanmean(valid_err**2))
    r["max_abs_error"] = np.nanmax(np.abs(valid_err))

# ======================================================================================
# Plot 1: convergence of error metrics vs. total histories (log-log)
# ======================================================================================
N_totals = np.array([r["N_total"] for r in runs], dtype=float)
mean_abs = np.array([r["mean_abs_error"] for r in runs])
rms = np.array([r["rms_error"] for r in runs])
max_abs = np.array([r["max_abs_error"] for r in runs])

fig, ax = plt.subplots(figsize=(8, 6))
ax.loglog(N_totals, mean_abs, "o-", label="Mean |error|", color="tab:blue")
ax.loglog(N_totals, rms, "s-", label="RMS error", color="tab:orange")
ax.loglog(N_totals, max_abs, "^-", label="Max |error| (excl. wavefront)", color="tab:red")

# 1/sqrt(N) reference line, anchored to the RMS error of the smallest run
ref_N = N_totals
ref_line = rms[0] * np.sqrt(N_totals[0] / ref_N)
ax.loglog(ref_N, ref_line, "k--", alpha=0.6, label=r"$\propto 1/\sqrt{N}$ reference")

ax.set_xlabel("Total histories (N_particle x N_batch)")
ax.set_ylabel("Error vs. analytical solution [flux units]")
ax.set_title("AZURV1 Benchmark: MC/DC Convergence to Ganapol's Analytical Solution")
ax.grid(True, which="both", ls=":", alpha=0.6)
ax.legend()
fig.tight_layout()
convergence_plot_path = os.path.join(script_dir, "AZURV1_error_convergence.png")
fig.savefig(convergence_plot_path, dpi=150)
plt.close(fig)
print(f"Convergence plot written to: {convergence_plot_path}")

# ======================================================================================
# Plot 2: spatial error profiles at a representative time snapshot, all N overlaid
# ======================================================================================
t_snapshot_target = 10.5  # near the middle of the time range
t_idx = int(np.argmin(np.abs(T_MID - t_snapshot_target)))
t_snapshot = T_MID[t_idx]

fig, ax = plt.subplots(figsize=(9, 6))
cmap = plt.get_cmap("viridis")
for i, r in enumerate(runs):
    color = cmap(i / max(1, len(runs) - 1))
    ax.plot(
        X_MID,
        r["error"][t_idx, :],
        label=f"N_total = {r['N_total']:,}",
        color=color,
        linewidth=1.2,
    )

ax.axhline(0.0, color="black", linewidth=0.8)
ax.set_xlabel("x [mfp]")
ax.set_ylabel("Error = flux_MCDC - flux_analytical")
ax.set_title(f"AZURV1: Spatial Error Profile at t = {t_snapshot:.1f}")
ax.grid(True, ls=":", alpha=0.6)
ax.legend(fontsize=8)
fig.tight_layout()
profile_plot_path = os.path.join(script_dir, "AZURV1_error_profile.png")
fig.savefig(profile_plot_path, dpi=150)
plt.close(fig)
print(f"Error profile plot written to: {profile_plot_path}")

# ======================================================================================
# Full text report: summary stats + full per-run error tables
# ======================================================================================
report_path = os.path.join(script_dir, "AZURV1_error_analysis.txt")
with open(report_path, "w") as out:
    out.write("AZURV1 benchmark: MC/DC vs. Ganapol analytical solution\n")
    out.write("=" * 100 + "\n")
    out.write(
        "Analytical model: infinite medium, isotropic planar pulse S(x,t)=delta(x)delta(t), "
        f"c = {C_SCATTERING_RATIO}\n"
    )
    out.write(
        "Reference: Ganapol (2001), LA-UR-01-1854; restated in Bennett & McClarren (2022), "
        "arXiv:2205.15783\n"
    )
    out.write(
        "Points within |x/t - 1| < 1e-6 of the causal wavefront are excluded (NaN) -- the "
        "exact solution is singular there.\n"
    )
    out.write("=" * 100 + "\n\n")

    out.write("Summary (error = flux_MCDC_mean - flux_analytical)\n")
    out.write("-" * 100 + "\n")
    out.write(
        f"{'run':>28} {'N_particle':>12} {'N_batch':>8} {'N_total':>14} "
        f"{'mean|err|':>14} {'rms_err':>14} {'max|err|':>14}\n"
    )
    for r in runs:
        out.write(
            f"{r['name']:>28} {r['N_particle']:>12} {r['N_batch']:>8} {r['N_total']:>14} "
            f"{r['mean_abs_error']:>14.6e} {r['rms_error']:>14.6e} {r['max_abs_error']:>14.6e}\n"
        )
    out.write("\n")

    out.write("=" * 100 + "\n")
    out.write("Full per-run error tables (rows = time bin, columns = x bin)\n")
    out.write("=" * 100 + "\n")
    header = f"{'t \\ x':>8} " + "".join(f"{x:>10.2f}" for x in X_MID) + "\n"
    for r in runs:
        out.write(f"\n--- {r['name']}  (N_total = {r['N_total']:,}) ---\n")
        out.write(header)
        for it in range(N_T):
            row = f"{T_MID[it]:>8.2f} " + "".join(
                f"{r['error'][it, ix]:>10.2e}" for ix in range(N_X)
            )
            out.write(row + "\n")

    out.write("\n")
    out.write("=" * 100 + "\n")
    out.write("Analytical reference solution phi(x,t) (rows = time bin, columns = x bin)\n")
    out.write("=" * 100 + "\n")
    out.write(header)
    for it in range(N_T):
        row = f"{T_MID[it]:>8.2f} " + "".join(
            f"{PHI_TRUE[it, ix]:>10.2e}" if not np.isnan(PHI_TRUE[it, ix]) else f"{'NaN':>10}"
            for ix in range(N_X)
        )
        out.write(row + "\n")

print(f"Full error analysis written to: {report_path}")
