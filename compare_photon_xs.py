#!/usr/bin/env python3
"""
Compare MC/DC photon cross sections (EPICS/EPDL -> MCDC-format HDF5, data/mcdc/)
against MCNP mcplib84 (ACE photoatomic tables, ESZG block).

Percent difference convention:  100 * (MCDC - MCNP) / MCNP

Step 1  element-by-element check over every Z present in both libraries
Step 2  material comparison (mass attenuation coefficient mu/rho and
        macroscopic cross section Sigma) for Pb, Al, Fe, water, concrete, air,
        using the exact compositions from the MCNP verification benchmarks.

Usage
-----
python compare_photon_xs.py [--mcdc-dir data/mcdc] [--ace <mcplib84 file>]
                            [--out xs_compare]
"""

import argparse
from pathlib import Path

import h5py
import numpy as np

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
M_NEUTRON_AMU = 1.00866491595  # AWR -> amu, MCNP convention
N_A = 6.02214076e23
EDGE_WINDOW = 0.01  # exclude +/-1% around absorption edges in "clean" stats
E_MIN_MEV, E_MAX_MEV = 1.0e-3, 1.0e5  # mcplib84 grid spans 1 keV - 100 GeV
REPORT_E = [0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]  # MeV, point values
BENCH_BAND = (1.0, 10.0)  # MeV, benchmark source range
PAIR_CLEAN_EMIN = 1.2  # MeV; pair xs just above threshold is ~0 and its
#                        % diff is dominated by threshold-grid placement

REACTIONS = ["incoherent", "coherent", "photoelectric", "pair", "total"]

# MCDC HDF5 dataset paths -- VERIFIED against data/mcdc/*.h5 (2026-09-30).
# Energy grid is in eV; cross sections in barns.
MCDC_PATHS = {
    "energy": "photon_reactions/xs_energy_grid",
    "coherent": "photon_reactions/elastic/MT-502/xs",
    "incoherent": "photon_reactions/incoherent_scattering/MT-504/xs",
    "photoelectric": "photon_reactions/photoelectric_absorption/MT-501/xs",
    "pair": "photon_reactions/pair_production/MT-503/xs",
    "pair_nuc": "photon_reactions/pair_production/MT-503/nuclear_field/xs",
    "pair_ele": "photon_reactions/pair_production/MT-503/electron_field/xs",
    "total_file": "photon_reactions/total/MT-401/xs",
}

SYMBOLS = ("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni "
           "Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I "
           "Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt "
           "Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm").split()

# --------------------------------------------------------------------------
# Material compositions -- taken verbatim from the MC/DC verification decks:
#   Complex_M&G/multi_material_slabs_mesh_tally.py  (Pb, water, concrete, air)
#   Complex_M&G/multi_material_spheres.py           (Fe)
#   benchmark_3a_al_1mev/problem.py                 (Al)
# Weight fractions are stored as given (NOT renormalized), together with the
# bulk density, so the resulting number densities reproduce exactly what
# mcdc.PhotonMaterial receives.  _A matches the deck's own atomic-weight table.
# --------------------------------------------------------------------------
DECK_A = {1: 1.008, 7: 14.007, 8: 15.999, 11: 22.990, 12: 24.305, 13: 26.982,
          14: 28.085, 18: 39.948, 20: 40.078, 26: 55.845, 82: 207.200}

BENCH_MATERIALS = {
    # name: (rho_g_cm3, {Z: weight_fraction})
    "Pb":       (11.34,   {82: 1.0}),
    "Al":       (2.69964, {13: 1.0}),   # 0.06026 at/b-cm with A=26.982
    "Fe":       (7.874,   {26: 1.0}),
    "water":    (1.0,     {1: 0.111898, 8: 0.888102}),
    "concrete": (2.3,     {8: 0.529107, 11: 0.016, 12: 0.002, 13: 0.033872,
                           14: 0.337021, 20: 0.044, 26: 0.014, 1: 0.010}),
    "air":      (0.00129, {7: 0.7818, 8: 0.2097, 18: 0.0085}),
}

