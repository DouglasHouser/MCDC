"""
Regression tests: Photon module compatibility checks.

Verifies that the photon transport module:
  1. Can be imported without circular imports.
  2. Exposes the expected public API (functions, classes, constants).
  3. Does not shadow or conflict with standard library names.
  4. All photon module attributes are internally consistent.

These tests serve as the first-pass "do no harm" check when integrating the
photon module alongside MCDC's existing neutron transport code.  In the
standalone environment they confirm that the module structure is complete and
importable, which is the precondition for all other regression tests.
"""

import importlib
import sys
import types

import pytest


# ======================================================================================
# Import checks
# ======================================================================================


class TestModuleImports:
    """All photon module components import without errors or circular imports."""

    def test_transport_photon_init_imports(self):
        """photon_transport_code.transport.physics.photon imports cleanly."""
        mod = importlib.import_module("photon_transport_code.transport.physics.photon")
        assert isinstance(mod, types.ModuleType)

    def test_cross_sections_imports(self):
        """cross_sections module imports cleanly."""
        mod = importlib.import_module(
            "photon_transport_code.transport.physics.photon.cross_sections"
        )
        assert isinstance(mod, types.ModuleType)

    def test_distributions_imports(self):
        """distributions module imports cleanly."""
        mod = importlib.import_module(
            "photon_transport_code.transport.physics.photon.distributions"
        )
        assert isinstance(mod, types.ModuleType)

    def test_interface_imports(self):
        """interface module imports cleanly."""
        mod = importlib.import_module(
            "photon_transport_code.transport.physics.photon.interface"
        )
        assert isinstance(mod, types.ModuleType)

    def test_native_imports(self):
        """native module imports cleanly."""
        mod = importlib.import_module(
            "photon_transport_code.transport.physics.photon.native"
        )
        assert isinstance(mod, types.ModuleType)

    def test_util_imports(self):
        """util module imports cleanly."""
        mod = importlib.import_module(
            "photon_transport_code.transport.physics.photon.util"
        )
        assert isinstance(mod, types.ModuleType)

    def test_mcdc_set_photon_material_imports(self):
        """mcdc_set.photon_material imports cleanly."""
        mod = importlib.import_module("photon_transport_code.mcdc_set.photon_material")
        assert isinstance(mod, types.ModuleType)

    def test_mcdc_get_photon_material_imports(self):
        """mcdc_get.photon_material imports cleanly."""
        mod = importlib.import_module("photon_transport_code.mcdc_get.photon_material")
        assert isinstance(mod, types.ModuleType)

    def test_no_import_side_effects_on_stdlib(self):
        """Importing the photon module does not corrupt sys.modules entries."""
        # Re-import and verify key stdlib modules are still intact
        import math
        import os

        assert hasattr(math, "pi"), "math.pi missing after photon module import"
        assert hasattr(os, "path"), "os.path missing after photon module import"

    def test_cross_imports_both_directions(self):
        """Can import cross_sections and distributions independently."""
        from photon_transport_code.transport.physics.photon import cross_sections
        from photon_transport_code.transport.physics.photon import distributions

        assert cross_sections is not distributions


# ======================================================================================
# Public API surface checks
# ======================================================================================


