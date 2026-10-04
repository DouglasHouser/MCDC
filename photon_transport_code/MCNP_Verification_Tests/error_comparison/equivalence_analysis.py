# -*- coding: utf-8 -*-
"""
Equivalence (TOST) analysis: MC/DC vs MCNP, every comparable tally bin of
every benchmark problem in the photon-transport paper.

Why this and not the agreement fraction
---------------------------------------
"What fraction of bins are statistically indistinguishable?" is a
significance test of H0: phi_M == phi_N.  As a verification figure of merit
it behaves backwards:

  * Precision punishes you.  As histories -> infinity, sigma -> 0, so |t| ->
    infinity for ANY nonzero bias, however physically trivial.  The mesh
    tally has sigma ~1.4 % against a 5-12 % offset and scores 1.5 %; running
    MORE histories would push that toward 0 %.
  * Noise rewards you.  Bins whose sigma reach 100 % "agree" because nothing
    can be resolved there.

And failing to reject H0 is not evidence for H0 in the first place.

The claim the paper actually wants to make is equivalence within a stated
tolerance, which is the reverse hypothesis:

    H0: |phi_M/phi_N - 1| >= delta        (the codes differ by at least delta)
    H1: |phi_M/phi_N - 1| <  delta        (the codes agree within delta)

Rejecting this H0 is positive evidence of agreement, and precision now HELPS:
a tight CI sitting inside +/- delta is a strong result.  Operationally this is
the two-one-sided-t (TOST) procedure, implemented here as a CI containment
test on the flux ratio.

Procedure, per bin
------------------
    R        = phi_M / phi_N
    s_lnR    = sqrt(re_M^2 + re_N^2)                  (delta method, log scale)
    nu_eff   = (re_M^2+re_N^2)^2 / (re_M^4/nu_M + re_N^4/nu_N)   Welch-Satterthwaite
    CI(R)    = exp( ln R  +/-  t(0.975, nu_eff) * s_lnR )

Three-way verdict against a tolerance delta, which is strictly more
informative than a pass/fail:

    EQUIVALENT    CI(R) lies entirely inside [1-delta, 1+delta]
                  -> agreement within delta is demonstrated
    DIFFERENT     CI(R) lies entirely outside that band
                  -> a discrepancy larger than delta is demonstrated
    INCONCLUSIVE  CI(R) straddles a boundary
                  -> the run is too noisy to decide at this delta

nu_M = 9 (B = 10 batches) and nu_N = nps - 1 exactly as in
welch_agreement.py, so the two analyses rest on identical inputs and the
same dof treatment.  Using the 95 % CI makes this a conservative
equivalence test; the conventional TOST at alpha = 0.05 uses the 90 % CI and
is slightly more permissive.  Both are reported.

Writes MCNP_Verification_Tests/equivalence_analysis.txt
"""
import os
import numpy as np
from scipy import stats

import welch_agreement as wa

NU_MCDC = wa.NU_MCDC
OUT = os.path.normpath(os.path.join(wa.BASE, "..", "equivalence_analysis.txt"))
DELTAS = [0.05, 0.10]


def ratio_ci(fM, sM, fN, sN, nu_N, conf):
    """(R, lo, hi, nu_eff, tcrit) for the flux ratio, or None if undefined."""
    if fM is None or fN is None or sM is None or sN is None:
        return None
    if not all(np.isfinite(x) for x in (fM, sM, fN, sN)):
        return None
    if fM <= 0 or fN <= 0:
        return None
    reM, reN = sM / fM, sN / fN
    vM, vN = reM ** 2, reN ** 2
    vc = vM + vN
    if vc <= 0:
        return None
    denom = vM ** 2 / NU_MCDC + (0.0 if nu_N == np.inf else vN ** 2 / nu_N)
    nu_eff = np.inf if denom <= 0 else vc ** 2 / denom
    tcrit = stats.t.ppf(1.0 - (1.0 - conf) / 2.0, nu_eff)
    lnR = np.log(fM / fN)
    h = tcrit * np.sqrt(vc)
    return (np.exp(lnR), np.exp(lnR - h), np.exp(lnR + h), nu_eff, tcrit)


