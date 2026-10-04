import math

from numba import njit

import mcdc.transport.rng as rng

from mcdc.constant import MATERIAL_CONSTANT_XS
from mcdc.transport.physics.photon import native, util

_M_E = 0.51099895
_PAIR_THRESH = 2.0 * _M_E

# hc in keV * angstrom; used to build the photon wavenumber k = E/(hc) [1/angstrom].
_HC_KEV_ANGSTROM = 12.39842
_MEV_TO_KEV = 1.0e3


@njit
def sample_compton_direction(E_in, particle_container, rng_module):
    kappa = E_in / _M_E
    tau = 1.0 / (1.0 + 2.0 * kappa)
    a1 = math.log(1.0 / tau)
    a2 = (1.0 - tau * tau) / 2.0

    eps = 1.0
    mu = 1.0
    while True:
        r1 = rng_module.lcg(particle_container)
        r2 = rng_module.lcg(particle_container)
        r3 = rng_module.lcg(particle_container)

        if r1 * (a1 + a2) < a1:
            eps = tau * math.exp(r2 * a1)
        else:
            eps = math.sqrt(tau * tau + r2 * (1.0 - tau * tau))

        mu = 1.0 - (1.0 / eps - 1.0) / kappa
        if mu < -1.0:
            mu = -1.0
        elif mu > 1.0:
            mu = 1.0

        sin2_theta = 1.0 - mu * mu
        if sin2_theta < 0.0:
            sin2_theta = 0.0

        p_acc = 1.0 - eps * sin2_theta / (1.0 + eps * eps)
        if r3 <= p_acc:
            break

    return eps, mu


# ======================================================================================
# Coherent (Rayleigh) form-factor angular sampler
#
#   dsigma/dOmega = (r_e^2 / 2) (1 + mu^2) F(q, Z)^2
#
# The (1 + mu^2)/2 Thomson factor is applied by rejection (efficiency >= 50% at any
# energy); the F(q)^2 part is sampled by inverting the precomputed cumulative
#   A(q^2) = integral_0^{q^2} F^2 d(q'^2)
# stored per element in the flat-data buffer (see mcdc/object_/photon_material.py).
#
# Momentum transfer / angle relations (k = E/(hc)):
#   q^2   = 2 k^2 (1 - mu)   =>   mu = 1 - q^2 / (2 k^2)
#   q_max = 2 k              (at mu = -1, backscatter)
# The stored q grid is already the code's momentum transfer (q = 2 x, where x is
# EPDL's variable; conversion done once in the data loader), so q_max and the grid
# share units (inverse angstrom).
# ======================================================================================


@njit
def sample_coherent_mu(particle_container, mcdc, data):
    """
    Sample the coherent (Rayleigh) scattering cosine ``mu`` for the colliding
    photon from the tabulated atomic form factor.

    For a multi-element material the scattering element is chosen with probability
    proportional to its coherent macroscopic contribution ``n_i * sigma_coh,i(E)``;
    ``mu`` is then sampled from that element's form factor.  Energy is unchanged
    (elastic); only the direction cosine is returned.

    Returns
    -------
    float
        Scattering cosine ``mu`` in ``[-1, 1]``.  Returns ``1.0`` (no deflection)
        in the degenerate low-energy limit where the accessible ``q`` range carries
        no form-factor weight.
    """
    material_ID = particle_container[0]["material_ID"]
    mat_base = mcdc["materials"][material_ID]
    # Constant-XS materials carry no form factor; the caller should not reach here,
    # but guard defensively with an isotropic-equivalent return.
    if mat_base["child_type"] == MATERIAL_CONSTANT_XS:
        return 2.0 * rng.lcg(particle_container) - 1.0

    E = particle_container[0]["E"]
    pm = mcdc["photon_materials"][mat_base["child_ID"]]
    N_elem = pm["N_element"]
    base = pm["flat_data_offset"]

    # --- Select the scattering element by coherent-XS weight ------------------
    idx = 0
    if N_elem > 1:
        Sigma_coh = 0.0
        for i in range(N_elem):
            n = data[base + N_elem + i]
            N_pts = int(data[base + 2 * N_elem + i])
            eg_off = base + int(data[base + 3 * N_elem + i])
            coh_off = base + int(data[base + 7 * N_elem + i])
            Sigma_coh += n * native.interpolate_xs(E, eg_off, coh_off, N_pts, data)
        target = rng.lcg(particle_container) * Sigma_coh
        acc = 0.0
        for i in range(N_elem):
            n = data[base + N_elem + i]
            N_pts = int(data[base + 2 * N_elem + i])
            eg_off = base + int(data[base + 3 * N_elem + i])
            coh_off = base + int(data[base + 7 * N_elem + i])
            acc += n * native.interpolate_xs(E, eg_off, coh_off, N_pts, data)
            if target <= acc:
                idx = i
                break

    # --- Form-factor grid + cumulative F^2 table for the chosen element -------
    nff = int(data[base + 8 * N_elem + idx])
    q_off = base + int(data[base + 9 * N_elem + idx])
    cum_off = base + int(data[base + 10 * N_elem + idx])

    # Photon wavenumber and backscatter (max) momentum transfer.
    k = E * _MEV_TO_KEV / _HC_KEV_ANGSTROM
    two_k2 = 2.0 * k * k
    q_max2 = 4.0 * k * k

    # Cumulative weight available up to q_max^2.
    A_qmax = _interp_cumulative_at_q2(q_max2, q_off, cum_off, nff, data)
    if A_qmax <= 0.0:
        # No accessible form-factor weight (E -> 0 limit): forward scatter.
        return 1.0

    # --- Inverse-CDF sample of q^2, with Thomson (1 + mu^2)/2 rejection -------
    while True:
        A_xi = rng.lcg(particle_container) * A_qmax
        q2 = _invert_cumulative(A_xi, q_off, cum_off, nff, data)
        if q2 > q_max2:
            q2 = q_max2
        mu = 1.0 - q2 / two_k2
        if mu > 1.0:
            mu = 1.0
        elif mu < -1.0:
            mu = -1.0
        if rng.lcg(particle_container) <= 0.5 * (1.0 + mu * mu):
            return mu


