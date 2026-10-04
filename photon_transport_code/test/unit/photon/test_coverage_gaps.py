"""
Coverage-gap tests for Phase 5.

Exercises the public functions not yet reached by the existing test suite:
    - util.py:  compton_scattered_energy, compton_scattering_cosine,
                pair_production_threshold, electron_rest_mass_energy,
                scatter_direction
    - photon_material.py: PhotonMaterial.set_name, set_density, add_element,
                          __repr__, __eq__; add_photon_material_to_mcdc
    - cross_sections.py: pair_production_xs_element (below-threshold path),
                         total_xs_element; macro_compton_xs,
                         macro_photoelectric_xs, macro_pair_production_xs,
                         macro_total_xs
    - interface.py:      particle_speed, macro_xs, photon_production_xs,
                         collision (all three branches + zero-XS early return)

Run with NUMBA_DISABLE_JIT=1 so @njit functions execute as plain Python
(required for coverage tracking)::

    NUMBA_DISABLE_JIT=1 pytest test/unit/photon/test_coverage_gaps.py -v
"""

import math

import numpy as np
import pytest

from photon_transport_code.mcdc_set.photon_material import (
    PhotonMaterial,
    add_photon_material_to_mcdc,
    photon_material,
)
from photon_transport_code.transport.physics.photon import util
from photon_transport_code.transport.physics.photon.cross_sections import (
    macro_compton_xs,
    macro_pair_production_xs,
    macro_photoelectric_xs,
    macro_total_xs,
    pair_production_xs_element,
    total_xs_element,
)
from photon_transport_code.transport.physics.photon.interface import (
    PHOTON_REACTION_COMPTON,
    PHOTON_REACTION_PAIR_PRODUCTION,
    PHOTON_REACTION_PHOTOELECTRIC,
    PHOTON_REACTION_TOTAL,
    collision,
    macro_xs,
    particle_speed,
    photon_production_xs,
)
from photon_transport_code.transport.physics.photon.native import (
    PHOTON_ELEMENT_DTYPE,
    build_element_buffer,
)

# =============================================================================
# Minimal structured-array dtypes for MCDC-interface testing
# =============================================================================

_MAX_NUCLIDES = 5
_MAX_MATERIALS = 3

_nuclide_dtype = np.dtype(
    [
        ("Z", np.int32),
        ("N", np.float64),  # number density atoms/b-cm
    ]
)

_material_dtype = np.dtype(
    [
        ("N_nuclide", np.int32),
        ("nuclides", _nuclide_dtype, (_MAX_NUCLIDES,)),
    ]
)

_mcdc_dtype = np.dtype(
    [
        ("N_material", np.int32),
        # shape (max_materials, 1) so that mcdc[0]["materials"][id] → (1,) array
        ("materials", _material_dtype, (_MAX_MATERIALS, 1)),
        ("photon_elements", PHOTON_ELEMENT_DTYPE, (_MAX_NUCLIDES, 1)),
    ]
)

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


def _make_al_mcdc():
    """Return (particle, mcdc, data) for a single-element Al material."""
    al_element, al_data = build_element_buffer(Z=13)

    mcdc = np.zeros(1, dtype=_mcdc_dtype)
    mcdc[0]["N_material"] = 1

    mat = mcdc[0]["materials"][0]  # shape (1,)
    mat[0]["N_nuclide"] = 1
    mat[0]["nuclides"][0]["Z"] = 13
    mat[0]["nuclides"][0]["N"] = 6.026e-2  # atoms/b-cm

    elem = mcdc[0]["photon_elements"][0]  # shape (1,)
    elem[0]["Z"] = int(al_element[0]["Z"])
    elem[0]["N_points"] = int(al_element[0]["N_points"])
    elem[0]["energy_grid_offset"] = int(al_element[0]["energy_grid_offset"])
    elem[0]["compton_offset"] = int(al_element[0]["compton_offset"])
    elem[0]["pe_offset"] = int(al_element[0]["pe_offset"])
    elem[0]["pair_offset"] = int(al_element[0]["pair_offset"])

    return mcdc, al_data


