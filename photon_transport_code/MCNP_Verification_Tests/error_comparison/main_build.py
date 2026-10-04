# -*- coding: utf-8 -*-
"""Main driver: writes photon_standard_error_comparison.xlsx."""
import os
import numpy as np
import xlsxwriter
from build_se_workbook import *          # noqa: F401,F403
from build_se_workbook import (
    page_setup,
    BASE, R1E7, RCONV, XLSB, OUT, Z95, SHELLS, make_formats, w, verdict,
    zstat, pdiff, ratio, summary_block, write_banner, sheet_sphere,
    parse_xlsb_sphere, parse_mcdc_cylinder, parse_mcnp_cell_tally,
    parse_mcdc_slabs, parse_mcdc_mesh, parse_mcnp_mesh,
    parse_mcdc_spectrum, parse_mcnp_spectrum,
)

wb = xlsxwriter.Workbook(OUT, {"nan_inf_to_errors": True})
F = make_formats(wb)
overview = []          # (sheet, problem, mcdc_n, mcnp_n, stats dict, note)

# =====================================================================
# 0. README placeholder (filled at the end so it sits first)
# =====================================================================
ws_readme = wb.add_worksheet("README")

# =====================================================================
# 1-4. Al / Pb spheres, 1e6 histories (from the .xlsb)
# =====================================================================
SPHERES = [
    ("Al 1 MeV", "Al 1 MeV", "Aluminum sphere, 1.0 MeV isotropic point source (R = 40 cm)"),
    ("Al 10 MeV", "Al 10 MeV", "Aluminum sphere, 10.0 MeV isotropic point source (R = 40 cm)"),
    ("Pb 1 MeV", "Pb 1 MeV", "Lead sphere, 1.0 MeV isotropic point source (R = 40 cm)"),
    ("Pb 10 MeV", "Pb 10 MeV", "Lead sphere, 10.0 MeV isotropic point source (R = 40 cm)"),
]
_REPO_MCNP = os.path.join(
    BASE, "..", "MCNP_test_problems", "mcnp_outputs",
    "pb_10mev_sphere_MCNP_nobrem.out")
BENCH3_NOBREM = (
    os.path.normpath(_REPO_MCNP) if os.path.exists(_REPO_MCNP)
    else os.path.join(os.path.expanduser("~"), "Downloads", "bench3-nobrem.out"))

# Per-sheet history labels, plus the Pb 10 MeV MCNP override. The .xlsb's MCNP
# rel-err column for Pb 10 MeV was not that problem's error column; it is
# replaced here with the real one from the TTB-off MCNP output, whose 20 fluxes
# match the .xlsb column exactly.
NOTE_BOTH_1E6 = ("Both codes run with 1x10^6 histories.  Track-length flux "
                 "averaged over each 2 cm spherical shell, reported at the "
                 "volume-averaged radius.")
NOTE_PB10 = ("Both codes run with 1x10^6 histories.  Track-length flux "
             "averaged over each 2 cm spherical shell, reported at the "
             "volume-averaged radius.")
L_MCDC6 = "MC/DC (1×10⁶ histories)"
L_MCDC5 = "MC/DC (1×10⁵ histories)"
L_MCNP6 = "MCNP (1×10⁶ histories)"
L_MCNP6T = "MCNP (1×10⁶ histories, TTB off)"

SPHERE_CFG = {
    "Al 1 MeV":  dict(note=NOTE_BOTH_1E6, mcdc=L_MCDC6, mcnp=L_MCNP6,
                      hist=("1e6", "1e6")),
    "Al 10 MeV": dict(note=NOTE_BOTH_1E6, mcdc=L_MCDC6, mcnp=L_MCNP6,
                      hist=("1e6", "1e6")),
    "Pb 1 MeV":  dict(note=NOTE_BOTH_1E6, mcdc=L_MCDC6, mcnp=L_MCNP6,
                      hist=("1e6", "1e6")),
    "Pb 10 MeV": dict(note=NOTE_PB10, mcdc=L_MCDC6, mcnp=L_MCNP6T,
                      hist=("1e6", "1e6"), override=BENCH3_NOBREM),
}

