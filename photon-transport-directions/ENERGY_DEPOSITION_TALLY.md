# Energy-Deposition Tally for Photon Transport

## Quick Context

Add a new tally score, `energy-deposit`, that records **how much energy each photon deposits at each
location**. Method: an **analog collision estimator, binned on a structured mesh**. At every real photon
collision we already know how much energy the photon loses (recoil electron, photoelectron/Auger, or pair
kinetic energy); this direction scores that lost energy into the mesh voxel where the collision occurred.

This is **photon-only**. Do **not** touch neutron code. (There is currently no neutron energy-deposition
tally in MCDC, so there is nothing on the neutron side to mirror — the design below patterns itself on the
existing photon collision physics and the existing mesh-tally machinery.)

Result: an HDF5 dataset `tallies/<name>/energy-deposit/{mean,sdev}` giving MeV deposited per source
particle, per voxel.

## READ FIRST (code, in this order)

- `mcdc/transport/physics/photon/interface.py` — `collision()`, the four reaction branches. This is where
  deposited energy is computed.
- `mcdc/transport/tally/score.py` — `tracklength_tally()` (mesh-index sweep) and `make_scores()` (score
  dispatch). You will mirror the mesh-indexing logic and extend the dispatch.
- `mcdc/object_/tally.py` — score-string parser (`~line 120`) and `decode_score_type()` (`~line 242`).
- `mcdc/transport/simulation.py` — the collision call site (`~line 293`) and the track-length tally loop
  (`~line 398`). You will add a parallel loop for the collision-energy tally.
- `mcdc/transport/mesh/interface.py` — `get_indices()` maps a particle position to `(i_x, i_y, i_z)`.
- `mcdc/output.py` — `create_tally_dataset()` writes every score automatically; no change needed there.

## WORKING DIRECTORY

```
c:\Projects\MCDC\
```

## REFERENCE PATTERNS (copy these, don't invent new ones)

- **Score dispatch:** `make_scores()` in `mcdc/transport/tally/score.py` — how `SCORE_COLLISION`,
  `SCORE_CAPTURE`, etc. are handled in the `if/elif` chain.
- **Mesh indexing:** `tracklength_tally()` in the same file — how a mesh tally computes `i_x, i_y, i_z`,
  applies the time filter, and builds `idx_base` from strides. Your point-estimator reuses this, minus the
  distance sweep.
- **Tally loop:** `simulation.py:398-419` — how cell tallies and mesh tallies are iterated during an active
  cycle.
- **Score constant + string:** `SCORE_NET_CURRENT` in `mcdc/constant.py`, `mcdc/object_/tally.py` — the
  full path a new score name travels (constant → parser → decoder → output).
- **Style:** the other `photon-transport-directions/PHASE_*.md` files.

## PHYSICS: energy deposited per collision

Capture `E_in = particle_container[0]["E"]` **before** any energy is modified (at the top of the
tabulated-cross-section section of `collision()`), then compute the deposited energy per branch:

| Reaction | Deposited locally | Notes |
|---|---|---|
| Coherent (Rayleigh) | `0.0` | elastic; direction changes, energy does not |
| Compton (incoherent) | `E_in * (1.0 - eps)` | recoil-electron energy; scattered photon keeps `E_in * eps` |
| Photoelectric | `E_in - E1 - E2` | `E1, E2` = fluorescence photon energies (both `0.0` if no fluorescence → full `E_in`) |
| Pair production | `E_in - 2.0 * _M_E` (= `E_in - 1.022` MeV) | pair kinetic energy; the two 0.511 MeV annihilation photons escape and deposit elsewhere when they later interact |
| Constant-XS absorb branch | `E_in` | analog capture in benchmark materials |
| Constant-XS scatter branch | `0.0` | elastic |

**Unifying rule (sanity check):**
`E_dep = E_in − (energy of the primary photon still alive) − (energy of any banked secondary photon)`.
This holds for every branch above and is the safest way to reason about correctness.

Energy conservation is preserved: the annihilation and fluorescence photons that carry energy *away* from
the site are transported and will deposit their energy at their own later collision sites.

## DELIVERABLES (edits, photon-only)

