# Photon–Electron Coupling: Physics and Integration Plan

Branch: `feature/photon-transport` · Drafted 2026-10-19

Photons and electrons are both transported on this branch, but neither one creates the other.
Every electron a photon produces is deposited on the spot, and every bremsstrahlung photon an electron produces is dropped.
This document covers the physics of the coupling, the decisions already made, the integration plan (built on the proton→neutron coupling already merged from upstream `mcdc-project/mcdc`), and a first verification against an existing MCNP run that needs no new MCNP jobs.

---

## 1. Decisions

| Topic | Decision |
|---|---|
| Positrons | **Not added.** No positron particle type. The positron's kinetic energy is deposited at the pair site, and its annihilation stays there too (two back-to-back 511 keV photons, as now). |
| Electron-only runs | **Bit-for-bit unchanged.** When photon transport is inactive, every electron code path, including its RNG draws, stays exactly as it is today. All new electron-side behavior sits behind `settings["photon_transport"]["active"]`. |
| Photon-only runs | Same rule in reverse: when electron transport is inactive, the photon physics, its RNG draws and the 8 `photon_*` regression answers stay unchanged. |
| Bremsstrahlung | Use the bremsstrahlung reaction already in the electron module. When photons are active, the photon it already accounts for (`dE`) is banked as a transported photon instead of being dropped. No new library data is needed to start (see §4.3 for the spectral limit this leaves). |
| Triplet production | No new cross sections and no new sampling functions (see §3). |
| Activation | Follow upstream: the second species is opt-in through `simulation.settings.electron_transport.active = True` (or `photon_transport`), the same way the proton→neutron coupling turns on neutrons. Sources still turn on their own species automatically. |

---

## 2. Physics

### 2.1 Photon → electron

| Event | When it occurs | Electrons produced | Kinematics |
|---|---|---|---|
| Photoelectric | Dominant at low energy. Photoelectric and Compton are equal near 30 keV in water and near 0.5 MeV in Pb; σ ∝ Z⁴⁻⁵/E³ | One photoelectron, plus Auger electrons from the vacancy cascade | T = E − B_i. Direction follows the Sauter K-shell distribution (forward-peaked at high E). Auger energies are the non-radiative EADL transition energies already loaded into `photon_relaxation_transition_energy`. |
| Compton (incoherent) | Dominant in the mid range: about 30 keV–25 MeV in water, about 0.5–5 MeV in Pb; σ ∝ Z | One recoil electron | Free-electron Klein–Nishina (the current model): T = E(1 − ε). Direction from momentum conservation, **p**_e = **p**_γ − **p**_γ′, which gives cot θ_e = (1+κ) tan(θ_γ/2) with φ_e = φ_γ + π. |
| Pair, nuclear field (MT-517) | Threshold 2mc² = 1.022 MeV. Dominant above about 25 MeV in water and about 5 MeV in Pb; σ ∝ Z² | e⁻ (transported) and e⁺ (deposited locally) | E⁻ + E⁺ = E − 2mc². The split ε = (E⁻ + mc²)/E follows the screened Bethe–Heitler distribution (near-flat at low E, U-shaped at high E). Polar angle is roughly mc²/E. |
| Pair, electron field / triplet (MT-515) | Threshold 4mc² = 2.044 MeV; roughly 1/Z of the nuclear-field cross section | Pair plus a recoil atomic electron | See §3. |
| Coherent (Rayleigh) | Low energy, forward-peaked | None | — |

### 2.2 Electron → photon

- **Bremsstrahlung.**
  - Photon energy k runs from 0 to T, with a spectrum of roughly 1/k.
  - The ratio of radiative to collisional stopping is about ZT/800 (T in MeV).
  - The critical energy is about 610/(Z+1.24) MeV: roughly 7 MeV in Pb and 80 MeV in water.
  - Emission is forward-peaked around θ ≈ mc²/E (Tsai / Koch–Motz 2BS).
  - The current electron module removes the tabulated **mean** photon energy per event (EPRDATA14 BREML) and drops the photon.
- **Electron-impact ionization → atomic relaxation.**
  - The inner-shell vacancy relaxes by fluorescence with probability ω_K (Al ≈ 0.04, Cu ≈ 0.44, Pb ≈ 0.96), and otherwise by Auger emission.
  - It uses the same EADL relaxation tables as the photoelectric effect.
  - The current module deposits the binding energy B on the spot.
- **Positron annihilation.** Two 511 keV photons, kept at the pair site (§1).

