"""
HDF5 photon cross-section data loader.

Reads reformatted photon element data from ``data/mcdc/{element}.h5`` files
(structured by FORMAT_PHOTON_DATA_MCDC.md) and returns arrays in the same unit
conventions expected by the transport physics functions:

    energies       — MeV           (HDF5 stores eV; converted here)
    cross-sections — cm²/atom      (HDF5 stores barn; 1 barn = 1e-24 cm²)

All loaded data is cached in-module so each element is read from disk only
once per Python session.

Supported elements: Z = 1 (H) through Z = 92 (U).  A ``FileNotFoundError``
is raised for elements whose HDF5 file is absent from ``data/mcdc/``.
"""

import h5py
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Path to reformatted HDF5 data files
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "mcdc"

# ---------------------------------------------------------------------------
# Z → element symbol map (Z = 1 to 92)
# ---------------------------------------------------------------------------

ELEMENT_MAP = {
    1: "H",  2: "He", 3: "Li",  4: "Be",  5: "B",  6: "C",  7: "N",  8: "O",
    9: "F", 10: "Ne", 11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P", 16: "S",
    17: "Cl", 18: "Ar", 19: "K",  20: "Ca", 21: "Sc", 22: "Ti", 23: "V",  24: "Cr",
    25: "Mn", 26: "Fe", 27: "Co", 28: "Ni", 29: "Cu", 30: "Zn", 31: "Ga", 32: "Ge",
    33: "As", 34: "Se", 35: "Br", 36: "Kr", 37: "Rb", 38: "Sr", 39: "Y",  40: "Zr",
    41: "Nb", 42: "Mo", 43: "Tc", 44: "Ru", 45: "Rh", 46: "Pd", 47: "Ag", 48: "Cd",
    49: "In", 50: "Sn", 51: "Sb", 52: "Te", 53: "I",  54: "Xe", 55: "Cs", 56: "Ba",
    57: "La", 58: "Ce", 59: "Pr", 60: "Nd", 61: "Pm", 62: "Sm", 63: "Eu", 64: "Gd",
    65: "Tb", 66: "Dy", 67: "Ho", 68: "Er", 69: "Tm", 70: "Yb", 71: "Lu", 72: "Hf",
    73: "Ta", 74: "W",  75: "Re", 76: "Os", 77: "Ir", 78: "Pt", 79: "Au", 80: "Hg",
    81: "Tl", 82: "Pb", 83: "Bi", 84: "Po", 85: "At", 86: "Rn", 87: "Fr", 88: "Ra",
    89: "Ac", 90: "Th", 91: "Pa", 92: "U",
}

# ---------------------------------------------------------------------------
# Module-level cache: Z -> (energies_MeV, compton_cm2, pe_cm2, pair_cm2)
# ---------------------------------------------------------------------------

_ELEMENT_CACHE: dict = {}
_FORM_FACTOR_CACHE: dict = {}
_SHELL_PE_CACHE: dict = {}
_RELAXATION_CACHE: dict = {}
_WATER_CACHE = None

# Unit conversion factors
_EV_TO_MEV = 1.0e-6       # HDF5 energies are in eV; physics code uses MeV
_BARN_TO_CM2 = 1.0e-24    # HDF5 cross-sections are in barn; code expects cm^2/atom

# Shells modeled for photoelectric fluorescence, by ENDF subshell designator and
# HDF5 group name.  K + L only (see the fluorescence plan): K=1, L1=2, L2=3, L3=4.
MODELED_SHELLS = ((1, "K"), (2, "L1"), (3, "L2"), (4, "L3"))


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------