for sheet_src, sheet_out, title in SPHERES:
    rows = parse_xlsb_sphere(sheet_src)
    cfg = SPHERE_CFG[sheet_out]
    extra = []
    if cfg.get("override"):
        mcnp_new = parse_mcnp_sphere_out(cfg["override"])
        if len(mcnp_new) != len(rows):
            raise RuntimeError("MCNP override has %d cells, sheet has %d rows"
                               % (len(mcnp_new), len(rows)))
        for row, (f_new, e_new) in zip(rows, mcnp_new):
            row["mcnp_flux"] = f_new
            row["mcnp_re"] = e_new if f_new > 0 else None
        extra = [
            ("MCNP flux AND relative error on this sheet come from "
             "bench3-nobrem.out: nps = 1x10^6, with 'phys:p j 1' so thick-target "
             "bremsstrahlung is OFF (0 brem tracks, 813,670 pair-production "
             "events). All 20 of its fluxes match the .xlsb column exactly, "
             "confirming it is the run behind those numbers.", "note"),
            ("REPLACED: the .xlsb's own MCNP rel-err column for this problem "
             "(0.0005, 0.0009, 0.0010 ... 0.0021) stayed flat across 9.8 decades "
             "of flux falloff and assigned 0.19-0.21 % error to bins of exactly "
             "zero flux, so it was not this problem's error column. The real "
             "one runs 0.03 % to 100 %.", "warn"),
        ]
    ws, r, stats, swidths = sheet_sphere(
        wb, F, sheet_out,
        "%s  -  MC/DC vs MCNP standard error  (paper Fig. 5 / Table I)" % title,
        rows, cfg["note"], cfg["mcdc"], cfg["mcnp"], extra,
    )
    r, st = summary_block(ws, F, r, stats, "shells", swidths)
    overview.append((sheet_out, title, cfg["hist"][0], cfg["hist"][1], st, ""))



# =====================================================================
# 5. Pb finite cylinder, off-center source
# =====================================================================
mcdc_cyl = parse_mcdc_cylinder(os.path.join(R1E7, "lead_finite_cylinder_2e8_results.txt"))
mcnp_cyl, cyl_vols, cyl_nps = parse_mcnp_cell_tally(
    os.path.join(R1E7, "lead_finite_cylinder_off_center_MCNP-big.out")
)
ws = wb.add_worksheet("Pb Cylinder Off-Ctr")
hdr = [("r shell", 8), ("z seg", 7), ("r_in\n[cm]", 8), ("r_out\n[cm]", 8),
       ("z_lo\n[cm]", 8), ("z_hi\n[cm]", 8), ("Volume\n[cm^3]", 11),
       ("MC/DC Flux\n[1/cm²]", 14), ("MC/DC\n1σ [1/cm²]", 14),
       ("MC/DC\nRel Err [%]", 11),
       ("MCNP cell", 9), ("MCNP Flux\n[1/cm²]", 14),
       ("MCNP\n1σ [1/cm²]", 14), ("MCNP\nRel Err [%]", 11),
       ("Rel Err ratio\nMC/DC ÷ MCNP", 13),
       ("Flux diff\n(MC/DC−MCNP)/MCNP [%]", 15),
       ("z = diff /\nσ_combined", 11), ("Agree at\n95% CI?", 10)]
top = write_banner(
    ws, F,
    "Pb finite cylinder (R = 20 cm, H = 40 cm), off-centre 1.0 MeV isotropic "
    "point source  -  paper Fig. 6",
    [("MC/DC: 1e7_results/lead_finite_cylinder_2e8_results.txt   (2x10^7 x 10 batches = 2x10^8 histories)", "note"),
     ("MCNP : 1e7_results/lead_finite_cylinder_off_center_MCNP-big.out   (nps = %d)" % cyl_nps, "note"),
     ("MC/DC region (ir,iz) maps to MCNP cell id = 10*(ir+1) + (iz+1); cell volumes agree to 6 figures.", "note"),
     ("MATCHED STATISTICS: both codes ran 2x10^8 histories, so the two "
      "relative errors are directly comparable with no sqrt(N) correction. "
      "This replaces the earlier 1x10^8 MC/DC run, which was mismatched "
      "against MCNP's 2x10^8 by a factor of 2.", "note")],
    hdr,
)
ws.merge_range(top, 0, top, 6, "Region definition", F["grpG"])
ws.merge_range(top, 7, top, 9, "MC/DC", F["grpA"])
ws.merge_range(top, 10, top, 13, "MCNP", F["grpB"])
ws.merge_range(top, 14, top, 17, "Comparison", F["grpC"])
hr = top + 1
for i, (h, width) in enumerate(hdr):
    ws.write(hr, i, h, F["hdr"]); ws.set_column(i, i, width)
