import h5py
import numpy as np
import pytest

from mcdc.constant import INTERPOLATION_LINEAR
from mcdc.object_.distribution import (
    DistributionEvaporation,
    DistributionMaxwellian,
)
from mcdc.object_.neutron_reaction import set_energy_distribution


@pytest.mark.parametrize(
    "spectrum_type, dataset_name, expected_type",
    [
        (
            "evaporation",
            "temperature_interpolations",
            DistributionEvaporation,
        ),
        (
            "maxwellian",
            "temperature_interpolation",
            DistributionMaxwellian,
        ),
    ],
)
def test_implicit_temperature_interpolation_defaults_to_linear(
    tmp_path, spectrum_type, dataset_name, expected_type
):
    path = tmp_path / "distribution.h5"
    with h5py.File(path, "w") as file:
        group = file.create_group("energy_spectrum")
        group.attrs["type"] = spectrum_type
        group.create_dataset("temperature_energy_grid", data=[1.0, 2.0])
        group.create_dataset("temperature", data=[0.5, 0.75])
        group.create_dataset("restriction_energy", data=0.0)
        group.create_dataset(dataset_name, data=np.zeros(0))
        group.create_dataset("interpolation_boundaries", data=np.zeros(0))

        result = set_energy_distribution(group)

    assert isinstance(result, expected_type)
    np.testing.assert_array_equal(
        result.nuclear_temperature.interpolations,
        [INTERPOLATION_LINEAR],
    )
    np.testing.assert_array_equal(
        result.nuclear_temperature.interpolation_boundaries,
        [2],
    )
