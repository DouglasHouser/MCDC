.. _api_photon_validation:

Validation Results & Test Coverage
=====================================

Summary of validation results for the photon transport module.  All physics
quantities are validated against NIST XCOM reference data and published
nuclear physics references.

.. contents::
   :local:
   :depth: 2

Running the Test Suite
----------------------

From the project root (``c:/Projects/MCDC/``)::

    pytest photon_transport_code/test/ -v

Run only unit tests::

    pytest photon_transport_code/test/unit/photon/ -v

Generate coverage report::

    pytest photon_transport_code/test/ \
        --cov=photon_transport_code.transport.physics.photon \
        --cov=photon_transport_code.mcdc_set.photon_material \
        --cov-report=term-missing

Phase 2: Cross-Section Validation
-----------------------------------

Klein-Nishina (Compton) cross-section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validated against Knoll (2010) free-electron Klein-Nishina reference values
and the Thomson limit.

.. list-table::
   :header-rows: 1
   :widths: 20 30 30 20

   * - Energy (MeV)
     - Reference (cm\ :sup:`2`/electron)
     - Computed (cm\ :sup:`2`/electron)
     - Error
   * - 0.001
     - :math:`6.652 \times 10^{-25}` (Thomson)
     - matches to < 0.5%
     - < 0.5%
   * - 0.1
     - :math:`4.93 \times 10^{-25}`
     - within 2%
     - < 2%
   * - 1.0
     - :math:`2.12 \times 10^{-25}`
     - within 2%
     - < 2%
   * - 5.0
     - :math:`8.3 \times 10^{-26}`
     - within 2%
     - < 2%
   * - 10.0
     - :math:`5.1 \times 10^{-26}`
     - within 2%
     - < 2%

Cross-section is monotonically decreasing across 0.01 – 100 MeV.

Photoelectric cross-section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validated against NIST XCOM tabulated data for Al and Pb.  K-edge
discontinuities are preserved in the interpolation.

* Error vs. NIST: < 1% for energies 1 keV – 100 MeV
* K-edge jumps preserved: paired energy entries at each shell edge
* Shell selection statistics: K-shell fraction > 70% above K-edge

Pair production cross-section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Threshold exact at :math:`2m_e c^2 = 1.02199790` MeV
* Zero below threshold (identically enforced)
* Error vs. NIST: < 2% above 1.1 MeV
* Cross-section monotonically increases above threshold

Phase 3: Interaction Physics Validation
-----------------------------------------

Compton kinematics
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Property
     - Result
   * - Energy conservation
     - :math:`|E_\text{out} + E_e - E_\text{in}| < 10^{-15}` MeV (exact)
   * - Scattering angle range
     - All samples in :math:`[0, \pi]`
   * - Forward scatters present
     - Yes (θ < 10° observed in 10k samples)
   * - Backscatters present
     - Yes (θ > 170° observed in 10k samples)
   * - Min energy at E=1 MeV
     - 0.204 MeV (backscatter: :math:`E/(1+2\alpha)`)

Pair production kinematics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Energy conservation: :math:`|E_{e^+} + E_{e^-} - E_\gamma| / E_\gamma < 10^{-14}`
* Below threshold returns ``None`` (correctly enforced)
* Forward peaking: > 80% of particles at θ < 90° for :math:`E_\gamma = 50` MeV
* Energy distribution: uniform spread confirmed by non-zero std deviation

Photoelectric kinematics
~~~~~~~~~~~~~~~~~~~~~~~~~~

* Energy deposited equals photon energy exactly (Phase 1 model)
* Shell selection: K-shell fraction > 70% above K-edge for all elements
* Emission direction: isotropic (Phase 1 model)

Phase 5: Code Quality
----------------------

Test coverage targets
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Module
     - Target coverage
     - How to verify
   * - ``transport.physics.photon.cross_sections``
     - ≥ 95%
     - ``pytest --cov=...cross_sections``
   * - ``transport.physics.photon.distributions``
     - ≥ 95%
     - ``pytest --cov=...distributions``
   * - ``transport.physics.photon.interface``
     - ≥ 95%
     - ``pytest --cov=...interface``
   * - ``transport.physics.photon.native``
     - ≥ 90%
     - ``pytest --cov=...native``
   * - ``mcdc_set.photon_material``
     - ≥ 95%
     - ``pytest --cov=...photon_material``

Code formatting
~~~~~~~~~~~~~~~~

All source files are Black-formatted (line length 88, Python 3.9 target)::

    black --check photon_transport_code/transport/ \
                  photon_transport_code/mcdc_set/ \
                  photon_transport_code/mcdc_get/ \
                  photon_transport_code/test/

Test count summary
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Test file
     - Tests
     - Validates
   * - ``test_klein_nishina.py``
     - 9
     - KN formula, Thomson limit, monotonicity
   * - ``test_photoelectric.py``
     - 7+
     - PE vs. NIST, shell statistics
   * - ``test_pair_production.py``
     - 6+
     - Threshold, NIST comparison, monotonicity
   * - ``test_total_xsec.py``
     - 5+
     - Total composition, dominance regions
   * - ``test_distributions.py``
     - 10+
     - Kernels, energy conservation, angles
   * - ``test_docstrings.py``
     - 4
     - All public functions documented
   * - Regression tests
     - 15+
     - Beer-Lambert, Compton spectrum, PP threshold

References
----------

* NIST XCOM: Berger, M.J. et al. (2010). XCOM: Photon Cross Sections Database,
  NIST Standard Reference Database 8 (XGAM). `<https://www.nist.gov/pml/xcom>`_
* Knoll, G.F. (2010). *Radiation Detection and Measurement*, 4th ed. Wiley.
* Evans, R.D. (1955). *The Atomic Nucleus*. McGraw-Hill.
