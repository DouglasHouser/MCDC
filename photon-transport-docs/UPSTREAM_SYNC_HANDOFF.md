# Photon Transport — Upstream Sync Handoff

Planning state as of **2026-10-08**. **Phase 0 is complete and pushed. Phase 1 is COMPLETE —
see §15. Phase 2 is cleared to start and has not begun.** Phases 3–4 are unstarted.
Pick up at §15's handover, then §5 Phase 2.

**§15 records three discoveries made while executing Phase 1.** None of them blocks Phase 2.
The largest is that a **populated photon HDF5 schema already exists** in
`mcdc-project/mcdc-regression_test_data`, which contradicts §2.8 and settles three details
§6.2 had to guess — group names, the on-disk energy unit, and the pair-production MT numbers.
§6.2 plus the electron generator were already sufficient to write the generator; the
discovered file is a **free cross-check**, and §15.4 resolves each detail in its favour on the
standing principle that matching a real upstream artifact beats matching an invented
convention.

**[OWNER DECISIONS 2026-10-08 — three operating rules that apply to every phase]**

1. **Everything runs on Python 3.13.** No 3.14 is installed and none is needed. Format with
   `python -m black .`, never `pre-commit`, and **do not run `pre-commit install`** — upstream's
   config pins `python3.14` and the hook cannot bootstrap here. Measured equivalent: §14.
2. **`origin` is the only writable remote.** The push URLs on `mcdc-project` and `upstream` are
   disarmed (§1). All work lands on branches in `DouglasHouser/MCDC`.
3. **The owner assembles the PR to `mcdc-project/mcdc` at the end.** §5 Phase 4's
   open-a-PR step is the owner's; what binds the port is Phase 4's *content* — the
   `CHANGELOG.md` entry, the five docs pages, and the PR-template fields.
4. **The artifact wins.** Where a real upstream artifact — a file in the tree, a dataset in
   the regression library, a generated accessor, a passing test — disagrees with a convention
   stated in this document, **the artifact is right and this document is wrong.** Follow the
   artifact, then fix the text and say so. No part of this plan is evidence about upstream;
   it is only ever a reading of it, and 1,060 commits have passed under it. This is not a new
   rule — it is what §6.2 already meant by "adopt **upstream's** layout" — but it was
   implicit, and being implicit cost one unnecessary escalation (§15.4). It applies to every
   phase, and it is never a reason to ask rather than to proceed.

**Audited end to end on 2026-10-08**: all 35 source line anchors verified against
`mcdc-project/dev` @ `295cd909`, all cross-references resolve, and the contradictions
introduced by this revision's own rewrites were swept out. See the §8 readiness table.
**[AMENDED by the second audit]** 38 anchors were re-checked independently against the same
tip: **33 landed exactly and 5 were off by ≤2 lines**, each pointing at a decorator or at the
line above its target. All five are fixed in place and marked **[ANCHOR FIX]**. Two anchors
were wrong outright rather than off by a line — both in §14's `MCDC_LIB` paragraph, corrected
there.

**[SECOND AUDIT 2026-10-08 — the environment gate was not actually green]** The audit above
checked the document for internal consistency and checked its anchors against the remote. It
did **not** execute §14's own four-command readiness gate. That gate was then run, against a
throwaway worktree of `mcdc-project/dev` @ `295cd909`, and **its fourth command failed**:
`pytest test/unit` produced **29 collection errors**, every one
`ModuleNotFoundError: No module named 'cffi'`. Two environment defects were behind it, both
now fixed and both recorded in §14:

1. **`cffi>=1.17.1,<3` was missing.** It is upstream's *first* declared runtime dependency and
   §14's table omitted it entirely.
2. **MC/DC itself was never installed into `mcdc-upstream`.** §14's check
   `python -c "import mcdc"` passes on a CWD-relative import, which masked it; the first test
   to call `importlib.metadata.version("mcdc")` did not.

Root cause: §14 built the environment by hand-transcribing pins out of `pyproject.toml`
instead of running upstream's documented developer setup, `python -m pip install -e ".[dev]"`,
which resolves both automatically. **The gate now passes in full — 405 passed, `git diff`
empty after regeneration.** See §14's "Gate result".

Four further gaps found by the same audit, all corrected below: **§13's touch-list is
incomplete by construction** (its grep cannot see bare lowercase `"proton"`, and the delta
includes a CI-gated file — §13); **Phase 4 carries an undocumented `CHANGELOG.md` and docs
obligation** (§5 Phase 4); **the regression harness has no answer-generation flag** (§7); and
**§1's post-snapshot commit table was stale** (§1). Minor anchor corrections are marked
**[ANCHOR FIX]** in place.

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
  dropped from the plan. **Nor is any merge needed** — §2.10 scopes this PR to photon-only
  transport, so a photon-only library is complete; see §6.2 for the `generate.py` + `util.py`
  plan that replaces the merge tool an earlier draft proposed.

**[NEW 2026-10-08] §14 Environment prerequisites** is new, was the last hard gate on Phase 1,
and is **now satisfied — but only after the second audit; see the block above.** `mcdc-env` (Python 3.10, numba 0.55.1, numpy 1.21.5) **cannot import
the upstream tree**, which requires Python ≥ 3.11, numba ≥ 0.61 and numpy ≥ 2.0 — no revision
before this one recorded that. A second environment, **`mcdc-upstream`** (Python 3.13.16,
numba 0.66.0, numpy 2.4.6), was built on 2026-10-08 and `mcdc-env` was left untouched as the
§9 control. Read §14's "What this environment can and cannot test" before assuming it runs the
current tree — it runs the **ported** code, which is the Phase 3 gate, not the snapshot.

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
199 files. The §7 deck set is intact, but its MCNP comparison targets are not in git.

**[REVISED 2026-10-08]** One of those nine was reversed: `lead_finite_cylinder_energy_deposition.py`
is now §7 **deck 8**, its `.gitignore` rule is removed and the file is committed (in a commit
after the snapshot, not retroactively). **Eight** named `Complex_M&G/` exclusions remain.

---

## 1. Repo State

| Fact | Value |
|---|---|
| `origin` | `DouglasHouser/MCDC` (fork) — **the only remote we can push to** |
| **Port base** | **`mcdc-project/mcdc`** — canonical; all contributions go here **[CORRECTED 2026-10-08]** |
| `upstream` | `CEMeNT-PSAAP/MCDC` — **retired, not used for anything.** Keep or delete the remote; do not branch from it **[CORRECTED 2026-10-08]** |
| Local branch | `wip/photon-snapshot-pre-refactor` — **pushed**. The Phase 0 snapshot ends at `c4f0cb49`; the branch has since taken planning commits (see below) |
| `dev` | `86ee515a` == `origin/dev`, 2 docs commits ahead of the old merge base |
| Divergence | **19 ours / 1,060 theirs** vs `mcdc-project/dev` (`295cd909`). "Ours" grows as this document is revised; only the 1,060 matters for the port |
| Photon code | **committed** in the Phase 0 snapshot — 12 topical commits, 199 files added |

**Remote hygiene — DONE 2026-10-08.** Both `upstream` and `mcdc-project` were added with the
same URL for fetch and push, so a bare `git push mcdc-project …` would have attempted to write
to a repository we do not own. **Both push URLs are now disarmed** by owner decision, so the
only writable remote is `origin`:

```bash
git remote set-url --push mcdc-project DISABLED
git remote set-url --push upstream DISABLED
```

| Remote | Fetch | Push |
|---|---|---|
| `origin` | `DouglasHouser/MCDC` | `DouglasHouser/MCDC` — **the only writable remote** |
| `mcdc-project` | `mcdc-project/mcdc` | `DISABLED` |
| `upstream` | `CEMeNT-PSAAP/MCDC` | `DISABLED` |

**[OWNER DECISION 2026-10-08] Nothing is pushed anywhere but `origin`, and the PR is assembled
by the owner at the end.** All Phase 1–3 work happens on branches in `DouglasHouser/MCDC`. The
pull request to `mcdc-project/mcdc` is composed by the owner once the work is green — so §5
Phase 4's branch-and-open-a-PR step is **the owner's**, not something to perform in passing.
What §5 Phase 4 still binds is the *content*: the `CHANGELOG.md` entry, the five docs pages,
and the PR-template fields all have to exist before that PR can be opened. `origin` being a
direct fork of `mcdc-project/mcdc` (§5 Phase 4) is what makes it openable.

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

**Commits made after the snapshot**, so the branch tip is not `c4f0cb49`.
**[CORRECTED 2026-10-08 — second audit]** This table listed only the first two and called them
"planning only — no photon source". Both statements were stale: two more commits exist, and
`41660da2` carries the six drifted files, which *are* source.

| Commit | Content | Source? |
|---|---|---|
| `6965d2a9` | Retarget the plan at `mcdc-project` and the proton template | no |
| `84154afb` | Close the last two §6 items; un-ignore and commit §7 deck 8 | §7 deck 8 + `.gitignore` |
| `e45833c8` | Audit the sync plan end to end; fix 14 contradictions and 11 bad anchors | no |
| `41660da2` | Build the 3.13 environment and commit the six drifted files | **yes — the six drifted files** |

**This table necessarily lags by at least one commit** — the revision that updates it cannot
list itself, which is how it went stale the first time. Regenerate it instead of trusting it:

```bash
git log --oneline --reverse c4f0cb49..HEAD
git diff --stat c4f0cb49..HEAD -- . ':!photon-transport-docs'   # what is NOT just planning
```

Two of the four touch something outside this document. `84154afb` removes a `.gitignore` rule
and adds `lead_finite_cylinder_energy_deposition.py`. `41660da2` commits the six drifted files
reviewed in the next subsection — including `mcdc/transport/distribution.py`, which is tracked
here and **must not be ported** (see below). **The 199-file snapshot figure above still refers
to `c4f0cb49`**. **[MEASURED 2026-10-08, second audit]** The 199 reconciles exactly —
`git diff --name-status dev..c4f0cb49` gives **181 added + 18 modified = 199**, so the figure
has always meant "paths in `git status --porcelain -uall`", not "files added". At the current
tip it is **183 added + 19 modified = 202**, not the 200 this paragraph predicted: deck 8 is
one of the three new paths, and `41660da2` contributed the other two — it added
`10MeV_cubesat_model_old.py` and modified `mcdc/transport/distribution.py`. Four of the six
drifted files were edits to already-tracked files; two were new.

Re-derive rather than trusting any of these numbers:

```bash
git diff --name-status dev..HEAD | awk '{print $1}' | sort | uniq -c
```

### The six drifted files — **RESOLVED 2026-10-08, all committed**

Owner decision: commit all six to this branch. Reviewed before staging, and two of them turn
out to be **one coupled change**:

