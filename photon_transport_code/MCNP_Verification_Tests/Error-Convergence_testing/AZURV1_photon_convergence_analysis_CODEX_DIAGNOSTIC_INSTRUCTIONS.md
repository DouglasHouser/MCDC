# Codex Task — Add Time-Resolved Error Plot and Diagnose Non-1/sqrt(N) Convergence

Follow this file as a single implementation prompt. Do not merely describe the changes. Inspect the available files, implement the requested analysis, run it against all available HDF5 results, and use the evidence to determine why the absolute- and relative-error curves do not follow the expected 1/sqrt(N) behavior.

## Files to inspect

Inspect all available versions of:

1. `AZURV1_photon_v3.py`
2. `AZURV1_photon_convergence_analysis_codex.py`
3. Every result named `AZURV1_photon_{N_histories}.h5`

Also inspect the actual MC/DC source used by the environment/repository wherever necessary, especially:
- photon speed
- particle time advancement
- track-length tally scoring
- tally normalization/finalization
- batch statistics
- HDF5 output
- photon scattering/absorption

Do not assume the cause of the convergence discrepancy. Investigate it.

---

# 1. Preserve the known-good methodology

Do not casually change these:

- `C_SCATTERING_RATIO = 0.5`
- photon speed `29.9792458 cm/ns`
- conversion from tally ns to Ganapol mean-free-time
- 201 spatial cells from -20.5 to +20.5
- 20 time cells from 0 to 20 mft
- existing Ganapol analytical solution
- existing `analytical_flux_bin_averaged()`
- `APPLY_DX_CORRECTION = True`
- no mirror folding: `FOLD_MIRROR_SYMMETRY = False`
- actual history count from HDF5 `N_particle * N_batch`

The bin-averaged analytical solution must remain the primary reference. Do not replace it with midpoint evaluation.

The pointwise solution is singular at t=0, but the finite `[0,1]` mft space-time cell average is a valid comparison quantity. Do not automatically delete the first finite cell.

---

# 2. Keep the three existing global convergence plots

Continue producing:

`AZURV1_photon_relative_error_convergence.png`

`AZURV1_photon_absolute_error_convergence.png`

`AZURV1_photon_sdev_convergence.png`

The existing `N^(-1/2)` reference-line implementation should be retained, but audit that it is anchored to the correct metric and actual data point.

---

# 3. ADD the required time-resolved relative-error plot

Create:

`AZURV1_photon_time_resolved_relative_error_convergence.png`

Use total histories on the x-axis and mean relative error over valid spatial cells at each selected time on the y-axis.

Use log-log axes.

At minimum plot:

- t = 1 mft
- t = 2 mft
- t = 5 mft
- t = 10 mft
- t = 15 mft
- t = 20 mft

For each time curve, calculate the relative error independently:

`abs(phi_MC - phi_true) / abs(phi_true)`

averaged only over valid nonzero analytical cells at that time.

Do not collapse over time before making this plot.

Use a separate `N^(-1/2)` reference line for each selected time, anchored to that time's first valid data point.

This plot is diagnostic and is intended to show whether the convergence problem occurs uniformly across the transient or only at particular times.

---

# 4. Also calculate time-resolved absolute error internally

For every time bin calculate:

`mean_absolute_error_by_time`

and retain it in memory.

Do not create another plot.

Print the values for the highest-history run.

---

# 5. Calculate robust relative error

Use a configurable threshold such as:

`RELATIVE_ERROR_FLOOR = 1e-12`

and a validity mask equivalent to:

```python
valid_relative = (
    np.isfinite(PHI_TRUE)
    & (np.abs(PHI_TRUE) > RELATIVE_ERROR_FLOOR)
)
```

Never divide by zero.

Do not treat zero analytical flux as zero relative error.

Do not include NaNs near the causal wavefront.

---

# 6. Calculate empirical convergence orders

For neighboring history levels use:

```python
p = -np.log(E2 / E1) / np.log(N2 / N1)
```

Calculate and print this for:

- global relative error
- global absolute error
- global sdev
- each selected time-resolved relative error
- each selected time-resolved absolute error

Ideal Monte Carlo behavior is approximately:

`p = 0.5`

Do not hide deviations.

---

# 7. Calculate E*sqrt(N)

For every history level calculate:

```python
error * np.sqrt(N_total)
```

for:

- relative error
- absolute error
- sdev

Print these values.

For correct 1/sqrt(N) convergence, they should approach an approximately constant value.

Also calculate this for the selected time-resolved relative errors.

This diagnostic is mandatory because it distinguishes true 1/sqrt(N) behavior from a curve that merely looks roughly similar to the reference line.

