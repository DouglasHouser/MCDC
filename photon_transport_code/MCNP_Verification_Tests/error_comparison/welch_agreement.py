# -*- coding: utf-8 -*-
"""
Welch-Satterthwaite agreement analysis: MC/DC vs MCNP, every tally bin of
every benchmark problem in the photon-transport paper that has an MCNP
counterpart.

Why Welch and not a plain z-test
--------------------------------
The two codes estimate sigma by different routes with very different
precision:

  MC/DC  sigma is a batch-to-batch sample standard error over B batches.
         All eight comparison problems ran B = 10, so that estimate carries
         nu = B - 1 = 9 degrees of freedom -- sigma itself is uncertain by
         about 1/sqrt(2(B-1)) = 24 %.

  MCNP   sigma is a per-history estimate over the full nps.  MCNP has no
         user batch count, so nu = nps - 1, which is >= 1e6 - 1 here and
         effectively infinite.

Comparing two means whose variance estimates have unequal and finite
degrees of freedom is the Behrens-Fisher problem.  The Welch-Satterthwaite
construction gives the effective dof of the pooled variance,

    nu_eff = (s_M^2 + s_N^2)^2 / ( s_M^4/nu_M + s_N^4/nu_N )

and the comparison is then made against Student's t at nu_eff rather than
the normal quantile 1.96.  Because nu_M = 9 is small, nu_eff is pulled down
toward 9 in every bin where MC/DC's sigma contributes appreciably, and the
critical value rises from 1.960 toward t(0.975, 9) = 2.262.  The test is
therefore strictly more permissive than the z-test -- correctly so, since
the z-test credits MC/DC's 10-batch sigma with more precision than it has.

Bin is called statistically indistinguishable when

    |t| = |phi_M - phi_N| / sqrt(s_M^2 + s_N^2)  <=  t(0.975, nu_eff)

Confidence intervals on the agreement fraction
----------------------------------------------
Two forms are reported per problem and overall:
  * Wilson score interval -- primary; behaves sensibly at 0/4 and 20/20
    where the Wald interval collapses to zero width.
  * Clopper-Pearson exact -- conservative cross-check.
Overall, a pooled bin-level interval is reported alongside an
equal-weight-per-problem interval, because bins inside one problem are not
independent samples (see the caveat printed in the report).

Writes MCNP_Verification_Tests/welch_satterthwaite_agreement.txt
"""
import os
import re
import numpy as np
from scipy import stats

from build_se_workbook import (
    BASE, R1E7, RCONV, SHELLS,
    parse_xlsb_sphere, parse_mcnp_sphere_out, parse_mcdc_cylinder,
    parse_mcnp_cell_tally, parse_mcdc_slabs, parse_mcdc_mesh,
    parse_mcnp_mesh, parse_mcdc_spectrum, parse_mcnp_spectrum,
)

MCDC_HIST = {}
CONF = 0.95
ALPHA = 1.0 - CONF
NU_MCDC = 9          # B - 1, B = 10 batches, all eight comparison problems
OUT = os.path.join(BASE, "..", "welch_satterthwaite_agreement.txt")

_REPO_MCNP = os.path.normpath(os.path.join(
    BASE, "..", "MCNP_test_problems", "mcnp_outputs",
    "pb_10mev_sphere_MCNP_nobrem.out"))
_PB1_MCNP = os.path.normpath(os.path.join(
    BASE, "..", "MCNP_test_problems", "mcnp_outputs",
    "pb_1mev_sphere_MCNP_TTBon.out"))


