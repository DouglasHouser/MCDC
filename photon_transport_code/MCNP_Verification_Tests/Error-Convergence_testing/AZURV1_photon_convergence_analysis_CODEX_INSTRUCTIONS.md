# Codex Task: Rebuild the AZURV1 Photon Convergence Analysis

Follow this file as a single implementation prompt. Do not merely describe the changes. Create a new runnable Python script named `AZURV1_photon_convergence_analysis_codex.py`.

## Starting point

Use `AZURV1_photon_convergence_analysis_claude_rework.py` as the starting point if it is available. Reuse the existing code that is already correct rather than rewriting the benchmark unnecessarily.

The goal is a focused convergence-analysis script for the HDF5 outputs produced by `AZURV1_photon_v3.py`.

The final script must produce **only these three primary PNG outputs**:

1. `AZURV1_photon_relative_error_convergence.png`
2. `AZURV1_photon_absolute_error_convergence.png`
3. `AZURV1_photon_sdev_convergence.png`

Do not modify `AZURV1_photon_v3.py`.

---

## A. Things that are already correct — DO NOT CHANGE

### 1. Photon benchmark physics

Keep:

```python
C_SCATTERING_RATIO = 0.5
```

Do not change the photon benchmark to the neutron benchmark's critical `c=1`.

### 2. Photon time conversion

Keep:

```python
SPEED_OF_LIGHT = 29.9792458  # cm/ns
```

The photon tally time is stored in ns. Convert to Ganapol mean-free-time with:

```python
t_mft = t_ns * SPEED_OF_LIGHT
```

Do not replace this with an unrelated time conversion.

### 3. HDF5 input discovery

Keep the existing mechanism that searches in the same directory as the analysis script, approximately:

```python
FILE_GLOB_PATTERN = "AZURV1_photon*.h5"
```

Read `N_particle` and `N_batch` from each HDF5 file and calculate:

```python
N_total = N_particle * N_batch
```

Sort runs by `N_total`. Do not determine the history count solely from the filename.

### 4. Mesh consistency

Keep the existing check that every HDF5 run has the same x and time tally meshes. Raise a clear error if they do not match.

### 5. Bin-averaged analytical reference

This is critical and is already correct.

Keep the existing `analytical_flux_bin_averaged()` implementation and use it to construct `PHI_TRUE`.

Do NOT replace the reference with midpoint/point evaluation.

The benchmark reference must be the space-time cell average:

```text
phi_bar[k,j] =
1/(Delta_t Delta_x) *
integral over cell of phi(x,t) dx dt
```

The official MC/DC AZURV1 documentation uses this bin-averaged reference.

### 6. dx normalization

Keep:

```python
APPLY_DX_CORRECTION = True
```

and the existing:

```python
flux_mean = flux_mean / dx[None, :]
flux_sdev = flux_sdev / dx[None, :]
```

Do not remove this correction or add another spatial normalization.

### 7. Existing analytical machinery

Keep the existing Ganapol implementation, Gauss-Legendre quadrature, `N_QUAD`, `Q_SUB`, causal-front treatment, and `c=0.5` formulation unless a concrete bug is found.

### 8. N^(-1/2) reference line

The current convergence script already has the Monte Carlo `1/sqrt(N)` reference line. **Do not remove it.**

Retain the existing style of anchoring the line to a real data point and scaling as:

```text
error proportional to N^(-1/2)
```

It must be present on the relative-error convergence plot and the sdev convergence plot.

### 9. Mirror symmetry

Keep:

```python
FOLD_MIRROR_SYMMETRY = False
```

Do not enable mirror folding automatically. Preserve +x and -x separately so asymmetries can expose transport/sampling bugs.

---

# B. Required changes

## 1. Make relative space-time flux error the PRIMARY accuracy metric

The official AZURV1 result is presented as a **relative space-time flux error**.

For every valid space-time cell calculate:

