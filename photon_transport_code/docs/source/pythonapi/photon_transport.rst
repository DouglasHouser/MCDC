.. _api_photon_transport:

API Reference — transport.physics.photon
==========================================

Physics functions for photon transport.  All functions with ``@njit``
decoration are Numba JIT-compiled and suitable for use inside the MCDC
transport loop.

.. contents::
   :local:
   :depth: 1

interface — High-Level Entry Point
------------------------------------

Main entry point for photon collision physics.  These four functions mirror
the neutron interface (``mcdc/transport/physics/neutron/interface.py``).

.. autofunction:: photon_transport_code.transport.physics.photon.interface.particle_speed

.. autofunction:: photon_transport_code.transport.physics.photon.interface.macro_xs

.. autofunction:: photon_transport_code.transport.physics.photon.interface.photon_production_xs

.. autofunction:: photon_transport_code.transport.physics.photon.interface.collision

Reaction-type constants defined in ``interface.py``:

.. code-block:: python

    PHOTON_REACTION_COMPTON        = 0
    PHOTON_REACTION_PHOTOELECTRIC  = 1
    PHOTON_REACTION_PAIR_PRODUCTION = 2
    PHOTON_REACTION_TOTAL          = 3

cross_sections — Cross-Section Calculations
---------------------------------------------

All photon interaction cross-sections.  Compton uses the analytical
Klein-Nishina formula; photoelectric and pair production use tabulated
NIST XCOM data via log-log interpolation.

**Per-electron / per-atom functions:**

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.klein_nishina_total

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.klein_nishina_differential

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.photoelectric_xs

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.pair_production_xs

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.total_xs

**Macroscopic (material-level) functions:**

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.macro_compton_xs

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.macro_photoelectric_xs

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.macro_pair_production_xs

.. autofunction:: photon_transport_code.transport.physics.photon.cross_sections.macro_total_xs

distributions — Scattering Kernels
--------------------------------------

Sampling routines for interaction kinematics.

.. autofunction:: photon_transport_code.transport.physics.photon.distributions.sample_klein_nishina

.. autofunction:: photon_transport_code.transport.physics.photon.distributions.sample_pair_production

.. autofunction:: photon_transport_code.transport.physics.photon.distributions.sample_photoelectric_shell

.. autofunction:: photon_transport_code.transport.physics.photon.distributions.photoelectric_absorption

.. autofunction:: photon_transport_code.transport.physics.photon.distributions.photoelectric_select_shell

native — NIST Data Management
--------------------------------

Handles loading and interpolation of NIST XCOM tabulated data.

.. autofunction:: photon_transport_code.transport.physics.photon.native.get_element_data

.. autofunction:: photon_transport_code.transport.physics.photon.native.get_water_data

.. autofunction:: photon_transport_code.transport.physics.photon.native.build_element_buffer

.. autofunction:: photon_transport_code.transport.physics.photon.native.interpolate_xs

.. autofunction:: photon_transport_code.transport.physics.photon.native.find_energy_bin

.. autodata:: photon_transport_code.transport.physics.photon.native.PHOTON_ELEMENT_DTYPE

util — Constants and Helpers
-------------------------------

Physical constants and numerical utilities.

.. autodata:: photon_transport_code.transport.physics.photon.util.ELECTRON_REST_MASS_ENERGY

.. autodata:: photon_transport_code.transport.physics.photon.util.CLASSICAL_ELECTRON_RADIUS

.. autodata:: photon_transport_code.transport.physics.photon.util.THOMSON_CROSS_SECTION

.. autodata:: photon_transport_code.transport.physics.photon.util.PAIR_PRODUCTION_THRESHOLD

.. autofunction:: photon_transport_code.transport.physics.photon.util.compton_scattered_energy

.. autofunction:: photon_transport_code.transport.physics.photon.util.log_log_interpolation

.. autofunction:: photon_transport_code.transport.physics.photon.util.scatter_direction