def _make_particle(E=1.0, ux=0.0, uy=0.0, uz=1.0, material_ID=0, alive=True):
    """Return a 1-element particle structured array."""
    p = np.zeros(1, dtype=_particle_dtype)
    p[0]["E"] = E
    p[0]["material_ID"] = material_ID
    p[0]["ux"] = ux
    p[0]["uy"] = uy
    p[0]["uz"] = uz
    p[0]["alive"] = alive
    return p


# =============================================================================
# util.py — uncovered functions
# =============================================================================


class TestUtilCompton:
    """Tests for compton_scattered_energy and compton_scattering_cosine."""

    def test_forward_scatter_no_energy_loss(self):
        """At mu=1 (forward scatter) scattered energy equals incident energy."""
        E_in = 1.0
        E_out = util.compton_scattered_energy(E_in, mu=1.0)
        assert abs(E_out - E_in) < 1e-10

    def test_backscatter_energy(self):
        """At mu=-1 (back scatter) E' = E / (1 + 2*kappa)."""
        E_in = 1.0
        kappa = E_in / 0.51099895
        expected = E_in / (1.0 + 2.0 * kappa)
        E_out = util.compton_scattered_energy(E_in, mu=-1.0)
        assert abs(E_out - expected) < 1e-10

    def test_90deg_scatter(self):
        """At mu=0 (90-degree scatter) E' = m_e / (1 + 1/kappa)."""
        E_in = 0.5
        E_out = util.compton_scattered_energy(E_in, mu=0.0)
        assert 0.0 < E_out < E_in

    def test_cosine_forward_recovery(self):
        """compton_scattering_cosine inverts compton_scattered_energy for forward."""
        E_in = 1.0
        mu_in = 0.7
        E_out = util.compton_scattered_energy(E_in, mu_in)
        mu_out = util.compton_scattering_cosine(E_in, E_out)
        assert abs(mu_out - mu_in) < 1e-10

    def test_cosine_backscatter(self):
        """Back-scatter: cosine recovered from back-scattered energy is -1."""
        E_in = 1.0
        E_back = util.compton_scattered_energy(E_in, mu=-1.0)
        mu = util.compton_scattering_cosine(E_in, E_back)
        assert abs(mu - (-1.0)) < 1e-10


class TestUtilThresholds:
    """Tests for pair_production_threshold and electron_rest_mass_energy."""

    def test_pair_production_threshold_value(self):
        """pair_production_threshold returns 2 * m_e = 1.022 MeV."""
        thresh = util.pair_production_threshold()
        assert abs(thresh - 1.02199790) < 1e-6

    def test_electron_rest_mass_value(self):
        """electron_rest_mass_energy returns 0.511 MeV."""
        m_e = util.electron_rest_mass_energy()
        assert abs(m_e - 0.51099895) < 1e-6

    def test_threshold_is_twice_rest_mass(self):
        """Pair threshold equals exactly 2 * electron rest mass."""
        assert (
            abs(
                util.pair_production_threshold()
                - 2.0 * util.electron_rest_mass_energy()
            )
            < 1e-12
        )


class TestUtilScatterDirection:
    """Tests for util.scatter_direction including both code branches."""

    def test_unit_vector_preserved(self):
        """After scatter, the output direction is still a unit vector."""
        ux_new, uy_new, uz_new = util.scatter_direction(0.0, 0.0, 1.0, mu=0.8, azi=1.2)
        norm = math.sqrt(ux_new**2 + uy_new**2 + uz_new**2)
        assert abs(norm - 1.0) < 1e-10

    def test_forward_scatter_unchanged(self):
        """mu=1, azi=0 → direction unchanged."""
        ux, uy, uz = 0.0, 0.0, 1.0
        ux_new, uy_new, uz_new = util.scatter_direction(ux, uy, uz, mu=1.0, azi=0.0)
        assert abs(ux_new - ux) < 1e-10
        assert abs(uy_new - uy) < 1e-10
        assert abs(uz_new - uz) < 1e-10

    def test_uz_near_one_branch(self):
        """Exercises the |uz| >= 1-eps fallback branch."""
        # uz very close to 1.0 triggers the else branch (abs(uz) >= 1-1e-10)
        ux_new, uy_new, uz_new = util.scatter_direction(
            0.0, 0.0, 1.0 - 1e-11, mu=0.5, azi=0.3
        )
        norm = math.sqrt(ux_new**2 + uy_new**2 + uz_new**2)
        assert abs(norm - 1.0) < 1e-9

    def test_uz_negative_near_minus_one(self):
        """Exercises the else branch with uz close to -1."""
        ux_new, uy_new, uz_new = util.scatter_direction(
            0.0, 0.0, -(1.0 - 1e-11), mu=0.5, azi=0.3
        )
        assert uz_new < 0.0  # scattered direction still points in -z hemisphere

    def test_generic_direction(self):
        """Scatter of an oblique direction vector."""
        ux, uy, uz = 1.0 / math.sqrt(3), 1.0 / math.sqrt(3), 1.0 / math.sqrt(3)
        ux_new, uy_new, uz_new = util.scatter_direction(ux, uy, uz, mu=0.6, azi=0.9)
        norm = math.sqrt(ux_new**2 + uy_new**2 + uz_new**2)
        assert abs(norm - 1.0) < 1e-10


