# MCNP Photon Benchmark Validation Directions

**Source document:** LA-12196 "MCNP: Photon Benchmark Problems" (Whalen, Hollowell, Hendricks, Los Alamos 1991)

This document contains ready-to-paste prompts for Claude Code — one per benchmark. Each prompt instructs Claude Code to build a `problem.py` + `compare.py` pair that you can run to see how MCDC performed against the benchmark's expected results.

---

## Benchmark Overview

| # | Status | Type | Description |
|---|--------|------|-------------|
| 1 | BLOCKED | Analytical | Infinite medium, constant XS, isotropic scatter |
| 2 | BLOCKED | Analytical | Simple spherical scatterer, constant XS |
| 3a | **READY** | Analytical | Point source in infinite Al at 1.0 MeV |
| 3b | **READY** | Analytical | Point source in infinite Al at 10.0 MeV |
| 3c | **READY** | Analytical | Point source in infinite Pb at 1.0 MeV |
| 3d | **READY** | Analytical | Point source in infinite Pb at 10.0 MeV |


**BLOCKED** = requires MCDC code additions before the benchmark can be run (see those sections for what is needed).

---

## How to Use This Document

For each READY benchmark:
1. Copy the entire section and paste it into a Claude Code conversation
2. Claude Code will create a folder under `photon_transport_code/examples/` with `problem.py` and `compare.py`
3. Run `python problem.py` to simulate, then `python compare.py` to see results vs expected values

---

---

## BENCHMARK 1 — Infinite Medium, Constant Cross Section, Isotropic Scattering

**STATUS: BLOCKED** — Requires adding constant-cross-section physics to MCDC.

**Reference:** Case, de Hoffman, Placzek (1953), *Introduction to the Theory of Neutron Diffusion*, Vol. 1, Tables 17 and 18.

### What it tests
A point isotropic source in an infinite homogeneous medium where photons undergo only isotropic scattering or absorption, with cross sections that are constant for all energies. Three sub-cases:
- **1a** Pure absorption: σ_abs = σ_tot, σ_scat = 0 → flux = e^(-μr)
- **1b** 30% scattering: σ_scat = 0.3 σ_tot, σ_abs = 0.7 σ_tot
- **1c** 90% scattering: σ_scat = 0.9 σ_tot, σ_abs = 0.1 σ_tot

Particle current is measured at spherical surfaces at distances 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 25.0 MFP from the source. (1 MFP = 1 cm; σ_tot = 1 barn; atom density chosen so σ_tot × n = 1 cm⁻¹.)

### What MCDC needs before this can run
MCDC currently only supports real material cross-sections (Compton, PE, PP from NIST data). This benchmark requires:
1. A `ConstantCrossSectionMaterial` that accepts user-specified σ_total and σ_absorption (both energy-independent)
2. The physics must restrict photon interactions to "pure absorption" or "isotropic scatter with no energy change"

This would be a new material type and new collision physics branch in `mcdc/transport/physics/photon/interface.py`.

---

---

## BENCHMARK 2 — Simple Spherical Scatterer

**STATUS: BLOCKED** — Requires same constant-cross-section physics as Benchmark 1.

**Reference:** Lent and Wilcox (LLNL), point-detector flux formula.

### What it tests
A point isotropic source at the center of a 1 cm sphere of scattering/absorbing material (σ_scat = 0.3 σ_tot, σ_abs = 0.7 σ_tot, 1 MFP = 1 cm). The uncollided flux and first-collided flux are computed at 10 points from 1.5 to 10 cm outside the sphere.

The once-scattered flux at distance a from the sphere center has an analytical formula:
```
Φ₁(a) = 0.3 × ∫∫ [e^(-t) / (4π r²)] × [e^(-ℓ) / (4π ℓ²)] × 4π r² dr dμ
```
where r is the integration radius inside the sphere (0 to 1 cm), ℓ is the distance from the scattering point to the observation point, and t is the distance from the center to the scattering point.

### What MCDC needs before this can run
Same as Benchmark 1 — requires constant-cross-section physics.

---

---

## BENCHMARK 3a — Point Source in Infinite Aluminum at 1.0 MeV

**STATUS: READY**

