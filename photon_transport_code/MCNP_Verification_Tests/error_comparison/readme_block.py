# -*- coding: utf-8 -*-
"""Writes the README sheet. Imported by main_build.py (needs ws_readme, F, w, overview)."""


def _pr(ws, F, r, txt, fmt="wrap", c0=1, c1=10, cpl=172):
    """Merged, explicitly-heighted prose cell so Excel never auto-balloons it."""
    ws.merge_range(r, c0, r, c1, txt, F[fmt])
    nlines = max(1, -(-len(txt) // cpl))
    ws.set_row(r, 13.2 * nlines + 5)

def write_readme(ws, F, w, overview):
    ws.set_column(0, 0, 26)
    ws.set_column(1, 1, 56)
    ws.set_column(2, 2, 21)
    ws.set_column(3, 4, 14)
    ws.set_column(5, 10, 14)
    ws.set_landscape()
    ws.set_paper(1)
    ws.fit_to_pages(1, 0)
    ws.set_margins(0.3, 0.3, 0.4, 0.4)
    ws.merge_range(0, 0, 0, 10,
                   "MC/DC vs MCNP  -  standard-error comparison for every test "
                   "problem in the photon-transport paper", F["title"])
    ws.set_row(0, 24)
    r = 2
    ws.write(r, 0, "Purpose", F["bold"])
    _pr(ws, F, r, "One sheet per test problem. Each sheet lists, bin by bin, the "
                  "flux, the 1-sigma absolute standard error and the relative "
                  "error reported by BOTH codes, plus the ratio of the two "
                  "relative errors, the flux difference, and a z-score test of "
                  "whether the two codes agree inside their combined error bars.")
    r += 2
    ws.write(r, 0, "Definitions", F["bold"])
    r += 1
    for lab, txt in [
        ("Rel Err [%]", "100 x sigma / flux. MCNP writes this as a fraction in its "
                        "output; it is converted to percent everywhere here."),
        ("Rel Err ratio", "MC/DC relative error divided by MCNP relative error. "
                          "Greater than 1 means MC/DC is the noisier of the two in that bin."),
        ("sigma_combined", "sqrt(sigma_MCDC^2 + sigma_MCNP^2)."),
        ("z", "(flux_MCDC - flux_MCNP) / sigma_combined."),
        ("Agree at 95% CI?", "yes when |z| <= 1.96.  'n/a' when both codes report "
                             "a zero flux with zero error, so no test is possible."),
        ("Mean rel err (own resolved bins)",
         "Averaged over every bin in which THAT code resolved a nonzero flux and a "
         "nonzero sigma. It is a property of that code's own output file alone, so it "
         "does not move if the other code's file is swapped. A bin where a code scored "
         "nothing has an UNDEFINED relative error, not a zero one - MCNP prints 0.0000 "
         "and MC/DC can print a zero sdev when every score landed in one batch, and "
         "both are excluded."),
        ("Median rel-err ratio (paired bins)",
         "Median over the bins where BOTH codes resolved an error. Unlike the two means, "
         "this is inherently a paired statistic, so its bin set - and therefore its value - does depend on both files."),
        ("Per-sheet SUMMARY blocks",
         "Each sheet's SUMMARY reports BOTH forms: the paired means (like-for-like, over "
         "the bins both codes resolved) and the own-resolved-bins means, with the bin "
         "count each is based on."),
    ]:
        ws.write(r, 0, lab, F["txt"])
        _pr(ws, F, r, txt)
        r += 1
    r += 1

    ws.write(r, 0, "Sheet index and headline numbers", F["bold"])
    r += 1
    cols = ["Sheet", "Test problem", "Paper figure", "MC/DC histories",
            "MCNP histories", "Comparable bins",
            "Mean rel err MC/DC [%]\n(own resolved bins)",
            "Mean rel err MCNP [%]\n(own resolved bins)",
            "Median rel-err ratio\n(paired bins)", "Bins agreeing 95%",
            "Agreeing [%]"]
    for i, c in enumerate(cols):
        ws.write(r, i, c, F["hdr"])
    ws.set_row(r, 46)
    r += 1
    figmap = {
        "Al 1 MeV": "Fig. 5 / Table I", "Al 10 MeV": "Fig. 5 / Table I",
        "Pb 1 MeV": "Fig. 5 / Table I", "Pb 10 MeV": "Fig. 5 / Table I",
        "Pb Cylinder Off-Ctr": "Fig. 6", "MM Slab Collim Beam": "Fig. 7",
        "MM Slab Mesh Tally": "Fig. 8",
        "MM Sphere Spectrum": "Fig. 9 (matched 1e8)",
    }
    tot_n = tot_a = 0
    for sheet, title, mh, nh, st, note in overview:
        ws.write(r, 0, sheet, F["txt"])
        ws.write(r, 1, title, F["txt"])
        ws.write(r, 2, figmap.get(sheet, ""), F["ctr"])
        ws.write(r, 3, mh, F["ctr"])
        ws.write(r, 4, nh, F["bad"] if "MISMATCH" in note else F["ctr"])
        w(ws, r, 5, st["n"], F["ctr"])
        w(ws, r, 6, st["mcdc"], F["pct"])
        w(ws, r, 7, st["mcnp"], F["pct"])
        w(ws, r, 8, st["med_ratio"], F["rat"])
        w(ws, r, 9, st["agree"], F["ctr"])
        w(ws, r, 10, 100.0 * st["agree"] / st["n"], F["pct2"])
        tot_n += st["n"]
        tot_a += st["agree"]
        r += 1
    ws.write(r, 0, "ALL PROBLEMS", F["bold"])
    w(ws, r, 5, tot_n, F["ctr"])
    w(ws, r, 9, tot_a, F["ctr"])
    w(ws, r, 10, 100.0 * tot_a / tot_n, F["pct2"])
    r += 2

    ws.write(r, 0, "Source files used", F["bold"])
    r += 1
    sep = "\\"
    for lab, txt in [
        ("Al / Pb spheres",
         "For_Doug_Benchmarks 7-8-26 (version 1).xlsb, sheets 'Al 1 MeV', "
         "'Al 10 MeV', 'Pb 1 MeV', 'Pb 10 MeV'  -  the MC/DC and MCNP column "
         "pairs that reproduce Table I of the paper. EXCEPTION: the Pb 10 MeV MCNP "
         "flux and relative error come from bench3-nobrem.out (nps = 1x10^6, TTB off)."),
        ("Pb cylinder",
         "Complex_M&G" + sep + "1e7_results" + sep + "lead_finite_cylinder_2e8_results.txt   and   "
         "lead_finite_cylinder_off_center_MCNP-big.out"),
        ("Slab, collimated beam",
         "Complex_M&G" + sep + "1e7_results" + sep + "mm_slabs_collimated_beam_results.txt   and   "
         "multi_material_slabs_collimated_beam_MCNP-big.out"),
        ("Slab, mesh tally",
         "Complex_M&G" + sep + "1e7_results" + sep + "multi_material_slabs_mesh_tally_results.txt   and   "
         "meshtam (the FMESH4 output of multi_material_slabs_mesh_tally_MCNP-big.out)"),
        ("Sphere, 1-10 MeV",
         "Complex_M&G" + sep + "Convergence" + sep + "mm_spheres_1to10mev_spec_1e8_results.txt   and   "
         "multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out"),
    ]:
        ws.write(r, 0, lab, F["txt"])
        _pr(ws, F, r, txt)
        r += 1
    r += 1

    ws.write(r, 0, "Verification against the paper", F["bold"])
    r += 1
    for txt in [
        "Pb cylinder: the flux differences computed here (+0.29, +1.54, +15.50, "
        "+0.93, +1.50, +6.59, +2.11, +0.55, +6.17, -4.89, -5.40, -100 %) reproduce "
        "every label on Fig. 6 exactly, in the same region order.",
        "Collimated-beam slab: +0.32 / +0.86 / +2.29 / +8.24 % reproduce all four "
        "labels on Fig. 7 exactly.",
        "Mesh-tally slab: the difference profile peaks near 12.5 % at z = 120-130 cm "
        "and ends near 5.6 % at z = 199.5 cm, matching the lower panel of Fig. 8.",
        "Al / Pb spheres: all 560 flux and Rel Err cells on the four sphere sheets "
        "were re-read from For_Doug_Benchmarks 7-8-26 (version 1).xlsb and compared "
        "against this workbook cell by cell - zero mismatches, the only change being "
        "the fraction-to-percent unit conversion on Rel Err.",
        "Al / Pb spheres: the flux differences reproduce Table I of the paper to the "
        "printed precision, and the MC/DC relative errors reproduce the 66.7 % "
        "(Pb 10 MeV at 31.02 cm), 74.33 % (Pb 1 MeV at 19.035 cm) and 100 % "
        "(MCNP Pb 1 MeV at 23.029 cm) values quoted in section 3.2.",
        "Sphere spectrum: region-to-cell and energy-bin alignment follow the mapping "
        "used by compare_mcdc_mcnp_spectrum_1e9_postprocessed.py, the script that produced "
        "Fig. 9. The MCNP input file is the same one that script reads; the MC/DC file is "
        "deliberately the 1e8 run rather than the 1e9 run, so that both sides have the same "
        "1x10^8 histories (see caveat 1).",
    ]:
        _pr(ws, F, r, txt)
        r += 1
    r += 1

    ws.write(r, 0, "Caveats found while building this", F["bold"])
    r += 1
    for txt, fmt, h in [
        ("1. Sphere spectrum uses a MATCHED 1e8 / 1e8 pair, which is NOT what "
         "Fig. 9 plotted. The file multi_material_spheres_1to10mev_spectrum_MCNP-1e9.out "
         "keeps a '-1e9' name but its tally header reports nps = 100,000,000, i.e. "
         "1x10^8 histories. Fig. 9 paired that file with the 1x10^9 MC/DC run and "
         "titled the result 'Matched 1e9-History Runs', so the errors it compared were "
         "not like-for-like. This workbook instead pairs it with "
         "mm_spheres_1to10mev_spec_1e8_results.txt (1e7 x 10 batches = 1x10^8), so both "
         "sides really do have 1x10^8 histories and the two relative errors are "
         "directly comparable. The fluxes on that sheet therefore differ slightly from "
         "the ones drawn in Fig. 9. Related: the file named ...MCNP-1e8.out reports "
         "nps = 1x10^7, so the top two points of the convergence study may be "
         "mislabelled as well.", "warn", 74),
        ("2. The Pb cylinder is now a matched 2x10^8 / 2x10^8 comparison, using "
         "lead_finite_cylinder_2e8_results.txt (2x10^7 x 10 batches). The earlier "
         "1x10^8 MC/DC run was mismatched against MCNP's 2x10^8 by a factor of 2; "
         "with the counts matched the median rel-err ratio is 0.99. At 2x10^8 "
         "MC/DC also resolves region (r3,z2), which scored zero in the 1x10^8 run, "
         "so that region is a real comparison instead of a -100 % entry.",
         "note", 60),
        ("3. Provenance of the four sphere sheets. For 'Al 1 MeV', 'Al 10 MeV' and "
         "'Pb 1 MeV' the MC/DC and MCNP flux and Rel Err values are taken verbatim "
         "from For_Doug_Benchmarks 7-8-26 (version 1).xlsb, and all 560 source cells "
         "were re-read and verified against this workbook with zero mismatches; the "
         "only transformation is the fraction-to-percent unit change on Rel Err. "
         "FOR Pb 10 MeV THE MCNP SIDE IS DIFFERENT: its flux and relative error are "
         "taken from the MCNP output bench3-nobrem.out (nps = 1x10^6, 'phys:p j 1' so "
         "thick-target bremsstrahlung is off, 0 brem tracks, 813,670 pair-production "
         "events). All 20 of that file's fluxes match the .xlsb column exactly, which "
         "identifies it as the run behind those numbers, and it supplies the real "
         "error column (0.03 % to 100 %) in place of the .xlsb's, which was flat at "
         "0.05-0.21 % across 9.8 decades of flux falloff and quoted 0.19-0.21 % error "
         "on bins of exactly zero flux.", "note", 74),
        ("4. In the 'Al 10 MeV' and 'Pb 10 MeV' source sheets the MC/DC 1e6 '1 sigma' "
         "column is not consistent with the 'Rel Err' column in the same block (they "
         "disagree by factors of roughly 1.3 to 3). The 'Al 1 MeV' and 'Pb 1 MeV' "
         "sheets are self-consistent. This workbook treats Rel Err as authoritative "
         "(it is the column the paper quotes) and recomputes 1 sigma = flux x Rel Err; "
         "the stored 1 sigma is carried in its own column with a 'stored 1 sigma "
         "consistent?' flag so every affected row is visible.", "warn", 74),
        ("5. Normalisation. In both slab problems MC/DC scores track length per 1 cm^2 "
         "of beam while the MCNP decks use a 100 x 100 cm slab, so MCNP flux and "
         "1 sigma are multiplied by 1.0e4 before comparison. Relative errors, rel-err "
         "ratios and z-scores are unaffected by this rescaling.", "note", 46),
        ("6. Energy bin 1 of the sphere spectrum (0.0100-0.0119 MeV) is not comparable: "
         "MCNP's first tally interval runs from 0 MeV, MC/DC's from 0.01 MeV. It is "
         "flagged 'NO - bin edge' and excluded from the summaries, matching the "
         "treatment in the paper's own comparison script.", "note", 46),
        ("7. The 'ALL PROBLEMS' agreement fraction above is dominated by the 200-bin "
         "mesh tally, where a persistent 5-12 % flux offset leaves almost no bin "
         "statistically compatible. It is not the same statistic as the roughly 55 % "
         "quoted in the paper's abstract, which must have been computed over a "
         "different bin set or weighting.", "note", 46),
    ]:
        _pr(ws, F, r, txt, fmt)
        r += 1
    return r
