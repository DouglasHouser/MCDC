# Handoff — Photon Transport Paper: Standard-Error Analysis & Figures

**Date:** 2026-10-02
**Paper:** *Implementation of Monte Carlo Photon Transport Capabilities in MC/DC Using Generative AI* (Houser, Palmer, Variansyah, Farmer)
**Draft PDF:** `C:\Users\dwhou\Downloads\Draft of Generative AI Use in Particle Transport Applications Paper.pdf`
**Spreadsheet of record (spheres):** `C:\Users\dwhou\OneDrive\Documents\For_Doug_Benchmarks 7-8-26 (version 1).xlsb`

---

## 1. What this work produced

| Deliverable | Path |
|---|---|
| Standard-error workbook (10 sheets, no charts) | `C:\Projects\MCDC\photon_standard_error_comparison.xlsx` |
| Workbook build scripts | `photon_transport_code\MCNP_Verification_Tests\error_comparison\` |
| Fig. 5 generator (Al/Pb spheres) | `...\MCNP_test_problems\plot_sphere_benchmark_comparison.py` |
| Fig. 5 updated | `...\MCNP_test_problems\v3_sphere_benchmark_comparison.png` (+ `_allshells.png` variant) |
| Fig. 6 updated (bar chart = the paper figure) | `...\Complex_M&G\1e7_results\mcdc_vs_mcnp_bars.png` |
| Fig. 6 parity plot (not in paper) | `...\Complex_M&G\1e7_results\mcdc_vs_mcnp_parity.png` |
| Archived MCNP sphere outputs | `...\MCNP_test_problems\mcnp_outputs\` |

**To rebuild the workbook:** `cd photon_transport_code\MCNP_Verification_Tests\error_comparison && python main_build.py`
It is self-contained — all inputs resolve from the repo or the `.xlsb`. Requires `pyxlsb`, `xlsxwriter`, `openpyxl`, `numpy`, `h5py`.

---

## 2. Authoritative source files — USE THESE

| Problem | Paper fig. | MC/DC file | MCNP file |
|---|---|---|---|
| Al sphere 1 MeV | 5 / Tbl I | `.xlsb` sheet `Al 1 MeV`, MC/DC 1e6 cols | `.xlsb` sheet, MCNP 1e6 cols — **no output file exists** |
| Al sphere 10 MeV | 5 / Tbl I | `.xlsb` sheet `Al 10 MeV`, MC/DC 1e6 cols | `.xlsb` sheet — **no output file exists** |
| Pb sphere 1 MeV | 5 / Tbl I | `.xlsb` sheet `Pb 1 MeV`, MC/DC 1e6 cols | `mcnp_outputs\pb_1mev_sphere_MCNP_TTBon.out` |
| Pb sphere 10 MeV | 5 / Tbl I | `.xlsb` sheet `Pb 10 MeV`, MC/DC 1e6 cols | `mcnp_outputs\pb_10mev_sphere_MCNP_nobrem.out` |
| Pb cylinder off-centre | 6 | `Complex_M&G\1e7_results\lead_finite_cylinder_2e8_results.txt` | `...\1e7_results\lead_finite_cylinder_off_center_MCNP-big.out` |
| MM slab, collimated beam | 7 | `...\1e7_results\mm_slabs_collimated_beam_results.txt` | `...\1e7_results\multi_material_slabs_collimated_beam_MCNP-big.out` |
| MM slab, mesh tally | 8 | `...\1e7_results\multi_material_slabs_mesh_tally_results.txt` | `...\1e7_results\meshtam` (FMESH4 output) |
| MM sphere, 1–10 MeV spectrum | 9 | `Convergence\mm_spheres_1to10mev_spec_1e8_results.txt` | `Convergence\multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out` |
| AZURV1 convergence | 10 | `Error-Convergence_testing\AZURV1_photon_1e2…1e9.h5` (8 files) | analytical — no MCNP |

Relative paths are under `C:\Projects\MCDC\photon_transport_code\MCNP_Verification_Tests\`.

### History counts (all verified from the files)

| # | Problem | MC/DC `N_particle × N_batch` | MC/DC total | MCNP `nps` |
|---|---|---:|---:|---:|
| 1 | Al sphere 1 MeV | 100,000 × 10 | 1×10⁶ | 1×10⁶ |
| 2 | Al sphere 10 MeV | 100,000 × 10 | 1×10⁶ | 1×10⁶ |
| 3 | Pb sphere 1 MeV | 100,000 × 10 | 1×10⁶ | 1×10⁶ |
| 4 | Pb sphere 10 MeV | — (see §4) | 1×10⁶ | 1×10⁶ |
| 5 | Pb cylinder | 20,000,000 × 10 | 2×10⁸ | 2×10⁸ |
| 6 | MM slab collimated | 10,000,000 × 10 | 1×10⁸ | 1×10⁸ |
| 7 | MM slab mesh tally | 10,000,000 × 10 | 1×10⁸ | 1×10⁸ |
| 8 | MM sphere spectrum | 10,000,000 × 10 | 1×10⁸ | 1×10⁸ |
| 9 | AZURV1 | 10×10 → 10,000,000×100 | 1×10² – 1×10⁹ | n/a |

MCNP has **no user batch count** — one continuous `nps` run. See §6 on why that matters.

---

## 3. Files that are WRONG or SUPERSEDED — do not use

| File | Problem |
|---|---|
| `Downloads\bench3.out` → archived as `mcnp_outputs\pb_10mev_sphere_MCNP_TTBon_DO_NOT_USE.out` | Pb 10 MeV **with TTB on** (13,997,927 brem tracks). Fluxes run 1.5–4.6× high; does **not** match the `.xlsb`. |
| `.xlsb` sheet `Pb 10 MeV`, MCNP **Rel Err** column | Not that problem's error column — see §4. **Replaced** in the workbook. Flux column in the same sheet is fine. |
| `Complex_M&G\1e7_results\lead_finite_cylinder_results.txt` | 1×10⁸ run, superseded by the matched `_2e8_` file. |
| `Convergence\…MCNP-1e9.out` | Name says 1e9; header reports **nps = 1×10⁸**. Still the right file to use — just know its true count. |
| `Convergence\…MCNP-1e8.out` | Name says 1e8; header reports **nps = 1×10⁷**. |
| `Convergence\mm_spheres_1to10mev_spec_1e9_results.txt` | Real 1e9 MC/DC run, but pairs with a 1e8 MCNP file. Use the `_1e8_` file instead for a matched comparison. |
| `MCNP_test_problems\10mev_pb_spheres_results.txt` | Reports 10,000 × 10 = 1×10⁵, not 1e6. `10mev_pb_spheres.py` is committed at `N_particle = 10000`. |
| `benchmark_3a…3d\*.h5` | Surface tallies for the Goldstein & Wilkins buildup benchmark — **not** the 20-shell sphere runs. |

---

## 4. The Pb 10 MeV error-column defect (resolved)

The `.xlsb`'s MCNP Rel Err column for `Pb 10 MeV` was byte-identical to the one in `Al 1 MeV` and `Al 10 MeV` (`0.0005, 0.0009, 0.0010 … 0.0021`) and could not be that problem's:

- It stayed flat at 0.05–0.21% while the flux fell **9.8 decades**.
- It quoted 0.19–0.21% relative error on three shells of **exactly zero flux** — a relative error is undefined when the mean is zero, and MCNP prints `0.0000` for an empty bin.
- A statistical test (`relerr_i/relerr_0 ≈ sqrt((φ₀V₀)/(φᵢVᵢ))`, valid for analogue track-length tallies with `imp:p=1`) gives **quoted ÷ predicted spread = 914×** for Pb 10 MeV, against 2× for the validated Pb 1 MeV control and 3× for both Al sheets. At r_in = 32 cm the flux demands ~138% error; the column said 0.18%.

**Resolution:** `pb_10mev_sphere_MCNP_nobrem.out` (nps = 1×10⁶, `phys:p j 1`, 0 brem tracks, 813,670 pair-production events) matches the `.xlsb` flux column **20/20 exactly**, identifying it as the run behind those numbers, and supplies the real error column (0.03% → 100%). The workbook now uses it.

**Both Al columns are self-consistent** with their own fluxes — the duplication between them is benign (values rounded to 4 dp inside a narrow 0.0005–0.0021 band). Only Pb 10 MeV was broken.

**Still unresolved:** the `.xlsb`'s MC/DC 1e6 **flux** column for Al 10 MeV matches no saved file (file gives 6.0037e-02 at r = 1.5, sheet says 0.067546; the σ column *does* match the 1e6 file). No 1e6 Pb 10 MeV MC/DC output exists either. User states both are genuinely 1e6 runs whose output files were not kept.

---

## 5. Current workbook results

| Sheet | Bins | MC/DC hist | MCNP hist | Mean σ% MC/DC | Mean σ% MCNP | Median ratio | Agree @95% |
|---|---:|---|---|---:|---:|---:|---:|
| Al 1 MeV | 20 | 1e6 | 1e6 | 0.232 | 0.132 | 1.658 | 5 (25%) |
| Al 10 MeV | 20 | 1e6 | 1e6 | 0.126 | 0.132 | 0.950 | 20 (100%) |
| Pb 1 MeV | 10 | 1e6 | 1e6 | 12.357 | 8.527 | 1.112 | 2 (20%) |
| Pb 10 MeV | 16 | 1e6 | 1e6 | 11.676 | 12.720 | 1.099 | 12 (75%) |
| Pb Cylinder Off-Ctr | 12 | 2e8 | 2e8 | 12.996 | 9.617 | 0.990 | 7 (58%) |
| MM Slab Collim Beam | 4 | 1e8 | 1e8 | 0.169 | 0.155 | 1.097 | 0 (0%) |
| MM Slab Mesh Tally | 200 | 1e8 | 1e8 | 1.418 | 1.413 | 0.960 | 1 (0.5%) |
| MM Sphere Spectrum | 420 | 1e8 | 1e8 | 0.903 | 2.153 | 1.006 | 186 (44%) |
| **ALL PROBLEMS** | **702** | | | | | | **233 (33.2%)** |

Plus sheet `MM Sphere by Material` — the volume-weighted aggregate actually plotted in Fig. 9.

Every matched-history problem now has a median rel-err ratio near 1.0 (0.95–1.10), i.e. the two codes achieve comparable statistical efficiency at equal history counts.

---

## 6. Conventions established — carry these forward

**Units.** `.xlsb` "Rel Err" is stored as a **fraction** despite the `[%]` header (×100 for percent). MC/DC `results.txt` "rel err [%]" is a **true percent**. The second number after each MCNP cell flux is a **fraction**.

**Error estimators differ between the codes.** MC/DC's σ is a batch-to-batch sample standard error over `N_batch` (10, or 100 for the AZURV1 1e9 run) → carries ≈ 1/√(2(B−1)) ≈ **24%** uncertainty on σ itself at B = 10. MCNP's is per-history over the full `nps` → effectively exact. Consequence: a per-bin rel-err ratio of 1.2 is not distinguishable from 1.0; use medians across bins. Note also that for fixed total histories the *magnitude* of σ is independent of the batch split — only the precision of the σ estimate depends on `B`.

**A zero-flux bin has an UNDEFINED relative error, not a zero one.** MCNP prints `0.0000` and MC/DC can print a zero sdev when all batch scores coincide. Both are excluded, symmetrically, from the workbook's means (`if m and n`). The workbook reports two forms: *paired bins* (both codes resolved) and *own resolved bins* (that code alone — independent of the other file).

**Normalisation.** Both slab problems: MC/DC scores per 1 cm² of beam, the MCNP decks use a 100 × 100 cm slab, so MCNP flux and σ are multiplied by **1.0e4** (recovered from the tally volumes / mesh header). Relative errors and z-scores are unaffected.

**Spectrum bin 1** (0.0100–0.0119 MeV) is **not comparable** — MCNP's first tally interval starts at 0 MeV, MC/DC's at 0.01 MeV. Flagged and excluded, matching the paper's own comparison script.

**Agreement test.** `z = (φ_MCDC − φ_MCNP)/sqrt(σ_MCDC² + σ_MCNP²)`; agree when `|z| ≤ 1.96`.

**Fig. 5 style** (reverse-engineered from the published PDF, reproduces the overlap colour byte-exactly): fill alpha **0.45**, edge alpha **0.70**, base `#2C73B6` (MCNP, drawn **first**), `#6FAD47` (MC/DC, drawn **second**); shells with relative error **≥ 50%** are not plotted.

