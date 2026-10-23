# Closing the bench3 Gap in Coupled Photon–Electron Transport

Work branch: `feature/photon-electron-coupling` (tip `554e3f98`) · Reference: `bench3.out` (MCNP6.3, `mode p`, TTB on, 10⁶ histories) · Written 2026-10-23

Companion to `photon_electron_coupling_plan.md`.
That plan ends at the bench3 check (its §5).
This document records why the check fails and how to close the gap.

> **Decision needed before any code.** Both fixes below reverse a standing decision in `photon_electron_coupling_plan.md` §1:
> - the bremsstrahlung spectrum is listed there as a refinement that waits for a request (§4.3);
> - positrons are listed as **not added**.
>
> This document is the plan only. Nothing here is implemented until the user asks for each step.

---

## 1. Conclusion

The gap has **two causes, and both are needed to close it**.
Missing positrons, the original suspect, explain most of the missing bremsstrahlung **energy**.
They do not explain the missing **flux**, which is what bench3 measures.

| Cause | What it removes | Share of the gap |
|---|---|---|
| **A. One mean-energy bremsstrahlung photon per event** (`sample_bremsstrahlung`) | The hard photons. Every bremsstrahlung photon is about 2.5 % of the electron energy (≈ 100 keV at 4 MeV) and is absorbed within about 0.2 mm of lead, so almost none of the radiated energy reaches shell 2 or beyond. | Most of the **flux** gap in shells ≥ 2. Fixing it alone recovered 46–72 % of MCNP's bremsstrahlung flux increase in a local experiment. |
| **B. No positron slowing-down** (`pair_production`) | The positrons' bremsstrahlung. Their 3.71 MeV per source is deposited at the pair site with no radiation. | About 0.7 of the 0.98 MeV per source of missing bremsstrahlung **energy**. It only becomes flux once A is fixed. |

Confidence that A and B together cause the gap, and that no third cause of similar size exists: **above 95 %**.
The evidence is in §2.
The one remaining uncertainty is how much each contributes in the deep shells; step 0 of §4 measures that directly and costs no production code.

**Why positrons alone would not close it.**
With the current mean-energy sampling, adding positrons adds about 0.7 MeV per source of ≈ 100 keV photons.
They are born where the positron is, a few mm from the pair site, and absorbed within a fraction of a mm.
Shell 1 would rise a little; shells 3–8 would barely move, because the coupled run today already radiates 1.30 MeV per source and recovers only 1–29 % of MCNP's increase there.

---

## 2. Evidence

### 2.1 What the code does

- **Bremsstrahlung** (`mcdc/transport/physics/electron/native.py::sample_bremsstrahlung`):
  - `dE = evaluate_eloss(E, ...)` reads EPRDATA14 BREML (MT-527 `energy_loss`), the **mean** photon energy per event.
  - Exactly one photon of energy `dE` is banked, along the electron direction.
  - No photon energy distribution is loaded or sampled.
- **Pair production** (`mcdc/transport/physics/photon/native.py::pair_production`):
  - The full pair kinetic energy `E − 2mc²` is added to the deposit, and only the electron's Bethe–Heitler share is banked back out.
  - The positron's share stays in the deposit; the two 511 keV photons start at the pair site.
  - Nothing ever produces bremsstrahlung from the positron.

### 2.2 How hard the bremsstrahlung photons are

Mean photon energy per event from the regression `Al.h5` BREML table (the generated Pb table gives about 0.03·E, per the handoff):

| Electron energy | Mean photon energy | k/E |
|---|---|---|
| 1 MeV | 24 keV | 0.024 |
| 2 MeV | 48 keV | 0.024 |
| 4 MeV | 100 keV | 0.025 |
| 9 MeV | 239 keV | 0.027 |

The mean is small because the cross section counts every soft photon; the spectrum goes as roughly 1/k, so **the radiated energy is spread almost evenly in k from 0 to T**.
About half of it is in photons above T/2, which is MeV-range for the pair electrons and positrons in this problem.

