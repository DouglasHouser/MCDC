"""
Phase 2 validation script for Klein-Nishina cross-sections.

Generates plots and diagnostic output for the photon transport module
without modifying any physics code.

Run from the project root::

    python debug_cross_sections.py

Produces:
    - Log-log plot of total KN cross-section vs energy (1e-3 to 100 MeV)
    - Polar cross-section plot of differential KN vs mu at E=1 MeV
    - Console validation output (min/max, value at 0.511 MeV, NaN/negative check)
    - Numerical integration check: integral of differential vs total
"""

import math
import os
import sys

# ---------------------------------------------------------------------------
# Path fix: ensure the transport package can be found regardless of where
# this script is invoked from.  The package lives at
#   <project-root>/photon-transport-code/transport/
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
_TRANSPORT_ROOT = os.path.join(_SCRIPT_DIR, "photon_transport_code")
if _TRANSPORT_ROOT not in sys.path:
    sys.path.insert(0, _TRANSPORT_ROOT)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

try:
    from photon_transport_code.transport.physics.photon.cross_sections import (
        klein_nishina_differential,
        klein_nishina_total,
    )
    from photon_transport_code.transport.physics.photon.util import (
        CLASSICAL_ELECTRON_RADIUS,
        THOMSON_CROSS_SECTION,
    )
except ModuleNotFoundError as exc:
    print(f"\nERROR: Could not import transport module: {exc}")
    print(f"  Expected package root: {_TRANSPORT_ROOT}")
    print(f"  Current sys.path entries:\n    " + "\n    ".join(sys.path[:6]))
    sys.exit(1)

# ---------------------------------------------------------------------------
# Energy grid: 1e-3 to 100 MeV, log-spaced
# ---------------------------------------------------------------------------
N_ENERGY = 200
energies = np.logspace(-3, 2, N_ENERGY)  # MeV

# Warm up Numba JIT compilation before timing or data collection
_ = klein_nishina_total(1.0)
_ = klein_nishina_differential(1.0, 0.0)

# Compute total cross-section over the energy grid
sigma_total = np.array([klein_nishina_total(E) for E in energies])

# ---------------------------------------------------------------------------
# Validation prints
# ---------------------------------------------------------------------------
print("=" * 60)
print("Klein-Nishina Cross-Section Validation")
print("=" * 60)

sigma_511 = klein_nishina_total(0.511)
print(f"\n  Thomson cross-section (reference): {THOMSON_CROSS_SECTION:.6e} cm^2")
print(f"  KN at 0.511 MeV (alpha=1):         {sigma_511:.6e} cm^2")
print(f"  sigma/sigma_T at 0.511 MeV:        {sigma_511/THOMSON_CROSS_SECTION:.4f}  (expect ~0.431)")
print(f"\n  Energy range:  {energies[0]:.1e} to {energies[-1]:.1e} MeV")
print(f"  Sigma min:     {sigma_total.min():.6e} cm^2  (at {energies[sigma_total.argmin()]:.1f} MeV)")
print(f"  Sigma max:     {sigma_total.max():.6e} cm^2  (at {energies[sigma_total.argmax()]:.1e} MeV)")

# NaN / negative check
n_nan = int(np.sum(np.isnan(sigma_total)))
n_neg = int(np.sum(sigma_total < 0.0))
print(f"\n  NaN values:      {n_nan}  (expect 0)")
print(f"  Negative values: {n_neg}  (expect 0)")

if n_nan == 0 and n_neg == 0:
    print("  [PASS] All cross-section values are finite and positive.")
else:
    print("  [FAIL] Unexpected NaN or negative values found.")

# ---------------------------------------------------------------------------
# Optional: numerical integration check at E = 1 MeV
# ---------------------------------------------------------------------------
E_CHECK = 1.0
N_MU = 10_000
mu_vals = np.linspace(-1.0, 1.0, N_MU)
ds_vals = np.array([klein_nishina_differential(E_CHECK, mu) for mu in mu_vals])

sigma_numerical = 2.0 * math.pi * np.trapz(ds_vals, mu_vals)
sigma_analytic  = klein_nishina_total(E_CHECK)
rel_err = abs(sigma_numerical - sigma_analytic) / sigma_analytic

print(f"\n  Integration check at {E_CHECK} MeV:")
print(f"    Numerical (2*pi * int dS/dOmega dmu): {sigma_numerical:.6e} cm^2")
print(f"    Analytic (KN total):               {sigma_analytic:.6e} cm^2")
print(f"    Relative error:             {rel_err*100:.4f}%")

print("=" * 60)

# ---------------------------------------------------------------------------
# Plot 1: Total KN cross-section vs energy (log-log)
# ---------------------------------------------------------------------------
fig1, ax1 = plt.subplots(figsize=(8, 5))

ax1.loglog(energies, sigma_total, "b-", linewidth=2, label="Klein-Nishina (free electron)")
ax1.axhline(THOMSON_CROSS_SECTION, color="gray", linestyle="--", linewidth=1,
            label=f"Thomson limit ({THOMSON_CROSS_SECTION:.3e} cm²)")
ax1.axvline(0.511, color="orange", linestyle=":", linewidth=1,
            label="0.511 MeV ($m_e c^2$)")

# Annotate the value at 0.511 MeV
ax1.scatter([0.511], [sigma_511], color="orange", zorder=5, s=50)
ax1.annotate(
    f"σ = {sigma_511:.3e} cm²\n(σ/σ_T = {sigma_511/THOMSON_CROSS_SECTION:.3f})",
    xy=(0.511, sigma_511),
    xytext=(1.5, sigma_511 * 1.4),
    fontsize=8,
    arrowprops=dict(arrowstyle="->", color="orange"),
    color="orange",
)

ax1.set_xlabel("Photon Energy (MeV)", fontsize=12)
ax1.set_ylabel("Cross-section per electron (cm²/electron)", fontsize=12)
ax1.set_title("Klein-Nishina Total Cross-Section vs Energy", fontsize=13)
ax1.legend(fontsize=9)
ax1.grid(True, which="both", alpha=0.3)
ax1.set_xlim(energies[0], energies[-1])
fig1.tight_layout()

# ---------------------------------------------------------------------------
# Plot 2: Differential KN vs mu at E = 1 MeV
# ---------------------------------------------------------------------------
mu_plot = np.linspace(-1.0, 1.0, 500)
ds_plot = np.array([klein_nishina_differential(E_CHECK, mu) for mu in mu_plot])

fig2, ax2 = plt.subplots(figsize=(8, 5))

ax2.plot(mu_plot, ds_plot, "r-", linewidth=2, label=f"E = {E_CHECK} MeV")
ax2.axvline(0.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.6,
            label="90° scatter (μ=0)")

# Thomson limit (very low energy reference shape)
r_e = CLASSICAL_ELECTRON_RADIUS
ds_thomson = 0.5 * r_e**2 * (1.0 + mu_plot**2)
ax2.plot(mu_plot, ds_thomson, "k--", linewidth=1, alpha=0.5,
         label="Thomson limit (low E)")

ax2.set_xlabel("cos(theta)  (mu)", fontsize=12)
ax2.set_ylabel("dS/dOmega  (cm^2/sr/electron)", fontsize=12)
ax2.set_title(f"Klein-Nishina Differential Cross-Section at E = {E_CHECK} MeV", fontsize=13)
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(-1.0, 1.0)
fig2.tight_layout()

# ---------------------------------------------------------------------------
# Render plots
# ---------------------------------------------------------------------------
plt.show()