def verdict(lo, hi, d):
    """EQUIVALENT / DIFFERENT / INCONCLUSIVE against tolerance d."""
    band_lo, band_hi = 1.0 - d, 1.0 + d
    if lo >= band_lo and hi <= band_hi:
        return "EQUIV"
    if hi < band_lo or lo > band_hi:
        return "DIFF"
    return "INCONC"


def wilson(k, n, conf=0.95):
    if n == 0:
        return (float("nan"), float("nan"))
    z = stats.norm.ppf(1.0 - (1.0 - conf) / 2.0)
    p = k / n
    den = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


# ------------------------------------------------------------------ compute
rows_by_problem = {}
summary = []

for key, title, nps, nps_note, bins, extra in wa.problems:
    nu_N = (nps - 1) if nps else 999999.0
    recs = []
    for label, fM, sM, fN, sN in bins:
        r95 = ratio_ci(fM, sM, fN, sN, nu_N, 0.95)
        r90 = ratio_ci(fM, sM, fN, sN, nu_N, 0.90)
        if r95 is None:
            continue
        R, lo, hi, nu_eff, tcrit = r95
        wv = wa.welch(fM, sM, fN, sN, NU_MCDC, nu_N)
        rec = dict(label=label, fM=fM, sM=sM, fN=fN, sN=sN, R=R, lo=lo, hi=hi,
                   nu_eff=nu_eff, tcrit=tcrit, d_pct=100.0 * (R - 1.0),
                   lo90=r90[1], hi90=r90[2],
                   indis=(wv[3] if wv is not None else None))
        for d in DELTAS:
            rec["v%d" % int(100 * d)] = verdict(lo, hi, d)
            rec["v%d_90" % int(100 * d)] = verdict(r90[1], r90[2], d)
        recs.append(rec)
    rows_by_problem[key] = recs
    n = len(recs)
    s = dict(key=key, title=title, n=n, nps=nps, nps_note=nps_note, extra=extra)
    for d in DELTAS:
        t = int(100 * d)
        s["eq%d" % t] = sum(1 for r in recs if r["v%d" % t] == "EQUIV")
        s["df%d" % t] = sum(1 for r in recs if r["v%d" % t] == "DIFF")
        s["ic%d" % t] = sum(1 for r in recs if r["v%d" % t] == "INCONC")
        s["eq%d_90" % t] = sum(1 for r in recs if r["v%d_90" % t] == "EQUIV")
        s["pt%d" % t] = sum(1 for r in recs if abs(r["d_pct"]) <= 100 * d)
    s["mean_abs_d"] = float(np.mean([abs(r["d_pct"]) for r in recs])) if n else float("nan")
    s["med_abs_d"] = float(np.median([abs(r["d_pct"]) for r in recs])) if n else float("nan")
    s["max_abs_d"] = float(np.max([abs(r["d_pct"]) for r in recs])) if n else float("nan")
    # indistinguishability recomputed on the IDENTICAL bin set, so all three
    # metrics in the side-by-side table share one denominator.  The companion
    # report's denominator is slightly larger (702 vs this 695) because a bin
    # with zero flux in one code still has a defined combined sigma, and so is
    # testable for a difference but has no defined ratio.
    s["indis"] = sum(1 for r in recs if r["indis"])
    s["n_indis"] = n
    summary.append(s)

N = sum(s["n"] for s in summary)
TOT = {}
for d in DELTAS:
    t = int(100 * d)
    TOT["eq%d" % t] = sum(s["eq%d" % t] for s in summary)
    TOT["df%d" % t] = sum(s["df%d" % t] for s in summary)
    TOT["ic%d" % t] = sum(s["ic%d" % t] for s in summary)
    TOT["eq%d_90" % t] = sum(s["eq%d_90" % t] for s in summary)
    TOT["pt%d" % t] = sum(s["pt%d" % t] for s in summary)