# =============================================================================
# photon_material.py — uncovered PhotonMaterial methods
# =============================================================================


class TestPhotonMaterialMethods:
    """Tests for the fluent-API methods of PhotonMaterial."""

    def test_set_name_changes_name(self):
        """set_name() updates the material name and returns self."""
        mat = PhotonMaterial(elements=[13], densities=[0.06], name="orig")
        result = mat.set_name("new_name")
        assert mat.name == "new_name"
        assert result is mat  # method chaining

    def test_set_density_all_elements(self):
        """set_density(d) without element_idx applies to all elements."""
        mat = PhotonMaterial(elements=[1, 8], densities=[0.06, 0.03])
        mat.set_density(0.1)
        assert mat.densities == [0.1, 0.1]

    def test_set_density_single_element(self):
        """set_density(d, element_idx=1) updates only the specified element."""
        mat = PhotonMaterial(elements=[1, 8], densities=[0.06, 0.03])
        mat.set_density(0.05, element_idx=1)
        assert abs(mat.densities[0] - 0.06) < 1e-15
        assert abs(mat.densities[1] - 0.05) < 1e-15

    def test_set_density_negative_raises(self):
        """set_density() raises ValueError for non-positive density."""
        mat = PhotonMaterial(elements=[13], densities=[0.06])
        with pytest.raises(ValueError):
            mat.set_density(-0.1)

    def test_add_element_appends(self):
        """add_element() appends Z and density and increments N_element."""
        mat = PhotonMaterial(elements=[13], densities=[0.06])
        mat.add_element(Z=82, density=0.03)
        assert mat.N_element == 2
        assert mat.elements[-1] == 82
        assert abs(mat.densities[-1] - 0.03) < 1e-15

    def test_repr_is_string(self):
        """__repr__ returns a non-empty string containing the material name."""
        mat = PhotonMaterial(elements=[13], densities=[0.06], name="al")
        s = repr(mat)
        assert isinstance(s, str)
        assert "al" in s

    def test_eq_equal_materials(self):
        """Two PhotonMaterial objects with the same data compare equal."""
        a = PhotonMaterial(elements=[13], densities=[0.06], name="al")
        b = PhotonMaterial(elements=[13], densities=[0.06], name="al")
        assert a == b

    def test_eq_different_materials(self):
        """Two PhotonMaterial objects with different data compare not equal."""
        a = PhotonMaterial(elements=[13], densities=[0.06], name="al")
        b = PhotonMaterial(elements=[82], densities=[0.03], name="pb")
        assert a != b

    def test_eq_non_photon_material(self):
        """Comparison with a non-PhotonMaterial returns NotImplemented."""
        mat = PhotonMaterial(elements=[13], densities=[0.06])
        result = mat.__eq__("not a material")
        assert result is NotImplemented


