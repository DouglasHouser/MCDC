"""
Getter functions for photon material objects.

Auto-generated getters that extract fields from a photon material, accepting
both the dict format returned by ``photon_material()`` and the class-based
``PhotonMaterial`` objects.  Mirrors the pattern of MCDC's auto-generated
nuclide/material getters in ``mcdc/mcdc_get/``.

Functions
---------
get_element(material, idx=0)
    Return the atomic number Z of element at position ``idx``.
get_density(material, idx=0)
    Return the number density for element at position ``idx``.
get_n_elements(material)
    Return the total number of distinct elements.
get_material_name(material)
    Return the material's human-readable name.
get_fissionable(material)
    Return whether the material is fissionable (always False for photons).
get_elements(material)
    Return the full list of atomic numbers.
get_densities(material)
    Return the full list of number densities.

Notes
-----
All getters accept either a dict (from ``photon_material()``) or a
``PhotonMaterial`` instance.  This allows the same getter interface to be
used during both setup (Python-level) and later MCDC-integrated transport.
"""


def get_element(material, idx=0):
    """
    Return the atomic number Z of the element at position ``idx``.

    Parameters
    ----------
    material : dict or PhotonMaterial
        Photon material specification.
    idx : int, optional
        Zero-based index into the element list.  Default: 0.

    Returns
    -------
    int
        Atomic number Z of the element at position ``idx``.

    Examples
    --------
    >>> water = photon_material([1, 8], [6.692e-2, 3.346e-2], name="water")
    >>> get_element(water, 0)
    1
    >>> get_element(water, 1)
    8
    """
    if isinstance(material, dict):
        return int(material["elements"][idx])
    return int(material.elements[idx])


def get_density(material, idx=0):
    """
    Return the number density for the element at position ``idx``.

    Parameters
    ----------
    material : dict or PhotonMaterial
        Photon material specification.
    idx : int, optional
        Zero-based index into the density list.  Default: 0.

    Returns
    -------
    float
        Number density in atoms/b-cm for the element at position ``idx``.
    """
    if isinstance(material, dict):
        return float(material["densities"][idx])
    return float(material.densities[idx])


def get_n_elements(material):
    """
    Return the total number of distinct elements in the material.

    Parameters
    ----------
    material : dict or PhotonMaterial
        Photon material specification.

    Returns
    -------
    int
        Number of elements.
    """
    if isinstance(material, dict):
        return int(material["N_element"])
    return int(material.N_element)


def get_material_name(material):
    """
    Return the material's human-readable name.

    Parameters
    ----------
    material : dict or PhotonMaterial
        Photon material specification.

    Returns
    -------
    str
        Material name.
    """
    if isinstance(material, dict):
        return str(material["name"])
    return str(material.name)


def get_fissionable(material):
    """
    Return whether the material is fissionable.

    For photon materials this is always ``False``.

    Parameters
    ----------
    material : dict or PhotonMaterial
        Photon material specification.

    Returns
    -------
    bool
        ``False`` for all photon materials.
    """
    if isinstance(material, dict):
        return bool(material.get("fissionable", False))
    return bool(material.fissionable)


def get_elements(material):
    """
    Return the full list of atomic numbers for all elements.

    Parameters
    ----------
    material : dict or PhotonMaterial
        Photon material specification.

    Returns
    -------
    list of int
        Atomic numbers [Z_1, Z_2, ...].
    """
    if isinstance(material, dict):
        return list(material["elements"])
    return list(material.elements)


def get_densities(material):
    """
    Return the full list of number densities for all elements.

    Parameters
    ----------
    material : dict or PhotonMaterial
        Photon material specification.

    Returns
    -------
    list of float
        Number densities [n_1, n_2, ...] in atoms/b-cm.
    """
    if isinstance(material, dict):
        return list(material["densities"])
    return list(material.densities)
