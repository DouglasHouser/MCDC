import math

from numba import njit

from mcdc.constant import MATERIAL_CONSTANT_XS, MATERIAL_PHOTON
from mcdc.transport.physics.photon import native

_R_E = 2.8179403e-13
_M_E = 0.51099895
_PAIR_THRESH = 2.0 * _M_E
_BARN_PER_CM2 = (
    1.0e24  # density is in atoms/barn-cm; XS is in cm^2 → multiply to get cm^-1
)

# ======================================================================================
# Klein-Nishina (Compton) cross-section per electron
# ======================================================================================


@njit
def klein_nishina_total(E):
    alpha = E / _M_E
    pi = math.pi
    r_e = _R_E

    if alpha < 1e-3:
        return (8.0 / 3.0) * pi * r_e * r_e

    a2 = 2.0 * alpha
    one_plus_a2 = 1.0 + a2
    ln_term = math.log(one_plus_a2)

    term1 = ((1.0 + alpha) / (alpha * alpha * alpha)) * (
        a2 * (1.0 + alpha) / one_plus_a2 - ln_term
    )
    term2 = ln_term / a2
    term3 = (1.0 + 3.0 * alpha) / (one_plus_a2 * one_plus_a2)

    return 2.0 * pi * r_e * r_e * (term1 + term2 - term3)


# ======================================================================================
# Macroscopic cross-sections — dispatch by material type (constant-XS vs NIST photon)
#
# For MATERIAL_PHOTON, flat_data layout for N elements (see mcdc/object_/photon_material.py):
#   [0 ..   N-1]  Z values
#   [N ..  2N-1]  densities
#   [2N..  3N-1]  N_points per element        (XS energy-grid length)
#   [3N..  4N-1]  energy_grid relative offsets  (relative to flat_data_offset)
#   [4N..  5N-1]  compton (incoherent) relative offsets
#   [5N..  6N-1]  pe relative offsets
#   [6N..  7N-1]  pair relative offsets
#   [7N..  8N-1]  coherent (Rayleigh) relative offsets
#   [8N..  9N-1]  N_ff points per element      (form-factor grid length)
#   [9N.. 10N-1]  q_grid (momentum-transfer) relative offsets
#   [10N..11N-1]  cumF2 (cumulative F^2 table) relative offsets
#   [11N..     ]  per-element data
#                   (E_grid | compton | pe | pair | coherent | q_grid | cumF2)
#
# The XS-lookup functions below use only sections 0–7, which are unchanged by the
# form-factor extension; the coherent angular sampler (distributions.py) uses
# sections 8–10.
#
# For MATERIAL_CONSTANT_XS, values are stored as macroscopic cm^-1 directly in the
# constant_xs_materials array (sigma_total, sigma_scatter, sigma_absorb). The full
# constant cross section is treated as Compton-equivalent for the dispatch below;
# the collision routine handles scatter-vs-absorb sampling separately.
# ======================================================================================


@njit
def macro_compton_xs(particle_container, mcdc, data):
    # Incoherent (Compton) scattering. Uses the *tabulated* incoherent cross section
    # from the dataset for the interaction probability; the Klein-Nishina/Kahn model
    # is used only for the outgoing energy/angle in the collision routine.
    material_ID = particle_container[0]["material_ID"]
    mat_base = mcdc["materials"][material_ID]
    if mat_base["child_type"] == MATERIAL_CONSTANT_XS:
        cxs = mcdc["constant_xs_materials"][mat_base["child_ID"]]
        return cxs["sigma_scatter"]

    E = particle_container[0]["E"]
    pm = mcdc["photon_materials"][mat_base["child_ID"]]
    N_elem = pm["N_element"]
    base = pm["flat_data_offset"]

    Sigma = 0.0
    for i in range(N_elem):
        n = data[base + N_elem + i]
        N_pts = int(data[base + 2 * N_elem + i])
        eg_off = base + int(data[base + 3 * N_elem + i])
        cm_off = base + int(data[base + 4 * N_elem + i])
        sigma = native.interpolate_xs(E, eg_off, cm_off, N_pts, data)
        Sigma += n * sigma
    return Sigma * _BARN_PER_CM2