def load_photon_element(Z):
    """
    Load photon cross-section data for element Z from the reformatted HDF5 file.

    Parameters
    ----------
    Z : int
        Atomic number (1 to 92).

    Returns
    -------
    tuple of (energies, compton_xs, photoelectric_xs, pair_production_xs)
        ``energies``          — float64 array, energy grid in MeV
        ``compton_xs``        — float64 array, incoherent (Compton) cross-section
                                in cm²/atom
        ``photoelectric_xs``  — float64 array, total photoelectric cross-section
                                in cm²/atom
        ``pair_production_xs``— float64 array, total pair production cross-section
                                in cm²/atom

    Raises
    ------
    ValueError
        If Z is not in the supported range 1–92.
    FileNotFoundError
        If the HDF5 file for element Z does not exist in ``data/mcdc/``.
    """
    if Z in _ELEMENT_CACHE:
        return _ELEMENT_CACHE[Z]

    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1–92.")

    symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{symbol}.h5"

    if not hdf5_path.exists():
        raise FileNotFoundError(
            f"Photon data file not found: {hdf5_path}. "
            "Ensure FORMAT_PHOTON_DATA_MCDC.md has been run."
        )

    with h5py.File(hdf5_path, "r") as f:
        pr = f["photon_reactions"]

        # Shared energy grid (eV → MeV)
        energies = pr["xs_energy_grid"][()] * _EV_TO_MEV

        # Incoherent (Compton) scattering cross-section (barn → cm²/atom)
        compton = pr["incoherent_scattering/MT-504/xs"][()] * _BARN_TO_CM2

        # Total photoelectric absorption cross-section (barn → cm²/atom)
        photoelectric = pr["photoelectric_absorption/MT-501/xs"][()] * _BARN_TO_CM2

        # Total pair production cross-section (barn → cm²/atom)
        pair_production = pr["pair_production/MT-503/xs"][()] * _BARN_TO_CM2

    result = (
        np.ascontiguousarray(energies, dtype=np.float64),
        np.ascontiguousarray(compton, dtype=np.float64),
        np.ascontiguousarray(photoelectric, dtype=np.float64),
        np.ascontiguousarray(pair_production, dtype=np.float64),
    )
    _ELEMENT_CACHE[Z] = result
    return result


def load_photon_element_coherent(Z):
    """
    Load the coherent (Rayleigh) scattering cross-section for element Z.

    Parameters
    ----------
    Z : int
        Atomic number (1 to 92).

    Returns
    -------
    tuple of (energies, coherent_xs)
        ``energies``    — float64 array, energy grid in MeV
        ``coherent_xs`` — float64 array, coherent cross-section in cm²/atom
    """
    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1–92.")

    symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{symbol}.h5"

    if not hdf5_path.exists():
        raise FileNotFoundError(f"Photon data file not found: {hdf5_path}")

    with h5py.File(hdf5_path, "r") as f:
        pr = f["photon_reactions"]
        energies = pr["xs_energy_grid"][()] * _EV_TO_MEV
        coherent = pr["elastic/MT-502/xs"][()] * _BARN_TO_CM2

    return (
        np.ascontiguousarray(energies, dtype=np.float64),
        np.ascontiguousarray(coherent, dtype=np.float64),
    )


def load_photon_element_coherent_form_factor(Z):
    """
    Load the coherent (Rayleigh) atomic form factor F(q, Z) for element Z and
    precompute the cumulative F^2 table used by the inverse-CDF angular sampler.

    The HDF5 group ``elastic/MT-502/form_factor`` stores the EPDL momentum-transfer
    variable ``x = sin(theta/2)/lambda`` (in inverse angstrom, verbatim from EPDL)
    and the form factor ``F``.  The code's momentum transfer ``q`` (defined by
    ``q^2 = 2 k^2 (1 - mu)`` with ``k = E/(hc)``) relates to the EPDL variable by

        q = 2 x

    (derivation: ``q = 2 k sin(theta/2)`` while ``x = k sin(theta/2)``), so the
    conversion is applied here exactly once by scaling the grid by two.  ``F`` is
    unchanged by the change of the horizontal variable.

    The cumulative table is

        cumF2[i] = A(q_i^2) = integral_0^{q_i^2} F(q')^2 d(q'^2)

    (trapezoid rule on the ``q^2`` grid), which is monotone increasing and hence
    directly invertible at sampling time — no runtime integration.

    Parameters
    ----------
    Z : int
        Atomic number (1 to 92).

    Returns
    -------
    tuple of (q_grid, cumF2, F)
        ``q_grid`` — float64 array, momentum-transfer grid in inverse angstrom
                     (``= 2 * EPDL x``).
        ``cumF2``  — float64 array, cumulative ``A(q^2)`` on ``q_grid`` (same length).
        ``F``      — float64 array, raw atomic form factor (``F[0] == Z``); returned
                     for validation/tests.
    """
    if Z in _FORM_FACTOR_CACHE:
        return _FORM_FACTOR_CACHE[Z]

    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1–92.")

    symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{symbol}.h5"

    if not hdf5_path.exists():
        raise FileNotFoundError(f"Photon data file not found: {hdf5_path}")

    with h5py.File(hdf5_path, "r") as f:
        ff = f["photon_reactions/elastic/MT-502/form_factor"]
        x = ff["momentum_transfer"][()]
        F = ff["form_factor"][()]

    x = np.ascontiguousarray(x, dtype=np.float64)
    F = np.ascontiguousarray(F, dtype=np.float64)

    # EPDL x -> code q (q = 2 x).  Horizontal-axis change only; F is unchanged.
    q_grid = 2.0 * x

    # Cumulative A(q^2) = integral of F^2 over q^2, trapezoid rule, leading 0.
    q2 = q_grid * q_grid
    F2 = F * F
    cumF2 = np.zeros_like(F)
    cumF2[1:] = np.cumsum(0.5 * (F2[1:] + F2[:-1]) * (q2[1:] - q2[:-1]))

    result = (
        np.ascontiguousarray(q_grid, dtype=np.float64),
        np.ascontiguousarray(cumF2, dtype=np.float64),
        np.ascontiguousarray(F, dtype=np.float64),
    )
    _FORM_FACTOR_CACHE[Z] = result
    return result