# ======================================================================================
# Photoelectric atomic relaxation (characteristic X-ray fluorescence)
#
# After a photoelectric absorption the incident photon is gone and a vacancy is left
# in an inner shell.  The vacancy de-excites either radiatively (emitting a
# characteristic X-ray) with probability omega (the shell's fluorescence yield) or
# non-radiatively (Auger), in which case the energy is deposited locally (electrons
# are not transported).  Only the K, L1, L2, L3 shells are modeled; a K radiative
# transition leaves a residual vacancy that is followed one further (L) cascade step.
#
# All per-shell data lives in the flat-data buffer (see mcdc/object_/photon_material.py):
#   section 11+s  shell-resolved PE-XS relative offsets   (s = 0..3 -> K,L1,L2,L3)
#   section 15+s  shell binding energies (MeV)            [unused here; gating is via XS]
#   section 19+s  shell fluorescence yields omega
#   section 23+s  shell radiative-line counts n_lines
#   section 27+s  shell line-table relative offsets
# Each line table is n_lines triples: (line_energy_MeV, cumulative_prob, final_shell_idx).
# ======================================================================================


@njit
def _relax_shell(shell, i_sel, base, N, particle_container, data):
    """
    Decide radiative vs. Auger for a vacancy in modeled shell index ``shell``
    (0=K, 1=L1, 2=L2, 3=L3) of element ``i_sel``, and, on radiative decay, sample
    the characteristic line by inverse-CDF over its normalized cumulative table.

    Returns
    -------
    (E_line, final_idx) : (float, int)
        Emitted line energy (MeV; 0.0 if non-radiative or no lines) and the
        MODELED_SHELLS index (0..3) of the residual vacancy, or -1 if unmodeled.
    """
    omega = data[base + (19 + shell) * N + i_sel]
    if omega <= 0.0 or rng.lcg(particle_container) >= omega:
        return 0.0, -1  # non-radiative (Auger): deposit locally

    n_lines = int(data[base + (23 + shell) * N + i_sel])
    if n_lines <= 0:
        return 0.0, -1

    line_off = base + int(data[base + (27 + shell) * N + i_sel])
    xi = rng.lcg(particle_container)
    j = 0
    while j < n_lines - 1 and xi > data[line_off + 3 * j + 1]:
        j += 1
    E_line = data[line_off + 3 * j]
    final_idx = int(data[line_off + 3 * j + 2])
    return E_line, final_idx


