"""
Photon reaction loader — stub for future HDF5-driven reaction initialization.

When nuclear data files provide tabulated photon cross-sections per reaction
channel, this module will load them into the appropriate PhotonReaction* objects,
mirroring the neutron_reaction.py ``from_h5_group`` pattern.

Currently all photon cross-sections are computed analytically (Klein-Nishina)
or interpolated from embedded NIST XCOM tables at runtime, so no per-reaction
HDF5 groups exist yet.  The stubs below define the expected API so that callers
can be written against it today.
"""

import numpy as np
from numpy import float64
from numpy.typing import NDArray

from mcdc.constant import (
    PHOTON_REACTION_COHERENT,
    PHOTON_REACTION_COMPTON,
    PHOTON_REACTION_PHOTOELECTRIC,
    PHOTON_REACTION_PAIR_PRODUCTION,
    REFERENCE_FRAME_LAB,
)
from mcdc.object_.photon_reaction import (
    PhotonReactionBase,
    PhotonReactionCoherent,
    PhotonReactionCompton,
    PhotonReactionPhotoelectric,
    PhotonReactionPairProduction,
)

# MT numbers following ENDF/B conventions for photon interactions
_MT_COHERENT = 502       # coherent (Rayleigh) scattering
_MT_COMPTON = 504        # incoherent (Compton) scattering
_MT_PHOTOELECTRIC = 501  # photoelectric absorption
_MT_PAIR_PRODUCTION = 503  # pair production (nuclear + electron field)


def load_photon_reaction(type_: int, xs: NDArray[float64] | None = None):
    """
    Return a PhotonReaction object for the given reaction type.

    Parameters
    ----------
    type_ : int
        One of PHOTON_REACTION_COMPTON, PHOTON_REACTION_PHOTOELECTRIC, or
        PHOTON_REACTION_PAIR_PRODUCTION (from mcdc.constant).
    xs : NDArray[float64], optional
        Pre-computed macroscopic cross-section array.  When None a placeholder
        zero-length array is used; callers should supply actual values before
        the object is used for transport.

    Returns
    -------
    PhotonReactionBase
        The appropriate concrete subclass instance (not registered in the
        simulation object list).
    """
    if xs is None:
        xs = np.zeros(1, dtype=np.float64)

    if type_ == PHOTON_REACTION_COMPTON:
        return PhotonReactionCompton(
            MT=_MT_COMPTON,
            xs=xs,
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
    elif type_ == PHOTON_REACTION_COHERENT:
        return PhotonReactionCoherent(
            MT=_MT_COHERENT,
            xs=xs,
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
    elif type_ == PHOTON_REACTION_PHOTOELECTRIC:
        return PhotonReactionPhotoelectric(
            MT=_MT_PHOTOELECTRIC,
            xs=xs,
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
    elif type_ == PHOTON_REACTION_PAIR_PRODUCTION:
        return PhotonReactionPairProduction(
            MT=_MT_PAIR_PRODUCTION,
            xs=xs,
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
    else:
        raise ValueError(f"Unknown photon reaction type: {type_}")


def load_photon_reaction_from_h5(h5_group, type_: int):
    """
    Load a PhotonReaction object from an HDF5 group.

    This is a stub — HDF5-backed photon reaction data is not yet implemented.
    The signature mirrors NeutronReactionBase.from_h5_group so that future
    callers can be written against this API now.

    Parameters
    ----------
    h5_group : h5py.Group
        HDF5 group containing reaction data (fields TBD when data format is
        finalised).
    type_ : int
        Reaction type constant (PHOTON_REACTION_*).

    Returns
    -------
    PhotonReactionBase
        Stub: delegates to load_photon_reaction(type_) with no XS data.

    Raises
    ------
    NotImplementedError
        Always — HDF5 photon reaction loading is not yet implemented.
    """
    raise NotImplementedError(
        "HDF5 photon reaction loading is not yet implemented. "
        "Use load_photon_reaction() with analytically computed cross-sections."
    )