Photon mean free paths in Pb (11.34 g/cm³, NIST XCOM μ/ρ):

| Photon energy | μ/ρ (cm²/g) | Mean free path |
|---|---|---|
| 100 keV | 5.55 | 0.16 mm |
| 240 keV | ≈ 0.85 | ≈ 1 mm |
| 2 MeV | 0.046 | 1.9 cm |
| 4 MeV | 0.042 | 2.1 cm |

A 2 cm shell is one mean free path for a hard bremsstrahlung photon and over 100 for the mean-energy one.
So with mean-energy sampling, the radiated energy is right on average but never leaves the shell it is born in.

### 2.3 Energy balance per source photon

| Quantity | MCNP bench3 | MC/DC coupled (mean dE) | MC/DC + spectrum (local experiment) |
|---|---|---|---|
| Bremsstrahlung energy (MeV) | 2.28 | 1.30 | 1.50 |
| Bremsstrahlung tracks | 14.0 (> 1 keV) | 28.5 | 11.2 |
| Pair events | 0.895 | 0.844 | 0.923 |
| 1st fluorescence | 6.48 | 9.6 | — |
| Collisions | 29.3 | 46.8 | — |

- **Positron estimate.** MC/DC's radiative yield for 4.18 MeV electrons in Pb is 18.8 %, close to NIST ESTAR. Applied to the positrons' 3.71 MeV per source, that is about 0.70 MeV of bremsstrahlung, or about 0.6 MeV allowing for the positron's slightly lower radiative stopping power.
- **Closure.** 1.50 (electrons, spectrum) + 0.6–0.7 (positrons) + the extra pair production the positrons' hard photons cause ≈ 2.1–2.3 MeV, against MCNP's 2.28. No third mechanism is needed to close the energy.
- **The excess counts point the same way.** MC/DC makes twice MCNP's bremsstrahlung tracks, 50 % more fluorescence and 60 % more collisions. That is the signature of energy emitted as many soft photons that photo-absorb in place, which is cause A.
- **Electron transport itself is fine.** The 18.8 % radiative yield matches ESTAR, so the electrons radiate the right total energy; the problem is how it is split into photons.

### 2.4 Shell flux

| Shell | Uncoupled ÷ bench3 | Coupled (mean dE) ÷ bench3 | Coupled + spectrum ÷ bench3 |
|---|---|---|---|
| 1 | 0.69 | 0.82 | 0.91 |
| 2 | 0.49 | 0.58 | 0.79 |
| 3 | 0.23–0.40 (shells 3–8) | 0.32–0.48 (shells 3–8) | 0.70 |
| 4–8 | | | 0.64–0.74 |

- Photon-only physics is already verified against `bench3-nobrem`: shells 1–7 at 0.98–1.04, matching collisions and pair counts. The whole gap is therefore in the charged-particle → photon path.
- The spectrum alone moved shells 2–8 by far more than the 1.30 MeV of mean-energy bremsstrahlung did. Positrons would add about 45 % more radiated energy with the same hard spectrum, which is about the size of the remaining 0.26–0.36 deficit in shells 3–8.
- These coupled numbers come from 1,000 histories, so the deep-shell ratios carry several percent of statistical noise. That does not change the ordering.

### 2.5 Ruled out

- **Photon transport and cross sections:** verified by the no-bremsstrahlung comparison above.
- **Pair-electron sampling:** pair events and annihilation counts agree within the expected change; the Bethe–Heitler split only redistributes energy between e⁻ and e⁺, both of which are at the pair site.
- **Photoelectric energy bug:** fixed in `554e3f98`. It was below 0.3 keV per event.
- **Emission point and angle:** TTB emits at the electron's birth site; MC/DC emits along a track that is at most about 5 mm long in Pb. Both use the electron's direction. Only shell 1 could notice.
- **Cutoffs:** MCNP loses 0.0025 MeV per source to the 1 keV cutoff.
- **Electron-impact X-rays:** absent on both sides (bench3 reports "electron x-rays 0").

