# Photon Transport — Upstream Sync Handoff

Planning state as of 2026-09-18. **No code has been changed yet.** Everything below is
investigation + decisions. Pick up at "Next Steps".

---

## 1. Repo State

| Fact | Value |
|---|---|
| Local branch | `dev` @ `10b7b85e` — this is the **exact merge-base**, 0 commits ahead |
| Upstream | `upstream` = `CEMeNT-PSAAP/MCDC`; `mcdc-project/mcdc` is the same codebase, now CARRE-led |
| Divergence | **715 commits behind** `upstream/dev` (`ae7d416e`) |
| Photon work | **entirely uncommitted** in the working tree (~2300 lines) |

### What changed upstream that matters

- **Electrons landed.** MC/DC is no longer single-particle — there is a complete second
  particle type spanning every layer. **This is the template for photons.**
- Base classes renamed: `ObjectBase/ObjectNonSingleton/ObjectPolymorphic` →
  `MCDCBase/MCDCObject/MCDCPolymorphic`
- Accessor generator: `code_factory/numba_objects_generator.py` →
  `numba_layers_generator.py` (+ `rebuild_numba_support.py`, `literals_generator.py`)
- **Material polymorphism deleted.** No `native_material`/`multigroup_material`/`MATERIAL_*`
  subtypes. One `Material` with `nuclide_composition` **or `element_composition`**.
- Transport arg naming: `mcdc` → `simulation` / `program`
- Energy deposition already exists: `SCORE_ENERGY_DEPOSITION = 200`, `TallyCollision`,
  `collision_data` / `collision_tally`
- Input decks now use a `Simulation` object (`simulation.set_model([...])`, etc.)
- New: `tools/data_library_generator/{neutron,electron}/`
- New docs: `docs/source/developer_guide/extending/extending_the_object_model.rst`

---

## 2. Decisions Made

1. **Approach: Option A — port onto upstream** (not merge). Branch from `upstream/dev` and
   hand-write the photon layer into the electron-shaped slots. Use a **side-by-side git
   worktree** so the old tree stays visible.
2. **Keep the constant-XS capability.** Do NOT delete. `ConstantCrossSectionMaterial`
   becomes `PhotonConstantXSData` in `object_/transport_model_data.py` (mirroring
   `NeutronMultigroupData`) + a `transport/physics/photon/constant_xs.py` treatment module.
   Precedent: `transport/physics/neutron/multigroup.py` is a second treatment dispatched by
   `interface.py` via `applicable()`. This also removes the constant-XS leakage currently in
   `transport/physics/neutron/native.py` (lines 82, 154, 261).
3. **Energy deposition → upstream plumbing.** Retire `SCORE_ENERGY_DEPOSIT = 13`; use
   `SCORE_ENERGY_DEPOSITION = 200` and write into `collision_data["energy_deposition"]`
   inside `native.collision(...)`. Per-branch deposition formulas port as-is.
4. **Reaction constants use the 200 block.** Neutron is 0–6, electron 100–104.
   Photon: `PHOTON_REACTION_TOTAL = 200`, `COHERENT = 201`, `INCOHERENT = 202`,
   `PHOTOELECTRIC = 203`, `PAIR_PRODUCTION = 204`. Current local values (0–4) **collide with
   the neutron block** — a real bug, since `macro_xs()` dispatches on a bare int.
   `PARTICLE_PHOTON = 3` is a free slot (0/1/2 = neutron/electron/proton).
5. **Merge the data library** — one element file per element carrying both particles.
6. **7 regression decks** (see §6), migrated to the `Simulation` API.
7. **Library generator** goes to `tools/data_library_generator/photon/`.

---

## 3. Target Structure