---

# 8. Audit the N^(-1/2) reference line itself

Inspect the code generating the reference line.

It should be equivalent to:

```python
reference = E0 * np.sqrt(N0 / N)
```

Verify that:

- `N0` is an actual plotted history count
- `E0` is the corresponding plotted metric
- the same metric is used on both sides
- no percent-vs-fraction mismatch exists
- no `N_particle` vs `N_particle*N_batch` mismatch exists
- the reference line is not accidentally based on sdev while the plotted curve is relative error, etc.

Do not force the data to match the reference line.

---

# 9. Audit every HDF5 history count

For every `AZURV1_photon_{N_histories}.h5`, extract:

- filename history count
- `settings/N_particle`
- `settings/N_batch`
- calculated `N_total = N_particle*N_batch`

Print:

```text
filename | filename_N | N_particle | N_batch | N_total | match?
```

The convergence x-axis must use the actual history count represented by the HDF5 result.

If any mismatch exists, investigate it before interpreting convergence.

---

# 10. Audit batch/statistical interpretation

Inspect the MC/DC implementation that creates the reported `flux/mean` and `flux/sdev`.

Determine exactly what `sdev` represents:

- history standard deviation,
- standard error of the mean,
- batch-based uncertainty,
- or another estimator.

Determine whether `N_particle*N_batch` is the correct effective sample count for the reported quantities.

Do not guess.

---

# 11. Audit tally normalization from source code

Trace the actual MC/DC code path for:

- track-length scoring
- cell-volume normalization
- time-bin normalization
- history normalization
- batch normalization
- finalization
- HDF5 writing

Verify whether the HDF5 `flux/mean` requires division by spatial `dx`.

Verify whether it requires any time-bin normalization.

Do not assume the existing `dx` correction is correct merely because it improved one result.

At the same time, do not remove it without evidence.

The final script must contain comments explaining the verified normalization.

---

# 12. Raw-vs-corrected flux diagnostic

For the largest-history result, compare:

- raw HDF5 MC flux
- dx-corrected MC flux
- bin-averaged analytical flux

at representative cells including:

- x=0, t=1 mft
- x=0, t=5 mft
- x=0, t=10 mft
- x=0, t=20 mft
- representative off-center valid cells

Print:

- raw/analytical
- corrected/analytical

This is specifically intended to detect a hidden normalization factor.

Do not modify the HDF5 data.

---

# 13. Investigate time-bin consistency

Verify mathematically that the MC tally quantity and analytical reference quantity are the same.

The analytical reference is a finite space-time cell average.

Trace the MC tally and determine whether its reported value is:

- integrated track length,
- spatially normalized,
- temporally normalized,
- history normalized,
- batch normalized.

Pay particular attention to the `[0,1]` mft cell.

Run a diagnostic comparison both:

1. including the valid `[0,1]` bin average
2. excluding the first time cell

Do not make exclusion the official methodology unless the finite-cell reference is demonstrated to be invalid.

---

# 14. Inspect valid-cell counts by time

For every time bin print:

- time
- number of valid x cells
- minimum valid analytical flux
- maximum analytical flux

This will show whether late-time relative errors are dominated by very small reference values.

---

# 15. Relative-error sensitivity study

Calculate diagnostic relative errors using:

### Baseline
Finite and `abs(phi_true) > 1e-12`.

### Stricter threshold
For example:

`abs(phi_true) > 1e-6 * max(abs(PHI_TRUE))`

### Wavefront-excluded diagnostic
Exclude cells within a configurable margin of the causal wavefront.

Do not replace the official metric with these diagnostics.

If the convergence slope changes substantially, explain why.

---

# 16. Compute L2 relative error internally

In addition to the requested mean relative error, calculate:

```python
L2_relative = sqrt(sum((MC-true)**2) / sum(true**2))
```

over valid cells.

This is diagnostic only.

If mean relative error fails to follow 1/sqrt(N) but L2 relative error does, identify whether the mean-relative metric is being dominated by low-flux cells.

Do not silently substitute L2 for the requested mean-relative metric.

---

# 17. Analyze the relative-error distribution

For the largest-history run calculate:

- median relative error
- mean relative error
- 90th percentile
- 95th percentile
- 99th percentile
- maximum relative error

Determine whether large relative errors occur mainly:

- near the wavefront
- at late times
- near x=0
- in very low-flux regions

Print the result.

---

# 18. Check spatial symmetry

The benchmark is symmetric about x=0.

With mirror folding disabled, calculate representative:

`phi(+x,t) - phi(-x,t)`

and a normalized symmetry error.