```python
relative_error = abs(flux_mean - PHI_TRUE) / abs(PHI_TRUE)
```

Then calculate the global metric as the arithmetic mean over valid cells:

```python
mean_relative_error = np.mean(relative_error[valid_relative])
```

Use this as the y-value of:

`AZURV1_photon_relative_error_convergence.png`

Plot it against total histories on log-log axes.

This is the primary convergence result.

---

## 2. Robust relative-error validity mask

Define a configurable small threshold near the top:

```python
RELATIVE_ERROR_FLOOR = 1e-12
```

Use a mask such as:

```python
valid_relative = (
    np.isfinite(PHI_TRUE)
    & (np.abs(PHI_TRUE) > RELATIVE_ERROR_FLOOR)
)
```

Do not include:

- NaN analytical values
- exact zero analytical values
- numerically insignificant reference values

in the relative-error average.

Never divide by zero and never turn zero-reference cells into zero relative error.

---

## 3. Correct treatment of t=0

This distinction is mandatory.

The pointwise Green's function has the singular term:

```text
exp(-t)/(2t)
```

so an analytical point value at exactly `t=0` must not be used.

However, the official AZURV1 methodology uses a **finite space-time bin average**.

Therefore:

- Do not evaluate the pointwise solution at `t=0` for the comparison.
- Do not allow a singular t=0 point into the error calculation.
- Do NOT automatically delete the entire first `[0,1]` mean-free-time bin.
- Retain `[0,1]` if `analytical_flux_bin_averaged()` provides its finite cell average.
- If the existing bin-average routine cannot robustly handle `[0,1]`, fix the bin integration rather than discarding the cell.

In short:

```text
point value at t=0       -> invalid/singular
finite [0,1] cell average -> valid comparison quantity
```

This is an important correction to a simplistic "drop the first time bin" approach.

---

## 4. Retain global mean absolute error as a SECOND metric

Keep:

```python
absolute_error = abs(flux_mean - PHI_TRUE)
```

and compute its mean over an appropriate valid analytical region.

Produce:

`AZURV1_photon_absolute_error_convergence.png`

Use total histories on the x-axis and mean absolute error on the y-axis, both logarithmic.

This is a secondary diagnostic. Do not use it instead of relative error.

An N^(-1/2) reference line may be retained here if the current plotting infrastructure already supports it.

---

## 5. Retain MC/DC statistical uncertainty as the THIRD metric

Keep reading:

```text
tallies/tracklength_tally_0/flux/sdev
```

and apply the same dx normalization as the flux mean.

Compute the mean MC/DC statistical standard deviation over a clearly defined valid tally/comparison region.

Produce:

`AZURV1_photon_sdev_convergence.png`

Use total histories on the x-axis and mean sdev on the y-axis, both logarithmic.

Keep the existing `1/sqrt(N)` reference line.

This plot is the independent test of statistical Monte Carlo convergence.

---

# C. Time-resolved error analysis is REQUIRED internally

Even though only three PNGs should be produced, calculate relative and absolute error **for each time bin before collapsing to global values**.

For each time index `it`, calculate approximately:

```python
mean_relative_error_by_time[it] = mean(
    relative_error[it, valid_x]
)
```

and:

```python
mean_absolute_error_by_time[it] = mean(
    absolute_error[it, valid_x]
)
```

using the same validity rules.

This prevents the global result from hiding a problem at a particular time.

Do not create a fourth plot.

Instead, print a concise time-resolved summary for the highest-history run, e.g.:

```text
t=1.0 mft: mean relative error = ...
t=2.0 mft: mean relative error = ...
...
t=20.0 mft: mean relative error = ...
```

---

# D. Causality and wavefront handling

Preserve the existing NaN treatment near the causal wavefront.

The relative-error mask must naturally exclude those NaNs.

Cells outside the causal wavefront with analytical flux exactly zero must not be included in relative-error calculations.

Do not average invalid cells as zeros.

---

# E. Convergence-order diagnostics