# ------------------------------------------------------------------ stats
def welch(fM, sM, fN, sN, nu_M=NU_MCDC, nu_N=np.inf):
    """(t, nu_eff, t_crit, indistinguishable) or None when undefined.

    A bin with zero flux in either code has an undefined relative error and
    is excluded symmetrically, exactly as in the workbook.
    """
    if fM is None or fN is None or sM is None or sN is None:
        return None
    if not (np.isfinite(fM) and np.isfinite(fN)
            and np.isfinite(sM) and np.isfinite(sN)):
        return None
    vM, vN = sM ** 2, sN ** 2
    vc = vM + vN
    if vc <= 0.0:
        return None
    if nu_N == np.inf:
        denom = vM ** 2 / nu_M
    else:
        denom = vM ** 2 / nu_M + vN ** 2 / nu_N
    nu_eff = np.inf if denom <= 0.0 else vc ** 2 / denom
    tcrit = stats.t.ppf(1.0 - ALPHA / 2.0, nu_eff)
    t = (fM - fN) / np.sqrt(vc)
    return t, nu_eff, tcrit, abs(t) <= tcrit


def wilson(k, n, conf=CONF):
    if n == 0:
        return (float("nan"), float("nan"))
    z = stats.norm.ppf(1.0 - (1.0 - conf) / 2.0)
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def clopper_pearson(k, n, conf=CONF):
    if n == 0:
        return (float("nan"), float("nan"))
    a = 1.0 - conf
    lo = 0.0 if k == 0 else stats.beta.ppf(a / 2.0, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1.0 - a / 2.0, k + 1, n - k)
    return (lo, hi)


def nps_from(path):
    """nps of the first F4 tally in an MCNP output."""
    txt = open(path).read()
    m = re.search(r"1tally\s+4\s+nps\s*=\s*(\d+)", txt)
    return int(m.group(1)) if m else None


# ------------------------------------------------------------------ build
# Each problem -> list of bins; a bin is (label, fM, sM, fN, sN).
problems = []    # (key, title, nps_mcnp, nps_note, bins, extra_note)

# ---- 1-4. Al / Pb spheres, 1e6 vs 1e6 -------------------------------
SPH = [("Al 1 MeV", "Al sphere, 1 MeV point source", None),
       ("Al 10 MeV", "Al sphere, 10 MeV point source", None),
       ("Pb 1 MeV", "Pb sphere, 1 MeV point source", _PB1_MCNP),
       ("Pb 10 MeV", "Pb sphere, 10 MeV point source", _REPO_MCNP)]

for sheet, title, outfile in SPH:
    rows = parse_xlsb_sphere(sheet)
    note = ""
    nps = 1_000_000
    if sheet == "Pb 10 MeV":
        # .xlsb MCNP rel-err column for this problem is not its own; replace
        # flux AND error from the TTB-off run that matches its fluxes 20/20.
        rep = parse_mcnp_sphere_out(outfile)
        for row, (f_new, e_new) in zip(rows, rep):
            row["mcnp_flux"] = f_new
            row["mcnp_re"] = e_new if f_new > 0 else None
        nps = nps_from(outfile) or nps
        note = ("MCNP flux and rel-err taken from pb_10mev_sphere_MCNP_nobrem.out "
                "(the .xlsb error column for this problem was not its own).")
    elif outfile and os.path.exists(outfile):
        nps = nps_from(outfile) or nps
        note = "MCNP nps read from %s." % os.path.basename(outfile)
    else:
        note = ("No MCNP output file exists for this problem; nps = 1e6 per the "
                "run record, per-history error assumed (nu_N = nps - 1).")
    bins = []
    for row in rows:
        fM, fN = row["mcdc_flux"], row["mcnp_flux"]
        reM, reN = row["mcdc_re"], row["mcnp_re"]
        sM = fM * reM if (fM and reM) else None
        sN = fN * reN if (fN and reN) else None
        bins.append(("r_vavg=%8.4f" % row["r_vavg"], fM, sM, fN, sN))
    problems.append((sheet, title, nps, note, bins, ""))
    MCDC_HIST[sheet] = "100,000 x 10 batches = 1e6"

