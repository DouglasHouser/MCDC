"""
User API for defining photon materials in MCDC.

Provides ``PhotonMaterial`` (class-based API) and ``photon_material()``
(function-based API) for defining photon transport materials.  Materials
are specified by their elemental composition (atomic numbers) and
corresponding number densities, matching the convention used throughout
MCDC for neutron materials.

Usage example::

    from photon_transport_code.mcdc_set.photon_material import PhotonMaterial

    water = PhotonMaterial(
        elements=[1, 8],
        densities=[6.692e-2, 3.346e-2],
        name="water",
    )
    mat_dict = water.to_dict()

    # Or with the function API:
    from photon_transport_code.mcdc_set.photon_material import photon_material

    water_dict = photon_material(
        elements=[1, 8],
        densities=[6.692e-2, 3.346e-2],
        name="water",
    )

Notes
-----
This module mirrors the pattern of mcdc/mcdc_set/material.py.  In the
standalone photon-transport-code environment the returned dict is consumed
by the transport engine directly.  After integration into MCDC it will be
processed by the same input-processing pipeline as neutron materials.

Number density units are atoms per barn-centimeter (atoms/b-cm), where
1 b-cm = 1e-24 cm^3.  To convert from mass density rho [g/cm^3]:

    n_i = rho * w_i * N_A / (A_i * 1e24)

where w_i is the weight fraction, N_A = 6.022e23 mol^-1, and A_i is the
atomic mass [g/mol].
"""

# ======================================================================================
# ConstantCrossSectionMaterial
# ======================================================================================


class ConstantCrossSectionMaterial:
    """
    Photon material with constant (energy-independent) cross sections.

    Used for analytical benchmark testing where scattering and absorption
    are independent of photon energy.

    Attributes
    ----------
    sigma_total : float
        Total cross section in cm^-1.
    sigma_scatter : float
        Scattering cross section in cm^-1.
    sigma_absorb : float
        Absorption cross section in cm^-1.
    name : str
        Material identifier.
    """

    def __init__(self, sigma_total, sigma_scatter, sigma_absorb, name=None):
        """
        Parameters
        ----------
        sigma_total : float
            Total macroscopic cross section in cm^-1.
        sigma_scatter : float
            Scattering cross section in cm^-1.
        sigma_absorb : float
            Absorption cross section in cm^-1.
        name : str, optional
            Optional material name for logging.
        """
        self.sigma_total = float(sigma_total)
        self.sigma_scatter = float(sigma_scatter)
        self.sigma_absorb = float(sigma_absorb)
        self.name = str(name) if name is not None else "constant_xs_material"
        self.fissionable = False
        self.validate()

    def validate(self):
        """
        Validate cross-section consistency.

        Returns
        -------
        bool
            True if sigma_scatter + sigma_absorb == sigma_total.

        Raises
        ------
        ValueError
            If inconsistent.
        """
        expected = self.sigma_scatter + self.sigma_absorb
        tol = 1e-10 * max(self.sigma_total, 1.0)
        if abs(expected - self.sigma_total) > tol:
            raise ValueError(
                f"ConstantCrossSectionMaterial '{self.name}': "
                f"sigma_scatter ({self.sigma_scatter}) + "
                f"sigma_absorb ({self.sigma_absorb}) = {expected} "
                f"!= sigma_total ({self.sigma_total})"
            )
        return True

    def __repr__(self):
        return (
            f"ConstantCrossSectionMaterial(name={self.name!r}, "
            f"sigma_total={self.sigma_total}, "
            f"sigma_scatter={self.sigma_scatter}, "
            f"sigma_absorb={self.sigma_absorb})"
        )

    def __eq__(self, other):
        if not isinstance(other, ConstantCrossSectionMaterial):
            return NotImplemented
        return (
            self.sigma_total == other.sigma_total
            and self.sigma_scatter == other.sigma_scatter
            and self.sigma_absorb == other.sigma_absorb
            and self.name == other.name
        )


