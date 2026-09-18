# Coherent (Rayleigh) Form-Factor Angular Sampler — Implementation Directions

Status: **DESIGN** (not yet implemented)
Scope: standard atomic form factor `F(q, Z)` only — anomalous scattering factors
(`F′`, `F″`) are explicitly out of scope for this pass.

**Implementation order:** §2 (import form factors into `data/mcdc`) **first**, then §3 physics,
§4 sampler, §5 flat-data model, §6 loader, §7 code touch-points, §8 validation.

---

## 1. Problem & Current State

Coherent (Rayleigh) scattering is currently deflected **isotropically**. The dataset ships
only the *integrated* coherent cross section, not the atomic form factor `F(q, Z)`, so the
outgoing direction cannot be sampled physically. Two code paths carry the same
approximation and the same TODO:

`mcdc/transport/physics/photon/interface.py`, coherent branch (lines 128–145):

```python
if xi < Sigma_coh:
    # Coherent (Rayleigh) scattering — elastic: no energy change.
    #
    # APPROXIMATION: the dataset carries only an integrated coherent cross
    # section (no atomic form factor F(q, Z)), so the outgoing direction is
    # sampled isotropically. Real Rayleigh scattering is strongly
    # forward-peaked, especially at high energy / high Z.
    # TODO: add a Rayleigh form-factor angular sampler (e.g. inverse-CDF on
    # the tabulated F(q, Z)^2 differential cross section) for MCNP-level
    # angular agreement. Energy is correctly conserved here, so attenuation
    # totals are already correct; only the deflection distribution is
    # approximate.
    ux, uy, uz = sample_isotropic_direction(particle_container)
    particle_container[0]["ux"] = ux
    particle_container[0]["uy"] = uy
    particle_container[0]["uz"] = uz
```

`mcdc/object_/photon_reaction.py`, `PhotonReactionCoherent.perform_collision` — the object
API mirror of the same fallback (samples `mu = 2*rand - 1` isotropically).

Key point: **totals and attenuation are already correct** because coherent scattering is
elastic (energy conserved) and the *magnitude* comes from the tabulated cross section. Only
the **angular deflection** is approximate. This design fixes only the deflection.

---

## 2. Step 1 — Import Form Factors from EPDL into `data/mcdc` (do this first)

The form factor is **not** in the current data files: `data/mcdc/*.h5` carries only
`elastic/MT-502/xs`, and the raw files hold only `coherent_scattering/cross_section`. The
data **does** exist in the EPDL source at `data/endf/epdl/EPDL.ZA0*.endf`, section
**MF=27 / MT=502**. Step 1 parses those files and writes the form factor **directly into each
element file in `data/mcdc/`** — no intermediate raw/reformat stage.

### 2.1 Element ↔ EPDL file mapping

Every `data/mcdc/*.h5` stores its atomic number under `atomic_number`. EPDL files are named
by `ZA = Z × 1000`. So for each element file:

```
Z            = h5file['atomic_number'][()]
epdl_path    = f"data/endf/epdl/EPDL.ZA{Z:03d}000.endf"
```

There are 100 element files and 100 EPDL files. Process **all** of them — not just the four
elements (`Z = 1, 8, 13, 82`) that `PhotonMaterial` currently accepts — so the data is ready
when more elements are enabled.

### 2.2 EPDL MF=27/MT=502 record layout (ENDF-6 TAB1)

ENDF lines carry the section id in fixed columns: **MF in columns 71–72, MT in columns
73–75** (0-based slice `line[70:72]` and `line[72:75]`). Filter the file to lines whose
`(MF, MT) == ("27", "502")`. Within that block the record is a standard TAB1:

```
line 0  HEAD : ZA, AWR, ...                        (skip)
line 1  CONT : C1, C2, L1, L2, NR, NP              (NP = number of (x,F) pairs)
line 2  interpolation ranges : NBT(1..NR), INT(...)(skip — lin-lin here)
line 3+ data : NP (x, F) pairs, packed 6 fields    (x, F, x, F, x, F) per line
              of 11 characters each (3 pairs/line)
```

The values are ENDF 11-character floats. In this EPDL revision they parse cleanly with
Python `float()` (`.001000000`, `13.0000000`, `1.00000E+9`, trailing-dot integers like
`819603763.`), but a parser should still defensively handle the classic Fortran style
(`1.234-5` → `1.234e-5`). Verified for Al (`EPDL.ZA013000.endf`): NP = 1209, first pair
`(0.0, 13.0)`, i.e. `F(0) = Z`, decreasing to `(1.0e9, 1.013e-27)`.

Store `x` (momentum transfer) and `F` **verbatim** — do **not** unit-convert at import time.
The EPDL-x → code-q conversion (§3) belongs in the loader/sampler so the on-disk data stays
a faithful copy of EPDL.

