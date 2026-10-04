"""
Unit tests for mcdc.object_.photon_reaction module.

Covers:
    - PhotonReactionBase initialisation (attributes, __repr__)
    - PhotonReactionCompton.perform_collision() — Kahn sampling, energy/direction
    - PhotonReactionPhotoelectric.perform_collision() — alive=False
    - PhotonReactionPairProduction.perform_collision() — alive=False
    - decode_type() helper

Run with NUMBA_DISABLE_JIT=1 so @njit functions execute as plain Python::

    NUMBA_DISABLE_JIT=1 pytest test/unit/photon/test_photon_reaction.py -v
"""

import math

import numpy as np
import pytest

from mcdc.constant import (
    PHOTON_REACTION_COMPTON,
    PHOTON_REACTION_PHOTOELECTRIC,
    PHOTON_REACTION_PAIR_PRODUCTION,
    PHOTON_REACTION_TOTAL,
    REFERENCE_FRAME_LAB,
    REFERENCE_FRAME_COM,
)
from mcdc.object_.photon_reaction import (
    PhotonReactionBase,
    PhotonReactionCompton,
    PhotonReactionPhotoelectric,
    PhotonReactionPairProduction,
    decode_type,
    _M_E,
    _PAIR_THRESH,
    _SPEED_OF_LIGHT,
)

# =============================================================================
# Minimal particle dtype used throughout these tests
# =============================================================================

_particle_dtype = np.dtype(
    [
        ("E", np.float64),
        ("material_ID", np.int32),
        ("ux", np.float64),
        ("uy", np.float64),
        ("uz", np.float64),
        ("alive", np.bool_),
    ]
)


def _make_particle(E=1.0, ux=0.0, uy=0.0, uz=1.0, alive=True):
    p = np.zeros(1, dtype=_particle_dtype)
    p[0]["E"] = E
    p[0]["ux"] = ux
    p[0]["uy"] = uy
    p[0]["uz"] = uz
    p[0]["alive"] = alive
    return p


def _make_reaction(cls, xs_val=1.0):
    """Construct a reaction object with minimal boilerplate."""
    return cls(
        MT=500,
        xs=np.array([xs_val]),
        xs_offset=0,
        reference_frame=REFERENCE_FRAME_LAB,
    )


# =============================================================================
# PhotonReactionBase
# =============================================================================