def load_water_data():
    """
    Load composition-weighted cross-sections for water (H₂O).

    Combines hydrogen (Z=1) and oxygen (Z=8) data using mass fractions:

        f_H = 2/18 ≈ 0.111   (2 H atoms, A=1)
        f_O = 16/18 ≈ 0.889  (1 O atom, A=16)

    Returns
    -------
    tuple of (energies, compton_xs, photoelectric_xs, pair_production_xs)
        All arrays in the same units as ``load_photon_element`` (MeV, cm²/atom).

    Raises
    ------
    ValueError
        If the H and O energy grids do not match.
    """
    global _WATER_CACHE
    if _WATER_CACHE is not None:
        return _WATER_CACHE

    e_h, c_h, pe_h, pp_h = load_photon_element(Z=1)   # Hydrogen
    e_o, c_o, pe_o, pp_o = load_photon_element(Z=8)   # Oxygen

    if not np.allclose(e_h, e_o):
        raise ValueError("H and O energy grids differ; cannot form water composite.")

    # Mass fractions: H₂ has mass 2, O has mass 16 → total 18
    f_h = 2.0 / 18.0
    f_o = 16.0 / 18.0

    _WATER_CACHE = (
        e_h,
        f_h * c_h  + f_o * c_o,
        f_h * pe_h + f_o * pe_o,
        f_h * pp_h + f_o * pp_o,
    )
    return _WATER_CACHE


def load_photon_shell_resolved_pe(Z):
    """
    Load shell-resolved photoelectric cross-sections for element Z.

    Parameters
    ----------
    Z : int
        Atomic number (1 to 92).

    Returns
    -------
    dict
        ``"energy_grid"`` — float64 array, energy grid in MeV.
        Additional keys are shell names (``"K"``, ``"L1"``, etc.), each mapping
        to a sub-dict with ``"xs"`` (cm²/atom) and ``"binding_energy"`` (eV,
        as stored in the data file).
    """
    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1–92.")

    symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{symbol}.h5"

    if not hdf5_path.exists():
        raise FileNotFoundError(f"Photon data file not found: {hdf5_path}")

    result = {}
    with h5py.File(hdf5_path, "r") as f:
        pr = f["photon_reactions"]
        result["energy_grid"] = pr["xs_energy_grid"][()] * _EV_TO_MEV

        pe_group = pr["photoelectric_absorption"]
        if "shell_resolved" in pe_group:
            for shell_name, shell_data in pe_group["shell_resolved"].items():
                entry = {"xs": shell_data["xs"][()] * _BARN_TO_CM2}
                if "binding_energy" in shell_data:
                    entry["binding_energy"] = shell_data["binding_energy"][()]
                result[shell_name] = entry

    return result