INDIS = sum(s["indis"] for s in summary)
all_d = [abs(r["d_pct"]) for recs in rows_by_problem.values() for r in recs]
MEAN_ABS = float(np.mean(all_d))
MED_ABS = float(np.median(all_d))

# equal-weight-per-problem equivalence rates
eq5_rates = np.array([s["eq5"] / s["n"] for s in summary if s["n"]])
eq10_rates = np.array([s["eq10"] / s["n"] for s in summary if s["n"]])


def eqw(rates):
    P = len(rates)
    m = float(rates.mean())
    sd = float(rates.std(ddof=1))
    tp = stats.t.ppf(0.975, P - 1)
    h = tp * sd / np.sqrt(P)
    return m, sd, max(0.0, m - h), min(1.0, m + h)


EQW5 = eqw(eq5_rates)
EQW10 = eqw(eq10_rates)

# ------------------------------------------------------------------ report
L = []
A = L.append
BAR = "=" * 100
SUB = "-" * 100


def pc(x):
    return "n/a" if not np.isfinite(x) else "%.1f%%" % (100.0 * x)


A(BAR)
A("EQUIVALENCE (TOST) ANALYSIS -- MC/DC vs MCNP")
A("Is MC/DC's photon transport demonstrably equivalent to MCNP within a")
A("stated tolerance?  (Companion to welch_satterthwaite_agreement.txt.)")
A(BAR)
A("")
A("Generated : 2026-10-02")
A("Script    : MCNP_Verification_Tests/error_comparison/equivalence_analysis.py")
A("Inputs    : identical to welch_satterthwaite_agreement.txt -- same files,")
A("            same bins, same nu_M = 9 / nu_N = nps - 1 dof treatment.")
A("")
A("")
A("1. WHY A SECOND METRIC IS NEEDED")
A(SUB)
A("")
A("The companion report answers 'what fraction of bins are statistically")
A("INDISTINGUISHABLE?'.  That is a significance test of H0: phi_M = phi_N, and")
A("as a verification figure of merit it runs backwards:")
A("")
A("  * Precision punishes you.  As histories -> inf, sigma -> 0, so |t| -> inf")
A("    for ANY nonzero bias, however physically trivial.  The mesh tally has")
A("    sigma ~1.4 % against a 5-12 % offset and scores 1.5 %.  Running MORE")
A("    histories would push that fraction toward 0 %.")
A("  * Noise rewards you.  Bins whose sigma reach 100 % 'agree' because")
A("    nothing can be resolved there at all.")
A("")
A("Worse, failing to reject H0 is not evidence FOR H0.  A low agreement")
A("fraction is therefore not evidence that MC/DC is wrong, and a high one")
A("would not have been evidence that it is right.")
A("")
A("The claim the paper wants is equivalence within a tolerance -- the reverse")
A("hypothesis:")
A("")
A("    H0: |phi_M/phi_N - 1| >= delta     (codes differ by at least delta)")
A("    H1: |phi_M/phi_N - 1| <  delta     (codes agree within delta)")
A("")
A("Rejecting THIS H0 is positive evidence of agreement, and precision now")
A("helps instead of hurting.  That is the TOST procedure, implemented here as")
A("a CI-containment test on the flux ratio:")
A("")
A("    R = phi_M/phi_N,   s_lnR = sqrt(re_M^2 + re_N^2)")
A("    nu_eff = (re_M^2+re_N^2)^2 / (re_M^4/nu_M + re_N^4/nu_N)")
A("    CI(R) = exp( ln R +/- t(0.975, nu_eff) * s_lnR )")
A("")
A("")
A("2. THREE-WAY VERDICT")
A(SUB)
A("")
A("A pass/fail split would hide the distinction that matters most here, so")
A("each bin gets one of three verdicts against tolerance delta:")
A("")
A("  EQUIVALENT    CI(R) lies entirely inside [1-delta, 1+delta].")
A("                Agreement within delta is DEMONSTRATED.")
A("  DIFFERENT     CI(R) lies entirely outside the band.")
A("                A discrepancy larger than delta is DEMONSTRATED.")
A("  INCONCLUSIVE  CI(R) straddles a boundary.  The run is too noisy to")
A("                decide at this delta -- not a defect, just no information.")
A("")
A("Separating INCONCLUSIVE from DIFFERENT is the whole point: under the")
A("indistinguishability metric those two were both counted as 'agreement',")
A("which is why noisy problems scored well and precise ones scored badly.")
A("")
A("")
A("3. PER-PROBLEM RESULTS")
A(SUB)
A("")
for d in DELTAS:
    t = int(100 * d)
    A("Tolerance delta = %d %%" % t)
    A("")
    h = ("%-22s %5s   %6s %6s %6s   %-18s  %7s" %
         ("Problem", "bins", "EQUIV", "DIFF", "INCONC", "95% CI on EQUIV frac",
          "|d|<%d%%" % t))
    A(h)
    A("-" * len(h))
    for s in summary:
        n = s["n"]
        lo, hi = wilson(s["eq%d" % t], n)
        A("%-22s %5d   %6d %6d %6d   [%5.1f%%, %5.1f%%]   %7s" % (
            s["key"], n, s["eq%d" % t], s["df%d" % t], s["ic%d" % t],
            100 * lo, 100 * hi, pc(s["pt%d" % t] / n) if n else "n/a"))
    A("-" * len(h))
    lo, hi = wilson(TOT["eq%d" % t], N)
    A("%-22s %5d   %6d %6d %6d   [%5.1f%%, %5.1f%%]   %7s" % (
        "ALL POOLED", N, TOT["eq%d" % t], TOT["df%d" % t], TOT["ic%d" % t],
        100 * lo, 100 * hi, pc(TOT["pt%d" % t] / N)))
    A("")
    A("  pooled EQUIV fraction          : %s   95%% CI [%.1f%%, %.1f%%]" % (
        pc(TOT["eq%d" % t] / N), 100 * lo, 100 * hi))
    E = EQW5 if d == 0.05 else EQW10
    A("  equal weight per problem       : %s   sd %.1f%%   95%% CI [%.1f%%, %.1f%%]" % (
        pc(E[0]), 100 * E[1], 100 * E[2], 100 * E[3]))
    A("  conventional TOST (90%% CI)      : %s pooled" % pc(TOT["eq%d_90" % t] / N))
    A("")
    A("")