---

## 7. Paper text that needs revising

1. **§3.2** — *"the MCNP simulation maintained a low statistical error, consistently below 0.2%, out to 33 cm"* (Pb 10 MeV). Unsupportable; the real error reaches **100% at 33 cm**, 46.7% at 29 cm. Also *"MC/DC only produced results to 31 cm"* now cuts both ways — MCNP's own usable range ends at 29 cm on the same 50% criterion.
2. **§3.3** — cylinder. At 2×10⁸ MC/DC now resolves region (r3,z2), so *"had a zero flux in MC/DC while particles did reach the region in MCNP"* is no longer true (now −53.2%). The *"increases to 15.5%"* figure also changes: r0,z2 is now +4.5%, and the largest differences are +23.6% (r1,z2) and +15.8% (r2,z2), both in bins with 10–23% relative error. Among well-resolved bins the max is ~2%.
3. **Fig. 9 title** — *"Matched 1e9-History Runs"* is wrong; that MCNP file is 1×10⁸. Either relabel, or regenerate against the 1e8 MC/DC file (which is what the workbook now does).
4. **Abstract** — *"roughly 55% of individual tally bins are statistically indistinguishable"*. Recomputing over all 702 comparable bins gives **33.2%**; the mesh tally (200 bins, persistent 5–12% offset) dominates. Basis for the 55% is unknown — needs reconciling or restating.
5. **Fig. 5 and Fig. 6** — replace with the regenerated versions listed in §1.
6. **Methodology** — §2.1 says secondary photons were excluded to match MC/DC, and the four Complex M&G decks do carry `phys:p j 1 j j j` (0 brem tracks, verified). But the **Pb 1 MeV sphere MCNP run has TTB ON** (1,248,836 brem tracks) and is the run behind the `.xlsb` column. Pb 10 MeV is now TTB-off. So the sphere benchmarks are internally inconsistent on this; worth either re-running Pb 1 MeV TTB-off or stating the difference.

