import h5py
import numpy as np
from pathlib import Path


def reformat_photon_element(input_file, output_file):
    """
    Reformat a single photon element HDF5 file from current format to target format.

    Parameters
    ----------
    input_file : str
        Path to existing photon data file (e.g., H.h5)
    output_file : str
        Path to write reformatted file
    """
    with h5py.File(input_file, 'r') as fin:
        atomic_number = fin['atomic_number'][()]
        atomic_weight_ratio = fin['atomic_weight_ratio'][()]
        element_name = fin['element_name'][()].decode() if 'element_name' in fin else ''

        xs_energy_grid = fin['photon_reactions/xs_energy_grid'][()]

        photon_rxn = fin['photon_reactions']

        # Read all data while file is open
        coherent_xs = photon_rxn['coherent_scattering/xs'][()] if 'coherent_scattering' in photon_rxn else None
        incoherent_xs = photon_rxn['incoherent_scattering/xs'][()] if 'incoherent_scattering' in photon_rxn else None

        pe_total_xs = None
        pe_shells = {}
        if 'photoelectric' in photon_rxn:
            pe_total_xs = photon_rxn['photoelectric/xs'][()]
            if 'subshells' in photon_rxn['photoelectric']:
                for shell_name in photon_rxn['photoelectric/subshells'].keys():
                    shell_src = photon_rxn['photoelectric/subshells'][shell_name]
                    pe_shells[shell_name] = {
                        'xs': shell_src['xs'][()] if 'xs' in shell_src else None,
                        'binding_energy': shell_src['binding_energy'][()] if 'binding_energy' in shell_src else None,
                    }

        pp_nuclear_xs = None
        pp_electron_xs = None
        pp_total_xs = None
        if 'pair_production' in photon_rxn:
            if 'nuclear' in photon_rxn['pair_production']:
                pp_nuclear_xs = photon_rxn['pair_production/nuclear/xs'][()]
            if 'electron' in photon_rxn['pair_production']:
                pp_electron_xs = photon_rxn['pair_production/electron/xs'][()]
            if 'xs' in photon_rxn['pair_production']:
                pp_total_xs = photon_rxn['pair_production/xs'][()]

        total_xs = photon_rxn['total/xs'][()] if 'total' in photon_rxn else None

    with h5py.File(output_file, 'w') as fout:
        fout.create_dataset('atomic_number', data=atomic_number)
        fout.create_dataset('atomic_weight_ratio', data=atomic_weight_ratio)
        fout.create_dataset('element_name', data=element_name.encode())
        fout.create_dataset('excitation_level', data=np.int64(0))
        fout.create_dataset('fissionable', data=np.bool_(False))

        pr = fout.create_group('photon_reactions')
        pr.create_dataset('xs_energy_grid', data=xs_energy_grid)

        # 1. Coherent Scattering (Rayleigh) -> elastic/MT-502
        if coherent_xs is not None:
            mt502 = pr.create_group('elastic/MT-502')
            mt502.create_dataset('Q-value', data=np.float64(0.0))
            mt502.create_dataset('reference_frame', data=b'LAB')
            mt502.create_dataset('xs', data=coherent_xs)

        # 2. Incoherent Scattering (Compton) -> incoherent_scattering/MT-504
        if incoherent_xs is not None:
            mt504 = pr.create_group('incoherent_scattering/MT-504')
            mt504.create_dataset('Q-value', data=np.float64(0.0))
            mt504.create_dataset('reference_frame', data=b'LAB')
            mt504.create_dataset('xs', data=incoherent_xs)

        # 3. Photoelectric Absorption -> photoelectric_absorption/MT-501 + shell_resolved
        if pe_total_xs is not None:
            pe = pr.create_group('photoelectric_absorption')
            mt501 = pe.create_group('MT-501')
            mt501.create_dataset('Q-value', data=np.float64(0.0))
            mt501.create_dataset('reference_frame', data=b'LAB')
            mt501.create_dataset('xs', data=pe_total_xs)

            if pe_shells:
                shell_res = pe.create_group('shell_resolved')
                for shell_name, shell_data in pe_shells.items():
                    sg = shell_res.create_group(shell_name)
                    if shell_data['binding_energy'] is not None:
                        sg.create_dataset('binding_energy', data=shell_data['binding_energy'])
                    if shell_data['xs'] is not None:
                        sg.create_dataset('xs', data=shell_data['xs'])

        # 4. Pair Production -> pair_production/MT-503
        if pp_total_xs is not None:
            mt503 = pr.create_group('pair_production/MT-503')
            mt503.create_dataset('Q-value', data=np.float64(0.0))
            mt503.create_dataset('reference_frame', data=b'LAB')
            if pp_nuclear_xs is not None:
                mt503.create_group('nuclear_field').create_dataset('xs', data=pp_nuclear_xs)
            if pp_electron_xs is not None:
                mt503.create_group('electron_field').create_dataset('xs', data=pp_electron_xs)
            mt503.create_dataset('xs', data=pp_total_xs)

        # 5. Total Photon Cross-Section -> total/MT-401
        if total_xs is not None:
            mt401 = pr.create_group('total/MT-401')
            mt401.create_dataset('Q-value', data=np.float64(0.0))
            mt401.create_dataset('reference_frame', data=b'LAB')
            mt401.create_dataset('xs', data=total_xs)