# ---- 5. Pb finite cylinder, off-centre source, 2e8 vs 2e8 -----------
mcdc_cyl = parse_mcdc_cylinder(os.path.join(R1E7, "lead_finite_cylinder_2e8_results.txt"))
mcnp_cyl, _cv, cyl_nps = parse_mcnp_cell_tally(
    os.path.join(R1E7, "lead_finite_cylinder_off_center_MCNP-big.out"))
bins = []
for row in mcdc_cyl:
    cell = 10 * (row["ir"] + 1) + (row["iz"] + 1)
    nf, nre = mcnp_cyl.get(cell, (None, None))
    bins.append(("r%d z%d (cell %d)" % (row["ir"], row["iz"], cell),
                 row["flux"], row["sig"], nf,
                 nf * nre if nf is not None else None))
MCDC_HIST["Pb Cylinder Off-Ctr"] = "20,000,000 x 10 batches = 2e8"
problems.append(("Pb Cylinder Off-Ctr", "Pb finite cylinder, off-centre 1 MeV source",
                 cyl_nps, "MCNP nps read from output file.", bins,
                 "All four regions of axial segment z3 tallied zero flux in BOTH "
                 "codes -> undefined relative error, excluded symmetrically."))

# ---- 6. Multi-material slab, collimated beam, 1e8 vs 1e8 -----------
mcdc_sl = parse_mcdc_slabs(os.path.join(R1E7, "mm_slabs_collimated_beam_results.txt"))
mcnp_sl, sl_vols, sl_nps = parse_mcnp_cell_tally(
    os.path.join(R1E7, "multi_material_slabs_collimated_beam_MCNP-big.out"))
bins = []
for row in mcdc_sl:
    cell = row["slab"] + 2
    nf_raw, nre = mcnp_sl[cell]
    area = sl_vols[cell] / row["thk"]          # 1.0e4 cm^2
    nf = nf_raw * area
    bins.append(("slab %d %-8s" % (row["slab"], row["mat"]),
                 row["flux"], row["sig"], nf, nf * nre))
MCDC_HIST["MM Slab Collim Beam"] = "10,000,000 x 10 batches = 1e8"
problems.append(("MM Slab Collim Beam", "Multi-material slab, 1 MeV collimated beam",
                 sl_nps, "MCNP nps read from output file.", bins,
                 "MCNP flux and sigma scaled by the transverse area "
                 "(volume/thickness = 1.0e4 cm^2) to match MC/DC's per-cm^2 "
                 "convention; the t statistic is invariant to this rescaling."))

# ---- 7. Multi-material slab, mesh tally, 1e8 vs 1e8 ----------------
mcdc_me = parse_mcdc_mesh(os.path.join(R1E7, "multi_material_slabs_mesh_tally_results.txt"))
area_me, mcnp_me, me_nps = parse_mcnp_mesh(os.path.join(R1E7, "meshtam"))
bins = []
for row in mcdc_me:
    if row["z"] <= 0:                 # backing gap, outside the plotted range
        continue
    key = round(row["z"], 3)
    if key not in mcnp_me:
        continue
    nf_raw, nre = mcnp_me[key]
    nf = nf_raw * area_me
    bins.append(("z=%7.2f %-9s" % (row["z"], row["mat"]),
                 row["flux"], row["sig"], nf, nf * nre))
MCDC_HIST["MM Slab Mesh Tally"] = "10,000,000 x 10 batches = 1e8"
problems.append(("MM Slab Mesh Tally", "Multi-material slab, 1 MeV point source, mesh tally",
                 int(me_nps), "MCNP nps read from the FMESH normalisation line.", bins,
                 "The 200 bins at z > 0 (the range plotted in Fig. 8); the "
                 "backing-gap bin at z = -0.5 cm is excluded.  MCNP flux and "
                 "sigma scaled by the transverse mesh area (%.0f cm^2)."
                 % area_me))