**Reference:** H. Goldstein and J. E. Wilkins (1954), *Calculations of the Penetration of Gamma Rays*, NYO-3075, Tables pp. 90-93.

---

**Paste this entire section to Claude Code:**

---

Build two files for MCNP Benchmark 3a (point gamma source in infinite aluminum at 1.0 MeV).

**Working directory:** `c:\Projects\MCDC`
**Files to create:**
- `photon_transport_code/examples/benchmark_3a_al_1mev/problem.py`
- `photon_transport_code/examples/benchmark_3a_al_1mev/compare.py`

---

### Physics

Photon physics is restricted to (this is already MCDC's default behavior):
- Compton scattering (no coherent/Thomson scatter, no form factors)
- Photoelectric absorption (pure absorption — no secondary photons from electrons)
- Pair production (pure absorption — no annihilation photons)
- No coherent scattering
- No electron transport

### Material

**Aluminum** at standard density:
- Element: Z = 13
- Atom density: n = 0.06026 atoms/barn·cm  (from ρ = 2.699 g/cm³, A = 26.982 g/mol)
- MCDC call: `mcdc.PhotonMaterial(elements=[13], densities=[0.06026], name="aluminum")`

**Cross-sections at 1.0 MeV** (from MCNP MCPLIB library — matches NIST XCOM):
- σ_Compton = 2.74582 barn/atom
- σ_pair = 0.00100 barn/atom
- σ_PE = 0.0 barn/atom
- σ_total = 2.74682 barn/atom

**1 MFP at 1.0 MeV** = 1 / (σ_total × n) = 1 / (2.74682 × 0.06026) = **6.044 cm**

### Geometry

5-shell concentric sphere geometry centered at origin, all filled with aluminum:

| Shell | Inner radius (cm) | Outer radius (cm) | Boundary |
|-------|------------------|------------------|----------|
| Cell 0 (core) | 0 | 6.044 (1 MFP) | none |
| Cell 1 | 6.044 | 12.088 (2 MFP) | none |
| Cell 2 | 12.088 | 24.176 (4 MFP) | none |
| Cell 3 | 24.176 | 42.308 (7 MFP) | none |
| Cell 4 | 42.308 | 120.880 (20 MFP) | none |
| Outer boundary | — | 120.880 | vacuum |

```python
MFP = 6.044  # cm

s1  = mcdc.Surface.Sphere(center=[0,0,0], radius=1*MFP)
s2  = mcdc.Surface.Sphere(center=[0,0,0], radius=2*MFP)
s4  = mcdc.Surface.Sphere(center=[0,0,0], radius=4*MFP)
s7  = mcdc.Surface.Sphere(center=[0,0,0], radius=7*MFP)
s20 = mcdc.Surface.Sphere(center=[0,0,0], radius=20*MFP, boundary_condition="vacuum")

c0 = mcdc.Cell(region=-s1,         fill=al)
c1 = mcdc.Cell(region=+s1 & -s2,   fill=al)
c2 = mcdc.Cell(region=+s2 & -s4,   fill=al)
c3 = mcdc.Cell(region=+s4 & -s7,   fill=al)
c4 = mcdc.Cell(region=+s7 & -s20,  fill=al)
```

### Source

Isotropic point source at the origin. Energy = 1.0 MeV. Particle type = photon.

```python
mcdc.Source(position=[0.0, 0.0, 0.0], energy=1.0, particle_type="photon")
```

### Tallies

Surface flux tallies on each of the 4 inner spheres (one tally per sphere):

```python
mcdc.Tally(surface=s1, scores=["flux"], name="flux_1mfp")
mcdc.Tally(surface=s2, scores=["flux"], name="flux_2mfp")
mcdc.Tally(surface=s4, scores=["flux"], name="flux_4mfp")
mcdc.Tally(surface=s7, scores=["flux"], name="flux_7mfp")
```

### Settings

```python
mcdc.settings.N_particle = 200000
mcdc.settings.N_batch    = 100
mcdc.settings.rng_seed   = 12345
mcdc.settings.output_name = "benchmark_3a"
```

### Expected Results (from Goldstein & Wilkins 1954)

**Energy Buildup Factor Be** at each distance:

| Distance | Analytic Be | MCNP Be ± σ |
|----------|-------------|-------------|
| 1 MFP | 2.01 | 2.018 ± 0.020 |
| 2 MFP | 3.29 | 3.307 ± 0.059 |
| 4 MFP | 6.52 | 6.648 ± 0.254 |
| 7 MFP | 12.95 | 12.622 ± 0.936 |

### compare.py Instructions

The compare.py script must:
1. Read `benchmark_3a.h5`
2. For each tally (flux_1mfp, flux_2mfp, flux_4mfp, flux_7mfp):
   - Read `flux/mean` and `flux/sdev` from `tallies/{name}/`
   - The tally value is the particle flux in units of **particles/cm²/source_particle** averaged over the sphere surface
   - Compute total particle crossing: `crossing = flux_mean × 4π r²`
   - Compute uncollided crossing (analytical): `uncollided = exp(-r / MFP_CM)`
   - Compute particle buildup factor: `Bf = crossing / uncollided`
   - Compute 1σ uncertainty: `Bf_sdev = (flux_sdev × 4π r²) / uncollided`
3. Print a comparison table:
   ```
   Distance | Be_analytic | Be_MCNP | Bf_MCDC | ±1σ | Bf > Be?
   ```
4. Print PASS if Bf > Be at all 4 distances (Bf ≥ Be is a necessary condition when physics is correct, because scattered photons have less energy than source photons, so more particles are needed to carry the same energy)
5. Print FAIL with explanation if any Bf < Be

**Physical constants for compare.py:**
```python
MFP_CM = 6.044
MU     = 1.0 / MFP_CM   # attenuation coefficient in cm⁻¹
import math
# Uncollided crossing at distance r: math.exp(-MU * r)
# Sphere area at radius r: 4 * math.pi * r**2
```

**Expected Be values (hardcode in compare.py):**
```python
EXPECTED_Be = {1: 2.01, 2: 3.29, 4: 6.52, 7: 12.95}
EXPECTED_MCNP_Be = {1: 2.018, 2: 3.307, 4: 6.648, 7: 12.622}
MFP_DISTANCES = [1, 2, 4, 7]  # MFP integers
```

---

---

## BENCHMARK 3b — Point Source in Infinite Aluminum at 10.0 MeV

**STATUS: READY**

**Reference:** Goldstein & Wilkins (1954), NYO-3075, pp. 106-109.

---

**Paste this entire section to Claude Code:**

---

Build two files for MCNP Benchmark 3b (point gamma source in infinite aluminum at 10.0 MeV).

**Working directory:** `c:\Projects\MCDC`
**Files to create:**
- `photon_transport_code/examples/benchmark_3b_al_10mev/problem.py`
- `photon_transport_code/examples/benchmark_3b_al_10mev/compare.py`

---

### Physics (same as Benchmark 3a)
Compton + PE absorption + PP absorption, no coherent scatter, no electron transport.

### Material

Same aluminum as 3a (Z=13, n=0.06026 atoms/barn·cm).

**Cross-sections at 10.0 MeV:**
- σ_Compton = 0.66495 barn/atom
- σ_pair = 0.00004 barn/atom (negligible)
- σ_PE = 0.37344 barn/atom
- σ_total = 1.03843 barn/atom

**1 MFP at 10.0 MeV** = 1 / (1.03843 × 0.06026) = **15.986 cm**

### Geometry

5-shell concentric sphere geometry. MFP = 15.986 cm.

| Shell | Inner radius (cm) | Outer radius (cm) | Boundary |
|-------|------------------|------------------|----------|
| Cell 0 | 0 | 15.986 (1 MFP) | none |
| Cell 1 | 15.986 | 31.972 (2 MFP) | none |
| Cell 2 | 31.972 | 63.944 (4 MFP) | none |
| Cell 3 | 63.944 | 111.902 (7 MFP) | none |
| Cell 4 | 111.902 | 319.720 (20 MFP) | vacuum |

```python
MFP = 15.986  # cm
```

Source, tally setup, and settings are identical to Benchmark 3a except:
- `energy=10.0` in `mcdc.Source`
- `output_name = "benchmark_3b"`
- Tally names: `"flux_1mfp"`, `"flux_2mfp"`, `"flux_4mfp"`, `"flux_7mfp"`

### Expected Results (Goldstein & Wilkins 1954)

| Distance | Analytic Be | MCNP Be ± σ |
|----------|-------------|-------------|
| 1 MFP | 1.22 | 1.227 ± 0.013 |
| 2 MFP | 1.45 | 1.460 ± 0.029 |
| 4 MFP | 1.91 | 1.944 ± 0.081 |
| 7 MFP | 2.64 | 2.793 ± 0.201 |

### compare.py Instructions

Same logic as Benchmark 3a, with:
```python
MFP_CM = 15.986
EXPECTED_Be = {1: 1.22, 2: 1.45, 4: 1.91, 7: 2.64}
EXPECTED_MCNP_Be = {1: 1.227, 2: 1.460, 4: 1.944, 7: 2.793}
```

Pass criterion: Bf > Be at all 4 distances. Print PASS or FAIL with the comparison table.

---

---

## BENCHMARK 3c — Point Source in Infinite Lead at 1.0 MeV

**STATUS: READY**

**Reference:** Goldstein & Wilkins (1954), NYO-3075, p. 136.

---

**Paste this entire section to Claude Code:**

---

Build two files for MCNP Benchmark 3c (point gamma source in infinite lead at 1.0 MeV).

**Working directory:** `c:\Projects\MCDC`
**Files to create:**
- `photon_transport_code/examples/benchmark_3c_pb_1mev/problem.py`
- `photon_transport_code/examples/benchmark_3c_pb_1mev/compare.py`

---

### Physics (same as Benchmark 3a)
Compton + PE absorption + PP absorption, no coherent scatter, no electron transport.

### Material

**Lead:**
- Element: Z = 82
- Atom density: n = 0.03297 atoms/barn·cm  (from ρ = 11.35 g/cm³, A = 207.2 g/mol)
- MCDC call: `mcdc.PhotonMaterial(elements=[82], densities=[0.03297], name="lead")`

**Cross-sections at 1.0 MeV:**
- σ_Compton = 17.18180 barn/atom
- σ_pair = 6.02800 barn/atom
- σ_PE = 0.0 barn/atom
- σ_total = 23.20980 barn/atom

**1 MFP at 1.0 MeV** = 1 / (23.20980 × 0.03297) = **1.306 cm**

### Geometry

5-shell concentric sphere geometry. MFP = 1.306 cm.

| Shell | Inner radius (cm) | Outer radius (cm) | Boundary |
|-------|------------------|------------------|----------|
| Cell 0 | 0 | 1.306 (1 MFP) | none |
| Cell 1 | 1.306 | 2.612 (2 MFP) | none |
| Cell 2 | 2.612 | 5.224 (4 MFP) | none |
| Cell 3 | 5.224 | 9.142 (7 MFP) | none |
| Cell 4 | 9.142 | 26.120 (20 MFP) | vacuum |

```python
MFP = 1.306  # cm
```

Source energy = 1.0 MeV. Output name = `"benchmark_3c"`. All other settings same as 3a.

### Expected Results (Goldstein & Wilkins 1954)

| Distance | Analytic Be | MCNP Be ± σ |
|----------|-------------|-------------|
| 1 MFP | 1.35 | 1.361 ± 0.006 |
| 2 MFP | 1.66 | 1.650 ± 0.013 |
| 4 MFP | 2.21 | 2.186 ± 0.028 |
| 7 MFP | 2.95 | 2.901 ± 0.058 |

### compare.py Instructions

Same logic as 3a with:
```python
MFP_CM = 1.306
EXPECTED_Be = {1: 1.35, 2: 1.66, 4: 2.21, 7: 2.95}
EXPECTED_MCNP_Be = {1: 1.361, 2: 1.650, 4: 2.186, 7: 2.901}
```

Pass criterion: Bf > Be at all 4 distances.

---

---

## BENCHMARK 3d — Point Source in Infinite Lead at 10.0 MeV

**STATUS: READY**

**Reference:** Goldstein & Wilkins (1954), NYO-3075, p. 140.

---

**Paste this entire section to Claude Code:**

---

Build two files for MCNP Benchmark 3d (point gamma source in infinite lead at 10.0 MeV).

**Working directory:** `c:\Projects\MCDC`
**Files to create:**
- `photon_transport_code/examples/benchmark_3d_pb_10mev/problem.py`
- `photon_transport_code/examples/benchmark_3d_pb_10mev/compare.py`

---

### Physics (same as Benchmark 3a)
Compton + PE absorption + PP absorption, no coherent scatter, no electron transport.

### Material

Same lead as 3c (Z=82, n=0.03297 atoms/barn·cm).

**Cross-sections at 10.0 MeV:**
- σ_Compton = 4.19291 barn/atom
- σ_pair = 0.16809 barn/atom
- σ_PE = 12.40100 barn/atom
- σ_total = 16.76200 barn/atom

**1 MFP at 10.0 MeV** = 1 / (16.76200 × 0.03297) = **1.809 cm**

### Geometry

5-shell concentric sphere geometry. MFP = 1.809 cm.

| Shell | Inner radius (cm) | Outer radius (cm) | Boundary |
|-------|------------------|------------------|----------|
| Cell 0 | 0 | 1.809 (1 MFP) | none |
| Cell 1 | 1.809 | 3.618 (2 MFP) | none |
| Cell 2 | 3.618 | 7.236 (4 MFP) | none |
| Cell 3 | 7.236 | 12.663 (7 MFP) | none |
| Cell 4 | 12.663 | 36.180 (20 MFP) | vacuum |

```python
MFP = 1.809  # cm
```

Source energy = 10.0 MeV. Output name = `"benchmark_3d"`. All other settings same as 3a.

### Expected Results (Goldstein & Wilkins 1954)

| Distance | Analytic Be | MCNP Be ± σ |
|----------|-------------|-------------|
| 1 MFP | 1.09 | 1.089 ± 0.0062 |
| 2 MFP | 1.19 | 1.192 ± 0.0096 |
| 4 MFP | 1.46 | 1.478 ± 0.0179 |
| 7 MFP | 2.16 | 2.255 ± 0.0438 |

### compare.py Instructions

Same logic as 3a with:
```python
MFP_CM = 1.809
EXPECTED_Be = {1: 1.09, 2: 1.19, 4: 1.46, 7: 2.16}
EXPECTED_MCNP_Be = {1: 1.089, 2: 1.192, 4: 1.478, 7: 2.255}
```

Pass criterion: Bf > Be at all 4 distances.

---

## Reference: Particle Buildup Factor Formula

For all Benchmark 3 compare.py scripts, the comparison formula is:

```python
import math, h5py

def compute_buildup_factor(h5_file, tally_name, radius_cm, mfp_cm, N_particle):
    """
    Compute particle flux buildup factor Bf from MCDC surface flux tally.

    Bf = total_particle_crossing / uncollided_particle_crossing
       = (flux_mean * 4*pi*r^2) / exp(-r/MFP)

    Returns: (Bf, Bf_1sigma_uncertainty)
    
    Note: Bf >= Be (energy buildup factor) always.
    If Bf < Be, the code has a physics bug.
    """
    mu = 1.0 / mfp_cm
    with h5py.File(h5_file, "r") as f:
        flux_mean = float(f[f"tallies/{tally_name}/flux/mean"][()])
        flux_sdev = float(f[f"tallies/{tally_name}/flux/sdev"][()])
    
    area = 4.0 * math.pi * radius_cm**2
    uncollided = math.exp(-mu * radius_cm)
    
    Bf = (flux_mean * area) / uncollided
    Bf_sdev = (flux_sdev * area) / uncollided
    return Bf, Bf_sdev
```

**Why Bf ≥ Be:**  
- Be = (total energy flux) / (uncollided energy flux)  
- Bf = (total particle flux) / (uncollided particle flux)  
- Scattered photons have lower energy than source energy (Compton degrades energy)  
- So: total_energy_flux < total_particle_flux × E_source  
- Therefore: Be < Bf  
- If MCDC returns Bf < Be: scattered photons aren't reaching the tally sphere → physics bug