A("4. THE THREE METRICS SIDE BY SIDE")
A(SUB)
A("")
A("Same bins, same sigmas, three different questions.  Note how the ordering")
A("of the problems changes completely between columns.")
A("")
h = ("%-22s %5s   %9s %9s %9s %9s" %
     ("Problem", "bins", "indisting", "equiv 5%", "equiv 10%", "mean |d|"))
A(h)
A("-" * len(h))
for s in summary:
    n = s["n"]
    A("%-22s %5d   %9s %9s %9s %8.2f%%" % (
        s["key"], n,
        pc(s["indis"] / s["n_indis"]) if s["n_indis"] else "n/a",
        pc(s["eq5"] / n), pc(s["eq10"] / n), s["mean_abs_d"]))
A("-" * len(h))
A("%-22s %5d   %9s %9s %9s %8.2f%%" % (
    "ALL POOLED", N, pc(INDIS / N), pc(TOT["eq5"] / N), pc(TOT["eq10"] / N), MEAN_ABS))
A("")
A("Demonstrably DIFFERENT by more than  5 %%: %s of bins" % pc(TOT["df5"] / N))
A("Demonstrably DIFFERENT by more than 10 %%: %s of bins" % pc(TOT["df10"] / N))
A("")
A("Mean |relative difference| over all %d bins : %.2f %%" % (N, MEAN_ABS))
A("Median |relative difference|                : %.2f %%" % MED_ABS)
A("")
A("Read the two slab problems against each other to see the effect:")
for k in ("MM Slab Collim Beam", "MM Slab Mesh Tally"):
    s = next(x for x in summary if x["key"] == k)
    A("  %-20s  indisting %6s   equiv@5%% %6s   equiv@10%% %6s   mean |d| %5.2f%%" % (
        k, pc(s["indis"] / s["n_indis"]), pc(s["eq5"] / s["n"]),
        pc(s["eq10"] / s["n"]), s["mean_abs_d"]))
