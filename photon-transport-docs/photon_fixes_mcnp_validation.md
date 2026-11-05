# Photon Transport Fixes and MCNP Validation

Work branch: `photon-fixes` on DouglasHouser/MCDC (tip `c0a9ddad`, based on mcdc-project/dev `b10fa476`) · Data branch: `photon-fixes` on DouglasHouser/mcdc-regression_test_data (`ea358a8`) · Reference: MCNP 6.3 with mcplib84, `mode p`, `phys:p j 1` (thick-target bremsstrahlung off) · Written 2026-11-05

This document records what the `photon-fixes` branch changes, why, and how MC/DC compares with MCNP before and after.
It covers the photon-only regression tests and the MCNP-referenced decks used to find and check the fixes.

---

## 1. Summary

MC/DC's photon-only transport disagreed with MCNP by 25–46% in the lead spectrum below 160 keV (85% in one K x-ray bin), and by about 2% in deep lead flux.
The comparison found three physics bugs, all fixed on this branch:

1. **Coherent scattering** looked up the atomic form factor at twice the right momentum transfer.
2. **Incoherent scattering** treated every electron as free. It sampled the angle from Klein-Nishina alone, ignoring the incoherent scattering function S(x, Z).
3. **Incoherent scattering** had no Doppler broadening, so every scattered photon got exactly the Compton energy.

It also found that the two slab test decks did not reproduce MCNP's materials. Their concrete was 1.4% too thin, because its weight fractions sum to 0.986 and the deck, unlike MCNP, did not renormalize them.

After the fixes:

- **12-shell 1–10 MeV spectrum deck:** cell-integrated flux matches MCNP to within −0.23% to +0.42%.
- **Lead spectral valley (112–158 keV):** moves from 0.74–0.76× MCNP to 0.99–1.01×.
- **10 MeV lead spheres:** move from 1.0229× to 1.0019× MCNP.
- **Slab regression tests at 10⁸ histories:** before the fixes the flux behind the lead was 1.4–10.5% high, with no mesh bin within 2σ. Now air agrees within statistics, and 86% of the 201 mesh bins are within 2σ (35% with the physics fixed but the old decks).

What remains is a deficit of about 1% in transmission through lead, seen in the water and concrete behind it. It comes from a difference in the libraries' tables, not a bug: MCNP's table of the incoherent scattering function ends at 8 Å⁻¹ (§5.1).

---

## 2. What changed

