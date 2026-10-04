.. _api_photon_material:

API Reference — Photon Material
==================================

User-facing material definition API and getter functions for photon transport
materials.  Mirrors the pattern of ``mcdc/mcdc_set/material.py``.

.. contents::
   :local:
   :depth: 1

mcdc_set.photon_material — Material Definition
------------------------------------------------

Define photon materials by elemental composition and number densities.

.. autoclass:: photon_transport_code.mcdc_set.photon_material.PhotonMaterial
   :members:
   :special-members: __init__, __repr__, __eq__

.. autofunction:: photon_transport_code.mcdc_set.photon_material.photon_material

.. autofunction:: photon_transport_code.mcdc_set.photon_material.add_photon_material_to_mcdc

mcdc_get.photon_material — Getter Functions
---------------------------------------------

Accessor functions that work with both ``dict`` and ``PhotonMaterial`` objects.

.. autofunction:: photon_transport_code.mcdc_get.photon_material.get_element

.. autofunction:: photon_transport_code.mcdc_get.photon_material.get_density

.. autofunction:: photon_transport_code.mcdc_get.photon_material.get_n_elements

.. autofunction:: photon_transport_code.mcdc_get.photon_material.get_material_name

.. autofunction:: photon_transport_code.mcdc_get.photon_material.get_fissionable

.. autofunction:: photon_transport_code.mcdc_get.photon_material.get_elements

.. autofunction:: photon_transport_code.mcdc_get.photon_material.get_densities

Supported Elements
------------------

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 45

   * - Z
     - Element
     - Atomic mass (g/mol)
     - NIST XCOM data available
   * - 1
     - Hydrogen (H)
     - 1.008
     - Yes — 43 energy points, 1 keV – 100 MeV
   * - 8
     - Oxygen (O)
     - 15.999
     - Yes — 42 energy points, includes K-edge at 0.543 keV
   * - 13
     - Aluminum (Al)
     - 26.982
     - Yes — 45 energy points, includes K-edge at 1.56 keV
   * - 82
     - Lead (Pb)
     - 207.2
     - Yes — 45 energy points, includes K-edge at 88.0 keV

Number Density Conversion
--------------------------

Number density from mass density:

.. math::

    n_i = \frac{\rho \cdot w_i \cdot N_A}{A_i \times 10^{24}}
    \quad \left[\frac{\text{atoms}}{\text{b·cm}}\right]

where :math:`\rho` is mass density (g/cm\ :sup:`3`), :math:`w_i` is weight
fraction, :math:`N_A = 6.022 \times 10^{23}` mol\ :sup:`-1`, and :math:`A_i`
is atomic mass (g/mol).

Common material number densities:

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Material
     - Density (g/cm\ :sup:`3`)
     - Number densities (atoms/b·cm)
   * - Aluminum
     - 2.699
     - ``[13]: [6.026e-2]``
   * - Lead
     - 11.35
     - ``[82]: [3.299e-2]``
   * - Water (H2O)
     - 1.000
     - ``[1, 8]: [6.692e-2, 3.346e-2]``
