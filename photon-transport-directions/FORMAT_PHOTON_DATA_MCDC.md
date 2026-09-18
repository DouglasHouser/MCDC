# Reformat Photon HDF5 Data in data/mcdc to Match Neutron Structure

## Overview

This document outlines how to reformat the existing photon cross-section HDF5 files in `data/mcdc/` to match the hierarchical structure of the neutron library format (as exemplified by `B10-293.6K.h5`).

**Current photon data format:** Flat structure with mixed electron and photon reactions  
**Target photon data format:** Hierarchical with photon_reactions organized by interaction type  
**Rationale:** Consistency with neutron library allows unified data handling across particle types

## Current Photon Data Structure

The files in `data/mcdc/` (e.g., `H.h5`, `Al.h5`, `Pb.h5`) currently have:

```
{Element}.h5
├── atomic_number: int64
├── atomic_weight_ratio: float64
├── element_name: string
├── electron_reactions/ (not needed for photon transport)
│   ├── bremsstrahlung/
│   ├── elastic_scattering/
│   ├── excitation/
│   ├── ionization/
│   └── xs_energy_grid: float64[N]
├── photon_reactions/
│   ├── coherent_scattering/xs: float64[N]
│   ├── incoherent_scattering/xs: float64[N]
│   ├── pair_production/
│   │   ├── nuclear/xs: float64[N]
│   │   ├── electron/xs: float64[N]
│   │   └── xs: float64[N] (sum)
│   ├── photoelectric/
│   │   ├── subshells/
│   │   │   ├── K/xs: float64[N]
│   │   │   └── [L, M, N, ...]/xs: float64[N]
│   │   └── xs: float64[N] (total)
│   ├── total/xs: float64[N]
│   └── xs_energy_grid: float64[N] - SHARED energy grid
└── atomic_relaxation/ (optional, for detailed PE shell handling)
```

### Key Issues with Current Format

1. **No per-reaction energy grid** - All cross-sections share `xs_energy_grid`
2. **No Q-values** - Unlike neutron reactions, missing reaction energy (photon is absorbed/created)
3. **No reference frames** - Photons don't have COM/LAB distinction like neutrons
4. **Shell structure buried** - Photoelectric shell data is nested deeply
5. **Inconsistent with neutron format** - Different hierarchy and metadata

## Target Photon Data Structure

Restructure to match the neutron library format:

```
{Element}.h5
├── atomic_number: int64
├── atomic_weight_ratio: float64
├── element_name: string (optional, for clarity)
├── excitation_level: int64 (default: 0 for ground state)
├── fissionable: bool (default: False for photons)
├── photon_reactions/
│   ├── elastic/ (Coherent Scattering - Rayleigh)
│   │   └── MT-502/ (or use MT codes for photon reactions)
│   │       ├── Q-value: float64 (0.0 - elastic)
│   │       ├── reference_frame: string ("LAB")
│   │       └── xs: float64[N_points]
│   │
│   ├── incoherent_scattering/ (Compton)
│   │   └── MT-504/
│   │       ├── Q-value: float64 (0.0 - no energy change)
│   │       ├── reference_frame: string ("LAB")
│   │       ├── angular_distribution/ (optional)
│   │       │   ├── energy: float64[N_energies]
│   │       │   ├── offset: int64[N_energies]
│   │       │   ├── pdf: float64[N_total]
│   │       │   └── value: float64[N_total] (scattering cosine)
│   │       └── xs: float64[N_points]
│   │
│   ├── photoelectric_absorption/
│   │   ├── MT-501/ (total photoelectric)
│   │   │   ├── Q-value: float64 (0.0)
│   │   │   ├── reference_frame: string ("LAB")
│   │   │   └── xs: float64[N_points]
│   │   │
│   │   └── shell_resolved/ (K, L1, L2, L3, M1, ...)
│   │       ├── K/
│   │       │   ├── binding_energy: float64 (in keV)
│   │       │   ├── xs: float64[N_points]
│   │       │   └── angular_distribution/ (optional)
│   │       │       ├── energy: float64[N_energies]
│   │       │       ├── offset: int64[N_energies]
│   │       │       ├── pdf: float64[N_total]
│   │       │       └── value: float64[N_total] (scattering cosine)
│   │       ├── L1/
│   │       │   ├── binding_energy: float64
│   │       │   └── xs: float64[N_points]
│   │       └── [L2, L3, M1, ...]/
│   │
│   ├── pair_production/
│   │   └── MT-503/
│   │       ├── Q-value: float64 (0.0)
│   │       ├── reference_frame: string ("LAB")
│   │       ├── nuclear_field/
│   │       │   └── xs: float64[N_points]
│   │       ├── electron_field/
│   │       │   └── xs: float64[N_points]
│   │       └── xs: float64[N_points] (total)
│   │
│   ├── total/
│   │   └── MT-401/ (Total photon cross-section)
│   │       ├── Q-value: float64 (0.0)
│   │       ├── reference_frame: string ("LAB")
│   │       └── xs: float64[N_points]
│   │
│   ├── triplet_production/ (optional)
│   │   └── MT-515/
│   │       ├── Q-value: float64
│   │       ├── reference_frame: string ("LAB")
│   │       └── xs: float64[N_points]
│   │
│   └── xs_energy_grid: float64[N_points] - SHARED energy grid for all reactions
│
└── atomic_relaxation/ (moved to top level for clarity)
    ├── n_subshells: int64
    └── subshells/ (contains fluorescence yields, etc. if available)
```