### 2.3 Where to write it in each `data/mcdc/*.h5`

Mirror the existing `elastic/MT-502/xs` layout by adding a sibling group:

```
photon_reactions/
  elastic/
    MT-502/
      xs                      (existing)
      form_factor/            (NEW)
        momentum_transfer     (x grid, float64, NP values)
        form_factor           (F values, float64, NP values)
```

Make the write **idempotent**: if `form_factor` already exists, delete and rewrite it, so the
script can be re-run safely.

### 2.4 Script skeleton (`photon_transport_code/tools/add_coherent_form_factors.py`)

```python
import glob
import h5py
import numpy as np


def _endf_float(field):
    """Parse an 11-char ENDF float, tolerating Fortran '1.234-5' exponents."""
    s = field.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        # Fortran style: insert 'e' before a sign that follows a digit/'.'
        mant = s[0]
        for prev, ch in zip(s, s[1:]):
            if ch in "+-" and prev not in "eE":
                mant += "e" + ch
            else:
                mant += ch
        return float(mant)


def read_formfactor(epdl_path):
    """Return (x, F) arrays from MF=27/MT=502 of an EPDL file."""
    with open(epdl_path) as f:
        block = [
            ln for ln in f
            if len(ln) >= 75 and ln[70:72].strip() == "27" and ln[72:75].strip() == "502"
        ]
    # line0 = HEAD, line1 = CONT (NP in cols 56-66), line2 = interp ranges
    NP = int(block[1][55:66])
    vals = []
    for ln in block[3:]:
        for i in range(0, 66, 11):
            v = _endf_float(ln[i:i + 11])
            if v is not None:
                vals.append(v)
    x = np.asarray(vals[0::2], dtype=np.float64)
    F = np.asarray(vals[1::2], dtype=np.float64)
    assert len(x) == len(F) == NP, (len(x), len(F), NP)
    return x, F


def add_form_factor(mcdc_path, epdl_dir="data/endf/epdl"):
    with h5py.File(mcdc_path, "r+") as h:
        Z = int(h["atomic_number"][()])
        x, F = read_formfactor(f"{epdl_dir}/EPDL.ZA{Z:03d}000.endf")
        # Sanity: F(0) == Z, monotone x, F non-increasing near origin
        assert abs(F[0] - Z) < 1e-6, (Z, F[0])
        assert np.all(np.diff(x) > 0.0)
        grp = h.require_group("photon_reactions/elastic/MT-502/form_factor")
        for name, arr in (("momentum_transfer", x), ("form_factor", F)):
            if name in grp:
                del grp[name]
            grp.create_dataset(name, data=arr)


if __name__ == "__main__":
    for path in sorted(glob.glob("data/mcdc/*.h5")):
        add_form_factor(path)
        print(f"form factor added: {path}")
```

Run from the repo root (conda env `mcdc-env`). After it completes, every `data/mcdc/*.h5`
carries the `elastic/MT-502/form_factor` group (see §8 validation).

---

## 3. Physics

Standard (non-relativistic form-factor) Rayleigh differential cross section:

```
dσ/dΩ = (r_e² / 2) · (1 + μ²) · F(q, Z)²
```

- `r_e` — classical electron radius (already available as a constant in the photon module).
- `μ = cos θ` — scattering cosine.
- `(1 + μ²)/2` — the Thomson angular factor.
- `F(q, Z)` — atomic form factor, monotonically decreasing from `F(0) = Z` toward 0 as `q`
  grows. This is the factor that produces the strong forward peaking.

**Momentum transfer ↔ angle.** With photon wavenumber `k = E / (hc)`:

```
q² = 2 k² (1 − μ)        ⇒     μ = 1 − q² / (2 k²)
q_max = 2 k               (at μ = −1, backscatter)
```

**⚠ Unit conversion — the single easiest place to introduce a silent bug.**
EPDL tabulates the form factor against its own momentum-transfer variable
`x = sin(θ/2) / λ`, **not** against `q` in the code's natural units. With
`hc = 12.39842 keV·Å`:

```
x [Å⁻¹] = E[keV] · sin(θ/2) / 12.39842
```

Because `sin²(θ/2) = (1 − μ)/2`, the code's `q` and EPDL's `x` are proportional; the loader
(or the sampler) **must** convert the stored EPDL x-grid into whatever unit the sampler works
in, or store the conversion constant explicitly. Do not assume EPDL `x` equals the code's
`q`. Pin this down against a known EPDL value before trusting any angular output. A cheap
runtime invariant that catches a wrong conversion immediately: `F` evaluated at the grid
origin must equal `Z`, and the *mean* scattering angle must **fall** as `E` rises.

---

## 4. Recommended Sampling Algorithm — Inverse-CDF on F²