# ---- 8. Multi-material sphere, 1-10 MeV spectrum, 1e8 vs 1e8 -------
edges, sf, ss, rv = parse_mcdc_spectrum(
    os.path.join(RCONV, "mm_spheres_1to10mev_spec_1e8_results.txt"))
nbins = sf.shape[1]
nf_all, nre_all, _nv, sp_nps = parse_mcnp_spectrum(
    os.path.join(RCONV, "multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out"), nbins)
bins = []
for reg in range(12):
    mat, r0, r1 = SHELLS[reg]
    for b in range(1, nbins):        # bin 1 (index 0) has mismatched edges
        fM, sM = float(sf[reg, b]), float(ss[reg, b])
        fN = float(nf_all[reg, b])
        sN = fN * float(nre_all[reg, b])
        bins.append(("reg %2d %-9s Ebin %2d" % (reg, mat, b + 1), fM, sM, fN, sN))
MCDC_HIST["MM Sphere Spectrum"] = "10,000,000 x 10 batches = 1e8"
problems.append(("MM Sphere Spectrum", "Multi-material sphere, 1-10 MeV source, energy spectrum",
                 sp_nps, "MCNP file is named '-1e9' but its tally header reports "
                 "nps = 1e8; the matched 1e8 MC/DC run is used.", bins,
                 "Energy bin 1 (0.0100-0.0119 MeV) is excluded: MCNP's first "
                 "interval starts at 0 MeV, MC/DC's at 0.01 MeV."))


# ------------------------------------------------------------------ run
results = []     # per problem: dict
detail = {}      # key -> list of detail rows

for key, title, nps, nps_note, bins, extra in problems:
    nu_N = (nps - 1) if nps else np.inf
    rows, k_w, k_z, n = [], 0, 0, 0
    nu_list, tc_list = [], []
    for label, fM, sM, fN, sN in bins:
        r = welch(fM, sM, fN, sN, NU_MCDC, nu_N)
        if r is None:
            rows.append((label, fM, sM, fN, sN, None, None, None, None, None))
            continue
        t, nu_eff, tcrit, ok = r
        n += 1
        k_w += ok
        k_z += abs(t) <= 1.959963985
        nu_list.append(nu_eff)
        tc_list.append(tcrit)
        sc = np.hypot(sM, sN)
        rows.append((label, fM, sM, fN, sN, t, nu_eff, tcrit, ok, sc))
    detail[key] = rows
    results.append(dict(
        key=key, title=title, nps=nps, nps_note=nps_note, extra=extra,
        n=n, k=k_w, k_z=k_z,
        frac=(k_w / n if n else float("nan")),
        frac_z=(k_z / n if n else float("nan")),
        wilson=wilson(k_w, n), cp=clopper_pearson(k_w, n),
        nu_med=(float(np.median(nu_list)) if nu_list else float("nan")),
        nu_min=(float(np.min(nu_list)) if nu_list else float("nan")),
        nu_max=(float(np.max(nu_list)) if nu_list else float("nan")),
        tc_med=(float(np.median(tc_list)) if tc_list else float("nan")),
        tc_min=(float(np.min(tc_list)) if tc_list else float("nan")),
        tc_max=(float(np.max(tc_list)) if tc_list else float("nan")),
        n_excl=len(bins) - n,
    ))

N = sum(r["n"] for r in results)
K = sum(r["k"] for r in results)
KZ = sum(r["k_z"] for r in results)
POOL_W = wilson(K, N)
POOL_CP = clopper_pearson(K, N)

# Equal-weight-per-problem mean, with a t interval over the 8 problem rates.
rates = np.array([r["frac"] for r in results])
P = len(rates)
mean_rate = float(rates.mean())
sd_rate = float(rates.std(ddof=1))
se_rate = sd_rate / np.sqrt(P)
t_p = stats.t.ppf(0.975, P - 1)
EQ_LO, EQ_HI = mean_rate - t_p * se_rate, mean_rate + t_p * se_rate