class TestPhotonReactionBase:
    def test_type_attribute(self):
        r = PhotonReactionBase(
            type_=PHOTON_REACTION_COMPTON,
            MT=502,
            xs=np.array([0.5]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        assert r.type == PHOTON_REACTION_COMPTON

    def test_mt_attribute(self):
        r = PhotonReactionBase(
            type_=PHOTON_REACTION_PHOTOELECTRIC,
            MT=501,
            xs=np.array([0.3]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        assert r.MT == 501

    def test_xs_attribute(self):
        xs = np.array([1.23, 4.56])
        r = PhotonReactionBase(
            type_=PHOTON_REACTION_COMPTON,
            MT=502,
            xs=xs,
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        np.testing.assert_array_equal(r.xs, xs)

    def test_xs_offset_attribute(self):
        r = PhotonReactionBase(
            type_=PHOTON_REACTION_COMPTON,
            MT=502,
            xs=np.array([1.0]),
            xs_offset=7,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        assert r.xs_offset_ == 7

    def test_reference_frame_attribute(self):
        r = PhotonReactionBase(
            type_=PHOTON_REACTION_COMPTON,
            MT=502,
            xs=np.array([1.0]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_COM,
        )
        assert r.reference_frame == REFERENCE_FRAME_COM

    def test_repr_contains_reaction_name(self):
        r = PhotonReactionBase(
            type_=PHOTON_REACTION_COMPTON,
            MT=502,
            xs=np.array([1.0]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        text = repr(r)
        assert "Compton" in text

    def test_repr_contains_mt(self):
        r = PhotonReactionBase(
            type_=PHOTON_REACTION_PHOTOELECTRIC,
            MT=501,
            xs=np.array([1.0]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        text = repr(r)
        assert "501" in text

    def test_not_registered_by_default(self):
        r = PhotonReactionBase(
            type_=PHOTON_REACTION_COMPTON,
            MT=502,
            xs=np.array([1.0]),
            xs_offset=0,
            reference_frame=REFERENCE_FRAME_LAB,
        )
        assert r.ID == -1


# =============================================================================
# PhotonReactionCompton
# =============================================================================


class TestPhotonReactionCompton:
    def test_type_is_compton(self):
        r = _make_reaction(PhotonReactionCompton)
        assert r.type == PHOTON_REACTION_COMPTON

    def test_mt_stored(self):
        r = _make_reaction(PhotonReactionCompton)
        assert r.MT == 500

    def test_scattered_energy_less_than_input(self):
        """Compton scattering must reduce or preserve photon energy."""
        np.random.seed(42)
        r = _make_reaction(PhotonReactionCompton)
        for _ in range(100):
            p = _make_particle(E=1.0)
            r.perform_collision(p, None, None)
            assert p[0]["E"] <= 1.0 + 1e-12

    def test_energy_strictly_positive(self):
        """Scattered photon energy must remain positive."""
        np.random.seed(0)
        r = _make_reaction(PhotonReactionCompton)
        for _ in range(100):
            p = _make_particle(E=0.1)
            r.perform_collision(p, None, None)
            assert p[0]["E"] > 0.0

    def test_direction_is_unit_vector(self):
        """After scatter the direction vector must remain normalised."""
        np.random.seed(7)
        r = _make_reaction(PhotonReactionCompton)
        for _ in range(100):
            p = _make_particle(E=1.0, ux=0.0, uy=0.0, uz=1.0)
            r.perform_collision(p, None, None)
            norm = math.sqrt(
                float(p[0]["ux"]) ** 2
                + float(p[0]["uy"]) ** 2
                + float(p[0]["uz"]) ** 2
            )
            assert abs(norm - 1.0) < 1e-10

    def test_direction_unit_vector_oblique_input(self):
        """Normalisation holds for a non-axial initial direction."""
        np.random.seed(13)
        r = _make_reaction(PhotonReactionCompton)
        ux0 = 1.0 / math.sqrt(3)
        uy0 = 1.0 / math.sqrt(3)
        uz0 = 1.0 / math.sqrt(3)
        for _ in range(50):
            p = _make_particle(E=1.0, ux=ux0, uy=uy0, uz=uz0)
            r.perform_collision(p, None, None)
            norm = math.sqrt(
                float(p[0]["ux"]) ** 2
                + float(p[0]["uy"]) ** 2
                + float(p[0]["uz"]) ** 2
            )
            assert abs(norm - 1.0) < 1e-10

    def test_uz_near_one_branch(self):
        """Exercises the |uz| ≥ 1-eps fallback branch in direction rotation."""
        np.random.seed(99)
        r = _make_reaction(PhotonReactionCompton)
        for seed in range(20):
            np.random.seed(seed)
            p = _make_particle(E=1.0, ux=0.0, uy=0.0, uz=1.0 - 1e-11)
            r.perform_collision(p, None, None)
            norm = math.sqrt(
                float(p[0]["ux"]) ** 2
                + float(p[0]["uy"]) ** 2
                + float(p[0]["uz"]) ** 2
            )
            assert abs(norm - 1.0) < 1e-9

    def test_uz_near_minus_one_branch(self):
        """Exercises the else branch with uz near -1."""
        np.random.seed(5)
        r = _make_reaction(PhotonReactionCompton)
        p = _make_particle(E=1.0, ux=0.0, uy=0.0, uz=-(1.0 - 1e-11))
        r.perform_collision(p, None, None)
        norm = math.sqrt(
            float(p[0]["ux"]) ** 2
            + float(p[0]["uy"]) ** 2
            + float(p[0]["uz"]) ** 2
        )
        assert abs(norm - 1.0) < 1e-9

    def test_high_energy_scatter(self):
        """At 10 MeV photon energy scatters with large energy loss."""
        np.random.seed(42)
        r = _make_reaction(PhotonReactionCompton)
        losses = []
        for seed in range(100):
            np.random.seed(seed)
            p = _make_particle(E=10.0)
            r.perform_collision(p, None, None)
            losses.append(10.0 - float(p[0]["E"]))
        assert max(losses) > 0.5  # significant energy losses expected

    def test_low_energy_scatter(self):
        """At 10 keV photon energy (Thomson limit) energy change is small."""
        np.random.seed(42)
        r = _make_reaction(PhotonReactionCompton)
        for seed in range(20):
            np.random.seed(seed)
            p = _make_particle(E=0.01)
            r.perform_collision(p, None, None)
            # At 10 keV, kappa ~ 0.02 → eps very close to 1, tiny energy loss
            assert float(p[0]["E"]) > 0.009

    def test_particle_stays_alive(self):
        """Compton scattering does not kill the photon."""
        np.random.seed(0)
        r = _make_reaction(PhotonReactionCompton)
        for _ in range(50):
            p = _make_particle(E=1.0)
            r.perform_collision(p, None, None)
            assert p[0]["alive"]


# =============================================================================
# PhotonReactionPhotoelectric
# =============================================================================


class TestPhotonReactionPhotoelectric:
    def test_type_is_photoelectric(self):
        r = _make_reaction(PhotonReactionPhotoelectric)
        assert r.type == PHOTON_REACTION_PHOTOELECTRIC

    def test_particle_killed(self):
        """Photoelectric absorption sets alive=False."""
        r = _make_reaction(PhotonReactionPhotoelectric)
        p = _make_particle(E=0.05, alive=True)
        r.perform_collision(p, None, None)
        assert not p[0]["alive"]

    def test_energy_unchanged(self):
        """Photoelectric absorption does not modify the photon energy."""
        r = _make_reaction(PhotonReactionPhotoelectric)
        E_in = 0.03
        p = _make_particle(E=E_in)
        r.perform_collision(p, None, None)
        assert float(p[0]["E"]) == E_in

    def test_direction_unchanged(self):
        """Photoelectric absorption does not modify the photon direction."""
        r = _make_reaction(PhotonReactionPhotoelectric)
        p = _make_particle(E=0.05, ux=0.5, uy=0.5, uz=1.0 / math.sqrt(2))
        r.perform_collision(p, None, None)
        assert float(p[0]["ux"]) == pytest.approx(0.5)
        assert float(p[0]["uy"]) == pytest.approx(0.5)

    def test_low_energy_absorbed(self):
        """Works correctly at very low photon energies (1 keV)."""
        r = _make_reaction(PhotonReactionPhotoelectric)
        p = _make_particle(E=0.001)
        r.perform_collision(p, None, None)
        assert not p[0]["alive"]


# =============================================================================
# PhotonReactionPairProduction
# =============================================================================


class TestPhotonReactionPairProduction:
    def test_type_is_pair_production(self):
        r = _make_reaction(PhotonReactionPairProduction)
        assert r.type == PHOTON_REACTION_PAIR_PRODUCTION

    def test_particle_killed_above_threshold(self):
        """Pair production above 1.022 MeV sets alive=False."""
        r = _make_reaction(PhotonReactionPairProduction)
        p = _make_particle(E=2.0)
        r.perform_collision(p, None, None)
        assert not p[0]["alive"]

    def test_particle_killed_at_high_energy(self):
        """Pair production at 10 MeV sets alive=False."""
        r = _make_reaction(PhotonReactionPairProduction)
        p = _make_particle(E=10.0)
        r.perform_collision(p, None, None)
        assert not p[0]["alive"]

    def test_energy_unchanged_after_kill(self):
        """Energy field is not modified (particle is simply killed)."""
        r = _make_reaction(PhotonReactionPairProduction)
        E_in = 5.0
        p = _make_particle(E=E_in)
        r.perform_collision(p, None, None)
        assert float(p[0]["E"]) == E_in


# =============================================================================
# decode_type helper
# =============================================================================


class TestDecodeType:
    def test_compton(self):
        assert decode_type(PHOTON_REACTION_COMPTON) == "Photon Compton scattering"

    def test_photoelectric(self):
        assert (
            decode_type(PHOTON_REACTION_PHOTOELECTRIC)
            == "Photon photoelectric absorption"
        )

    def test_pair_production(self):
        assert decode_type(PHOTON_REACTION_PAIR_PRODUCTION) == "Photon pair production"

    def test_total(self):
        assert decode_type(PHOTON_REACTION_TOTAL) == "Photon total"

    def test_unknown(self):
        assert decode_type(999) == "Unknown"


# =============================================================================
# Physical constant exports
# =============================================================================


class TestPhysicalConstants:
    def test_speed_of_light(self):
        assert abs(_SPEED_OF_LIGHT - 29.9792458) < 1e-6

    def test_electron_rest_mass(self):
        assert abs(_M_E - 0.51099895) < 1e-7

    def test_pair_threshold(self):
        assert abs(_PAIR_THRESH - 1.02199790) < 1e-6

    def test_pair_threshold_is_twice_me(self):
        assert abs(_PAIR_THRESH - 2.0 * _M_E) < 1e-12