| File | What it is | Port? |
|---|---|---|
| `mcdc/transport/distribution.py` | **Divide-by-zero fix** in `sample_white_direction`: `nz != 1.0` → `abs(nz) != 1.0`. At `nz = -1.0`, `B = sqrt(1 - nz²) = 0` and `C = Ac / B` divides by zero | **NO — see below** |
| `…/CARRE_examples/10MeV_cubesat_model.py` | Boundary 100 cm → 20 cm; face sources changed from pointwise isotropic to inward cosine (`white_direction`), inset 1 mm inside the vacuum boundary. **This is what exposed the bug above** — line 336 passes `white_direction=[0.0, 0.0, -1.0]`, the exact `nz = -1.0` case | yes, as a deck |
| `…/CARRE_examples/Plot_cubesat_tallies_avg.py` | Axis labels `a.u.` → physical units; default input filename follows the model rename | yes, as tooling |
| `…/CARRE_examples/10MeV_cubesat_model_old.py` | The pre-change 100 cm version, kept as reference | no |
| `…/Error-Convergence_testing/AZURV1_photon.py` | Run parameters only: `N_particle` 60 → 10 000, `N_batch` 2 → 10. Note this is **not** §7 deck 5 — that is `AZURV1_photon_v3.py` | n/a |
| `…/CODEX_DIAGNOSTIC_INSTRUCTIONS.md` | One sentence scoping an agent task to a single file | no |

**The cubesat change is substantive and measured.** Shrinking the enclosing box leaves the
interior field unchanged (a convex enclosing surface with inward cosine emission gives a
uniform isotropic interior field, `phi = 4/A_box` per source photon) while raising the fraction
of histories that reach the spacecraft from **1.1% to 29%**. Over 400k histories that moved the
median per-voxel flux error from **33.8% to 6.3%**, and the share of voxels under 10% error from
**2.6% to 88%**. It is a sampling-efficiency change, not a physics change.

**⚠ `distribution.py` must NOT be ported — verified obsolete.** Upstream **rewrote**
`sample_white_direction` (`transport/distribution.py:258`). The `if nz != 1.0` branch structure
no longer exists; it now calls `make_direction_basis(nx, ny, nz)`
(`transport/linalg.py:51`), which handles the degenerate axis explicitly:

```python
r = math.hypot(px, py)
if r == 0.0:
    return 1.0, 0.0, 0.0, 0.0, 1.0, 0.0
```

That covers **both** poles, so upstream's version is strictly better than our patch and the bug
we hit cannot occur there. Carrying our fix forward would conflict with a function that no
longer has the line we changed. **Do not raise it with maintainers either** — it is already
fixed. It is committed here only so the snapshot records why the cubesat deck works.

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
  object is `object_/particle.py:35`, the dtype is `numba_types.py:579`, and it carries exactly
  two fields: `energy_deposition` (float, **eV**, weight-included) and `incident_particle`
  (a saved `ParticleData`). The collision signature is
  `collision(particle_container, interaction_data_container, program, data)` — the previous
  revision's `collision_data_container` is wrong. **[CORRECTED 2026-10-08]**
- **`score.collision()` is now `score.interaction()`** — `transport/tally/score.py:128`,
  consuming `interaction_data["energy_deposition"]` at `:175` (the `SCORE_ENERGY_DEPOSITION`
  branch opens at `:174`). **[CORRECTED 2026-10-08; ANCHOR FIX, second audit]**
- **`set_transported_particles` is gone.** Replaced by a `ParticleTransportSettings` dataclass
  per species (`settings.py:97`): `neutron_transport`, `electron_transport`,
  `proton_transport`, each with `active` and `prioritize_low_energy`. Activation is automatic
  from the source list in `simulation.py:359`. **[CORRECTED 2026-10-08]**