@njit
def macro_coherent_xs(particle_container, mcdc, data):
    # Coherent (Rayleigh) scattering — tabulated cross section.
    material_ID = particle_container[0]["material_ID"]
    mat_base = mcdc["materials"][material_ID]
    if mat_base["child_type"] == MATERIAL_CONSTANT_XS:
        # Constant-XS materials lump all interactions into scatter+absorb; no separate
        # coherent channel.
        return 0.0

    E = particle_container[0]["E"]
    pm = mcdc["photon_materials"][mat_base["child_ID"]]
    N_elem = pm["N_element"]
    base = pm["flat_data_offset"]

    Sigma = 0.0
    for i in range(N_elem):
        n = data[base + N_elem + i]
        N_pts = int(data[base + 2 * N_elem + i])
        eg_off = base + int(data[base + 3 * N_elem + i])
        coh_off = base + int(data[base + 7 * N_elem + i])
        sigma = native.interpolate_xs(E, eg_off, coh_off, N_pts, data)
        Sigma += n * sigma
    return Sigma * _BARN_PER_CM2


@njit
def macro_photoelectric_xs(particle_container, mcdc, data):
    material_ID = particle_container[0]["material_ID"]
    mat_base = mcdc["materials"][material_ID]
    if mat_base["child_type"] == MATERIAL_CONSTANT_XS:
        cxs = mcdc["constant_xs_materials"][mat_base["child_ID"]]
        return cxs["sigma_absorb"]

    E = particle_container[0]["E"]
    pm = mcdc["photon_materials"][mat_base["child_ID"]]
    N_elem = pm["N_element"]
    base = pm["flat_data_offset"]

    Sigma = 0.0
    for i in range(N_elem):
        n = data[base + N_elem + i]
        N_pts = int(data[base + 2 * N_elem + i])
        eg_off = base + int(data[base + 3 * N_elem + i])
        pe_off = base + int(data[base + 5 * N_elem + i])
        sigma = native.interpolate_xs(E, eg_off, pe_off, N_pts, data)
        Sigma += n * sigma
    return Sigma * _BARN_PER_CM2


@njit
def macro_pair_production_xs(particle_container, mcdc, data):
    material_ID = particle_container[0]["material_ID"]
    mat_base = mcdc["materials"][material_ID]
    if mat_base["child_type"] == MATERIAL_CONSTANT_XS:
        # Constant-XS materials lump all interactions into scatter+absorb; no pair
        # production channel.
        return 0.0

    if particle_container[0]["E"] < _PAIR_THRESH:
        return 0.0

    E = particle_container[0]["E"]
    pm = mcdc["photon_materials"][mat_base["child_ID"]]
    N_elem = pm["N_element"]
    base = pm["flat_data_offset"]

    Sigma = 0.0
    for i in range(N_elem):
        n = data[base + N_elem + i]
        N_pts = int(data[base + 2 * N_elem + i])
        eg_off = base + int(data[base + 3 * N_elem + i])
        pp_off = base + int(data[base + 6 * N_elem + i])
        sigma = native.interpolate_xs(E, eg_off, pp_off, N_pts, data)
        Sigma += n * sigma
    return Sigma * _BARN_PER_CM2


@njit
def macro_total_xs(particle_container, mcdc, data):
    material_ID = particle_container[0]["material_ID"]
    mat_base = mcdc["materials"][material_ID]
    if mat_base["child_type"] == MATERIAL_CONSTANT_XS:
        cxs = mcdc["constant_xs_materials"][mat_base["child_ID"]]
        return cxs["sigma_total"]

    return (
        macro_coherent_xs(particle_container, mcdc, data)
        + macro_compton_xs(particle_container, mcdc, data)
        + macro_photoelectric_xs(particle_container, mcdc, data)
        + macro_pair_production_xs(particle_container, mcdc, data)
    )