class PhotonMaterial:
    """
    User-facing class for defining photon materials in MCDC.

    Wraps elemental composition and number densities with validation and
    helper methods.  Compatible with the ``photon_material()`` dict format
    and the getter functions in ``mcdc_get.photon_material``.

    Parameters
    ----------
    elements : list of int
        Atomic numbers Z of the constituent elements (e.g. [1, 8] for H2O).
        All values must satisfy 1 <= Z <= 92.  Tabulated cross-section data
        is available for every element in that range (data/mcdc/{symbol}.h5).
    densities : list of float
        Number densities [atoms/b-cm] for each element.  Must have the same
        length as ``elements``.  All values must be > 0.
    name : str, optional
        Human-readable label for this material.  Default: "photon_material".

    Raises
    ------
    ValueError
        If ``elements`` is empty, ``elements`` and ``densities`` have
        different lengths, any Z is outside [1, 92], or any density <= 0.

    Examples
    --------
    Pure aluminum::

        al = PhotonMaterial(elements=[13], densities=[6.026e-2], name="Al")

    Water at 1 g/cm^3::

        h2o = PhotonMaterial(
            elements=[1, 8],
            densities=[6.692e-2, 3.346e-2],
            name="water",
        )
    """

    def __init__(self, elements, densities, name="photon_material"):
        self.validate(elements, densities)
        self.name = str(name)
        self.elements = list(elements)
        self.densities = list(float(d) for d in densities)
        self.N_element = len(self.elements)
        self.fissionable = False

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate(elements, densities):
        """
        Validate element list and density list.

        Parameters
        ----------
        elements : list of int
            Atomic numbers.
        densities : list of float
            Number densities [atoms/b-cm].

        Raises
        ------
        ValueError
            On any constraint violation.
        """
        if len(elements) == 0:
            raise ValueError("elements list cannot be empty")
        if len(elements) != len(densities):
            raise ValueError(
                f"elements and densities must have the same length: "
                f"got {len(elements)} elements and {len(densities)} densities"
            )
        for Z in elements:
            if not (1 <= int(Z) <= 92):
                raise ValueError(
                    f"Atomic number Z={Z} is out of the physical range [1, 92]"
                )
        for n in densities:
            if float(n) <= 0.0:
                raise ValueError(
                    f"Number density {n} atoms/b-cm must be positive (> 0)"
                )

    # ------------------------------------------------------------------
    # Setters (fluent interface)
    # ------------------------------------------------------------------

    def set_name(self, name):
        """
        Set the material name.

        Parameters
        ----------
        name : str
            New material label.

        Returns
        -------
        PhotonMaterial
            Self, for method chaining.
        """
        self.name = str(name)
        return self

    def set_density(self, density, element_idx=None):
        """
        Set number density for one element or all elements.

        Parameters
        ----------
        density : float
            New number density in atoms/b-cm.  Must be > 0.
        element_idx : int or None, optional
            Index of the element to update.  If None (default), the same
            density is applied to all elements.

        Returns
        -------
        PhotonMaterial
            Self, for method chaining.

        Raises
        ------
        ValueError
            If density <= 0.
        IndexError
            If element_idx is out of range.
        """
        if float(density) <= 0.0:
            raise ValueError(f"density {density} must be positive")
        if element_idx is None:
            self.densities = [float(density)] * self.N_element
        else:
            self.densities[int(element_idx)] = float(density)
        return self

    def add_element(self, Z, density):
        """
        Append an element to the material composition.

        Parameters
        ----------
        Z : int
            Atomic number of the new element (1 <= Z <= 92).
        density : float
            Number density in atoms/b-cm.  Must be > 0.

        Returns
        -------
        PhotonMaterial
            Self, for method chaining.

        Raises
        ------
        ValueError
            If Z is out of range or density <= 0.
        """
        self.validate([Z], [density])
        self.elements.append(int(Z))
        self.densities.append(float(density))
        self.N_element += 1
        return self

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def to_dict(self):
        """
        Return a dict representation compatible with ``photon_material()``.

        Returns
        -------
        dict
            Keys: ``"name"``, ``"N_element"``, ``"elements"``,
            ``"densities"``, ``"fissionable"``.
        """
        return {
            "name": self.name,
            "N_element": self.N_element,
            "elements": list(self.elements),
            "densities": list(self.densities),
            "fissionable": self.fissionable,
        }

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"PhotonMaterial(name={self.name!r}, "
            f"elements={self.elements}, "
            f"densities={self.densities})"
        )

    def __eq__(self, other):
        if not isinstance(other, PhotonMaterial):
            return NotImplemented
        return (
            self.name == other.name
            and self.elements == other.elements
            and self.densities == other.densities
        )


