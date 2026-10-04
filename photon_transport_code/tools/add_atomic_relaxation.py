"""
Import atomic relaxation data from EADL into ``data/mcdc/*.h5``.

Parses EADL section MF=28 / MT=533 (atomic relaxation data) for every element
file and writes the per-subshell binding energies, fluorescence yields, and
radiative transition lists into each element's HDF5 as a new group:

    photon_reactions/atomic_relaxation/
        subshells/<name>/              # e.g. K, L1, L2, L3, M1, ...
            designator                 # int64, ENDF subshell designator (1=K, ...)
            binding_energy             # float64 scalar, eV  (EADL EBI)
            fluorescence_yield         # float64 scalar, sum of radiative FTR (omega)
            radiative/
                final_subshell         # int64 array, ENDF designator of the donor shell (SUBJ)
                transition_energy      # float64 array, eV  (EADL ETR)
                probability            # float64 array, per-transition FTR

Energies are stored *verbatim* in eV (as in the EADL file); the eV -> MeV
conversion is done later in the loader, matching the form-factor convention.

Run from the repo root (conda env ``mcdc-env``)::

    python photon_transport_code/tools/add_atomic_relaxation.py
"""

import glob
import h5py
import numpy as np


# ENDF subshell designator -> shell name (matches the shell_resolved/* naming).
_SUBSHELL_NAME = {
    1: "K",
    2: "L1", 3: "L2", 4: "L3",
    5: "M1", 6: "M2", 7: "M3", 8: "M4", 9: "M5",
    10: "N1", 11: "N2", 12: "N3", 13: "N4", 14: "N5", 15: "N6", 16: "N7",
    17: "O1", 18: "O2", 19: "O3", 20: "O4", 21: "O5",
    22: "P1", 23: "P2", 24: "P3",
    25: "Q1", 26: "Q2", 27: "Q3",
}


def _endf_float(field):
    """Parse an 11-char ENDF float, tolerating Fortran '1.234-5' exponents."""
    s = field.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        mant = s[0]
        for prev, ch in zip(s, s[1:]):
            if ch in "+-" and prev not in "eE":
                mant += "e" + ch
            else:
                mant += ch
        return float(mant)


def _fields(line):
    """Return the six 11-char ENDF numeric fields of a data line."""
    return [_endf_float(line[i:i + 11]) for i in range(0, 66, 11)]


def read_relaxation(eadl_path):
    """
    Parse MF=28/MT=533 from an EADL file.

    Returns
    -------
    dict
        Maps ENDF subshell designator (int) -> dict with keys:
        ``binding_energy`` (eV), ``fluorescence_yield`` (sum radiative FTR),
        and ``radiative`` = list of (final_subshell, transition_energy_eV, FTR).
        Returns an empty dict if the file has no MF=28/MT=533 section.
    """
    with open(eadl_path) as f:
        block = [
            ln for ln in f
            if len(ln) >= 75 and ln[70:72].strip() == "28" and ln[72:75].strip() == "533"
        ]
    if not block:
        return {}

    # block[0] = HEAD: field5 (index 4) = NSS = number of subshells.
    NSS = int(_fields(block[0])[4])

    shells = {}
    p = 1
    for _ in range(NSS):
        # Subshell header: field1 = SUBI (designator), field6 = NTR (# transitions).
        hdr = _fields(block[p])
        SUBI = int(round(hdr[0]))
        NTR = int(round(hdr[5]))
        p += 1

        # First data row of the subshell: EBI (binding energy, eV), ELN.
        bind_row = _fields(block[p])
        EBI = bind_row[0]
        p += 1

        radiative = []
        omega = 0.0
        for _t in range(NTR):
            SUBJ, SUBK, ETR, FTR = _fields(block[p])[:4]
            p += 1
            if int(round(SUBK)) == 0:  # radiative transition
                radiative.append((int(round(SUBJ)), ETR, FTR))
                omega += FTR

        shells[SUBI] = {
            "binding_energy": EBI,
            "fluorescence_yield": omega,
            "radiative": radiative,
        }
    return shells


def add_relaxation(mcdc_path, eadl_dir="data/endf/eadl"):
    with h5py.File(mcdc_path, "r+") as h:
        Z = int(h["atomic_number"][()])
        shells = read_relaxation(f"{eadl_dir}/EADL.ZA{Z:03d}000.endf")

        # Idempotent: drop any prior extraction before rewriting.
        if "photon_reactions/atomic_relaxation" in h:
            del h["photon_reactions/atomic_relaxation"]
        if not shells:
            return 0

        ar = h.require_group("photon_reactions/atomic_relaxation/subshells")
        for designator, data in sorted(shells.items()):
            name = _SUBSHELL_NAME.get(designator, f"S{designator}")
            sg = ar.create_group(name)
            sg.create_dataset("designator", data=np.int64(designator))
            sg.create_dataset("binding_energy", data=np.float64(data["binding_energy"]))
            sg.create_dataset(
                "fluorescence_yield", data=np.float64(data["fluorescence_yield"])
            )
            rad = data["radiative"]
            rg = sg.create_group("radiative")
            final = np.array([r[0] for r in rad], dtype=np.int64)
            energy = np.array([r[1] for r in rad], dtype=np.float64)
            prob = np.array([r[2] for r in rad], dtype=np.float64)
            rg.create_dataset("final_subshell", data=final)
            rg.create_dataset("transition_energy", data=energy)
            rg.create_dataset("probability", data=prob)
        return len(shells)


if __name__ == "__main__":
    for path in sorted(glob.glob("data/mcdc/*.h5")):
        n = add_relaxation(path)
        print(f"atomic relaxation added ({n:2d} subshells): {path}")