ws.set_row(hr, 32)
ws.freeze_panes(hr + 1, 2)
page_setup(ws, hdr, hr)
r = hr + 1
stats = []
for row in mcdc_cyl:
    cell = 10 * (row["ir"] + 1) + (row["iz"] + 1)
    nf, nre = mcnp_cyl.get(cell, (None, None))
    nsig = nf * nre if nf is not None else None
    mf, msig = row["flux"], row["sig"]
    mre = msig / mf if mf else None
    z = zstat(mf, msig, nf, nsig)
    vals = [row["ir"], row["iz"], row["r_in"], row["r_out"], row["z_lo"],
            row["z_hi"], row["vol"], mf, msig,
            None if mre is None else mre * 100, cell, nf, nsig,
            None if nre is None else nre * 100,
            ratio(mre, nre), pdiff(mf, nf), z]
    fmts = [F["ctr"], F["ctr"], F["num"], F["num"], F["num"], F["num"],
            F["sci"], F["sci"], F["sci"], F["pct"], F["ctr"], F["sci"],
            F["sci"], F["pct"], F["rat"], F["pct2"], F["rat"]]
    for i, (v, fm) in enumerate(zip(vals, fmts)):
        w(ws, r, i, v, fm)
    verdict(ws, r, 17, z, F)
    if z is not None:
        stats.append((mre, nre, z))
    r += 1
r, st = summary_block(ws, F, r, stats, "regions", [x[1] for x in hdr])
ws.write(r + 1, 0,
         "4 of the 16 regions (all of z-segment iz=3, z = 10-20 cm) tallied zero "
         "flux in BOTH codes and have no defined error; they are excluded from the "
         "paper figure and from the summary above. At 2x10^8 histories MC/DC now "
         "resolves region (r3,z2), which scored zero in the earlier 1x10^8 run, so "
         "that region is a real comparison here instead of a -100 % entry.", F["note"])
overview.append(("Pb Cylinder Off-Ctr",
                 "Pb finite cylinder, off-centre 1 MeV point source",
                 "2e8", "2e8", st, ""))

# =====================================================================
# 6. Multi-material slab, collimated beam
# =====================================================================
mcdc_sl = parse_mcdc_slabs(os.path.join(R1E7, "mm_slabs_collimated_beam_results.txt"))
mcnp_sl, sl_vols, sl_nps = parse_mcnp_cell_tally(
    os.path.join(R1E7, "multi_material_slabs_collimated_beam_MCNP-big.out")
)
ws = wb.add_worksheet("MM Slab Collim Beam")
hdr = [("Slab", 6), ("Material", 10), ("z_front\n[cm]", 9), ("z_back\n[cm]", 9),
       ("Thickness\n[cm]", 10),
       ("MC/DC Flux\n[1/cm²]", 14), ("MC/DC\n1σ [1/cm²]", 14),
       ("MC/DC\nRel Err [%]", 11),
       ("MCNP cell", 9), ("MCNP area\n[cm²]", 10),
       ("MCNP Flux\n(scaled) [1/cm²]", 15),
       ("MCNP 1σ\n(scaled) [1/cm²]", 15), ("MCNP\nRel Err [%]", 11),
       ("Rel Err ratio\nMC/DC ÷ MCNP", 13),
       ("Flux diff\n(MC/DC−MCNP)/MCNP [%]", 15),
       ("z = diff /\nσ_combined", 11), ("Agree at\n95% CI?", 10)]