## Photon Reaction MT Codes

Map photon interactions to standard MT codes:

| Reaction | MT Code | Description |
|----------|---------|-------------|
| Coherent Scattering (Rayleigh) | 502 | Elastic scattering from bound electrons |
| Incoherent Scattering (Compton) | 504 | Inelastic scattering |
| Photoelectric Absorption | 501 | Shell-resolved absorption |
| Pair Production (Total) | 503 | Electron-positron pair creation |
| Pair Production (Nuclear) | 521 | Pair production in nuclear field |
| Pair Production (Electron) | 522 | Triplet production in electron field |
| Triplet Production | 515 | Electron-electron pair creation |
| Total Photon | 401 | Sum of all reactions |

## Migration Strategy

### Phase 1: Create Reformatting Script

Create `photon_transport_code/tools/reformat_photon_data.py`:

```python
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
        # Extract metadata
        atomic_number = fin['atomic_number'][()]
        atomic_weight_ratio = fin['atomic_weight_ratio'][()]
        element_name = fin.get('element_name', b'').decode() if 'element_name' in fin else ''
        
        # Extract shared energy grid
        xs_energy_grid = fin['photon_reactions/xs_energy_grid'][()]
        
        # Extract reaction data
        photon_rxn = fin['photon_reactions']
    
    with h5py.File(output_file, 'w') as fout:
        # Write metadata
        fout.create_dataset('atomic_number', data=atomic_number)
        fout.create_dataset('atomic_weight_ratio', data=atomic_weight_ratio)
        fout.create_dataset('element_name', data=element_name.encode())
        fout.create_dataset('excitation_level', data=np.int64(0))
        fout.create_dataset('fissionable', data=np.bool_(False))
        
        # Create photon_reactions group
        pr = fout.create_group('photon_reactions')
        
        # Write shared energy grid
        pr.create_dataset('xs_energy_grid', data=xs_energy_grid)
        
        # Reformat each reaction type
        
        # 1. Coherent Scattering (Rayleigh)
        if 'coherent_scattering' in photon_rxn:
            coherent = pr.create_group('elastic')
            mt502 = coherent.create_group('MT-502')
            mt502.create_dataset('Q-value', data=np.float64(0.0))
            mt502.create_dataset('reference_frame', data=b'LAB')
            mt502.create_dataset('xs', 
                data=photon_rxn['coherent_scattering/xs'][()])
        
        # 2. Incoherent Scattering (Compton)
        if 'incoherent_scattering' in photon_rxn:
            incoherent = pr.create_group('incoherent_scattering')
            mt504 = incoherent.create_group('MT-504')
            mt504.create_dataset('Q-value', data=np.float64(0.0))
            mt504.create_dataset('reference_frame', data=b'LAB')
            mt504.create_dataset('xs', 
                data=photon_rxn['incoherent_scattering/xs'][()])
            
            # Optional: Add angular distribution if available
            # if 'angular_cosine_distribution' in photon_rxn['incoherent_scattering']:
            #     ... copy angular distribution data
        
        # 3. Photoelectric Absorption
        if 'photoelectric' in photon_rxn:
            pe = pr.create_group('photoelectric_absorption')
            
            # Total photoelectric
            mt501 = pe.create_group('MT-501')
            mt501.create_dataset('Q-value', data=np.float64(0.0))
            mt501.create_dataset('reference_frame', data=b'LAB')
            mt501.create_dataset('xs', 
                data=photon_rxn['photoelectric/xs'][()])
            
            # Shell-resolved photoelectric
            if 'subshells' in photon_rxn['photoelectric']:
                shell_res = pe.create_group('shell_resolved')
                for shell_name in photon_rxn['photoelectric/subshells'].keys():
                    shell_group = shell_res.create_group(shell_name)
                    shell_src = photon_rxn['photoelectric/subshells'][shell_name]
                    
                    if 'binding_energy' in shell_src:
                        shell_group.create_dataset('binding_energy',
                            data=shell_src['binding_energy'][()])
                    
                    if 'xs' in shell_src:
                        shell_group.create_dataset('xs',
                            data=shell_src['xs'][()])
        
        # 4. Pair Production
        if 'pair_production' in photon_rxn:
            pp = pr.create_group('pair_production')
            mt503 = pp.create_group('MT-503')
            mt503.create_dataset('Q-value', data=np.float64(0.0))
            mt503.create_dataset('reference_frame', data=b'LAB')
            
            if 'nuclear' in photon_rxn['pair_production']:
                nuc_group = mt503.create_group('nuclear_field')
                nuc_group.create_dataset('xs',
                    data=photon_rxn['pair_production/nuclear/xs'][()])
            
            if 'electron' in photon_rxn['pair_production']:
                elec_group = mt503.create_group('electron_field')
                elec_group.create_dataset('xs',
                    data=photon_rxn['pair_production/electron/xs'][()])
            
            mt503.create_dataset('xs', 
                data=photon_rxn['pair_production/xs'][()])
        
        # 5. Total Photon Cross-Section
        if 'total' in photon_rxn:
            total = pr.create_group('total')
            mt401 = total.create_group('MT-401')
            mt401.create_dataset('Q-value', data=np.float64(0.0))
            mt401.create_dataset('reference_frame', data=b'LAB')
            mt401.create_dataset('xs', 
                data=photon_rxn['total/xs'][()])

def reformat_all_photon_data(input_dir='data/mcdc', output_dir='data/mcdc_reformatted'):
    """
    Reformat all photon element files from input directory to output directory.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for h5_file in input_path.glob('*.h5'):
        output_file = output_path / h5_file.name
        print(f"Reformatting {h5_file.name}...")
        reformat_photon_element(str(h5_file), str(output_file))
        print(f"  → {output_file.name}")

if __name__ == '__main__':
    reformat_all_photon_data()
    print("\nReformatting complete! Review output files before replacing originals.")
```