For each of the three metrics, calculate empirical convergence order between successive history counts:

```python
p = -np.log(E2 / E1) / np.log(N2 / N1)
```

For ideal Monte Carlo convergence:

```text
p ≈ 0.5
```

Print:

- pairwise relative-error orders
- overall relative-error order
- pairwise absolute-error orders
- overall absolute-error order
- pairwise sdev orders
- overall sdev order

This is console output only; no extra files.

---

# F. Highest-history diagnostic

Find the run with the largest `N_total`.

Print:

- total histories
- mean relative error
- mean absolute error
- mean statistical sdev
- time-resolved mean relative error for every time bin

This is important because AZURV1 is transient and a global average can hide time-dependent problems.

---

# G. Interpretation safeguards

Do not claim that increasing histories must eliminate every discrepancy.

If statistical sdev follows approximately `N^(-1/2)` but the relative/absolute error flattens, report that the result may be limited by a systematic error, normalization issue, or discretization/reference issue rather than statistical noise.

Do not "fix" a flat convergence curve by changing the analytical solution without evidence.

---

# H. Remove legacy outputs

The new script should NOT create the old:

- `AZURV1_photon_comparison_table.csv`
- `AZURV1_photon_error_analysis.txt`
- full per-run error grids
- old comparison tables
- extra legacy plots

The final analysis should produce exactly the three requested primary PNGs plus console diagnostics.

---

# I. Plot requirements

Use the existing plot style where practical.

All plots should:

- use log-log axes
- have clear axis labels
- have legends
- have grid lines
- use `tight_layout()`
- save at approximately 150 dpi
- save beside the analysis script

Required filenames:

```text
AZURV1_photon_relative_error_convergence.png
AZURV1_photon_absolute_error_convergence.png
AZURV1_photon_sdev_convergence.png
```

---

# J. Robustness requirements

Before calculating results, verify:

1. At least one HDF5 file exists.
2. All runs have matching meshes.
3. `flux_mean.shape == PHI_TRUE.shape`.
4. `flux_sdev.shape == PHI_TRUE.shape`.
5. `N_total > 0`.
6. There are valid analytical cells.
7. Final metrics are finite.
8. No NaN/inf values silently contaminate the global results.

Use clear errors when these checks fail.

---

# K. Script location independence

Use:

```python
script_dir = os.path.dirname(os.path.abspath(__file__))
```

for both input HDF5 discovery and output PNG paths.

The script must work regardless of the user's current shell directory.

---

# L. Do NOT modify the photon transport simulation

Do not change `AZURV1_photon_v3.py`.

Do not change:

- source
- cross sections
- material
- particle type
- tally mesh
- time grid
- particle count
- batch count
- transport settings

This task is solely to rebuild the analysis script.

---

# M. Expected code structure

Organize the new script approximately as:

1. Imports
2. Configuration/constants
3. HDF5 file discovery
4. HDF5 loading
5. Mesh consistency checks
6. Time conversion
7. Existing Ganapol analytical functions
8. Existing bin-averaged analytical reference
9. Validity masks
10. Per-run error calculations
11. Time-resolved error calculations
12. Convergence-order diagnostics
13. Relative-error plot
14. Absolute-error plot
15. Statistical-sdev plot
16. Highest-history console summary

Keep physics/mathematical comments explaining why the bin average and validity masks are used.

---

# N. Final acceptance test

Do not stop after proposing code.

Actually create:

`AZURV1_photon_convergence_analysis_codex.py`

Then, if the AZURV1 photon HDF5 files are available, run it.

Confirm that it successfully creates:

```text
AZURV1_photon_relative_error_convergence.png
AZURV1_photon_absolute_error_convergence.png
AZURV1_photon_sdev_convergence.png
```

Confirm that the console reports:

- all discovered runs
- total histories
- three global metrics
- empirical convergence orders
- highest-history time-resolved relative errors

The final result must be a runnable implementation, not a plan.