top = write_banner(
    ws, F,
    "Multi-material slab (Pb / water / concrete / air), 1.0 MeV collimated beam "
    "-  paper Fig. 7",
    [("MC/DC: 1e7_results/mm_slabs_collimated_beam_results.txt   (1x10^7 x 10 batches = 1x10^8 histories)", "note"),
     ("MCNP : 1e7_results/multi_material_slabs_collimated_beam_MCNP-big.out   (nps = %d)" % sl_nps, "note"),
     ("NORMALISATION: MC/DC scores track length per 1 cm^2 of beam; the MCNP deck "
      "uses a 100 x 100 cm slab, so MCNP flux and 1 sigma are multiplied by the "
      "transverse area (volume / thickness = 1.0e4 cm^2) before comparison. "
      "Relative errors are unaffected by this rescaling.", "note"),
     ("NOTE: MCNP ran 1x10^8 histories and MC/DC 1x10^8 - history counts match here.", "note")],
    hdr,
)
ws.merge_range(top, 0, top, 4, "Slab definition", F["grpG"])
ws.merge_range(top, 5, top, 7, "MC/DC", F["grpA"])
ws.merge_range(top, 8, top, 12, "MCNP (area-rescaled)", F["grpB"])
ws.merge_range(top, 13, top, 16, "Comparison", F["grpC"])
hr = top + 1
for i, (h, width) in enumerate(hdr):
    ws.write(hr, i, h, F["hdr"]); ws.set_column(i, i, width)
ws.set_row(hr, 32)
ws.freeze_panes(hr + 1, 2)
page_setup(ws, hdr, hr)
r = hr + 1
stats = []
for row in mcdc_sl:
    cell = row["slab"] + 2
    nf_raw, nre = mcnp_sl[cell]
    area = sl_vols[cell] / row["thk"]
    nf = nf_raw * area
    nsig = nf * nre
    mf, msig = row["flux"], row["sig"]
    mre = msig / mf
    z = zstat(mf, msig, nf, nsig)
    vals = [row["slab"], row["mat"], row["z0"], row["z1"], row["thk"],
            mf, msig, mre * 100, cell, area, nf, nsig, nre * 100,
            ratio(mre, nre), pdiff(mf, nf), z]
    fmts = [F["ctr"], F["txt"], F["num"], F["num"], F["num"], F["sci"],
            F["sci"], F["pct"], F["ctr"], F["sci"], F["sci"], F["sci"],
            F["pct"], F["rat"], F["pct2"], F["rat"]]
    for i, (v, fm) in enumerate(zip(vals, fmts)):
        w(ws, r, i, v, fm)
    verdict(ws, r, 16, z, F)
    stats.append((mre, nre, z))
    r += 1
r, st = summary_block(ws, F, r, stats, "slabs", [x[1] for x in hdr])
overview.append(("MM Slab Collim Beam",
                 "Multi-material slab, 1 MeV collimated beam",
                 "1e8", "1e8", st, ""))

# =====================================================================
# 7. Multi-material slab, mesh tally
# =====================================================================
mcdc_me = parse_mcdc_mesh(os.path.join(R1E7, "multi_material_slabs_mesh_tally_results.txt"))
area_me, mcnp_me, me_nps = parse_mcnp_mesh(os.path.join(R1E7, "meshtam"))
ws = wb.add_worksheet("MM Slab Mesh Tally")
hdr = [("z_mid\n[cm]", 9), ("Material", 11),
       ("MC/DC Flux\n[1/cm²]", 14), ("MC/DC\n1σ [1/cm²]", 14),
       ("MC/DC\nRel Err [%]", 11),
       ("MCNP Flux\n(scaled) [1/cm²]", 15),
       ("MCNP 1σ\n(scaled) [1/cm²]", 15), ("MCNP\nRel Err [%]", 11),
       ("Rel Err ratio\nMC/DC ÷ MCNP", 13),
       ("Flux diff\n(MC/DC−MCNP)/MCNP [%]", 15),
       ("z = diff /\nσ_combined", 11), ("Agree at\n95% CI?", 10)]
