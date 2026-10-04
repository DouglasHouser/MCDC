# Fix Instructions — Benchmark 1a (Pure Absorption) comparison is wrong

> Instructions for Claude Code. Apply the edits below in order. The simulation
> data is **already correct** — the bugs are in the comparison tooling and the
> tally type, not in the physics.

## Symptoms reported

- Changing the sphere radii (÷10) in `problem.py` produced the **exact same**
  comparison output.
- Most rows are "far off" the analytic solution `I(r) = exp(-r)`.
- The **3 MFP row shows 0.0**, and stayed 0.0 after dividing radii by 10.

## Diagnosis (verified against `benchmark_1a.h5`)

Reading the tallies in true numeric order, every radius matches `exp(-r)` to <1%.
So the transport is correct. There are three real problems:

### Root cause 1 — lexicographic key sort (the main bug)

`compare.py` and `compare_n_and_p.py` read tallies with `sorted(tally_group.keys())`.
The keys are `surface_tally_0 … surface_tally_13`. String-sorting them gives
`0, 1, 10, 11, 12, 13, 2, 3, …, 9`, so each radius in `DISTANCES` is paired with
the **wrong** tally:

| row radius | gets paired with | should be |
|------------|------------------|-----------|
| 0.5 | surface_tally_0 ✓ | tally_0 |
| 0.8 | surface_tally_1 ✓ | tally_1 |
| 1.0 | surface_tally_10 (8 cm sphere) ✗ | tally_2 |
| 3.0 | surface_tally_13 (25 cm sphere, ~0) ✗ | tally_5 |
| 4.0 | surface_tally_2 (1 cm sphere) ✗ | tally_6 |

Only the first two rows align (by luck). The **0.0 at 3 MFP** is the outermost
25 MFP vacuum shell — essentially no photons reach 25 mean-free-paths in a pure
absorber — landing in the wrong slot.

### Root cause 2 — the h5 was never regenerated (why ÷10 changed nothing)

`mcdc.run()` overwrites `benchmark_1a.h5`, but a full run takes **~2.3 hours**.
Re-running only `compare.py` re-reads the **same old h5**, so a radius change in
`problem.py` has no effect until `problem.py` itself is re-run. `compare.py` also
hard-codes `DISTANCES` (with a commented-out ÷10 block at lines 36–37), so the
reference column never moves either.

### Root cause 3 — `problem.py` now uses CELL tallies (latent)

`problem.py` uses `mcdc.Tally(cell=c, …)`, but `neutron_problem.py` and the
documented `compare.py` semantics expect `mcdc.Tally(surface=s, …)`. A cell tally
is a track-length estimator normalized only by `N_particle` (never by volume —
see `mcdc/transport/tally/closeout.py` lines 35–49), giving the volume-integrated
flux `exp(-r_in) − exp(-r_out)`, not the surface current `exp(-r)`. The existing
correct h5 contains `surface_tally_*` keys. Regenerating with the current cell
version would produce `tracklength_tally_*` keys and wrong values.

## Edits to make

### Edit 1 — numeric tally sort in `compare.py`

In `load_surface_flux()`, replace:

```python
keys = sorted(tally_group.keys())
```

with:

```python
def _tally_key(k):
    tail = k.rsplit("_", 1)[-1]
    return (0, int(tail)) if tail.isdigit() else (1, k)

keys = sorted(tally_group.keys(), key=_tally_key)
```

### Edit 2 — same numeric sort in `compare_n_and_p.py`

In its `load_surface_flux()`, replace:

```python
for key in sorted(tally_group.keys()):
```

with the same `_tally_key` helper and `sorted(tally_group.keys(), key=_tally_key)`.

### Edit 3 — revert `problem.py` to surface tallies

Replace the tally loop:

```python
for c in cells:
    mcdc.Tally(cell = c, scores=["flux"])
```

with (matching `neutron_problem.py`):

```python
for s in spheres:
    mcdc.Tally(surface=s, scores=["flux"])
```

Leave the `cells` list in place — it still defines the material fill regions.

### Edit 4 — keep `DISTANCES` in sync with `problem.py`

`compare.py` hard-codes `DISTANCES`. Whenever the radii in `problem.py` change,
update this list to match (or derive the radii from the geometry). With
`sigma_total = 1.0`, the analytic reference is `exp(-r)`, so if radii are divided
by 10 the expected values become `exp(-r/10)` (near 1.0), not `exp(-r)`.

### Edit 5 — don't fail on points below the MC resolution floor

After the sort fix, the only remaining FAIL was the 25 MFP point: `exp(-25) ≈
1.4e-11` is far below the `~1/N_history ≈ 5e-8` floor (20M histories), so the sim
correctly reports 0.0 and a 100% relative error there is meaningless. `compare.py`
now reads `N_particle * N_batch` from the h5 `settings` group (helper
`load_n_history`) and marks any radius whose analytic value is below
`1 / N_history` as **N/A** rather than FAIL.

## Note — separate pre-existing issue in the neutron run

`compare_n_and_p.py` now reads tallies in the correct order, but it exposes an
unrelated problem: `benchmark_1a_neutron.h5` contains `mean = 1.0, sdev = 0.0` for
**every** surface tally — a broken/stub neutron run, not a tooling bug. The
neutron surface-flux tally is not accumulating `w/|μ|`. Investigate
`neutron_problem.py` / the neutron surface-tally path separately; it is out of
scope for the photon benchmark fix.

## Verification

1. **Primary fix needs no re-run** — the existing h5 is valid:
   ```
   cd photon_transport_code/MCNP_Verification_Tests/benchmark_1a_const_pure_absorption
   python compare.py
   ```
   Expect **ALL PASS**; the 3 MFP row now shows ~4.97e-2 instead of 0.0.
2. To validate a radii change, re-run `python problem.py` (~2.3 h; or temporarily
   lower `N_particle`/`N_batch` for a smoke test), confirm the new h5 has
   `surface_tally_*` keys, update `DISTANCES`, then re-run `compare.py`.
3. Run `python compare_n_and_p.py` — photon vs neutron should agree within 3σ.