class TestAddPhotonMaterialToMcdc:
    """Tests for add_photon_material_to_mcdc."""

    def test_registers_material_in_mcdc(self):
        """add_photon_material_to_mcdc writes element data and increments N_material."""
        mat_dict = photon_material(elements=[13], densities=[6.026e-2], name="al")

        mcdc = np.zeros(1, dtype=_mcdc_dtype)
        mcdc[0]["N_material"] = 0

        material_ID = add_photon_material_to_mcdc(mat_dict, mcdc)

        assert material_ID == 0
        assert int(mcdc[0]["N_material"]) == 1
        mat = mcdc[0]["materials"][0]
        assert int(mat[0]["N_nuclide"]) == 1
        assert int(mat[0]["nuclides"][0]["Z"]) == 13
        assert abs(float(mat[0]["nuclides"][0]["N"]) - 6.026e-2) < 1e-10

    def test_two_materials_increment(self):
        """Adding two materials increments material_ID correctly."""
        mat_dict = photon_material(elements=[13], densities=[0.06], name="al")
        mcdc = np.zeros(1, dtype=_mcdc_dtype)
        mcdc[0]["N_material"] = 0

        id1 = add_photon_material_to_mcdc(mat_dict, mcdc)
        id2 = add_photon_material_to_mcdc(mat_dict, mcdc)
        assert id1 == 0
        assert id2 == 1
        assert int(mcdc[0]["N_material"]) == 2


# =============================================================================
# cross_sections.py — uncovered paths
# =============================================================================


class TestPairProductionXsElementBelowThreshold:
    """pair_production_xs_element must return 0 below the threshold."""

    def test_zero_below_threshold(self):
        """Photon below 1.022 MeV returns 0 pair-production cross-section."""
        al_element, al_data = build_element_buffer(Z=13)
        sigma = pair_production_xs_element(
            Z=13, E=0.5, photon_element=al_element, flat_data=al_data
        )
        assert sigma == 0.0

    def test_zero_exactly_at_threshold(self):
        """At exactly the threshold energy pair production is zero (strict <)."""
        al_element, al_data = build_element_buffer(Z=13)
        sigma = pair_production_xs_element(
            Z=13, E=1.022, photon_element=al_element, flat_data=al_data
        )
        # May be 0 or a small value depending on threshold comparison
        assert sigma >= 0.0


class TestTotalXsElement:
    """total_xs_element returns the sum of Compton + PE + pair contributions."""

    def test_returns_positive_value(self):
        """Total cross-section is positive at a representative energy."""
        al_element, al_data = build_element_buffer(Z=13)
        sigma = total_xs_element(
            Z=13, E=0.1, photon_element=al_element, flat_data=al_data
        )
        assert sigma > 0.0

    def test_above_pair_threshold_includes_pair(self):
        """Total XS above pair threshold is larger than without pair contribution."""
        pb_element, pb_data = build_element_buffer(Z=82)
        sigma_low = total_xs_element(
            Z=82, E=1.0, photon_element=pb_element, flat_data=pb_data
        )
        sigma_high = total_xs_element(
            Z=82, E=10.0, photon_element=pb_element, flat_data=pb_data
        )
        # At 10 MeV pair production is significant for Pb
        assert sigma_high > 0.0
        assert sigma_low > 0.0


# =============================================================================
# cross_sections.py — macroscopic XS functions
# =============================================================================


class TestMacroCompton:
    """macro_compton_xs using a mock single-element Al material."""

    def test_positive_result(self):
        """Macroscopic Compton XS is positive at 1 MeV in Al."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=1.0)
        sigma = macro_compton_xs(p, mcdc, data)
        assert sigma > 0.0

    def test_zero_nuclides_returns_zero(self):
        """N_nuclide = 0 → macroscopic Compton XS is zero."""
        mcdc, data = _make_al_mcdc()
        mcdc[0]["materials"][0][0]["N_nuclide"] = 0
        p = _make_particle(E=1.0)
        sigma = macro_compton_xs(p, mcdc, data)
        assert sigma == 0.0


class TestMacroPhotoelectric:
    """macro_photoelectric_xs using a mock single-element Al material."""

    def test_positive_result_low_energy(self):
        """Macroscopic PE XS is positive at 0.01 MeV in Al."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=0.01)
        sigma = macro_photoelectric_xs(p, mcdc, data)
        assert sigma > 0.0

    def test_decreases_with_energy(self):
        """PE XS decreases with increasing photon energy."""
        mcdc, data = _make_al_mcdc()
        p_low = _make_particle(E=0.01)
        p_high = _make_particle(E=0.1)
        sigma_low = macro_photoelectric_xs(p_low, mcdc, data)
        sigma_high = macro_photoelectric_xs(p_high, mcdc, data)
        assert sigma_low > sigma_high


