"""Add Compton profiles to photon libraries that already exist.

``generate.py`` writes each element file from scratch, which would discard any
data merged into it afterwards -- the regression library, for one, carries
electron data in some element files. This script appends only the
``compton_profile`` group, through the same writer ``generate.py`` uses, and
leaves every other dataset untouched.
"""

import argparse
import glob
import hashlib
import h5py
import os

####

import util
from util import print_error

parser = argparse.ArgumentParser(description="Add Compton profiles to photon data")
parser.add_argument("--rewrite", dest="rewrite", action="store_true", default=False)
args, unargs = parser.parse_known_args()

library_dir = os.getenv("MCDC_LIB_PHOTON")
profiles_path = os.getenv("MCDC_COMPTON_PROFILES")
if library_dir is None:
    print_error("Environment variable $MCDC_LIB_PHOTON is not set")
if profiles_path is None:
    print_error("Environment variable $MCDC_COMPTON_PROFILES is not set")

with open(profiles_path, "rb") as source:
    source_sha256 = hashlib.sha256(source.read()).hexdigest()

print(f"\nProfiles    : {profiles_path} (sha256 {source_sha256})")
print(f"Library dir : {library_dir}\n")

with h5py.File(profiles_path, "r") as profiles:
    for path in sorted(glob.glob(os.path.join(library_dir, "*.h5"))):
        with h5py.File(path, "a") as file:
            if "photon_reactions/incoherent_scattering/MT504" not in file:
                continue

            Z = int(file["atomic_number"][()])
            if f"{Z:03d}" not in profiles:
                print(f"  {os.path.basename(path)}: no profile for Z={Z}, skipped")
                continue

            group = file["photon_reactions/incoherent_scattering/MT504"]
            if "compton_profile" in group:
                if not args.rewrite:
                    print(f"  {os.path.basename(path)}: already present, skipped")
                    continue
                del group["compton_profile"]

            util.write_compton_profile(group, profiles, Z, source_sha256)
            print(f"  {os.path.basename(path)}: Z={Z}, written")

print("\nDone.\n")