This is the method named in the TODO and is the standard used by EGSnrc / PENELOPE. It is
robust across the full energy range (unlike the rejection variant below).

**Precompute once (at data-build / load time), per element:** the cumulative integral of `F²`
over `x²`:

```
A(x²) = ∫₀^{x²} F(x′)² d(x′²)
```

evaluated on the tabulated x-grid and stored alongside the grid (see §5). Storing the
cumulative removes the need to integrate at every collision.

**At each collision (given photon energy E):**

```
k        = E / (hc)
x_max    = x_max(E)                      # backscatter limit, μ = −1
loop:
    ξ    = rand()
    Aξ   = ξ · A(x_max²)                 # A is monotone increasing → invertible
    x²   = invert A at Aξ                # binary search + interpolation on the A-grid
    q²   = (unit-convert x² → q²)
    μ    = 1 − q² / (2 k²)               # guaranteed in [−1, 1] since x² ≤ x_max²
    if rand() ≤ (1 + μ²) / 2:            # Thomson angular factor
        break
azi = 2π · rand()
scatter_direction(particle_container, μ, azi)   # rotate into lab frame; energy unchanged
```

Notes:
- The `A` inversion reuses the same bisection idea as
  `mcdc/transport/physics/photon/native.py::find_energy_bin` — search the cumulative grid
  for `Aξ`, then interpolate within the bin.
- Acceptance probability `(1 + μ²)/2 ∈ [0.5, 1]`, so efficiency ≥ 50% regardless of energy.
- Energy is **not** modified (elastic). Only direction changes.

**Lab-frame rotation — factor out shared code.** The Compton branch in `interface.py`
(lines 191–211) already contains the polar rotation of `(ux, uy, uz)` by `(μ, azi)`,
including the `|uz| → 1` degenerate-axis guard. Extract it into a shared `@njit` helper,
e.g. `scatter_direction(particle_container, mu, azi)`, and call it from **both** the Compton
and coherent branches. Do not copy-paste the rotation a third time.

**Rejected alternative — pure rejection on F(x)/Z.** Sample `μ` from the Thomson `(1 + μ²)`
distribution, then accept with probability `[F(x(μ)) / Z]²`. Correct but its efficiency
collapses at high energy / high Z, where `F` falls off rapidly and almost every trial is
rejected. Inverse-CDF avoids this.

---

## 5. Data-Model Changes — Carrying F(q) Through the Flat-Data Pipeline