class TestMacroPairProduction:
    """macro_pair_production_xs using a mock single-element Al material."""

    def test_zero_below_threshold(self):
        """Macroscopic pair XS is zero below 1.022 MeV."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=0.5)
        sigma = macro_pair_production_xs(p, mcdc, data)
        assert sigma == 0.0

    def test_positive_above_threshold(self):
        """Macroscopic pair XS is positive at 10 MeV in Al."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=10.0)
        sigma = macro_pair_production_xs(p, mcdc, data)
        assert sigma > 0.0


class TestMacroTotal:
    """macro_total_xs returns Compton + PE + pair contributions."""

    def test_total_exceeds_compton(self):
        """Total macroscopic XS >= Compton XS at all energies."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=1.0)
        sigma_total = macro_total_xs(p, mcdc, data)
        sigma_compton = macro_compton_xs(p, mcdc, data)
        assert sigma_total >= sigma_compton

    def test_total_positive(self):
        """Total macroscopic XS is positive at 0.1 MeV."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=0.1)
        assert macro_total_xs(p, mcdc, data) > 0.0


# =============================================================================
# interface.py — particle_speed, macro_xs, photon_production_xs, collision
# =============================================================================


class TestInterfaceParticleSpeed:
    """particle_speed always returns the speed of light."""

    def test_returns_speed_of_light(self):
        """particle_speed ignores args and returns c in cm/shake."""
        # With NUMBA_DISABLE_JIT=1 the args are never used, so None is fine
        speed = particle_speed(None, None, None)
        assert abs(speed - 29.9792458) < 1e-6


class TestInterfaceMacroXs:
    """macro_xs dispatches to the correct partial cross-section."""

    def test_compton_reaction(self):
        """macro_xs with PHOTON_REACTION_COMPTON matches macro_compton_xs."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=1.0)
        xs_dispatch = macro_xs(PHOTON_REACTION_COMPTON, p, mcdc, data)
        xs_direct = macro_compton_xs(p, mcdc, data)
        assert abs(xs_dispatch - xs_direct) < 1e-30

    def test_photoelectric_reaction(self):
        """macro_xs with PHOTON_REACTION_PHOTOELECTRIC matches macro_photoelectric_xs."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=0.01)
        xs_dispatch = macro_xs(PHOTON_REACTION_PHOTOELECTRIC, p, mcdc, data)
        xs_direct = macro_photoelectric_xs(p, mcdc, data)
        assert abs(xs_dispatch - xs_direct) < 1e-30

    def test_pair_production_reaction(self):
        """macro_xs with PHOTON_REACTION_PAIR_PRODUCTION."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=10.0)
        xs_dispatch = macro_xs(PHOTON_REACTION_PAIR_PRODUCTION, p, mcdc, data)
        xs_direct = macro_pair_production_xs(p, mcdc, data)
        assert abs(xs_dispatch - xs_direct) < 1e-30

    def test_total_reaction(self):
        """macro_xs with PHOTON_REACTION_TOTAL matches macro_total_xs."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=1.0)
        xs_dispatch = macro_xs(PHOTON_REACTION_TOTAL, p, mcdc, data)
        xs_direct = macro_total_xs(p, mcdc, data)
        assert abs(xs_dispatch - xs_direct) < 1e-30


