.. _photon_examples:

Photon Transport — Example Problems
=====================================

Three standalone example scripts demonstrate the photon transport module.
Each example targets one primary interaction type and runs without requiring
a full MCDC installation.

Running the Examples
--------------------

From the project root directory (``c:/Projects/MCDC/``)::

    python photon_transport_code/examples/photon_transport_compton/problem.py
    python photon_transport_code/examples/photon_transport_pair_production/problem.py
    python photon_transport_code/examples/photon_transport_photoelectric/problem.py

Each example writes an HDF5 output file (``output.h5``) in its directory.

.. contents::
   :local:
   :depth: 1

Example 1: Compton Scattering Spectrum
---------------------------------------

**File:** ``examples/photon_transport_compton/problem.py``

**Physics demonstrated:** Compton scattering (Klein-Nishina)

A monoenergetic 1 MeV photon beam undergoes Compton scattering in water.
The simulation samples :math:`10^5` independent scatters using the Kahn (1954)
composition-rejection method and records the energy spectrum of scattered
photons.

**Expected results:**

* Continuous spectrum from backscatter minimum (~0.20 MeV) to incident energy
* Energy conservation exact (floating-point) for every scatter event
* Mean scattered energy ~0.72 MeV for 1 MeV incident photons
* Angle distribution peaks near :math:`\theta = 0` (forward scattering)

**Output HDF5 structure:**

.. code-block:: text

    output.h5
    ├── energy_bins    (float64, shape N+1)   — energy bin edges (MeV)
    ├── spectrum       (float64, shape N)     — scattered photon count per bin
    ├── mean_energy    (float64, scalar)      — mean scattered energy (MeV)
    └── energy_conservation_max_error (float64) — max |E_out + E_e - E_in|

Example 2: Pair Production Threshold
--------------------------------------

**File:** ``examples/photon_transport_pair_production/problem.py``

**Physics demonstrated:** Pair production threshold at 1.022 MeV

The simulation tests pair production cross-sections across the threshold at
:math:`2 m_e c^2 = 1.02199790` MeV.  A lead (Pb) material is used because
pair production is strongly enhanced for high-Z elements.

**Expected results:**

* Zero pair production cross-section for all energies < 1.022 MeV
* Sharp threshold: non-zero cross-section immediately above 1.022 MeV
* Cross-section increases monotonically above threshold
* Energy sharing between electron and positron is uniform in
  :math:`[m_e,\, E_\gamma - m_e]`

**Output HDF5 structure:**

.. code-block:: text

    output.h5
    ├── energies_MeV     (float64, shape N)  — test energies
    ├── pair_xs          (float64, shape N)  — pair XS per atom (cm^2/atom)
    ├── threshold_MeV    (float64, scalar)   — observed threshold (MeV)
    └── kinematic_sample/ (group)
        ├── E_electron   (float64, shape M)  — sampled electron energies
        └── E_positron   (float64, shape M)  — sampled positron energies

Example 3: Photoelectric Absorption
--------------------------------------

**File:** ``examples/photon_transport_photoelectric/problem.py``

**Physics demonstrated:** Photoelectric absorption (Beer-Lambert law)

A 10 keV photon beam travels through an aluminum slab.  At 10 keV the
photoelectric effect dominates for aluminum (~73% of total), so attenuation
follows Beer-Lambert law :math:`I(x) = I_0 \exp(-\mu x)`.  The simulation
tracks :math:`10^5` histories and computes the transmitted fraction.

**Expected results:**

* Transmitted fraction follows :math:`\exp(-\mu_T x)` within 5%
* At 10 keV for Al: :math:`\Sigma_T \approx 1.85` cm\ :sup:`-1` (PE ~73%),
  giving ~16% transmission through a 1 cm slab
* Shell statistics: K-shell selected ~80% of the time above the K-edge
* No secondary particles in Phase 1 model (all energy deposited locally)

**Output HDF5 structure:**

.. code-block:: text

    output.h5
    ├── slab_thickness_cm   (float64, scalar) — slab thickness
    ├── transmitted         (int64, scalar)   — photons reaching far side
    ├── total_histories     (int64, scalar)   — total photons launched
    ├── transmission_ratio  (float64, scalar) — transmitted / total
    ├── beer_lambert_pred   (float64, scalar) — exp(-mu*x) prediction
    ├── shell_selections    (str array)       — 'K', 'L', or 'M' per event
    └── energy_deposited    (float64, array)  — deposited energies (MeV)