### 1. `mcdc/constant.py`
Add the new score id after `SCORE_SPACE_MOMENT_MU_SQ = 12`:
```python
SCORE_ENERGY_DEPOSIT = 13
```

### 2. `mcdc/object_/tally.py`
- Import `SCORE_ENERGY_DEPOSIT`.
- In the score-string parser (the `if score == "flux": ... elif ...` chain, ~line 120) add:
  ```python
  elif score == "energy-deposit":
      self.scores.append(SCORE_ENERGY_DEPOSIT)
  ```
- In `decode_score_type()` (~line 242) add:
  ```python
  elif type_ == SCORE_ENERGY_DEPOSIT:
      return "Energy deposit" if not lower_case else "energy-deposit"
  ```
- Add a short validation/comment: `energy-deposit` is only meaningful on a mesh (or cell)
  `TallyTracklength`. It is a collision estimator, so it ignores the direction (`mu`, `azi`) and energy
  phase-space filters; only the spatial mesh and (optionally) the time filter apply.

### 3. `mcdc/transport/physics/photon/interface.py`
- Change `collision()` to **return a float `E_dep`** (currently returns `None`).
- Capture `E_in` before energies change; in each branch compute `E_dep` per the physics table.
  - Initialize `E_dep = 0.0` at the top and set it in the Compton / photoelectric / pair / constant-XS
    branches; coherent and constant-XS scatter leave it `0.0`.
  - Every early `return` in the function must return a float (e.g. `return 0.0` for the
    `Sigma_T <= 0.0` and `sigma_t <= 0.0` guards).
- End with `return E_dep`.

### 4. `mcdc/transport/physics/interface.py`
The dispatcher `collision()` (~line 82) must propagate the return value:
```python
@njit
def collision(particle_container, mcdc, data):
    particle = particle_container[0]
    if particle["particle_type"] == PARTICLE_NEUTRON:
        neutron.collision(particle_container, mcdc, data)
        return 0.0                       # neutrons: unchanged, no deposition tally
    elif particle["particle_type"] == PARTICLE_PHOTON:
        return photon.collision(particle_container, mcdc, data)
    return 0.0
```

### 5. `mcdc/transport/tally/score.py`
- Import `SCORE_ENERGY_DEPOSIT`.
- In `make_scores()` add a no-op branch so the flux/track-length sweep never writes into this slot
  (deposition is scored only at collisions):
  ```python
  elif score_type == SCORE_ENERGY_DEPOSIT:
      score = 0.0
  ```
- Add a new `@njit` function `collision_energy_tally(particle_container, E_dep, tally, mcdc, data)`. It is a
  **point** estimator (no distance sweep). Mirror the mesh-index portion of `tracklength_tally()`:
  1. `tally_base = mcdc["tallies"][tally["parent_ID"]]`.
  2. Locate the score slot for `SCORE_ENERGY_DEPOSIT`:
     ```python
     i_edep = -1
     for i_score in range(tally_base["scores_length"]):
         if mcdc_get.tally.scores(i_score, tally_base, data) == SCORE_ENERGY_DEPOSIT:
             i_edep = i_score
             break
     if i_edep == -1:
         return
     ```
  3. Compute the mesh voxel index at the collision point via
     `mesh_module.get_indices(particle_container, mesh, mcdc, data)`; return if any index is out of range
     (`-1` or `>= N`). Also support the cell-tally case (`SPATIAL_FILTER_CELL`) with no mesh indices.
  4. Compute the time-filter index for the current `particle["t"]` (reuse the time-bin logic from
     `tracklength_tally`); leave `i_mu = i_azi = i_energy = 0` (filters not applied).
  5. Build `idx_base` from `tally_base` strides + mesh strides exactly as `tracklength_tally` does.
  6. `atomic_add(data, idx_base + i_edep, E_dep * particle_container[0]["w"])`.

### 6. `mcdc/transport/simulation.py`
- At the collision call site (~line 293) capture the return value:
  ```python
  if particle["event"] & EVENT_COLLISION:
      E_dep = physics.collision(particle_container, mcdc, data)
      if mcdc["cycle_active"] and E_dep > 0.0:
          _score_energy_deposition(particle_container, E_dep, mcdc, data)
  ```
