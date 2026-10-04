"""
Import atomic form factors F(q, Z) from EPDL into ``data/mcdc/*.h5``.

Parses EPDL section MF=27 / MT=502 (coherent scattering atomic form factor) for
every element file and writes it into each element's HDF5 as a sibling of the
existing coherent cross section:

    photon_reactions/elastic/MT-502/
        xs                      (existing)
        form_factor/            (NEW)
            momentum_transfer   (EPDL x-grid, float64)
            form_factor         (F values, float64)

The EPDL x-grid and F values are stored *verbatim* (no unit conversion); the
EPDL-x -> code-q conversion is done later in the loader/sampler.

Run from the repo root (conda env ``mcdc-env``)::

    python photon_transport_code/tools/add_coherent_form_factors.py
"""

import glob
import h5py
import numpy as np


def _endf_float(field):
    """Parse an 11-char ENDF float, tolerating Fortran '1.234-5' exponents."""
    s = field.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        # Fortran style: insert 'e' before a sign that follows a digit/'.'
        mant = s[0]
        for prev, ch in zip(s, s[1:]):
            if ch in "+-" and prev not in "eE":
                mant += "e" + ch
            else:
                mant += ch
        return float(mant)


def read_formfactor(epdl_path):
    """Return (x, F) arrays from MF=27/MT=502 of an EPDL file."""
    with open(epdl_path) as f:
        block = [
            ln for ln in f
            if len(ln) >= 75 and ln[70:72].strip() == "27" and ln[72:75].strip() == "502"
        ]
    # line0 = HEAD, line1 = CONT (NP in cols 56-66), line2 = interp ranges
    NP = int(block[1][55:66])
    vals = []
    for ln in block[3:]:
        for i in range(0, 66, 11):
            v = _endf_float(ln[i:i + 11])
            if v is not None:
                vals.append(v)
    x = np.asarray(vals[0::2], dtype=np.float64)
    F = np.asarray(vals[1::2], dtype=np.float64)
    assert len(x) == len(F) == NP, (len(x), len(F), NP)
    return x, F


def add_form_factor(mcdc_path, epdl_dir="data/endf/epdl"):
    with h5py.File(mcdc_path, "r+") as h:
        Z = int(h["atomic_number"][()])
        x, F = read_formfactor(f"{epdl_dir}/EPDL.ZA{Z:03d}000.endf")
        # Sanity: F(0) == Z, monotone x, F non-increasing near origin
        assert abs(F[0] - Z) < 1e-6, (Z, F[0])
        assert np.all(np.diff(x) > 0.0)
        grp = h.require_group("photon_reactions/elastic/MT-502/form_factor")
        for name, arr in (("momentum_transfer", x), ("form_factor", F)):
            if name in grp:
                del grp[name]
            grp.create_dataset(name, data=arr)


if __name__ == "__main__":
    for path in sorted(glob.glob("data/mcdc/*.h5")):
        add_form_factor(path)
        print(f"form factor added: {path}")