# NIST XAAMDI/XCOM reference total mu/rho [cm^2/g] for an independent physical
# sanity check (total WITH coherent scattering).
NIST_REF = {
    "Pb":    {0.1: 5.549, 1.0: 0.07102, 10.0: 0.04972},
    "Al":    {0.1: 0.1704, 1.0: 0.06146, 10.0: 0.02318},
    "Fe":    {0.1: 0.3717, 1.0: 0.05995, 10.0: 0.02994},
    "water": {0.1: 0.1707, 1.0: 0.07072, 10.0: 0.02219},
    "air":   {0.1: 0.1541, 1.0: 0.06358, 10.0: 0.02045},
}


# --------------------------------------------------------------------------
# Readers
# --------------------------------------------------------------------------
def read_mcplib(ace_path):
    """Parse every photoatomic table in an ASCII ACE library (legacy header).

    ESZG block (NES values each): ln(E[MeV]), ln(sig_incoh), ln(sig_coh),
    ln(sig_pe), ln(sig_pair).  A stored 0.0 means sigma = 0 (OpenMC convention).
    """
    lines = Path(ace_path).read_text().splitlines()
    out, i = {}, 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        tok = lines[i].split()
        if tok[0].startswith("2.0"):  # ACE 2.0.x header
            zaid = tok[1]
            awr = float(lines[i + 1].split()[0])
            n_comment = int(lines[i + 1].split()[3])
            i += 2 + n_comment
        else:  # legacy header: ZAID line + comment line
            zaid, awr = tok[0], float(tok[1])
            i += 2
        izaw = i
        nxs = [int(x) for x in " ".join(lines[izaw + 4: izaw + 6]).split()]
        jxs = [int(x) for x in " ".join(lines[izaw + 6: izaw + 10]).split()]
        i = izaw + 10
        n_lines = -(-nxs[0] // 4)
        if not zaid.endswith("p"):  # not photoatomic
            i += n_lines
            continue
        xss = np.array(" ".join(lines[i: i + n_lines]).split(), dtype=float)
        i += n_lines

        Z = int(zaid.split(".")[0]) // 1000
        nes, s = nxs[2], jxs[0] - 1
        blk = xss[s: s + 5 * nes].reshape(5, nes)

        def unlog(a):
            a = a.copy()
            nz = a != 0.0
            a[nz] = np.exp(a[nz])
            return a

        out[Z] = dict(zaid=zaid, awr=awr, energy=np.exp(blk[0]),
                      incoherent=unlog(blk[1]), coherent=unlog(blk[2]),
                      photoelectric=unlog(blk[3]), pair=unlog(blk[4]))
    return out


def read_mcdc(mcdc_dir, pair_mode="total"):
    """Read every <Symbol>.h5 MCDC photon file.  Energy converted eV -> MeV.

    pair_mode: 'total'   -> MT-503/xs            (nuclear + electron field)
               'nuclear' -> nuclear_field/xs only
    """
    out = {}
    for Z, sym in enumerate(SYMBOLS, start=1):
        f = Path(mcdc_dir) / f"{sym}.h5"
        if not f.exists():
            continue
        with h5py.File(f, "r") as h:
            d = {"energy": h[MCDC_PATHS["energy"]][()] * 1.0e-6,
                 "awr": float(h["atomic_weight_ratio"][()])}
            for r in ("coherent", "incoherent", "photoelectric"):
                d[r] = h[MCDC_PATHS[r]][()]
            if pair_mode == "nuclear":
                d["pair"] = h[MCDC_PATHS["pair_nuc"]][()]
            else:
                d["pair"] = h[MCDC_PATHS["pair"]][()]
                if not np.any(d["pair"] > 0):
                    alt = (h[MCDC_PATHS["pair_nuc"]][()]
                           + h[MCDC_PATHS["pair_ele"]][()])
                    if np.any(alt > 0):
                        print(f"  WARNING {sym}: MT-503/xs all zero; using "
                              f"nuclear + electron components")
                        d["pair"] = alt
            d["total_file"] = h[MCDC_PATHS["total_file"]][()]
        out[Z] = d
    return out


# --------------------------------------------------------------------------
# Interpolation / edge handling
# --------------------------------------------------------------------------
def loglog_interp(x, xp, fp):
    """Log-log interpolation (ENDF INT=5); lin-lin across intervals touching a
    zero.  Duplicate xp (absorption edges) resolve to the upper side."""
    x = np.atleast_1d(np.asarray(x, dtype=float))
    xp, fp = np.asarray(xp, dtype=float), np.asarray(fp, dtype=float)
    j = np.clip(np.searchsorted(xp, x, side="right"), 1, len(xp) - 1)
    x0, x1, f0, f1 = xp[j - 1], xp[j], fp[j - 1], fp[j]
    out = np.empty_like(x)
    pos = (f0 > 0) & (f1 > 0) & (x1 > x0) & (x > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.log(x[pos] / x0[pos]) / np.log(x1[pos] / x0[pos])
        out[pos] = np.exp(np.log(f0[pos]) + t * np.log(f1[pos] / f0[pos]))
    lin = ~pos
    dx = np.where(x1[lin] > x0[lin], x1[lin] - x0[lin], 1.0)
    out[lin] = f0[lin] + (x[lin] - x0[lin]) * (f1[lin] - f0[lin]) / dx
    out[(x < xp[0]) | (x > xp[-1])] = np.nan
    return out


def find_edges(E, pe):
    """Absorption edges: duplicated grid points, or photoelectric jumping up."""
    dup = E[1:][np.isclose(E[1:], E[:-1], rtol=1e-10)]
    with np.errstate(divide="ignore", invalid="ignore"):
        jump = E[1:][(pe[1:] > 1.05 * pe[:-1]) & (pe[:-1] > 0)]
    return np.unique(np.concatenate([dup, jump]))


def edge_mask(E, edges, window=EDGE_WINDOW):
    keep = np.ones_like(E, dtype=bool)
    for e in edges:
        if e > 0:
            keep &= np.abs(E / e - 1.0) > window
    return keep


def eval_grid(*grids):
    """Union of all grids, clipped to the common overlap and the library range."""
    lo = max(E_MIN_MEV, *(g[0] for g in grids))
    hi = min(E_MAX_MEV, *(g[-1] for g in grids))
    E = np.unique(np.concatenate(grids))
    return E[(E >= lo) & (E <= hi)]


def element_on_grid(lib, E):
    d = {r: loglog_interp(E, lib["energy"], lib[r]) for r in REACTIONS[:-1]}
    d["total"] = sum(np.nan_to_num(d[r]) for r in REACTIONS[:-1])
    return d


def pct(a, b, E=None, reaction=None):
    a, b = np.atleast_1d(a), np.atleast_1d(b)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = 100.0 * (a - b) / b
    p = np.where(np.isfinite(p) & (b > 0) & (a > 0), p, np.nan)
    if reaction == "pair" and E is not None:
        p = np.where(np.atleast_1d(E) < PAIR_CLEAN_EMIN, np.nan, p)
    return p


def nanmaxabs(q):
    return np.nanmax(np.abs(q)) if np.any(np.isfinite(q)) else np.nan


def nanmean(q):
    return np.nanmean(q) if np.any(np.isfinite(q)) else np.nan


# --------------------------------------------------------------------------
# Comparisons
# --------------------------------------------------------------------------
def compare_elements(mcdc, mcnp, tol=1.0e-3):
    rows = []
    for Z in sorted(set(mcdc) & set(mcnp)):
        a, b = mcdc[Z], mcnp[Z]
        E = eval_grid(a["energy"], b["energy"])
        xa, xb = element_on_grid(a, E), element_on_grid(b, E)
        keep = edge_mask(E, np.concatenate([
            find_edges(a["energy"], a["photoelectric"]),
            find_edges(b["energy"], b["photoelectric"])]))
        band = (E >= BENCH_BAND[0]) & (E <= BENCH_BAND[1])
        row = {"Z": Z, "sym": SYMBOLS[Z - 1], "identical": True}
        for r in REACTIONS:
            p = pct(xa[r], xb[r], E, r)
            row[f"{r}_max_all"] = nanmaxabs(p)
            row[f"{r}_max_clean"] = nanmaxabs(p[keep])
            row[f"{r}_max_band"] = nanmaxabs(p[band])
            m = row[f"{r}_max_clean"]
            if np.isfinite(m) and m >= tol:
                row["identical"] = False
        rows.append(row)
    return rows


def material_xs(rho, wfrac, libs_on_grid, awr):
    """Returns (mu_rho[cm^2/g] per reaction, Sigma[1/cm] per reaction, n_per_g).

    Atomic masses come from the MCNP AWR for BOTH libraries so the percent
    difference reflects only the cross sections, never the mass data.
    Weight fractions are used as written (not renormalized), matching the deck.
    """
    Zs = list(wfrac)
    A = np.array([awr[Z] * M_NEUTRON_AMU for Z in Zs])
    w = np.array([wfrac[Z] for Z in Zs])
    n_per_g = w / A * N_A * 1.0e-24  # atoms/barn per gram
    mu = {r: sum(n * libs_on_grid[Z][r] for n, Z in zip(n_per_g, Zs))
          for r in REACTIONS}
    sig = {r: mu[r] * rho for r in REACTIONS}
    return mu, sig, n_per_g


def compare_material(name, rho, wfrac, mcdc, mcnp, outdir):
    Zs = list(wfrac)
    missing = [Z for Z in Zs if Z not in mcdc or Z not in mcnp]
    if missing:
        raise KeyError(f"{name}: Z={missing} missing from one library")
    E = eval_grid(*[mcdc[Z]["energy"] for Z in Zs],
                  *[mcnp[Z]["energy"] for Z in Zs])
    edges = np.concatenate([find_edges(lib[Z]["energy"], lib[Z]["photoelectric"])
                            for Z in Zs for lib in (mcdc, mcnp)])
    keep = edge_mask(E, edges)
    awr = {Z: mcnp[Z]["awr"] for Z in Zs}
    mu_a, sig_a, _ = material_xs(rho, wfrac, {Z: element_on_grid(mcdc[Z], E) for Z in Zs}, awr)
    mu_b, sig_b, _ = material_xs(rho, wfrac, {Z: element_on_grid(mcnp[Z], E) for Z in Zs}, awr)
    p = {r: pct(mu_a[r], mu_b[r], E, r) for r in REACTIONS}

    cols, hdr = [E], ["E_MeV"]
    for r in REACTIONS:
        cols += [mu_a[r], mu_b[r], p[r]]
        hdr += [f"{r}_MCDC_cm2g", f"{r}_MCNP_cm2g", f"{r}_pctdiff"]
    cols += [sig_a["total"], sig_b["total"], keep.astype(float)]
    hdr += ["total_MCDC_Sigma_percm", "total_MCNP_Sigma_percm", "away_from_edge"]
    np.savetxt(outdir / f"{name}_xs_compare.csv", np.column_stack(cols),
               delimiter=",", header=",".join(hdr), comments="", fmt="%.8e")

    band = (E >= BENCH_BAND[0]) & (E <= BENCH_BAND[1])
    Ep = np.array(REPORT_E, float)
    s = {"E": E, "pct": p, "keep": keep, "rho": rho,
         "mu_mcdc": mu_a, "mu_mcnp": mu_b, "sig_mcdc": sig_a, "sig_mcnp": sig_b}
    for r in REACTIONS:
        q = p[r]
        s[(r, "max_clean")] = nanmaxabs(q[keep])
        s[(r, "mean_clean")] = nanmean(q[keep])
        s[(r, "max_band")] = nanmaxabs(q[band])
        s[(r, "mean_band")] = nanmean(q[band])
        ea = loglog_interp(Ep, E, mu_a[r])
        eb = loglog_interp(Ep, E, mu_b[r])
        s[(r, "points")] = pct(ea, eb, Ep, r)
        s[(r, "mu_a_pts")] = ea
        s[(r, "mu_b_pts")] = eb
    return s


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcdc-dir", default="data/mcdc")
    ap.add_argument("--ace", default="data/mcplib84/mcplib84/mcplib84/mcplib84")
    ap.add_argument("--out", default="xs_compare")
    ap.add_argument("--pair-mode", default="total", choices=["total", "nuclear"])
    ap.add_argument("--skip-elements", action="store_true")
    args = ap.parse_args()
    outdir = Path(args.out)
    outdir.mkdir(exist_ok=True)

    print("Reading mcplib84 ...")
    mcnp = read_mcplib(args.ace)
    print(f"  {len(mcnp)} photoatomic tables, Z = {min(mcnp)}..{max(mcnp)}")
    print("Reading MCDC HDF5 ...")
    mcdc = read_mcdc(args.mcdc_dir, pair_mode=args.pair_mode)
    print(f"  {len(mcdc)} element files, Z = {min(mcdc)}..{max(mcdc)}")

    # ---- Sanity: MCDC AWR vs MCNP AWR -------------------------------------
    dmax = max(abs(mcdc[Z]["awr"] - mcnp[Z]["awr"]) / mcnp[Z]["awr"]
               for Z in set(mcdc) & set(mcnp))
    print(f"  max |AWR_MCDC - AWR_MCNP|/AWR = {dmax*100:.3f} %")

    # ---- Sanity: internal consistency of each library's total -------------
    for Z in (1, 13, 26, 82):
        if Z in mcdc:
            E = mcdc[Z]["energy"]
            tot = sum(mcdc[Z][r] for r in REACTIONS[:-1])
            d = np.abs(tot - mcdc[Z]["total_file"]) / np.maximum(mcdc[Z]["total_file"], 1e-30)
            m = (E >= 1e-3) & (E <= 1e5)
            print(f"  MCDC {SYMBOLS[Z-1]:>2s}: max |sum(partials)-MT401|/MT401 "
                  f"= {np.nanmax(d[m])*100:.3f} %")

    # ---- Step 1: every element --------------------------------------------
    if not args.skip_elements:
        rows = compare_elements(mcdc, mcnp)
        n_same = sum(r["identical"] for r in rows)
        print(f"\n=== Element check: {n_same}/{len(rows)} elements identical to "
              f"1e-3 % (edges +/-{EDGE_WINDOW*100:.0f}% excluded) ===")
        print("Z   sym " + " ".join(f"{r[:6]:>9s}" for r in REACTIONS)
              + "   max |%diff| (edges excl., full range)")
        with open(outdir / "all_elements_summary.csv", "w") as fh:
            fh.write("Z,sym," + ",".join(
                f"{r}_max_clean,{r}_max_band,{r}_max_all" for r in REACTIONS)
                + ",identical\n")
            for r in rows:
                print(f"{r['Z']:<3d} {r['sym']:<3s} " +
                      " ".join(f"{r[f'{x}_max_clean']:9.3f}" for x in REACTIONS))
                fh.write(f"{r['Z']},{r['sym']}," + ",".join(
                    f"{r[f'{x}_max_clean']:.6g},{r[f'{x}_max_band']:.6g},"
                    f"{r[f'{x}_max_all']:.6g}" for x in REACTIONS)
                    + f",{r['identical']}\n")
        # Worst offenders in the benchmark band
        print("\nWorst 10 elements by total max|%diff| in 1-10 MeV:")
        for r in sorted(rows, key=lambda d: -(d["total_max_band"]
                        if np.isfinite(d["total_max_band"]) else -1))[:10]:
            print(f"  Z={r['Z']:<3d} {r['sym']:<3s} total {r['total_max_band']:7.3f} %  "
                  f"(inc {r['incoherent_max_band']:6.3f}, coh {r['coherent_max_band']:7.3f}, "
                  f"pe {r['photoelectric_max_band']:7.3f}, pair {r['pair_max_band']:6.3f})")

    # ---- Step 2: the six benchmark materials ------------------------------
    results = {}
    for name, (rho, wf) in BENCH_MATERIALS.items():
        results[name] = compare_material(name, rho, wf, mcdc, mcnp, outdir)

    print("\n\n=== Physical sanity check: total mu/rho [cm^2/g] vs NIST ===")
    print(f"{'material':<10}{'E[MeV]':>8}{'MCDC':>11}{'MCNP':>11}{'NIST':>11}"
          f"{'MCDC/NIST-1':>13}{'MCNP/NIST-1':>13}")
    for name, s in results.items():
        if name not in NIST_REF:
            continue
        for Eref, ref in NIST_REF[name].items():
            a = float(loglog_interp(np.array([Eref]), s["E"], s["mu_mcdc"]["total"])[0])
            b = float(loglog_interp(np.array([Eref]), s["E"], s["mu_mcnp"]["total"])[0])
            print(f"{name:<10}{Eref:>8g}{a:>11.5f}{b:>11.5f}{ref:>11.5f}"
                  f"{(a/ref-1)*100:>12.2f}%{(b/ref-1)*100:>12.2f}%")

    print("\n\n=== Material comparison: % diff = 100*(MCDC-MCNP)/MCNP ===")
    print(f"(absorption edges +/-{EDGE_WINDOW*100:.0f}% excluded from 'clean'; "
          f"pair below {PAIR_CLEAN_EMIN} MeV excluded)")
    for name, s in results.items():
        print(f"\n== {name}  (rho = {s['rho']} g/cm^3) ==")
        print(f"{'reaction':<14}{'max|%|':>9}{'mean%':>9}{'max|%|':>9}{'mean%':>9}"
              f"  " + "".join(f"{e:>8g}" for e in REPORT_E) + "  (MeV)")
        print(f"{'':<14}{'full':>9}{'full':>9}{'1-10MeV':>9}{'1-10MeV':>9}"
              f"  " + "".join(f"{'':>8}" for e in REPORT_E))
        for r in REACTIONS:
            print(f"{r:<14}{s[(r,'max_clean')]:9.3f}{s[(r,'mean_clean')]:9.3f}"
                  f"{s[(r,'max_band')]:9.3f}{s[(r,'mean_band')]:9.3f}  "
                  + "".join(f"{v:8.3f}" for v in s[(r, 'points')]))

    print("\n\n=== Absolute total mu/rho [cm^2/g] at report energies ===")
    for name, s in results.items():
        print(f"\n{name}:")
        print(f"{'E[MeV]':>9}{'MCDC':>13}{'MCNP':>13}{'%diff':>9}"
              f"{'Sig_MCDC[1/cm]':>16}{'Sig_MCNP[1/cm]':>16}")
        for i, e in enumerate(REPORT_E):
            a, b = s[("total", "mu_a_pts")][i], s[("total", "mu_b_pts")][i]
            print(f"{e:>9g}{a:>13.5g}{b:>13.5g}{(a/b-1)*100:>9.3f}"
                  f"{a*s['rho']:>16.5g}{b*s['rho']:>16.5g}")

    # ---- Plot --------------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(2, 3, figsize=(16, 9), sharex=True)
        for ax, (name, s) in zip(axs.flat, results.items()):
            for r in REACTIONS:
                q = np.where(s["keep"], s["pct"][r], np.nan)
                ax.semilogx(s["E"], q, lw=1.8 if r == "total" else 0.9,
                            color="k" if r == "total" else None, label=r,
                            zorder=5 if r == "total" else 2)
            ax.axhline(0, color="gray", lw=0.6)
            ax.axvspan(*BENCH_BAND, color="gold", alpha=0.18, zorder=0)
            ax.set_title(f"{name}  (rho = {s['rho']} g/cm$^3$)")
            ax.set_ylabel("100(MCDC-MCNP)/MCNP [%]")
            ax.set_ylim(-15, 15)
            ax.grid(alpha=0.3, which="both")
        for ax in axs[-1]:
            ax.set_xlabel("Energy [MeV]")
        axs.flat[0].legend(fontsize=8, loc="lower left")
        fig.suptitle("MC/DC (EPICS) vs MCNP mcplib84 photon cross sections; "
                     "gold band = 1-10 MeV benchmark source range")
        fig.tight_layout()
        fig.savefig(outdir / "pctdiff_materials.png", dpi=160)
        print(f"\nPlot: {outdir/'pctdiff_materials.png'}")
    except ImportError:
        print("\n(matplotlib unavailable; no plot)")
    print(f"CSVs in {outdir}/")


if __name__ == "__main__":
    main()
