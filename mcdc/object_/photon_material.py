import math

import numpy as np

from numpy import float64
from numpy.typing import NDArray

####

from mcdc.constant import MATERIAL_PHOTON, MATERIAL_CONSTANT_XS
from mcdc.object_.material import MaterialBase
from mcdc.print_ import print_error

# Supported atomic numbers are those with tabulated photon cross-section data in
# data/mcdc/ (Z = 1–92).  Derived lazily from the data loader's element map so the
# set stays authoritative rather than a hand-maintained whitelist.
def _supported_z():
    from mcdc.transport.physics.photon.data_loader import ELEMENT_MAP

    return frozenset(ELEMENT_MAP)

# ======================================================================================
# PhotonMaterial
# ======================================================================================


class PhotonMaterial(MaterialBase):
    """
    Define a photon-transport material from elemental composition.

    Parameters
    ----------
    elements : list of int
        Atomic numbers Z of the constituent elements.  All Z must satisfy
        1 <= Z <= 92; tabulated cross-section data is available for every
        element in that range (data/mcdc/{symbol}.h5).
    densities : list of float
        Number densities in atoms/barn-cm for each element.  Must be positive.
    name : str, optional
        Human-readable label.

    Returns
    -------
    PhotonMaterial
        The material object.
    """

    # Annotations for Numba mode
    label: str = "photon_material"
    #
    N_element: int
    flat_data: NDArray[float64]

    def __init__(self, elements, densities, name=""):
        super().__init__(MATERIAL_PHOTON, name)

        # Validate
        _validate(elements, densities)

        self.N_element = len(elements)
        self.flat_data = _build_flat_data(
            [int(z) for z in elements], [float(d) for d in densities]
        )

    def __repr__(self):
        text = f"\nPhotonMaterial\n"
        text += f"  - ID: {self.ID}\n"
        text += f"  - N_element: {self.N_element}\n"
        return text


# ======================================================================================
# ConstantCrossSectionMaterial
# ======================================================================================


class ConstantCrossSectionMaterial(MaterialBase):
    """
    Photon material with constant (energy-independent) cross sections.

    Used for analytical benchmark testing where scattering and absorption
    are independent of photon energy.

    Parameters
    ----------
    sigma_total : float
        Total macroscopic cross section in cm^-1.
    sigma_scatter : float
        Scattering cross section in cm^-1.
    sigma_absorb : float
        Absorption cross section in cm^-1.
    name : str, optional
        Human-readable label.

    Raises
    ------
    ValueError
        If sigma_scatter + sigma_absorb != sigma_total (within floating-point
        tolerance of 1e-10).
    """

    label: str = "constant_xs_material"
    sigma_total: float
    sigma_scatter: float
    sigma_absorb: float

    def __init__(self, sigma_total, sigma_scatter, sigma_absorb, name=""):
        super().__init__(MATERIAL_CONSTANT_XS, name)
        self.sigma_total = float(sigma_total)
        self.sigma_scatter = float(sigma_scatter)
        self.sigma_absorb = float(sigma_absorb)
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
            If the cross sections are inconsistent.
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
        text = "\nConstantCrossSectionMaterial\n"
        text += f"  - ID: {self.ID}\n"
        text += f"  - Name: {self.name}\n"
        text += f"  - sigma_total: {self.sigma_total}\n"
        text += f"  - sigma_scatter: {self.sigma_scatter}\n"
        text += f"  - sigma_absorb: {self.sigma_absorb}\n"
        return text


# ======================================================================================
# Validation
# ======================================================================================


def _validate(elements, densities):
    if len(elements) == 0:
        print_error("PhotonMaterial: elements list cannot be empty")
    if len(elements) != len(densities):
        print_error(
            f"PhotonMaterial: elements and densities must have same length "
            f"({len(elements)} vs {len(densities)})"
        )
    supported = _supported_z()
    for Z in elements:
        if not (1 <= int(Z) <= 92):
            print_error(f"PhotonMaterial: atomic number Z={Z} out of range [1, 92]")
        elif int(Z) not in supported:
            print_error(
                f"PhotonMaterial: Z={Z} has no tabulated photon data "
                f"(supported: Z=1–92)"
            )
    for n in densities:
        if float(n) <= 0.0:
            print_error(f"PhotonMaterial: density {n} must be positive")