top = write_banner(
    ws, F,
    "Multi-material slab (Pb / water / concrete / air), 1.0 MeV isotropic point "
    "source, mesh tally  -  paper Fig. 8",
    [("MC/DC: 1e7_results/multi_material_slabs_mesh_tally_results.txt   (1x10^7 x 10 batches = 1x10^8 histories)", "note"),
     ("MCNP : 1e7_results/meshtam  (FMESH4 output of multi_material_slabs_mesh_tally_MCNP-big.out, nps = %d)" % int(me_nps), "note"),
     ("MCNP flux and 1 sigma multiplied by the transverse mesh area "
      "(%.0f cm^2) to match MC/DC's 1 cm^2 convention; relative errors unaffected." % area_me, "note"),
     ("The first bin (z_mid = -0.5 cm, the vacuum backing gap behind the source) "
      "is reported here but is OUTSIDE the depth range plotted in Fig. 8.", "note")],
    hdr,
)
ws.merge_range(top, 0, top, 1, "Mesh bin", F["grpG"])
ws.merge_range(top, 2, top, 4, "MC/DC", F["grpA"])
ws.merge_range(top, 5, top, 7, "MCNP (area-rescaled)", F["grpB"])
ws.merge_range(top, 8, top, 11, "Comparison", F["grpC"])
hr = top + 1
for i, (h, width) in enumerate(hdr):
    ws.write(hr, i, h, F["hdr"]); ws.set_column(i, i, width)
ws.set_row(hr, 32)
ws.freeze_panes(hr + 1, 2)
page_setup(ws, hdr, hr)
r = hr + 1
stats = []
for row in mcdc_me:
    key = round(row["z"], 3)
    if key not in mcnp_me:
        continue
    nf_raw, nre = mcnp_me[key]
    nf, nsig = nf_raw * area_me, nf_raw * area_me * nre
    mf, msig = row["flux"], row["sig"]
    mre = msig / mf if mf else None
    z = zstat(mf, msig, nf, nsig)
    vals = [row["z"], row["mat"], mf, msig, None if mre is None else mre * 100,
            nf, nsig, nre * 100, ratio(mre, nre), pdiff(mf, nf), z]
    fmts = [F["num"], F["txt"], F["sci"], F["sci"], F["pct"], F["sci"],
            F["sci"], F["pct"], F["rat"], F["pct2"], F["rat"]]
    for i, (v, fm) in enumerate(zip(vals, fmts)):
        w(ws, r, i, v, fm)
    verdict(ws, r, 11, z, F)
    if z is not None and row["z"] > 0:
        stats.append((mre, nre, z))
    r += 1
r, st = summary_block(ws, F, r, stats, "mesh bins", [x[1] for x in hdr])
ws.write(r + 1, 0, "Summary covers the 200 bins at z > 0 (the range plotted in "
                   "Fig. 8); the backing-gap bin at z = -0.5 cm is excluded.",
         F["note"])
overview.append(("MM Slab Mesh Tally",
                 "Multi-material slab, 1 MeV point source, mesh tally",
                 "1e8", "1e8", st, ""))

# =====================================================================
# 8. Multi-material sphere, 1-10 MeV spectrum (matched 1e8 vs 1e8)
# =====================================================================
edges, sf, ss, rv = parse_mcdc_spectrum(
    os.path.join(RCONV, "mm_spheres_1to10mev_spec_1e8_results.txt"))
nbins = sf.shape[1]
nf_all, nre_all, nvols, sp_nps = parse_mcnp_spectrum(
    os.path.join(RCONV, "multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out"), nbins)

ws = wb.add_worksheet("MM Sphere Spectrum")
hdr = [("Region", 7), ("Material", 10), ("r_in\n[cm]", 8), ("r_out\n[cm]", 8),
       ("r_vavg\n[cm]", 9), ("E bin", 7), ("E_lo\n[MeV]", 10), ("E_hi\n[MeV]", 10),
       ("MC/DC Flux\n[1/cm²]", 14), ("MC/DC\n1σ [1/cm²]", 14),
       ("MC/DC\nRel Err [%]", 11),
       ("MCNP cell", 9), ("MCNP Flux\n[1/cm²]", 14),
       ("MCNP\n1σ [1/cm²]", 14), ("MCNP\nRel Err [%]", 11),
       ("Rel Err ratio\nMC/DC ÷ MCNP", 13),
       ("Flux diff\n(MC/DC−MCNP)/MCNP [%]", 15),
       ("z = diff /\nσ_combined", 11), ("Agree at\n95% CI?", 10),
       ("Comparable?", 12)]