### 2.3 Energy bookkeeping (upstream convention)

Each reaction adds the energy available to its products to `interaction_data["energy_deposition"]`.
Every **transported** product then subtracts its own energy.
A product that is not transported, whether because its species is inactive or because it is below cutoff, leaves its energy in the local deposit.
The energy-deposit tally therefore stays consistent whether or not the second species is active.

---

## 3. Triplet production: how it works with the current code

**No new cross sections are needed.**
The photon library generator already writes MT-515 (electron field, triplet) and MT-517 (nuclear field) as separate pair-production reaction groups, plus their MT-516 sum.
`Element.set_photon_data` loads both into `photon_pair_production_reactions` and sums them into `photon_pair_production_xs`.
`photon.collision` currently samples pair production from that sum and calls one `pair_production()` for either field.

**No new sampling functions are needed either.**
The recommended treatment is the one PENELOPE, EGSnrc's default and MCNP use: sample a triplet event exactly like a nuclear-field pair.
Energy is conserved either way, because the recoil electron's share (small on average) is simply folded into the pair.
Since the positron is deposited locally, the only quantity coupling actually transports is the e⁻ energy from the Bethe–Heitler split, which is the same function for both fields.

**Optional refinement, deferred:** pick MT-515 vs MT-517 by their reaction cross sections, using the same reaction loop the electron collision uses.
For MT-515, emit the recoil electron with an energy sampled from the triplet recoil distribution (Borsellino–Ghizzetti).
This would add one function and no data.
It only matters for depth-dose detail above a few MeV in low-Z media, so it waits until the verification in §5 passes.

---

## 4. Integration plan

### 4.0 Sync and shared helper