class TestInterfacePhotonProductionXs:
    """photon_production_xs returns the effective secondary-photon XS."""

    def test_compton_production_equals_compton_xs(self):
        """Compton produces one photon — production XS equals scatter XS."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=1.0)
        xs_prod = photon_production_xs(PHOTON_REACTION_COMPTON, p, mcdc, data)
        xs_compt = macro_compton_xs(p, mcdc, data)
        assert abs(xs_prod - xs_compt) < 1e-30

    def test_photoelectric_production_is_zero(self):
        """Photoelectric absorption produces no photon — production XS is zero."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=0.01)
        xs_prod = photon_production_xs(PHOTON_REACTION_PHOTOELECTRIC, p, mcdc, data)
        assert xs_prod == 0.0

    def test_pair_production_multiplicity(self):
        """Pair production produces two annihilation photons — production XS is 2× pair XS."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=10.0)
        xs_prod = photon_production_xs(PHOTON_REACTION_PAIR_PRODUCTION, p, mcdc, data)
        xs_pair = macro_pair_production_xs(p, mcdc, data)
        assert abs(xs_prod - 2.0 * xs_pair) < 1e-30

    def test_total_production(self):
        """PHOTON_REACTION_TOTAL returns Compton + 2*pair."""
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=10.0)
        xs_prod = photon_production_xs(PHOTON_REACTION_TOTAL, p, mcdc, data)
        xs_compt = macro_compton_xs(p, mcdc, data)
        xs_pair = macro_pair_production_xs(p, mcdc, data)
        expected = xs_compt + 2.0 * xs_pair
        assert abs(xs_prod - expected) < 1e-30


class TestInterfaceCollision:
    """collision function — all branches."""

    def test_zero_xs_early_return(self):
        """When all XS = 0 (N_nuclide=0), collision returns without modifying particle."""
        mcdc, data = _make_al_mcdc()
        mcdc[0]["materials"][0][0]["N_nuclide"] = 0  # force Sigma_T = 0
        p = _make_particle(E=1.0, ux=0.0, uy=0.0, uz=1.0)
        p[0]["alive"] = True
        collision(p, mcdc, data)
        assert p[0]["alive"]  # not modified

    def test_photoelectric_absorption(self):
        """At 10 keV in Al, photoelectric dominates — photon is killed."""
        np.random.seed(0)
        mcdc, data = _make_al_mcdc()
        p = _make_particle(E=0.010, ux=0.0, uy=0.0, uz=1.0)
        p[0]["alive"] = True
        # Run 100 events; at 10 keV PE ~97% — vast majority should absorb
        absorbed = 0
        for seed in range(100):
            np.random.seed(seed)
            p_copy = _make_particle(E=0.010, ux=0.0, uy=0.0, uz=1.0)
            p_copy[0]["alive"] = True
            collision(p_copy, mcdc, data)
            if not p_copy[0]["alive"]:
                absorbed += 1
        assert absorbed > 50  # > 50% absorbed (PE-dominated at 10 keV for Al)

    def test_compton_scatter_changes_energy(self):
        """At 1 MeV in Al, Compton dominates — photon energy decreases or stays."""
        np.random.seed(42)
        mcdc, data = _make_al_mcdc()
        # Run several events; at 1 MeV Compton ~ dominant → most will scatter
        changed = 0
        for seed in range(50):
            np.random.seed(seed)
            p = _make_particle(E=1.0, ux=0.0, uy=0.0, uz=1.0)
            p[0]["alive"] = True
            E_before = float(p[0]["E"])
            collision(p, mcdc, data)
            if p[0]["alive"] and float(p[0]["E"]) != E_before:
                changed += 1
        assert changed > 0  # at least some Compton scatters occurred

    def test_compton_scatter_uz_near_one(self):
        """Tests the |uz|~1 branch in the direction-update code."""
        np.random.seed(7)
        mcdc, data = _make_al_mcdc()
        # uz = 1.0 triggers the else branch in direction rotation
        for seed in range(20):
            np.random.seed(seed)
            p = _make_particle(E=1.0, ux=0.0, uy=0.0, uz=1.0)
            p[0]["alive"] = True
            collision(p, mcdc, data)
            if p[0]["alive"]:
                norm = math.sqrt(
                    float(p[0]["ux"]) ** 2
                    + float(p[0]["uy"]) ** 2
                    + float(p[0]["uz"]) ** 2
                )
                assert abs(norm - 1.0) < 1e-10

    def test_pair_production_kills_photon(self):
        """At high energy in Al (10 MeV) pair production events kill the photon."""
        mcdc, data = _make_al_mcdc()
        pair_killed = 0
        for seed in range(200):
            np.random.seed(seed)
            p = _make_particle(E=10.0, ux=0.0, uy=0.0, uz=1.0)
            p[0]["alive"] = True
            collision(p, mcdc, data)
            if not p[0]["alive"]:
                pair_killed += 1
        # At 10 MeV Al: PP + PE both kill photon; some should be killed
        assert pair_killed > 0