def load_photon_shell_pe_xs(Z):
    """
    Load the photoelectric cross-sections for the modeled fluorescence shells
    (K, L1, L2, L3) of element Z, aligned to the main XS energy grid.

    Each shell's XS shares the ``xs_energy_grid`` (verified equal length), so the
    returned arrays can be interpolated with the same ``interpolate_xs`` used for
    the total cross-sections.  Shells absent from the file yield all-zero arrays.

    Parameters
    ----------
    Z : int
        Atomic number (1 to 92).

    Returns
    -------
    tuple of (energies, shell_xs)
        ``energies`` — float64 array, energy grid in MeV.
        ``shell_xs`` — tuple of float64 arrays (cm²/atom) in ``MODELED_SHELLS``
                       order (K, L1, L2, L3), each the same length as ``energies``.
    """
    if Z in _SHELL_PE_CACHE:
        return _SHELL_PE_CACHE[Z]

    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1–92.")

    symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{symbol}.h5"
    if not hdf5_path.exists():
        raise FileNotFoundError(f"Photon data file not found: {hdf5_path}")

    with h5py.File(hdf5_path, "r") as f:
        pr = f["photon_reactions"]
        energies = pr["xs_energy_grid"][()] * _EV_TO_MEV
        n = len(energies)
        sr = pr["photoelectric_absorption"].get("shell_resolved", None)
        shell_xs = []
        for _designator, name in MODELED_SHELLS:
            if sr is not None and name in sr and "xs" in sr[name]:
                shell_xs.append(sr[name]["xs"][()] * _BARN_TO_CM2)
            else:
                shell_xs.append(np.zeros(n, dtype=np.float64))

    result = (
        np.ascontiguousarray(energies, dtype=np.float64),
        tuple(np.ascontiguousarray(x, dtype=np.float64) for x in shell_xs),
    )
    _SHELL_PE_CACHE[Z] = result
    return result


def load_photon_relaxation(Z):
    """
    Load atomic relaxation (fluorescence) data for the modeled shells of element Z.

    Reads the ``atomic_relaxation`` group written by
    ``photon_transport_code/tools/add_atomic_relaxation.py``.  Energies are
    converted eV → MeV; per-line probabilities are returned as a normalized
    cumulative table (over the shell's radiative transitions) for inverse-CDF
    line sampling given that the vacancy decays radiatively.

    Parameters
    ----------
    Z : int
        Atomic number (1 to 92).

    Returns
    -------
    dict
        Maps ENDF subshell designator (int, one of ``MODELED_SHELLS``) -> dict:
        ``binding_energy``     — float, MeV.
        ``fluorescence_yield`` — float, omega (sum of radiative probabilities).
        ``line_energy``        — float64 array, MeV, one per radiative transition.
        ``line_cumprob``       — float64 array, normalized cumulative probability
                                 (monotone increasing, last entry == 1.0).
        ``line_final``         — int64 array, ENDF designator of the donor shell
                                 (the new vacancy after the transition).
        Only shells present in the file and in ``MODELED_SHELLS`` are included.
    """
    if Z in _RELAXATION_CACHE:
        return _RELAXATION_CACHE[Z]

    if Z not in ELEMENT_MAP:
        raise ValueError(f"Unsupported atomic number Z={Z}. Must be 1–92.")

    symbol = ELEMENT_MAP[Z]
    hdf5_path = DATA_DIR / f"{symbol}.h5"
    if not hdf5_path.exists():
        raise FileNotFoundError(f"Photon data file not found: {hdf5_path}")

    result = {}
    with h5py.File(hdf5_path, "r") as f:
        pr = f["photon_reactions"]
        if "atomic_relaxation" not in pr:
            _RELAXATION_CACHE[Z] = result
            return result
        subshells = pr["atomic_relaxation/subshells"]
        for designator, name in MODELED_SHELLS:
            if name not in subshells:
                continue
            sg = subshells[name]
            omega = float(sg["fluorescence_yield"][()])
            energy = sg["radiative/transition_energy"][()] * _EV_TO_MEV
            prob = sg["radiative/probability"][()].astype(np.float64)
            final = sg["radiative/final_subshell"][()].astype(np.int64)

            # Normalized cumulative probability over the radiative lines.
            total = prob.sum()
            if total > 0.0:
                cumprob = np.cumsum(prob) / total
                cumprob[-1] = 1.0
            else:
                cumprob = np.zeros(0, dtype=np.float64)
                energy = np.zeros(0, dtype=np.float64)
                final = np.zeros(0, dtype=np.int64)

            result[designator] = {
                "binding_energy": float(sg["binding_energy"][()]) * _EV_TO_MEV,
                "fluorescence_yield": omega,
                "line_energy": np.ascontiguousarray(energy, dtype=np.float64),
                "line_cumprob": np.ascontiguousarray(cumprob, dtype=np.float64),
                "line_final": np.ascontiguousarray(final, dtype=np.int64),
            }

    _RELAXATION_CACHE[Z] = result
    return result