def validate_reformatted_data(original, reformatted):
    """Verify that reformatting preserved all data correctly."""
    with h5py.File(original, 'r') as forg, h5py.File(reformatted, 'r') as fref:
        assert forg['atomic_number'][()] == fref['atomic_number'][()], "atomic_number mismatch"
        assert np.isclose(forg['atomic_weight_ratio'][()], fref['atomic_weight_ratio'][()]), \
            "atomic_weight_ratio mismatch"

        org_grid = forg['photon_reactions/xs_energy_grid'][()]
        ref_grid = fref['photon_reactions/xs_energy_grid'][()]
        assert np.allclose(org_grid, ref_grid), "Energy grids don't match"

        reaction_map = [
            ('photon_reactions/coherent_scattering/xs',    'photon_reactions/elastic/MT-502/xs'),
            ('photon_reactions/incoherent_scattering/xs',  'photon_reactions/incoherent_scattering/MT-504/xs'),
            ('photon_reactions/photoelectric/xs',           'photon_reactions/photoelectric_absorption/MT-501/xs'),
            ('photon_reactions/pair_production/xs',         'photon_reactions/pair_production/MT-503/xs'),
            ('photon_reactions/total/xs',                   'photon_reactions/total/MT-401/xs'),
        ]
        for old_path, new_path in reaction_map:
            if old_path in forg and new_path in fref:
                assert np.allclose(forg[old_path][()], fref[new_path][()]), \
                    f"Cross-section mismatch: {old_path} vs {new_path}"

        # Validate pair production sub-fields
        if 'photon_reactions/pair_production/nuclear/xs' in forg:
            assert np.allclose(
                forg['photon_reactions/pair_production/nuclear/xs'][()],
                fref['photon_reactions/pair_production/MT-503/nuclear_field/xs'][()]
            ), "Pair production nuclear field mismatch"
        if 'photon_reactions/pair_production/electron/xs' in forg:
            assert np.allclose(
                forg['photon_reactions/pair_production/electron/xs'][()],
                fref['photon_reactions/pair_production/MT-503/electron_field/xs'][()]
            ), "Pair production electron field mismatch"


def reformat_all_photon_data(input_dir='data/mcdc', output_dir='data/mcdc_reformatted'):
    """
    Reformat all photon element files from input directory to output directory.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files = sorted(input_path.glob('*.h5'))
    for h5_file in files:
        output_file = output_path / h5_file.name
        print(f"Reformatting {h5_file.name}...", end=' ', flush=True)
        reformat_photon_element(str(h5_file), str(output_file))
        validate_reformatted_data(str(h5_file), str(output_file))
        print("OK")

    print(f"\nReformatted {len(files)} files to {output_path}")
    print("All validation checks passed.")
    print("Review output files before replacing originals.")


if __name__ == '__main__':
    reformat_all_photon_data()
