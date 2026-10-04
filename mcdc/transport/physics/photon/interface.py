import math

import numpy as np

from numba import njit

import mcdc.numba_types as type_
import mcdc.transport.particle as particle_module
import mcdc.transport.particle_bank as particle_bank_module
import mcdc.transport.rng as rng

from mcdc.constant import (
    MATERIAL_CONSTANT_XS,
    PHOTON_REACTION_COHERENT,
    PHOTON_REACTION_COMPTON,
    PHOTON_REACTION_PHOTOELECTRIC,
    PHOTON_REACTION_PAIR_PRODUCTION,
    PHOTON_REACTION_TOTAL,
)
from mcdc.transport.distribution import sample_isotropic_direction
from mcdc.transport.physics.photon.cross_sections import (
    macro_coherent_xs,
    macro_compton_xs,
    macro_pair_production_xs,
    macro_photoelectric_xs,
    macro_total_xs,
)
from mcdc.transport.physics.photon.distributions import (
    sample_coherent_mu,
    sample_photoelectric_emission,
)
from mcdc.transport.physics.photon.util import scatter_direction

_SPEED_OF_LIGHT = 29.9792458  # cm/shake
_M_E = 0.51099895  # MeV
_PAIR_THRESH = 2.0 * _M_E

# ======================================================================================
# Particle speed
# ======================================================================================


@njit
def particle_speed(particle_container, mcdc, data):
    return _SPEED_OF_LIGHT


# ======================================================================================
# Material cross-sections
# ======================================================================================


@njit
def macro_xs(reaction_type, particle_container, mcdc, data):
    if reaction_type == PHOTON_REACTION_COMPTON:
        return macro_compton_xs(particle_container, mcdc, data)
    elif reaction_type == PHOTON_REACTION_PHOTOELECTRIC:
        return macro_photoelectric_xs(particle_container, mcdc, data)
    elif reaction_type == PHOTON_REACTION_PAIR_PRODUCTION:
        return macro_pair_production_xs(particle_container, mcdc, data)
    elif reaction_type == PHOTON_REACTION_COHERENT:
        return macro_coherent_xs(particle_container, mcdc, data)
    else:
        # PHOTON_REACTION_TOTAL (3) or any other value
        return macro_total_xs(particle_container, mcdc, data)


@njit
def photon_production_xs(reaction_type, particle_container, mcdc, data):
    # Number of photons leaving each channel: coherent and incoherent scatter both
    # produce one outgoing photon; photoelectric absorbs (0); pair production yields
    # two 0.511 MeV annihilation photons.
    if reaction_type == PHOTON_REACTION_COMPTON:
        return macro_compton_xs(particle_container, mcdc, data)
    elif reaction_type == PHOTON_REACTION_COHERENT:
        return macro_coherent_xs(particle_container, mcdc, data)
    elif reaction_type == PHOTON_REACTION_PHOTOELECTRIC:
        return 0.0
    elif reaction_type == PHOTON_REACTION_PAIR_PRODUCTION:
        return 2.0 * macro_pair_production_xs(particle_container, mcdc, data)
    else:
        Sigma_coh = macro_coherent_xs(particle_container, mcdc, data)
        Sigma_C = macro_compton_xs(particle_container, mcdc, data)
        Sigma_PP = macro_pair_production_xs(particle_container, mcdc, data)
        return Sigma_coh + Sigma_C + 2.0 * Sigma_PP


# ======================================================================================
# Collision
# ======================================================================================