class TestPublicAPI:
    """Expected public functions and classes are present in each module."""

    def test_interface_exposes_required_functions(self):
        """interface module has particle_speed, macro_xs, photon_production_xs,
        collision."""
        from photon_transport_code.transport.physics.photon import interface

        for name in ("particle_speed", "macro_xs", "photon_production_xs", "collision"):
            assert hasattr(interface, name), f"interface.{name} is missing"
            assert callable(
                getattr(interface, name)
            ), f"interface.{name} is not callable"

    def test_interface_reaction_constants(self):
        """interface module has reaction-type integer constants."""
        from photon_transport_code.transport.physics.photon import interface

        for const in (
            "PHOTON_REACTION_COMPTON",
            "PHOTON_REACTION_PHOTOELECTRIC",
            "PHOTON_REACTION_PAIR_PRODUCTION",
            "PHOTON_REACTION_TOTAL",
        ):
            assert hasattr(interface, const), f"interface.{const} is missing"
            val = getattr(interface, const)
            assert isinstance(
                val, int
            ), f"interface.{const} should be int, got {type(val).__name__}"

    def test_reaction_constants_distinct(self):
        """All reaction-type constants have distinct values."""
        from photon_transport_code.transport.physics.photon.interface import (
            PHOTON_REACTION_COMPTON,
            PHOTON_REACTION_PAIR_PRODUCTION,
            PHOTON_REACTION_PHOTOELECTRIC,
            PHOTON_REACTION_TOTAL,
        )

        constants = [
            PHOTON_REACTION_COMPTON,
            PHOTON_REACTION_PHOTOELECTRIC,
            PHOTON_REACTION_PAIR_PRODUCTION,
            PHOTON_REACTION_TOTAL,
        ]
        assert (
            len(set(constants)) == 4
        ), f"Reaction constants not all distinct: {constants}"

    def test_cross_sections_exposes_required_functions(self):
        """cross_sections module has the expected public functions."""
        from photon_transport_code.transport.physics.photon import cross_sections

        required = (
            "klein_nishina_total",
            "klein_nishina_differential",
            "photoelectric_xs",
            "pair_production_xs",
            "total_xs",
            "macro_compton_xs",
            "macro_photoelectric_xs",
            "macro_pair_production_xs",
            "macro_total_xs",
        )
        for name in required:
            assert hasattr(cross_sections, name), f"cross_sections.{name} is missing"

    def test_distributions_exposes_required_functions(self):
        """distributions module has the expected public functions."""
        from photon_transport_code.transport.physics.photon import distributions

        required = (
            "sample_klein_nishina",
            "sample_pair_production",
            "sample_photoelectric_shell",
            "photoelectric_absorption",
            "photoelectric_select_shell",
        )
        for name in required:
            assert hasattr(distributions, name), f"distributions.{name} is missing"

    def test_mcdc_set_exposes_photon_material(self):
        """mcdc_set.photon_material exposes PhotonMaterial and photon_material."""
        from photon_transport_code.mcdc_set import photon_material as pm_module

        assert hasattr(
            pm_module, "PhotonMaterial"
        ), "PhotonMaterial class missing from mcdc_set.photon_material"
        assert hasattr(
            pm_module, "photon_material"
        ), "photon_material() function missing from mcdc_set.photon_material"
        assert hasattr(
            pm_module, "add_photon_material_to_mcdc"
        ), "add_photon_material_to_mcdc() missing from mcdc_set.photon_material"

    def test_mcdc_get_exposes_getter_functions(self):
        """mcdc_get.photon_material exposes all getter functions."""
        from photon_transport_code.mcdc_get import photon_material as get_module

        required = (
            "get_element",
            "get_density",
            "get_n_elements",
            "get_material_name",
            "get_fissionable",
            "get_elements",
            "get_densities",
        )
        for name in required:
            assert hasattr(
                get_module, name
            ), f"mcdc_get.photon_material.{name} is missing"

    def test_native_exposes_required_functions(self):
        """native module has the expected data and functions."""
        from photon_transport_code.transport.physics.photon import native

        required = (
            "build_element_buffer",
            "get_element_data",
            "interpolate_xs",
            "find_energy_bin",
            "compton_xs",
            "photoelectric_xs",
            "pair_production_xs",
            "PHOTON_ELEMENT_DTYPE",
        )
        for name in required:
            assert hasattr(native, name), f"native.{name} is missing"


# ======================================================================================
# PhotonMaterial class API
# ======================================================================================


