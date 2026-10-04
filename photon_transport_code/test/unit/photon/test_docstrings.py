"""
Phase 5 code-quality test: verify all public functions in the photon transport
module have non-empty docstrings.

Run with::

    pytest test/unit/photon/test_docstrings.py -v
"""

import inspect
import types

import pytest


# =============================================================================
# Helpers
# =============================================================================


def _public_callables(module):
    """Yield (name, obj) pairs for public callable objects in ``module``."""
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        if callable(obj) and not isinstance(obj, type):
            yield name, obj


def _public_classes(module):
    """Yield (name, cls) pairs for public classes defined in ``module``."""
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        if isinstance(obj, type) and obj.__module__ == module.__name__:
            yield name, obj


# =============================================================================
# Modules under test
# =============================================================================


@pytest.fixture(scope="module")
def interface_module():
    from photon_transport_code.transport.physics.photon import interface

    return interface


@pytest.fixture(scope="module")
def cross_sections_module():
    from photon_transport_code.transport.physics.photon import cross_sections

    return cross_sections


@pytest.fixture(scope="module")
def distributions_module():
    from photon_transport_code.transport.physics.photon import distributions

    return distributions


@pytest.fixture(scope="module")
def native_module():
    from photon_transport_code.transport.physics.photon import native

    return native


@pytest.fixture(scope="module")
def util_module():
    from photon_transport_code.transport.physics.photon import util

    return util


@pytest.fixture(scope="module")
def photon_material_module():
    from photon_transport_code.mcdc_set import photon_material as pm

    return pm


@pytest.fixture(scope="module")
def photon_material_get_module():
    from photon_transport_code.mcdc_get import photon_material as pm_get

    return pm_get


# =============================================================================
# Test: all public functions have docstrings
# =============================================================================


def _check_module_docstrings(module, module_label):
    """Assert every public callable in ``module`` has a non-empty docstring."""
    missing = []
    for name, obj in _public_callables(module):
        doc = getattr(obj, "__doc__", None)
        if not doc or not doc.strip():
            missing.append(f"{module_label}.{name}")
    return missing


def test_interface_docstrings(interface_module):
    """All public functions in interface.py have docstrings."""
    missing = _check_module_docstrings(interface_module, "interface")
    assert not missing, f"Missing docstrings: {missing}"


def test_cross_sections_docstrings(cross_sections_module):
    """All public functions in cross_sections.py have docstrings."""
    missing = _check_module_docstrings(cross_sections_module, "cross_sections")
    assert not missing, f"Missing docstrings: {missing}"


def test_distributions_docstrings(distributions_module):
    """All public functions in distributions.py have docstrings."""
    missing = _check_module_docstrings(distributions_module, "distributions")
    assert not missing, f"Missing docstrings: {missing}"


def test_native_docstrings(native_module):
    """All public functions in native.py have docstrings."""
    missing = _check_module_docstrings(native_module, "native")
    assert not missing, f"Missing docstrings: {missing}"


def test_util_docstrings(util_module):
    """All public functions in util.py have docstrings."""
    missing = _check_module_docstrings(util_module, "util")
    assert not missing, f"Missing docstrings: {missing}"


def test_photon_material_class_docstrings(photon_material_module):
    """PhotonMaterial class and all its public methods have docstrings."""
    from photon_transport_code.mcdc_set.photon_material import PhotonMaterial

    assert (
        PhotonMaterial.__doc__ and PhotonMaterial.__doc__.strip()
    ), "PhotonMaterial class missing docstring"

    missing_methods = []
    for name, method in inspect.getmembers(
        PhotonMaterial, predicate=inspect.isfunction
    ):
        # Only check public methods (no underscores); dunder methods are optional
        if name.startswith("_"):
            continue
        doc = getattr(method, "__doc__", None)
        if not doc or not doc.strip():
            missing_methods.append(f"PhotonMaterial.{name}")

    assert not missing_methods, f"Missing method docstrings: {missing_methods}"


def test_photon_material_functions_docstrings(photon_material_module):
    """photon_material() and add_photon_material_to_mcdc() have docstrings."""
    missing = _check_module_docstrings(
        photon_material_module, "mcdc_set.photon_material"
    )
    assert not missing, f"Missing docstrings: {missing}"


def test_photon_material_getter_docstrings(photon_material_get_module):
    """All getter functions in mcdc_get.photon_material have docstrings."""
    missing = _check_module_docstrings(
        photon_material_get_module, "mcdc_get.photon_material"
    )
    assert not missing, f"Missing docstrings: {missing}"


# =============================================================================
# Test: module-level docstrings
# =============================================================================


def test_module_docstrings_present(
    interface_module,
    cross_sections_module,
    distributions_module,
    native_module,
    util_module,
    photon_material_module,
):
    """Every photon physics module has a module-level docstring."""
    modules = [
        ("interface", interface_module),
        ("cross_sections", cross_sections_module),
        ("distributions", distributions_module),
        ("native", native_module),
        ("util", util_module),
        ("photon_material", photon_material_module),
    ]
    missing = [
        name for name, mod in modules if not mod.__doc__ or not mod.__doc__.strip()
    ]
    assert not missing, f"Modules missing module-level docstrings: {missing}"
