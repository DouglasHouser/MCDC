import math

import numpy as np
from numpy import float64
from numpy.typing import NDArray

####

from mcdc.constant import (
    PHOTON_REACTION_COHERENT,
    PHOTON_REACTION_COMPTON,
    PHOTON_REACTION_PHOTOELECTRIC,
    PHOTON_REACTION_PAIR_PRODUCTION,
    PHOTON_REACTION_TOTAL,
    REFERENCE_FRAME_LAB,
    REFERENCE_FRAME_COM,
)
from mcdc.object_.base import ObjectPolymorphic
from mcdc.print_ import print_1d_array

# Physical constants
_SPEED_OF_LIGHT = 29.9792458  # cm/shake
_PAIR_THRESH = 2.0 * 0.51099895  # 1.02199790 MeV
_M_E = 0.51099895  # MeV (electron rest-mass energy)

# ======================================================================================
# Photon reaction base class
# ======================================================================================


class PhotonReactionBase(ObjectPolymorphic):
    # Annotations for Numba mode
    label: str = "photon_reaction"
    #
    MT: int
    xs: NDArray[float64]
    xs_offset_: int  # "xs_offset" is reserved for "xs"
    reference_frame: int

    def __init__(self, type_, MT, xs, xs_offset, reference_frame, register=False):
        super().__init__(type_, register=register)
        self.MT = MT
        self.xs = xs
        self.xs_offset_ = xs_offset
        self.reference_frame = reference_frame

    def __repr__(self):
        text = "\n"
        text += f"{decode_type(self.type)}\n"
        text += f"  - MT: {self.MT}\n"
        text += f"  - XS {print_1d_array(self.xs)} barn\n"
        text += f"  - Reference frame: {_decode_reference_frame(self.reference_frame)}\n"
        return text


def decode_type(type_):
    if type_ == PHOTON_REACTION_COMPTON:
        return "Photon incoherent (Compton) scattering"
    elif type_ == PHOTON_REACTION_PHOTOELECTRIC:
        return "Photon photoelectric absorption"
    elif type_ == PHOTON_REACTION_PAIR_PRODUCTION:
        return "Photon pair production"
    elif type_ == PHOTON_REACTION_COHERENT:
        return "Photon coherent (Rayleigh) scattering"
    elif type_ == PHOTON_REACTION_TOTAL:
        return "Photon total"
    return "Unknown"


def _decode_reference_frame(type_):
    if type_ == REFERENCE_FRAME_LAB:
        return "Laboratory"
    elif type_ == REFERENCE_FRAME_COM:
        return "Center of mass"
    return "Unknown"


# ======================================================================================
# Compton scattering
# ======================================================================================


class PhotonReactionCompton(PhotonReactionBase):
    # Annotations for Numba mode
    label: str = "photon_compton_reaction"

    def __init__(self, MT, xs, xs_offset, reference_frame, register=False):
        super().__init__(
            PHOTON_REACTION_COMPTON, MT, xs, xs_offset, reference_frame, register
        )

    def perform_collision(self, particle_container, mcdc, data):
        """
        Perform Compton scattering using Kahn (1954) composition-rejection sampling.

        Samples the scattered photon energy (via eps = E'/E_in) and polar cosine mu
        from the Klein-Nishina distribution, then rotates the particle direction
        by (mu, random azimuth).  Updates particle energy and direction in-place.

        Parameters
        ----------
        particle_container : numpy.ndarray, shape (1,)
            Structured array with fields E, ux, uy, uz, alive.
        mcdc : numpy.ndarray, shape (1,)
            MCDC global state (unused here; present for interface consistency).
        data : numpy.ndarray
            Flat data buffer (unused here; present for interface consistency).
        """
        E_in = particle_container[0]["E"]
        kappa = E_in / _M_E
        tau = 1.0 / (1.0 + 2.0 * kappa)

        # Normalisation constants for the two envelope functions
        a1 = math.log(1.0 / tau)       # integral of 1/eps from tau to 1
        a2 = (1.0 - tau * tau) / 2.0   # integral of eps from tau to 1

        # Kahn rejection-sampling loop; acceptance rate >= 50 % at all energies
        eps = 1.0
        mu = 1.0
        while True:
            r1 = np.random.random()
            r2 = np.random.random()
            r3 = np.random.random()

            if r1 * (a1 + a2) < a1:
                eps = tau * math.exp(r2 * a1)
            else:
                eps = math.sqrt(tau * tau + r2 * (1.0 - tau * tau))

            # Compton kinematic relation: mu = 1 - (1/eps - 1)/kappa
            mu = 1.0 - (1.0 / eps - 1.0) / kappa
            if mu < -1.0:
                mu = -1.0
            elif mu > 1.0:
                mu = 1.0

            sin2_theta = 1.0 - mu * mu
            if sin2_theta < 0.0:
                sin2_theta = 0.0

            # Kahn acceptance probability (always in [0.5, 1])
            p_acc = 1.0 - eps * sin2_theta / (1.0 + eps * eps)
            if r3 <= p_acc:
                break

        # Update energy
        particle_container[0]["E"] = E_in * eps

        # Update direction (rotate by polar cos mu and random azimuth)
        azi = 2.0 * math.pi * np.random.random()
        ux = particle_container[0]["ux"]
        uy = particle_container[0]["uy"]
        uz = particle_container[0]["uz"]
        sin_theta = math.sqrt(max(0.0, 1.0 - mu * mu))
        cos_azi = math.cos(azi)
        sin_azi = math.sin(azi)

        if abs(uz) < 1.0 - 1e-10:
            sin_polar = math.sqrt(max(0.0, 1.0 - uz * uz))
            particle_container[0]["ux"] = (
                mu * ux + sin_theta * (ux * uz * cos_azi - uy * sin_azi) / sin_polar
            )
            particle_container[0]["uy"] = (
                mu * uy + sin_theta * (uy * uz * cos_azi + ux * sin_azi) / sin_polar
            )
            particle_container[0]["uz"] = mu * uz - sin_theta * sin_polar * cos_azi
        else:
            particle_container[0]["ux"] = sin_theta * cos_azi
            particle_container[0]["uy"] = sin_theta * sin_azi
            particle_container[0]["uz"] = mu * (1.0 if uz > 0.0 else -1.0)