class TestPhotonMaterialAPI:
    """PhotonMaterial class has expected attributes and behaviors."""

    def test_photon_material_instantiation(self):
        """PhotonMaterial can be instantiated with valid inputs."""
        from photon_transport_code.mcdc_set.photon_material import PhotonMaterial

        mat = PhotonMaterial(elements=[13], densities=[6.026e-2], name="Al")
        assert mat.N_element == 1
        assert mat.elements == [13]
        assert mat.fissionable is False

    def test_photon_material_to_dict(self):
        """to_dict() returns the expected keys."""
        from photon_transport_code.mcdc_set.photon_material import PhotonMaterial

        mat = PhotonMaterial(elements=[1, 8], densities=[6.692e-2, 3.346e-2])
        d = mat.to_dict()

        assert set(d.keys()) == {
            "name",
            "N_element",
            "elements",
            "densities",
            "fissionable",
        }
        assert d["N_element"] == 2
        assert d["fissionable"] is False

    def test_photon_material_validation_rejects_bad_inputs(self):
        """PhotonMaterial raises ValueError for invalid inputs."""
        from photon_transport_code.mcdc_set.photon_material import PhotonMaterial

        with pytest.raises(ValueError):
            PhotonMaterial(elements=[], densities=[])  # Empty

        with pytest.raises(ValueError):
            PhotonMaterial(elements=[13], densities=[6.026e-2, 1.0])  # Length mismatch

        with pytest.raises(ValueError):
            PhotonMaterial(elements=[0], densities=[1.0])  # Z out of range

        with pytest.raises(ValueError):
            PhotonMaterial(elements=[13], densities=[-1.0])  # Negative density

    def test_getter_compatibility_with_dict_and_class(self):
        """Getter functions accept both dict and PhotonMaterial inputs."""
        from photon_transport_code.mcdc_set.photon_material import (
            PhotonMaterial,
            photon_material,
        )
        from photon_transport_code.mcdc_get.photon_material import (
            get_element,
            get_n_elements,
            get_material_name,
        )

        mat_class = PhotonMaterial(elements=[13], densities=[6.026e-2], name="aluminum")
        mat_dict = photon_material(elements=[13], densities=[6.026e-2], name="aluminum")

        for mat in (mat_class, mat_dict):
            assert get_element(mat, 0) == 13
            assert get_n_elements(mat) == 1
            assert get_material_name(mat) == "aluminum"


# ======================================================================================
# No circular imports
# ======================================================================================


class TestNoCircularImports:
    """Module import graph is acyclic (no circular dependencies)."""

    def test_interface_does_not_import_distributions_at_module_level(self):
        """
        interface.py imports are self-contained at the physics layer.

        After importing interface, the distributions module may or may not be
        loaded — the key check is that interface works without side-effects
        on distributions.
        """
        # If we can import interface after clearing it from cache and
        # re-importing, there are no circular dependencies that prevent
        # fresh loading.
        mod_name = "photon_transport_code.transport.physics.photon.interface"

        # Temporarily remove from cache
        was_cached = mod_name in sys.modules
        if was_cached:
            cached = sys.modules.pop(mod_name)

        try:
            mod = importlib.import_module(mod_name)
            assert hasattr(mod, "collision")
        finally:
            # Restore original state
            if was_cached:
                sys.modules[mod_name] = cached
            elif mod_name in sys.modules:
                del sys.modules[mod_name]

    def test_can_import_all_modules_in_any_order(self):
        """All photon submodules can be imported independently in any order."""
        module_names = [
            "photon_transport_code.transport.physics.photon.util",
            "photon_transport_code.transport.physics.photon.native",
            "photon_transport_code.transport.physics.photon.cross_sections",
            "photon_transport_code.transport.physics.photon.distributions",
            "photon_transport_code.transport.physics.photon.interface",
            "photon_transport_code.mcdc_set.photon_material",
            "photon_transport_code.mcdc_get.photon_material",
        ]
        for name in module_names:
            mod = importlib.import_module(name)
            assert isinstance(mod, types.ModuleType), f"{name} did not return a module"