- Add `_score_energy_deposition` (or inline it) mirroring the tally loop at `simulation.py:398-419`: iterate
  the current cell's tallies and the mesh tracklength tallies, and call
  `tally_module.score.collision_energy_tally(particle_container, E_dep, tally, mcdc, data)` for each. The
  slot check inside `collision_energy_tally` makes it a no-op for tallies that don't request
  `energy-deposit`, so it is safe to call on every tracklength tally.
- **Important:** score using the particle position/time *at the collision site*. `physics.collision` does
  not move the particle (movement happens later via `particle_module.move`), so `particle["x/y/z/t"]` are
  still the collision coordinates at this point — verify this holds before finalizing.

### 7. Output & closeout — NO CHANGES
`closeout.accumulate()` / `finalize()` operate on all bins generically, and `output.create_tally_dataset()`
writes each score's `mean`/`sdev` using `decode_score_type`. Once step 2 is done, the dataset
`tallies/<name>/energy-deposit/{mean,sdev}` and the mesh grid axes (`grid/x`, `grid/y`, `grid/z`) appear
automatically. Just confirm this after a run.

## REQUIREMENTS

- ✅ Photon code only — zero edits to any `neutron` module or neutron data.
- ✅ `collision()` and the physics dispatcher return a float `E_dep`; every early return returns a float.
- ✅ `E_dep` computed by the unifying rule; coherent/elastic deposit `0.0`.
- ✅ Deposition scored at the collision voxel, weighted by `particle["w"]`, via `atomic_add`.
- ✅ `make_scores()` never contributes to the `energy-deposit` slot (no double counting with the
  track-length sweep).
- ✅ A tally may request `scores=["flux", "energy-deposit"]` together and both populate correctly.
- ✅ No new circular imports (scoring is driven from `simulation.py`, not from inside `physics`).

## VALIDATION

Run from `c:\Projects\MCDC\`:

```bash
# 1. Smoke test: a mesh problem requesting the new score produces the dataset
python -c "import h5py; f=h5py.File('photon_slab.h5','r'); print(list(f['tallies']))"
# expect an 'energy-deposit' group with 'mean' and 'sdev', shaped like the mesh (Nx,Ny,Nz)

# 2. Unit tests for the per-branch E_dep formulas
pytest test/unit/transport/physics/ -q
```

Build a small check problem patterned on the existing `photon_slab` inputs: a `MeshStructured` over the
slab with `mcdc.Tally(mesh=..., scores=["flux", "energy-deposit"])`, monoenergetic source.

- **Energy balance:** `sum(energy-deposit over all voxels)` + `energy leaking across boundaries` +
  `energy still carried by live/banked photons` ≈ `total source energy`. Script this like
  `validate_photon_xs.py`.
- **Pure photoelectric absorber:** in a strong-PE material with fluorescence off, the full `E_in` is
  deposited at the first collision — compare the tallied total to a hand calculation.
- **Fluorescence A/B:** rerun the `fluor_on` vs `fluor_off` configuration (see `validate_fluorescence.py`).
  Local deposition should be *lower* with fluorescence on, because characteristic X-rays escape and
  deposit elsewhere.

## SUCCESS CRITERIA

- ✅ `scores=["energy-deposit"]` runs without error on a mesh tally and writes
  `tallies/<name>/energy-deposit/{mean,sdev}`.
- ✅ Energy-balance check closes to within statistical error.
- ✅ Photoelectric hand-calc matches; fluorescence A/B shows the expected reduction.
- ✅ Existing photon regression/validation outputs (flux tallies) are unchanged.
- ✅ Unit tests for the per-branch `E_dep` formulas pass.

## UNITS & POST-PROCESSING

The tally accumulates **MeV deposited per source particle, summed per voxel**. To get a deposited-energy
*density*, divide each voxel's value by its volume (derivable from `grid/x`, `grid/y`, `grid/z` in the
output). Leave that as a post-processing step; do not bake it into the tally.

## IMPORTANT — STOP

This document is the implementation direction only. Implement exactly the photon-side steps above; make no
neutron changes and add no score types beyond `energy-deposit`.