top = write_banner(
    ws, F,
    "Multi-material sphere (Pb / Fe / concrete / water), 1-10 MeV uniform "
    "isotropic point source, energy-spectrum tally  -  paper Fig. 9",
    [("MC/DC: Convergence/mm_spheres_1to10mev_spec_1e8_results.txt   (1x10^7 x 10 batches = 1x10^8 histories)", "note"),
     ("MCNP : Convergence/multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out   (reports nps = %d = 1x10^8)" % sp_nps, "note"),
     ("MATCHED STATISTICS: both runs on this sheet used 1x10^8 histories, so "
      "the two relative errors are directly comparable with no sqrt(N) "
      "correction. The MCNP file keeps its '-1e9' name but its tally header "
      "reports nps = 1x10^8, which is why the 1e8 MC/DC file is the correct "
      "partner for it.", "note"),
     ("DIFFERS FROM Fig. 9: the published figure plotted the 1x10^9 MC/DC run "
      "against this same 1x10^8 MCNP file, so its fluxes differ slightly from "
      "the ones here and its error comparison was not like-for-like. This "
      "sheet deliberately uses the matched 1x10^8 pair instead, so the "
      "standard-error comparison is on equal footing.", "warn"),
     ("Energy bin 1 (0.0100-0.0119 MeV) is NOT comparable: MCNP's first tally "
      "interval runs from 0 to 0.011885 MeV whereas MC/DC's starts at 0.01 MeV. "
      "It is flagged below and excluded from the summary (same treatment as the "
      "paper's comparison script).", "warn"),
     ("Region r (0-11) maps to MCNP cell r+1; shell volumes agree with MCNP's "
      "reported volumes to 6 figures.", "note")],
    hdr,
)
ws.merge_range(top, 0, top, 7, "Tally bin definition", F["grpG"])
ws.merge_range(top, 8, top, 10, "MC/DC (1e8 histories)", F["grpA"])
ws.merge_range(top, 11, top, 14, "MCNP (1e8 histories)", F["grpB"])
ws.merge_range(top, 15, top, 19, "Comparison", F["grpC"])
hr = top + 1
for i, (h, width) in enumerate(hdr):
    ws.write(hr, i, h, F["hdr"]); ws.set_column(i, i, width)
ws.set_row(hr, 32)
ws.freeze_panes(hr + 1, 2)
page_setup(ws, hdr, hr)
r = hr + 1
stats = []
for reg in range(12):
    mat, r0, r1 = SHELLS[reg]
    for b in range(nbins):
        mf, msig = float(sf[reg, b]), float(ss[reg, b])
        nf, nre = float(nf_all[reg, b]), float(nre_all[reg, b])
        nsig = nf * nre
        mre = msig / mf if mf else None
        comparable = (b > 0)
        z = zstat(mf, msig, nf, nsig) if comparable else None
        vals = [reg, mat, r0, r1, rv[reg], b + 1, edges[b], edges[b + 1],
                mf, msig, None if mre is None else mre * 100,
                reg + 1, nf, nsig, nre * 100,
                ratio(mre, nre) if comparable else None,
                pdiff(mf, nf) if comparable else None, z]
        fmts = [F["ctr"], F["txt"], F["num"], F["num"], F["num"], F["ctr"],
                F["sci"], F["sci"], F["sci"], F["sci"], F["pct"], F["ctr"],
                F["sci"], F["sci"], F["pct"], F["rat"], F["pct2"], F["rat"]]
        for i, (v, fm) in enumerate(zip(vals, fmts)):
            w(ws, r, i, v, fm)
        if comparable:
            verdict(ws, r, 18, z, F)
            ws.write(r, 19, "yes", F["ctr"])
        else:
            ws.write(r, 18, "n/a", F["ctr"])
            ws.write(r, 19, "NO - bin edge", F["bad"])
        if z is not None:
            stats.append((mre, nre, z))
        r += 1
r, st = summary_block(ws, F, r, stats, "energy bins", [x[1] for x in hdr])
overview.append(("MM Sphere Spectrum",
                 "Multi-material sphere, 1-10 MeV source, energy spectrum",
                 "1e8", "1e8", st, ""))