```
mcdc/constant.py                        + PARTICLE_PHOTON, PHOTON_REACTION_* = 200..204
mcdc/object_/photon_reaction.py         PhotonReactionBase(MCDCPolymorphic), 4 subtypes,
                                          label + sub_type + @classmethod from_h5_group
                                          (NO perform_collision — physics lives in transport/)
mcdc/object_/element.py                 + photon_* xs fields, photon_*_reactions lists,
                                          photon_subshell_binding_energy, set_photon_data()
mcdc/object_/simulation.py              + element.set_photon_data(self)  (~line 409)
mcdc/object_/transport_model_data.py    + PhotonConstantXSData
mcdc/object_/material.py                + photon_constant_xs kwarg + classmethod
mcdc/object_/source.py                  + "photon" to particle_type
mcdc/transport/physics/util.py          + evaluate_photon_xs_energy_grid
mcdc/transport/physics/photon/
  interface.py                          thin; constant_xs.applicable() dispatch
  native.py                             macro_xs / total_micro_xs / reaction_micro_xs
                                          + collision + one section per reaction (~550 lines)
  constant_xs.py                        applicable / particle_speed / macro_xs / collision
mcdc/transport/physics/interface.py     + PARTICLE_PHOTON branches
tools/data_library_generator/photon/    generate.py + README.md
test/regression/<7 decks>/
```

`mcdc_get/` and `mcdc_set/` are **generated** — never hand-written. Run
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
| `mcdc_get\|set/photon_*.py`, `constant_xs_material.py` | Delete, regenerate |
| `test/unit/transport/physics/photon/*.py` | Rename with `test_` prefix, relocate to upstream layout |

**Already exists upstream — delete your copies:**
- `scatter_direction` → `transport/physics/util.py` (identical)
- `log_log_interpolation` → `DataTable(..., INTERPOLATION_LOG)` + `evaluate_table`
- `interpolate_xs` / `find_energy_bin` → `evaluate_photon_xs_energy_grid` + `find_bin`

---

## 4. Cross-Section Pattern (neutron and electron are identical)

1. **Library file** — one HDF5 per carrier in `$MCDC_LIB` (neutron: per-nuclide; electron:
   per-element). Shared `xs_energy_grid` + per-reaction `MT-nnn/xs` with an **`offset`
   attribute** indexing into that grid.
2. **Loader** — `set_{neutron,electron}_data(simulation)`, called from
   `Simulation._finalize_compilation` (`simulation.py:403,409`). Sums per-type XS, derives
   total, builds reactions via `from_h5_group`, registers them.
3. **Annotated fields** — plain `NDArray[float64]` annotations on `Nuclide`/`Element`. The
   layer generator packs them into flat `data` and emits accessors. **Never build the flat
   buffer by hand** — this is what `PhotonMaterial.flat_data` gets replaced by.
4. **Runtime** — `macro_xs()` (density-weighted loop over material elements) →
   `total_micro_xs()` (dispatch on reaction_type) → `reaction_micro_xs()` (applies
   `reaction["xs_offset_"]`, returns 0.0 below it). Grid search in `transport/physics/util.py`.
5. **Sub-tabulated data** — anything with its own grid becomes `DataTable` /
   `DistributionMultiTable`, not a packed array. `DataTable` supports piecewise
   `interpolations` + `interpolation_boundaries`; `INTERPOLATION_LOG = 5` is log-log.

### flat_data → annotated fields

| `flat_data` section | Becomes |
|---|---|
| energy grid | `Element.photon_xs_energy_grid` |
| Compton/coherent/PE/pair XS | `Element.photon_{incoherent,coherent,photoelectric,pair_production}_xs` |
| total XS | `Element.photon_total_xs` (derived in loader) |
| per-element densities | already `Material.element_densities` — delete yours |
| coherent form factor | `PhotonReactionCoherent.form_factor: DataBase` → `DataTable(q, F, INTERPOLATION_LOG)` |
| shell-resolved PE XS | `PhotonReactionPhotoelectric.N_subshell` + `subshell_xs: list[DataBase]` (mirrors `ElectronReactionIonization`) |
| shell binding energies | `Element.photon_subshell_binding_energy` |
| fluorescence lines | Use upstream's top-level `atomic_relaxation/` group |

### Data library merge

Your `data/mcdc/*.h5` are **photon-only** element files. Upstream's `Al.h5` has
`electron_reactions/` + `atomic_relaxation/`. **Same filename**, and upstream's generator
opens with mode `"w"` (truncating). Target:

```
$MCDC_LIB/Al.h5
├── element_symbol, atomic_number, atomic_weight_ratio
├── electron_reactions/      <- electron generator
├── photon_reactions/        <- your generator, mode "a"
└── atomic_relaxation/       <- shared by both
```

Schema fixes needed in your files: `element_name` → `element_symbol`; **add the `offset`
attribute on every `xs` dataset** (upstream reads it unconditionally → `KeyError` without
it); drop `excitation_level`/`fissionable` (nuclide fields); move relaxation to top level;
open with `"a"` not `"w"`.

---

## 5. Open Items

1. **ENERGY UNITS — verify first, highest risk.** Runtime unit is **eV** (`Source.energy` is
   eV; `Nuclide.set_neutron_data` does `* 1e6  # MeV to eV`). But the electron library is
   written in MeV and `Element.set_electron_data` does **no conversion**, while the Lockwood
   electron regression runs at `ENERGY = 1e4  # eV`. Possible upstream bug — unresolved.
   Regardless: your photon code is MeV-native (Klein-Nishina, 1.022 MeV threshold, cm/ns), so
   **convert MeV→eV in the loader** per the neutron precedent, then work in eV.
2. **Relaxation source.** Upstream ships `atomic_relaxation/` from EPRDATA14; yours is EADL.
   Compare before reusing upstream's — your validated fluorescence results depend on it.
3. **`.gitignore`** — gates the step-0 commit, not yet drafted. See below.
4. **`data/` cleanup** — which of `data/mcdc/` (204M), `data/mcdc_reformatted/` (196M),
   `data/mcdc.backup/` (262M) is authoritative? Not yet determined. `data/` totals 859 MB.
5. **Raise with maintainers**: photon constant allocations (`PARTICLE_PHOTON = 3`, 200 block);
   whether they intend a photon path from EPRDATA14 (it contains photon data) vs your EPDL
   route (shell-resolved PE + coherent form factors, likely higher fidelity).
6. **Coverage gaps** in the chosen decks: no energy-deposition deck (the tally being
   rewritten), and fluorescence is effectively untested (both Pb decks at 10 MeV; Pb K-edge
   is 88 keV). Unit tests still cover both.

### .gitignore

Already covered locally: `*.h5` (blanket), `photon-transport-docs/`, `.coverage`,
`mcnp_val_extracted.txt`, `MCNP_validation_test.pdf`, `examine_*.py`, `.claude/`.

**Not covered — would land in the step-0 commit:**
- `data/endf/**/*.endf` — 300 files, **116 MB** (not matched by `*.h5`)
- `photon-transport-directions/` (17 planning .md files)
- `photon_transport_code/` (the duplicate tree)
- root `validate_*.py`, `visualize_output.py`

**Delete rather than ignore:** `data/mcdc.backup/`, `data/mcdc_reformatted/` (458 MB of
stale duplicates).

**Conflict warning:** `.gitignore` has 23 uncommitted local insertions AND upstream rewrote
it (42+/40-). Take upstream's version first, then re-add photon rules — **scoped**, since the
blanket `*.h5` is a local invention (upstream uses narrow rules: `*output.h5`, `output*.h5`,
`dummy_nuclide.h5`, `source_particles.h5`).

---

## 6. The 7 Decks

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

## 7. Next Steps

**Blocked on:** `.gitignore` draft, and deciding which `data/` library is authoritative.

```bash
cd /c/Projects/MCDC

# 0. Fix .gitignore FIRST, then snapshot
git checkout -b photon-wip
git add -A
git status            # REVIEW: nothing from data/ should appear
git commit -m "WIP: photon transport before upstream sync"

# 1. Park old tree side by side
git worktree add ../MCDC-photon-old photon-wip
#    open ../MCDC-photon-old in a second VSCode window

# 2. Sync (fast-forwards 715 commits once the tree is clean)
git checkout dev
git merge --ff-only upstream/dev

# 3. Port branch
git checkout -b photon-transport
```

Then: port the photon layer per §3/§4, regenerate Numba support, migrate the 7 decks,
write the library merge script.

Cleanup when done: `git worktree remove ../MCDC-photon-old`