| Commit | Change |
|---|---|
| `604be49a` | The photon data generator writes Compton profiles (Biggs, Mendelsohn and Mann 1975, from OpenMC's `compton_profiles.h5`) into `incoherent_scattering/MT504/compton_profile`. `add_compton_profiles.py` adds them to existing libraries. |
| `57581312` | Coherent form factor looked up at x = sin(θ/2)/λ, the variable it is tabulated against, not at 2x. The capped rejection loop is replaced with an inverse-CDF sampler of F² plus a Thomson-factor rejection. |
| `0980bcd4` | Incoherent angle sampled from Klein-Nishina × S(x, Z)/Z, using the scattering function every library already carries. |
| `79aae6cf` | Doppler broadening of incoherent scattering, using MCNP's scheme (LA-UR-04-0487): shell chosen by occupancy, p_z drawn with \|p_z\| ≤ p_max, and no broadening when the shell cannot be ionized. The binding energy deposits locally. Includes the CHANGELOG entry. |
| `a1591229` | Regenerated the five photon regression answers that the physics moved. |
| `393fdced` | Restored `photon_mm_slabs_collimated` and `photon_mm_slabs_mesh` as regression cases, with MCNP-matched materials. |
| `6f7913f9` | Gave `photon_mm_spheres_spectrum` the same materials, and regenerated its answer, which moved only at round-off level. |
| `c0a9ddad` | Removed `photon_pb_spheres` and `photon_pb_cylinder_edep`. The photon-only suite is now the three multi-material cases. |

**Data branch.** `ea358a8` on `mcdc-regression_test_data` adds the Compton profiles to the 11 regression elements. Every pre-existing dataset stays bit-identical.

**Unit tests added.**
- `test_coherent_form_factor.py`: the sampled cosine follows the form-factor distribution.
- `test_klein_nishina.py`: the bound sampler follows Klein-Nishina × S(x, Z), and the Doppler momentum follows the restricted Compton profile.
- `conftest.py`: the synthetic photon library gains an S(x, Z) table, defaulting to the free-electron limit, and Compton profiles.

**Photon-only regression suite.**
- `photon_mm_slabs_collimated`: 1 MeV beam through Pb / water / concrete / air slabs. Has an MCNP reference.
- `photon_mm_slabs_mesh`: isotropic 1 MeV point source with a 201-bin depth mesh through the same slabs. Has an MCNP reference.
- `photon_mm_spheres_spectrum`: 1–10 MeV source in 5 spherical regions, with a 40-bin energy spectrum. No MCNP reference.

All three use identical atom densities:

| Material | Atoms/b-cm |
|---|---|
| Pb | 3.29558e-2 |
| water | 1.00280e-1 |
| concrete | 8.19993e-2 |
| air | 5.37076e-5 |

---

## 3. Why: the problems

### 3.1 Coherent form factor at twice the momentum transfer

**What was wrong.** The library tabulates F against EPDL's x = sin(θ/2)/λ, but the sampler looked it up at q = 2k sin(θ/2) = 2x. The pre-refactor loader converted the grid to q; the port kept the q lookup and dropped the conversion.

**Effect.**
- Every coherent event was over-peaked forward. With real Pb data, the sampled ⟨μ⟩ at 100 keV was 0.894 against the correct 0.815, 31 standard errors off.
- Acceptance fell fourfold, so 68% of 300 keV coherent events in Pb hit the 1000-attempt cap and fell back to μ = 1.
- Against MCNP the flux effect is at most 0.3% on the MeV decks. It matters below about 100 keV.

### 3.2 Incoherent scattering from free electrons

**What was wrong.** The library's incoherent cross section is Klein-Nishina integrated against S(x, Z); it matches that integral to 0.1% for Pb, Fe and O. The angle, however, was sampled from Klein-Nishina alone. That puts too many events at small momentum transfer, where binding suppresses them, so scattered photons kept too much energy.

**Effect.**
- With Pb data at 100 keV, the mean energy loss was 0.137 against the bound value of 0.149, 19 standard errors off.
- Against MCNP this produced an excess that grew with depth: 10 MeV Pb sphere flux was +1.8% over shells 3–10.

### 3.3 No Doppler broadening

**What was wrong.** A bound electron's momentum spreads the scattered energy about the Compton line. MC/DC gave every photon exactly the Compton energy, so each kinematic edge in the spectrum was a cliff.

**Effect.** In the 12-shell spectrum deck:
- Pb flux was 25–46% low just below the backscatter edge of the 511 keV annihilation photons (94–158 keV).
- It was 85% low below the single-scatter edge of the K x-rays (47–56 keV).
- It was 7% high on the edges themselves.

**Choice of scheme.** Sampling p_z over the full impulse-approximation range was tried first. It overshot MCNP by 18–48% in the deepest Pb and Fe valleys, so the MCNP scheme was kept.

### 3.4 Slab decks did not reproduce MCNP's materials

**What was wrong.**
- The MCNP decks give each material as a mass density plus weight fractions.
- The concrete fractions sum to 0.986. MCNP renormalizes them, printing 2.300 g/cm³ and 0.0820 atoms/b-cm in table 60.
- The MC/DC decks' `composition()` helper did not renormalize. It gave 0.0809 atoms/b-cm, 1.4% thin.
- MC/DC's atomic weights also put lead 0.0097% denser than MCNP.

**Effect.** The thin concrete let 4–6% too much flux into the air behind it.

**Fix.** Each slab deck now sets every material's total atom density to MCNP's table-60 value, split over elements in proportion to w_i / A_i. Against the old decks:
- concrete: +1.417%;
- lead: −0.0097%;
- water and air: below 10⁻⁵.

The spectrum test uses the same four materials. It built them with `mass_fractions`, which normalizes but left them 2×10⁻⁵ to 10⁻⁴ from MCNP's values, so it now uses the same densities.

### 3.5 Regression suite

- **Slab cases restored.** `e28ea53c` had removed the two slab cases as overlapping, but they are the only photon-only cases with MCNP references. They are restored with the corrected materials.
- **Pb cases removed.** `photon_pb_spheres` and `photon_pb_cylinder_edep` are removed, leaving three photon-only cases.
- **Energy-deposition coverage kept.** It stays covered by `test/unit/photon/test_energy_deposition.py`, `test/unit/tally/test_energy_deposition.py` and the `photon_electron_*` cases.

---

## 4. Results against MCNP, before and after

**Definitions.**
- **% diff** is (MC/DC − MCNP) / MCNP.
- **±** is the combined 1σ of both codes.
- **σ-score** is the difference divided by that combined σ.

**Run conditions.**
- MC/DC tallies are track length per source particle, divided by MCNP's cell or mesh volumes.
- MCNP's reflecting ±50 cm side walls are equivalent to MC/DC's laterally infinite slabs for total track length.
- MC/DC ran in Numba mode, at the history counts given in each table.
- MCNP ran 10⁸ histories.

### 4.1 Physics fixes, on the decks used to find them

These are from the commits' own evidence: MC/DC 10⁷ histories for the spectrum, 4×10⁶ for the Pb spheres.
Neither deck is in the regression suite now.

**12-shell 1–10 MeV spectrum** (Pb / Fe / concrete / water), MC/DC / MCNP:

| Quantity | Before (dev `b10fa476`) | After (`photon-fixes`) |
|---|---|---|
| Pb 112–133 keV | 0.738 | 1.013 |
| Pb 133–158 keV | 0.756 | 0.991 |
| Pb 47–56 keV | 0.15 | 0.990 |
| Pb 158–188 keV | 1.074 | 1.011 |
| Fe 47–56 keV | 0.63 | 1.023 |
| Cell-integrated flux, 12 shells | +0.1% to +1.0% | −0.23% to +0.42% |

**10 MeV point source in Pb spheres**, shells 1–12:

| Quantity | Before | After |
|---|---|---|
| Mean ratio, MC/DC / MCNP | 1.0229 | 1.0019 |
| Shells within 1.7σ | — | all |

What the spectrum deck still shows:
- The Pb K x-ray bins are 4–5% high. The fixes don't touch them, and the cause is unverified; see §5.3.
- Pb 94–112 keV is 11% high in the innermost shell. That bin holds about 10⁻⁵ of the peak flux.

### 4.2 `photon_mm_slabs_collimated` (10⁸ histories)

Three stages:
- **Original:** dev `b10fa476` with the original deck.
- **Physics fixed:** `photon-fixes` with the original deck.
- **Physics + materials:** `photon-fixes` with the committed deck.

| Slab | MCNP rel | Original | Physics fixed | Physics + materials |
|---|---|---|---|---|
| lead 0–5 cm | 0.01% | +0.29 ± 0.01 (+22.9σ) | −0.05 ± 0.01 (−3.8σ) | −0.04 ± 0.01 (−3.1σ) |
| water 5–25 cm | 0.06% | +1.38 ± 0.08 (+16.7σ) | −1.00 ± 0.08 (−12.8σ) | −0.97 ± 0.08 (−12.4σ) |
| concrete 25–55 cm | 0.08% | +2.96 ± 0.10 (+28.5σ) | −0.03 ± 0.11 (−0.3σ) | −1.19 ± 0.11 (−11.2σ) |
| air 55–200 cm | 0.47% | +7.98 ± 0.66 (+12.0σ) | +4.20 ± 0.67 (+6.3σ) | −1.08 ± 0.65 (−1.7σ) |

### 4.3 `photon_mm_slabs_mesh` (10⁸ histories)

Each row is the flux summed over the region. One track crosses many bins, so the bins are correlated and the region totals carry no simple σ. The bin-level check is the share of bins within 2σ.

| Region | Bins | Original | Physics fixed | Physics + materials |
|---|---|---|---|---|
| backing air −1–0 cm | 1 | +0.18% (100%) | +0.31% (100%) | +0.31% (100%) |
| lead 0–5 cm | 5 | +0.33% (0%) | −0.15% (0%) | −0.14% (0%) |
| water 5–25 cm | 20 | +1.43% (0%) | −1.00% (5%) | −0.96% (10%) |
| concrete 25–55 cm | 30 | +3.47% (0%) | +0.49% (70%) | −0.71% (80%) |
| air 55–200 cm | 145 | +10.54% (0%) | +5.92% (32%) | +0.01% (100%) |
| all 201 bins: median \|dev\| | | 10.20% | 4.98% | 0.68% |
| all 201 bins: within 2σ | | 0% | 35% | 86% |

What the physics fixes did (Original → Physics fixed, same deck):
- **Flux in every slab dropped**, by 0.3% in lead, 2.4% in water, 3.0% in concrete and 3.8% in air (collimated). Free-electron Compton without Doppler broadening, and the over-forward coherent sampling, both left scattered photons too energetic and too forward, so too many got through.
- **Mesh agreement:** the median bin deviation fell from 10.2% to 5.0%, and the share of bins within 2σ rose from 0% to 35%.
- **Water now reads low:** it went from +1.4% to −1.0%. The −1.0% left is the scattering-function truncation in MCNP (§5.1), not over-correction; emulating it brings water to 0.9999.
- **Original concrete and air:** these combined two errors, the physics and the thin concrete. The physics fixes removed about 3–5% of each; the materials change removed the rest of the air excess.

What the materials change did:
- **Air excess:** removed.
- **Concrete:** the old thin concrete had been hiding the transmission deficit that water already showed. With it corrected, concrete shows the deficit too (§5.1).

### 4.4 `photon_mm_spheres_spectrum`

This case has no MCNP reference. It is a different problem from the 12-shell deck in §4.1, so its comparison is with its own previous answer.

The materials change moved its answer only at round-off level:
- region totals: at most 0.007%;
- every energy bin: at most 0.02 of its own σ.

The physics fixes moved it as they moved every photon case (`a1591229`).

---

## 5. Remaining differences

### 5.1 About 1% transmission deficit through lead: MCNP truncates the scattering function

The two codes use the same data:
- MC/DC's EPDL (IAEA 2023/2025) and MCNP's mcplib84 agree to within 0.1%, over 10 keV–1 MeV, for H, N, O, Si, Ca and Pb.
- This holds for the incoherent and photoelectric cross sections.
- The scattering-function values match exactly at all 21 mcplib84 grid points.

**Where they differ: where the table ends.**
- **MCNP.** The mcplib84 table I(v) ends at v = 8 Å⁻¹, where Pb's scattering function has reached only 78.5 of its Z = 82. MCNP accepts a Klein-Nishina sample with I(v)/I(v_max), so beyond 8 Å⁻¹ it applies no binding suppression. At 1 MeV that is every angle above about 11°.
- **MC/DC.** MC/DC uses the full EPDL table.

**Consequence.** For the same integrated cross section, MC/DC sends slightly more lead scatters backward:
- +0.5% at 1 MeV;
- +1.1% at 0.5 MeV;
- +1.5% at 0.2 MeV.

Fe changes by 0.04% or less, and lighter elements not at all. MC/DC's angular distribution is the one consistent with the cross section both codes use.

**Test.** Emulating MCNP's truncation inside MC/DC, with acceptance S(min(x, 8))/S(min(k, 8)) and normalized concrete at 10⁷ histories, gave:

| Tally | MC/DC physics | MCNP-truncated S(x) |
|---|---|---|
| collimated water | 0.9911 (−5.1σ) | 0.9999 (−0.1σ) |
| tracks entering water | 0.9908 | 0.9995 |
| collimated concrete | 0.9873 (−5.2σ) | 0.9955 (−2.0σ) |
| mesh lead bins (mean) | 0.9958 | 1.0014 |
| mesh water bins (mean) | 0.9914 | 1.0009 |

The emulation is not on the branch. The water and concrete deficits in §4.2–4.3 are this effect, not a transport bug.

### 5.2 Coherent cross section: different, but flux-neutral here

- **The difference.** MC/DC's Pb coherent cross section is 2–9% above mcplib84 at 0.1–1 MeV, because the 2017 EPICS revision folds anomalous scattering factors into it. That makes the Pb total 0.2–0.6% higher.
- **Test.** Swapping in mcplib84's coherent cross sections moved no flux by more than 0.02%.
- **An inconsistency, not fixed.** MC/DC samples the coherent angle from F² alone, so its coherent cross section and its coherent angular distribution are slightly inconsistent.

### 5.3 Small lead residuals, not investigated

| Residual | Size |
|---|---|
| Pb source-cell flux | +0.13% |
| Pb collisions | +0.4% |
| Photons leaving the Pb front face | +1.5% |
| Pb K x-ray bins in the spectrum deck | +4–5% |

Fluorescence is the likely source: MC/DC runs the full EADL relaxation cascade, while MCNP uses a simplified K/L model. This is not tested.

---

## 6. Verification on the branch

All on `photon-fixes` at `c0a9ddad`, with the data branch at `ea358a8`. The runs used the `mcdc-upstream` environment.

| Check | Result |
|---|---|
| `python -m pytest test/unit` (Python, then Numba mode) | 566 passed in each mode |
| `python -m pytest test/regression --mode python` | 35 passed |
| The three photon-only cases in Numba mode | pass; largest relative difference from the Python-mode answers: collimated 0, mesh 2.1×10⁻¹⁴, spectrum 5.0×10⁻¹⁴ |
| `black --check` on the changed Python files | clean |
| Data branch, every pre-existing dataset | bit-identical |

**Regression answers that moved.**
- `a1591229` regenerated five photon answers that the physics moved.
- `393fdced` added answers for the two restored slab cases.
- `6f7913f9` regenerated `photon_mm_spheres_spectrum` for the materials change; it moved by at most 0.007% (§4.4).

All regenerated answers are Python-mode outputs at the deck defaults (1000 × 2).

**Not run:** the full regression suite in Numba mode, MPI runs, and GPU.

---

## 7. Related work not in this branch

- **Photon collision and capture tally scores are always zero.** Track-length `collision` and `capture` pass neutron reaction codes for every species (`mcdc/transport/tally/score.py`), so photon tallies of these scores read zero. This is upstream issue #583. A separate fix exists, uncommitted, on `claude/optimistic-almeida-60024d`. It doesn't affect any flux result here.
- **Data format.** On 2026-11-04 the upstream `mcdc-regression_test_data` main switched to a new `mcdc-data` format (`photon-X.h5` plus `atoms.h5`). No public MC/DC branch reads it yet, so the Compton-profile data branch will need porting.

---

## 8. Reproducing

**MCNP references:**
- `multi_material_slabs_collimated_beam_MCNP-big.out`
- `multi_material_slabs_mesh_tally_MCNP-big.out` with its `meshtam`
- `multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out` (nps 10⁸)
- MCNP's photon library: `mcplib84`

**MC/DC runs.** Run the committed decks with:

```bash
python input.py --mode=numba --N_particle 1000000 --N_batch 100
```

`MCDC_LIB` must point at the `photon-fixes` data branch.

**Comparison scripts and probe decks.** The table-126 probes, the S(x)-truncation emulation and the coherent swap were kept outside the repository, in the local MCNP comparison folder.