---

## 3. Fix design

### 3.1 Fix A: sample the bremsstrahlung photon energy

**Data.**
- EPRDATA14 carries the photon energy distribution as the BREMI (incident energies) and BREME (outgoing photon energy distributions) blocks.
- Add them to `tools/data_library_generator/electron/generate.py` under the existing `electron_reactions/bremsstrahlung/MT527` group, as a tabulated distribution, e.g. `photon_energy/{energy, offset, value, pdf, cdf}`. Follow whatever layout the photon library already uses for tabulated distributions; check ACEtk's eprdata accessor names before writing the generator.
- Regenerate Pb and Al in WSL (`~/mcdc_coupling/electron_lib/`) and rebuild the coupled Pb library (regression `Pb.h5` plus `electron_reactions`).
- The regression `Al.h5` has no such block. The loader must treat it as optional, and the old mean-energy path stays as the fallback when it is absent.

**Loader.** `mcdc/object_/electron_reaction.py`: read the optional block into the bremsstrahlung reaction as a `data` ID, as BREML is today.

**Sampling.** In `sample_bremsstrahlung`, only on the photon-active path:
1. Sample k from the tabulated distribution at E, interpolating between the bracketing incident energies by the usual statistical (stochastic) interpolation.
2. If `E − k` falls to or below `ELECTRON_CUTOFF_ENERGY`, deposit the residual and kill the electron, as the current cutoff branch does.
3. The electron loses k, not `dE`.
4. Bank the photon if k > `PHOTON_CUTOFF_ENERGY`, else deposit it.

The photon-inactive path keeps `dE`, so electron-only runs stay bit-identical. The photon-active path draws one or two more random numbers per event, which is allowed: no regression covers coupled runs except `photon_electron_al_spheres`, whose answer is regenerated.

**Consistency check.** The mean of the sampled k must equal BREML within about 1 % at every incident energy, or the radiative yield changes. Write this as a unit test.

### 3.2 Fix B: transport positrons

**Recommended: a positron particle type that reuses electron physics.**
- Add `PARTICLE_POSITRON = 4` in `mcdc/constant.py` (and the `"positron"` name entry).
- In `mcdc/transport/physics/interface.py`, dispatch `PARTICLE_POSITRON` to the electron module in all four places (`particle_speed`, `macro_xs`, `collision_distance`, `collision`).
- In `mcdc/transport/technique.py` and the tally particle filters, treat positrons as their own type; `PARTICLE_ANY` already covers them.
- Activation: positrons are transported whenever electrons are (`is_transported(PARTICLE_POSITRON)` returns the electron setting). There is no separate user switch.
- **Annihilation at end of track.** Route the five electron kill sites in `physics/electron/native.py` (`collision`, `sample_excitation`, `sample_bremsstrahlung` and the two in `sample_ionization`) through one helper, `terminate_charged(...)`. For a positron it deposits the residual kinetic energy as now and then emits two back-to-back 511 keV photons at the current position, isotropic, when photons are transported. For an electron it does exactly what the code does today, with no extra RNG draws.
- **Pair production.** When electrons are transported, sample the positron's share `T⁺ = (1 − ε)E − mc²` from the same Bethe–Heitler draw, at the same fixed 1/γ angle on the opposite azimuth, and bank it as a positron. The annihilation photons then come from the positron's end of track instead of the pair site. When electrons are not transported, keep today's behavior (deposit T⁺, annihilate at the pair site), so photon-only runs stay bit-identical.
- **Leakage.** A positron that leaves the geometry does not annihilate.