1. **Merge upstream `dev`.** The branch is 20 commits behind `mcdc-project/dev`. The incoming work includes per-particle-type weight windows (#563) and the source upgrade (#564), which coupled γ/e⁻ problems will want.
2. **Factor out the banking tail.** `physics/cross_species_production.py::produce_cross_species` combines two things:
   - yield/spectrum sampling from library products (proton-specific);
   - a generic tail: activation check → `copy_as_child` → set phase space → subtract `E·w` from the deposit → census-or-active bank.

   Move the generic tail into a helper:

   ```python
   @njit
   def bank_cross_species(product_type, E, ux, uy, uz,
                          particle_container, interaction_data_container, program):
       """Bank one kinematically determined product of another species.

       Returns False, and banks nothing, when the product's species is inactive,
       so the caller's deposit already holds its energy.
       """
   ```

   `produce_cross_species` then calls this helper, with no behavior change; `lockwood` and `proton_beam` must stay bit-identical.
3. **Fix the activation gap.** The activation check in `produce_cross_species` has no `PARTICLE_PHOTON` branch, so a photon product is currently always treated as inactive. Add the branch in the helper.
4. Callers check activation **before** drawing any random number for the product's direction. This keeps uncoupled runs bit-identical (§1).

### 4.1 Photon → electron (`physics/photon/native.py`)

Every step below runs only when electron transport is active **and** T > `ELECTRON_CUTOFF_ENERGY`; otherwise the existing local deposit stands.

1. **Compton recoil electron** (`incoherent_scattering`). T = E(1−ε). The direction comes from **p**_γ − **p**_γ′ using the already-sampled μ and azimuth, so no extra RNG draw is needed.
2. **Photoelectron** (`photoelectric`). T = E − B_i for the sampled subshell. Start with an isotropic direction, then switch to Sauter sampling in its own commit so its effect on the answers can be seen separately.
3. **Pair electron** (`pair_production`). Sample ε from Bethe–Heitler, transport e⁻ with T⁻ = εE − mc², and deposit T⁺ locally. The annihilation photons are unchanged.
4. **Auger electrons** (`relax_subshell`). Return the non-radiative transition energy and a kind flag instead of `0.0`. When electrons are active, bank the Auger electron isotropically.
   - This must not change the RNG sequence for photon-only runs. The transition draw already happens; only the banking is new.

### 4.2 Electron → photon, bremsstrahlung (`physics/electron/native.py::sample_bremsstrahlung`)

Only when photon transport is active:

- Bank a photon of energy `dE` (the tabulated mean photon energy the electron already loses).
- Its direction comes from the electron direction plus a sampled angle θ ≈ mc²/E, with 2BS or Tsai sampling as the refinement.
- Below `PHOTON_CUTOFF_ENERGY`, deposit `dE` locally instead.
- When the electron itself falls below cutoff in this event, the current code deposits `E_out` and kills the electron. That stays, and the photon is still banked.

### 4.3 Bremsstrahlung spectrum (deferred)

Using the mean photon energy is correct on average for **energy**, but it emits one photon at a single energy for each incident energy, where the true spectrum is roughly 1/k.
This shows up in:
- photon **counts**;
- the low-energy photon population that photo-absorbs and drives fluorescence;
- the shape of the flux spectrum.

The EPRDATA14 ACE file carries the photon-energy distribution (BREMI/BREME blocks).
If §5 shows a gap in the shell fluxes or the fluorescence yield, add those blocks to `tools/data_library_generator/electron/generate.py` and sample k from them, **only on the photon-active path**. That keeps electron-only runs unchanged.

### 4.4 Electron-impact relaxation (after §5)

In `sample_ionization`, when photons are active, relax the vacancy in the sampled subshell with the photoelectric relaxation tables, matching subshells by EADL designator. Emit fluorescence X-rays, plus Auger electrons since electrons are active by construction.

This is deliberately ordered **after** the bench3 check, for two reasons:
- MCNP's TTB model produces no electron-impact X-rays ("electron x-rays 0" in bench3), so this physics has to be off for that comparison to be like for like.
- When photons are inactive it stays off, preserving electron-only answers.

### 4.5 Tests

- **Energy conservation per event** (unit tests, Python mode): incident E equals local deposit plus the sum of banked product energies, for Compton, photoelectric (with and without Auger), pair, and bremsstrahlung, each with the partner species on and off.
- **Compton recoil spectrum:** a histogram of T reproduces the Klein–Nishina dσ/dT, including the Compton edge 2κE/(1+2κ).
- **Kinematics:** the momentum sum is conserved for Compton (p_γ = p_γ′ + p_e).
- **Isolation regressions:** with the partner species inactive, the `photon_*` regressions, `lockwood` and `proton_beam` match their answers bit for bit.
- **New regression** `photon_pb_spheres_coupled`: the bench3 geometry with electrons active and few particles, like the existing decks.

---

## 5. First verification against bench3 (no new MCNP runs)

`C:\Users\dwhou\Downloads\bench3.out` comes from an MCNP6.3 `mode p` run.
In `mode p`, MCNP uses its **thick-target bremsstrahlung (TTB)** approximation: every electron it would create is slowed down on the spot, and the bremsstrahlung photons it would emit are produced at its birth site, in its direction.
Coupled MC/DC transport should approach this result, which the current uncoupled code cannot.

**The problem.** It matches `test/regression/photon_pb_spheres` exactly:
- a 10 MeV isotropic point source at the origin;
- natural Pb at 11.34 g/cm³ (0.0329558 atoms/b·cm);
- 20 concentric 2 cm shells out to 40 cm;
- F4 flux in each shell;
- 10⁶ histories, 1 keV photon and electron cutoffs.

The deck title says "Al sphere"; the material is lead.

### 5.1 Reference values per source photon (MCNP, TTB on)

| Photon creation | Tracks | Energy (MeV) |
|---|---|---|
| Source | 1.0000 | 10.000 |
| Bremsstrahlung | 13.998 | 2.2825 |
| Positron annihilation | 1.7906 | 0.91503 |
| 1st fluorescence | 6.4847 | 0.34184 |
| 2nd fluorescence | 1.1323 | 0.012758 |
| Electron X-rays | 0 | 0 |
| **Total** | **24.406** | **13.552** |

| Photon loss | Energy (MeV) |
|---|---|
| Compton scatter (to recoil electrons) | 2.8437 |
| Capture (photoelectric) | 2.5759 |
| Pair production (0.89531 events) | 8.1301 |
| Energy cutoff | 0.0024825 |
| Escape | 0 |

- Photon collisions per source: 29.270.
- F4, cell 1 (r < 2 cm): 9.17948×10⁻² cm⁻² (0.05 % relative error). The flux falls to 3.24×10⁻⁷ by cell 10 and is zero beyond cell 17.

The energy balance closes: 10 + 2.2825 + 0.91503 + 0.34184 + 0.01276 = 13.552 MeV.

### 5.2 Expected size of the coupling effect

The charged particles this problem creates carry about 12.3 MeV per source:
- Compton recoil: 2.84 MeV.
- Photoelectrons and Auger electrons: 2.58 − 0.34 − 0.01 ≈ 2.22 MeV.
- Pair kinetic energy: 8.13 − 0.8953 × 1.022 ≈ 7.22 MeV.

MCNP's TTB converts 2.28 MeV of that, about 19 %, back into photons.
That is about 14 additional photons per source, and through photo-absorption it roughly multiplies the fluorescence count.
The uncoupled MC/DC run has none of this, so it should sit visibly below bench3 in total photon tracks, collisions, fluorescence counts and the inner-shell F4 fluxes.

### 5.3 Known, expected differences after coupling

1. **Missing positron bremsstrahlung (the largest).**
   - MCNP's TTB radiates from positrons too; this plan deposits them (§1).
   - Positrons carry about half of the 7.2 MeV of pair kinetic energy, roughly 30 % of the charged-particle energy, and the higher-energy part at that.
   - Expect MC/DC's bremsstrahlung energy to be **noticeably low**, plausibly a few tenths of an MeV out of 2.28.
   - Estimate it directly: record the bremsstrahlung energy that descends from **pair electrons**. With a symmetric average split, the positron contribution is about equal to it (slightly less, since a positron's radiative stopping power is a little below an electron's).
   - A coupled result plus that estimate should land near 2.28 MeV.
2. **Bremsstrahlung spectrum (§4.3).** Using the mean photon energy gets the energy right but under-counts bremsstrahlung **tracks** and the low-energy photons behind fluorescence. Compare energies first and counts second.
3. **Cutoffs.** MCNP cuts photons and electrons at 1 keV; MC/DC uses 1 eV for photons and 100 eV for electrons. Count bremsstrahlung tracks only above 1 keV. The energy effect is negligible (MCNP's cutoff loss is 0.0025 MeV).
4. **Emission point.** TTB emits at the electron's birth site; MC/DC emits along the electron track. A 10 MeV electron's CSDA range in Pb is about 5 mm, well inside a 2 cm shell, so only cell 1 might notice.
5. **Statistics.** Use the error-comparison rules from the photon paper work: MCNP's σ is a per-history estimate over all histories, while MC/DC's comes from batches. Compare medians, and exclude zero-flux bins on both sides.

### 5.4 Procedure

1. **Baseline.** Run `photon_pb_spheres` uncoupled at a production particle count and record the shell F4 values and their ratio to bench3. This is the gap coupling should close.
2. **Coupled run.** Run the same deck with `simulation.settings.electron_transport.active = True`.
3. **Production ledger** (verification script only, Python mode, no production code). Wrap the bank calls to accumulate tracks and energy per source by creating mechanism (bremsstrahlung, annihilation, 1st/2nd fluorescence, and bremsstrahlung from pair electrons), so the results line up with the §5.1 table.
4. **Pass criteria (rough).**
   - Annihilation tracks and energy and the pair loss agree within statistics. These don't depend on coupling, so they check the bookkeeping.
   - Bremsstrahlung energy plus the positron estimate is within about 10 % of 2.28 MeV.
   - Fluorescence counts and inner-shell F4 move from the baseline toward bench3, with the remaining gap explained by §5.3 items 1–2.
5. **What comes next depends on the result.**
   - If the bremsstrahlung energy agrees but counts, fluorescence or F4 shape do not → do §4.3.
   - If the energy itself is off → check the bremsstrahlung cross section and BREML before anything else.
   - Run `MODE P E` comparisons in MCNP (needed for §4.4, Sauter and triplet refinements) only after this rough check passes.

---

## 6. Order of work

| # | Step | Gate |
|---|---|---|
| 0 | Merge upstream `dev`; add `bank_cross_species` and the photon activation branch | `lockwood`, `proton_beam`, `photon_*` bit-identical |
| 1 | Compton recoil, photoelectron (isotropic), pair e⁻ | Energy-conservation and Compton-edge unit tests |
| 2 | Auger electrons from photoelectric relaxation | Photon-only regressions bit-identical |
| 3 | Bremsstrahlung photon banking (mean `dE`) | Electron-only regressions bit-identical |
| 4 | bench3 verification (§5) | Pass criteria in §5.4 |
| 5 | Sauter photoelectron direction; bremsstrahlung angle sampling | Re-run §5 |
| 6 | Bremsstrahlung spectrum (BREMI/BREME), if §5 calls for it | Re-run §5; electron-only regressions unchanged |
| 7 | Electron-impact relaxation; optional triplet recoil | New MCNP `MODE P E` runs |