Once §2 has put the form factor into `data/mcdc`, it must ride through the flat `float64`
buffer built in `_build_flat_data`
([mcdc/object_/photon_material.py:188-239](../mcdc/object_/photon_material.py#L188-L239)).

Current layout — **8 header sections** followed by per-element data blocks:

```
[0 .. N-1]   Z values
[N .. 2N-1]  number densities
[2N.. 3N-1]  N_points per element  (XS energy grid length)
[3N.. 4N-1]  energy_grid offsets
[4N.. 5N-1]  compton (incoherent) offsets
[5N.. 6N-1]  pe offsets
[6N.. 7N-1]  pair offsets
[7N.. 8N-1]  coherent (Rayleigh) offsets
[8N..     ]  per-element data: [E_grid | compton | pe | pair | coherent]
```

### Recommended: extend from 8 to 11 header sections

The form-factor grid length **differs** from the XS energy-grid length (e.g. Al: 1209
form-factor points vs 6682 XS points), so it needs its own count plus two offsets. Add three
sections and append the form-factor block to each element's data:

```
[8N ..  9N-1]  N_ff points per element        (form-factor grid length)
[9N .. 10N-1]  q-grid (momentum-transfer) offset
[10N.. 11N-1]  cumulative-F² table offset       (the A-grid from §4)
[11N..      ]  per-element data: [E_grid | compton | pe | pair | coherent | q_grid | cumF2]
```

- Bump the `cursor` base from `8*N` to `11*N`, and per element append `q_grid` and `cumF2`
  after `coherent`.
- **Sections 3–7 keep their indices**, so `cross_sections.py` XS lookups are untouched — the
  same reason coherent was originally appended as section 7 rather than inserted in physical
  order (see the layout comment at
  [photon_material.py:168-186](../mcdc/object_/photon_material.py#L168-L186)).
- The q-grid lookup and A-inversion reuse `native.find_energy_bin` /
  `util.log_log_interpolation` (or a linear interpolation on the A-grid — cumulative arrays
  interpolate better linearly).
- Update the module's layout doc-comment block to describe the 11-section version.

Storing `cumF2` (the cumulative `A`) directly — rather than raw `F` — means the sampler never
integrates at runtime. Store the raw q-grid alongside so `μ` can be recovered.

### Alternative (not recommended here): a dedicated distribution object

A `photon_coherent_angular_distribution` structured dtype in
`mcdc/numba_types.py`, modeled on the existing `multi_table_distribution` (which carries
grid / offset / value / pdf / cdf offsets for *energy-dependent* angular tables). This is
the right tool when the angular table varies with energy. For standard Rayleigh it is
**overkill**: `F(q)` is energy-independent — energy enters *only* through `q_max` at runtime
— so a single per-element 1-D table suffices and the flat-section extension is simpler and
cheaper. Prefer the flat extension; reach for the object only if anomalous factors
(energy-dependent `F′(E)`, `F″(E)`) are added later.

---

## 6. Loader — Reading the Form Factor Group at Build Time

Add `load_photon_element_coherent_form_factor(Z)` to
`photon_transport_code/transport/physics/photon/data_loader.py`, mirroring the existing
`load_photon_element_coherent`. It reads the `elastic/MT-502/form_factor/{momentum_transfer,
form_factor}` group written in §2, applies the §3 EPDL-x → code-q unit conversion **once**,
precomputes the cumulative `A(x²)` from §4, and returns `(q_grid, cumF2)` (plus `F` if useful
for tests). `_build_flat_data` then consumes this to fill the three new flat-data sections.

> The earlier two-stage `EPDL → data/raw → reformat_photon_data.py → data/mcdc` route is
> **superseded** by the §2 direct import and is no longer required. Keep
> `reformat_photon_data.py` only if you separately regenerate `data/mcdc` from raw; if so,
> add a matching `elastic/MT-502/form_factor` copy there too.

---

## 7. Code Touch-Points (for the implementer)

| File | Change |
|------|--------|
| `photon_transport_code/tools/add_coherent_form_factors.py` **(new)** | §2 EPDL MF=27/MT=502 parser; writes `elastic/MT-502/form_factor/*` into every `data/mcdc/*.h5`. |
| `photon_transport_code/transport/physics/photon/data_loader.py` | New `load_photon_element_coherent_form_factor(Z)`: read the group, unit-convert, precompute cumulative `A`. |
| `mcdc/object_/photon_material.py` | `_build_flat_data`: 8→11 header sections; append `[q_grid | cumF2]`; update layout comment. |
| `mcdc/transport/physics/photon/cross_sections.py` (or new `distributions.py`) | New `@njit sample_coherent_mu(E, offsets…, particle_container, data)` implementing §4. |
| `mcdc/transport/physics/photon/native.py` | Add an A-grid inversion helper if `find_energy_bin` needs a linear-interpolation twin. |
| `mcdc/transport/physics/photon/interface.py` | Replace the isotropic coherent block with the `sample_coherent_mu(...)` call + shared `scatter_direction` rotation. |
| `mcdc/object_/photon_reaction.py` | Mirror the same sampler in `PhotonReactionCoherent.perform_collision`. |

---

## 8. Validation

**After §2 (import):** confirm every `data/mcdc/*.h5` now contains
`photon_reactions/elastic/MT-502/form_factor` with `momentum_transfer` and `form_factor`
arrays of equal length and `form_factor[0] == atomic_number` (F(0) = Z). Spot-check Al
(NP = 1209, F[0] = 13) and Pb.

**After the sampler:** new unit test under `test/unit/transport/physics/photon/`:

- **F(0) = Z sanity** — form factor at the grid origin equals the atomic number (catches a
  broken loader / wrong column).
- **Forward-peaking** — the sampled `μ` histogram is significantly forward-biased vs the
  current isotropic baseline (χ² or KS test against uniform-in-μ).
- **Energy trend** — mean scattering angle **decreases** as `E` rises (higher energy → more
  forward). Increases with `Z` at fixed `E`.
- **Elastic invariant** — outgoing energy is unchanged; macroscopic attenuation totals are
  identical to the pre-change run (the sampler must not touch the cross section).
- **Reference cross-check** — a few angular points for Pb against MCNP MODE P or PENELOPE.

Run with `NUMBA_DISABLE_JIT=1` in conda env `mcdc-env`, per the existing photon-test
convention (see `validate_photon_xs.py` and the current
`test/unit/transport/physics/photon/` suite).

---

## 9. Summary — What Data Must Be Imported

Only one thing: the **atomic form factor `F(q, Z)`**, EPDL **MF=27 / MT=502**, for each
element. It is a single **energy-independent** 1-D `(x, F)` table per element (~1200 points),
present in `data/endf/epdl/EPDL.ZA0*.endf` but absent from the current HDF5 and loaded by no
current code path. **§2 imports it directly into `data/mcdc/*.h5`.** Because scope is standard
`F(q)` only, the anomalous factors (MT-505/506) and incoherent `S(q)` (MT-504) are **not**
needed. No new energy grids or per-energy angular tables are required — `q_max` is derived
from the photon energy at runtime.