# =====================================================================
# 8b. Same problem aggregated by material (the view plotted in Fig. 9)
# =====================================================================
vols = np.array([(4.0 / 3.0) * np.pi * (r1 ** 3 - r0 ** 3) for _, r0, r1 in SHELLS])
mats = ["lead", "iron", "concrete", "water"]
ws = wb.add_worksheet("MM Sphere by Material")
hdr = [("Material", 10), ("E bin", 7), ("E_lo\n[MeV]", 10), ("E_hi\n[MeV]", 10),
       ("MC/DC Flux\n[1/cm²]", 14), ("MC/DC\n1σ [1/cm²]", 14),
       ("MC/DC\nRel Err [%]", 11),
       ("MCNP Flux\n[1/cm²]", 14), ("MCNP\n1σ [1/cm²]", 14),
       ("MCNP\nRel Err [%]", 11),
       ("Rel Err ratio\nMC/DC ÷ MCNP", 13),
       ("Flux diff\n(MC/DC−MCNP)/MCNP [%]", 15),
       ("z = diff /\nσ_combined", 11), ("Agree at\n95% CI?", 10),
       ("Comparable?", 12)]
top = write_banner(
    ws, F,
    "Multi-material sphere spectrum, volume-weighted by material  -  exactly the "
    "quantity plotted in paper Fig. 9",
    [("flux_material = sum(flux_shell * V_shell) / sum(V_shell) over the 3 shells "
      "of each material; 1 sigma combined in quadrature with the same weights.", "note"),
     ("Same source files as sheet 'MM Sphere Spectrum': the matched 1x10^8 "
      "MC/DC and 1x10^8 MCNP runs.", "note")],
    hdr,
)
ws.merge_range(top, 0, top, 3, "Bin", F["grpG"])
ws.merge_range(top, 4, top, 6, "MC/DC (1e8)", F["grpA"])
ws.merge_range(top, 7, top, 9, "MCNP (1e8)", F["grpB"])
ws.merge_range(top, 10, top, 14, "Comparison", F["grpC"])
hr = top + 1
for i, (h, width) in enumerate(hdr):
    ws.write(hr, i, h, F["hdr"]); ws.set_column(i, i, width)
ws.set_row(hr, 32)
ws.freeze_panes(hr + 1, 1)
page_setup(ws, hdr, hr)
r = hr + 1
stats = []
for mi, mat in enumerate(mats):
    idx = [i for i, (m, _, _) in enumerate(SHELLS) if m == mat]
    V = vols[idx]
    Vt = V.sum()
    for b in range(nbins):
        mf = float((sf[idx, b] * V).sum() / Vt)
        msig = float(np.sqrt(((ss[idx, b] * V) ** 2).sum()) / Vt)
        nf = float((nf_all[idx, b] * V).sum() / Vt)
        nsig_sh = nf_all[idx, b] * nre_all[idx, b]
        nsig = float(np.sqrt(((nsig_sh * V) ** 2).sum()) / Vt)
        mre = msig / mf if mf else None
        nre = nsig / nf if nf else None
        comparable = (b > 0)
        z = zstat(mf, msig, nf, nsig) if comparable else None
        vals = [mat, b + 1, edges[b], edges[b + 1], mf, msig,
                None if mre is None else mre * 100, nf, nsig,
                None if nre is None else nre * 100,
                ratio(mre, nre) if comparable else None,
                pdiff(mf, nf) if comparable else None, z]
        fmts = [F["txt"], F["ctr"], F["sci"], F["sci"], F["sci"], F["sci"],
                F["pct"], F["sci"], F["sci"], F["pct"], F["rat"], F["pct2"],
                F["rat"]]
        for i, (v, fm) in enumerate(zip(vals, fmts)):
            w(ws, r, i, v, fm)
        if comparable:
            verdict(ws, r, 13, z, F)
            ws.write(r, 14, "yes", F["ctr"])
        else:
            ws.write(r, 13, "n/a", F["ctr"])
            ws.write(r, 14, "NO - bin edge", F["bad"])
        if z is not None:
            stats.append((mre, nre, z))
        r += 1
summary_block(ws, F, r, stats, "material-energy bins", [x[1] for x in hdr])

from readme_block import write_readme
write_readme(ws_readme, F, w, overview)

wb.close()
print("wrote", OUT)
for o in overview:
    print(o[0], "|", o[4])
import json
json.dump([[o[0], o[1], o[2], o[3], o[4], o[5]] for o in overview],
          open("overview.json", "w"), default=float)