@njit
def collision(particle_container, mcdc, data):
    # Energy deposited locally at this collision site (returned for the
    # energy-deposit tally). Computed by the unifying rule:
    #   E_dep = E_in - (energy of the primary photon still alive)
    #                - (energy of any banked secondary photon)
    # Captured before any energy is modified below.
    E_in = particle_container[0]["E"]
    E_dep = 0.0

    # ===================================================================
    # Constant-XS dispatch: scatter-or-absorb sampling, isotropic-elastic
    # scatter (no energy change). Used by analytical benchmarks (Case-de
    # Hoffmann-Placzek) where cross sections are energy-independent.
    # ===================================================================
    material_ID = particle_container[0]["material_ID"]
    mat_base = mcdc["materials"][material_ID]
    if mat_base["child_type"] == MATERIAL_CONSTANT_XS:
        cxs = mcdc["constant_xs_materials"][mat_base["child_ID"]]
        sigma_t = cxs["sigma_total"]
        if sigma_t <= 0.0:
            return 0.0
        sigma_a = cxs["sigma_absorb"]
        xi = rng.lcg(particle_container) * sigma_t
        if xi < sigma_a:
            # Analog capture: the full incident energy deposits locally.
            particle_container[0]["alive"] = False
            return E_in
        # Isotropic-elastic scatter: no energy change, nothing deposited.
        mu = 2.0 * rng.lcg(particle_container) - 1.0
        azi = 2.0 * math.pi * rng.lcg(particle_container)
        c = math.sqrt(max(0.0, 1.0 - mu * mu))
        particle_container[0]["ux"] = mu
        particle_container[0]["uy"] = math.cos(azi) * c
        particle_container[0]["uz"] = math.sin(azi) * c
        return 0.0

    # Tabulated channel cross sections drive the interaction probabilities.
    Sigma_coh = macro_coherent_xs(particle_container, mcdc, data)
    Sigma_C = macro_compton_xs(particle_container, mcdc, data)
    Sigma_PE = macro_photoelectric_xs(particle_container, mcdc, data)
    Sigma_PP = macro_pair_production_xs(particle_container, mcdc, data)
    Sigma_T = Sigma_coh + Sigma_C + Sigma_PE + Sigma_PP

    if Sigma_T <= 0.0:
        return 0.0

    xi = rng.lcg(particle_container) * Sigma_T

    if xi < Sigma_coh:
        # ===================================================================
        # Coherent (Rayleigh) scattering — elastic: no energy change.
        #
        # The scattering cosine is sampled from the tabulated atomic form factor
        # F(q, Z) via inverse-CDF on F^2 (see distributions.sample_coherent_mu),
        # reproducing the strong forward peaking that grows with energy and Z.
        # Energy is conserved (elastic); only the direction is deflected.
        # ===================================================================
        mu = sample_coherent_mu(particle_container, mcdc, data)
        azi = 2.0 * math.pi * rng.lcg(particle_container)
        ux = particle_container[0]["ux"]
        uy = particle_container[0]["uy"]
        uz = particle_container[0]["uz"]
        ux, uy, uz = scatter_direction(ux, uy, uz, mu, azi)
        particle_container[0]["ux"] = ux
        particle_container[0]["uy"] = uy
        particle_container[0]["uz"] = uz

    elif xi < Sigma_coh + Sigma_C:
        # ===================================================================
        # Incoherent (Compton) scattering — Kahn (1954) composition-rejection
        # sampling. The interaction probability above came from the tabulated
        # incoherent cross section; Klein-Nishina/Kahn is used here only for the
        # outgoing energy and angle.
        # ===================================================================
        E_in = particle_container[0]["E"]
        kappa = E_in / _M_E
        tau = 1.0 / (1.0 + 2.0 * kappa)

        a1 = math.log(1.0 / tau)
        a2 = (1.0 - tau * tau) / 2.0

        eps = 1.0
        mu = 1.0
        while True:
            r1 = rng.lcg(particle_container)
            r2 = rng.lcg(particle_container)
            r3 = rng.lcg(particle_container)

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

        # Update energy
        particle_container[0]["E"] = E_in * eps

        # Recoil-electron energy deposits locally (electrons not transported);
        # the scattered photon carries away E_in * eps.
        E_dep = E_in * (1.0 - eps)

        # Update direction (shared polar rotation; see coherent branch above)
        azi = 2.0 * math.pi * rng.lcg(particle_container)
        ux = particle_container[0]["ux"]
        uy = particle_container[0]["uy"]
        uz = particle_container[0]["uz"]
        ux, uy, uz = scatter_direction(ux, uy, uz, mu, azi)
        particle_container[0]["ux"] = ux
        particle_container[0]["uy"] = uy
        particle_container[0]["uz"] = uz

    elif xi < Sigma_coh + Sigma_C + Sigma_PE:
        # ===================================================================
        # Photoelectric absorption — the incident photon is absorbed.  With
        # fluorescence enabled, the inner-shell vacancy may emit one or two
        # characteristic X-rays (K, then an L cascade); Auger / unmodeled-shell
        # outcomes deposit locally.  The photoelectron kinetic energy
        # (E - E_bind) is deposited locally (electrons are not transported).
        # ===================================================================
        n_photons = 0
        E1 = 0.0
        E2 = 0.0
        if mcdc["settings"]["photon_fluorescence"]:
            n_photons, E1, E2 = sample_photoelectric_emission(
                particle_container, mcdc, data
            )

        # Photoelectron + Auger + unmodeled-shell energy deposits locally; only the
        # (0, 1, or 2) fluorescence photons carry energy away from the site.
        E_dep = E_in - E1 - E2

        if n_photons == 0:
            particle_container[0]["alive"] = False
        else:
            # First fluorescence photon: revive the current history in place
            # (cheaper than killing it and banking a fresh history), emitted
            # isotropically from the absorption site.
            ux1, uy1, uz1 = sample_isotropic_direction(particle_container)
            particle_container[0]["E"] = E1
            particle_container[0]["ux"] = ux1
            particle_container[0]["uy"] = uy1
            particle_container[0]["uz"] = uz1

            if n_photons == 2:
                # Second (L-cascade) fluorescence photon: emit as a new active
                # particle from the collision site, inheriting the weight.
                ux2, uy2, uz2 = sample_isotropic_direction(particle_container)
                particle_container_new = np.zeros(1, type_.particle_data)
                particle_module.copy_as_child(
                    particle_container_new, particle_container
                )
                particle_container_new[0]["E"] = E2
                particle_container_new[0]["ux"] = ux2
                particle_container_new[0]["uy"] = uy2
                particle_container_new[0]["uz"] = uz2
                particle_bank_module.bank_active_particle(
                    particle_container_new, mcdc
                )

    else:
        # ===================================================================
        # Pair production — photon converts to an e+/e- pair. The kinetic
        # energy of the pair is deposited locally (electrons are not
        # transported and bremsstrahlung is neglected), and the positron
        # annihilates at rest, emitting two 0.511 MeV (= m_e c^2)
        # annihilation photons. These secondaries carry the deep-penetration
        # buildup that pure absorption would otherwise discard.
        # ===================================================================
        # Pair kinetic energy deposits locally (electrons not transported,
        # bremsstrahlung neglected); the two 0.511 MeV annihilation photons
        # escape and deposit their energy at their own later collision sites.
        E_dep = E_in - _PAIR_THRESH

        # First annihilation photon: revive the current history in place
        # (cheaper than killing it and banking two fresh histories).
        ux1, uy1, uz1 = sample_isotropic_direction(particle_container)
        particle_container[0]["E"] = _M_E
        particle_container[0]["ux"] = ux1
        particle_container[0]["uy"] = uy1
        particle_container[0]["uz"] = uz1

        # Second annihilation photon: emit as a new active particle from the
        # collision site, inheriting the current photon's weight.
        particle_container_new = np.zeros(1, type_.particle_data)
        particle_module.copy_as_child(particle_container_new, particle_container)
        particle_container_new[0]["E"] = _M_E
        particle_container_new[0]["ux"] = -ux1
        particle_container_new[0]["uy"] = -uy1
        particle_container_new[0]["uz"] = -uz1
        particle_bank_module.bank_active_particle(particle_container_new, mcdc)

    return E_dep