A("")
A("The collimated-beam slab is 'indistinguishable' in 0 of 4 bins yet")
A("demonstrably equivalent within 5 % in most of them: its sigmas are so")
A("small (~0.16 %) that a sub-percent difference is resolvable, which the")
A("significance test reads as failure and the equivalence test reads as a")
A("tight, well-located agreement.  That is the metric artefact in one line.")
A("")
A("")
A("4b. RESTRICTED TO BINS MCNP ITSELF CALLS RELIABLE")
A(SUB)
A("")
A("The paper already cites MCNP's 10 % reliability threshold.  Applying it as")
A("a pre-declared screen -- keeping only bins where BOTH codes report a")
A("relative error <= 10 % -- removes the bins that carry no information, and")
A("removes them by a published criterion rather than an ad hoc one.")
A("")
_rel = {}
for _s in summary:
    _recs = [r for r in rows_by_problem[_s["key"]]
             if r["sM"] / r["fM"] <= 0.10 and r["sN"] / r["fN"] <= 0.10]
    _rel[_s["key"]] = _recs
h = ("%-22s %5s   %9s %9s %9s %9s" %
     ("Problem", "bins", "indisting", "equiv 5%", "equiv 10%", "mean |d|"))
A(h)
A("-" * len(h))
_tn = _te5 = _te10 = _td5 = _ti = 0
for _s in summary:
    _recs = _rel[_s["key"]]
    if not _recs:
        continue
    _n = len(_recs)
    _e5 = sum(1 for r in _recs if r["v5"] == "EQUIV")
    _e10 = sum(1 for r in _recs if r["v10"] == "EQUIV")
    _d5 = sum(1 for r in _recs if r["v5"] == "DIFF")
    _i = sum(1 for r in _recs if r["indis"])
    _md = float(np.mean([abs(r["d_pct"]) for r in _recs]))
    _tn += _n; _te5 += _e5; _te10 += _e10; _td5 += _d5; _ti += _i
    A("%-22s %5d   %9s %9s %9s %8.2f%%" % (
        _s["key"], _n, pc(_i / _n), pc(_e5 / _n), pc(_e10 / _n), _md))
A("-" * len(h))
A("%-22s %5d   %9s %9s %9s" % ("ALL RELIABLE", _tn, pc(_ti / _tn),
                               pc(_te5 / _tn), pc(_te10 / _tn)))
_l5, _h5 = wilson(_te5, _tn)
_l10, _h10 = wilson(_te10, _tn)
A("")
A("  %d of %d bins dropped as unreliable in one or both codes." % (N - _tn, N))
A("  equivalent within  5 %%: %s   95%% CI [%.1f%%, %.1f%%]" % (
    pc(_te5 / _tn), 100 * _l5, 100 * _h5))
A("  equivalent within 10 %%: %s   95%% CI [%.1f%%, %.1f%%]" % (
    pc(_te10 / _tn), 100 * _l10, 100 * _h10))
A("  demonstrably different by >5 %%: %s" % pc(_td5 / _tn))
A("")
A("  The screen barely moves the pooled numbers (%s -> %s at delta = 5 %%)" % (
    pc(TOT["eq5"] / N), pc(_te5 / _tn)))
