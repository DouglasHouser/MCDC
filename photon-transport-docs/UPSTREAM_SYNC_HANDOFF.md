# Photon Transport — Upstream Sync Handoff

Planning state as of **2026-10-03**. **No code has been changed yet.** Everything below is
investigation + decisions. Pick up at §8 "Execution".

Supersedes the 2026-09-18 revision. New findings in this revision are marked **[NEW]**;
corrections to the previous revision are marked **[CORRECTED]**.

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
| `origin` | `DouglasHouser/MCDC` (fork) |
| `upstream` | `CEMeNT-PSAAP/MCDC`; `mcdc-project/mcdc` is the same codebase, now CARRE-led |
| Local branch | `dev` @ `86ee515a` — **5 commits ahead** of the merge base, and **already pushed** (`dev` == `origin/dev`) **[CORRECTED 2026-10-03]** |
| Merge base | `10b7b85e` (PR #385) |
| Divergence | **5 ours / 715 theirs** vs `upstream/dev` (`ae7d416e`, PR #523) |
| Our 5 commits | **markdown only** — `photon-transport-docs/`, `photon-transport-directions/` (~9,500 lines) |
| Photon code | **entirely uncommitted** in the working tree (~2,300 lines, 28 files, ~113 KB) |

**[CORRECTED] `git merge --ff-only upstream/dev` will now fail.** The previous revision
recorded `dev` as sitting exactly on the merge base with 0 commits ahead. It now carries 2
docs commits, so the fast-forward in the old §7 is no longer valid. Phase 1 below branches
from `upstream/dev` directly instead.

### What changed upstream that matters

- **Electrons landed.** MC/DC is no longer single-particle — there is a complete second
  particle type spanning every layer. **This is the template for photons.** `mcdc_get/
  photon_reaction.py` and upstream's `mcdc_get/electron_reaction.py` are byte-identical
  modulo the word "photon", because both come from the same generator.
- Base classes renamed: `ObjectBase` / `ObjectNonSingleton` / `ObjectPolymorphic` →
  `MCDCBase` / `MCDCObject` / `MCDCPolymorphic`
- Accessor generator: `code_factory/numba_objects_generator.py` →
  `numba_layers_generator.py` (+ `rebuild_numba_support.py`, `literals_generator.py`,
  `python_objects_compiler.py`)
- **Material polymorphism deleted.** No `MaterialBase` / `MaterialMG` /
  `native_material` / `multigroup_material` / `MATERIAL_*` subtypes. One `Material` with
  `nuclide_composition` **or `element_composition`**.
- Transport arg naming: `mcdc` → `simulation` / `program`. `collision()` is now
  `collision(particle_container, collision_data_container, program, data)`.
- **Energy deposition already exists:** `SCORE_ENERGY_DEPOSITION = 200`, collision tallies,
  `collision_data["energy_deposition"]`, plus `test/unit/tally/test_energy_deposition.py`
  and `test_collision_tally.py`. **[NEW]**
- New: `tools/data_library_generator/{neutron,electron}/`
- New docs: `docs/source/developer_guide/extending/extending_the_object_model.rst`
- **[NEW]** `.pre-commit-config.yaml` pins **black 26.1.0 / python3.14** (ours is older) —
  reformat or CI fails.

---

## 2. Decisions Made

1. **Approach: port onto upstream, do not merge.** Branch from `upstream/dev` and hand-write
   the photon layer into the electron-shaped slots. 715 commits against whole-file rewrites
   of `tally.py` (+714), `source.py` (+566), `score.py` (+345), `simulation.py` (+306)
   produces a conflict set larger than the code itself — and git cannot know that our
   `score.py` additions should be **discarded** rather than reconciled. Use a **side-by-side
   git worktree** so the old tree stays visible.
2. **Keep the constant-XS capability, photon-only.** `ConstantCrossSectionMaterial` becomes
   `PhotonConstantXSData` in `object_/transport_model_data.py` (mirroring
   `NeutronMultigroupData`) + a `transport/physics/photon/constant_xs.py` treatment module.
   Precedent: `transport/physics/neutron/multigroup.py:36` defines `applicable()` as a second
   treatment dispatched by `interface.py`. **[NEW] Drop the neutron constant-XS additions**
   to `transport/physics/neutron/native.py` (lines 82, 154, 261) — upstream's one-group
   `Material.multigroup(...)` already covers the Case / de Hoffmann–Placzek benchmark.
3. **Energy deposition → upstream plumbing.** Retire `SCORE_ENERGY_DEPOSIT = 13`; use
   `SCORE_ENERGY_DEPOSITION = 200` and write into `collision_data["energy_deposition"]`
   inside `native.collision(...)`. Per-branch deposition formulas port as-is. **Delete
   outright:** the `tally.py` score plumbing, the 81 `score.py` lines, and
   `_score_energy_deposition` in `simulation.py` — `score.collision()` already consumes the
   container.
4. **Reaction constants use the 200 block.** Neutron is 0–6, electron 100–104.
   Photon: `PHOTON_REACTION_TOTAL = 200`, `COHERENT = 201`, `INCOHERENT = 202`,
   `PHOTOELECTRIC = 203`, `PAIR_PRODUCTION = 204`. Current local values (0–4) **collide with
   the neutron block** — a real bug, since `macro_xs()` dispatches on a bare int.
   `PARTICLE_PHOTON = 3` is a free slot (0/1/2 = neutron/electron/proton).
5. **Merge the data library** — one element file per element carrying both particles.
6. **7 regression decks** (see §7), migrated to the `Simulation` API.
7. **Library generator** goes to `tools/data_library_generator/photon/`.
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

---

## 3. Target Structure

```
mcdc/constant.py                        + PARTICLE_PHOTON, PHOTON_REACTION_* = 200..204
mcdc/object_/photon_reaction.py         PhotonReactionBase(MCDCPolymorphic), 4 subtypes,
                                          label + sub_type + @classmethod from_h5_group
                                          (NO perform_collision — physics lives in transport/)
mcdc/object_/element.py                 + photon_* xs fields, photon_*_reactions lists,
                                          photon_subshell_binding_energy, set_photon_data()
mcdc/object_/simulation.py              + element.set_photon_data(self)  (~line 409,
                                          inside _finalize_compilation at line 299)
mcdc/object_/transport_model_data.py    + PhotonConstantXSData
mcdc/object_/material.py                + photon_constant_xs kwarg + classmethod
mcdc/object_/source.py                  + "photon" to particle_type
mcdc/object_/settings.py                + photon_transport flag (set_transported_particles,
                                          line 243)
mcdc/transport/physics/util.py          + evaluate_photon_xs_energy_grid
                                          (third sibling of evaluate_{neutron,electron}_...)
mcdc/transport/physics/photon/
  interface.py                          thin; constant_xs.applicable() dispatch
  native.py                             macro_xs / total_micro_xs / reaction_micro_xs
                                          + collision + one section per reaction (~550 lines)
  constant_xs.py                        applicable / particle_speed / macro_xs / collision
mcdc/transport/physics/interface.py     + PARTICLE_PHOTON branches
mcdc/code_factory/python_objects_compiler.py
                                        + PhotonReactionBase branch (mirrors
                                          ElectronReactionBase / Element)
tools/data_library_generator/photon/    generate.py + README.md
test/unit/photon/                       relocated unit tests
test/regression/<7 decks>/
```

`mcdc_get/`, `mcdc_set/` and `numba_types.py` are **generated** — never hand-written. Run
`python mcdc/code_factory/rebuild_numba_support.py`.

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
| `photon_transport_code/MCNP_Verification_Tests/**/*.py` (628 KB) | **Keep.** All decks `import mcdc`, so they are production-bound, not prototype-bound. Migrate the 7 chosen decks (§7) to `test/regression/` |
| `photon_transport_code/examples/CARRE_examples/` (cubesat), `examples/photon_slab/` | **Keep.** Both `import mcdc` |
| `photon_transport_code/test/` (**362 live tests**) | **Port alongside the physics.** Rewrite imports `photon_transport_code.transport.physics.photon.*` → `mcdc.transport.physics.photon.*`. This is the bulk of the real photon coverage |
| `photon_transport_code/{transport,mcdc_get,mcdc_set}/`, `conftest.py`, `__init__.py` | Archive, then delete — the genuinely superseded duplicate source, and the only part "archive" ever should have referred to |
| `photon_transport_code/examples/photon_transport_{compton,pair_production,photoelectric}/`, `debugging/`, `docs/` | Prototype-bound (`import photon_transport_code.*`); port or retire deliberately |
| `photon_transport_code/**/*.{out,log,png}` (1.63 GB) | gitignore — upstream ignores `*.out` and `*.png`, but **not** `*.log`; §6.3.5 adds a scoped rule for the one 3.4 MB log. Delete locally for disk space; never committed |
| **[NEW]** root `validate_*.py`, `compare_photon_xs.py`, `photon_issue_isolator.py`, `visualize_output.py` | Archive; upstream's root carries no loose scripts |

**Already exists upstream — delete our copies:**
- `scatter_direction` → `transport/physics/util.py:35` (identical)
- `log_log_interpolation` → `DataTable(..., INTERPOLATION_LOG)` + `evaluate_table`
- `interpolate_xs` / `find_energy_bin` → `evaluate_photon_xs_energy_grid` +
  `find_bin` (**[CORRECTED]** `find_bin` lives in `transport/util.py:98`, not
  `transport/physics/util.py`)

---

## 4. Cross-Section Pattern (neutron and electron are identical)

1. **Library file** — one HDF5 per carrier in `$MCDC_LIB` (neutron: per-nuclide; electron:
   per-element). Shared `xs_energy_grid` + per-reaction `MT-nnn/xs` with an **`offset`
   attribute** indexing into that grid.
2. **Loader** — `set_{neutron,electron}_data(simulation)`, called from
   `Simulation._finalize_compilation` (`simulation.py:403`, `:409`). Sums per-type XS,
   derives total, builds reactions via `from_h5_group`, registers them.
3. **Annotated fields** — plain `NDArray[float64]` annotations on `Nuclide` / `Element`. The
   layer generator packs them into flat `data` and emits accessors. **Never build the flat
   buffer by hand** — this is what `PhotonMaterial.flat_data` gets replaced by.
4. **Runtime** — `macro_xs()` (density-weighted loop over material elements) →
   `total_micro_xs()` (dispatch on reaction_type) → `reaction_micro_xs()` (applies
   `reaction["xs_offset_"]`, returns 0.0 below it).
5. **Sub-tabulated data** — anything with its own grid becomes `DataTable` /
   `DistributionMultiTable`, not a packed array. `DataTable` supports piecewise
   `interpolations` + `interpolation_boundaries`; `INTERPOLATION_LOG = 5` is log-log.

### flat_data → annotated fields

| `flat_data` section | Becomes |
|---|---|
| energy grid | `Element.photon_xs_energy_grid` |
| Compton/coherent/PE/pair XS | `Element.photon_{incoherent,coherent,photoelectric,pair_production}_xs` |
| total XS | `Element.photon_total_xs` (derived in loader) |
| per-element densities | already `Material.element_densities` — delete ours |
| coherent form factor | `PhotonReactionCoherent.form_factor: DataBase` → `DataTable(q, F, INTERPOLATION_LOG)` |
| shell-resolved PE XS | `PhotonReactionPhotoelectric.N_subshell` + `subshell_xs: list[DataBase]` (mirrors `ElectronReactionIonization`) |
| shell binding energies | `Element.photon_subshell_binding_energy` |
| fluorescence lines | Our EADL data, written at upstream's top-level `atomic_relaxation/` path |

### Data library merge

Our `data/mcdc/*.h5` are **photon-only** element files. Upstream's `Al.h5` has
`electron_reactions/` + `atomic_relaxation/`. **Same filename**, and upstream's generator
opens with mode `"w"` (truncating). Target:

```
$MCDC_LIB/Al.h5
├── element_symbol, atomic_number, atomic_weight_ratio
├── electron_reactions/      <- electron generator (mode "w", runs first)
├── photon_reactions/        <- our generator (mode "a", runs second)
└── atomic_relaxation/       <- shared location; our EADL data (decision §2.9)
```

Schema fixes needed in our files:

- `element_name` → `element_symbol`
- **Add the `offset` attribute on every `xs` dataset.** **[NEW] Confirmed critical:**
  `element.py` does `xs_container[xs.attrs["offset"]:] += xs[()]` unconditionally, and all
  four of our `xs` datasets currently have **empty attrs** → `KeyError` without it.
- Convert **eV → MeV** and **cm² → barns** on disk (see §6.1 before committing to this)
- Drop `excitation_level` / `fissionable` (nuclide fields, not element fields)
- Move relaxation from `photon_reactions/atomic_relaxation/subshells/<shell>/` to top-level
  `atomic_relaxation/MT-NNN/` with upstream's dataset names
- Open with `"a"` not `"w"`
- **[NEW]** Raise with maintainers: upstream's electron generator must either switch to
  `"a"` or be guaranteed to run first, or the two generators will clobber each other.

---

## 5. Phases

### Phase 0 — Snapshot first (~15 min, zero risk)

Nothing else happens until the work is recoverable. 2,300 lines of photon source currently
exist only in the working tree.

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

```
git checkout -b feature/photon-transport upstream/dev
```

Re-apply onto pristine upstream using the Phase 0 snapshot as reference.

### Phase 2 — Re-apply in dependency order

Per §3 and §4. Every step has an electron twin to copy:

| Step | Template |
|---|---|
| Photon constants in the 200 block, `PARTICLE_PHOTON = 3` | `constant.py` electron block |
| `object_/photon_reaction.py` on `MCDCPolymorphic` | `object_/electron_reaction.py` |
| Photon XS fields + `set_photon_data()` on `Element` | `object_/element.py:82` |
| `PhotonConstantXSData` | `NeutronMultigroupData` in `transport_model_data.py` |
| `constant_xs.py` treatment + `applicable()` | `physics/neutron/multigroup.py:36` |
| Register in `python_objects_compiler.py` | its `ElectronReactionBase` / `Element` branches |
| **Regenerate** `mcdc_get/`, `mcdc_set/`, `numba_types.py` | `rebuild_numba_support.py` |
| `transport/physics/photon/` with new signatures | `transport/physics/electron/` |
| Dispatch arms in `physics/interface.py` | its `PARTICLE_ELECTRON` arms |
| `photon_transport` flag | `settings.py:243` |
| `"photon"` source type | `object_/source.py` |
| `tools/data_library_generator/photon/` (mode `"a"`) | `tools/data_library_generator/electron/` |

Mechanical renames throughout: `mcdc` → `simulation` (~100 sites in the photon files),
`ObjectPolymorphic` → `MCDCPolymorphic`, `ObjectSingleton` / `ObjectNonSingleton` →
`MCDCObject`. `MaterialBase` / `MaterialMG` and the `MATERIAL_*` `child_type` dispatch are
gone — rehome onto `Material.element_composition`.

### Phase 3 — Validate

1. `pre-commit run --all-files` against upstream's pinned black 26.1.0 / py3.14.
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
5. **[NEW]** Generate the smoke-test references for all 30 decks — **§11**. Last step; gate
   it on items 1–4 being green.

### Phase 4 — Publish

Push `feature/photon-transport` to `origin`. For a CEMeNT-PSAAP PR, split by layer
(data/objects → physics → tooling → tests) rather than one 2,300-line drop.
`photon-transport-docs/` and `photon-transport-directions/` (9,500 lines at repo root)
should not go up as-is — upstream's root carries no loose directories. Fold the durable
parts into `docs/` or keep them fork-only.

---

## 6. Open Items

1. **ENERGY UNITS — verify first, highest risk.** Runtime unit is **eV** (`Source.energy` is
   eV; `Nuclide.set_neutron_data` does `* 1e6  # MeV to eV`). But the electron library is
   written in MeV and `Element.set_electron_data` does **no conversion**, while the Lockwood
   electron regression runs at `ENERGY = 1e4  # eV`. Possible upstream bug — unresolved.
   Regardless: our photon code is MeV-native (Klein–Nishina, 1.022 MeV threshold, cm/ns), so
   **convert MeV→eV in the loader** per the neutron precedent, then work in eV. This
   interacts with the §4 decision to store MeV on disk — settle the runtime unit before
   rewriting the library.
2. **Relaxation source.** Upstream ships `atomic_relaxation/` from EPRDATA14; ours is EADL.
   Decision §2.9 keeps ours, but the two should still be compared — if they agree, consuming
   upstream's removes a generator stage; if they disagree, our validated fluorescence
   numbers tell us which to trust.
3. **`data/` cleanup — [NEW] resolved.** `data/mcdc/` (204 MB) is authoritative; it is what
   `data_loader.py` reads. `data/mcdc.backup/` (262 MB) and `data/mcdc_reformatted/`
   (196 MB) are stale duplicates — **458 MB, delete**. `data/` totals 872 MB.
4. **Raise with maintainers**: photon constant allocations (`PARTICLE_PHOTON = 3`, the 200
   block); the generator file-mode collision (§4); and whether they intend their own photon
   path from EPRDATA14 vs our EPDL route (shell-resolved PE + coherent form factors, finer
   grid, 1 eV floor).
5. **Coverage gaps** in the chosen decks: no energy-deposition deck (the tally being
   rewritten), and fluorescence is effectively untested (both Pb decks at 10 MeV; Pb K-edge
   is 88 keV). Unit tests still cover both.

### 6.3 `.gitignore` — full specification  **[REWRITTEN 2026-10-03]**

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
| Named decks and scripts under `Complex_M&G/` | 9 | `lead_finite_cylinder.py`, `lead_finite_cylinder_energy_deposition.py`, `multi_material_slabs.py`, `multi_material_spheres.py`, `multi_material_spheres_energy_spectrum.py`, `multi_material_spheres_energy_spectrum_results.txt`, `Convergence/compare_mcdc_mcnp_spectrum_1e7.py`, `Convergence/compare_mcdc_mcnp_spectrum_1e7_postprocessed.py`, `Convergence/mm_spheres_1to10mev_sdev_convergence.py` |
| `Complex_M&G/1e7_results/comparisons/` | 4 | Whole folder |
| `test/regression/azurv1/input.py` | 1 | Local edits were photon experimentation; working version lives on `dev` |

Every one is an exact path or scoped glob, so the four §7 decks that share name prefixes are
unaffected, and every excluded file remains on disk untracked — each decision is reversible.

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
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/lead_finite_cylinder.py
photon_transport_code/MCNP_Verification_Tests/Complex_M&G/lead_finite_cylinder_energy_deposition.py
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

#### 6.3.6 Verification gate — run before staging anything

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

# 6c. The four section 7 decks sharing name prefixes MUST survive. Expect 4.
git status --porcelain -uall | grep -cE 'lead_finite_cylinder_off_center\.py|multi_material_slabs_collimated_beam\.py|multi_material_slabs_mesh_tally\.py|multi_material_spheres_1to10mev_spectrum\.py'

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
Phase 0 block above, **and** upstream rewrote the file across the 715-commit divergence.
Resolution order is not negotiable:

1. Take **upstream's version wholesale** — `git checkout upstream/dev -- .gitignore`.
2. Re-add only what §6.3.5 justifies, minus anything upstream has since absorbed. Re-check
   §6.3.1 against the new file rather than assuming the line numbers above still hold.
3. Drop the blanket `*.h5` at this point (§6.3.4) and re-run the §6.3.6 audit.
4. `data/` is fork-only — upstream fetches its libraries. Keep the rule locally, but it does
   not go up in the Phase 4 PR.
---

## 7. The 7 Decks

All under `photon_transport_code/MCNP_Verification_Tests/`:

1. `Complex_M&G/lead_finite_cylinder_off_center.py`
2. `Complex_M&G/multi_material_slabs_collimated_beam.py`
3. `Complex_M&G/multi_material_slabs_mesh_tally.py`
4. `Complex_M&G/multi_material_spheres_1to10mev_spectrum.py`
5. `Error-Convergence_testing/AZURV1_photon_v3.py`  (constant-XS treatment)
6. `MCNP_test_problems/10mev_al_spheres.py`
7. `MCNP_test_problems/10mev_pb_spheres.py`

(30 photon decks exist total; the other 23 are variants/duplicates. Nothing lands in
`examples/`, so upstream's example-validator obligation does not apply.)

---

## 8. Execution

**Blocked on:** nothing. §6.1 (energy units) and §6.2 (relaxation comparison) can be settled
during Phase 2; §6.3 is resolved.

```
cd /c/Projects/MCDC

# 0. Fix .gitignore FIRST, then snapshot
git checkout -b wip/photon-snapshot-pre-refactor
git add -A
git status            # REVIEW: no data/, and no .out/.log/.png from photon_transport_code/.
                      # The folder's .py files SHOULD appear — see §3.
git commit -m "WIP: photon transport before upstream sync"
git push -u origin wip/photon-snapshot-pre-refactor

# 1. Park the old tree side by side
git worktree add ../MCDC-photon-old wip/photon-snapshot-pre-refactor
#    open ../MCDC-photon-old in a second editor window

# 2. Port branch, straight off upstream (NOT a merge, NOT a fast-forward)
git fetch upstream
git checkout -b feature/photon-transport upstream/dev
```

Then: port the photon layer per §3/§4, regenerate Numba support with
`rebuild_numba_support.py`, migrate the 7 decks, write the library merge script.

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
| ~~MCNP input decks (`*_MCNP.txt`, `Benchmark5_MCNP_Deck*.txt`)~~ **[SUPERSEDED 2026-10-03]** | 28.7 KB | This row argued they were hand-written ground truth that cannot be regenerated without MCNP. **Owner decision overrides it: no MCNP input deck goes in the repo.** Ignored per §6.3.5. The consequence is that for the four §7 decks compared against MCNP, the comparison target is no longer in git — only the MCDC decks and the result tables are. The files stay on disk, so this is reversible |
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