---

## 8. Open questions / next steps

1. **Missing Al MCNP outputs.** No output file for either Al sphere anywhere in the repo or Downloads. Needed to confirm their error columns and TTB status. (Both Al columns pass the plausibility test, so this is confirmation rather than suspicion.)
2. **Al 10 MeV / Pb 10 MeV MC/DC 1e6 provenance.** See §4. Re-running `10mev_al_spheres.py` and `10mev_pb_spheres.py` at `N_particle = 100000, N_batch = 10` would close this; note `10mev_pb_spheres.py` is currently committed at `N_particle = 10000`.
3. **Pb 1 MeV TTB-off re-run** — add `phys:p j 1 j j j` to the bench4 deck for consistency with everything else (0.09 min runtime).
4. **Unexplained inner-shell deficit.** In Pb 10 MeV, r ≤ 7 cm shows a consistent **−1.5 to −2%** MC/DC deficit against 0.02–0.08% MC/DC error — tens of sigma, and now with both runs confirmed TTB-off, bremsstrahlung is ruled out. Al 10 MeV agrees in all 20 shells at ≤0.2%, so it is Pb-specific and scales with attenuation (Al 10 MeV ~0.1% < Al 1 MeV 0.5–1.3% < Pb 10 MeV 1.5–2% < Pb 1 MeV 3–8%). Candidate causes, **unverified**:
   - Cross-section library: MC/DC reads EPDL, the decks use MCNP's `.84p`.
   - Pair production: `mcdc/transport/physics/photon/data_loader.py:126` pulls `pair_production/MT-503/xs` — confirm MT-503 is the *total* and not just the nuclear-field component (MCNP includes electron-field pair production).
   - Coherent scattering, far stronger in Pb than Al.
   - **Ruled out:** annihilation photons. `mcdc/transport/physics/photon/interface.py:268` does emit both 0.511 MeV photons on pair production.
5. **AZURV1 (Fig. 10) is sound** — all eight runs verified to carry distinct `N_particle × N_batch`, distinct tally data, and errors falling as 1/√N. No action needed.

---

## 9. Verification already performed (don't redo)

- Pb cylinder: all 12 percent differences reproduce Fig. 6 exactly (at 1×10⁸; the figure has since been regenerated at 2×10⁸).
- Collimated slab: +0.32 / +0.86 / +2.29 / +8.24% reproduce all four Fig. 7 labels exactly.
- Mesh tally: difference profile peaks at 12.51% (z = 121.5 cm) and ends at 5.66% (z = 199.5 cm), matching Fig. 8.
- Spheres: flux differences reproduce Table I to printed precision; MC/DC relative errors reproduce the 66.7%, 74.33% and 100% values quoted in §3.2.
- `.xlsb` fidelity: 560 cells across the four sphere sheets re-read and compared — **0 mismatches**.
- Pb 10 MeV MCNP side vs `pb_10mev_sphere_MCNP_nobrem.out`: 40 values — **0 mismatches**.
- Cylinder MC/DC vs the 2e8 file: 32 values — **0 mismatches**.
- MM sphere spectrum MC/DC vs the 1e8 file: 960 values — **0 mismatches**.