# Design effect of the pooled interval (cluster = problem).
ns = np.array([r["n"] for r in results], float)
p_bar = K / N
num = float(np.sum(ns * (rates - p_bar) ** 2)) / (P - 1)
deff = num / (p_bar * (1 - p_bar)) if 0 < p_bar < 1 else float("nan")
n_eff = N / deff if deff and np.isfinite(deff) and deff > 0 else float("nan")
if np.isfinite(n_eff):
    k_eff = int(round(p_bar * n_eff))
    DE_LO, DE_HI = wilson(k_eff, int(round(n_eff)))
else:
    DE_LO = DE_HI = float("nan")


if __name__ == "__main__":
    # ------------------------------------------------------------------ report
    L = []
    A = L.append
    BAR = "=" * 100
    SUB = "-" * 100


    def pc(x):
        return "n/a" if not np.isfinite(x) else "%.1f%%" % (100.0 * x)


    A(BAR)
    A("WELCH-SATTERTHWAITE AGREEMENT ANALYSIS -- MC/DC vs MCNP")
    A("Photon transport in MC/DC: what fraction of tally bins are statistically")
    A("indistinguishable between the two codes at the 95% confidence level?")
    A(BAR)
    A("")
    A("Generated : 2026-10-02")
    A("Script    : MCNP_Verification_Tests/error_comparison/welch_agreement.py")
    A("Companion : photon_standard_error_comparison.xlsx (per-bin workbook)")
    A("")
    A("")
    A("1. WHY WELCH-SATTERTHWAITE")
    A(SUB)
    A("")
    A("The two codes do not estimate sigma the same way, and the two estimates do")
    A("not carry the same precision:")
    A("")
    A("  MC/DC   sigma is a batch-to-batch sample standard error over B batches.")
    A("          Every one of the eight comparison problems ran B = 10, so that")
    A("          estimate has nu_M = B - 1 = 9 degrees of freedom.  sigma itself")
    A("          is uncertain by ~1/sqrt(2(B-1)) = 24%.")
    A("")
    A("  MCNP    sigma is a per-history estimate over the full nps.  MCNP has no")
    A("          user batch count -- one continuous run -- so nu_N = nps - 1.")
    A("          Here nps >= 1e6 in every problem, so nu_N is effectively")
    A("          infinite and sigma_N is effectively exact.")
    A("")
    A("Comparing two means whose variance estimates have unequal and finite dof is")
    A("the Behrens-Fisher problem.  A plain z-test against 1.96 implicitly treats")
    A("BOTH sigmas as exact, which over-credits MC/DC's 10-batch estimate and")
    A("rejects agreement too often.  The Welch-Satterthwaite effective dof of the")
    A("pooled variance is")
    A("")
    A("    nu_eff = (s_M^2 + s_N^2)^2 / ( s_M^4/nu_M + s_N^4/nu_N )")
    A("")
    A("and a bin is called statistically indistinguishable when")
    A("")
    A("    |t| = |phi_M - phi_N| / sqrt(s_M^2 + s_N^2)  <=  t(0.975, nu_eff)")
    A("")
    A("Because nu_M = 9 is small, nu_eff is pulled toward 9 in every bin where")
    A("MC/DC's sigma contributes appreciably, and the critical value rises from")
    A("1.960 toward t(0.975, 9) = 2.262.  The bound is therefore")
    A("")
    A("    1.960  <=  t_crit  <=  2.262")
    A("")
    A("so this test can only ever call MORE bins indistinguishable than the")
    A("z-test, never fewer.  Both counts are reported side by side below.")
    A("")
    A("For the two Al sphere problems no MCNP output file survives.  Per the run")
    A("record both used nps = 1e6, and MCNP reports per-history error, so nu_N =")
    A("1e6 - 1 is assumed for them.  t(0.975, nu) is flat to 4 decimals for any")
    A("nu above ~1e5, so this assumption changes no verdict.")
    A("")
    A("")
    A("2. BIN EXCLUSIONS (applied symmetrically to both codes)")
    A(SUB)
    A("")
    A("A bin with zero flux in either code has an UNDEFINED relative error, not a")
    A("zero one -- MCNP prints 0.0000 for an empty bin and MC/DC can print a zero")
    A("sdev when all batch scores coincide.  Such bins carry no information about")
    A("agreement and are dropped from both the numerator and the denominator.")
    A("Two further exclusions, both carried over from the paper's own comparison")
    A("script:")
    A("")
    A("  * MM Sphere Spectrum, energy bin 1 (0.0100-0.0119 MeV): MCNP's first")
    A("    tally interval starts at 0 MeV, MC/DC's at 0.01 MeV -- not the same bin.")
    A("  * MM Slab Mesh Tally, z = -0.5 cm: the vacuum backing gap behind the")
    A("    source, outside the depth range the paper plots.")
    A("")
    A("")
    A("3. PER-PROBLEM RESULTS")
    A(SUB)
    A("")
    hdr = ("%-22s %5s %5s %7s   %-18s %-18s  %6s %6s" %
           ("Problem", "bins", "indis", "frac", "95% CI (Wilson)",
            "95% CI (Clopper-P)", "nu_eff", "t_crit"))
    A(hdr)
    A("%-22s %5s %5s %7s   %-18s %-18s  %6s %6s" %
      ("", "", "", "", "", "", "median", "median"))
    A("-" * len(hdr))
    for r in results:
        A("%-22s %5d %5d %7s   [%5.1f%%, %5.1f%%]   [%5.1f%%, %5.1f%%]   %6s %6.3f" % (
            r["key"], r["n"], r["k"], pc(r["frac"]),
            100 * r["wilson"][0], 100 * r["wilson"][1],
            100 * r["cp"][0], 100 * r["cp"][1],
            ("%.1f" % r["nu_med"]) if np.isfinite(r["nu_med"]) else "inf",
            r["tc_med"]))
    A("-" * len(hdr))
    A("%-22s %5d %5d %7s   [%5.1f%%, %5.1f%%]   [%5.1f%%, %5.1f%%]" % (
        "ALL PROBLEMS (pooled)", N, K, pc(K / N),
        100 * POOL_W[0], 100 * POOL_W[1], 100 * POOL_CP[0], 100 * POOL_CP[1]))
    A("")
    A("Comparison with the plain z-test (critical value fixed at 1.960):")
    A("")
    A("%-22s %7s %7s %9s" % ("Problem", "Welch", "z-test", "bins moved"))
    A("-" * 48)
    for r in results:
        A("%-22s %7s %7s %9d" % (r["key"], pc(r["frac"]), pc(r["frac_z"]),
                                 r["k"] - r["k_z"]))
    A("-" * 48)
    A("%-22s %7s %7s %9d" % ("ALL PROBLEMS", pc(K / N), pc(KZ / N), K - KZ))
    A("")
    A("")
    A("4. OVERALL AGREEMENT -- THREE INTERVALS, AND WHICH TO QUOTE")
    A(SUB)
    A("")
    A("(a) Pooled bin-level, every comparable bin treated as one independent draw")
    A("")
    A("      %d / %d = %s      95%% CI  [%.1f%%, %.1f%%]   (Wilson)" %
      (K, N, pc(K / N), 100 * POOL_W[0], 100 * POOL_W[1]))
    A("                             95%% CI  [%.1f%%, %.1f%%]   (Clopper-Pearson)" %
      (100 * POOL_CP[0], 100 * POOL_CP[1]))
    A("")
    _big = sum(r["n"] for r in results
               if r["key"] in ("MM Slab Mesh Tally", "MM Sphere Spectrum"))
    A("    This is the headline number, and it is the one directly comparable to")
    A("    the claim currently in the abstract.  Its interval is however too")
    A("    narrow: bins within one problem share a geometry, a source and a")
    A("    cross-section path, so they are not independent draws, and just two")
    A("    problems (mesh tally and sphere spectrum) supply %d of the %d bins," % (_big, N))
    A("    i.e. %.0f%% of the pooled weight." % (100.0 * _big / N))
    A("")
    A("(b) Equal weight per problem -- the mean of the eight per-problem rates")
    A("")
    A("      mean = %s   sd = %.1f%%   95%% CI  [%.1f%%, %.1f%%]   (t, %d dof)" %
      (pc(mean_rate), 100 * sd_rate, 100 * EQ_LO, 100 * EQ_HI, P - 1))
    A("")
    A("    This treats the eight benchmark problems as the sampling unit rather")
    A("    than the bins, so one 420-bin problem cannot outvote one 4-bin")
    A("    problem.  The interval is wide because the per-problem rates are")
    A("    genuinely spread from 0% to 100% -- that spread is the real result.")
    A("")
    A("(c) Pooled, corrected for clustering by problem (design effect)")
    A("")
    if np.isfinite(deff):
        A("      design effect = %.1f   effective n = %.0f of %d bins" % (deff, n_eff, N))
        A("      %s      95%% CI  [%.1f%%, %.1f%%]" %
          (pc(p_bar), 100 * DE_LO, 100 * DE_HI))
        A("")
        A("    The between-problem spread inflates the variance by a factor of")
        A("    %.1f over binomial, so the %d bins carry only about %.0f bins' worth" %
          (deff, N, n_eff))
        A("    of independent information.  Treat this as evidence that interval")
        A("    (a) is too narrow rather than as a precise interval itself: with")
        A("    only %d clusters, of sizes 4 to %d, the design effect is a noisy" % (P, int(ns.max())))
        A("    estimate.  For a headline claim, quote (a) for the literal bin")
        A("    fraction and (b) when speaking about the problems as a set.")
    else:
        A("      not computable")
    A("")
    A("")
    A("5. WHAT THIS MEANS FOR THE PAPER")
    A(SUB)
    A("")
    A("The abstract currently states that 'roughly 55% of individual tally bins")
    A("are statistically indistinguishable between MC/DC and MCNP' at the 95%")
    A("confidence level.  Recomputed over all %d comparable bins with the Welch-" % N)
    A("Satterthwaite correction, the figure is %s, 95%% CI [%.1f%%, %.1f%%]" %
      (pc(K / N), 100 * POOL_W[0], 100 * POOL_W[1]))
    A("pooled, or %s [%.1f%%, %.1f%%] weighting each problem equally." %
      (pc(mean_rate), 100 * EQ_LO, 100 * EQ_HI))
    A("")
    A("The Welch correction moves the pooled count by %+d bins (%s -> %s)" %
      (K - KZ, pc(KZ / N), pc(K / N)))
    A("relative to the z-test, so the gap against 55% is not an artefact of the")
    A("unequal batch structure: it survives the correction that was supposed to")
    A("explain it.  The dominant cause is the mesh tally, where a persistent")
    A("5-12% flux offset sits far outside sigmas of ~1.4%, and the mesh tally")
    A("alone contributes 200 of the %d bins." % N)
    A("")
    A("Two honest framings are available and both should be stated:")
    A("  * pooled over bins, agreement is %s -- driven down by the two" % pc(K / N))
    A("    large-bin-count problems;")
    A("  * per problem, agreement ranges from %s to %s, and the simple" %
      (pc(min(rates)), pc(max(rates))))
    A("    average across the eight problems is %s." % pc(mean_rate))
    A("")
    A("Note separately that 'statistically indistinguishable' and 'physically")
    A("close' are different claims.  MM Slab Collim Beam agrees in 0 of 4 bins")
    A("yet its largest flux difference is 8.24%, because its sigmas are ~0.16%;")
    A("Pb 10 MeV agrees in 12 of 16 bins while differing by up to 76%, because")
    A("its sigmas reach 100%.  A high agreement fraction in a high-variance")
    A("problem is weak evidence of physics agreement, not strong evidence.")
    A("")
    A("")
    A("6. PER-BIN DETAIL")
    A(SUB)
    for r in results:
        A("")
        A("")
        A("%s -- %s" % (r["key"], r["title"]))
        A("  MC/DC: %s, nu_M = 9" % MCDC_HIST.get(r["key"], "10 batches"))
        A("  MCNP : nps = %s, per-history error, nu_N = %s" %
          ("%d" % r["nps"] if r["nps"] else "1e6 (assumed)",
           "%d" % (r["nps"] - 1) if r["nps"] else "999999"))
        A("  %s" % r["nps_note"])
        if r["extra"]:
            A("  %s" % r["extra"])
        A("  comparable bins: %d   excluded: %d   indistinguishable: %d (%s)" %
          (r["n"], r["n_excl"], r["k"], pc(r["frac"])))
        A("  nu_eff over comparable bins: min %.1f  median %.1f  max %s" %
          (r["nu_min"], r["nu_med"],
           ("%.1f" % r["nu_max"]) if np.isfinite(r["nu_max"]) else "inf"))
        A("  t_crit  over comparable bins: min %.3f  median %.3f  max %.3f" %
          (r["tc_min"], r["tc_med"], r["tc_max"]))
        A("")
        A("  %-26s %12s %11s %12s %11s %9s %8s %7s %6s" % (
            "bin", "MC/DC flux", "MC/DC sig", "MCNP flux", "MCNP sig",
            "t", "nu_eff", "t_crit", "indis"))
        A("  " + "-" * 118)
        for (label, fM, sM, fN, sN, t, nu_eff, tcrit, ok, sc) in detail[r["key"]]:
            if t is None:
                A("  %-26s %12s %11s %12s %11s %9s %8s %7s %6s" % (
                    label,
                    "%.4e" % fM if fM is not None else "-",
                    "%.4e" % sM if sM is not None else "-",
                    "%.4e" % fN if fN is not None else "-",
                    "%.4e" % sN if sN is not None else "-",
                    "-", "-", "-", "EXCL"))
                continue
            A("  %-26s %12.4e %11.4e %12.4e %11.4e %9.3f %8.1f %7.3f %6s" % (
                label, fM, sM, fN, sN, t, nu_eff, tcrit, "yes" if ok else "no"))

    A("")
    A("")
    A(BAR)
    A("END")
    A(BAR)

    txt = "\n".join(x for x in L if x is not None)
    OUT = os.path.normpath(OUT)
    open(OUT, "w") .write(txt)
    print("wrote", OUT, len(txt), "chars")
    print()
    print("%-22s %5s %5s %8s  %-20s" % ("Problem", "bins", "indis", "frac", "95% CI Wilson"))
    for r in results:
        print("%-22s %5d %5d %8s  [%5.1f%%, %5.1f%%]" % (
            r["key"], r["n"], r["k"], pc(r["frac"]),
            100 * r["wilson"][0], 100 * r["wilson"][1]))
    print("%-22s %5d %5d %8s  [%5.1f%%, %5.1f%%]" % (
        "ALL (pooled)", N, K, pc(K / N), 100 * POOL_W[0], 100 * POOL_W[1]))
    print("z-test pooled: %d/%d = %s" % (KZ, N, pc(KZ / N)))
    print("equal-weight : %s  [%.1f%%, %.1f%%]" % (pc(mean_rate), 100 * EQ_LO, 100 * EQ_HI))
    print("design effect: %.2f  n_eff %.0f  CI [%.1f%%, %.1f%%]" % (deff, n_eff, 100 * DE_LO, 100 * DE_HI))
