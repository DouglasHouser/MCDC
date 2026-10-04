.. _photon_physics:

Photon Transport — Physics Model
==================================

This page describes the physics models implemented in the photon transport
module: the Klein-Nishina Compton cross-section, photoelectric absorption using
NIST XCOM tabulated data, and pair production with a 1.022 MeV threshold.

.. contents::
   :local:
   :depth: 2

Interaction Overview
--------------------

At each collision point the transport engine samples an interaction type
proportional to the partial macroscopic cross-sections:

.. math::

    \Sigma_T = \Sigma_C + \Sigma_{PE} + \Sigma_{PP}

where :math:`\Sigma_C`, :math:`\Sigma_{PE}`, and :math:`\Sigma_{PP}` are the
macroscopic Compton, photoelectric, and pair production cross-sections
(cm\ :sup:`-1`).

Compton Scattering (Klein-Nishina)
-----------------------------------

**Cross-section formula**

The total Compton cross-section per electron uses the closed-form
Klein-Nishina (1929) formula (Evans 1955, p. 685):

.. math::

    \sigma_{KN} = 2\pi r_e^2 \left\{
      \frac{1+\alpha}{\alpha^3}
      \left[ \frac{2\alpha(1+\alpha)}{1+2\alpha} - \ln(1+2\alpha) \right]
      + \frac{\ln(1+2\alpha)}{2\alpha}
      - \frac{1+3\alpha}{(1+2\alpha)^2}
    \right\}

where :math:`\alpha = E / (m_e c^2)` and :math:`r_e = 2.818 \times 10^{-13}` cm.

At low energies (:math:`\alpha \to 0`) the formula reduces to the Thomson
cross-section :math:`\sigma_T = (8/3)\pi r_e^2 = 6.652 \times 10^{-25}` cm\ :sup:`2`.

**Macroscopic cross-section**

For a material with elements of atomic number :math:`Z_i` and number density
:math:`n_i`:

.. math::

    \Sigma_C = \sum_i n_i \cdot Z_i \cdot \sigma_{KN}(E)

**Scattering kinematics — Kahn (1954) method**

The scattered photon energy ratio :math:`\varepsilon = E'/E` is sampled using
the composition-rejection method of Kahn (1954) / Butcher-Messel (1960).
Let :math:`\tau = 1/(1+2\alpha)`.  Two envelope functions cover
:math:`[\tau, 1]`:

.. math::

    g_1(\varepsilon) \propto 1/\varepsilon, \quad a_1 = \ln(1/\tau)

    g_2(\varepsilon) \propto \varepsilon, \quad a_2 = (1-\tau^2)/2

The acceptance probability is :math:`P = 1 - \varepsilon \sin^2\theta / (1+\varepsilon^2) \geq 0.5`.

The scattering cosine follows from the Compton kinematic relation:

.. math::

    \mu = \cos\theta = 1 - \frac{1}{\alpha}\left(\frac{1}{\varepsilon} - 1\right)

**Energy conservation**

Energy is conserved exactly (to floating-point precision) by computing the
electron recoil energy as :math:`E_e = E - E'` rather than from a formula:

.. math::

    E_e + E' = E \quad (\text{error} < 10^{-15}\ \text{MeV})

Photoelectric Absorption
--------------------------

**Cross-section**

Photoelectric cross-sections are tabulated from NIST XCOM (Berger et al. 2010)
for Z = 1, 8, 13, 82.  Values include K-, L-, and M-shell contributions
with shell-edge discontinuities preserved (paired entries at each K-edge).

Lookup uses log-log interpolation between tabulated points:

.. math::

    \ln\sigma = \ln\sigma_0 + \frac{\ln(\sigma_1/\sigma_0)}{\ln(E_1/E_0)}
    \cdot \ln(E/E_0)

This power-law interpolation is appropriate because photon cross-sections
are smooth between shell edges and span many decades.

**Absorption model (Phase 1)**

In the Phase 1 model the photon is fully absorbed and all its energy is
deposited locally.  No fluorescence photons or Auger electrons are tracked::

    E_deposited = E_photon  (exact)

Shell selection (K/L/M) follows simplified partial-cross-section fractions
derived from NIST XCOM.  Above the K-edge: K-shell ≈ 80%, L ≈ 15%, M ≈ 5%.

Pair Production
---------------

**Threshold**

Pair production requires at least :math:`2 m_e c^2 = 1.02199790` MeV.
The cross-section is identically zero below this threshold.

**Cross-section**

Nuclear-field and electron-field (triplet) contributions are combined from
NIST XCOM tabulated data using the same log-log interpolation as photoelectric.

**Kinematics (Phase 1 simplified model)**

The available kinetic energy :math:`Q = E_\gamma - 2m_e` is shared uniformly
between the electron and positron:

.. math::

    E_e \sim \mathrm{Uniform}[m_e,\, E_\gamma - m_e]

    E_{e^+} = E_\gamma - E_e \quad (\text{exact conservation})

Emission angles follow an exponential distribution with characteristic angle
:math:`\theta_0 = m_e / E_\text{particle}`, producing strong forward peaking
at high energies.

Data Sources
------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Interaction
     - Data source
     - Reference
   * - Compton
     - Analytical (Klein-Nishina formula)
     - Klein & Nishina (1929); Evans (1955)
   * - Photoelectric
     - NIST XCOM tabulated (Z = 1, 8, 13, 82)
     - Berger et al. (2010); NIST SRD 8
   * - Pair production
     - NIST XCOM tabulated (Z = 1, 8, 13, 82)
     - Berger et al. (2010); Bethe & Heitler (1934)
   * - Kinematics
     - Kahn (1954) / Butcher-Messel (1960)
     - Salvat et al. (2011) PENELOPE

References
----------

* Klein, O. & Nishina, Y. (1929). Z. Phys. **52**, 853–868.
* Evans, R.D. (1955). *The Atomic Nucleus*. McGraw-Hill.
* Kahn, H. (1954). *Applications of Monte Carlo*. AECU-3259, Rand Corp.
* Butcher, J.C. & Messel, H. (1960). Nucl. Phys. **20**, 15.
* Bethe, H.A. & Heitler, W. (1934). Proc. R. Soc. London A **146**, 83.
* Berger, M.J. et al. (2010). XCOM: Photon Cross Sections Database. NIST SRD 8.
* Salvat, F. et al. (2011). PENELOPE-2011. OECD/NEA, Paris.