If left/right asymmetry persists as N increases, investigate photon direction/scattering sampling.

Do not fold the official convergence data.

---

# 19. Compare statistical uncertainty against actual error

For every history level compare:

- relative error
- absolute error
- sdev

Interpret the results as follows:

### If sdev ~ 1/sqrt(N) and error ~ 1/sqrt(N)
The result is statistically consistent.

### If sdev ~ 1/sqrt(N) but error plateaus
Investigate systematic bias, normalization, analytical reference, tally estimator, or transport implementation.

### If sdev does not ~ 1/sqrt(N)
Investigate sampling/batching/HDF5 interpretation first.

Do not change the analytical solution simply to improve agreement.

---

# 20. If needed, investigate the photon transport implementation

If statistical convergence is correct but error approaches a nonzero plateau, inspect `AZURV1_photon_v3.py` and the actual photon transport source for:

- photon speed
- time advancement
- scattering sampling
- direction sampling
- absorption
- particle weight
- source normalization
- source position
- source time
- energy handling
- track-length scoring

The benchmark is energy-independent and isotropic, so energy should not introduce an unintended spatial/time dependence.

Do not modify the transport code automatically. First establish evidence of a problem.

---

# 21. Verify the infinite-medium approximation

The transport input uses very large reflective boundaries.

Verify that particles cannot interact with those boundaries in a way that affects the benchmark over t=0–20 mft.

Do not change the boundaries unless evidence shows they affect the result.

---

# 22. Do not modify the raw simulation results

Do not rewrite, rescale, or edit the HDF5 files.

Do not rename them.

All corrections must occur in the analysis code.

---

# 23. Required final PNG outputs

The new analysis should create exactly four primary plots:

```text
AZURV1_photon_relative_error_convergence.png
AZURV1_photon_absolute_error_convergence.png
AZURV1_photon_sdev_convergence.png
AZURV1_photon_time_resolved_relative_error_convergence.png
```

Do not create the old CSV/text/error-grid outputs.

---

# 24. Required console diagnostics

Print:

## Run audit
filename, filename N, N_particle, N_batch, N_total, match

## Global metrics
For every run:
- N_total
- mean relative error
- mean absolute error
- mean sdev
- relative error*sqrt(N)
- absolute error*sqrt(N)
- sdev*sqrt(N)

## Convergence orders
Pairwise and overall for all three global metrics.

## Time-resolved diagnostics
For the highest-history run:
- time
- valid x cells
- mean relative error
- mean absolute error

## Selected-time convergence
For 1, 2, 5, 10, 15, 20 mft:
- empirical relative-error order

## Distribution
Median, mean, 90th, 95th, 99th percentile, maximum relative error.

## Normalization
Raw vs corrected vs analytical representative values.

## Symmetry
Representative left/right symmetry errors.

## Final diagnosis
Print:

```text
STATISTICAL CONVERGENCE: PASS / FAIL / INCONCLUSIVE
NORMALIZATION: CONSISTENT / INCONSISTENT / INCONCLUSIVE
ANALYTICAL REFERENCE: CONSISTENT / INCONSISTENT / INCONCLUSIVE
TIME BINNING: CONSISTENT / INCONSISTENT / INCONCLUSIVE
RELATIVE-ERROR METRIC: WELL-BEHAVED / LOW-FLUX SENSITIVE / INCONCLUSIVE
TRANSPORT IMPLEMENTATION: NO EVIDENCE OF BIAS / POSSIBLE SYSTEMATIC BIAS / INCONCLUSIVE
```

Then state the strongest evidence-based explanation for the deviation from 1/sqrt(N).

---

# 25. Do not force convergence

Never:

- rescale errors to make them match the reference line
- change the analytical solution just to improve convergence
- delete inconvenient history levels
- arbitrarily delete time bins
- arbitrarily change the relative-error floor
- change dx normalization without source-code evidence
- modify the simulation to make the plot look better

The purpose is to determine what is actually happening.

---

# 26. Final implementation requirements

Create/update:

`AZURV1_photon_convergence_analysis_codex.py`

Run it against every available:

`AZURV1_photon_{N_histories}.h5`

Inspect the generated plots and diagnostics.

If the investigation identifies an error in the analysis implementation, correct it in the script and rerun.

The final script must answer, using evidence:

> Why do the absolute-error and relative-error convergence curves differ from the expected 1/sqrt(N) Monte Carlo convergence line, and is the cause statistical sampling, normalization, metric choice, time/bin treatment, analytical reference, or the photon transport implementation?

Do not guess. Investigate the actual files and MC/DC implementation and report the evidence.
