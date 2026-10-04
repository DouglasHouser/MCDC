"""
Phase 1 structural validation tests.

Verifies that all required files, directories, and imports are in place
after Phase 1 implementation.  These tests should all pass before
proceeding to Phase 2 (cross-section implementation).

Run with::

    pytest test/unit/photon/test_phase1_structure.py -v

All tests should be run from the photon-transport-code/ root directory.
"""

import importlib
import inspect
import os

import pytest

# Resolve photon_transport_code root regardless of pytest invocation directory.
# This file lives at  .../photon_transport_code/test/unit/photon/
# The module root is  3 levels up:  ../../..
_MODULE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)


def _p(relative_path):
    """Return an absolute path rooted at the photon_transport_code directory."""
    return os.path.join(_MODULE_ROOT, relative_path)


# ======================================================================================
# Directory structure tests
# ======================================================================================


def test_photon_physics_directory_exists():
    """Verify that the photon physics module directory exists."""
    assert os.path.isdir(
        _p("transport/physics/photon")
    ), "Missing directory: transport/physics/photon/"


def test_mcdc_set_directory_exists():
    """Verify that the mcdc_set directory exists."""
    assert os.path.isdir(_p("mcdc_set")), "Missing directory: mcdc_set/"


def test_test_unit_photon_directory_exists():
    """Verify that the unit test directory for photon exists."""
    assert os.path.isdir(_p("test/unit/photon")), "Missing directory: test/unit/photon/"


def test_test_regression_photon_directory_exists():
    """Verify that the regression test directory for photon exists."""
    assert os.path.isdir(
        _p("test/regression/photon")
    ), "Missing directory: test/regression/photon/"


# ======================================================================================
# File existence tests
# ======================================================================================


@pytest.mark.parametrize(
    "filepath",
    [
        "transport/physics/photon/__init__.py",
        "transport/physics/photon/interface.py",
        "transport/physics/photon/cross_sections.py",
        "transport/physics/photon/distributions.py",
        "transport/physics/photon/native.py",
        "transport/physics/photon/util.py",
    ],
)
def test_core_physics_files_exist(filepath):
    """Verify all six core physics module files are present."""
    assert os.path.isfile(_p(filepath)), f"Missing file: {filepath}"


def test_photon_material_set_exists():
    """Verify mcdc_set/photon_material.py exists."""
    assert os.path.isfile(
        _p("mcdc_set/photon_material.py")
    ), "Missing file: mcdc_set/photon_material.py"


def test_conftest_exists():
    """Verify test/unit/photon/conftest.py exists."""
    assert os.path.isfile(
        _p("test/unit/photon/conftest.py")
    ), "Missing file: test/unit/photon/conftest.py"


@pytest.mark.parametrize(
    "filepath",
    [
        "transport/__init__.py",
        "transport/physics/__init__.py",
        "transport/physics/photon/__init__.py",
        "mcdc_set/__init__.py",
        "test/__init__.py",
        "test/unit/__init__.py",
        "test/unit/photon/__init__.py",
        "test/regression/__init__.py",
        "test/regression/photon/__init__.py",
    ],
)
def test_init_files_exist(filepath):
    """Verify all __init__.py package markers are in place."""
    assert os.path.isfile(_p(filepath)), f"Missing __init__.py: {filepath}"


# ======================================================================================
# Import tests
# ======================================================================================


def test_photon_module_importable():
    """Verify that the photon physics package can be imported without errors."""
    mod = importlib.import_module("transport.physics.photon")
    assert mod is not None


def test_interface_importable():
    """Verify transport.physics.photon.interface imports cleanly."""
    mod = importlib.import_module("transport.physics.photon.interface")
    assert mod is not None


def test_cross_sections_importable():
    """Verify transport.physics.photon.cross_sections imports cleanly."""
    mod = importlib.import_module("transport.physics.photon.cross_sections")
    assert mod is not None


def test_distributions_importable():
    """Verify transport.physics.photon.distributions imports cleanly."""
    mod = importlib.import_module("transport.physics.photon.distributions")
    assert mod is not None


def test_native_importable():
    """Verify transport.physics.photon.native imports cleanly."""
    mod = importlib.import_module("transport.physics.photon.native")
    assert mod is not None


def test_util_importable():
    """Verify transport.physics.photon.util imports cleanly."""
    mod = importlib.import_module("transport.physics.photon.util")
    assert mod is not None


def test_photon_material_importable():
    """Verify mcdc_set.photon_material imports cleanly."""
    mod = importlib.import_module("mcdc_set.photon_material")
    assert mod is not None