# ======================================================================================
# Coherent (Rayleigh) scattering
# ======================================================================================


class PhotonReactionCoherent(PhotonReactionBase):
    # Annotations for Numba mode
    label: str = "photon_coherent_reaction"

    def __init__(self, MT, xs, xs_offset, reference_frame, register=False):
        super().__init__(
            PHOTON_REACTION_COHERENT, MT, xs, xs_offset, reference_frame, register
        )

    def perform_collision(self, particle_container, mcdc, data):
        """
        Perform coherent (Rayleigh) scattering.

        Coherent scattering is elastic: the photon energy is unchanged and only the
        direction is deflected.  The scattering cosine is sampled from the tabulated
        atomic form factor F(q, Z) via inverse-CDF on F^2, delegating to the shared
        ``sample_coherent_mu`` sampler (the same physics as the @njit transport path)
        so there is a single source of truth.  This consumes from the particle's LCG
        stream rather than ``np.random`` used by the isotropic legacy path.

        Parameters
        ----------
        particle_container : numpy.ndarray, shape (1,)
            Structured array with fields E, ux, uy, uz, alive, rng_seed.
        mcdc : numpy.ndarray, shape (1,)
            MCDC global state (typed simulation array with photon_materials/flat data).
        data : numpy.ndarray
            Flat data buffer carrying the per-element form factor (q-grid, cumF2).
        """
        from mcdc.transport import rng
        from mcdc.transport.physics.photon.distributions import sample_coherent_mu
        from mcdc.transport.physics.photon.util import scatter_direction

        # Form-factor scattering cosine (energy unchanged); random azimuth.
        mu = sample_coherent_mu(particle_container, mcdc, data)
        azi = 2.0 * math.pi * rng.lcg(particle_container)
        ux = particle_container[0]["ux"]
        uy = particle_container[0]["uy"]
        uz = particle_container[0]["uz"]
        ux, uy, uz = scatter_direction(ux, uy, uz, mu, azi)
        particle_container[0]["ux"] = ux
        particle_container[0]["uy"] = uy
        particle_container[0]["uz"] = uz


# ======================================================================================
# Photoelectric absorption
# ======================================================================================


class PhotonReactionPhotoelectric(PhotonReactionBase):
    # Annotations for Numba mode
    label: str = "photon_photoelectric_reaction"

    def __init__(self, MT, xs, xs_offset, reference_frame, register=False):
        super().__init__(
            PHOTON_REACTION_PHOTOELECTRIC, MT, xs, xs_offset, reference_frame, register
        )

    def perform_collision(self, particle_container, mcdc, data):
        """
        Perform photoelectric absorption: mark the photon as absorbed.

        Parameters
        ----------
        particle_container : numpy.ndarray, shape (1,)
            Structured array with fields E, ux, uy, uz, alive.
        mcdc : numpy.ndarray, shape (1,)
            MCDC global state.
        data : numpy.ndarray
            Flat data buffer.
        """
        particle_container[0]["alive"] = False


# ======================================================================================
# Pair production
# ======================================================================================


class PhotonReactionPairProduction(PhotonReactionBase):
    # Annotations for Numba mode
    label: str = "photon_pair_production_reaction"

    def __init__(self, MT, xs, xs_offset, reference_frame, register=False):
        super().__init__(
            PHOTON_REACTION_PAIR_PRODUCTION,
            MT,
            xs,
            xs_offset,
            reference_frame,
            register,
        )

    def perform_collision(self, particle_container, mcdc, data):
        """
        Perform pair production: mark the photon as absorbed.

        The photon is converted to an electron-positron pair above the 1.022 MeV
        threshold.  Secondary annihilation photons are handled by the transport
        loop; here the incident photon history is terminated.

        Parameters
        ----------
        particle_container : numpy.ndarray, shape (1,)
            Structured array with fields E, ux, uy, uz, alive.
        mcdc : numpy.ndarray, shape (1,)
            MCDC global state.
        data : numpy.ndarray
            Flat data buffer.
        """
        particle_container[0]["alive"] = False
