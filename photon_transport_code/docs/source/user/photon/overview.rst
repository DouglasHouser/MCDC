.. _photon_overview:

Photon Transport — Overview
============================

The photon transport module implements continuous-energy photon physics for
Monte Carlo radiation transport, following the same structural conventions as
the MCDC neutron physics module.

.. contents::
   :local:
   :depth: 2

What This Module Does
---------------------

The module handles three photon interaction types across the energy range
1 keV – 100 MeV:

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Interaction
     - Energy Range
     - Outcome
   * - Compton scattering
     - All energies
     - Photon scattered with reduced energy; recoil electron produced
   * - Photoelectric absorption
     - Low energies (< 0.5 MeV typical)
     - Photon fully absorbed; bound electron ejected
   * - Pair production
     - E > 1.022 MeV
     - Photon converts to electron–positron pair

Supported elements: H (Z=1), O (Z=8), Al (Z=13), Pb (Z=82).

Module Structure
----------------

::

    photon_transport_code/
    ├── transport/physics/photon/
    │   ├── interface.py        # collision(), macro_xs(), particle_speed()
    │   ├── cross_sections.py   # klein_nishina_total(), photoelectric_xs(), …
    │   ├── distributions.py    # sample_klein_nishina(), sample_pair_production()
    │   ├── native.py           # NIST XCOM data tables and interpolation
    │   └── util.py             # Constants, log-log interpolation, helpers
    ├── mcdc_set/
    │   └── photon_material.py  # PhotonMaterial, photon_material()
    └── mcdc_get/
        └── photon_material.py  # Getter functions for material fields

Quickstart
----------

Define a photon material and look up cross-sections::

    from photon_transport_code.mcdc_set.photon_material import photon_material
    from photon_transport_code.transport.physics.photon.cross_sections import (
        klein_nishina_total,
    )
    from photon_transport_code.transport.physics.photon.native import (
        build_element_buffer,
        get_element_data,
    )

    # Define water at 1 g/cm^3 (H2O)
    water = photon_material(
        elements=[1, 8],
        densities=[6.692e-2, 3.346e-2],
        name="water",
    )

    # Compton cross-section per electron at 1 MeV
    sigma_kn = klein_nishina_total(1.0)
    print(f"Klein-Nishina at 1 MeV: {sigma_kn:.4e} cm^2/electron")

    # Tabulated NIST data for aluminum
    energies, compton, pe, pair = get_element_data(Z=13)

Sample Compton scattering kinematics::

    from photon_transport_code.transport.physics.photon.distributions import (
        sample_klein_nishina,
    )

    E_in = 1.0  # MeV — 1 MeV incident photon

    E_out, theta, E_electron = sample_klein_nishina(E_in)
    print(f"Scattered energy:  {E_out:.4f} MeV")
    print(f"Scattering angle:  {theta*180/3.14159:.2f} degrees")
    print(f"Electron energy:   {E_electron:.4f} MeV")
    print(f"Energy conserved:  {E_out + E_electron:.6f} MeV (= {E_in} MeV)")

Design Principles
-----------------

**Mirror neutron structure.**
  The module follows the same file layout, function signatures, and data-buffer
  conventions as ``mcdc/transport/physics/neutron/``, so integration into MCDC
  requires only copying files and wiring into the transport loop.

**NIST-validated cross-sections.**
  All tabulated cross-section data come directly from NIST XCOM (Berger et al.
  2010).  The Klein-Nishina formula is implemented analytically (Evans 1955).
  Validated within 2% at benchmark energies across the supported energy range.

**Numba JIT compatible.**
  All cross-section and collision functions are ``@njit`` decorated, matching
  MCDC's performance requirements.  Pure-Python helpers (data loading, material
  definition) run outside the JIT boundary.

**Standalone operation.**
  The module operates without a full MCDC installation.  Examples and tests run
  directly using the physics routines and the ``PhotonMaterial`` API.

Version and Status
------------------

:Module version: 1.0
:Physics scope: Compton, Photoelectric, Pair Production (Phase 1 model)
:Supported elements: H, O, Al, Pb (Z = 1, 8, 13, 82)
:Energy range: 1 keV – 100 MeV
:NIST validation: ±2% for Compton and pair production; ±1% for photoelectric
:MCDC integration: Ready — copy ``transport/physics/photon/`` into MCDC tree
