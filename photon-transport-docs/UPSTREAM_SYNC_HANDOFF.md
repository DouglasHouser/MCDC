# Photon Transport — Upstream Sync Handoff

Planning state as of **2026-10-08**. **Phase 0 is complete and pushed.** Phases 1–4 are
unstarted. Pick up at §8 "Execution".

Supersedes the 2026-09-18 and 2026-10-03 revisions. New findings in this revision are marked
**[NEW]**; corrections to a previous revision are marked **[CORRECTED]**.

**[REVISED 2026-10-08 — read this before anything else]** The 2026-10-03 revision planned the
port against `CEMeNT-PSAAP/MCDC`. **That repository is retired.** All contributions now go to
`mcdc-project/mcdc`, which is a strict superset — 303 commits ahead of CEMeNT-PSAAP's `dev` and
0 behind it when first compared, 1,060 ahead of our snapshot as of this writing. Owner decision:
**the port branches from `mcdc-project/dev`.** Everything downstream of that choice is corrected
in §1, §2.0, §5 Phase 1 and §8.

The newest of those commits land **proton transport** (PR #439), making MC/DC a
three-particle code. Two consequences, both corrected below:

1. **The 200 reaction block is taken.** `PROTON_REACTION_* = 200..203` now occupies the block
   §2.4 assigned to photon. Photon moves to the **300 block** (§2.4). `PARTICLE_PHOTON = 3`
   survives unchanged — `PARTICLE_PROTON = 2` and `PARTICLE_ANY = 100`.
2. **Proton replaces electron as the porting template.** Proton is the most recently merged
   particle and reflects current conventions most faithfully. §3, §4 and §5 Phase 2 are
   rewritten against it, and §13 is new: the complete per-file touch-list derived by
   enumerating every site upstream mentions `PARTICLE_PROTON`.

**[RESOLVED 2026-10-08]** Two items the previous revision left open are now closed by evidence
from the live tree, not by judgement:

- **§6.1 energy units — closed, and there is no upstream bug.** `object_/element.py` imports
  `read_energy` from `object_/electron_reaction.py:29`, which reads a **`unit` attribute** off
  each energy dataset and multiplies by `1e6` only when it says `"MeV"`, defaulting to eV.
  The runtime unit is eV throughout; the library stores MeV and declares it. The previous
  revision's "possible upstream bug — unresolved" was an artifact of not finding that helper.
- **§4 generator file-mode collision — closed, and needs no maintainer negotiation.** Each
  non-neutron generator writes to **its own output directory** (`MCDC_LIB_ELECTRON`,
  `MCDC_LIB_PROTON`) with mode `"w"`. Photon follows with `MCDC_LIB_PHOTON`. Mode `"a"` is
  dropped from the plan. What remains genuinely open is that **upstream ships no tool to merge
  per-particle libraries into the single `$MCDC_LIB/<symbol>.h5` that `Element` reads** — see
  §6.2.

**[NEW 2026-10-08] §14 Environment prerequisites** is new and is a hard gate on Phase 1.
`mcdc-env` (Python 3.10, numba 0.55.1, numpy 1.21.5) **cannot import the upstream tree**, which
requires Python ≥ 3.11, numba ≥ 0.61 and numpy ≥ 2.0. No revision before this one recorded that.

**[REVISED 2026-10-03]** The 2026-10-01 revision told Phase 0 to archive
`photon_transport_code/` wholesale. That was wrong — the folder holds **362 live tests** and
every verification deck, and its "1.6 GB" is almost entirely SLURM job logs. Corrected in §3,
§5 Phase 0, §5 Phase 3 and §6.3. New sections: **§9** measurements, **§10** per-file test
rewrite inventory, **§11** smoke-test references, **§12** paper-artifact policy.

**[REWRITTEN 2026-10-03] §6.3 `.gitignore`** is now a full specification — what upstream already
covers, a per-path audit with verdicts, the annotated block to append, a verification gate with
expected numbers, and the Phase 1 handover. It **corrects four rules the previous revision
proposed**: `__pycache__/` and the scoped `*.png` rule are redundant, a blanket `*.xlsx` would
delete advisor-supplied benchmark input, and a `*.slurm` rule would delete the 21 job submission
scripts. It also records that upstream does **not** ignore `*.log`, that upstream's global `*.csv`
rule is silently hiding nine files, and that the blanket `*.h5` must be kept through Phase 0.

**[OWNER DECISIONS 2026-10-03]** Two exclusions from the Phase 0 snapshot, decided by the
repo owner rather than by the §6.3 audit. The 21 `*.slurm` job submission scripts are **not**
committed, which reverses the §6.3.3 row arguing they were source worth keeping; they remain
on disk, untracked, so this is reversible. And `test/regression/azurv1/input.py` is **not**
committed — its local edits were photon experimentation and the working deck on `dev` stands.

**[OWNER DECISIONS — second round]** Four further exclusions, all ignored rather than committed,
all still on disk: **every MCNP input deck** (the five `*_MCNP.txt` files plus
`benchmark_5/Benchmark5_MCNP_Deck.txt` and `Benchmark5_MCNP_Deck_MCDC_equivalent.txt`, which do
not match the glob but are MCNP decks by their own headers) — this reverses the §12 row that
called them irreplaceable ground truth; **nine named decks and analysis scripts** under
`Complex_M&G/`; and the whole **`Complex_M&G/1e7_results/comparisons/`** folder. The snapshot is
now 199 files. The §7 deck set is intact, but its MCNP comparison targets are not in git.

---

## 1. Repo State

| Fact | Value |
|---|---|
| `origin` | `DouglasHouser/MCDC` (fork) — **the only remote we can push to** |
| **Port base** | **`mcdc-project/mcdc`** — canonical; all contributions go here **[CORRECTED 2026-10-08]** |
| `upstream` | `CEMeNT-PSAAP/MCDC` — **retired, not used for anything.** Keep or delete the remote; do not branch from it **[CORRECTED 2026-10-08]** |
| Local branch | `wip/photon-snapshot-pre-refactor` @ `c4f0cb49` — the Phase 0 snapshot, **pushed** |
| `dev` | `86ee515a` == `origin/dev`, 2 docs commits ahead of the old merge base |
| Divergence | **17 ours / 1,060 theirs** vs `mcdc-project/dev` (`295cd909`) **[CORRECTED 2026-10-08]** |
| Photon code | **committed** in the Phase 0 snapshot — 12 topical commits, 199 files |

**Remote hygiene.** Both `upstream` and `mcdc-project` were added with the same URL for fetch
and push, so a bare `git push mcdc-project …` would attempt to write to a repository we do not
own. Disarm both before Phase 1:

```bash
git remote set-url --push mcdc-project DISABLED
git remote set-url --push upstream DISABLED
```

**`mcdc-project/dev` moves daily.** It advanced from `d41bf52f` to `295cd909` inside a single
day while this revision was being written. Re-run `git fetch mcdc-project` immediately before
branching and re-check §13 against the tip you actually get — the line numbers in this document
are anchors for `grep`, not guarantees.

### Phase 0 status — done  **[NEW 2026-10-08]**

The previous revision's header said "no code has been changed yet". That is no longer true, and
**§8's first command block must not be re-run.** On `wip/photon-snapshot-pre-refactor`:

| Commit | Content |
|---|---|
| `83e8bdd9` | `.gitignore` scoped for the snapshot (§6.3.5 applied) |
| `ea4f909d` | Photon data objects + their get/set accessors |
| `805b963c` | Photon physics kernels |
| `55125f1b` | Photon wired into the shared transport core |
| `8467de01` | Constant-XS material treatment on neutron physics |
| `cdbc5bab` | Formatter churn in generated accessors — **DO NOT PORT** |
| `eac011a6` | Photon unit tests at their current paths |
| `ac23dce9` | Root validation scripts + error-analysis handoff |
| `423b4755` | The April photon prototype — superseded, reference only |
| `9db13a7d` | The 362-test photon suite |
| `ca6f2e9c` | Remaining verification decks and reference data |
| `c4f0cb49` | This document's §6.3 rewrite |

**Six files have drifted since the snapshot** and are still uncommitted. Decide their
disposition before Phase 1 branches away from this tree:

| File | State |
|---|---|
| `mcdc/transport/distribution.py` | modified — **production source**, the one that matters |
| `…/Error-Convergence_testing/AZURV1_photon.py` | modified |
| `…/Error-Convergence_testing/AZURV1_photon_convergence_analysis_CODEX_DIAGNOSTIC_INSTRUCTIONS.md` | modified |
| `…/CARRE_examples/10MeV_cubesat_model.py` | modified |
| `…/CARRE_examples/Plot_cubesat_tallies_avg.py` | modified |
| `…/CARRE_examples/10MeV_cubesat_model_old.py` | untracked |

`backup/phase0-v1` and `backup/phase0-v2` are local-only, 13 commits each off superseded
snapshot attempts, and are not pushed. They are insurance against nothing that `c4f0cb49` does
not already cover; delete them once Phase 1 is branched.

**`cdbc5bab` is now provably safe to drop.** Upstream's `pyproject.toml` carries
`[tool.black] force-exclude` over `mcdc/numba_types.py`, `mcdc/mcdc_get/` and `mcdc/mcdc_set/`,
so the generated accessors are no longer formatted at all and the churn in that commit cannot
recur.

### What changed upstream that matters

- **Electrons landed**, then **protons landed** (PR #439). MC/DC is now a three-particle code
  with a settled per-particle pattern. **Proton is the template for photons**, not electron —
  it is the most recent and therefore the most faithful to current conventions. Electron
  remains the template for one thing only: **per-element** data carried on `Element`, which is
  what photon needs (proton data hangs off `Nuclide`). **[CORRECTED 2026-10-08]**
- **`PARTICLE_PROTON = 2` and `PROTON_REACTION_* = 200..203`.** The 200 block photon was
  assigned is gone; see §2.4. **[NEW 2026-10-08]**
- **`collision_data` is now `InteractionData`.** The container is `interaction_data`, the
  object is `object_/particle.py:34`, the dtype is `numba_types.py:579`, and it carries exactly
  two fields: `energy_deposition` (float, **eV**, weight-included) and `incident_particle`
  (a saved `ParticleData`). The collision signature is
  `collision(particle_container, interaction_data_container, program, data)` — the previous
  revision's `collision_data_container` is wrong. **[CORRECTED 2026-10-08]**
- **`score.collision()` is now `score.interaction()`** — `transport/tally/score.py:128`,
  consuming `interaction_data["energy_deposition"]` at `:174`. **[CORRECTED 2026-10-08]**
- **`set_transported_particles` is gone.** Replaced by a `ParticleTransportSettings` dataclass
  per species (`settings.py:96`): `neutron_transport`, `electron_transport`,
  `proton_transport`, each with `active` and `prioritize_low_energy`. Activation is automatic
  from the source list in `simulation.py:359`. **[CORRECTED 2026-10-08]**
- **`transport/physics/cross_species_production.py` is new and matters a great deal for
  photon.** It banks secondary products of a *different* species from a reaction's
  `secondary_products` list, gated on that species' `…_transport["active"]` flag, and
  **subtracts each transported product's energy from the deposition balance**. This is the
  mechanism photon needs for photoelectrons, pair-production electrons and positrons.
  **[NEW 2026-10-08]**
- **`read_energy` (`object_/electron_reaction.py:29`) is the unit gate.** It converts MeV→eV
  based on a `unit` attribute written by the generator. Settles §6.1. **[NEW 2026-10-08]**
- **Energy deposition already exists** and is richer than the previous revision recorded:
  `SCORE_ENERGY_DEPOSITION = 200`, the `interaction_data` container, `score.interaction()`,
  `test/unit/tally/test_energy_deposition.py` and `test/unit/tally/test_interaction_tally.py`.
- Base classes renamed: `ObjectBase` / `ObjectNonSingleton` / `ObjectPolymorphic` →
  `MCDCBase` / `MCDCObject` / `MCDCPolymorphic`
- Accessor generator: `code_factory/numba_objects_generator.py` →
  `numba_layers_generator.py` (+ `rebuild_numba_support.py`, `literals_generator.py`,
  `python_objects_compiler.py`)
- **Material polymorphism deleted.** No `MaterialBase` / `MaterialMG` /
  `native_material` / `multigroup_material` / `MATERIAL_*` subtypes. One `Material` with
  `nuclide_composition` **or `element_composition`**.
- Transport arg naming: `mcdc` → `simulation` / `program`. Inside an `@njit` function the
  simulation is recovered with `simulation = util.access_simulation(program)`.
- New: `tools/data_library_generator/{neutron,electron,proton}/`
- New docs: `docs/source/developer_guide/extending/extending_the_object_model.rst`
- `.pre-commit-config.yaml` pins **black 26.1.0 / `language_version: python3.14`**, and
  `[tool.black] target-version = ["py311","py312","py313","py314"]` with `force-exclude` over
  `numba_types.py`, `mcdc_get/` and `mcdc_set/`. `[tool.pyright]` runs **strict** over
  `test/typecheck` at `pythonVersion = "3.14"`. See §14 — we have no 3.14 interpreter.
- `[tool.pytest.ini_options] testpaths = ["test/unit"]`, and `test/regression` is selected by
  path. Regression cases are **auto-discovered as directories** — see §7. **[NEW 2026-10-08]**

---

## 2. Decisions Made

0. **[NEW 2026-10-08] Port base: `mcdc-project/dev`.** `CEMeNT-PSAAP/MCDC` is retired and is
   not used for anything. `mcdc-project/mcdc` is where contributions go, and it is a strict
   superset of CEMeNT-PSAAP's history, so nothing is lost by moving. The cost is that the
   divergence to port against is 1,060 commits rather than 715 — paid once now instead of
   twice later. The Phase 4 PR targets `mcdc-project/mcdc` from a branch on `origin`.
1. **Approach: port onto upstream, do not merge.** Branch from `mcdc-project/dev` and
   hand-write the photon layer into the proton-shaped slots. 1,060 commits against whole-file
   rewrites
   of `tally.py`, `source.py`, `score.py` and `simulation.py` produces a conflict set larger
   than the code itself — and git cannot know that our `score.py` additions should be
   **discarded** rather than reconciled. Use a **side-by-side git worktree** so the old tree
   stays visible.
2. **Keep the constant-XS capability, photon-only.** `ConstantCrossSectionMaterial` becomes
   `PhotonConstantXSData` in `object_/transport_model_data.py` (mirroring
   `NeutronMultigroupData`) + a `transport/physics/photon/constant_xs.py` treatment module.
   **[CORRECTED 2026-10-08]** The precedent is `transport/physics/neutron/multigroup.py:38`
   (was `:36`), whose `applicable()` reads two fields the generator derives from `Material`:

   ```python
   material["has_neutron_multigroup"]          # bool flag
   material["neutron_multigroup_ID"]           # index into simulation["neutron_multigroup_data"]
   ```

   Photon mirrors it exactly: `has_photon_constant_xs` / `photon_constant_xs_ID` /
   `simulation["photon_constant_xs_data"]`. Dispatch goes in `physics/photon/interface.py`,
   following **neutron's** interface (which branches on `applicable()`) and **not** proton's
   (which delegates straight to `native` and leaves its own `multigroup.py` unreachable — a
   live inconsistency upstream; do not copy it). **Drop the neutron constant-XS additions**
   to `transport/physics/neutron/native.py` (snapshot commit `8467de01`) — upstream's
   one-group `Material.multigroup(...)` already covers the Case / de Hoffmann–Placzek
   benchmark.
3. **[REWRITTEN 2026-10-08, THEN RESCOPED — read §2.10 first] Energy deposition → upstream's
   container, our formulas unchanged.** Retire `SCORE_ENERGY_DEPOSIT = 13`; use
   `SCORE_ENERGY_DEPOSITION = 200` and write into `interaction_data["energy_deposition"]`
   (**eV, weight-included**) inside `native.collision(...)`.

   Upstream's model, visible in `cross_species_production.py:131`, is:

   > deposit the full available energy, then **subtract the energy of every product that is
   > actually transported** — `interaction_data["energy_deposition"] -= E_new * w`.

   **Because §2.10 scopes this PR to photon-only transport, the subtraction term is
   identically zero for every charged product, and our existing per-branch formulas port
   essentially as-is.** Upstream's architecture is adopted; upstream's cross-species
   machinery is not exercised. This is a happy accident of the design: "energy carried by a
   species whose transport is switched off stays deposited" is exactly local deposition.

   | Branch | Deposited this PR | Later, once electrons are coupled |
   |---|---|---|
   | Coherent | 0 — no energy transfer | unchanged |
   | Incoherent (Compton) | `E − E_scattered` (the electron's energy, deposited locally) | subtract the Compton electron |
   | Photoelectric | `E − Σ E_fluorescence` | additionally subtract the photoelectron |
   | Pair production | `E` minus any escaping annihilation photons | subtract e⁺/e⁻ |

   **Fluorescence photons are the one product still transported**, because they are
   same-species: `cross_species_production.py:68` explicitly `continue`s on same-species
   products, so they are banked inside `photon/native.py` and never touch
   `produce_cross_species`. The same applies to annihilation photons from pair production.
   So the only deposition subtraction photon performs in this PR is for the photons it banks
   itself — which is what our current code already does.

   **What this buys:** no `secondary_products` on photon reactions, no
   `produce_cross_species` call, and no photon arm in `cross_species_production.py` for this
   PR. Those are deferred, and §13 marks them so.

   **Delete outright:** the `tally.py` score plumbing, the 81 `score.py` lines, and
   `_score_energy_deposition` in `simulation.py` — `score.interaction()`
   (`transport/tally/score.py:128`) already consumes the container. This deletion is the whole
   of the energy-deposition work, and §7 deck 8 is its regression coverage.
4. **[CORRECTED 2026-10-08] Reaction constants use the 300 block.** Neutron is 0–6, electron
   100–104, **proton 200–203**. The previous revision assigned photon 200–204, which now
   collides with proton exactly as the local 0–4 values collide with neutron. Photon takes
   the first free block:

   ```python
   PARTICLE_PHOTON = 3            # 0/1/2 = neutron/electron/proton; 100 = PARTICLE_ANY

   PHOTON_REACTION_TOTAL = 300
   PHOTON_REACTION_COHERENT = 301
   PHOTON_REACTION_INCOHERENT = 302
   PHOTON_REACTION_PHOTOELECTRIC = 303
   PHOTON_REACTION_PAIR_PRODUCTION = 304
   ```

   The 300 block is confirmed empty on `295cd909` — no constant in `mcdc/constant.py` matches
   `= 3[0-9][0-9]`. Re-confirm on the tip you branch from; if proton has since grown a 300
   block, move photon to 400 and update §13 with it. The local 0–4 values are a real bug, not
   a style issue, because `macro_xs()` dispatches on a bare int.
5. **Merge the data library** — one element file per element carrying every particle.
   **[CORRECTED 2026-10-08]** Superseded — there is no merge step. See §6.2 for the
   `generate.py` + `util.py` plan that replaces it.
6. **8 regression decks** (see §7), migrated to the `Simulation` API **and to upstream's
   `test/regression/<case>/{input.py,answer.h5}` directory convention**. **[WAS 7 — the
   energy-deposition deck was added 2026-10-08 so that §2.3's rewritten tally has coverage.]**
7. **Library generator** goes to `tools/data_library_generator/photon/`, writing to
   `$MCDC_LIB_PHOTON` with mode `"w"`, mirroring electron and proton. **[CORRECTED
   2026-10-08]**
8. **[NEW] Data source: keep EPDL, adopt upstream's layout.** EPRDATA14 *does* carry photon
   cross sections — upstream's electron generator already opens `.14p` **photoatomic**
   tables via `ACEtk.PhotoatomicTable` and its README says "electron/photon/relaxation
   data" — but it extracts only the electron blocks and writes no `photon_reactions/` group.
   Rather than re-derive from EPRDATA14, keep our validated EPDL numbers and the finer grid
   (6,682 pts, 1 eV – 100 GeV vs EPRDATA14's ~hundreds of pts from ~1 keV) and write them
   into upstream's file layout and units. Rationale: preserves the 117-test suite, keeps the
   1 eV floor and shell-resolved PE + coherent form factors, and needs no ACEtk build.
   EPRDATA14 extraction stays available as a later cross-validation PR.
9. **[NEW] Keep our EADL relaxation data, at upstream's path.** Upstream's root-level
   `atomic_relaxation/` is richer in form (full transition tables with primary/secondary
   designators and probabilities) but is EPRDATA14-derived. Our validated fluorescence
   results depend on the EADL numbers, so write **our** data into **upstream's** schema and
   path rather than consuming theirs. See open item §6.2.
10. **[NEW 2026-10-08 — OWNER DECISION] Scope: photon-only. No electron coupling in this PR,
   and no change to the photon physics.** This is the single most load-bearing scoping
   decision in the document, and several earlier sections were written without it.

   - **Photons are not coupled to electrons.** `electron_transport.active` is irrelevant to
     this PR; a photon deck enables photon transport alone.
   - **Photoelectrons, Compton electrons, and pair e⁺/e⁻ deposit their energy locally.**
     They are not created as particles, not banked, and carry no `secondary_products` entry.
   - **The photon physics is not changed by this merge.** Klein–Nishina sampling, the
     coherent form-factor sampler, shell-resolved photoelectric selection and EADL
     fluorescence all port with their algorithms intact. What changes is where they live,
     what they are called, what units they take, and which container they write deposition
     into — **not what they compute.** A port that changes a physics result is a bug, and
     the 117 cross-section tests plus the §10 suite exist to catch exactly that.

   Consequences recorded elsewhere: §2.3 (deposition formulas port as-is), §13
   (`cross_species_production.py` arm deferred), §6.2 (a photon-only library is sufficient,
   so no cross-particle merge is needed), §6.5 (fluorescence is the only transported PE
   product, so its unit tests carry real weight).

   **Deferred to a later PR, deliberately:** `secondary_products` on photon reactions,
   `produce_cross_species` integration, the `PARTICLE_PHOTON` arm in
   `cross_species_production.py`, and any shared photon+electron element library.
11. **[NEW 2026-10-08 — OWNER DECISION] `prioritize_low_energy = False` for photon.**
   Matching neutron and proton; electron is the only species that sets `True`. So:

   ```python
   photon_transport: ParticleTransportSettings = field(
       default_factory=ParticleTransportSettings
   )
   ```

   identical to `proton_transport` at `settings.py:183`, with no `default_factory` lambda.
   Note that `simulation.py:350` currently `print_error`s if `prioritize_low_energy` is set
   on neutron or proton — **photon must be added to that guard**, or the setting will be
   silently accepted and silently ignored.

---

## 3. Target Structure

**[REWRITTEN 2026-10-08]** Derived from the proton layer on `295cd909`. §13 carries the
exhaustive touch-list with line anchors; this is the shape.

```
mcdc/constant.py                        + PARTICLE_PHOTON = 3
                                          + PHOTON_REACTION_* = 300..304   (§2.4)
mcdc/object_/photon_reaction.py         PhotonReactionBase(MCDCPolymorphic) + 4 subtypes.
                                          Template: object_/proton_reaction.py (484 lines)
                                          - label: str  + sub_type  (base = -1)
                                          - xs_offset_  NOT xs_offset  (see note below)
                                          - @classmethod from_h5_group(cls, h5_group)
                                          - module-level decode_type()
                                          - NO perform_collision — physics lives in transport/
mcdc/object_/element.py                 + photon_xs_energy_grid, photon_total_xs,
                                          photon_{coherent,incoherent,photoelectric,
                                          pair_production}_xs
                                          + photon_*_reactions lists
                                          + photon_photoelectric_subshell_binding_energy
                                          + set_photon_data(self, simulation)
                                          Template: the electron half of element.py (197 ln)
mcdc/object_/simulation.py              + photon_reactions: list[PhotonReactionBase]  (:120)
                                          + self.photon_reactions = []                (:315)
                                          + photon_constant_xs_data list
                                          + 4 edits in _finalize_compilation — see §13
mcdc/object_/transport_model_data.py    + PhotonConstantXSData(MCDCObject)
                                          Template: NeutronMultigroupData (same file)
mcdc/object_/material.py                + photon_constant_xs kwarg
                                          + has_photon_constant_xs: bool
                                          + optional Material.photon_constant_xs(...) ctor
mcdc/object_/source.py                  + "photon" -> PARTICLE_PHOTON  (:431 chain)
                                          + docstring particle_type set  (:94)
                                          + decode_particle_type arm     (:546)
mcdc/object_/settings.py                + photon_transport: ParticleTransportSettings
                                          = field(default_factory=ParticleTransportSettings)
                                          (NOT a flag; set_transported_particles is gone)
mcdc/object_/tally.py                   + "photon" particle-type FILTER (:323, :414, :82)
mcdc/transport/util.py                  + PARTICLE_PHOTON -> "photon"  (:25)
mcdc/transport/physics/util.py          + evaluate_photon_xs_energy_grid(e, element, data)
                                          Template: evaluate_electron_xs_energy_grid (:34)
mcdc/transport/physics/photon/
  __init__.py                           re-export particle_speed / macro_xs / collision
  interface.py                          ~40 lines; branches on constant_xs.applicable()
                                          Template: neutron/interface.py (NOT proton's)
  native.py                             particle_speed / macro_xs / total_micro_xs /
                                          reaction_micro_xs / collision + one section per
                                          reaction  (~550-650 lines)
                                          Template: proton/native.py (664 lines)
  constant_xs.py                        applicable / particle_speed / macro_xs / collision
mcdc/transport/physics/interface.py     + PARTICLE_PHOTON arms in FOUR functions:
                                          particle_speed, macro_xs, collision_distance
                                          (the SigmaT block), collision
mcdc/transport/physics/cross_species_production.py
                                        + PARTICLE_PHOTON arm in the transport-active gate
                                          (:69) so photon products can be banked
mcdc/code_factory/python_objects_compiler.py
                                        + PhotonReactionBase -> simulation.photon_reactions
                                          + PhotonConstantXSData branch   (:91 pattern)
tools/data_library_generator/photon/    generate.py + README.md, writing $MCDC_LIB_PHOTON
test/unit/photon/                       relocated + renamed unit tests  (§10)
test/regression/<case>/input.py         + answer.h5, one directory per deck  (§7)
```

**Not applicable to photon:** `transport/physics/condensed_interactions.py` and
`proton/condensed_interactions.py`. Condensed interactions model continuous slowing-down for
charged particles; photons have no analogue. Do not add a photon arm there.

**`xs_offset_` — the trailing underscore is mandatory.** `proton_reaction.py:52` and
`electron_reaction.py:52` both carry the comment *"`xs_offset` is reserved for `xs`"*. The
layer generator emits `<field>_offset` and `<field>_length` for every array field, so a field
literally named `xs_offset` collides with the generated accessor for `xs`. The dtype at
`numba_types.py:584` shows all three side by side: `xs_offset`, `xs_length`, `xs_offset_`.

`mcdc_get/`, `mcdc_set/` and `numba_types.py` are **generated** — never hand-written. Run
`python mcdc/code_factory/rebuild_numba_support.py` (it inserts its own repo root on `sys.path`,
so it runs from any working directory).

### Local files → disposition

| Local | Action |
|---|---|
| `object_/photon_reaction.py` (289) | Reshape: `MCDCPolymorphic`, add `sub_type`, add `from_h5_group`, drop `perform_collision` |
| `object_/photon_material.py` (341) | Delete — `PhotonMaterial` → `Element` fields; constant-XS → `transport_model_data.py` |
| `object_/photon_reaction_loader.py` (124) | Delete — folds into `from_h5_group` + `set_photon_data` |
| `physics/photon/interface.py` (298) | Shrink to ~40 lines |
| `physics/photon/native.py` (37) | Grows to ~550 |
| `physics/photon/cross_sections.py` (189) | Merge → `native.py` |
| `physics/photon/distributions.py` (338) | Merge → `native.py` |
| `physics/photon/util.py` (84) | Split; see redundancies below |
| `physics/photon/data_loader.py` (458) | → `tools/data_library_generator/photon/` |
| `mcdc_get` / `mcdc_set` `photon_*.py`, `constant_xs_material.py` | Delete, regenerate |
| `test/unit/transport/physics/photon/*.py` (33 tests) | Rename with `test_` prefix, relocate to `test/unit/photon/`. **[REVISED]** 26 of the 33 are currently never collected — see Phase 3 |
| **[REVISED]** `photon_transport_code/` | **Do not archive as a unit.** Split by role — see the five rows below |
| `photon_transport_code/MCNP_Verification_Tests/**/*.py` (628 KB) | **Keep.** All decks `import mcdc`, so they are production-bound, not prototype-bound. Migrate the 8 chosen decks (§7) to `test/regression/` |
| `photon_transport_code/examples/CARRE_examples/` (cubesat), `examples/photon_slab/` | **Keep.** Both `import mcdc` |
| `photon_transport_code/test/` (**362 live tests**) | **Port alongside the physics.** Rewrite imports `photon_transport_code.transport.physics.photon.*` → `mcdc.transport.physics.photon.*`. This is the bulk of the real photon coverage |
| `photon_transport_code/{transport,mcdc_get,mcdc_set}/`, `conftest.py`, `__init__.py` | Archive, then delete — the genuinely superseded duplicate source, and the only part "archive" ever should have referred to |
| `photon_transport_code/examples/photon_transport_{compton,pair_production,photoelectric}/`, `debugging/`, `docs/` | Prototype-bound (`import photon_transport_code.*`); port or retire deliberately |
| `photon_transport_code/**/*.{out,log,png}` (1.63 GB) | gitignore — upstream ignores `*.out` and `*.png`, but **not** `*.log`; §6.3.5 adds a scoped rule for the one 3.4 MB log. Delete locally for disk space; never committed |
| **[NEW]** root `validate_*.py`, `compare_photon_xs.py`, `photon_issue_isolator.py`, `visualize_output.py` | Archive; upstream's root carries no loose scripts |

**Already exists upstream — delete our copies:**
- `scatter_direction` → `transport/physics/util.py:55` (identical)
- **[CORRECTED 2026-10-08]** `log_log_interpolation` → **`log_interpolation`** in
  `transport/util.py:168`, which is exactly `y1 * (x/x1)**(log(y2/y1)/log(x2/x1))` — ENDF
  INT=5. The previous revision pointed this at `DataTable(..., INTERPOLATION_LOG)` +
  `evaluate_table`, which is the wrong target for the **main XS grid**: that path is for
  sub-tabulated data carrying its own grid. Use the bare helper for `total_micro_xs` /
  `reaction_micro_xs` and reserve `DataTable` for coherent form factors and subshell PE tables.
  The sibling family in the same file is `histogram_interpolation` (INT=1),
  `linear_interpolation` (2), `semilogx_interpolation` (3), `semilogy_interpolation` (4).
- **[NEW 2026-10-08]** Note that proton and electron `total_micro_xs` both call
  `linear_interpolation`. **Photon must call `log_interpolation` instead** — log-log is what
  our 117-test validation was performed against, and linear interpolation on a log-spaced
  6,682-point grid spanning 1 eV – 100 GeV would be visibly wrong near absorption edges.
  This is the one place where photon deliberately departs from the template.
- `interpolate_xs` / `find_energy_bin` → `evaluate_photon_xs_energy_grid` +
  `find_bin` (`transport/util.py`, not `transport/physics/util.py`; it takes an epsilon
  tie-breaking band and a `go_lower` flag, and has its own unit test at
  `test/unit/util/test_find_bin.py`)

---

## 4. Cross-Section Pattern (neutron, electron and proton are identical)

1. **Library file** — one HDF5 per carrier (neutron: per-nuclide in `$MCDC_LIB`; electron:
   per-element; proton: per-nuclide). Shared `xs_energy_grid` + per-reaction `MT-nnn/xs`
   carrying **two attributes**: `offset` (index into the shared grid) and `unit` (`"barns"`).
2. **Loader** — `set_{neutron,electron,proton}_data(simulation)`, called from
   `Simulation._finalize_compilation`. Sums per-type XS, derives total, builds reactions via
   `from_h5_group`, then registers each with `reaction._compile_into_simulation(simulation)`
   as the last step.
3. **Annotated fields** — plain `NDArray[float64]` annotations on `Nuclide` / `Element`. The
   layer generator packs them into flat `data` and emits accessors. **Never build the flat
   buffer by hand** — this is what `PhotonMaterial.flat_data` gets replaced by.
4. **Runtime** — `macro_xs()` (density-weighted loop over material elements) →
   `total_micro_xs()` (dispatch on reaction_type) → `reaction_micro_xs()` (applies
   `reaction["xs_offset_"]`, returns 0.0 below it).
5. **Sub-tabulated data** — anything with its own grid becomes `DataTable` /
   `DistributionMultiTable`, not a packed array. `DataTable` supports piecewise
   `interpolations` + `interpolation_boundaries`; `INTERPOLATION_LOG = 5` is log-log.

### Units — settled  **[RESOLVED 2026-10-08]**

| Quantity | On disk | At runtime | Converted by |
|---|---|---|---|
| Energy | **MeV**, with `attrs["unit"] = "MeV"` | **eV** | `read_energy()`, `object_/electron_reaction.py:29` |
| Energy PDF | per MeV | per eV | `/ 1e6` at the read site (`proton_reaction.py` `set_energy_distribution`) |
| Cross section | **barns**, with `attrs["unit"] = "barns"` | barns | nothing — see below |
| Atom density | — | **10²⁴ atoms/cm³** | nothing |
| Speed | — | **cm/s** | — |
| `energy_deposition` | — | **eV**, weight-included | — |

`read_energy` is the whole mechanism: it reads the dataset's own `unit` attribute and
multiplies by `1e6` only when it says `"MeV"`, defaulting to eV. So a generator that writes
MeV **must** write the attribute, and a loader that wants eV must go through `read_energy`
rather than reading the dataset directly.

**There is no barn→cm² conversion anywhere in the code.** `macro_xs` computes
`element_density * xs` directly, which is dimensionally correct only because densities are
expressed in 10²⁴ atoms/cm³. `examples/proton_beam/input.py` makes the convention explicit:

```python
atom_density = material_density * 1e-24 * 1 / molar_mass * 6.022e23
```

So the previous revision's instruction to convert **cm² → barns on disk** is correct and
stands. Our photon code is MeV-native and uses cm/ns; both need converting — energies via the
`unit` attribute plus `read_energy`, speeds to cm/s.

### Unit-conversion gotcha for the photon loader

Our `data_loader.py` currently converts **eV → MeV on read** (its docstring: *"energies — MeV
(HDF5 stores eV; converted here)"*) and **barn → cm²**. Both directions are backwards relative
to upstream. The port inverts both, and the physics kernels move from MeV/cm² to eV/barn. The
1.022 MeV pair-production threshold becomes `2.0 * ELECTRON_MASS`, and every Klein–Nishina
expression that divides by the electron rest mass must use the existing constant rather than a
local MeV literal. `mcdc/constant.py` already provides everything needed, all in eV:

```python
LIGHT_SPEED   = 2.99792458e10    # cm/s
ELECTRON_MASS = 510.99895069e3   # eV/c^2
```

So the pair threshold is `1021997.90138 eV`, not a new literal. There is also
`ELECTRON_CUTOFF_ENERGY = 100  # eV`; photon will want a `PHOTON_CUTOFF_ENERGY` sibling, and
our EPDL grid's 1 eV floor is the natural lower bound to justify it against.

**This is the single largest source of silent numerical error in the port** — it is mechanical,
but it touches every formula, and a factor of 1e6 in the wrong place produces plausible-looking
output rather than a crash. Port the unit change and the 117 cross-section unit tests together,
not in separate commits.

### flat_data → annotated fields

| `flat_data` section | Becomes |
|---|---|
| energy grid | `Element.photon_xs_energy_grid` |
| Compton/coherent/PE/pair XS | `Element.photon_{incoherent,coherent,photoelectric,pair_production}_xs` |
| total XS | `Element.photon_total_xs` (derived in loader) |
| per-element densities | already `Material.element_densities` — delete ours |
| coherent form factor | `PhotonReactionCoherent.form_factor: DataBase` → `DataTable(q, F, INTERPOLATION_LOG)` |
| shell-resolved PE XS | `PhotonReactionPhotoelectric.N_subshell` + `subshell_xs: list[DataBase]` (mirrors `ElectronReactionIonization`) |
| shell binding energies | `Element.photon_photoelectric_subshell_binding_energy` — **[CORRECTED 2026-10-08]** name the reaction in the field, mirroring upstream's `electron_ionization_subshell_binding_energy`, and read each through `read_energy` as `element.py:171` does |
| fluorescence lines | Our EADL data, written at upstream's top-level `atomic_relaxation/` path |

### Data library — generated, not merged  **[RETITLED 2026-10-08]**

**[REWRITTEN 2026-10-08]** Our `data/mcdc/*.h5` are **photon-only** element files. Verified
structure of our `Al.h5`:

```
atomic_number, atomic_weight_ratio, element_name, excitation_level, fissionable
photon_reactions/{xs_energy_grid, total, elastic, incoherent_scattering,
                  photoelectric_absorption, pair_production, atomic_relaxation}
```

**The generator convention, confirmed from the live tree:** each non-neutron generator writes
to its **own** output directory with mode `"w"`, so they cannot clobber each other and mode
`"a"` is unnecessary:

| Generator | Output env var | ACE/source env var | Mode |
|---|---|---|---|
| neutron | `MCDC_LIB` | `MCDC_ACELIB` | `"w"` |
| electron | `MCDC_LIB_ELECTRON` | `MCDC_ACELIB_ELECTRON` | `"w"` |
| proton | `MCDC_LIB_PROTON` | `MCDC_ACELIB_PROTON` (+ `MCDC_PSTAR_LIB`) | `"w"` |
| **photon** | **`MCDC_LIB_PHOTON`** | **`MCDC_EPDL_LIB`** (EPDL + EADL; no ACEtk build needed — §2.8) | **`"w"`** |

**[CORRECTED 2026-10-08 — OWNER DECISION] There is no merge step.** §2.5's "merge the data
library" is superseded: photon gets a `generate.py` + `util.py` pair like every other particle,
writing a **photon-only** library, and §2.10's photon-only transport scope is what makes that
complete. The full rationale, the three bolt-on scripts it replaces, and the MT-number
corrections are in **§6.2** — read that section, not this one, for the generation plan.

Target shape of the file the photon generator writes:

```
$MCDC_LIB_PHOTON/Al.h5
├── element_symbol, atomic_number, atomic_weight_ratio
│     ^ atomic_number and atomic_weight_ratio are read by Element._compile_into_simulation
│       for EVERY particle type and are NOT optional, even in a photon-only library
├── photon_reactions/
│   ├── xs_energy_grid                      attrs: unit="MeV"
│   ├── coherent/MT-502/{xs, form_factor/}  xs attrs: offset, unit="barns"
│   ├── incoherent/MT-504/xs
│   ├── photoelectric/MT-522/xs             + MT-534+/xs per subshell
│   └── pair_production/MT-516/xs           + MT-515, MT-517
└── atomic_relaxation/                      our EADL data, top-level (decision §2.9)
```

Point `MCDC_LIB` at that directory for photon runs. A later PR that couples photon and electron
transport will have to solve two particles in one file; this one does not.

Schema fixes the new generator must get right (the existing 330 files are **replaced, not
patched** — see §6.2):

- **Add `offset` AND `unit` attributes on every `xs` dataset.** Confirmed critical twice over:
  `element.py` does `xs_container[xs.attrs["offset"]:] += xs[()]` unconditionally, and all
  four of our `xs` datasets currently have **empty attrs** → `KeyError` on the first load.
  The proton generator writes `attrs["offset"]` and `attrs["unit"] = "barns"` together; do
  both. **Note the `- 1`** in `generate.py:583` — ACE energy indices are 1-based and the
  attribute is stored 0-based.
- Energy datasets get `attrs["unit"] = "MeV"` so `read_energy` converts them (§4 Units).
- **[CORRECTED 2026-10-08]** `element_name` → `element_symbol`, **but not as a migration.**
  Neither name is read by the runtime: `Element.__init__` takes the symbol as a constructor
  argument and `_compile_into_simulation` reads only `atomic_weight_ratio` and
  `atomic_number`. So do **not** write a script to rename it in the existing 330 files. The
  new generator emits `element_symbol` because the electron generator does
  (`electron/generate.py:82`), and the old files are replaced wholesale rather than patched —
  see §6.2.
- Group names: `elastic` → **`coherent`**, `incoherent_scattering` → `incoherent`,
  `photoelectric_absorption` → `photoelectric`, to match the `PHOTON_REACTION_*` names and
  the `rx_names` list style in `set_electron_data`. **[NEW 2026-10-08]**
- **MT numbers move to the ENDF MF=23 standard** — total 501, photoelectric 522, pair 516
  (515 electron-field, 517 nuclear-field), subshells 534+. Our current 401/501/503 assignments
  are non-standard and one of them collides with the standard total. Full table and rationale
  in §6.2. **[NEW 2026-10-08]**
- Convert **eV → MeV** and **cm² → barns** on disk.
- Drop `excitation_level` / `fissionable` (nuclide fields, not element fields).
- Move relaxation from `photon_reactions/atomic_relaxation/subshells/<shell>/` to top-level
  `atomic_relaxation/MT-NNN/` with upstream's dataset names.
- Add the file-level provenance attrs the proton generator writes: `source_title`,
  `source_version`, `source_date`, and `source_comments` when present. **[NEW 2026-10-08]**

**Generator CLI to mirror** (electron's `generate.py:14`): `argparse` with `--rewrite` and
`--verbose`; default converts only elements missing from the output directory; `tqdm` progress
bar with `bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}{postfix}"` and `set_postfix_str` per
element; `os.makedirs(output_dir, exist_ok=True)`; `print_error` on either env var being unset.
The README follows upstream's five-heading shape: Prerequisites / Environment Variables /
Usage / What it Does / Output HDF5 Schema.

**Split of work between the two files** — mirroring `electron/{generate.py,util.py}`:

| File | Holds |
|---|---|
| `generate.py` | argparse, env-var checks, source loading, target selection, the element loop, and all HDF5 writing |
| `util.py` | `print_error` / `print_note`, `SYMBOL_TO_Z` / `Z_TO_SYMBOL`, the photon MT table, subshell designator→MT→label maps, `create_mt_group`, and the EPDL/EADL parsing helpers |

Electron's `util.py` is 334 lines of which the bulk is the `SYMBOL_TO_Z` map and the subshell
tables — **both of which photon can import rather than duplicate**, since photoelectric
subshells use the same MT-534+ designators as electron ionization. Decide in Phase 2 whether to
`from ..electron import util` (coupling two generators) or lift the shared maps into
`tools/data_library_generator/common.py` (a change upstream would have to accept). Duplicating
them is the third option and the worst.

---

## 5. Phases

### Phase 0 — Snapshot first (~15 min, zero risk) — **✅ COMPLETE 2026-10-03**

**Done and pushed.** See "Phase 0 status" in §1 for the 12 commits and the six drifted files.
This subsection is retained as the record of what was done and why; **do not re-run it.**

Nothing else happens until the work is recoverable. 2,300 lines of photon source existed
only in the working tree.

1. **`.gitignore` first, as its own commit** — the full specification is §6.3, the block to
   append is §6.3.5, and §6.3.6 is the verification gate that must pass before anything is
   staged. Nothing from `data/` may appear in `git status`.
2. Branch `wip/photon-snapshot-pre-refactor` off current `dev`; commit all source-like
   changes there in topical commits, **on the old base**, with no porting and no cleanup.
   Push to `origin`. This is a permanent diffable reference and is never merged.
3. **[REVISED] Commit `photon_transport_code/` source too — do not archive the folder.**
   Phase 0 is a snapshot, so everything source-like goes in, including the 362 tests and all
   the verification decks. The only things excluded are the `.out` / `.log` / `.png` outputs
   (1.63 GB), which `.gitignore` handles once §6.3.5 is applied — the `.log` is **not**
   covered by upstream and needs the new rule. Commit the loose root scripts (they are
   source; §6.3.2) and relocate them in Phase 2. **Nothing is deleted in Phase 0.**

**[REVISED] Provenance note.** Only
`photon_transport_code/{transport,mcdc_get,mcdc_set}/` is superseded: that is the **April
prototype** of the physics, whose 12 KB `native.py` is the ancestor of the July three-way
split across `native.py` / `cross_sections.py` / `interface.py` in `mcdc/`, and whose modules
import `photon_transport_code.transport.physics.photon`. For the physics modules the `mcdc/`
tree is authoritative.

The rest of the folder is **not** superseded and must not be swept up with it:

- Every deck under `MCNP_Verification_Tests/`, plus the CARRE cubesat model and
  `examples/photon_slab/`, does `import mcdc` — they already target the production package.
- `photon_transport_code/test/` collects **362 tests cleanly** under `mcdc-env`. It is live,
  not rotted, and it holds roughly 11× the coverage of the main tree's 33.

Verify both claims before deleting anything.

### Phase 1 — Fresh branch, no merge

**Gated on §14 (environment) being green.** The branch cannot be imported, let alone tested,
in `mcdc-env`.

```bash
git fetch mcdc-project
git checkout -b feature/photon-transport mcdc-project/dev
```

**[CORRECTED 2026-10-08]** The base is `mcdc-project/dev`, not `upstream/dev`. Re-apply onto
pristine upstream using the Phase 0 snapshot as reference. Also in this phase:

1. Resolve `.gitignore` per §6.3.7 — take upstream's wholesale, re-add only what §6.3.5
   justifies, and drop the blanket `*.h5` (§6.3.4). **Do not carry over the
   `lead_finite_cylinder_energy_deposition.py` rule** — that deck is now §7 deck 8 and must
   be committed, not ignored.
2. Delete the two local `backup/phase0-*` branches.
3. Disarm the push URLs on `mcdc-project` and `upstream` (§1).

### Phase 2 — Re-apply in dependency order

**[REWRITTEN 2026-10-08]** Per §3, §4 and the touch-list in §13. The template column now
names **proton** wherever proton is the newest expression of the pattern, and electron only
where per-element data is the point. Work top to bottom — the order is a dependency order,
and the regeneration step in the middle is load-bearing.

| # | Step | Template |
|---|---|---|
| 1 | Photon constants in the **300** block, `PARTICLE_PHOTON = 3` | `constant.py:60` proton block |
| 2 | `object_/photon_reaction.py` on `MCDCPolymorphic`, 4 subtypes, `xs_offset_` | `object_/proton_reaction.py` (484 ln) |
| 3 | `PhotonConstantXSData` | `NeutronMultigroupData`, `transport_model_data.py:30` |
| 4 | `Material`: `photon_constant_xs` kwarg + `has_photon_constant_xs` | `material.py:97` `has_neutron_multigroup` |
| 5 | Photon XS fields + `set_photon_data()` on `Element` | the electron half of `element.py` (`:82`, `:171`) |
| 6 | `photon_reactions` list on `Simulation` | `simulation.py:120`, `:315` |
| 7 | Register both new types in `python_objects_compiler.py` | its `ProtonReactionBase` (`:104`) / `NeutronMultigroupData` (`:91`) branches |
| 8 | **Regenerate** `mcdc_get/`, `mcdc_set/`, `numba_types.py` | `python mcdc/code_factory/rebuild_numba_support.py` |
| 9 | `evaluate_photon_xs_energy_grid` | `physics/util.py:34` (electron — same `mcdc_get.element` form) |
| 10 | `physics/photon/native.py` | `physics/proton/native.py` (664 ln) |
| 11 | `physics/photon/constant_xs.py` + `applicable()` | `physics/neutron/multigroup.py:38` |
| 12 | `physics/photon/interface.py` + `__init__.py` | `physics/neutron/interface.py` (**not** proton's) |
| 13 | Four dispatch arms in `physics/interface.py` | its `PARTICLE_PROTON` arms |
| 14 | `photon_transport: ParticleTransportSettings` | `settings.py:183` `proton_transport` |
| 15 | Activation + loader call in `simulation.py` `_finalize_compilation` | `:365`, `:482`, `:498` |
| 16 | `"photon"` source type | `object_/source.py:431` |
| 17 | `"photon"` tally filter + output label | `object_/tally.py:323`, `transport/util.py:25` |
| ~~18~~ | ~~Photon arm in `cross_species_production.py`~~ | **DEFERRED — §2.10** |
| 18 | `photon_transport` in the `prioritize_low_energy` guard at `simulation.py:350` | its neutron/proton arms (§2.11) |
| 19 | `tools/data_library_generator/photon/{generate.py,util.py,README.md}` (mode `"w"`, `$MCDC_LIB_PHOTON`) | `tools/data_library_generator/electron/` — see §6.2 |

**Step 8 is not optional and not last.** Steps 2–7 define annotated fields; the accessors in
`mcdc_get.element.photon_*` and `mcdc_get.photon_reaction.*` that step 10 calls **do not exist
until the generator has run.** Regenerate after every change to an annotated field, and never
hand-edit the output.

Mechanical renames throughout: `mcdc` → `simulation` (~100 sites in the photon files),
`ObjectPolymorphic` → `MCDCPolymorphic`, `ObjectSingleton` / `ObjectNonSingleton` →
`MCDCObject`, `collision_data` → `interaction_data`. `MaterialBase` / `MaterialMG` and the
`MATERIAL_*` `child_type` dispatch are gone — rehome onto `Material.element_composition`.
Inside `@njit` functions, recover the simulation with
`simulation = util.access_simulation(program)`.

### Phase 3 — Validate

0. **[NEW 2026-10-08] The generic object-model tests now cover photon for free** — and will
   fail loudly if the new objects are malformed. Run these first, before any photon-specific
   test:
   - `test/unit/test_object_compilation.py`
   - `test/unit/test_numba_layers_generator.py`
   - `test/unit/test_annotation_shape.py`
   - `test/unit/test_material.py`, `test_settings.py`, `test_source.py`,
     `test_transport_model_data.py`

   A missing `label`, a bad `sub_type`, or an `Annotated` shape the generator cannot pack will
   surface here with a clear message, long before a physics test gets confusing numbers.
1. `pre-commit run --all-files` against upstream's pinned black 26.1.0 /
   `language_version: python3.14`. **See §14** — this hook cannot bootstrap without a 3.14
   interpreter on `PATH`, and pre-commit will not install one. Fallback: run `black` directly
   and let CI arbitrate. Generated accessors are `force-exclude`d, so they need no formatting.
2. **[REVISED] The `test_` prefix is a correctness problem, not a convention tidy-up.**
   `pytest test/unit/transport/physics` collects **7 tests**, because only
   `test_energy_deposition.py` matches the default discovery pattern.
   `coherent_form_factor.py`, `cross_sections.py` and `fluorescence.py` hold **26 more tests
   that never run** unless the files are named explicitly on the command line. Rename all
   three, relocate to `test/unit/photon/`, and confirm the collected count rises 7 → 33.
   **Reconcile** `test_energy_deposition.py` with upstream's
   `test/unit/tally/test_energy_deposition.py` instead of duplicating.
3. **[REVISED]** Port and re-run `photon_transport_code/test/` — **362 tests** — after
   rewriting its imports onto `mcdc.transport.physics.photon.*`. These were written against
   the April API and many import symbols that no longer exist, so this is not a bulk
   find-and-replace: **see §10 for the per-file inventory and the three rewrite tiers.**
   Start with `test/regression/photon/conftest.py`, which gates 80 tests on its own.
   Target: 362 + 33 collected, all green. Then the MCNP benchmarks.
4. Confirm the neutron regression passes. `neutron/native.py` carries the constant-XS
   dispatch and **is** in the snapshot, so it is the thing to re-verify.
   **[RESOLVED 2026-10-03]** `azurv1/input.py` is no longer a concern: the local edits to it
   were photon experimentation, not a change to carry forward, and the deck was
   deliberately **left out of the Phase 0 snapshot**. The working version on `dev` stands.
   **[NEW 2026-10-08] The regression suite needs a data clone first:**

   ```bash
   git clone https://github.com/mcdc-project/mcdc-regression_test_data \
     test/regression/mcdc-regression_test_data
   ```

   `test/regression/conftest.py` names that directory in `NON_TEST_DIRS` and upstream's
   `pyproject.toml` lists it in `norecursedirs`. Without it, every case that reads reference
   data fails for the wrong reason. Comparison tolerances are `RELATIVE_TOLERANCE = 1e-6` and
   `ABSOLUTE_TOLERANCE = 1e-14`; the harness takes `--name`, `--skip`, `--target` and
   `--mode`.
5. **[NEW]** Generate the smoke-test references for all 30 decks — **§11**. Last step; gate
   it on items 1–4 being green.

### Phase 4 — Publish

Push `feature/photon-transport` to **`origin`** (the only remote we can write to) and open the
PR against **`mcdc-project/mcdc`**. **[CORRECTED 2026-10-08]** — not CEMeNT-PSAAP, which is
retired. Split by layer (data/objects → physics → tooling → tests) rather than one 2,300-line
drop; the Phase 2 table above is already in that order and steps 1–8, 9–13, 19 and the tests
are natural PR boundaries.

`photon-transport-docs/` and `photon-transport-directions/` (9,500 lines at repo root)
should not go up as-is — upstream's root carries no loose directories. Fold the durable
parts into `docs/` or keep them fork-only. The same applies to the `data/` gitignore rule
(§6.3.7 item 4).

---

## 6. Open Items

1. **~~ENERGY UNITS~~ — CLOSED 2026-10-08.** Not an open item and not an upstream bug. The
   runtime unit is **eV** throughout; the library stores **MeV** and declares it with a
   `unit` attribute; `read_energy` (`object_/electron_reaction.py:29`) performs the
   conversion. `Element.set_electron_data` *does* convert — through that helper, which the
   previous revision did not find. The Lockwood deck at `ENERGY = 1e4  # eV` is consistent.
   Our photon code is MeV-native and cm/ns, so the port converts: see "Units — settled" and
   "Unit-conversion gotcha" in §4. **This is now a mechanical porting task, not a risk to
   investigate** — but it is still the largest source of silent numerical error, so port it
   together with the 117 cross-section unit tests.
2. **[REWRITTEN 2026-10-08 — OWNER DECISION] Data generation: a `generate.py` + `util.py`
   pair, exactly like neutron and electron. No merge tool.**

   The previous revision proposed `tools/data_library_generator/merge.py` to stitch
   per-particle element files together. **Rejected by the owner.** Photon gets the same
   two-file generator shape every other particle has, and §2.10's photon-only scope is what
   makes that sufficient: a photon-only library needs nothing from electron.

   ```
   tools/data_library_generator/photon/
   ├── generate.py   # CLI + env vars + element loop + HDF5 writing
   ├── util.py       # Z<->symbol maps, MT tables, subshell tables, EPDL/EADL parsing
   └── README.md     # upstream's five-heading shape
   ```

   **Why photon-only is sufficient.** `Element.set_photon_data` runs only when
   `photon_transport.active` and reads only `photon_reactions/`. `set_electron_data` runs only
   when `electron_transport.active` and reads only `electron_reactions/`. Neither inspects the
   other's group, and §2.10 means we never enable both. So `$MCDC_LIB` pointed at a
   photon-only library is correct and complete for every deck in §7.

   **The one thing a photon-only file must still carry.**
   `Element._compile_into_simulation` reads `atomic_weight_ratio` and `atomic_number` from
   `$MCDC_LIB/<symbol>.h5` **regardless of which particle is active**. Those two datasets are
   not optional — omit them and every element fails at compile time, before any photon code
   runs. Our existing files already have both.

   **What this replaces: a three-pass bolt-on pipeline.** The current `data/mcdc/*.h5` were
   not built by one generator. They were built by three scripts run in sequence, all still
   sitting in `photon_transport_code/tools/`:

   | Script | Did |
   |---|---|
   | `reformat_photon_data.py` | base reformat: energy grid + the four XS arrays |
   | `add_atomic_relaxation.py` | bolted EADL relaxation onto the existing files |
   | `add_coherent_form_factors.py` | bolted EPDL MF=27/MT-502 form factors on afterwards |

   That history explains two defects the port must fix anyway, so collapsing the three into
   one single-pass `generate.py` is not extra scope — it is the cheapest way to fix them:

   - **Every `xs` dataset has empty attrs.** No `offset`, no `unit`. `set_photon_data` will
     `KeyError` on the first element (§4). A bolt-on pass never had the energy-grid context
     to compute `offset`; a single pass does.
   - **The schema has bolt-on shapes** — `photoelectric_absorption/shell_resolved/<K,L1,…>/xs`
     instead of per-MT subshell groups, and `pair_production/MT-503/{electron_field,
     nuclear_field}/xs` as sub-groups of a group that also has its own `xs`.

   **MT numbers are wrong and should be fixed here. [NEW 2026-10-08]** Measured from
   `data/mcdc/Al.h5`:

   | Reaction | Our file | Standard ENDF MF=23 | Verdict |
   |---|---|---|---|
   | total | `total/MT-401` | **501** | wrong — 401 is not a photon MT |
   | photoelectric | `photoelectric_absorption/MT-501` | **522** | wrong, and **collides with standard total** |
   | coherent | `elastic/MT-502` | 502 | correct |
   | incoherent | `incoherent_scattering/MT-504` | 504 | correct |
   | pair, total | `pair_production/MT-503` | **516** | wrong |
   | pair, electron field | `MT-503/electron_field/xs` | **515** | should be its own MT group |
   | pair, nuclear field | `MT-503/nuclear_field/xs` | **517** | should be its own MT group |
   | PE subshells | `shell_resolved/<label>/xs` | **534+** | should be per-MT |

   This numbering has already caused one real bug — the old reaction loader read
   `_MT_COMPTON = 502`, which is coherent, not Compton. Standardising removes the trap, and
   **MT-534+ for photoelectric subshells is the same convention electron already uses for
   ionization subshells**, so `util.py` can reuse electron's subshell tables rather than
   inventing a parallel set. That reuse is the strongest argument for the change.

   Group names also move to match the `PHOTON_REACTION_*` names (§4): `elastic` → `coherent`,
   `incoherent_scattering` → `incoherent`, `photoelectric_absorption` → `photoelectric`.

   **Relaxation source — still open, and now narrower.** Upstream ships `atomic_relaxation/`
   from EPRDATA14; ours is EADL, currently nested under
   `photon_reactions/atomic_relaxation/subshells/<shell>/` with `binding_energy`,
   `designator`, `fluorescence_yield` and a `radiative/` triple of
   `{final_subshell, probability, transition_energy}`. Decision §2.9 keeps ours and moves it
   to the top-level `atomic_relaxation/` path. Compare the two before writing that part of the
   generator: if they agree, consuming upstream's drops a generator stage; if they disagree,
   our validated fluorescence numbers say which to trust. **§2.10 raises the stakes slightly**
   — fluorescence is the only photoelectric product still transported, so this data is
   load-bearing rather than incidental.

   **Still worth raising with maintainers, but no longer blocking:** that `Element` has no
   story for two particles in one file. We are not solving it (§2.10), but we are the first
   case that will eventually need it, and they should know.

3. **`data/` cleanup — [NEW] resolved.** `data/mcdc/` (204 MB) is authoritative; it is what
   `data_loader.py` reads. `data/mcdc.backup/` (262 MB) and `data/mcdc_reformatted/`
   (196 MB) are stale duplicates — **458 MB, delete**. `data/` totals 872 MB. **[NEW
   2026-10-08]** Measured again on the current tree: `data/mcdc` 204 MB, `data/mcdc.backup`
   262 MB, `data/mcdc_reformatted` 196 MB, `data/endf` 116 MB, `data/raw` 81 MB.
   `data/mcplib84` is **gone** — the previous revision listed it at 16 MB; it no longer
   exists on disk, so drop it from any cleanup script.
4. **[REWRITTEN 2026-10-08] Raise with maintainers.** Two of the previous revision's four
   topics are closed; the list is now:
   - **The 300 reaction block and `PARTICLE_PHOTON = 3`.** The ask has changed shape: it is
     no longer "may we have 200" but "we are taking **300**; is it reserved, and is 3 the
     slot you want for photon?" Proton took 200 while our plan named it, so the cost of not
     asking is now demonstrated rather than hypothetical.
   - **That `Element` has no story for two particles in one file.** We are not solving it
     (§2.10 scopes this PR to photon-only), but photon is the first case that will need it,
     so they should know it is coming. **Not** a request for a merge tool — §6.2.
   - **EPRDATA14 vs our EPDL route** (shell-resolved PE + coherent form factors, finer grid,
     1 eV floor) — do they intend their own photon path?
   - ~~the generator file-mode collision~~ — **closed**, see the header and §4.
   - ~~energy units / possible upstream bug~~ — **closed**, see §6.1. Do not raise it; there
     is no bug, and `read_energy` is the answer.
5. **Coverage gaps** in the chosen decks. **[PARTLY RESOLVED 2026-10-08]**
   - ~~No energy-deposition deck~~ — **closed.** `lead_finite_cylinder_energy_deposition.py`
     is now §7 deck 8 by owner decision, reversing its §6.3.2 exclusion. Use
     `test/regression/pincell-energy_deposition/` as the structural pattern.
   - **Fluorescence remains effectively untested at the deck level** — both Pb decks run at
     10 MeV and the Pb K-edge is 88 keV, so no deck puts meaningful flux near it. Unit tests
     cover it. Still open, and lower priority now that §2.10 scopes photoelectrons to local
     deposition: fluorescence photons are the one PE product still transported, so the unit
     tests are carrying real weight. Consider a low-energy Pb deck in a later PR.

### 6.3 `.gitignore` — full specification  **[REWRITTEN 2026-10-03]**

**[STATUS 2026-10-08] §6.3.1–§6.3.6 are DONE** — applied as snapshot commit `83e8bdd9` and the
gate passed. They are retained as the record of what was decided and why. **§6.3.1's line
numbers were measured against `CEMeNT-PSAAP/MCDC` and are now stale**; re-derive them against
`mcdc-project/dev` during §6.3.7, which is the only part still outstanding.

This is **Phase 0 step 1 and it is its own commit**, made before any source is staged.
The reason is asymmetry: an output file left out of the snapshot can be added in a later
commit, but an output file committed once lives in the history permanently and can only be
removed by a filter-repo rewrite that invalidates every clone and every open PR. The working
tree currently holds **2.5 GB**, of which **~2.5 MB across 199 files** belongs in git
(measured after applying §6.3.5).

Measured on the tree at `86ee515a`. Reproduce any figure here with the commands in §6.3.6.

#### 6.3.1 What upstream's `.gitignore` already covers

Upstream's 71-line file (unchanged at the merge base) already handles more than the previous
revision credited it with. Do not re-add any of these:

| Rule | Line | Covers in our tree |
|---|---|---|
| `__pycache__`, `*.pyc`, `*.nbc`, `*.nbi` | 11–14 | All Python and Numba cache. **The previous revision wrongly listed `__pycache__/` as missing** |
| `*.png`, `*.mp4`, `*.gif` | 29–31 | All 76 plots under `photon_transport_code/`. **Also already covered — the previous revision's scoped png rule is redundant** |
| `*.out` | 38 | All 23 SLURM job logs, 1.61 GB, including the 666 MB and 589 MB files in `benchmark_5/` |
| `*.pbs` | 39 | Cluster scripts in the PBS dialect (we use SLURM — see the trap in §6.3.3) |
| `.pytest_cache`, `pytestdebug.log` | 52–53 | Test cache only — **not** `*.log` generally |
| `*.prof`, `*.core`, `*.swp`, `.vscode/`, `**/.DS_Store` | various | Profiler, editor, OS noise |
| `dummy_nuclide.h5`, `source_particles.h5`, `*output.h5`, `output*.h5` | 26–28, 65–66 | The *narrow* h5 rules. See §6.3.4 |
| `docs/build`, `docs/source/pythonapi/generated/` | 59–60 | Root `docs/` only — **path-anchored, so it does not reach `photon_transport_code/docs/`** |

**Two traps in upstream's file that bite the photon tree specifically:**

1. **`*.csv` is ignored globally (line 62).** Nine CSV files exist in our tree —
   `AZURV1_photon_comparison_table.csv`, its `_post_one_half_mft` variant, and seven under
   `xs_compare/`. All nine are invisible to `git status` today and **would be silently
   omitted from the snapshot with no warning at all**. Per the §12 test, the two AZURV1
   comparison tables are derived output (regenerate from `error_comparison/*.py`) and the
   `xs_compare/` set is output of `compare_photon_xs.py`, so leaving them ignored is the
   right outcome — but it must be a *decision*, not an accident. If any CSV later becomes
   irreplaceable input it needs an explicit `!` negation.
2. **The `*.png` negation is path-anchored to the root docs tree** —
   `!docs/source/images/**/*.png` (line 34). Any photon figure that later needs committing
   must get its own negation; it will not inherit this one.

#### 6.3.2 Audit — every uncovered path, with verdict

592 files appear in `git status --porcelain -uall` today, totalling **128 MB**. The table
accounts for all of it.

Several paths were excluded from the snapshot by **owner decision** rather than by the audit
below. The audit records what the artifact *is*; these override what happens to it:

| Excluded by decision | Count | Note |
|---|---|---|
| All MCNP input decks | 7 | Reverses the §12 row. Five `*_MCNP.txt` plus two `benchmark_5/Benchmark5_MCNP_Deck*.txt` that do not match the glob but are MCNP decks by their own headers |
| `1e7_results/meshtam` | 1 | MCNP6 mesh tally output. Deleted from the branch by the owner in commit `6c06c947`; now excluded so it never enters history |
| `**/*.slurm` job scripts | 21 | §6.3.3 |
| Named decks and scripts under `Complex_M&G/` | **8** — was 9 **[REVISED 2026-10-08]** | `lead_finite_cylinder.py`, ~~`lead_finite_cylinder_energy_deposition.py`~~ (**now §7 deck 8**), `multi_material_slabs.py`, `multi_material_spheres.py`, `multi_material_spheres_energy_spectrum.py`, `multi_material_spheres_energy_spectrum_results.txt`, `Convergence/compare_mcdc_mcnp_spectrum_1e7.py`, `Convergence/compare_mcdc_mcnp_spectrum_1e7_postprocessed.py`, `Convergence/mm_spheres_1to10mev_sdev_convergence.py` |
| `Complex_M&G/1e7_results/comparisons/` | 4 | Whole folder |
| `test/regression/azurv1/input.py` | 1 | Local edits were photon experimentation; working version lives on `dev` |

Every one is an exact path or scoped glob, so the **five** §7 decks that share name prefixes
are unaffected, and every excluded file remains on disk untracked — each decision is
reversible, and `lead_finite_cylinder_energy_deposition.py` is the proof: it was excluded here
and **un-excluded on 2026-10-08** at the cost of one `git add`.

| Path | Size | Files | Verdict | Rationale |
|---|---|---|---|---|
| `data/mcdc/` | 204 MB | ~330 `.h5` | **ignore** | Generated by `tools/data_library_generator/`. Authoritative at runtime but reproducible from `data/endf/` plus the generator. Masked today only by our blanket `*.h5` |
| `data/mcdc.backup/` | 262 MB | ~330 | **ignore + delete** | Stale duplicate — §6 item 3 |
| `data/mcdc_reformatted/` | 196 MB | ~330 | **ignore + delete** | Stale duplicate — §6 item 3 |
| `data/endf/` | 116 MB | 300 `.endf` | **ignore** | **The single largest gap.** Plain text, so `*.h5` never touched it. Upstream fetches its libraries rather than vendoring them; ENDF/B and EPDL are redistributable but belong behind a fetch script, not in history |
| `data/raw/` | 81 MB | — | **ignore** | Generator intermediate |
| `data/mcplib84/` | 16 MB | — | **ignore** | Third-party library, fetched not vendored |
| `.sonar/` | 5 KB | few | **ignore** | SonarQube scanner state, machine-local |
| `photon_transport_code/docs/source/_build/` | 1.7 MB | 46 | **ignore** | Sphinx HTML output — vendored `jquery-3.6.0.js`, 7 binary `.doctree` files, `.buildinfo`, `objects.inv`, a `.pickle`. Reproducible by `make html`. Upstream's `docs/build` rule is path-anchored and misses this |
| `.../MCNP_test_problems/_pb_full_run.log` | 3.4 MB | 1 | **ignore** | **The largest single file that would actually land.** The previous revision's claim that "`*.log` already comes from upstream's `.gitignore`" is **wrong** — only `pytestdebug.log` is listed |
| `.../Error-Convergence_testing/v004t11a003-icone22-30156.pdf` | 1.7 MB | 1 | **ignore** | Draft manuscript PDF. §12: belongs with the manuscript, not the code repo |
| `photon_standard_error_comparison.xlsx` | 144 KB | 1 | **ignore** | Build output of `error_comparison/` — §12 |
| `.../MCNP_test_problems/For Doug - bench 1.xlsx` | 16 KB | 1 | **COMMIT** | Advisor-supplied benchmark data = irreplaceable *input* under the §12 test. **A blanket `*.xlsx` rule would destroy this** — see §6.3.3 |
| `photon_issue_report.txt` | small | 1 | **ignore** | Output of `photon_issue_isolator.py` |
| root `validate_*.py`, `compare_photon_xs.py`, `photon_issue_isolator.py`, `visualize_output.py` | ~60 KB | 6 | **commit, then relocate** | Source, and the only record of several validation procedures. Upstream's root carries no loose scripts, so commit them in the snapshot and rehome them under `tools/` or `test/` during Phase 2. Do **not** ignore them |
| `mcdc/` photon modules, `test/unit/transport/physics/`, `photon_transport_code/**/*.py` | ~800 KB | ~240 | **commit** | The snapshot itself |

#### 6.3.3 Rules the previous revision proposed that must **not** be added

| Proposed | Why it is wrong |
|---|---|
| `__pycache__/` | Already upstream line 11 |
| scoped `photon_transport_code/**/*.png` | Already covered by the global `*.png`, line 29 |
| ~~`*.slurm`~~ **[SUPERSEDED 2026-10-03]** | This row argued the rule was destructive, because SLURM *outputs* are `slurm-<jobid>.out` and already caught by `*.out`, while the 21 `*.slurm` files are hand-written **job submission scripts**. **Owner decision overrides this: the scripts are excluded from the snapshot.** The rule is now in §6.3.5, scoped to `photon_transport_code/**/*.slurm`. Accepted consequence: git no longer records how each benchmark was launched — only the decks themselves. The files stay on disk, untracked, so the decision is reversible |
| blanket `*.xlsx` | Catches `For Doug - bench 1.xlsx`, which §6.3.2 keeps. Anchor the rule to the one file instead |
| removing `*.h5` **in Phase 0** | See §6.3.4 — correct eventually, wrong now |

#### 6.3.4 The `*.h5` rule — keep in Phase 0, narrow in Phase 1

The earlier instruction to drop our blanket `*.h5` is right in principle and wrong in
sequencing. `*.h5` is currently the **only** thing standing between the snapshot commit and
**666 HDF5 files**, roughly 700 MB, most of it `data/mcdc*/`.

- **Phase 0:** keep `*.h5`. The new `data/` rule and `*.h5` overlap heavily, and that
  redundancy is deliberate belt-and-braces for the one commit that cannot be undone.
- **Phase 1:** when taking upstream's `.gitignore` wholesale, drop `*.h5` and rely on
  `data/` plus upstream's narrow rules (`*output.h5`, `output*.h5`, `dummy_nuclide.h5`,
  `source_particles.h5`). The rationale is unchanged: a blanket `*.h5` would later swallow
  legitimate test fixtures, and the §11 smoke-test references are the obvious casualty.
- Audit at that point with `git check-ignore -v` over every `.h5` path and confirm each hit
  is attributed to `data/` or to a narrow rule, never to a blanket one.

#### 6.3.5 The block to append — Phase 0

Append verbatim beneath the existing 23 local insertions. Every rule carries the reason it
exists, because the next person to read this file will otherwise re-litigate all of it.

```gitignore
# ---------------------------------------------------------------------------
# Photon transport — Phase 0 snapshot rules (see UPSTREAM_SYNC_HANDOFF §6.3)
# ---------------------------------------------------------------------------

# Nuclear data libraries — 857 MB. Generated by tools/data_library_generator/
# or fetched from ENDF/EPDL upstream. data/endf/ is 116 MB of plain text and is
# NOT caught by *.h5. data/mcdc.backup/ and data/mcdc_reformatted/ are stale
# duplicates slated for deletion (handoff section 6, item 3).
data/

# SonarQube scanner state — machine-local
.sonar/

# Sphinx output in the verification tree. Upstream's `docs/build` rule is
# path-anchored to the repo root and does not reach here. Reproduce with
# `make html`.
photon_transport_code/docs/source/_build/

# Full-run capture, 3.4 MB. Upstream ignores only pytestdebug.log, NOT *.log,
# so this needs an explicit rule. Scoped rather than blanket *.log so that a
# deliberately committed log stays possible.
photon_transport_code/**/*_full_run.log

# Draft manuscript PDF — belongs with the paper, not the code (section 12)
photon_transport_code/**/*.pdf

# Build output of MCNP_Verification_Tests/error_comparison/*.py (section 12).
# Anchored with a leading slash: "For Doug - bench 1.xlsx" in the verification
# tree is advisor-supplied INPUT and must stay committable.
/photon_standard_error_comparison.xlsx

# Output of photon_issue_isolator.py
/photon_issue_report.txt

# SLURM job submission scripts. Excluded by owner decision 2026-10-03,
# reversing the 6.3.3 note that treated these as source. They remain on
# disk, untracked.
photon_transport_code/**/*.slurm

# MCNP input decks. Not to be included in the repo. Reverses the section 12
# row that called them irreplaceable ground truth. The two benchmark_5 decks
# do not match the *_MCNP.txt glob but are MCNP input decks by their own
# headers.
photon_transport_code/**/*_MCNP.txt
photon_transport_code/MCNP_Verification_Tests/benchmark_5/Benchmark5_MCNP_Deck.txt
photon_transport_code/MCNP_Verification_Tests/benchmark_5/Benchmark5_MCNP_Deck_MCDC_equivalent.txt

# Verification decks and analysis scripts excluded by owner decision. Exact
# paths, so the kept siblings (lead_finite_cylinder_off_center.py,
# multi_material_slabs_collimated_beam.py, multi_material_slabs_mesh_tally.py,
# multi_material_spheres_1to10mev_spectrum.py) are unaffected.
#
# 2026-10-08: lead_finite_cylinder_energy_deposition.py was REMOVED from this
# list by owner decision and is now section 7 deck 8 -- it is the only
# energy-deposition deck, and section 2.3 rewrites that tally. 8 paths remain.
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/lead_finite_cylinder.py
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/multi_material_slabs.py
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/multi_material_spheres.py
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/multi_material_spheres_energy_spectrum.py
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/multi_material_spheres_energy_spectrum_results.txt
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/Convergence/compare_mcdc_mcnp_spectrum_1e7.py
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/Convergence/compare_mcdc_mcnp_spectrum_1e7_postprocessed.py
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/Convergence/mm_spheres_1to10mev_sdev_convergence.py

# Whole folder excluded by owner decision
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/1e7_results/comparisons/

# MCNP6 mesh tally output. Deleted from the branch by the owner in commit
# 6c06c947 "cleanup"; excluded here so it never enters history at all.
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/1e7_results/meshtam
```

Deliberately **not** in the block, so that nobody adds them later: `__pycache__`, `*.png`,
`*.out` (upstream already has them); `*.xlsx`, `*.log` and `*.pdf` unanchored (each would eat
source — §6.3.3); `*.h5` (already present locally, keep until Phase 1 — §6.3.4).

#### 6.3.6 Verification gate — run before staging anything  **[PASSED 2026-10-03]**

```bash
# 1. The two monsters must already be ignored by upstream's *.out
git check-ignore -v photon_transport_code/MCNP_Verification_Tests/benchmark_5/slurm-20749880.out

# 2. File count: 592 before the block, 199 after (measured)
git status --porcelain --untracked-files=all | wc -l

# 3. Total bytes about to enter history: 128 MB before, ~2.5 MB after (measured)
git status --porcelain -uall | awk '{print $2}' \
  | while read -r f; do [ -f "$f" ] && du -k "$f"; done \
  | awk '{s+=$1} END {print s " KB"}'

# 4. Nothing from data/ may appear. Expect zero lines.
git status --porcelain -uall | grep '^?? data/' | head

# 5. The 21 .slurm job scripts are now EXCLUDED by owner decision. Expect 0
#    listed, and 21 still present on disk.
git status --porcelain -uall | grep -c 'slurm$'
find photon_transport_code -name '*.slurm' | wc -l

# 6. The advisor's benchmark workbook MUST still be listed. Expect 1.
git status --porcelain -uall | grep -c 'bench 1.xlsx'

# 6b. No MCNP input deck may be listed. Expect 0 and 0.
git status --porcelain -uall | grep -c '_MCNP.txt$'
git status --porcelain -uall | grep -c 'Benchmark5_MCNP_Deck'

# 6c. The section 7 decks sharing name prefixes MUST survive. Expect 5.
#     (was 4 before lead_finite_cylinder_energy_deposition.py became deck 8)
git status --porcelain -uall | grep -cE 'lead_finite_cylinder_off_center\.py|lead_finite_cylinder_energy_deposition\.py|multi_material_slabs_collimated_beam\.py|multi_material_slabs_mesh_tally\.py|multi_material_spheres_1to10mev_spectrum\.py'

# 7. Largest file about to be committed — expect 348 KB
#    (Error-Convergence_testing/AZURV1_photon_error_analysis.txt); nothing else above 104 KB
git status --porcelain -uall | awk '{print $2}' \
  | while read -r f; do [ -f "$f" ] && du -k "$f"; done | sort -rn | head -5

# 8. After committing, before pushing: confirm the pack is small
git count-objects -vH    # size-pack should be single-digit MB
```

**Gate:** items 2, 3, 5 and 6 must all hit their expected values before anything is staged.
GitHub hard-rejects any single file over 100 MB and warns above 50 MB; nothing in the
corrected set approaches either, so a failure here means a rule is missing — not that the
limit is tight.

#### 6.3.7 Phase 1 handover

`.gitignore` is a guaranteed conflict: it carries 23 uncommitted local insertions plus the
Phase 0 block above, **and** upstream rewrote the file across the 1,060-commit divergence.
Resolution order is not negotiable:

1. Take **upstream's version wholesale** — `git checkout mcdc-project/dev -- .gitignore`.
   **[CORRECTED 2026-10-08]** Not `upstream/dev`; and re-verify §6.3.1's line numbers against
   the file you actually get, since 1,060 commits have passed over it.
2. Re-add only what §6.3.5 justifies, minus anything upstream has since absorbed. Re-check
   §6.3.1 against the new file rather than assuming the line numbers above still hold.
3. Drop the blanket `*.h5` at this point (§6.3.4) and re-run the §6.3.6 audit.
4. `data/` is fork-only — upstream fetches its libraries. Keep the rule locally, but it does
   not go up in the Phase 4 PR.
---

## 7. The 8 Decks  **[WAS 7 — EXPANDED 2026-10-08]**

All under `photon_transport_code/MCNP_Verification_Tests/`:

1. `Complex_M&G/lead_finite_cylinder_off_center.py`
2. `Complex_M&G/multi_material_slabs_collimated_beam.py`
3. `Complex_M&G/multi_material_slabs_mesh_tally.py`
4. `Complex_M&G/multi_material_spheres_1to10mev_spectrum.py`
5. `Error-Convergence_testing/AZURV1_photon_v3.py`  (constant-XS treatment)
6. `MCNP_test_problems/10mev_al_spheres.py`
7. `MCNP_test_problems/10mev_pb_spheres.py`
8. **`Complex_M&G/lead_finite_cylinder_energy_deposition.py`** — **[ADDED 2026-10-08]**

(30 photon decks exist total; the other 22 are variants/duplicates.)

### Why deck 8 was added  **[NEW 2026-10-08]**

**Owner decision 2026-10-08.** §2.3 changes where energy deposition is *written* — from our
own `SCORE_ENERGY_DEPOSIT = 13` plumbing to upstream's `interaction_data["energy_deposition"]`
and `score.interaction()`. The original seven decks contain **no energy-deposition tally**, so
the one piece of plumbing being replaced would have had no regression coverage at all. That is
the gap §6.5 flagged, and this closes it.

**This reverses an owner exclusion.** `lead_finite_cylinder_energy_deposition.py` was one of
the nine named `Complex_M&G/` files excluded from the Phase 0 snapshot (§6.3.2) and ignored by
§6.3.5. Both have been updated: the file is **removed from the ignore block** and the exclusion
count drops from 9 to 8. Because the file stayed on disk untracked, nothing was lost and the
reversal costs only a `git add`.

Consequences to carry out:

1. **The working tree's `.gitignore` has NOT been changed yet.** This revision edits the
   §6.3.5 *specification* block only. The live file still carries the rule at
   `.gitignore:147`, verified with:

   ```bash
   git check-ignore -v photon_transport_code/MCNP_Verification_Tests/Complex_M&G/lead_finite_cylinder_energy_deposition.py
   ```

   So the deck is still invisible to `git status`. **Deleting that line is the first action of
   Phase 1**, after which the file is committed normally. It is not in the Phase 0 snapshot
   and does not need to be — it joins the tree in Phase 1 rather than retroactively.
2. §6.3.6 gate item 6c now expects **5**, not 4 — updated.
3. Its MCNP comparison target is **not in git** (owner decision on MCNP decks stands), so its
   `answer.h5` is a self-consistency reference like every other case. See §7's migration note:
   `answer.h5` was never an MCNP comparison.

### Migration target — upstream's convention  **[NEW 2026-10-08]**

Regression cases are **auto-discovered as directories** by `test/regression/conftest.py`:
every subdirectory of `test/regression/` that is not `__pycache__` or
`mcdc-regression_test_data` is collected as a case. So each deck becomes:

```
test/regression/photon_<case_name>/
├── input.py      <- the deck, renamed; MUST be exactly "input.py"
└── answer.h5     <- reference output; conftest fails with "answer.h5 is missing" without it
```

The harness runs `input.py` as a subprocess with `--mode=<mode>`, then compares every tally,
score and result in `answer.h5` against the produced output at `rtol = 1e-6`, `atol = 1e-14`.
That tolerance is far tighter than MCNP agreement — `answer.h5` is a **self-consistency**
reference generated from our own code once it is trusted, not an MCNP comparison. Keep the
MCNP comparison as separate analysis, which is what §11 and §12 already assume.

**The example validator does apply if we add an example.**
`test/unit/test_example_inputs.py` globs `examples/**/input.py`, runs each with `run()`
monkeypatched to compile-only, and asserts exactly one simulation compiles. It carries
`EXCLUDED_EXAMPLES = ["hybrid_multigroup", "proton_beam"]` for data-library-dependent cases.
So if `examples/photon_slab/` lands (and §3 keeps it), it must be named `input.py` **and added
to `EXCLUDED_EXAMPLES`**, since it needs `$MCDC_LIB`. The previous revision's parenthetical
that "upstream's example-validator obligation does not apply" is true only for as long as we
add nothing to `examples/`.

---

## 8. Execution

**[REWRITTEN 2026-10-08]**

**Blocked on: §14, the environment.** That is now the only hard blocker, and it is a real one —
`mcdc-env` cannot import the upstream tree. §6.1 is closed. §6.2 (data generation) can be settled
during Phase 2. §6.3 is resolved.

**Phase 0 is already done — the previous revision's step 0 is deleted from this block.** Do not
re-create `wip/photon-snapshot-pre-refactor`; it exists at `c4f0cb49` and is pushed.

```bash
cd /c/Projects/MCDC

# 0. PREREQUISITE — build the environment (section 14). Nothing below works without it.
#    Then decide the six drifted files (section 1) and commit or discard them.

# 1. Disarm push to repositories we do not own
git remote set-url --push mcdc-project DISABLED
git remote set-url --push upstream     DISABLED

# 2. Park the Phase 0 snapshot side by side, as a read-only reference
git worktree add ../MCDC-photon-old wip/photon-snapshot-pre-refactor
#    open ../MCDC-photon-old in a second editor window

# 3. Port branch, straight off the canonical remote
#    (NOT a merge, NOT a fast-forward, NOT CEMeNT-PSAAP)
git fetch mcdc-project
git checkout -b feature/photon-transport mcdc-project/dev

# 4. Re-verify the two assumptions this document rests on, against the tip you just got
grep -nE "^PARTICLE_|= 3[0-9][0-9] *$" mcdc/constant.py   # PARTICLE_PHOTON=3 free? 300 free?
git ls-tree -r --name-only HEAD | grep -i photon          # expect EMPTY

# 5. Regression reference data (section 5 Phase 3 item 4)
git clone https://github.com/mcdc-project/mcdc-regression_test_data \
  test/regression/mcdc-regression_test_data

# 6. .gitignore per section 6.3.7
git checkout mcdc-project/dev -- .gitignore
#    then re-add only what 6.3.5 justifies, and drop the blanket *.h5

# 7. Delete the superseded local backups
git branch -D backup/phase0-v1 backup/phase0-v2
```

Then: port the photon layer per §3, §4 and the §13 touch-list, **in the Phase 2 step order**,
regenerating Numba support with `rebuild_numba_support.py` after every annotated-field change;
migrate the 8 decks into `test/regression/photon_*/`; build the generator (§6.2).

Step 4 is not ceremony. `mcdc-project/dev` moved from `d41bf52f` to `295cd909` in one day while
this revision was written, and the 200 block was taken by proton between two revisions of this
same document. Confirm, do not assume.

Cleanup when done: `git worktree remove ../MCDC-photon-old`

---

## 9. `photon_transport_code/` — Measurements  **[NEW 2026-10-03]**

Recorded because the 2026-10-01 revision mischaracterised this folder and told Phase 0 to
archive it wholesale.

### Size is job logs, not work

| Extension | Bytes | Count |
|---|---|---|
| `.out` (SLURM stdout) | **1,610,652,045** | 23 |
| `.png` | 17,654,723 | 61 |
| `.log` | 3,556,249 | 1 |
| `.h5` | 2,007,656 | 26 |
| **`.py`** | **643,622** | **59** |

99.6% of the folder is 23 job logs. Two files are 1.25 GB of that total.

### Import boundary — what is production-bound vs prototype-bound

`import mcdc` (production — survives the prototype being deleted):

- every `MCNP_Verification_Tests/**/problem.py` and `neutron_problem.py`
- `examples/CARRE_examples/10MeV_cubesat_model.py`
- `examples/photon_slab/problem.py`

`import photon_transport_code.*` (prototype-bound — dies with the duplicate source):

- all of `test/` (unit, regression, integration)
- `examples/photon_transport_{compton,pair_production,photoelectric}/problem.py`
- `debugging/debug_cross_sections.py`, `docs/source/conf.py`

### Test coverage lives in the prototype, not the main tree

```
pytest photon_transport_code/test --collect-only   ->  362 tests collected in 0.29s
pytest test/unit/transport/physics --collect-only  ->    7 tests collected
```

Both under `C:\Users\dwhou\anaconda3\envs\mcdc-env`. The 362 collect cleanly — live, not
rotted. Per-file counts in `test/unit/photon/`: `test_coverage_gaps` 50,
`test_phase1_structure` 43, `test_photon_reaction` 37, `test_distributions` 28,
`test_total_xsec` 26, `test_pair_production` 17, `test_photoelectric` 16,
`test_klein_nishina` 15, `test_docstrings` 9 (241 total), plus 7 regression files and 1
integration file.

The main tree's 7 is not the whole story either: naming the three unprefixed files
explicitly collects **26 more**, for 33 actual tests of which 26 never run by default.

### The folder is under active development

`MCNP_Verification_Tests/error_comparison/` was created **2026-10-02** and holds 102 KB of
paper-figure tooling (`build_se_workbook.py`, `equivalence_analysis.py`, `main_build.py`,
`welch_agreement.py`, `readme_block.py`, `overview.json`). It is self-contained — numpy /
xlsxwriter / pyxlsb plus a local import — and it is the build path for
`photon_standard_error_comparison.xlsx`, per `PHOTON_ERROR_ANALYSIS_HANDOFF.md` at the repo
root. It did not exist when this folder was first surveyed earlier in the same session.

**Conclusion:** the main tree is not a superset of the prototype's coverage, and this folder
is live working tooling, not a dead prototype. Archiving it would have removed 362 live
tests, every verification deck, and the in-flight paper analysis.

---

## 10. Test Suite — Rewrite Inventory  **[NEW 2026-10-03]**

The prototype tests were written against the **April** photon API. Several of the symbols
they import no longer exist in `mcdc/transport/physics/photon/`. Measured by parsing each
test's `from ...photon... import` list and checking each name against the current production
modules, `mcdc/object_/photon*.py` and `mcdc/constant.py`.

`tests` = count of `def test_` functions (287 total; 362 after parametrisation).
`gone` = imported names with no current definition.

### Tier A — import rewrite only (`gone` = 0) — 100 tests

| File | tests |
|---|---|
| `photon_transport_code/test/unit/photon/test_photon_reaction.py` | 37 |
| `photon_transport_code/test/unit/photon/test_phase1_structure.py` | 25 |
| `photon_transport_code/test/unit/photon/test_docstrings.py` | 9 |
| `photon_transport_code/test/unit/photon/conftest.py` | 0 |
| `test/unit/transport/physics/photon/fluorescence.py` | 9 |
| `test/unit/transport/physics/photon/coherent_form_factor.py` | 7 |
| `test/unit/transport/physics/photon/cross_sections.py` | 7 |
| `test/unit/transport/physics/photon/test_energy_deposition.py` | 6 |

The four main-tree files already import `mcdc.*` — they need only the `test_` prefix and
relocation to `test/unit/photon/`. The four prototype files need
`photon_transport_code.transport.physics.photon.*` → `mcdc.transport.physics.photon.*`.

### Tier B — partial rewrite (`gone` = 1–3) — 106 tests

| File | tests | gone | Missing |
|---|---|---|---|
| `test/regression/photon/test_neutron_compatibility.py` | 24 | 3 | `get_element`, `get_material_name`, `get_n_elements` |
| `test/regression/photon/test_photoelectric_absorption.py` | 13 | 3 | `photoelectric_absorption`, `photoelectric_select_shell`, `sample_photoelectric_shell` |
| `test/unit/photon/test_pair_production.py` | 13 | 3 | `build_element_buffer`, `pair_production_xs`, `pair_production_xs_element` |
| `test/unit/photon/test_photoelectric.py` | 9 | 3 | `build_element_buffer`, `photoelectric_xs`, `photoelectric_xs_element` |
| `test/integration/test_photon_reaction_collision.py` | 12 | 2 | `PHOTON_ELEMENT_DTYPE`, `build_element_buffer` |
| `test/unit/photon/test_klein_nishina.py` | 12 | 1 | `klein_nishina_differential` |
| `test/regression/photon/test_pair_production.py` | 12 | 1 | `sample_pair_production` |
| `test/regression/photon/test_compton_scattering.py` | 11 | 1 | `sample_klein_nishina` |
| `test/regression/photon/conftest.py` | 0 | 1 | `build_element_buffer` |

**Fix `test/regression/photon/conftest.py` first.** A conftest import error fails collection
for its whole directory, so that single missing symbol gates **all 80 regression tests**.
Highest-leverage fix in the suite.

### Tier C — substantial rewrite (`gone` ≥ 5) — 110 tests

| File | tests | gone | Missing |
|---|---|---|---|
| `test/unit/photon/test_coverage_gaps.py` | 50 | 5 | `PHOTON_ELEMENT_DTYPE`, `add_photon_material_to_mcdc`, `build_element_buffer`, `pair_production_xs_element`, `total_xs_element` |
| `test/unit/photon/test_distributions.py` | 28 | 6 | `klein_nishina_differential`, `photoelectric_absorption`, `photoelectric_select_shell`, `sample_klein_nishina`, `sample_pair_production`, `sample_photoelectric_shell` |
| `test/regression/photon/test_mixed_interactions.py` | 14 | 7 | `get_densities`, `get_element`, `get_elements`, `get_n_elements`, `photoelectric_absorption`, `sample_klein_nishina`, `sample_pair_production` |
| `test/unit/photon/test_total_xsec.py` | 12 | 5 | `_loglog_interp_python`, `build_element_buffer`, `pair_production_xs`, `photoelectric_xs`, `total_xs` |
| `test/regression/photon/test_performance_benchmark.py` | 6 | 5 | `build_element_buffer`, `photoelectric_absorption`, `photoelectric_select_shell`, `sample_klein_nishina`, `sample_pair_production` |

### Why the symbols vanished — each maps to a decision already in this plan

The tests are stale **in the direction the port is already going**, so rewriting them is part
of the same work rather than extra scope.

| Missing group | Superseded by | Files |
|---|---|---|
| `build_element_buffer`, `PHOTON_ELEMENT_DTYPE` | §4.3 annotated fields + the layer generator. The hand-built flat buffer is exactly what gets deleted | 7 |
| `sample_klein_nishina`, `sample_pair_production`, `sample_photoelectric_shell`, `photoelectric_select_shell`, `klein_nishina_differential`, `photoelectric_absorption` | Folded/renamed into the current `native.py` / `distributions.py` during the July three-way split | 7 |
| `total_xs`, `total_xs_element`, `pair_production_xs(_element)`, `photoelectric_xs(_element)` | §4.4 `macro_xs` → `total_micro_xs` → `reaction_micro_xs` | 4 |
| `get_element`, `get_elements`, `get_densities`, `get_n_elements`, `get_material_name`, `add_photon_material_to_mcdc` | §3 — `photon_material.py` is deleted; use `Element` fields + `Material.element_densities` | 3 |
| `_loglog_interp_python` | `DataTable(..., INTERPOLATION_LOG)` + `evaluate_table` | 1 |

**Sequencing:** do Tier A during Phase 2 as each module lands, Tier B and C in Phase 3 once
the production API is settled. Rewriting Tier C before the API is final means doing it twice.

---

## 11. Smoke-Test References  **[NEW 2026-10-03]**

**Deliverable:** every runnable deck gets a small committed result file beside it, so that
anyone picking up the code has a reference without a cluster run.

**Scope: 30 decks** that `import mcdc` — 9 under `Complex_M&G/`, 6 under
`MCNP_test_problems/`, 2 under `Error-Convergence_testing/`, 11 under `benchmark_*/`, plus
`examples/CARRE_examples/10MeV_cubesat_model.py` and `examples/photon_slab/problem.py`.

**Timing:** last, after all restructuring. A reference generated against a half-ported API is
worthless. Gate it on Phase 3 being green.

**Spec:**

1. **`N_particle = 10_000`** as the default. Drop to `1_000` only where runtime demands it —
   realistically the two `benchmark_5` decks.
2. **Pin the RNG seed.** Without a fixed seed a committed reference cannot be compared
   against anything and the whole exercise is pointless. No deck currently pins one.
3. **Commit two files per deck:** `smoke_1e4.h5` (exact artifact) and `smoke_1e4.txt` (the
   tally table as text). The text file is what makes a regression visible in a PR diff —
   HDF5 is opaque to review.
4. **Size is not a concern.** Tally array size is independent of history count: the AZURV1
   outputs are 97,752 bytes at every history count from 1e6 to 1e9, and the cubesat h5 is
   340 KB. 30 decks lands around 3–12 MB total.
5. **Label them clearly as smoke tests, not validation.** At 1e4 histories the relative
   error is percent-level or worse. These files prove a deck still runs and produces finite,
   physical numbers. They do **not** demonstrate agreement with MCNP — that remains the job
   of the full-history runs and the §7 regression decks.
6. Record the MC/DC commit hash and the date in each `.txt` header.

---

## 12. Paper Artifacts — What Belongs in Git  **[NEW 2026-10-03]**

Relates to `PHOTON_ERROR_ANALYSIS_HANDOFF.md` (repo root) and the standard-error workbook.
The test is **irreplaceable input vs reproducible output**, not "is it paper-related".

### Commit — irreplaceable, and small

| Artifact | Size | Why |
|---|---|---|
| ~~MCNP input decks (`*_MCNP.txt`, `Benchmark5_MCNP_Deck*.txt`)~~ **[SUPERSEDED 2026-10-03]** | 28.7 KB | This row argued they were hand-written ground truth that cannot be regenerated without MCNP. **Owner decision overrides it: no MCNP input deck goes in the repo.** Ignored per §6.3.5. The consequence is that for the §7 decks compared against MCNP, the comparison target is no longer in git — only the MCDC decks and the result tables are. The files stay on disk, so this is reversible |
| MCNP reference result tables (`*_results.txt`) | ~715 KB total `.txt` | Need an MCNP licence and cluster time to reproduce |
| `MCNP_Verification_Tests/error_comparison/*.py` | 102 KB | Source. Builds the workbook |
| Smoke-test references (§11) | ~3–12 MB | The point is that they are committed |
| `PHOTON_ERROR_ANALYSIS_HANDOFF.md` | 14 KB | Same category as `photon-transport-docs/`. **Genericise the absolute paths first** — it currently points at `C:\Users\dwhou\Downloads\...` and a OneDrive `.xlsb`, which resolve for nobody else. Fork-only; do not send upstream |

### Do not commit — reproducible, or bulky, or both

| Artifact | Size | Instead |
|---|---|---|
| 23 SLURM `.out` logs | **1.61 GB** | Already ignored by upstream's `*.out`. Delete locally for disk |
| 76 `.png` plots | 17.6 MB | Regenerate from the plotting scripts. Already covered by upstream's global `*.png` (§6.3.1) |
| 26 `.h5` run products | 2 MB | Superseded in the reference role by §11 smoke files |
| `photon_standard_error_comparison.xlsx` | 145 KB | Build output of `error_comparison/`. Commit the scripts, not the workbook |
| Draft PDF | 1.7 MB | Belongs with the manuscript, not the code repo |

### For the bulky run products, archive rather than discard

The full-history outputs underpin the paper's figures, so they should be citable even though
they do not belong in git. Deposit them in **Zenodo or figshare** for a DOI, and reference
that DOI from `PHOTON_ERROR_ANALYSIS_HANDOFF.md`. That satisfies journal data-availability
requirements, survives independently of the repo, and keeps 1.6 GB out of git history —
where, unlike a working tree, it could never be removed.

---

## 13. Particle-Type Touch-List  **[NEW 2026-10-08]**

Derived mechanically: every file on `mcdc-project/dev` @ `295cd909` that mentions
`PARTICLE_PROTON`, `proton_transport` or `PROTON_REACTION`, ordered by mention count. Proton
is the most recently integrated particle, so **this is the complete set of places a new
particle type touches.** Photon needs an edit in each one except where noted.

Reproduce on whatever tip you branch from — the counts and line numbers will drift:

```bash
git grep -c -E "PARTICLE_PROTON|proton_transport|PROTON_REACTION" mcdc-project/dev \
  -- 'mcdc/*' 'tools/*' 'test/*' 'examples/*' | sort -t: -k2 -rn
```

| File | Proton mentions | Photon action |
|---|---|---|
| `mcdc/transport/physics/proton/native.py` | 17 | **New file** `physics/photon/native.py` |
| `mcdc/object_/proton_reaction.py` | 11 | **New file** `object_/photon_reaction.py` |
| `mcdc/transport/physics/proton/multigroup.py` | 9 | **New file** `physics/photon/constant_xs.py` (different physics, same slot) |
| `mcdc/object_/simulation.py` | 6 | **4 edits** — list declaration `:120`, init `:315`, activation `:365`, loader call `:498`; plus the `set_elements_from_nuclides` gate and the `print_msg` gate |
| `mcdc/transport/physics/interface.py` | 5 | **4 arms** — `particle_speed`, `macro_xs`, `collision_distance` (SigmaT block), `collision` |
| `mcdc/constant.py` | 5 | `PARTICLE_PHOTON = 3` + `PHOTON_REACTION_* = 300..304` + a `PHOTON_CUTOFF_ENERGY` sibling |
| `mcdc/transport/physics/cross_species_production.py` | 3 | **DEFERRED — no edit this PR** (§2.10). Would be 1 arm in the transport-active gate (`:69`–`:73`) once electrons are coupled |
| `mcdc/transport/physics/condensed_interactions.py` | 3 | **NO EDIT** — photons have no continuous slowing-down |
| `mcdc/object_/tally.py` | 3 | particle-type **filter**: string to constant `:323`, label map `:414`, docstring `:82` |
| `mcdc/object_/source.py` | 3 | string to constant `:431`, docstring `:94`, `decode_particle_type` `:546` |
| `mcdc/transport/util.py` | 2 | `PARTICLE_PHOTON` to `"photon"` at `:25` (used for output naming) |
| `mcdc/object_/settings.py` | 1 | `photon_transport: ParticleTransportSettings` field (§2.11, plain `default_factory`) |
| `mcdc/numba_types.py` | 1 | **GENERATED** — never hand-edit; comes from step 8 |
| `mcdc/transport/simulation.py` | 1 | proton-only condensed-interaction gate — **NO EDIT** |
| `test/regression/*/answer.h5` (15 files) | 1 each | **NO EDIT** — the string appears inside stored tally metadata |

Three files proton does **not** touch but photon must, because photon is per-**element** where
proton is per-nuclide:

| File | Photon action | Template |
|---|---|---|
| `mcdc/object_/element.py` | XS fields, reaction lists, subshell binding energies, `set_photon_data()` | the electron half of the same file |
| `mcdc/transport/physics/util.py` | `evaluate_photon_xs_energy_grid` | `evaluate_electron_xs_energy_grid` `:34` |
| `mcdc/object_/material.py` | `photon_constant_xs` kwarg + `has_photon_constant_xs` | `has_neutron_multigroup` `:97` |

And two that are neither, but are required:

| File | Photon action |
|---|---|
| `mcdc/object_/transport_model_data.py` | `PhotonConstantXSData`, mirroring `NeutronMultigroupData` `:30` |
| `mcdc/code_factory/python_objects_compiler.py` | two `isinstance` branches in the dispatch at `:80`–`:118` |

### Object-model conventions every new class must satisfy

From `mcdc/object_/base.py`:

- `MCDCBase` — requires a `label` class attribute; `__init_subclass__` raises without it.
  `non_numba = ()` lists fields the layer generator must skip (e.g. `Material` excludes
  `nuclide_composition` / `element_composition`).
- `MCDCObject` — adds `_compile_into_simulation`, guarded by `compile_ID` so a shared object
  registers once.
- `MCDCPolymorphic` — requires `sub_type`; the base class uses `-1` and each concrete subtype
  uses its `*_REACTION_*` constant. The generator assigns `sub_ID` per `(list, sub_type)`.

`from_h5_group` signatures differ by particle, and photon should follow **electron's**:

```python
# electron - no simulation argument
@classmethod
def from_h5_group(cls, h5_group): ...

# proton - needs simulation to reach simulation.distributions[0] (the shared isotropic)
@classmethod
def from_h5_group(cls, h5_group, simulation): ...
```

Photon needs `simulation` **only** if a photon reaction references a shared distribution
object. Coherent form factors and subshell PE tables are `DataTable`s built from our own
arrays, so the electron signature is sufficient — unless pair production or fluorescence is
modelled with a shared isotropic distribution, in which case take proton's.

---

## 14. Environment Prerequisites  **[NEW 2026-10-08]**

**This is the hard gate on Phase 1, and no revision before this one recorded it.**

`mcdc-env` — the environment in which the 362 prototype tests collect and every benchmark in
§9 was run — **cannot import the upstream tree**:

| | `mcdc-env` (measured) | `mcdc-project/dev` requires |
|---|---|---|
| Python | **3.10.20** | `>=3.11` |
| numba | **0.55.1** | `>=0.61.0,<0.67` |
| numpy | **1.21.5** | `>=2.0.0,<2.5` |
| scipy | — | `<1.19` |
| matplotlib | — | `<3.12` |
| mpi4py | — | `>=3.1.4,<4.2` |
| h5py | — | `<3.17` |
| colorama | — | `<0.5` |
| sympy | — | `<1.15` |

Dev extras: `black<27`, `pre-commit<5`, `pyright<1.2`, `pytest<10`.

### Build a second environment — do not upgrade `mcdc-env` in place

`mcdc-env` is the only place the 362-test baseline in §9 reproduces, and that baseline is the
evidence for the §10 rewrite tiers. Upgrading it destroys the control. Create a parallel
environment instead; the two coexist.

**Python version: 3.13. [SETTLED 2026-10-08 — from upstream's CI, not from caution.]**

The 3.14 references in `pyproject.toml` and `.pre-commit-config.yaml` are real but narrow.
Upstream's workflows show what is actually gated:

| Workflow | Trigger | Python | Runs numba? |
|---|---|---|---|
| `unit_test.yml` | push / PR | **3.13** | yes |
| `regression_test.yml` | push / PR | **3.13** | yes (`--mode numba`) |
| `check_numba_support.yml` | push / PR | **3.13** | yes — regenerates and diffs the Numba layer |
| `docs_test.yml`, `publish-pypi.yml` | push / release | 3.13 | — |
| `regression_test-gpu.yml` | push | `module load python/3.13` | yes |
| `black_lint.yml` | push / PR | 3.14 | **no** — formatter only, never imports mcdc |
| `python_compatibility.yml` | **`workflow_dispatch` only** | 3.11, 3.12, **3.14** | yes |

So the answer to "upstream uses 3.14 and uses numba, why the concern?" is that **upstream does
not run numba on 3.14 in any automatic check.** Every workflow that imports MC/DC or compiles
with numba on push or PR pins **3.13**. 3.14 appears on push/PR in exactly one place — the
black formatter, which never imports the package. `python_compatibility.yml` does run the full
unit and numba-mode regression suites on 3.14, and its existence means upstream believes numba
works there — but it is `workflow_dispatch`, manually triggered, so it is a periodic sweep
rather than a gate, and a 3.14 regression could sit unnoticed between runs.

**Therefore 3.13 is not a hedge against numba — it is the version upstream's own gating CI
proves works.** Building on 3.14 would mean our port is validated only against a configuration
upstream does not continuously test, and any numba failure there would be ours to diagnose
before we could tell whether it was photon's fault.

For the record on numba itself: `numba>=0.61,<0.67` is the pin, and upstream's willingness to
run numba-mode regressions on 3.14 in `python_compatibility.yml` indicates the pinned range
does carry 3.14 support. The concern was never that numba *cannot* work on 3.14; it is that
**3.13 is where the evidence is.**

### The `pre-commit` / black 3.14 problem

`.pre-commit-config.yaml` pins:

```yaml
- repo: https://github.com/psf/black-pre-commit-mirror
  rev: 26.1.0
  hooks:
    - id: black
      language_version: python3.14
```

`language_version` tells pre-commit which interpreter to build the hook's virtualenv with.
**pre-commit cannot install a Python interpreter**, so `pre-commit run --all-files` fails to
bootstrap unless `python3.14` is on `PATH`. No 3.14 interpreter exists on this machine
(`anaconda3` base is 3.9.13, `epics-env` is 3.13.13, `mcdc-env` is 3.10.20).

**[RESOLVED 2026-10-08] Use two interpreters for two different jobs.** This is not a
compromise — it is exactly what upstream's CI does:

| Interpreter | Purpose | Matches |
|---|---|---|
| **3.13** | the environment: numba, pytest, running MC/DC | `unit_test.yml`, `regression_test.yml`, `check_numba_support.yml` |
| **3.14** | the black pre-commit hook only — never imports mcdc | `black_lint.yml` |

So install a standalone Python 3.14 **solely** so `pre-commit` can build the black hook's
virtualenv, and keep the 3.13 conda environment for everything else. Black reformats text and
does not need numba, numpy or MC/DC itself, so the 3.14 install needs no packages beyond what
pre-commit puts in its own venv.

Fallback if a 3.14 install is inconvenient: run `black` directly from the 3.13 environment and
let `black_lint.yml` arbitrate. Black's output is stable across these versions for this
codebase — `[tool.black] target-version` lists py311 through py314, so it is not emitting
version-specific formatting — and generated accessors are `force-exclude`d. This is a safe
fallback, not a silent divergence.

### `MCDC_LIB` — a Phase 2 task, not a prerequisite  **[CORRECTED 2026-10-08]**

`MCDC_LIB` is **unset** in both the user and machine environment, and that has never mattered,
because our photon loader does not read it. `mcdc/transport/physics/photon/data_loader.py:26`
hardcodes the path relative to its own source file:

```python
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "mcdc"
```

That resolves to the repo's own `data/mcdc/` and is why every benchmark in §9 runs today.
`MCDC_LIB` is read only by `object_/material.py:118` and `object_/nuclide.py:62` — the
**neutron** continuous-energy path, which no photon deck exercises.

The port changes this: `Element._compile_into_simulation` is `os.getenv("MCDC_LIB")`-based and
`print_error`s when it is unset. So that hardcoded `DATA_DIR` is **deleted by the port**, and
`MCDC_LIB` must be set from Phase 2 onward. Point it at `C:\Projects\MCDC\data\mcdc` unless the
photon generator (§6.2) writes somewhere else. Generator variables `MCDC_LIB_PHOTON` and
`MCDC_EPDL_LIB` come with §4.

### Verification — the environment is ready when this passes

```bash
python -c "import mcdc; print(mcdc.__file__)"
python -c "import numba, numpy; print(numba.__version__, numpy.__version__)"
python mcdc/code_factory/rebuild_numba_support.py && git diff --stat
pytest test/unit -q
```

The third command must leave `git diff` **empty** on a clean checkout. If regeneration changes
tracked files before you have touched anything, the generator and the committed output
disagree, and that must be understood before any photon field is added — it would otherwise
look like damage from step 8.
