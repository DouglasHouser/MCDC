"""
Validation: MCDC macroscopic photon cross sections vs. raw HDF5 tabulated data (Pb).

Builds the real flat_data buffer + mcdc state arrays and calls the actual
macro_*_xs transport functions, then compares against the underlying HDF5
cross sections (coherent, incoherent/Compton, photoelectric, pair) read
directly from data/mcdc/Pb.h5.
"""

import numpy as np

import mcdc.numba_types as t
from mcdc.constant import MATERIAL_PHOTON, PARTICLE_PHOTON
from mcdc.object_.photon_material import _build_flat_data
from mcdc.transport.physics.photon.cross_sections import (
    macro_coherent_xs,
    macro_compton_xs,
    macro_photoelectric_xs,
    macro_pair_production_xs,
    macro_total_xs,
)
from mcdc.transport.physics.photon.data_loader import (
    load_photon_element,
    load_photon_element_coherent,
)

_BARN_PER_CM2 = 1.0e24
_PAIR_THRESH = 2.0 * 0.51099895

Z = 82          # Pb
density = 0.033  # atoms/barn-cm (representative)

# --- Build flat_data and mcdc state ----------------------------------------
flat = _build_flat_data([Z], [density])

# Build the minimal arrays the macro functions touch.
materials = np.zeros(1, dtype=t.material)
materials[0]["child_type"] = MATERIAL_PHOTON
materials[0]["child_ID"] = 0

photon_materials = np.zeros(1, dtype=t.photon_material)
photon_materials[0]["N_element"] = 1
photon_materials[0]["flat_data_offset"] = 0
photon_materials[0]["flat_data_length"] = len(flat)

# Assemble a tiny dict-like mcdc via numpy structured "record" the funcs index by name.
mcdc_state = {
    "materials": materials,
    "photon_materials": photon_materials,
    "constant_xs_materials": np.zeros(1, dtype=t.constant_xs_material),
}

data = flat

# Raw HDF5 reference data (cm^2/atom on the shared energy grid)
energies, compton_ref, pe_ref, pair_ref = load_photon_element(Z)
_, coherent_ref = load_photon_element_coherent(Z)


def make_particle(E):
    p = np.zeros(1, dtype=t.particle)
    p[0]["material_ID"] = 0
    p[0]["particle_type"] = PARTICLE_PHOTON
    p[0]["E"] = E
    p[0]["alive"] = True
    return p


def ref_macro(xs_arr, E):
    """Macroscopic cm^-1 from a tabulated cm^2/atom array via log-log interp."""
    sigma = np.exp(np.interp(np.log(E), np.log(energies), np.log(xs_arr)))
    return density * sigma * _BARN_PER_CM2


test_energies = [0.01, 0.03, 0.1, 0.5, 1.0, 5.0, 10.0]  # MeV: 10-100 keV and 1-10 MeV

print(f"{'E (MeV)':>9} {'channel':>12} {'MCDC (1/cm)':>14} {'HDF5 (1/cm)':>14} {'rel.err':>10}")
print("-" * 64)

max_err = 0.0
for E in test_energies:
    p = make_particle(E)
    rows = [
        ("coherent", macro_coherent_xs(p, mcdc_state, data), ref_macro(coherent_ref, E)),
        ("incoherent", macro_compton_xs(p, mcdc_state, data), ref_macro(compton_ref, E)),
        ("photoelec", macro_photoelectric_xs(p, mcdc_state, data), ref_macro(pe_ref, E)),
        (
            "pair",
            macro_pair_production_xs(p, mcdc_state, data),
            0.0 if E < _PAIR_THRESH else ref_macro(pair_ref, E),
        ),
    ]
    sigma_t_mcdc = macro_total_xs(p, mcdc_state, data)
    sigma_t_ref = sum(r[2] for r in rows)
    rows.append(("TOTAL", sigma_t_mcdc, sigma_t_ref))

    for name, got, ref in rows:
        rel = abs(got - ref) / ref if ref > 0 else abs(got - ref)
        max_err = max(max_err, rel)
        print(f"{E:>9.3g} {name:>12} {got:>14.6e} {ref:>14.6e} {rel:>10.2e}")
    print()

print(f"Max relative error across all channels/energies: {max_err:.2e}")
assert max_err < 1e-9, "MCDC cross sections diverge from tabulated HDF5 data!"
print("PASS: total = coherent + incoherent + photoelectric + pair, all match HDF5.")