- **`transport/physics/cross_species_production.py` is new and matters a great deal for
  photon.** It banks secondary products of a *different* species from a reaction's
  `secondary_products` list, gated on that species' `…_transport["active"]` flag, and
  **subtracts each transported product's energy from the deposition balance**. It is the
  mechanism photon would need for photoelectrons, pair-production electrons and positrons —
  **but §2.10 defers all of that: this PR does not touch this file.** Read it to understand
  the deposition balance §2.3 adopts, not as work to do. **[NEW 2026-10-08]**
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
   `PhotonConstantXSData` in `object_/transport_model_data.py:29` (mirroring
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

   Upstream's model, visible in `cross_species_production.py:142`, is:

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
   | Pair production | `E − 2 m_e c²` — the pair's kinetic energy, deposited locally | subtract e⁺/e⁻ kinetic energy |

   **Fluorescence and annihilation photons are the only products still transported**, because
   they are same-species: `cross_species_production.py:68` explicitly `continue`s on
   same-species products, so they are banked inside `photon/native.py` and never touch
   `produce_cross_species`. So the only deposition subtraction photon performs in this PR is
   for the photons it banks itself.

   **Our code already works this way — verified, not assumed.**
   `mcdc/transport/physics/photon/interface.py:268–290` deposits the pair's kinetic energy
   locally (its own comment: *"electrons are not transported and bremsstrahlung is
   neglected"*), then emits the two 0.511 MeV annihilation photons — reviving the current
   history in place for the first and banking the second as a new active particle. That is
   exactly the §2.10 model, already implemented. The port moves where the number is written,
   not how it is computed.

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
9. **Keep our EADL relaxation data, at upstream's path.** Upstream's root-level
   `atomic_relaxation/` is richer in form (full transition tables with primary and secondary
   designators, so it carries Auger as well as radiative) but is EPRDATA14-derived. Our
   validated fluorescence results depend on the EADL numbers, so write **our** data into
   **upstream's** schema and path rather than consuming theirs.
   **[SETTLED 2026-10-08]** The field-by-field translation is specified in §6.2, and the
   proposed EADL-vs-EPRDATA14 comparison is **withdrawn** — it would have required building
   ACEtk from source, the one dependency §2.8 exists to avoid. Our data is radiative-only,
   which is numerically equivalent to upstream's under §2.10's local-deposition scope.
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
   Note that `simulation.py:350–356` currently `print_error`s if `prioritize_low_energy` is
   set on neutron or proton — **photon must be added to that guard**, or the setting will be
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
                                          Template: the electron half of element.py --
                                          fields :44, set_electron_data :83,
                                          binding energies :179  (197 ln total)
mcdc/object_/simulation.py              + photon_reactions: list[PhotonReactionBase]  (:120)
                                          + self.photon_reactions = []                (:315)
                                          + photon_constant_xs_data list
                                          + 4 edits in _finalize_compilation — see §13
mcdc/object_/transport_model_data.py    + PhotonConstantXSData(MCDCObject)
                                          Template: NeutronMultigroupData (same file, :29)
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
                                        NO EDIT THIS PR -- deferred, see 2.10. (Would be a
                                          PARTICLE_PHOTON arm at :69 once electrons couple.)
mcdc/code_factory/python_objects_compiler.py
                                        + PhotonReactionBase -> simulation.photon_reactions
                                          + PhotonConstantXSData branch   (:92 pattern)
mcdc/object_/simulation.py (again)      + photon_transport in the prioritize_low_energy
                                          guard at :351-355, else silently ignored
tools/data_library_generator/photon/    generate.py + util.py + README.md, writing
                                          $MCDC_LIB_PHOTON  (see 6.2 -- NOT a merge tool)
mcdc/transport/physics/__init__.py      + import mcdc.transport.physics.photon as photon
                                          (one line, beside its three siblings)  [NEW]
docs/source/_ext/simulation_members.py  + "photon" in the hardcoded species tuple at :119.
                                          CI-GATED by docs_test.yml  (§13)        [NEW]
docs/source/user_guide/{sources,tallies}.rst
docs/source/user_guide/getting_started/what_is_mcdc.rst
docs/source/developer_guide/architecture/particle_transport.rst
                                          particle-type lists + the "three-particle"
                                          claim  (§5 Phase 4)                     [NEW]
CHANGELOG.md                            + one entry under [Unreleased] / ### Added.
                                          Required by the contributing guide       [NEW]
test/unit/photon/                       relocated + renamed unit tests  (§10)
test/regression/<case>/input.py         + answer.h5, one directory per deck  (§7)
```

**The five `[NEW]` entries were added by the second audit on 2026-10-08.** Four of them are
documentation and the fifth is one import line, so they are easy to leave out — but
`simulation_members.py` is enforced by `docs_test.yml` on every push and pull request, and
`CHANGELOG.md` is a PR-template checklist item. See §13 for why §13's own derivation missed
them.

**Not applicable to photon:** `transport/physics/condensed_interactions.py` and
`proton/condensed_interactions.py`. Condensed interactions model continuous slowing-down for
charged particles; photons have no analogue. Do not add a photon arm there.

**`xs_offset_` — the trailing underscore is mandatory.** `proton_reaction.py:54` and
`electron_reaction.py:52` both carry the comment *"`xs_offset` is reserved for `xs`"* (proton's
spells it "ir reserved" — same comment, a typo upstream). The
layer generator emits `<field>_offset` and `<field>_length` for every array field, so a field
literally named `xs_offset` collides with the generated accessor for `xs`. The dtype at
`numba_types.py:586–593` (the `proton_reaction` block) shows all three side by side:
`xs_offset`, `xs_length`, `xs_offset_`.

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
| Relaxation transition + binding energies | **eV in OUR EADL files already** | eV | **nothing — do NOT multiply by 1e6** (§6.2) |

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
`ELECTRON_CUTOFF_ENERGY = 100  # eV` and `PROTON_CUTOFF_ENERGY = 250000  # eV`
(**[CORRECTED 2026-10-08, second audit]** — there are two siblings, not one, so the
convention is established rather than inferred); photon will want a `PHOTON_CUTOFF_ENERGY`
sibling, and
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
| shell binding energies | `Element.photon_photoelectric_subshell_binding_energy` — **[CORRECTED 2026-10-08]** name the reaction in the field, mirroring upstream's `electron_ionization_subshell_binding_energy`, and read each through `read_energy` as `element.py:179` does |
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
  (`electron/generate.py:84`), and the old files are replaced wholesale rather than patched —
  see §6.2.
- Group names: `elastic` → **`coherent`**, `incoherent_scattering` → `incoherent`,
  `photoelectric_absorption` → `photoelectric`, to match the `PHOTON_REACTION_*` names and
  the `rx_names` list style in `set_electron_data`. **[NEW 2026-10-08]**
- **MT numbers move to the ENDF MF=23 standard** — total 501, photoelectric 522, pair 516
  (515 electron-field, 517 nuclear-field), subshells 534+. Our current 401/501/503 assignments
  are non-standard and one of them collides with the standard total. Full table and rationale
  in §6.2. **[NEW 2026-10-08]**
- Convert **eV → MeV** and **cm² → barns** on disk — **for the cross-section energy grid and
  the XS arrays only.** The `atomic_relaxation/` transition and binding energies are **already
  in eV** in our files (Pb K = `88011.0`) and upstream's schema stores them in eV too, so they
  pass through unconverted. Blanket-converting everything to MeV is a 10⁶ error in the
  fluorescence line energies. See the translation table in §6.2.
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

### Phase 1 — Fresh branch, no merge  — **✅ COMPLETE 2026-10-08. See §15.**

**Done.** `feature/photon-transport` exists at `295cd909`, **0 commits ahead of
`mcdc-project/dev` and byte-identical to it**, with a clean `git status`. All exit gates pass:
405 unit tests, regeneration leaves `git diff` empty, black clean, and one regression case
green against the cloned reference data. The subsection below is retained as the record of
what was planned; **§15 is the record of what happened, and it differs in three places.**

**Gated on §14 (environment) being green.** The branch cannot be imported, let alone tested,
in `mcdc-env`.

```bash
git fetch mcdc-project
git checkout -b feature/photon-transport mcdc-project/dev
```

**[CORRECTED 2026-10-08]** The base is `mcdc-project/dev`, not `upstream/dev`. Re-apply onto
pristine upstream using the Phase 0 snapshot as reference. Also in this phase:

1. Resolve `.gitignore` per §6.3.7 — take upstream's wholesale, re-add only what §6.3.5
   justifies, and drop the blanket `*.h5` (§6.3.4). **Do not re-add the
   `lead_finite_cylinder_energy_deposition.py` rule** — it was deliberately removed on
   2026-10-08 and that deck is now §7 deck 8, already tracked.
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
| 3 | `PhotonConstantXSData` | `NeutronMultigroupData`, `transport_model_data.py:29` |
| 4 | `Material`: `photon_constant_xs` kwarg + `has_photon_constant_xs` | `material.py:97` `has_neutron_multigroup` |
| 5 | Photon XS fields + `set_photon_data()` on `Element` | the electron half of `element.py` — fields `:44`, `set_electron_data` `:83`, binding energies `:179` |
| 6 | `photon_reactions` list on `Simulation` | `simulation.py:120`, `:315` |
| 7 | Register both new types in `python_objects_compiler.py` | its `ProtonReactionBase` (`:104`) / `NeutronMultigroupData` (`:92`) branches |
| 8 | **Regenerate** `mcdc_get/`, `mcdc_set/`, `numba_types.py` | `python mcdc/code_factory/rebuild_numba_support.py` |
| 9 | `evaluate_photon_xs_energy_grid` | `physics/util.py:34` (electron — same `mcdc_get.element` form) |
| 10 | `physics/photon/native.py` | `physics/proton/native.py` (664 ln) |
| 11 | `physics/photon/constant_xs.py` + `applicable()` | `physics/neutron/multigroup.py:38` |
| 12 | `physics/photon/interface.py` + `__init__.py` | `physics/neutron/interface.py` (**not** proton's) |
| 13 | Four dispatch arms in `physics/interface.py` | its `PARTICLE_PROTON` arms |
| 14 | `photon_transport: ParticleTransportSettings` | `settings.py:183` `proton_transport` |
| 15 | Activation + loader call in `simulation.py` `_finalize_compilation` | `:363`, `:483`, `:512` |
| 16 | `"photon"` source type | `object_/source.py:431` |
| 17 | `"photon"` tally filter + output label | `object_/tally.py:323`, `transport/util.py:25` |
| 18 | `photon_transport` in the `prioritize_low_energy` guard at `simulation.py:350–356` | its neutron/proton arms (§2.11) |
| 19 | `tools/data_library_generator/photon/{generate.py,util.py,README.md}` (mode `"w"`, `$MCDC_LIB_PHOTON`) | `tools/data_library_generator/electron/` — see §6.2 |
| 20 | `import mcdc.transport.physics.photon as photon` in `physics/__init__.py` | its three sibling imports — **[ADDED 2026-10-08, second audit]** |
| 21 | `"photon"` in the species tuple at `docs/source/_ext/simulation_members.py:119`, leaving the `prioritize_low_energy` special case alone (§2.11) | its `"proton"` entry — **[ADDED 2026-10-08, second audit; CI-gated by `docs_test.yml`]** |
| 22 | The four docs pages and the `CHANGELOG.md` entry | §5 Phase 4 — **[ADDED 2026-10-08, second audit]** |
| — | ~~Photon arm in `cross_species_production.py`~~ | **DEFERRED, not a step — §2.10** |

**Steps 20–22 are small and were missing entirely before the second audit.** Step 21 in
particular fails CI rather than review, so do not defer it to Phase 4 with the rest of the
documentation — it belongs with the code that makes it true.

**Step 8 is not optional and not last.** Steps 2–7 define annotated fields; the accessors in
`mcdc_get.element.photon_*` and `mcdc_get.photon_reaction.*` that step 10 calls **do not exist
until the generator has run.** Regenerate after every change to an annotated field, and never
hand-edit the output.

**Do not port these two snapshot commits** — both are obsolete against upstream:

| Snapshot commit | Why not |
|---|---|
| `cdbc5bab` | Formatter churn in generated accessors. Upstream `force-exclude`s `mcdc_get/`, `mcdc_set/` and `numba_types.py` from black, so it cannot recur (§1) |
| the `distribution.py` fix | Upstream rewrote `sample_white_direction` around `make_direction_basis`, which handles both poles. The line we patched is gone (§1 "six drifted files") |

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
   - `test/unit/test_numba_layers_generator.py`
   - `test/unit/test_annotation_shape.py`
   - `test/unit/test_material.py`, `test_settings.py`, `test_source.py`,
     `test_transport_model_data.py`
   - `test/unit/test_object_compilation.py` — **but this one is not free.**
     **[CORRECTED 2026-10-08, second audit]** Its per-particle cases are hand-written, not
     parametrised (`:198`–`:217` proton, `:228`–`:237` electron), so photon gets no coverage
     from it until a photon case is added. Add one; see §13.

   **Baseline, so a photon failure is distinguishable from an inherited one:** the whole of
   `test/unit` is **405 passed** on `mcdc-project/dev` @ `295cd909` under `mcdc-upstream`
   (§14 "Gate result"). Measure the ported tree against that number, not against zero.

   A missing `label`, a bad `sub_type`, or an `Annotated` shape the generator cannot pack will
   surface here with a clear message, long before a physics test gets confusing numbers.
1. **Formatting. [SETTLED 2026-10-08 — OWNER DECISION: everything runs on Python 3.13.]**
   Do **not** run `pre-commit`, and do **not** install a Python 3.14. Run black directly:

   ```bash
   conda activate mcdc-upstream
   python -m black .          # the env's Scripts/ dir is not on PATH, so use -m
   ```

   This is **verified equivalent, not a concession** — see §14, where black 26.1.0 on
   CPython 3.13.16 was run against pristine `mcdc-project/dev` and reported **all 232 files
   unchanged**, which is the same verdict `black_lint.yml` reaches on 3.14. Generated
   accessors are `force-exclude`d and need no formatting. Let `black_lint.yml` arbitrate on
   the PR.

   **Two things not to do**, because both convert a non-problem into a real one:
   - **Do not run `pre-commit install`.** Upstream's config pins `language_version:
     python3.14`, so the hook cannot bootstrap here and *every* commit on the Phase 1 branch
     would fail. No hook is installed today — verified — and it should stay that way.
   - **Do not edit upstream's `.pre-commit-config.yaml`** to say `python3.13`. It would work
     locally and it would be unexplained churn in the PR, touching a file the photon port has
     no business changing.
2. **[REVISED] The `test_` prefix is a correctness problem, not a convention tidy-up.**
   `pytest test/unit/transport/physics` collects **7 tests**, because only
   `test_energy_deposition.py` matches the default discovery pattern.
   `coherent_form_factor.py`, `cross_sections.py` and `fluorescence.py` hold **26 more tests
   that never run** unless the files are named explicitly on the command line. Rename all
   three, relocate to `test/unit/photon/`, and confirm the collected count rises 7 → 33.
   **Reconcile** `test_energy_deposition.py` with upstream's
   `test/unit/tally/test_energy_deposition.py` instead of duplicating.

   **[VERIFIED 2026-10-08]** Re-measured under `mcdc-env`, and the numbers are exact:

   ```bash
   pytest test/unit/transport/physics --collect-only -q          # 7
   pytest test/unit/transport/physics/photon/coherent_form_factor.py           test/unit/transport/physics/photon/cross_sections.py           test/unit/transport/physics/photon/fluorescence.py           --collect-only -q                                      # 26
   ```

   **Trap:** passing the directory *and* the three files in one invocation collects **7**,
   not 33 — pytest dedupes against the directory argument and the unprefixed files are
   dropped again. So the obvious way to check "33" reports 7 and makes this section look
   wrong. Run the two commands separately and add them.
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
drop; the Phase 2 table above is already in that order and steps 1–8 (objects + the Numba
layer), 9–13 (physics), 14–18 (wiring), 19 (the generator) and the tests are natural PR
boundaries.

**The cross-fork PR works directly from `origin` — verified, no re-fork needed.
[NEW 2026-10-08, second audit]** This was an unexamined assumption: GitHub only offers a pull
request between repositories in the same fork network, and the plan's base moved mid-stream
from CEMeNT-PSAAP to mcdc-project. Checked against the API, and the network has been
re-parented in our favour:

| Repo | `fork` | parent |
|---|---|---|
| `mcdc-project/mcdc` | false | — (network root) |
| `DouglasHouser/MCDC` (`origin`) | true | **`mcdc-project/mcdc`** |
| `CEMeNT-PSAAP/MCDC` (`upstream`) | true | `mcdc-project/mcdc` |

So `origin` is a **direct fork of the PR target**, and CEMeNT-PSAAP is now itself a downstream
fork of it. Note also that CEMeNT-PSAAP/MCDC is **not** GitHub-archived — "retired" in this
document means "no longer the canonical upstream", not "locked".

**Upstream requires a `CHANGELOG.md` entry and documentation updates.
[NEW 2026-10-08, second audit]** No previous revision mentioned either, and both are
checklist items on the PR template that a reviewer will ask for:

1. **`CHANGELOG.md`** — add one entry under `## [Unreleased]` → `### Added`, in the existing
   house style, which ends each line with `from [@handle]`. Proton's own entry is the model:
   *"Add proton transport with nuclear reactions and secondary-particle production, …, from
   [@ethan-lame]"*. Required by
   `docs/source/developer_guide/contributing/pull_requests.rst` for any notable change.
2. **Documentation**, which is **CI-gated** — `docs_test.yml` builds the docs on every push
   and pull request. The pages that enumerate particle types and will be wrong without a
   photon edit:

   | Page | What needs the photon arm |
   |---|---|
   | `docs/source/_ext/simulation_members.py:119` | **the hard one** — a hardcoded `for species in ("neutron", "electron", "proton")`. See §13 |
   | `docs/source/user_guide/sources.rst` | the `particle_type` value list |
   | `docs/source/user_guide/tallies.rst` | the particle-filter value list |
   | `docs/source/user_guide/getting_started/what_is_mcdc.rst` | says MC/DC is a three-particle code |
   | `docs/source/developer_guide/architecture/particle_transport.rst` | per-particle interaction data and tally scoring |

   The docs extras must be installed to build these locally — see §14, where they were also
   missing.

Fill in the PR template's "Associated Developers" and link the §6.4 maintainer questions as
issues rather than burying them in the PR body.

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

   **Relaxation source — CLOSED 2026-10-08. Keep EADL; do not run the comparison.**

   A previous draft of this section said to compare our EADL relaxation data against
   upstream's EPRDATA14 data before writing the generator. **That was the wrong call and is
   withdrawn.** Performing it would require downloading the EPRDATA14 ACE tarball **and
   building ACEtk from source** — which is precisely the dependency §2.8 chose the EPDL route
   to avoid. Re-introducing a from-source C++ build in order to second-guess data that our
   117 cross-section tests and the fluorescence validation already exercise is a bad trade.
   Neither EPRDATA14 nor ACEtk is present on this machine; `data/endf/` holds `epdl`, `eadl`
   and `eedl`, which is what our generator reads.

   What *can* be determined without EPRDATA14 — by reading upstream's schema and our files —
   is the field-by-field translation, and that is the actionable part. It replaces the vague
   "write our data into upstream's schema" instruction in §2.9.

   **Upstream's schema** (`electron/generate.py:246`, README lines 94–100), one group per
   ionization subshell, keyed by MT:

   ```
   atomic_relaxation/MT-NNN/        NNN = 534+   attrs: MT, subshell_designator, subshell
     number_of_transitions          int
     primary_designator             1-D int     [only if number_of_transitions > 0]
     secondary_designator           1-D int     [only if number_of_transitions > 0]
     energy                         1-D, attrs: unit="eV"
     probability                    1-D
   ```

   **Ours**, measured from `data/mcdc/Pb.h5`:

   ```
   photon_reactions/atomic_relaxation/subshells/<K,L1,L2,L3,M1…S28>/
     binding_energy      scalar, eV   (Pb K = 88011.0 — the 88 keV K-edge, so already eV)
     designator          scalar       (1 = K, 2 = L1, 3 = L2, … — the EADL/ENDF scheme)
     fluorescence_yield  scalar
     radiative/{final_subshell, transition_energy, probability}   1-D each
   ```

   **The translation the generator must perform:**

   | Ours (EADL) | Upstream's field | Note |
   |---|---|---|
   | `subshells/<label>/` | `atomic_relaxation/MT-NNN/` | NNN from the same designator→MT map electron uses for ionization subshells |
   | `designator` | `attrs["subshell_designator"]` | identical convention, no remapping |
   | shell label | `attrs["subshell"]` | `util.get_electron_subshell_name(designator)` already does this |
   | `radiative/final_subshell` | `primary_designator` | |
   | — | `secondary_designator` | **write 0** — see the gap below |
   | `radiative/transition_energy` | `energy` + `attrs["unit"] = "eV"` | **already eV; no `* 1e6`.** Upstream's electron path converts from MeV; ours must not |
   | `radiative/probability` | `probability` | |
   | `len(radiative/probability)` | `number_of_transitions` | |
   | `fluorescence_yield` | — | **derived, drop it.** Verified on Pb K: `sum(probability) = 0.9613108603` equals `fluorescence_yield` exactly, so the probabilities are **absolute**, not normalised within the radiative set |
   | `binding_energy` | — | does not belong here; it feeds `Element.photon_photoelectric_subshell_binding_energy` from the photoelectric MT-534+ groups, mirroring `element.py:179` |

   **The one substantive difference, recorded because it is a real limitation:** our EADL
   extraction carries **radiative transitions only — no Auger.** Upstream's
   `secondary_designator` distinguishes radiative (0) from non-radiative; ours has no
   non-radiative entries at all, which is why `sum(probability)` equals the fluorescence yield
   rather than 1.0. The remaining `1 − ω` probability is implicitly local deposition.

   **Under §2.10 this is correct, not merely tolerable.** Auger products are electrons, and
   §2.10 deposits all photon-produced electrons locally, so an Auger channel would deposit
   exactly the energy that the missing probability already deposits. The two are numerically
   identical for this PR. It becomes a real gap only when electrons are coupled, and it should
   be recorded in that PR's scope rather than this one.

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

   **[CAUTION 2026-10-08] Do not delete `data/mcdc/` itself, and do not regard it as
   disposable just because §6.2 says the new generator replaces it.** Those 204 MB are the
   only copy of the numbers the 117 cross-section tests and the fluorescence validation were
   run against. The new single-pass generator must be **diffed against them** before they go
   anywhere — that comparison is the only thing standing between a schema fix and a silent
   physics regression. Deleting the two stale duplicates (458 MB) is safe now; retiring
   `data/mcdc/` waits until the generator reproduces it.
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
     1 eV floor) — do they intend their own photon path? Worth asking as a **design**
     question; it is no longer a data-comparison question, since §6.2 withdrew that
     comparison. If they say yes, mention that our relaxation data is radiative-only.
   - ~~the generator file-mode collision~~ — **closed**, see the header and §4.
   - ~~energy units / possible upstream bug~~ — **closed**, see §6.1. Do not raise it; there
     is no bug, and `read_energy` is the answer.
5. **Coverage gaps** in the chosen decks. **[RESOLVED 2026-10-08 — both items closed]**
   - ~~No energy-deposition deck~~ — **closed.** `lead_finite_cylinder_energy_deposition.py`
     is now §7 deck 8 by owner decision, reversing its §6.3.2 exclusion. Use
     `test/regression/pincell-energy_deposition/` as the structural pattern.
   - ~~Fluorescence untested at the deck level~~ — **CLOSED 2026-10-08 by owner decision:
     the unit tests are accepted as sufficient coverage.** Both Pb decks run at 10 MeV and the
     Pb K-edge is 88 keV, so no deck puts meaningful flux near it, and none will in this PR.
     Coverage rests on `test/unit/photon/` — principally the fluorescence tests in §10 Tier A
     (`fluorescence.py`, 9 tests) plus the EADL relaxation path.

     **Two consequences follow from that, and both are load-bearing:**

     1. **Those 9 tests must not stay unrunnable.** `fluorescence.py` is one of the three
        files §5 Phase 3 item 2 identifies as never collected by default, because it lacks the
        `test_` prefix. Accepting unit tests as the coverage for fluorescence means the
        rename in Phase 3 item 2 is **the** thing standing between us and having no
        fluorescence coverage at all. Treat it as required, not cosmetic.
     2. Fluorescence photons are the only photoelectric product still transported under
        §2.10 — everything else deposits locally — so these tests are the only check on the
        one PE branch that still creates particles.

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
#
#    [CORRECTED 2026-10-08, second audit] As written this check CANNOT PASS, and
#    it is measuring the wrong thing. `git count-objects` reports the whole
#    repository, upstream's history included, which is 59.14 MiB here -- dominated
#    by five revisions of test/regression/moving_pellet/answer.h5 at ~27.7 MB each
#    and a 19.54 MB examples/.../sphere_S.npy. None of that is ours and none of it
#    is removable. A failure here would say nothing about the photon snapshot.
#
#    Measure what the BRANCH adds instead. Expect ~2.8 MB over ~191 blobs, which
#    is what the "~2.5 MB across 199 files" figure in 6.3 refers to:
git rev-list --objects dev..HEAD | awk '{print $1}' \
  | git cat-file --batch-check='%(objecttype) %(objectsize)' \
  | awk '$1=="blob"{s+=$2; n++} END{printf "%d blobs, %.2f MB\n", n, s/1048576}'

#    Measured 2026-10-08: 191 blobs, 2.76 MB. Largest single file added by the
#    branch is 348 KB (AZURV1_photon_error_analysis.txt), well under GitHub's
#    50 MB warning and 100 MB hard limit.
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

1. **DONE 2026-10-08 — the rule is removed and the deck is committed.** Both the §6.3.5
   specification block and the live `.gitignore` have been updated, and the deck is tracked.
   Verify with:

   ```bash
   git check-ignore -v photon_transport_code/MCNP_Verification_Tests/Complex_M&G/lead_finite_cylinder_energy_deposition.py
   #   -> exit 1, no output: NOT ignored
   git ls-files --error-unmatch "photon_transport_code/MCNP_Verification_Tests/Complex_M&G/lead_finite_cylinder_energy_deposition.py"
   ```

   The named-deck exclusion list in `.gitignore` is now **8 paths**, down from 9, and carries
   a dated comment recording the reversal so the next reader does not re-add the rule.

   **Migration note for deck 8.** Its own docstring says *"verify whether your local photon
   branch reports energy_deposition in eV or MeV"* — an open question when it was written.
   §4 now answers it: **eV, weight-included**. Resolve that comment during the migration
   rather than carrying the ambiguity into `test/regression/`. The deck also runs
   `N_particle = 200_000` and uses the old module-level `mcdc.settings` / `mcdc.Tally(cell=…)`
   API, so it needs the same `Simulation`-API migration as the other seven, plus the
   `sys.path` preamble stripped — it currently inserts its own parent directories to find the
   local `mcdc` package, which is wrong once it lives in `test/regression/`.
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

**There is no answer-generation flag. [NEW 2026-10-08, second audit]** `test/regression/conftest.py`
takes `--name`, `--skip`, `--target`, `--mode` and `--mpiexec` / `--srun`, and nothing else —
no `--generate-answer`, no `--update`. Each `answer.h5` is produced **by hand**, and the
previous revision said only that it was "generated from our own code once it is trusted", which
is not a procedure. It is:

1. Run the deck exactly the way the harness will, from inside the case directory. The harness
   invokes `python input.py --clear_cache --caching --mode=<mode> --target=<target>
   --output=output --no-progress-bar`, so match those flags — in particular `--output=output`,
   which fixes the filename.
2. Rename `output.h5` to `answer.h5` in the same directory.
3. Re-run the harness against it and confirm the case passes before committing.

**Record which `--mode` produced it.** `rtol = 1e-6` is tight enough that a `python`-mode answer
is not guaranteed to satisfy a `numba`-mode run, and `regression_test.yml` runs
`--mode numba`. Generate each answer in **numba** mode and verify it also passes in python
mode, not the reverse. A deck whose two modes disagree above `1e-6` is a finding, not a
tolerance to loosen.

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

**✅ Blocked on nothing. Cleared to start Phase 1 as of 2026-10-08.**

| Gate | Status |
|---|---|
| §14 environment | **done, and now actually executed** — `mcdc-upstream`, Python 3.13.16; §14's four-command gate run against `mcdc-project/dev` @ `295cd909`: **405 passed**, `git diff` empty after regeneration. **[REVISED 2026-10-08, second audit — this row said "done" before the gate had ever been run, and the gate failed on first execution. See §14 "Gate result".]** |
| The six drifted files | **done** — all committed in `41660da2`; `distribution.py` flagged do-not-port |
| `.gitignore` + §7 deck 8 | **done** — rule removed, deck tracked (`check-ignore` exits 1) |
| `PARTICLE_PHOTON = 3` free | **verified by the owner 2026-10-08**; re-verified against `295cd909` — `PARTICLE_` stops at `PROTON = 2`, with `PARTICLE_ANY = 100` |
| 300 block free | verified on `295cd909` — no constant in `mcdc/constant.py` matches `= 3[0-9][0-9]`; re-confirm on the tip you fetch (§8 step 4) |
| All §6 open items | closed |
| §13 touch-list complete | **was incomplete; now corrected — 2026-10-08, second audit.** Its grep could not see bare lowercase `"proton"`; two files were missing, one of them CI-gated. See §13 |
| Phase 4 obligations known | **were undocumented; now recorded — 2026-10-08, second audit.** `CHANGELOG.md` and five docs pages. See §5 Phase 4 |

**[UPDATED 2026-10-08 — OWNER DECISION] There is no remaining prerequisite.** This paragraph
previously said one was left: install a standalone Python 3.14 for the black pre-commit hook,
or accept the fallback. **The owner took the fallback — everything runs on Python 3.13**, and
§14 now carries the measurement that makes the two identical in outcome (black 26.1.0 on
3.13.16 leaves all 232 files of pristine upstream unchanged). `pre-commit` is not used; black
runs directly. See §5 Phase 3 item 1 for the two things not to do.

The push URLs on `mcdc-project` and `upstream` are also **already disarmed** (§1), so §8's
step 1 below is a no-op kept for the record.

**What the second audit did not change.** Every physics decision, the §4 unit model, the §6.2
relaxation translation table and the Phase 2 dependency order were re-checked and stand. So do
all 38 spot-checked source anchors (33 exact, 5 off by ≤2 lines and fixed in place), every
file line count in §3 and §13, §13's proton mention counts, the 7 / 26 / 362 test counts, the
`Al.h5` schema and empty-attrs finding in §6.2, and the regression harness tolerances in §7.

**Every other open item in §6 is now closed.** §6.1 (energy units) and §6.2 (data generation,
including the relaxation translation) are settled by evidence; §6.3 (`.gitignore`) is resolved
bar the Phase 1 handover; §6.4 is a list of things to tell the maintainers, not a blocker; and
§6.5's two coverage gaps are both closed by owner decision. The plan is executable as written.

**Phase 0 is already done — the previous revision's step 0 is deleted from this block.** Do not
re-create `wip/photon-snapshot-pre-refactor`; it exists at `c4f0cb49` and is pushed.

```bash
cd /c/Projects/MCDC

# 0. PREREQUISITES -- all DONE as of 2026-10-08:
#      - environment `mcdc-upstream` (Python 3.13.16) built, section 14
#      - section 14's four-command gate RUN, not just asserted: 405 passed.
#        It failed on first execution -- cffi was missing and mcdc itself was
#        never installed. Both fixed; see section 14 "Gate result".
#      - the six drifted files reviewed and committed, section 1
#      - push URLs on mcdc-project and upstream DISARMED, section 1
#      - Python 3.14: NOT needed. Owner decision -- everything runs on 3.13 and
#        black is run directly instead of through pre-commit. Section 14 carries
#        the measurement: black 26.1.0 on 3.13.16 leaves all 232 files of
#        pristine upstream unchanged. Do NOT run `pre-commit install`.
#    Nothing is outstanding.
conda activate mcdc-upstream

# 1. Disarm push to repositories we do not own -- ALREADY DONE 2026-10-08,
#    kept here for the record. Re-running is harmless. Only `origin` is
#    writable, and the PR to mcdc-project/mcdc is assembled by the owner at
#    the end (section 1).
git remote set-url --push mcdc-project DISABLED
git remote set-url --push upstream     DISABLED

# 2. Park the Phase 0 snapshot side by side, as a read-only reference
git worktree add ../MCDC-photon-old wip/photon-snapshot-pre-refactor
#    open ../MCDC-photon-old in a second editor window

# 3. Port branch, straight off the canonical remote
#    (NOT a merge, NOT a fast-forward, NOT CEMeNT-PSAAP)
git fetch mcdc-project
git checkout -b feature/photon-transport mcdc-project/dev

# 4. Re-verify, against the tip you just got.
#    PARTICLE_PHOTON = 3 was verified free by the owner on 2026-10-08; the 300 block
#    was verified free on 295cd909. Both still worth one grep, since proton took the
#    200 block between two revisions of this very document.
grep -nE "^PARTICLE_|= 3[0-9][0-9] *$" mcdc/constant.py   # expect no 3xx constants
git ls-tree -r --name-only HEAD | grep -i photon          # expect EMPTY

# 4b. Reinstall editable against UPSTREAM's pyproject, now that it is checked out.
#     Until this runs, the editable install points at the snapshot's pyproject, which
#     declares neither cffi nor cffconvert and pins the wrong Sphinx theme. This picks
#     up upstream's own dependency set and extras. Section 14.
python -m pip install -e ".[dev]"

# 4c. Confirm section 14's gate still passes on the branch you just made.
#     Expect 405 passed and an EMPTY git diff from the regeneration.
python mcdc/code_factory/rebuild_numba_support.py && git diff --stat
pytest test/unit -q

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
rotted. **[RE-VERIFIED 2026-10-08]** Both figures reproduce exactly on the current tree —
362 collected in 0.45 s, 7 from the main tree. This is why `mcdc-env` must not be upgraded in
place (§14): it is the control for §10's rewrite tiers, and `mcdc-upstream` cannot replace it
(our pre-port code predates numpy 2 and the upstream API rename). Per-file counts in `test/unit/photon/`: `test_coverage_gaps` 50,
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

**[NEW 2026-10-08] How this relates to §7's `answer.h5`.** The two do not overlap and must not
be confused:

- The **8 decks in §7** become `test/regression/<case>/{input.py, answer.h5}`. Their
  `answer.h5` *is* their committed reference, compared at `rtol = 1e-6` by the harness. They
  do **not** also get a `smoke_1e4.h5`.
- The **other 22 decks** stay in `photon_transport_code/` and get the §11 smoke pair beside
  them. Nothing runs them automatically; the files exist so a reader has a reference.

So §11's scope is really **22 decks**, not 30, once §7 is migrated. The 30-deck figure below
is the pre-migration inventory. Also note `smoke_1e4.h5` survives upstream's narrow HDF5 rules
(`*output.h5`, `output*.h5`, `dummy_nuclide.h5`, `source_particles.h5`) — which is exactly why
§6.3.4 drops the blanket `*.h5` in Phase 1.

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
is the most recently integrated particle, so this is **nearly** the complete set of places a
new particle type touches. Photon needs an edit in each one except where noted.

**[CORRECTED 2026-10-08, second audit]** That sentence read "**this is the complete set**". It
was not, and the derivation is why — the grep sees constants and field names but not bare
lowercase `"proton"`. Two files were missing, one of them CI-gated. They are now rows in the
table, and **"The grep above has a blind spot"** below explains the gap and gives the wider
command. Re-run both greps, not just the one in the block below.

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
| `mcdc/object_/simulation.py` | 6 | **4 edits** — list declaration `:120`, init `:315`, activation `:363`, loader call `:512`; plus the `set_elements_from_nuclides` gate (`:473`–`:477`) and the `print_msg` gate (`:483`). **[ANCHOR FIX 2026-10-08, second audit — activation was `:365`, loader call `:498`; both measured against the electron arms, which are the photon templates]** |
| `mcdc/transport/physics/interface.py` | 5 | **4 arms** — `particle_speed`, `macro_xs`, `collision_distance` (SigmaT block), `collision` |
| `mcdc/constant.py` | 5 | `PARTICLE_PHOTON = 3` + `PHOTON_REACTION_* = 300..304` + a `PHOTON_CUTOFF_ENERGY` sibling |
| `mcdc/transport/physics/cross_species_production.py` | 3 | **DEFERRED — no edit this PR** (§2.10). Would be 1 arm in the transport-active gate (`:69`–`:73`) once electrons are coupled |
| `mcdc/transport/physics/condensed_interactions.py` | 3 | **NO EDIT** — photons have no continuous slowing-down |
| `mcdc/object_/tally.py` | 3 | particle-type **filter**: string to constant `:323`, label map `:414`, docstring `:82` |
| `mcdc/object_/source.py` | 3 | string to constant `:431`, docstring `:94`, `decode_particle_type` `:546` |
| `mcdc/transport/util.py` | 2 | `PARTICLE_PHOTON` to `"photon"` at `:25` (used for output naming) |
| `docs/source/_ext/simulation_members.py` | **0** — see below | **1 edit, CI-gated** — `:119` hardcodes `for species in ("neutron", "electron", "proton")`. **[ADDED 2026-10-08, second audit]** |
| `mcdc/transport/physics/__init__.py` | **0** — see below | **1 line** — `import mcdc.transport.physics.photon as photon`, beside its three siblings. **[ADDED 2026-10-08, second audit]** |
| `mcdc/object_/settings.py` | 1 | `photon_transport: ParticleTransportSettings` field (§2.11, plain `default_factory`) |
| `mcdc/numba_types.py` | 1 | **GENERATED** — never hand-edit; comes from step 8 |
| `mcdc/transport/simulation.py` | 1 | proton-only condensed-interaction gate — **NO EDIT** |
| `test/regression/*/answer.h5` (15 files) | 1 each | **NO EDIT** — the string appears inside stored tally metadata |

### The grep above has a blind spot — read this before trusting the table
**[NEW 2026-10-08, second audit]**

This section called itself "the complete set of places a new particle type touches". It is not,
and the reason is in its own derivation: the pattern
`PARTICLE_PROTON|proton_transport|PROTON_REACTION` matches **constants and field names only**.
It cannot see a bare lowercase `"proton"` string, and upstream has those. Re-derive with the
wider pattern as well:

```bash
git grep -lI "proton" mcdc-project/dev \
  -- 'mcdc/*' 'tools/*' 'test/*' 'examples/*' 'docs/*' CHANGELOG.md
```

The difference between the two greps is 29 files. Most are generated (`mcdc_get/`,
`mcdc_set/`), proton-specific with no photon analogue, or already covered by name elsewhere in
this plan. **Two need a photon edit and are now rows in the table above**, and one of the two
is the more dangerous kind of miss, because it is enforced by CI rather than by a reviewer:

- **`docs/source/_ext/simulation_members.py:119`** — a Sphinx extension that documents
  `Simulation`'s members, with a hardcoded `for species in ("neutron", "electron", "proton")`
  and, at `:124`, an `is_electron`-style special case for `prioritize_low_energy`. Add
  `"photon"` to the tuple and leave the special case alone (§2.11: photon does not prioritize
  low energy). `docs_test.yml` builds the docs on **every push and pull request**, so this is a
  CI failure, not a documentation nit. It is also why §14 now installs the docs extras.
- **`mcdc/transport/physics/__init__.py`** — re-exports the interface functions and then
  imports each particle subpackage by name (`electron`, `neutron`, `proton`). Photon needs the
  fourth line, or `physics.photon` is reachable only by full import path while its three
  siblings are not.

**Two further files mention proton but need no photon edit, for reasons worth recording:**

- `test/unit/transport/test_native_particle_kinematics.py` parametrises over
  `(neutron, NEUTRON_MASS)` and `(proton, PROTON_MASS)`. Photons are massless and have no
  analogue here — the same reasoning as `condensed_interactions.py`. **No edit.**
- `test/unit/test_object_compilation.py` has **hand-written per-particle cases**, not generic
  ones (`:198`–`:217` for proton, `:228`–`:237` for electron, each asserting a
  `"Loading <particle> data [1/1]: <file>.h5"` message). This qualifies §5 Phase 3 item 0's
  claim that the object-model tests "cover photon for free": the genuinely generic ones
  (`test_annotation_shape.py`, `test_numba_layers_generator.py`) do, but this file gives photon
  no coverage until a photon case is added to it. Add one — it is four lines and it is the
  cheapest possible check that `set_photon_data` is wired into
  `_finalize_compilation` at all.

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
| `mcdc/object_/transport_model_data.py` | `PhotonConstantXSData`, mirroring `NeutronMultigroupData` `:29` |
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
| **cffi** | **absent** | **`>=1.17.1,<3`** — **[ADDED 2026-10-08, second audit]** upstream's *first* declared dependency, omitted by the original table. `mcdc/code_factory/array_return.py:1` does a bare `import cffi`, reached through `mcdc.transport` → `geometry` → `mcdc_get`, so **every** import of the transport layer fails without it |
| numba | **0.55.1** | `>=0.61.0,<0.67` |
| numpy | **1.21.5** | `>=2.0.0,<2.5` |
| scipy | — | `<1.19` |
| matplotlib | — | `<3.12` |
| mpi4py | — | `>=3.1.4,<4.2` |
| h5py | — | `<3.17` |
| colorama | — | `<0.5` |
| sympy | — | `<1.15` |

Dev extras: `black<27`, **`cffconvert>=2,<3`**, `pre-commit<5`, `pyright<1.2`, `pytest<10`.
Docs extras: `sphinx>=8,<10`, `pydata-sphinx-theme>=0.20,<0.21`, `sphinx-design>=0.6,<0.8`.
**[CORRECTED 2026-10-08, second audit]** `cffconvert` and all three docs extras were missing
from this line and from the environment. `cffconvert` backs `check_citation.yml` and the docs
extras back `docs_test.yml`; both workflows run on every push and pull request, so a photon PR
that cannot build the docs locally will fail CI (§5 Phase 4).

### ✅ BUILT 2026-10-08 — `mcdc-upstream`

| | Value |
|---|---|
| Name | **`mcdc-upstream`** |
| Python | **3.13.16** |
| Path | `C:\Users\dwhou\anaconda3\envs\mcdc-upstream` |
| Interpreter | `C:/Users/dwhou/anaconda3/envs/mcdc-upstream/python.exe` |

Installed, with upstream's pin beside each so a future reader can see the headroom:

| Package | Installed | Upstream pin |
|---|---|---|
| Python | **3.13.16** | `>=3.11` |
| numba | **0.66.0** | `>=0.61.0,<0.67` |
| numpy | **2.4.6** | `>=2.0.0,<2.5` |
| scipy | 1.18.1 | `<1.19` |
| matplotlib | 3.11.2 | `<3.12` |
| h5py | 3.16.0 | `<3.17` |
| colorama | 0.4.6 | `<0.5` |
| sympy | 1.14.0 | `<1.15` |
| mpi4py | 4.1.2 | `>=3.1.4,<4.2` |
| **cffi** | **2.1.1** | `>=1.17.1,<3` |
| black | **26.1.0** — pinned deliberately, see below | `<27` |
| pytest | 9.1.1 | `<10` |
| pyright | 1.1.414 | `<1.2` |
| pre-commit | 4.6.2 | `<5` |
| **cffconvert** | **2.0.0** | `>=2,<3` |
| **sphinx** | **9.1.0** | `>=8,<10` |
| **pydata-sphinx-theme** | **0.20.0** | `>=0.20,<0.21` |
| **sphinx-design** | **0.7.0** | `>=0.6,<0.8` |
| **`mcdc` itself** | **editable, from `C:\Projects\MCDC`** | — |

**[CORRECTED 2026-10-08, second audit] `cffi` and the last five rows were added after the
environment failed §14's own gate.** The bolded entries did not exist when this section was
first written. Two of them were fatal rather than cosmetic:

- **`cffi`** — without it `pytest test/unit` produced **29 collection errors**, all
  `ModuleNotFoundError: No module named 'cffi'`. Nothing in the transport layer imports.
- **`mcdc` itself was never installed.** The environment had the dependencies but not the
  package, so `importlib.metadata.version("mcdc")` raised `PackageNotFoundError` and
  `test/unit/test_output.py::test_output_serializes_nested_transport_settings` failed. The
  verification command `python -c "import mcdc"` **does not catch this** — it succeeds on a
  CWD-relative import whenever you are standing in the repo root, which is exactly where you
  run it. Only a test that reads the package *metadata* notices.

**The underlying mistake was the install method, and it is worth not repeating.** This section
originally built the environment by transcribing pins out of `pyproject.toml` by hand. Upstream
documents one command for developers
(`docs/source/user_guide/getting_started/installation.rst:63`) that resolves the whole set,
extras included:

```bash
conda activate mcdc-upstream
python -m pip install -e ".[dev]"
```

**Run that from `feature/photon-transport` as soon as Phase 1 branches.** Until then the
editable install points at this snapshot's `pyproject.toml`, which declares neither `cffi` nor
`cffconvert` and pins `sphinx==7.2.6` with `furo` rather than upstream's `pydata-sphinx-theme`.
It was therefore installed with `--no-deps`, specifically so the snapshot's stale pins could
not disturb the versions above, and the missing packages were added explicitly. `-e` follows
branch switches, so the install survives the Phase 1 checkout — but re-run it as
`-e ".[dev]"` on the new branch to pick up upstream's own extras and drop this caveat.

`mpi4py` built against the MS MPI already on this machine
(`C:\Program Files\Microsoft MPI\Bin`), so no SDK install was needed.

**numba verified working on 3.13, not merely installed.** The whole 3.13-vs-3.14 question in
this section is about numba, so it was tested rather than assumed — an `@njit` kernel
compiled and returned the correct result:

```
njit sum-of-squares over 1000 elements -> 332833500.0  (exact)
numba 0.66.0 on py3.13: WORKING
```

**black is pinned to exactly 26.1.0** to match `.pre-commit-config.yaml`. `black<27` initially
resolved to 26.10.0, which is *newer* than the hook's pin and could therefore format
differently from CI. Pinning removes that divergence and makes the fallback in the next
subsection genuinely safe rather than merely probable.

**`mcdc-env` is untouched and must stay that way** — it is the only environment in which
§9's 362-test baseline reproduces, and that baseline is the evidence behind §10's rewrite
tiers. Two environments, two jobs.

#### What this environment can and cannot test  **[READ THIS — it is a common misreading]**

**It tests the ported code, not the current tree.**

| Target | Environment | Why |
|---|---|---|
| Upstream's own `test/unit` and `test/regression`, after Phase 1 | **`mcdc-upstream`** | this is what it is for |
| The ported photon layer and the 8 migrated decks, in Phase 3 | **`mcdc-upstream`** | same |
| `photon_transport_code/test/` — the 362-test baseline **as it stands today** | **`mcdc-env`** | written against the April API, numba 0.55 / numpy 1.21 |
| The pre-port snapshot tree (this branch) | **`mcdc-env`** | our photon code predates the numpy 2 / numba 0.61 era and the upstream API rename |

So the answer to "can this environment test that all the test problems run" is **yes — once
they are ported**, and that is precisely the Phase 3 gate. It cannot validate the snapshot
as it exists right now, and it is not meant to: Phase 1 branches onto pristine upstream, and
everything after that runs in `mcdc-upstream`.

**Three things must be in place before the decks will run there**, none of which the
environment itself provides:

1. **`MCDC_LIB`** must point at a photon library — see the subsection below. Not needed today
   (our loader hardcodes its path), required from Phase 2.
2. **The regression reference data** must be cloned — §5 Phase 3 item 4.
3. **The photon data library must be regenerated** by the new §6.2 generator, because the
   existing files have empty `xs` attrs and will `KeyError` on the first element under the
   upstream loader (§4).

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

### The `pre-commit` / black 3.14 problem — **CLOSED: 3.13 only**

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
(`anaconda3` base is 3.9.13, `epics-env` is 3.13.13, `mcdc-env` is 3.10.20,
`mcdc-upstream` is 3.13.16).

**[OWNER DECISION 2026-10-08 — everything runs on Python 3.13. Do not install a 3.14.]**
A previous revision of this subsection told the reader to install a standalone 3.14 purely so
`pre-commit` could build the black hook's virtualenv, with "run black directly" as a fallback.
**The fallback is now the decision, and it was measured rather than assumed.**

**The evidence. [NEW 2026-10-08, second audit]** Both halves were run, not predicted:

| Run on pristine `mcdc-project/dev` @ `295cd909`, under `mcdc-upstream` (3.13.16) | Result |
|---|---|
| `python -m black --version` | `black 26.1.0 (compiled: yes)`, CPython **3.13.16** — the exact version the hook pins |
| `python -m black --check .` | **"232 files would be left unchanged"** — the same verdict `black_lint.yml` reaches on 3.14 |
| `python -m pre_commit run --all-files` | fails, as predicted: `RuntimeError: failed to find interpreter for Builtin discover of python_spec='python3.14'` |

So the two interpreters produce **identical formatting on the real tree**, and the only thing
3.14 buys is the ability to run a bootstrapper we have no need for. Three independent reasons
it has to come out that way: the environment pins **black 26.1.0, the version the hook pins**;
`[tool.black] target-version` lists py311 through py314, so black emits no version-specific
formatting; and the generated accessors are `force-exclude`d, so the largest body of machine-
written code is not formatted at all.

**What this means in practice:**

- **Format with `python -m black .`** from `mcdc-upstream`. Let `black_lint.yml` arbitrate on
  the PR — it runs on 3.14 and will agree.
- **Do not run `pre-commit install`.** Upstream's config pins `python3.14`, so the hook cannot
  bootstrap here and every commit on the Phase 1 branch would fail with the error above.
  Verified 2026-10-08: no hook is installed in `.git/hooks/pre-commit`, and it should stay
  that way. (Note the local snapshot's own config pins `python3.11`, so this trap appears only
  *after* Phase 1 takes upstream's file.)
- **Do not edit upstream's `.pre-commit-config.yaml`.** Changing `python3.14` to `python3.13`
  would work locally and would be unexplained churn in a PR that has no business touching it.

For the record, upstream's own split — which is what the superseded two-interpreter advice was
mirroring:

| Interpreter | Purpose | Matches |
|---|---|---|
| **3.13** | the environment: numba, pytest, running MC/DC | `unit_test.yml`, `regression_test.yml`, `check_numba_support.yml` |
| 3.14 | the black formatter only — never imports mcdc | `black_lint.yml` |

Run black as:

```bash
conda activate mcdc-upstream
python -m black .          # note: the env's Scripts/ dir is not on PATH, so use -m
```

### `MCDC_LIB` — a Phase 2 task, not a prerequisite  **[CORRECTED 2026-10-08]**

`MCDC_LIB` is **unset** in both the user and machine environment, and that has never mattered,
because our photon loader does not read it. `mcdc/transport/physics/photon/data_loader.py:26`
hardcodes the path relative to its own source file:

```python
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "mcdc"
```

That resolves to the repo's own `data/mcdc/` and is why every benchmark in §9 runs today.
`MCDC_LIB` is read by `object_/material.py:297` and `object_/nuclide.py:139`, `:171` and
`:319` — the **neutron** continuous-energy path, which no photon deck exercises — **and also
by `object_/element.py:68` and `:88`**, which is the path that matters here.
**[ANCHOR FIX 2026-10-08, second audit]** This sentence previously read "read only by
`object_/material.py:118` and `object_/nuclide.py:62`". Both anchors were wrong, and the word
"only" contradicted the next paragraph, which correctly says
`Element._compile_into_simulation` is `os.getenv("MCDC_LIB")`-based. The conclusion below is
unaffected.

The port changes this: `Element._compile_into_simulation` is `os.getenv("MCDC_LIB")`-based and
`print_error`s when it is unset. So that hardcoded `DATA_DIR` is **deleted by the port**, and
`MCDC_LIB` must be set from Phase 2 onward. Point it at `C:\Projects\MCDC\data\mcdc` unless the
photon generator (§6.2) writes somewhere else. Generator variables `MCDC_LIB_PHOTON` and
`MCDC_EPDL_LIB` come with §4.

### Verification — the environment is ready when this passes

**[REVISED 2026-10-08, second audit]** The first command was not a sufficient check — see
"the install method" above — so it is replaced by a metadata check, which is what actually
failed.

```bash
python -c "import mcdc, importlib.metadata as m; print(mcdc.__file__, m.version('mcdc'))"
python -c "import numba, numpy, cffi; print(numba.__version__, numpy.__version__, cffi.__version__)"
python mcdc/code_factory/rebuild_numba_support.py && git diff --stat
pytest test/unit -q
```

The third command must leave `git diff` **empty** on a clean checkout. If regeneration changes
tracked files before you have touched anything, the generator and the committed output
disagree, and that must be understood before any photon field is added — it would otherwise
look like damage from step 8.

**Windows caveat on the third command. [NEW 2026-10-08, second audit]** With
`core.autocrlf=true`, which is the setting on this machine, regeneration writes CRLF while the
repository stores LF, so `git status` lists all **57** generated files as modified even though
their content is byte-identical after normalisation. `git diff` is correctly empty.
**Read the gate off `git diff`, as written above, and not off `git status`**, or the check
reports a generator/output disagreement that does not exist. `git add --renormalize .` confirms
it: nothing under `mcdc_get/`, `mcdc_set/` or `numba_types.py` survives as a real change.

### Gate result — PASSES IN FULL  **[NEW 2026-10-08, second audit]**

Run against a throwaway `git worktree` of `mcdc-project/dev` @ `295cd909`, under
`mcdc-upstream`, after the two fixes above:

| Command | Result |
|---|---|
| metadata check | `mcdc` imports; `importlib.metadata.version` returns `0.12.0` |
| versions | numba 0.66.0, numpy 2.4.6, cffi 2.1.1 |
| `rebuild_numba_support.py` | `git diff` **empty** — generator and committed output agree |
| `pytest test/unit -q` | **405 passed** in 107 s |

That is the whole of §14's gate, executed rather than asserted. Before the fixes the same
sequence gave 29 collection errors; after the `cffi` fix alone, 404 passed and 1 failed. The
**regression** suite is not covered by this result — it needs the data clone (§5 Phase 3
item 4) and is a Phase 3 gate, not an environment one.

---

## 15. Phase 1 — Execution Record  **[NEW 2026-10-08]**

Phase 1 was executed on 2026-10-08. This section is what happened, as distinct from §5
Phase 1 and §8, which are what was planned. **Three things came out differently, and the
third is large enough to reshape Phase 2.**

### 15.1 Final state

| | |
|---|---|
| Port branch | **`feature/photon-transport`** @ `295cd909` |
| Relationship to base | **0 commits ahead, `git diff` 0 lines — byte-identical to `mcdc-project/dev`** |
| `git status --porcelain -uall` | **0** |
| Snapshot worktree | `C:/Projects/MCDC-photon-old` on `wip/photon-snapshot-pre-refactor` @ `837edebf` |
| Regression data | cloned, 8 files, 73 MB, at `test/regression/mcdc-regression_test_data` |
| Backup branches | `backup/phase0-v1` (`0532385f`) and `-v2` (`6c06c947`) **deleted** |
| Push URLs | `mcdc-project` and `upstream` DISABLED; `origin` only |
| Environment | `mcdc` **0.15.4.dev352+g295cd9096** editable, numba 0.66.0, numpy 2.4.6, cffi 2.1.1 |

**Phase 1 produced no commits, by design.** The whole of it is "branch, and change nothing",
so the only correct outcome is a branch identical to its base. Anything else means Phase 1
leaked work that belongs to Phase 2.

### 15.2 Exit gates — all green

| Gate | Result |
|---|---|
| `import mcdc` + metadata | `C:\Projects\MCDC\mcdc\__init__.py`, version `0.15.4.dev352+g295cd9096` |
| numba / numpy / cffi | 0.66.0 / 2.4.6 / 2.1.1 |
| `rebuild_numba_support.py` → `git diff` | **empty** — generator and committed output agree |
| `pytest test/unit -q` | **405 passed** in 113 s |
| black over the tracked set | **232 files unchanged** |
| `pytest test/regression --name=slab_absorbium --mode=python` | **1 passed** — the clone is wired up |

### 15.3 `.gitignore` — resolved differently from §6.3.7, and why

§6.3.7 said: take upstream's file wholesale, then **re-add** what §6.3.5 justifies, and
remember that `data/` "does not go up in the Phase 4 PR". **The re-adding was done in
`.git/info/exclude` instead of in the committed `.gitignore`.**

Rationale: branching from `mcdc-project/dev` already leaves `.gitignore` byte-identical to
upstream, and `.git/info/exclude` is never committed. So the port branch carries **zero
`.gitignore` churn**, which is what §6.3.7 item 4 asks for — guaranteed by construction rather
than by remembering to strip a rule before the PR. §6.3.4 is satisfied for free: upstream has
no blanket `*.h5`, so taking its file wholesale drops ours.

**§6.3.1's audit is two findings out of date**, because it was measured against
`CEMeNT-PSAAP/MCDC` and 1,060 commits have passed over the file. §6.3.7 step 2 says to
re-check; the re-check found:

| §6.3.1 said | Upstream's file today | Consequence |
|---|---|---|
| "upstream does **not** ignore `*.log`, only `pytestdebug.log`" | **blanket `*.log` at `:51`** | §6.3.5's scoped `photon_transport_code/**/*_full_run.log` rule is **absorbed** — not re-added |
| "`*.csv` is ignored globally (line 62)" — trap #1, nine files "silently omitted" | **no `*.csv` rule at all** | the seven `xs_compare/` CSVs became **visible** for the first time. §6.3.1 asked that their status be a decision rather than an accident, so it was made explicitly: derived output of `compare_photon_xs.py`, excluded **by directory name**, not by `*.csv`, so no other CSV anywhere is hidden |

`__pycache__/` and `*.pyc` (`:13`–`:14`), `*.png` with its `!docs/source/images/**/*.png`
negation (`:40`, `:45`), `*.out` (`:49`) and `*.pbs` all still hold.

**The `*.h5` audit §6.3.4 demands, performed:**

| Path | Attributed to |
|---|---|
| `test/regression/azurv1/answer.h5` | **not ignored** — correct, it is a tracked reference |
| `test/regression/moving_pellet/answer.h5` | **not ignored** — correct |
| `AZURV1_Neutron_1e5.h5` (root product) | `.git/info/exclude` → `/*.h5`, **anchored** |
| `data/mcdc/Al.h5` | `.git/info/exclude` → `/data/` |
| `output.h5` | `.gitignore:39` → `output*.h5`, upstream's narrow rule |

No hit is attributed to a blanket rule, and **26 tracked `answer.h5` files stay visible** —
which is exactly the casualty §6.3.4 was written to prevent. The root rule is `/*.h5` with a
leading slash for that reason.

**One consequence of the exclude-file choice, worth knowing. [NEW]** **black reads
`.gitignore` but not `.git/info/exclude`.** So `black --check .` locally reports **13 files
would be reformatted** — all of them orphans the branch switch left on disk
(`photon_transport_code/` owner-excluded scripts, and two root scratch scripts). Upstream's
`black_lint.yml` runs `black --check .` on a **fresh checkout**, where those files do not
exist. The faithful local equivalent is therefore to format the tracked set:

```bash
git ls-files -z '*.py' | xargs -0 python -m black --check     # 232 unchanged, matches CI
```

Use that, not a bare `black .`, for the whole of Phase 2 and 3. A bare `black .` would also
reach into the cloned `mcdc-regression_test_data` repository.

**Housekeeping done at the same time.** The branch switch left gitignored residue behind,
since git removes only tracked files: **32 `__pycache__` directories holding 119 stale
photon `.pyc` files**, plus empty `mcdc/transport/physics/photon/` and
`test/unit/transport/physics/photon/` directories. All removed, so that Phase 2 creates those
packages fresh and nothing greps as "photon already exists here". The 1.61 GB of SLURM `.out`
logs and the rest of `photon_transport_code/` were **left alone** — §12 says those full-history
outputs underpin the paper's figures and should be deposited for a DOI, so they are not
deleted until that happens.

### 15.4 [MAJOR] An authoritative photon schema already exists upstream

**This is the single most consequential thing Phase 1 turned up, and no revision of this
document anticipated it.**

`mcdc-project/mcdc-regression_test_data` — the repository §5 Phase 3 item 4 tells us to clone
— contains `Al.h5` with a **fully populated `photon_reactions/` group**, on a **6,682-point
energy grid, the same length as ours**.

**§2.8 is wrong.** It states that upstream "extracts only the electron blocks and writes no
`photon_reactions/` group". A `photon_reactions/` group exists. What is *also* true, and
determines how much authority to give it:

- **No upstream code reads it** — `grep -rn photon_reactions mcdc/ test/ tools/` finds nothing.
- **No upstream generator writes it** — `tools/data_library_generator/electron/` mentions
  photon in exactly one comment.
- **Only `Al.h5` has it.** The other seven files in the repository are neutron nuclides.

So it is a schema someone produced by hand or with an unreleased tool, parked in the data
repository ahead of the code. Treat it as **the strongest available evidence of the schema
maintainers would accept**, not as a contract.

**The measured structure**, which should be the generator's target in preference to §6.2's
invented one:

```
photon_reactions/
  xs_energy_grid                                    (6682,)
  coherent_scattering/MT502/        attrs: MT=502
    xs                              (6682,)  attrs: offset=0, unit="barns"
    form_factor/{momentum_transfer, value}   (1209,)  mt attrs: unit="1/angstrom"
    anomalous_scattering/{real,imaginary}/{energy, value}   (373,)  unit="eV"
    reference_frame
  incoherent_scattering/MT504/      attrs: MT=504
    xs                              (6682,)  attrs: offset=0, unit="barns"
    scattering_function/{momentum_transfer, value}   (445,)  unit="1/angstrom"
  pair_production/
    MT515/xs                        attrs: MT=515, offset=0, unit="barns"   (electron field)
    MT517/xs                        attrs: MT=517, offset=0, unit="barns"   (nuclear field)
    total/xs                        attrs: unit="barns"                     (no MT group)
  photoelectric/MT522/              attrs: MT=522
    xs                              (6682,)
    subshells/MT-534 .. MT-5NN/{binding_energy, energy_grid, xs}
                                    binding_energy, energy_grid: unit="eV"
atomic_relaxation/                  top-level -- confirms decision 2.9
  n_subshells, subshells/...
```

**What this overrides in the existing plan:**

| Section | Said | The reference file says |
|---|---|---|
| §4 Units, §6.2 | energies on disk in **MeV** with `attrs["unit"]="MeV"`; "convert eV→MeV on disk" | energies on disk in **eV**, declared `unit="eV"`. `read_energy` honours either, so **our eV data may need no conversion at all** — this removes most of what §4 calls "the single largest source of silent numerical error" |
| §6.2 group names | `coherent`, `incoherent`, `photoelectric` | **`coherent_scattering`**, **`incoherent_scattering`**, **`photoelectric`** |
| §6.2 MT table | pair total = **516**, plus 515/517 | **no MT516.** `MT515` and `MT517` as sibling groups plus an unnumbered `total/xs` |
| §6.2 MT naming | `MT-NNN` throughout | **`MT502`/`MT504`/`MT515`/`MT517`/`MT522` without a hyphen**, but subshells **with** one (`MT-534`). Inconsistent upstream; match it anyway |
| §4 flat_data table | coherent form factor only | also **`anomalous_scattering`** (real + imaginary), which our EPDL extraction does not carry |
| §6.2 | our incoherent group holds `xs` only | also **`scattering_function`** S(q) — the incoherent binding correction. **We do not have this**, and its absence is a physics gap, not a schema gap: pure Klein–Nishina without S(q) overestimates low-energy incoherent scattering |
| §6.2 subshell PE | `MT-534+/{xs}` | `MT-534+/{binding_energy, energy_grid, xs}` — each subshell carries **its own grid**, so it is `DataTable`-shaped as §4.5 predicted |

### Resolved, not deferred  **[DECIDED 2026-10-08]**

An earlier draft of this subsection asked the owner to choose between §6.2's schema and this
one. **That was an over-escalation and is withdrawn.** §6.2, plus the electron and proton
generators it points at, was always sufficient to write the generator — the discovered file
does not add a decision, it removes three guesses. §6.2's own stated goal is "keep EPDL, adopt
**upstream's** layout", so where a real upstream artifact and an invented convention disagree,
the artifact wins. Each row of the table above resolves that way:

| Detail | Resolution |
|---|---|
| On-disk energy unit | **eV**, with `attrs["unit"] = "eV"`. Our data is already eV, so the conversion §4 called "the single largest source of silent numerical error" **largely disappears**. `read_energy` honours either unit, so this is a free simplification, not a compromise |
| Group names | **`coherent_scattering`**, **`incoherent_scattering`**, `photoelectric`, `pair_production` |
| Pair production | **`MT515` + `MT517` siblings plus an unnumbered `total/xs`.** No MT516 |
| MT group spelling | `MT502`/`MT504`/`MT515`/`MT517`/`MT522` **unhyphenated**; photoelectric subshells `MT-534+` **hyphenated**. Inconsistent, but matched exactly |
| Subshell PE | `MT-534+/{binding_energy, energy_grid, xs}` — per-subshell grid, so `DataTable`-shaped per §4.5 |
| `anomalous_scattering`, `scattering_function` | **Not written.** We have neither, and §2.10 says the photon physics is not changed by this merge, so adding S(q) binding corrections is out of scope. Omitting a dataset nothing reads is schema-compatible; record it as a gap for the electron-coupling PR |
| Everything else | §6.2 stands unchanged — the `generate.py`/`util.py` split, the CLI to mirror, the relaxation translation table, the five-heading README |

**One step is still worth doing first, as verification rather than as a decision:** diff our
`data/mcdc/Al.h5` against the reference file field by field. Same element, same grid length, so
the comparison is direct. If the two were built from the same EPDL release the numbers should
agree, and any disagreement is a bug in one of them — which is exactly the diff §6 item 3
already demands before `data/mcdc/` is retired.

**Still worth adding to §6.4 as a maintainer question**, now purely informational rather than
blocking: *there is a `photon_reactions/` group in your regression data that nothing reads and
no generator writes — is that the schema you want, who produced it, and does an unreleased
photon generator exist?* The answer costs nothing to wait for, because we are proceeding on the
artifact regardless.

### 15.5 How regression decks get their data library — and a Phase 3 blocker

§14 says to point `MCDC_LIB` at `C:\Projects\MCDC\data\mcdc`. **That is right for local
runs and wrong for anything that goes in the PR.** The harness runs each `input.py` as a
subprocess from its own case directory, and upstream's decks set the variable **themselves**,
relative:

```python
# test/regression/lockwood/input.py:8  -- the electron deck, i.e. the photon template
os.environ["MCDC_LIB"] = "../mcdc-regression_test_data/"
```

Seven decks do this (`basic_weight_windows`, `hybrid_multigroup`, `lockwood`, `pincell`,
`pincell-energy_deposition`, `pincell-k_eigenvalue`, `proton_beam`). An absolute Windows path
would fail on every CI runner.

So each migrated photon deck (§7) carries that same two-line preamble. **Copy electron's
exactly** — `lockwood/input.py` is the template for this as it is for per-element data
generally.

### Resolved from the electron precedent  **[DECIDED 2026-10-08]**

An earlier draft called this a blocker needing an owner decision between three options.
**Withdrawn — the electron precedent answers it, and the quantity involved is small and
bounded.**

**What the decks actually need.** Measured by parsing `elements=[...]` and the composition
tables out of all eight decks: **eleven elements**, and `AZURV1_photon_v3.py` needs none at all
because it uses the constant-XS treatment (§2.2).

| Z | 1 | 7 | 8 | 11 | 12 | 13 | 14 | 18 | 20 | 26 | 82 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| | H | N | O | Na | Mg | Al | Si | Ar | Ca | Fe | Pb |

All eleven are already in `data/mcdc/`, and they total **9.7 MB** — `Pb.h5` is the largest at
3.2 MB. That is the same order as the single `Al.h5` the regression library already carries for
electron, so nothing here is unusual in kind or size.

**Local Phase 3 runs: copy the eleven files into the clone.** It is a working clone; adding
files to it is not a push. Verified that the `regression_data` fixture's `git pull` tolerates
added untracked files (exit 0), and the fixture warns rather than skips even if a pull fails, so
an enriched clone stays usable offline.

**The PR: the data goes to the maintainers' repository the same way electron's did.** Someone
had to add `Al.h5` to `mcdc-regression_test_data` when electron landed, and the same step
applies to photon. That makes it a **Phase 4 coordination item, not a design decision** — it
belongs in the PR description beside the §6.4 questions, and it is why §15.4's maintainer
question is worth asking early even though we are not waiting on it. Nothing about it blocks
writing the decks, generating their `answer.h5` locally, or anything in Phase 2.

### 15.6 Handover to Phase 2

The port branch is clean and the environment is proven. **Phase 2 is unblocked — there is
nothing to decide first.** It begins at §5's step table, which now runs to 22 steps. Carry
these five standing rules through it:

1. **Schema: follow the reference file** (§15.4's resolution table) — eV on disk,
   `coherent_scattering` / `incoherent_scattering`, `MT515`+`MT517`+`total`, unhyphenated
   reaction MTs, hyphenated subshell MTs. §6.2 governs everything else.
2. **Decks: copy `lockwood/input.py`'s `MCDC_LIB` preamble verbatim** and put the eleven
   element files in the local clone (§15.5). The maintainers' copy is a Phase 4 item.
3. **Format** with `git ls-files -z '*.py' | xargs -0 python -m black --check`, never a bare
   `black .` (§15.3).
4. **Re-run `rebuild_numba_support.py` after every annotated-field change** (§5 Phase 2 step 8
   — "not optional and not last"), and read the gate off `git diff`, never `git status`
   (§14's Windows caveat).
5. **The snapshot is at `C:/Projects/MCDC-photon-old`** for side-by-side reference. Leave it
   until Phase 3 is green, then `git worktree remove ../MCDC-photon-old`.

**A note on where work lands, since it caused confusion once.** `origin` is the remote *name*
for `DouglasHouser/MCDC`; `wip/photon-snapshot-pre-refactor` is a *branch on* it. Every
planning and documentation commit belongs on that branch and has gone there. `origin/dev`
remains untouched at `86ee515a`. Phase 2's code belongs on `feature/photon-transport`, pushed
with `git push -u origin feature/photon-transport` on its first commit.

**`feature/photon-transport` has not been pushed.** It has no commits of its own, so there is
nothing to push; its tracking ref is `mcdc-project/dev`, whose push URL is DISABLED. On the
first Phase 2 commit, push with `git push -u origin feature/photon-transport` to retarget
tracking at the writable remote.