@njit
def sample_photoelectric_emission(particle_container, mcdc, data):
    """
    Sample the atomic-relaxation outcome of a photoelectric absorption.

    Selects the absorbing element (proportional to ``n_i * sigma_PE,i(E)``) and the
    vacancy shell (proportional to the shell-resolved PE cross section), then decays
    the vacancy radiatively or via Auger, following one K->L cascade step.

    Returns
    -------
    (n_photons, E1, E2) : (int, float, float)
        Number of fluorescence photons to emit (0, 1, or 2) and their energies in
        MeV (entries beyond ``n_photons`` are 0.0).
    """
    material_ID = particle_container[0]["material_ID"]
    mat_base = mcdc["materials"][material_ID]
    if mat_base["child_type"] == MATERIAL_CONSTANT_XS:
        return 0, 0.0, 0.0

    E = particle_container[0]["E"]
    pm = mcdc["photon_materials"][mat_base["child_ID"]]
    N = pm["N_element"]
    base = pm["flat_data_offset"]

    # --- Select absorbing element by photoelectric-XS weight ------------------
    i_sel = 0
    if N > 1:
        Sigma_pe = 0.0
        for i in range(N):
            n = data[base + N + i]
            N_pts = int(data[base + 2 * N + i])
            eg_off = base + int(data[base + 3 * N + i])
            pe_off = base + int(data[base + 5 * N + i])
            Sigma_pe += n * native.interpolate_xs(E, eg_off, pe_off, N_pts, data)
        target = rng.lcg(particle_container) * Sigma_pe
        acc = 0.0
        i_sel = N - 1
        for i in range(N):
            n = data[base + N + i]
            N_pts = int(data[base + 2 * N + i])
            eg_off = base + int(data[base + 3 * N + i])
            pe_off = base + int(data[base + 5 * N + i])
            acc += n * native.interpolate_xs(E, eg_off, pe_off, N_pts, data)
            if target <= acc:
                i_sel = i
                break

    # --- Select the vacancy shell by shell-resolved PE-XS weight --------------
    N_pts = int(data[base + 2 * N + i_sel])
    eg_off = base + int(data[base + 3 * N + i_sel])
    pe_off = base + int(data[base + 5 * N + i_sel])
    sigma_pe_tot = native.interpolate_xs(E, eg_off, pe_off, N_pts, data)
    if sigma_pe_tot <= 0.0:
        return 0, 0.0, 0.0

    r = rng.lcg(particle_container) * sigma_pe_tot
    acc = 0.0
    shell = -1
    for s in range(4):
        sh_off = base + int(data[base + (11 + s) * N + i_sel])
        acc += native.interpolate_xs(E, eg_off, sh_off, N_pts, data)
        if r < acc:
            shell = s
            break
    if shell < 0:
        # Vacancy in an unmodeled (M+) shell: local deposition only.
        return 0, 0.0, 0.0

    # --- Radiative vs Auger for the primary vacancy, then one L cascade -------
    E1, final_idx = _relax_shell(shell, i_sel, base, N, particle_container, data)
    if E1 <= 0.0:
        return 0, 0.0, 0.0

    if 0 <= final_idx < 4:
        E2, _f2 = _relax_shell(final_idx, i_sel, base, N, particle_container, data)
        if E2 > 0.0:
            return 2, E1, E2
    return 1, E1, 0.0


@njit
def _interp_cumulative_at_q2(q2_target, q_off, cum_off, nff, data):
    """
    Interpolate the cumulative table ``A`` at momentum-transfer-squared ``q2_target``.

    ``A`` is stored against the ``q`` grid but is piecewise-linear in ``q^2`` (a
    trapezoid integral over ``q^2``), so interpolation is done in ``q^2``.
    """
    q = math.sqrt(q2_target)
    j = native.find_energy_bin(q, q_off, nff, data)
    q0 = data[q_off + j]
    q1 = data[q_off + j + 1]
    A0 = data[cum_off + j]
    A1 = data[cum_off + j + 1]
    q0_2 = q0 * q0
    q1_2 = q1 * q1
    denom = q1_2 - q0_2
    if denom <= 0.0:
        return A0
    frac = (q2_target - q0_2) / denom
    if frac < 0.0:
        frac = 0.0
    elif frac > 1.0:
        frac = 1.0
    return A0 + frac * (A1 - A0)


@njit
def _invert_cumulative(A_target, q_off, cum_off, nff, data):
    """
    Invert the monotone cumulative table: return ``q^2`` with ``A(q^2) == A_target``.

    Binary-searches the ``cum`` array for ``A_target`` (same monotone-bin search as
    ``find_energy_bin``), then linearly interpolates ``q^2`` within the bin.
    """
    m = native.find_energy_bin(A_target, cum_off, nff, data)
    A0 = data[cum_off + m]
    A1 = data[cum_off + m + 1]
    q0 = data[q_off + m]
    q1 = data[q_off + m + 1]
    q0_2 = q0 * q0
    q1_2 = q1 * q1
    dA = A1 - A0
    if dA <= 0.0:
        return q0_2
    frac = (A_target - A0) / dA
    if frac < 0.0:
        frac = 0.0
    elif frac > 1.0:
        frac = 1.0
    return q0_2 + frac * (q1_2 - q0_2)