# ======================================================================================
# Public API surface tests
# ======================================================================================


def test_interface_has_required_functions():
    """Verify that interface.py exports the required public functions."""
    from transport.physics.photon import interface

    required = ["particle_speed", "macro_xs", "collision", "photon_production_xs"]
    for name in required:
        assert hasattr(interface, name), f"interface.py missing function: {name}"
        assert callable(getattr(interface, name))


def test_cross_sections_has_required_functions():
    """Verify that cross_sections.py exports the required public functions."""
    from transport.physics.photon import cross_sections

    required = [
        "klein_nishina_total",
        "klein_nishina_differential",
        "photoelectric_xs",
        "pair_production_xs",
        "total_xs",
        "macro_compton_xs",
        "macro_photoelectric_xs",
        "macro_pair_production_xs",
        "macro_total_xs",
    ]
    for name in required:
        assert hasattr(
            cross_sections, name
        ), f"cross_sections.py missing function: {name}"


def test_distributions_has_required_functions():
    """Verify that distributions.py exports the required public functions."""
    from transport.physics.photon import distributions

    required = [
        "sample_klein_nishina",
        "sample_pair_production",
        "sample_photoelectric",
    ]
    for name in required:
        assert hasattr(
            distributions, name
        ), f"distributions.py missing function: {name}"


def test_native_has_required_functions():
    """Verify that native.py exports the required public functions."""
    from transport.physics.photon import native

    required = [
        "interpolate_xs",
        "find_energy_bin",
        "get_element_xs",
        "compton_xs",
        "photoelectric_xs",
        "pair_production_xs",
    ]
    for name in required:
        assert hasattr(native, name), f"native.py missing function: {name}"


def test_util_has_required_functions():
    """Verify that util.py exports the required public functions."""
    from transport.physics.photon import util

    required = [
        "compton_scattered_energy",
        "compton_scattering_cosine",
        "pair_production_threshold",
        "electron_rest_mass_energy",
        "log_log_interpolation",
        "scatter_direction",
    ]
    for name in required:
        assert hasattr(util, name), f"util.py missing function: {name}"


def test_photon_material_has_required_functions():
    """Verify that mcdc_set/photon_material.py exports the required functions."""
    from mcdc_set import photon_material as pm

    required = ["photon_material", "add_photon_material_to_mcdc"]
    for name in required:
        assert hasattr(pm, name), f"photon_material.py missing: {name}"


# ======================================================================================
# Docstring completeness tests
# ======================================================================================


def _get_public_callables(module):
    """Return all public callable objects from a module."""
    return [
        (name, obj)
        for name, obj in inspect.getmembers(module, callable)
        if not name.startswith("_") and inspect.getmodule(obj) is module
    ]


@pytest.mark.parametrize(
    "module_path",
    [
        "transport.physics.photon.interface",
        "transport.physics.photon.cross_sections",
        "transport.physics.photon.distributions",
        "transport.physics.photon.native",
        "transport.physics.photon.util",
        "mcdc_set.photon_material",
    ],
)
def test_all_public_functions_have_docstrings(module_path):
    """Verify every public function in each module has a docstring."""
    mod = importlib.import_module(module_path)
    callables = _get_public_callables(mod)
    # At least some functions should be present
    assert len(callables) > 0, f"{module_path} has no public functions"
    for name, func in callables:
        assert (
            func.__doc__ is not None and func.__doc__.strip() != ""
        ), f"{module_path}.{name} is missing a docstring"


# ======================================================================================
# util constants tests
# ======================================================================================


def test_util_physical_constants_present():
    """Verify that util.py exposes the required physical constants."""
    from transport.physics.photon import util

    assert hasattr(util, "ELECTRON_REST_MASS_ENERGY")
    assert hasattr(util, "CLASSICAL_ELECTRON_RADIUS")
    assert hasattr(util, "THOMSON_CROSS_SECTION")
    assert hasattr(util, "PAIR_PRODUCTION_THRESHOLD")


def test_util_electron_rest_mass_value():
    """Verify ELECTRON_REST_MASS_ENERGY is approximately 0.511 MeV."""
    from transport.physics.photon import util

    assert abs(util.ELECTRON_REST_MASS_ENERGY - 0.511) < 1e-3


def test_util_pair_production_threshold_value():
    """Verify PAIR_PRODUCTION_THRESHOLD is approximately 1.022 MeV."""
    from transport.physics.photon import util

    assert abs(util.PAIR_PRODUCTION_THRESHOLD - 1.022) < 1e-3