**Physics approximations this leaves, all small for bench3:**
- Electron cross sections stand in for positron ones. The positron's radiative stopping power is a few percent to about 10 % lower than the electron's at a few MeV in Pb, and its collision stopping power slightly different, so its bremsstrahlung is slightly overestimated. Note it in the docstring; positron-specific tables can come later if a positron-sensitive benchmark needs them.
- No annihilation in flight. In Pb the in-flight fraction for a few-MeV positron is a few percent, and it would harden the annihilation photons, so ignoring it slightly underestimates deep flux.
- No Bhabha distinction in ionization. The secondary electrons come from the electron (Møller) tables.

**Alternative considered: positrons slowed down in place (TTB-style).**
Sample a thick-target bremsstrahlung yield for the positron at the pair site instead of transporting it.
It needs no new particle type, but it needs thick-target yield tables MC/DC does not have, and it would be the only TTB-style approximation in an otherwise fully transported coupling. Not recommended.

---

## 4. Order of work

| # | Step | Code | Gate |
|---|---|---|---|
| 0 | **Confirm the split** with two local hacks on the bench3 script, no commits: (a) spectrum on, positrons off (repeat the earlier experiment at 2,000+ histories); (b) spectrum on, the positron's T⁺ banked as an *electron* and annihilation left at the pair site. | Local only | (b) brings bremsstrahlung energy within 10 % of 2.28 MeV and shells 1–8 within about 10 % of bench3. If (b) still leaves shells 3–8 below 0.85, there is a third cause: stop and report before step 1. |
| 1 | Fix A: generator, loader, sampler (§3.1) | `generate.py`, `electron_reaction.py`, `electron/native.py` | Sampled-k mean = BREML within 1 %; electron-only regressions (`lockwood`, `proton_beam` and any electron cases) bit-identical; `photon_*` unchanged |
| 2 | Re-run bench3 coupled (≥ 2,000 histories) | — | Bremsstrahlung ≈ 1.5 MeV per source; shells 1–8 at roughly 0.65–0.9 of bench3, as in §2.4 |
| 3 | Fix B: positron type, `terminate_charged`, pair positron banking (§3.2) | `constant.py`, `physics/interface.py`, `technique.py`, tally filters, `electron/native.py`, `photon/native.py` | Unit tests: positron energy conservation through to the two 511 keV photons; leakage emits nothing; electron-only and photon-only runs bit-identical |
| 4 | Re-run bench3 coupled | — | Bremsstrahlung energy within 10 % of 2.28 MeV; annihilation tracks 1.79 ± stats; shell flux within 10 % of bench3 in shells 1–8, and the deep shells no longer trending low |
| 5 | `MODE P E` MCNP reference for bench3 (optional) | — | Separates MC/DC error from TTB's own approximation if step 4 lands within 10–15 % but not closer |
| 6 | Regression and docs | `photon_electron_al_spheres` answer regenerated; `particle_transport.rst`; CHANGELOG | Full regression suite in Numba mode |

Fix A goes first because it is the larger flux effect, needs no new particle type, and without it Fix B's photons stay local.

**Scope.** These are two PRs after the coupling PR (or two commits on it, if the user takes it off hold and prefers one PR): about 150 lines for Fix A (generator, loader, sampler, test) and about 250 for Fix B (type plumbing, terminate helper, pair banking, tests).

---

## 5. Pass criteria summary

| Quantity per source | bench3 | Target after both fixes |
|---|---|---|
| Bremsstrahlung energy | 2.28 MeV | 2.05–2.5 MeV |
| Bremsstrahlung tracks above 1 keV | 14.0 | within 20 % (spectrum shape and cutoff differences) |
| Annihilation tracks | 1.79 | within statistics |
| Pair events | 0.895 | within 5 % |
| 1st fluorescence | 6.48 | within 20 % |
| Shell F4, shells 1–8 | — | 0.9–1.1 × bench3 |

The remaining differences after both fixes should be TTB's own approximations (emission at birth, no transport of the electron) and the positron approximations in §3.2. A `MODE P E` reference (step 5) is the way to tell them apart.