# ======================================================================================
# Function-based API (retained for backward compatibility)
# ======================================================================================


def photon_material(elements, densities, name="photon_material"):
    """
    Define a photon material by its elemental composition.

    Convenience function that constructs a ``PhotonMaterial`` and returns
    its dict representation.

    Parameters
    ----------
    elements : list of int
        Atomic numbers Z of the constituent elements (e.g. [1, 8] for H2O).
        All values must satisfy 1 <= Z <= 92.
    densities : list of float
        Number densities [atoms/b-cm] for each element.  Must have the same
        length as ``elements``.  All values must be > 0.
    name : str, optional
        Human-readable label for this material, default "photon_material".

    Returns
    -------
    dict
        Material specification with keys:
            ``"name"``          : str   -- material label
            ``"N_element"``     : int   -- number of distinct elements
            ``"elements"``      : list  -- atomic numbers [Z_1, Z_2, ...]
            ``"densities"``     : list  -- number densities [n_1, n_2, ...]
            ``"fissionable"``   : bool  -- always False for photon materials

    Raises
    ------
    ValueError
        If any input constraint is violated (see ``PhotonMaterial.validate``).

    Notes
    -----
    Number density units: atoms per barn-centimeter (atoms/b-cm), where
    1 b-cm = 1e-24 cm^3.  To convert from mass density rho [g/cm^3]:

        n_i = rho * w_i * N_A / (A_i * 1e24)

    where w_i is the weight fraction, N_A = 6.022e23 mol^-1 is Avogadro's
    number, and A_i [g/mol] is the atomic mass of element i.
    """
    mat = PhotonMaterial(elements=elements, densities=densities, name=name)
    return mat.to_dict()


def add_photon_material_to_mcdc(material_dict, mcdc):
    """
    Register a photon material into the MCDC simulation state.

    Called internally by the MCDC input-processing pipeline after the user
    calls ``photon_material()`` and before the transport loop begins.

    Parameters
    ----------
    material_dict : dict
        Material specification as returned by ``photon_material()``.
    mcdc : numpy.ndarray, shape (1,)
        MCDC global state structured array; the new material entry is
        appended to the photon materials table.

    Returns
    -------
    int
        Material ID assigned to this material in the MCDC state.

    Notes
    -----
    This function is NOT @njit decorated because it runs during setup, not
    transport.  It mirrors the behavior of the neutron material registration
    functions in ``mcdc/input_.py``.

    Currently raises NotImplementedError in the standalone module; full
    MCDC integration is deferred to the transport-loop integration phase.
    """
    n_materials = int(mcdc[0]["N_material"])
    material_ID = n_materials

    mat = mcdc[0]["materials"][material_ID]
    mat[0]["N_nuclide"] = material_dict["N_element"]

    for i, (Z, n) in enumerate(
        zip(material_dict["elements"], material_dict["densities"])
    ):
        mat[0]["nuclides"][i]["Z"] = int(Z)
        mat[0]["nuclides"][i]["N"] = float(n)

    mcdc[0]["N_material"] += 1
    return material_ID