# ======================================================================================
# Flat-data buffer construction
# ======================================================================================
#
# Layout for N elements (31 header sections + per-element data):
#   [0 ..   N-1]  Z values (as float64)
#   [N ..  2N-1]  number densities
#   [2N..  3N-1]  N_points per element        (XS energy-grid length)
#   [3N..  4N-1]  energy_grid relative offsets (from start of flat_data array)
#   [4N..  5N-1]  compton_xs (incoherent) relative offsets
#   [5N..  6N-1]  pe_xs relative offsets       (total photoelectric)
#   [6N..  7N-1]  pair_xs relative offsets
#   [7N..  8N-1]  coherent_xs (Rayleigh) relative offsets
#   [8N..  9N-1]  N_ff points per element      (form-factor grid length)
#   [9N.. 10N-1]  q_grid (momentum-transfer) relative offsets
#   [10N..11N-1]  cumF2 (cumulative F^2 table) relative offsets
#   --- fluorescence sections (appended; K, L1, L2, L3 = MODELED_SHELLS order) ---
#   [11N..15N-1]  shell-resolved PE-XS relative offsets, one section per shell
#                   (11N=K, 12N=L1, 13N=L2, 14N=L3); each array has length N_points
#   [15N..19N-1]  shell binding energies (MeV), one section per shell (K..L3)
#   [19N..23N-1]  shell fluorescence yields omega, one section per shell (K..L3)
#   [23N..27N-1]  shell radiative-line counts n_lines, one section per shell (K..L3)
#   [27N..31N-1]  shell line-table relative offsets, one section per shell (K..L3)
#   [31N..     ]  per-element data:
#                   [E_grid | compton | pe | pair | coherent | q_grid | cumF2 |
#                    K_xs | L1_xs | L2_xs | L3_xs | line_triples]
#                 line_triples are, for each shell K,L1,L2,L3 in order, n_lines
#                 triples of (line_energy_MeV, cumulative_probability, final_shell_idx)
#                 where final_shell_idx maps the donor subshell to a MODELED_SHELLS
#                 index 0..3 (K..L3) for the K->L cascade, or -1 if unmodeled.
#
# Notes:
#  * All fluorescence sections (11..30) are appended after the original eleven so
#    the energy/compton/pe/pair/coherent/form-factor offsets used by
#    cross_sections.py are untouched.
#  * Shells absent from an element's data (e.g. low-Z) get zero XS arrays, zero
#    binding/omega, and n_lines=0, so they are never selected and never fluoresce.

# Header section count (see layout above).
_N_HEADER = 31
# Number of fluorescence shells modeled (K, L1, L2, L3).
_N_SHELL = 4


def _final_shell_index(designator):
    """Map an ENDF donor-subshell designator to a MODELED_SHELLS index (0..3), or -1."""
    # MODELED_SHELLS designators are 1=K, 2=L1, 3=L2, 4=L3.
    if 1 <= designator <= 4:
        return designator - 1
    return -1


