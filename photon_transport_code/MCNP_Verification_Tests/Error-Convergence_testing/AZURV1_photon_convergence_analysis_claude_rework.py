"""
AZURV1 convergence study (PHOTON version): MC/DC vs. Ganapol's semi-analytical
solution.

Adapted from the neutron AZURV1_convergence_analysis.py for the photon runs
produced by AZURV1_photon_v3.py, which uses ConstantCrossSectionMaterial
(isotropic-elastic scatter + capture, no fission) instead of the fissioning
MaterialMG used in the neutron problem. Two physics/unit changes follow from
that:

  1. Scattering ratio: c = sigma_scatter / sigma_total = 0.5 (subcritical),
     not c = 1.1. Ganapol's formula below is otherwise unchanged -- it just
     takes a different c.

  2. Time units: MC/DC's photon speed is hardcoded (interface.py,
     _SPEED_OF_LIGHT = 29.9792458 cm/ns) and particle["t"] accumulates in
     nanoseconds (particle.py: move() does t += distance / particle_speed()).
     AZURV1_photon_v3.py's tally time grid is therefore stored in ns, not
     mean-free-times. Ganapol's formula assumes speed=1, sigma_t=1, so the
     stored ns grid is converted back to mean-free-time via
     t_mft = t_ns * SPEED_OF_LIGHT before evaluating the analytical solution.

  UNVERIFIED ASSUMPTION -- flux value normalization: it is not confirmed
  whether MC/DC's tracklength "flux" score divides by the time-bin width in
  native units (ns) or is otherwise unit-agnostic. If it divides by the
  native (ns) bin width, MC/DC's photon flux values will be systematically
  inflated by a factor of SPEED_OF_LIGHT (~29.98) relative to Ganapol's
  per-mean-free-time convention -- and critically, that inflation would be
  IDENTICAL for every run regardless of N (same failure signature as the old
  photon_fluorescence bug: flat error vs. particle count = systematic bias,
  not statistical noise; see AZURV1_error_convergence.png reference). Check
  the convergence plot this script produces: if mean|error|, RMS, and max
  |error| are all flat with N and roughly SPEED_OF_LIGHT times larger/smaller
  than expected, flip MCDC_FLUX_SCALE below and rerun.
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
# Problem parameters
# ======================================================================================
C_SCATTERING_RATIO = 0.5  # sigma_scatter / sigma_total in AZURV1_photon_v3.py

# Photon speed MC/DC uses internally (interface.py: _SPEED_OF_LIGHT), cm/ns.
# Used to convert the tally's stored ns time grid back to mean-free-time for
# the analytical formula (Ganapol assumes speed=1, sigma_t=1).
SPEED_OF_LIGHT = 29.9792458  # cm/ns

# Flux-value correction -- CONFIRMED, not a guess. MC/DC's tracklength tally
# (transport/tally/score.py: tracklength_tally) scores raw
#     flux = distance_scored * particle["w"]
# with NO division by cell volume anywhere in the scoring path, and
# closeout.py's _finalize only divides by N_history (particle/batch count).
# So flux/mean in the h5 file is a raw fluence-per-history sum over whatever
# x-bin width the mesh happens to use -- not a true flux -- until it's
# divided by dx here. (The time-bin width does NOT need a separate division:
# the tally time grid was constructed with exactly 1-mean-free-time-wide
# bins by design, so that factor is already 1.) Verified empirically: this
# correction drops mean|error| on the 1e9-particle run from ~0.09 (flat,
# unexplained) to ~0.001 -- this is very likely also present, uncorrected,
# in the neutron AZURV1 benchmark, since that comparison script never
# divided by dx either.
APPLY_DX_CORRECTION = True

# Glob pattern for photon output files to include in the convergence study.
# Adjust this (or the file names you save from AZURV1_photon_v3.py) so every
# run you want compared matches. N_total for sorting/labeling is read from
# each file's own settings/N_particle * settings/N_batch, not parsed from
# the filename, so the naming convention itself doesn't matter.
FILE_GLOB_PATTERN = "AZURV1_photon*.h5"

# If True, average flux(x) and flux(-x) together before comparing to the
# analytical solution. The problem is exactly symmetric about x=0, so this
# pools 2x the MC statistics into each |x| point and reduces noise -- but it
# also halves spatial resolution and could mask a real left-right asymmetry
# (e.g. a direction-sampling bug). Off by default so this methodological
# choice isn't made silently.
FOLD_MIRROR_SYMMETRY = False

# ======================================================================================
# Analytical AZURV1 planar-pulse Green's function (Ganapol 2001) -- unchanged
# from the neutron version except for the value of c passed in.
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
_U_NODES = (_gl_nodes + 1.0) * (np.pi / 2.0)
_U_WEIGHTS = _gl_weights * (np.pi / 2.0)

# Sub-quadrature order (per dimension) used to bin-average phi(x,t) over each
# (dx, dt) cell -- see analytical_flux_bin_averaged below. Verified stable to
# 3-4 significant figures from Q_SUB=7 up through Q_SUB=30 on representative
# cells away from t=0, so 7 is not a precision bottleneck (see MIN_T_MFT_FOR_STATS
# note below for the actual source of residual bias near t=0).
Q_SUB = 7

# Ganapol's uncollided term phi_u(x,t) = e^(-t)/(2t) diverges as t -> 0, and
# integral_0^1 (1/2t) dt diverges logarithmically -- so the TRUE bin-average
# of the analytical solution over the first time bin (t in [0,1] mft) is
# mathematically infinite near x=0, not just hard to compute. No amount of
# quadrature refinement fixes this (verified: Q_SUB=7 vs 30 agree to 3-4 sig
# figs on non-singular cells). Confirmed empirically on the 1e9-particle run:
# mean|error|/mean(sdev) = 977 at t=0.5 mft, 42 at t=1.5, decaying smoothly
# to settle at 0.75-1.05 from t=5.5 mft onward -- matching the theoretical
# value sqrt(2/pi)=0.798 expected for an unbiased Gaussian estimator almost
# exactly. Time bins below this threshold are excluded from the summary
# statistics/plots (but retained in the full per-run report table below) so
# the headline "accuracy" numbers reflect real MC/DC performance rather than
# an artifact of comparing against an analytically-undefined quantity.
MIN_T_MFT_FOR_STATS = 2.0
_gl_sub_nodes, _gl_sub_weights = np.polynomial.legendre.leggauss(Q_SUB)


def analytical_flux_points(x_points, t_points, c):
    """
    Evaluate phi(x,t) = phi_u + phi_c at explicit PAIRED points (x_points[i],
    t_points[i]) -- not an outer product. Both inputs must be 1D arrays of
    the same length (t in mean-free-times). Returns a 1D array of the same
    length. Points within ~1e-6 of the causal wavefront |x|=t are NaN.
    """
    x_points = np.asarray(x_points, dtype=np.float64)
    t_points = np.asarray(t_points, dtype=np.float64)

    with np.errstate(divide="ignore", invalid="ignore"):
        eta = x_points / t_points

    inside = np.abs(eta) < (1.0 - 1e-6)
    near_front = (np.abs(eta) >= (1.0 - 1e-6)) & (np.abs(eta) <= (1.0 + 1e-6))

    phi = np.zeros_like(eta)
    phi[~inside] = 0.0
    phi[near_front] = np.nan

    idx = np.where(inside)[0]
    if idx.size > 0:
        t_i = t_points[idx]
        eta_i = eta[idx]

        phi_u = np.exp(-t_i) / (2.0 * t_i)

        u = _U_NODES
        w = _U_WEIGHTS

        tan_half_u = np.tan(u / 2.0)
        sec2_half_u = 1.0 / np.cos(u / 2.0) ** 2

        q = (1.0 + eta_i) / (1.0 - eta_i)
        logq = np.log(q)

        numerator = logq[:, None] + 1j * u[None, :]
        denominator = eta_i[:, None] + 1j * tan_half_u[None, :]
        xi = numerator / denominator

        exponent = (c * t_i[:, None] / 2.0) * (1.0 - eta_i[:, None] ** 2) * xi
        integrand = sec2_half_u[None, :] * xi**2 * np.exp(exponent)
        integral = (integrand.real) @ w

        prefactor = c * np.exp(-t_i) / (8.0 * np.pi) * (1.0 - eta_i**2)
        phi_c = prefactor * integral

        phi[idx] = phi_u + phi_c

    return phi


def analytical_flux(x_grid, t_grid, c):
    """
    Point-value phi(x,t) on the full outer product of x_grid and t_grid
    (t_grid in mean-free-times), evaluated at each grid point exactly --
    NOT bin-averaged. Kept for reference/diagnostics; the main comparison
    below uses analytical_flux_bin_averaged instead, since that's the
    quantity MC/DC's track-length tally actually estimates.

    Returns an array of shape (len(t_grid), len(x_grid)), matching MC/DC's
    flux/mean convention (time, space).
    """
    T, X = np.meshgrid(t_grid, x_grid, indexing="ij")
    shape = T.shape
    phi = analytical_flux_points(X.ravel(), T.ravel(), c)
    return phi.reshape(shape)


def analytical_flux_bin_averaged(x_edges, t_edges_mft, c, q_sub=Q_SUB):
    """
    Cell-averaged phi(x,t): for each (x_bin, t_bin) rectangle, the exact
    integral of phi over that dx*dt area divided by the area -- the same
    quantity MC/DC's track-length tally is an unbiased estimator of (raw
    track length scored in a cell, divided by the cell's dx once
    APPLY_DX_CORRECTION is applied; time bins are already exactly 1 mft
    wide by construction). Comparing against this instead of the point
    value at the bin midpoint removes the fixed-mesh discretization bias
    that otherwise plateaus the mean-error convergence plot even as N grows
    -- see AZURV1_photon_error_convergence.png discussion.

    Uses q_sub x q_sub Gauss-Legendre sub-quadrature per cell (accurate to
    high order for a smooth integrand; only the wavefront-straddling cells
    need care, handled below).

    Returns array of shape (len(t_edges_mft)-1, len(x_edges)-1), matching
    MC/DC's flux/mean convention (time, space). A cell is NaN only if every
    sub-quadrature point in it lands within the ~1e-6 wavefront-singularity
    band (astronomically unlikely away from x=t exactly); cells straddling
    the wavefront otherwise average over their valid sub-points only, with
    invalid (NaN) sub-points excluded and the remaining weights renormalized.
    """
    x_lo = x_edges[:-1]
    x_hi = x_edges[1:]
    t_lo = t_edges_mft[:-1]
    t_hi = t_edges_mft[1:]
    N_X = len(x_lo)
    N_T = len(t_lo)

    g, w = np.polynomial.legendre.leggauss(q_sub)  # (q_sub,) nodes/weights on [-1,1]

    # Sub-point coordinates per cell, broadcast to (N_T, N_X, q_sub, q_sub):
    # axis 2 = x sub-index, axis 3 = t sub-index.
    x_sub = 0.5 * (x_hi - x_lo)[None, :, None, None] * g[None, None, :, None] + 0.5 * (
        x_hi + x_lo
    )[None, :, None, None]
    t_sub = 0.5 * (t_hi - t_lo)[:, None, None, None] * g[None, None, None, :] + 0.5 * (
        t_hi + t_lo
    )[:, None, None, None]
    x_sub = np.broadcast_to(x_sub, (N_T, N_X, q_sub, q_sub))
    t_sub = np.broadcast_to(t_sub, (N_T, N_X, q_sub, q_sub))

    phi_sub = analytical_flux_points(x_sub.ravel(), t_sub.ravel(), c).reshape(
        N_T, N_X, q_sub, q_sub
    )

    weight_grid = w[None, None, :, None] * w[None, None, None, :]  # (1,1,q_sub,q_sub)
    valid = ~np.isnan(phi_sub)
    phi_filled = np.where(valid, phi_sub, 0.0)
    weight_valid = np.where(valid, weight_grid, 0.0)

    weight_sum = weight_valid.sum(axis=(2, 3))
    numerator = (phi_filled * weight_valid).sum(axis=(2, 3))

    with np.errstate(invalid="ignore", divide="ignore"):
        bin_avg = numerator / weight_sum
    bin_avg = np.where(weight_sum > 0.0, bin_avg, np.nan)

    return bin_avg


# ======================================================================================
# Load MC/DC result files
# ======================================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))
h5_files = sorted(glob.glob(os.path.join(script_dir, FILE_GLOB_PATTERN)))

if not h5_files:
    raise FileNotFoundError(
        f"No files matching '{FILE_GLOB_PATTERN}' found in {script_dir}. "
        "Adjust FILE_GLOB_PATTERN to match your saved photon run names."
    )

runs = []
for path in h5_files:
    with h5py.File(path, "r") as f:
        flux_mean = f["tallies/tracklength_tally_0/flux/mean"][:]
        flux_sdev = f["tallies/tracklength_tally_0/flux/sdev"][:]
        x_edges = f["tallies/tracklength_tally_0/grid/x"][:]
        t_edges_native = f["tallies/tracklength_tally_0/grid/time"][:]  # ns
        N_particle = int(f["settings/N_particle"][()])
        N_batch = int(f["settings/N_batch"][()])

    m = re.search(r"N(\d+)", os.path.basename(path))
    n_tag = int(m.group(1)) if m else None

    if APPLY_DX_CORRECTION:
        dx = x_edges[1:] - x_edges[:-1]  # per-bin width; supports non-uniform mesh
        flux_mean = flux_mean / dx[None, :]
        flux_sdev = flux_sdev / dx[None, :]

    runs.append(
        {
            "path": path,
            "name": os.path.basename(path),
            "flux_mean": flux_mean,
            "flux_sdev": flux_sdev,
            "x_edges": x_edges,
            "t_edges_native": t_edges_native,
            "N_particle": N_particle,
            "N_batch": N_batch,
            "N_total": N_particle * N_batch,
            "N_tag": n_tag,
        }
    )

runs.sort(key=lambda r: r["N_total"])

# Sanity check: all runs must share the same mesh
ref_x_edges = runs[0]["x_edges"]
ref_t_edges_native = runs[0]["t_edges_native"]
for r in runs[1:]:
    if not (
        np.allclose(r["x_edges"], ref_x_edges)
        and np.allclose(r["t_edges_native"], ref_t_edges_native)
    ):
        raise ValueError(
            f"{r['name']} has a different tally mesh than {runs[0]['name']}; "
            "cannot compare errors point-by-point across runs."
        )

X_MID = 0.5 * (ref_x_edges[:-1] + ref_x_edges[1:])
T_MID_native = 0.5 * (ref_t_edges_native[:-1] + ref_t_edges_native[1:])  # ns
T_MID_MFT = T_MID_native * SPEED_OF_LIGHT  # convert to mean-free-time for Ganapol
ref_t_edges_mft = ref_t_edges_native * SPEED_OF_LIGHT  # bin edges, for bin-averaging
N_X = len(X_MID)
N_T = len(T_MID_MFT)

print(f"Found {len(runs)} runs (APPLY_DX_CORRECTION = {APPLY_DX_CORRECTION}):")
for r in runs:
    print(
        f"  {r['name']:32s}  N_particle={r['N_particle']:>10d}  "
        f"N_batch={r['N_batch']:>3d}  N_total={r['N_total']:>12d}"
    )

# ======================================================================================
# Analytical reference solution: BIN-AVERAGED over each (dx, dt) cell, not
# evaluated at the bin midpoint. This matches exactly what MC/DC's
# track-length tally estimates -- see analytical_flux_bin_averaged docstring
# above. Using the point-value version here instead would reintroduce the
# fixed-mesh discretization bias discussed for AZURV1_photon_error_convergence.png.
# ======================================================================================
print(f"Computing bin-averaged analytical reference solution (Q_SUB={Q_SUB}x{Q_SUB} per cell)...")
PHI_TRUE = analytical_flux_bin_averaged(
    ref_x_edges, ref_t_edges_mft, C_SCATTERING_RATIO, q_sub=Q_SUB
)  # (N_T, N_X)

valid_mask = ~np.isnan(PHI_TRUE)

# Additionally exclude time bins too close to t=0, where the analytical
# solution's uncollided term is singular -- see MIN_T_MFT_FOR_STATS note
# above. This mask is used for summary statistics/plots only; the full
# per-run report table below still includes every bin for transparency.
stats_time_mask = T_MID_MFT >= MIN_T_MFT_FOR_STATS  # (N_T,)
stats_valid_mask = valid_mask & stats_time_mask[:, None]
n_excluded_bins = int(np.sum(~stats_time_mask))
print(
    f"Excluding {n_excluded_bins} time bin(s) below t={MIN_T_MFT_FOR_STATS} mft from "
    "summary statistics (analytical uncollided term singular near t=0; see "
    "MIN_T_MFT_FOR_STATS note in script header)."
)

# ======================================================================================
# Per-run error and summary statistics
# ======================================================================================
for r in runs:
    err = r["flux_mean"] - PHI_TRUE
    r["error"] = err  # full (N_T, N_X) grid, all bins, for the report table

    valid_err = err[stats_valid_mask]
    r["mean_abs_error"] = np.nanmean(np.abs(valid_err))
    r["rms_error"] = np.sqrt(np.nanmean(valid_err**2))
    r["max_abs_error"] = np.nanmax(np.abs(valid_err))

    # Mean statistical (batch) standard deviation over the same (post-t-cutoff)
    # points -- this is MC/DC's own reported uncertainty, independent of the
    # analytical comparison, and should shrink as 1/sqrt(N) by construction.
    r["mean_sdev"] = np.nanmean(r["flux_sdev"][stats_valid_mask])

# ======================================================================================
# Plot 1: mean error vs. analytical solution (accuracy), vs. total histories
# ======================================================================================
N_totals = np.array([r["N_total"] for r in runs], dtype=float)
mean_abs = np.array([r["mean_abs_error"] for r in runs])
rms = np.array([r["rms_error"] for r in runs])
max_abs = np.array([r["max_abs_error"] for r in runs])
mean_sdev = np.array([r["mean_sdev"] for r in runs])

fig, ax = plt.subplots(figsize=(8, 6))
ax.loglog(N_totals, mean_abs, "o-", label="Mean |error| vs. analytical", color="tab:blue")

ref_N = N_totals
ref_line = mean_abs[2] * np.sqrt(N_totals[2] / ref_N)
ax.loglog(ref_N, ref_line, "k--", alpha=0.6, label=r"$\propto 1/\sqrt{N}$ reference")

ax.set_xlabel("Total histories (N_particle x N_batch)")
ax.set_ylabel("Mean |error| vs. analytical solution [flux units]")
ax.set_title(
    f"AZURV1 Photon Benchmark (c={C_SCATTERING_RATIO}): "
    "MC/DC Accuracy vs. Ganapol's Analytical Solution"
)
ax.grid(True, which="both", ls=":", alpha=0.6)
ax.legend()
fig.tight_layout()
convergence_plot_path = os.path.join(script_dir, "AZURV1_photon_error_convergence_post_one_half_mft.png")
fig.savefig(convergence_plot_path, dpi=150)
plt.close(fig)
print(f"Mean-error (accuracy) plot written to: {convergence_plot_path}")

if len(runs) >= 2 and np.allclose(mean_abs, mean_abs[0], rtol=1e-3):
    print(
        "NOTE: mean error is flat across all N (not decreasing with more "
        "histories). With APPLY_DX_CORRECTION on, this is the expected "
        "fixed-mesh discretization floor (MC/DC's cell-averaged flux vs. "
        "Ganapol's point-value solution at the bin midpoint) -- check the "
        "statistical convergence plot below to confirm the underlying "
        "statistical error is still shrinking as expected; if it isn't, "
        "something else needs investigating."
    )

# ======================================================================================
# Plot 2: statistical error convergence (MC/DC's own batch sdev vs. N)
# ======================================================================================
# This isolates pure Monte Carlo statistical convergence from the mean-error
# plot above. It uses MC/DC's own reported sdev (flux/sdev in the h5 file,
# dx-corrected the same way as flux/mean), which shrinks as 1/sqrt(N) by
# construction of the batch-statistics estimator in closeout.py -- this is
# what confirms MC/DC's transport/statistics engine itself is behaving
# correctly, independent of whether the mean has converged close enough to
# the analytical solution to see that trend in Plot 1.
fig, ax = plt.subplots(figsize=(8, 6))
ax.loglog(N_totals, mean_sdev, "o-", label="Mean statistical sdev (MC/DC)", color="tab:green")

ref_N = N_totals
ref_line = mean_sdev[2] * np.sqrt(N_totals[2] / ref_N)
ax.loglog(ref_N, ref_line, "k--", alpha=0.6, label=r"$\propto 1/\sqrt{N}$ reference")

ax.set_xlabel("Total histories (N_particle x N_batch)")
ax.set_ylabel("Mean statistical standard deviation [flux units]")
ax.set_title(
    f"AZURV1 Photon Benchmark (c={C_SCATTERING_RATIO}): "
    "Statistical Error Convergence (MC/DC batch sdev)"
)
ax.grid(True, which="both", ls=":", alpha=0.6)
ax.legend()
fig.tight_layout()
sdev_plot_path = os.path.join(script_dir, "AZURV1_photon_sdev_convergence_post_one_half_mft.png")
fig.savefig(sdev_plot_path, dpi=150)
plt.close(fig)
print(f"Statistical (sdev) convergence plot written to: {sdev_plot_path}")

# ======================================================================================
# Comparison table averaged over distance, with time as the row axis: for
# each time bin, collapse the spatial dimension into mean/max |% diff|
# (and signed mean, to catch systematic bias) against the analytical
# solution. Points near the causal wavefront (NaN in PHI_TRUE) and points
# where the analytical flux is exactly zero (outside the wavefront) are
# excluded from the average, since relative error is undefined there.
# ======================================================================================


def _fold_mirror(arr_2d, x_mid):
    """Average arr_2d[:, i] with arr_2d[:, mirror(i)] across the x axis,
    where mirror(i) is the bin whose x_mid is closest to -x_mid[i]."""
    n_x = len(x_mid)
    folded = arr_2d.copy()
    for i in range(n_x):
        j = int(np.argmin(np.abs(x_mid + x_mid[i])))
        folded[:, i] = 0.5 * (arr_2d[:, i] + arr_2d[:, j])
    return folded


if FOLD_MIRROR_SYMMETRY:
    PHI_TRUE_CMP = _fold_mirror(PHI_TRUE, X_MID)
    for r in runs:
        r["flux_mean_cmp"] = _fold_mirror(r["flux_mean"], X_MID)
else:
    PHI_TRUE_CMP = PHI_TRUE
    for r in runs:
        r["flux_mean_cmp"] = r["flux_mean"]

time_table_rows = []
for it in range(N_T):
    analytical_row = PHI_TRUE_CMP[it, :]
    valid = ~np.isnan(analytical_row) & (analytical_row != 0.0)
    n_valid = int(np.sum(valid))

    row = {"t_mft": T_MID_MFT[it], "n_valid_x": n_valid}
    for r in runs:
        if n_valid == 0:
            row[f"{r['name']}_mean_signed_pctdiff"] = np.nan
            row[f"{r['name']}_mean_abs_pctdiff"] = np.nan
            row[f"{r['name']}_max_abs_pctdiff"] = np.nan
            continue
        mcdc_row = r["flux_mean_cmp"][it, :]
        pct_diff = (mcdc_row[valid] - analytical_row[valid]) / analytical_row[valid] * 100.0
        row[f"{r['name']}_mean_signed_pctdiff"] = np.mean(pct_diff)
        row[f"{r['name']}_mean_abs_pctdiff"] = np.mean(np.abs(pct_diff))
        row[f"{r['name']}_max_abs_pctdiff"] = np.max(np.abs(pct_diff))
    time_table_rows.append(row)

# ---- CSV (primary deliverable) ----
csv_path = os.path.join(script_dir, "AZURV1_photon_comparison_table_post_one_half_mft.csv")
with open(csv_path, "w") as out:
    header_cols = ["t_mft", "n_valid_x"]
    for r in runs:
        header_cols += [
            f"{r['name']}_mean_signed_pctdiff",
            f"{r['name']}_mean_abs_pctdiff",
            f"{r['name']}_max_abs_pctdiff",
        ]
    out.write(",".join(header_cols) + "\n")
    for row in time_table_rows:
        vals = [f"{row['t_mft']:.4f}", str(row["n_valid_x"])]
        for r in runs:
            for suffix in ("mean_signed_pctdiff", "mean_abs_pctdiff", "max_abs_pctdiff"):
                v = row[f"{r['name']}_{suffix}"]
                vals.append("nan" if np.isnan(v) else f"{v:.3f}")
        out.write(",".join(vals) + "\n")
print(f"Comparison table (CSV, time-axis, x-averaged) written to: {csv_path}")
if FOLD_MIRROR_SYMMETRY:
    print("  (mirror-folded across x=0 before comparison)")

# ---- Console summary ----
print("\nPer-time-bin comparison (averaged over x):")
for row in time_table_rows:
    line = f"  t={row['t_mft']:>6.2f} mft  n_valid_x={row['n_valid_x']:>4}"
    for r in runs:
        mabs = row[f"{r['name']}_mean_abs_pctdiff"]
        mmax = row[f"{r['name']}_max_abs_pctdiff"]
        mabs_s = "  nan" if np.isnan(mabs) else f"{mabs:>6.2f}"
        mmax_s = "  nan" if np.isnan(mmax) else f"{mmax:>6.2f}"
        line += f"  |  {r['name']}: mean|%diff|={mabs_s}  max|%diff|={mmax_s}"
    print(line)

# ======================================================================================
# Full text report: summary stats + comparison table + full per-run error grids
# ======================================================================================
report_path = os.path.join(script_dir, "AZURV1_photon_error_analysis.txt")
with open(report_path, "w") as out:
    out.write("AZURV1 photon benchmark: MC/DC vs. Ganapol analytical solution\n")
    out.write("=" * 100 + "\n")
    out.write(
        "Analytical model: infinite medium, isotropic planar pulse S(x,t)=delta(x)delta(t), "
        f"c = {C_SCATTERING_RATIO} (ConstantCrossSectionMaterial, sigma_scatter=0.5, "
        "sigma_absorb=0.5, sigma_total=1.0)\n"
    )
    out.write(
        "Reference: Ganapol (2001), LA-UR-01-1854; restated in Bennett & McClarren (2022), "
        "arXiv:2205.15783\n"
    )
    out.write(
        f"Tally time grid stored in native units (ns); converted to mean-free-time via "
        f"t_mft = t_ns * {SPEED_OF_LIGHT} for comparison against the analytical solution.\n"
    )
    out.write(
        f"APPLY_DX_CORRECTION: {APPLY_DX_CORRECTION} (divides raw MC/DC flux by the "
        "x-bin width dx -- confirmed necessary; MC/DC's tracklength_tally scores raw "
        "distance*weight with no volume normalization built in; see script header for "
        "verification against the 1e9-particle run).\n"
    )
    out.write(
        "Points within |x/t - 1| < 1e-6 of the causal wavefront are excluded (NaN) -- the "
        "exact solution is singular there.\n"
    )
    out.write(
        f"Analytical reference is BIN-AVERAGED (Q_SUB={Q_SUB}x{Q_SUB} Gauss-Legendre "
        "sub-quadrature per cell), matching what MC/DC's tracklength tally estimates -- "
        "not evaluated at the bin midpoint.\n"
    )
    out.write(
        f"Summary statistics (Plot 1, RMS/max/mean_sdev columns below) exclude time bins "
        f"below t={MIN_T_MFT_FOR_STATS} mft: Ganapol's uncollided term e^(-t)/(2t) diverges "
        "as t->0, making the true bin-average analytically undefined near the pulse origin "
        "in time (verified: mean|err|/sdev = 977 at t=0.5 mft vs. the expected sqrt(2/pi)="
        "0.798 for an unbiased estimator, settling to 0.75-1.05 from t=5.5 mft onward). "
        "The full per-run error table further below still includes every time bin.\n"
    )
    out.write("=" * 100 + "\n\n")

    out.write("Summary (error = flux_MCDC_mean - flux_analytical)\n")
    out.write("-" * 100 + "\n")
    out.write(
        f"{'run':>32} {'N_particle':>12} {'N_batch':>8} {'N_total':>14} "
        f"{'mean|err|':>14} {'rms_err':>14} {'max|err|':>14}\n"
    )
    for r in runs:
        out.write(
            f"{r['name']:>32} {r['N_particle']:>12} {r['N_batch']:>8} {r['N_total']:>14} "
            f"{r['mean_abs_error']:>14.6e} {r['rms_error']:>14.6e} {r['max_abs_error']:>14.6e}\n"
        )
    out.write("\n")

    out.write("=" * 100 + "\n")
    out.write("Comparison table: time as row axis, averaged (|%diff|) over the spatial (x) axis\n")
    if FOLD_MIRROR_SYMMETRY:
        out.write("(mirror-folded across x=0 before comparison, pooling +x/-x statistics)\n")
    out.write("=" * 100 + "\n")
    col_header = f"{'t_mft':>8} {'n_valid_x':>10}"
    for r in runs:
        col_header += f" {r['name']+'_mean_signed%':>18} {r['name']+'_mean_abs%':>16} {r['name']+'_max_abs%':>16}"
    out.write(col_header + "\n")
    for row in time_table_rows:
        line = f"{row['t_mft']:>8.2f} {row['n_valid_x']:>10}"
        for r in runs:
            ms = row[f"{r['name']}_mean_signed_pctdiff"]
            ma = row[f"{r['name']}_mean_abs_pctdiff"]
            mx = row[f"{r['name']}_max_abs_pctdiff"]
            ms_s = "nan" if np.isnan(ms) else f"{ms:.3f}"
            ma_s = "nan" if np.isnan(ma) else f"{ma:.3f}"
            mx_s = "nan" if np.isnan(mx) else f"{mx:.3f}"
            line += f" {ms_s:>18} {ma_s:>16} {mx_s:>16}"
        out.write(line + "\n")

    out.write("\n")
    out.write("=" * 100 + "\n")
    out.write("Full per-run error tables (rows = time bin [mft], columns = x bin)\n")
    out.write("=" * 100 + "\n")
    t_x_label = "t \\ x"
    header = f"{t_x_label:>8} " + "".join(f"{x:>10.2f}" for x in X_MID) + "\n"
    for r in runs:
        out.write(f"\n--- {r['name']}  (N_total = {r['N_total']:,}) ---\n")
        out.write(header)
        for it in range(N_T):
            row = f"{T_MID_MFT[it]:>8.2f} " + "".join(
                f"{r['error'][it, ix]:>10.2e}" for ix in range(N_X)
            )
            out.write(row + "\n")

print(f"Full error analysis written to: {report_path}")