### Phase 2: Validation and Testing

1. Compare original and reformatted files:
   - Verify all energy grids match
   - Verify all cross-section values are identical
   - Check metadata is preserved

2. Create validation script:

```python
def validate_reformatted_data(original, reformatted):
    """Verify that reformatting preserved all data correctly."""
    with h5py.File(original, 'r') as forg, h5py.File(reformatted, 'r') as fref:
        # Check metadata
        assert forg['atomic_number'][()] == fref['atomic_number'][()]
        assert forg['atomic_weight_ratio'][()] == fref['atomic_weight_ratio'][()]
        
        # Check energy grids
        org_grid = forg['photon_reactions/xs_energy_grid'][()]
        ref_grid = fref['photon_reactions/xs_energy_grid'][()]
        assert np.allclose(org_grid, ref_grid), "Energy grids don't match"
        
        # Check cross-sections
        for reaction in ['coherent_scattering', 'incoherent_scattering', 
                         'photoelectric', 'pair_production', 'total']:
            # Map old paths to new paths and compare
            # ... validation logic
```

### Phase 3: In-Place Replacement

1. Backup original `data/mcdc/` directory:
   ```bash
   cp -r data/mcdc data/mcdc.backup
   ```

2. Replace files:
   ```bash
   rm data/mcdc/*.h5
   cp data/mcdc_reformatted/*.h5 data/mcdc/
   ```

3. Verify MCDC still works with new format

### Phase 4: Update Documentation

- Update [MCDC_FILE_ARCHITECTURE.md](../photon-transport-docs/MCDC_FILE_ARCHITECTURE.md) with new format
- Update comments in data loading code
- Create example script showing how to use new format

## Key Changes for Data Consumers

After reformatting, code that reads photon cross-sections must adapt:

### Old Format (Native.py):
```python
energies, compton, pe, pair = native.get_element_data(Z)
```

### New Format (HDF5):
```python
import h5py

def load_photon_element(Z):
    """Load photon cross-sections from reformatted HDF5."""
    elem_map = {1: "H", 2: "He", ..., 92: "U"}
    
    with h5py.File(f"data/mcdc/{elem_map[Z]}.h5", 'r') as f:
        pr = f['photon_reactions']
        energies = pr['xs_energy_grid'][()]
        
        # Extract by reaction type as needed
        compton = pr['incoherent_scattering/MT-504/xs'][()]
        pe = pr['photoelectric_absorption/MT-501/xs'][()]
        pair = pr['pair_production/MT-503/xs'][()]
    
    return energies, compton, pe, pair
```

## Benefits of New Structure

1. ✅ **Unified Format** - Same structure for neutron and photon data
2. ✅ **Clear Semantics** - MT codes explicitly define reaction types
3. ✅ **Hierarchical** - Extensible for shell-resolved and angular distribution data
4. ✅ **Q-values & Reference Frames** - Complete reaction metadata
5. ✅ **Tool Compatibility** - Can use nuclear data tools developed for neutron libraries
6. ✅ **Better Documentation** - Each reaction clearly labeled with MT code
7. ✅ **Shell Information** - Photoelectric shell details preserved and accessible

## Timeline

- Phase 1 (Reformatting Script): 30 minutes
- Phase 2 (Validation): 30 minutes
- Phase 3 (Integration): 1-2 hours (includes updating all calling code)
- Phase 4 (Documentation): 30 minutes

**Total: ~3-4 hours**

## Rollback Strategy

- Backup original `data/mcdc/` before modification (Phase 3)
- All reformatting is reversible with inverse transformation
- Git history preserves original format if needed