A("  because the mesh tally dominates the bin count and all 200 of its bins")
A("  are well resolved -- its disagreement is a real offset, not noise.  It")
A("  does clean up the two Pb spheres and the cylinder substantially.")
A("")
A("")
A("5. HOW TO STATE THIS IN THE PAPER")
A(SUB)
A("")
A("Defensible, and all three from the same analysis:")
A("")
A("  * Mean absolute flux difference across all %d comparable bins is %.1f %%," % (N, MEAN_ABS))
A("    median %.1f %%." % MED_ABS)
A("  * %s of bins are demonstrably equivalent within 10 %% at 95 %%" % pc(TOT["eq10"] / N))
A("    confidence; %s within 5 %%." % pc(TOT["eq5"] / N))
A("  * %s of bins are statistically indistinguishable, but this metric is" % pc(INDIS / N))
A("    depressed by the high-precision runs and should be reported WITH the")
A("    equivalence result, not instead of it.")
A("")
A("Avoid: 'results within 5 % of MCNP' stated as a bound.  It is not a bound")
A("-- the largest differences reach %.0f %%.  It is true of the MEAN." % max(s["max_abs_d"] for s in summary))
A("")
A("")
A("6. PER-BIN DETAIL")
A(SUB)
for s in summary:
    A("")
    A("")
    A("%s -- %s" % (s["key"], s["title"]))
    A("  bins %d   EQUIV@5%% %d   EQUIV@10%% %d   mean |d| %.2f %%   max |d| %.2f %%" % (
        s["n"], s["eq5"], s["eq10"], s["mean_abs_d"], s["max_abs_d"]))
    A("")
    A("  %-26s %11s %11s %9s %9s %8s %7s %7s" % (
        "bin", "ratio R", "d [%]", "CI lo", "CI hi", "nu_eff", "v@5%", "v@10%"))
    A("  " + "-" * 102)
    for r in rows_by_problem[s["key"]]:
        A("  %-26s %11.5f %10.3f%% %9.5f %9.5f %8.1f %7s %7s" % (
            r["label"], r["R"], r["d_pct"], r["lo"], r["hi"],
            min(r["nu_eff"], 99999999.0), r["v5"], r["v10"]))

A("")
A("")
A(BAR)
A("END")
A(BAR)

open(OUT, "w").write("\n".join(L))
print("wrote", OUT)
print()
h = "%-22s %5s %10s %10s %10s %9s" % ("Problem", "bins", "indisting", "equiv5", "equiv10", "mean|d|")
print(h)
print("-" * len(h))
for s in summary:
    print("%-22s %5d %10s %10s %10s %8.2f%%" % (
        s["key"], s["n"], pc(s["indis"] / s["n_indis"]),
        pc(s["eq5"] / s["n"]), pc(s["eq10"] / s["n"]), s["mean_abs_d"]))
print("-" * len(h))
print("%-22s %5d %10s %10s %10s %8.2f%%" % (
    "ALL POOLED", N, pc(INDIS / N), pc(TOT["eq5"] / N), pc(TOT["eq10"] / N), MEAN_ABS))
print()
for d in DELTAS:
    t = int(100 * d)
    lo, hi = wilson(TOT["eq%d" % t], N)
    E = EQW5 if d == 0.05 else EQW10
    print("delta=%2d%%  pooled EQUIV %s CI [%.1f%%, %.1f%%] | DIFF %s | INCONC %s | eq-weight %s CI [%.1f%%, %.1f%%]" % (
        t, pc(TOT["eq%d" % t] / N), 100 * lo, 100 * hi,
        pc(TOT["df%d" % t] / N), pc(TOT["ic%d" % t] / N),
        pc(E[0]), 100 * E[2], 100 * E[3]))
print("mean |d| %.2f%%  median |d| %.2f%%" % (MEAN_ABS, MED_ABS))