def _build_flat_data(elements, densities):
    from mcdc.transport.physics.photon.data_loader import (
        load_photon_element,
        load_photon_element_coherent,
        load_photon_element_coherent_form_factor,
        load_photon_shell_pe_xs,
        load_photon_relaxation,
        MODELED_SHELLS,
    )

    N = len(elements)

    # Collect raw arrays for each element
    elem_arrays = []
    for Z in elements:
        energies, compton, pe, pair = load_photon_element(Z)
        e_coh, coherent = load_photon_element_coherent(Z)
        # Coherent data shares the same xs_energy_grid as the other channels.
        if len(coherent) != len(energies):
            print_error(
                f"PhotonMaterial: coherent XS grid for Z={Z} "
                f"({len(coherent)} pts) does not match main grid ({len(energies)} pts)"
            )
        # Coherent form factor F(q, Z): its own (energy-independent) grid — length
        # generally differs from the XS grid.
        q_grid, cumF2, _F = load_photon_element_coherent_form_factor(Z)
        # Shell-resolved PE cross sections (K, L1, L2, L3) on the main XS grid.
        _e_sh, shell_xs = load_photon_shell_pe_xs(Z)
        # Atomic relaxation (fluorescence) data, keyed by ENDF designator.
        relax = load_photon_relaxation(Z)
        elem_arrays.append(
            (energies, compton, pe, pair, coherent, q_grid, cumF2, shell_xs, relax)
        )

    # Per element: 9*N_points (5 XS + 4 shell XS) + 2*N_ff (q, cumF2) + 3*total_lines
    def _total_lines(relax):
        n = 0
        for designator, _name in MODELED_SHELLS:
            if designator in relax:
                n += len(relax[designator]["line_energy"])
        return n

    total_data_pts = sum(
        len(ea[0]) * 9 + len(ea[5]) * 2 + 3 * _total_lines(ea[8]) for ea in elem_arrays
    )

    total_len = _N_HEADER * N + total_data_pts

    buf = np.zeros(total_len, dtype=np.float64)

    # Fill header sections
    cursor = _N_HEADER * N
    for i, (Z, dens, ea) in enumerate(zip(elements, densities, elem_arrays)):
        energies, compton, pe, pair, coherent, q_grid, cumF2, shell_xs, relax = ea
        np_ = len(energies)
        nff = len(q_grid)
        buf[i] = float(Z)
        buf[N + i] = dens
        buf[2 * N + i] = float(np_)
        buf[3 * N + i] = float(cursor)  # energy_grid relative offset
        buf[4 * N + i] = float(cursor + np_)  # compton (incoherent) relative offset
        buf[5 * N + i] = float(cursor + 2 * np_)  # pe (total) relative offset
        buf[6 * N + i] = float(cursor + 3 * np_)  # pair relative offset
        buf[7 * N + i] = float(cursor + 4 * np_)  # coherent (Rayleigh) relative offset
        buf[8 * N + i] = float(nff)  # form-factor grid length
        buf[9 * N + i] = float(cursor + 5 * np_)  # q_grid relative offset
        buf[10 * N + i] = float(cursor + 5 * np_ + nff)  # cumF2 relative offset

        # Write core cross-section data
        buf[cursor : cursor + np_] = energies
        buf[cursor + np_ : cursor + 2 * np_] = compton
        buf[cursor + 2 * np_ : cursor + 3 * np_] = pe
        buf[cursor + 3 * np_ : cursor + 4 * np_] = pair
        buf[cursor + 4 * np_ : cursor + 5 * np_] = coherent
        # Write form-factor data (q-grid then cumulative F^2 table)
        buf[cursor + 5 * np_ : cursor + 5 * np_ + nff] = q_grid
        buf[cursor + 5 * np_ + nff : cursor + 5 * np_ + 2 * nff] = cumF2

        # Write the 4 shell-resolved PE-XS arrays (K, L1, L2, L3) after the ff data.
        sh_base = cursor + 5 * np_ + 2 * nff
        for s in range(_N_SHELL):
            off = sh_base + s * np_
            buf[off : off + np_] = shell_xs[s]
            buf[(11 + s) * N + i] = float(off)  # shell PE-XS relative offset

        # Write per-shell scalars and the radiative line tables.
        line_cursor = sh_base + _N_SHELL * np_
        for s, (designator, _name) in enumerate(MODELED_SHELLS):
            entry = relax.get(designator, None)
            if entry is None:
                binding = 0.0
                omega = 0.0
                n_lines = 0
            else:
                binding = entry["binding_energy"]
                omega = entry["fluorescence_yield"]
                n_lines = len(entry["line_energy"])
            buf[(15 + s) * N + i] = float(binding)
            buf[(19 + s) * N + i] = float(omega)
            buf[(23 + s) * N + i] = float(n_lines)
            buf[(27 + s) * N + i] = float(line_cursor)  # line-table relative offset
            if n_lines > 0:
                le = entry["line_energy"]
                cp = entry["line_cumprob"]
                ff = entry["line_final"]
                for j in range(n_lines):
                    buf[line_cursor + 3 * j] = le[j]
                    buf[line_cursor + 3 * j + 1] = cp[j]
                    buf[line_cursor + 3 * j + 2] = float(_final_shell_index(int(ff[j])))
                line_cursor += 3 * n_lines

        cursor = line_cursor

    return buf
