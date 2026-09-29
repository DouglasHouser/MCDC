import numpy as np
from numba import njit

####

import mcdc.mcdc_get as mcdc_get

from mcdc.constant import PROTON_CUTOFF_ENERGY, PROTON_MASS


@njit
def distance(particle_container, simulation, data):
    """Return the maximum proton condensed-history step length."""
    condensed_history = simulation["settings"]["condensed_history"]
    particle = particle_container[0]
    material = simulation["materials"][particle["material_ID"]]
    E = particle["E"]
    total_rho = 0.0
    total_dedx = 0.0

    for i in range(material["N_nuclide"]):
        nuclide_ID = int(mcdc_get.material.nuclide_IDs(i, material, data))
        nuclide = simulation["nuclides"][nuclide_ID]

        if not material["stopping_power_provided"]:
            dedx_values = mcdc_get.nuclide.stopping_power_all(nuclide, data)
            dedx_energies = mcdc_get.nuclide.stopping_power_energy_grid_all(
                nuclide, data
            )
            dedx = np.interp(E / 1e6, dedx_energies, dedx_values)
            total_dedx += dedx * 1e6

        atomic_mass = nuclide["atomic_weight_ratio"]
        nuclide_density = mcdc_get.material.nuclide_densities(i, material, data)
        density_gcm3 = nuclide_density * 1e24 * atomic_mass / (6.022e23)
        total_rho += density_gcm3

    if material["stopping_power_provided"]:
        dedx_values = mcdc_get.material.stopping_power_all(material, data)
        dedx_energies = mcdc_get.material.stopping_power_energy_grid_all(material, data)
        dedx = np.interp(E / 1e6, dedx_energies, dedx_values)
        total_dedx = dedx * 1e6

    max_fractional_energy_loss = condensed_history["max_fractional_energy_loss"]
    return max_fractional_energy_loss * E / total_dedx / total_rho


@njit
def apply(particle_container, collision_data_container, distance, simulation, data):
    """Apply proton condensed interactions over the traveled distance."""
    particle = particle_container[0]
    collision_data = collision_data_container[0]
    material = simulation["materials"][particle["material_ID"]]
    E = particle["E"]

    # Check for cutoff energy
    if E <= PROTON_CUTOFF_ENERGY:
        collision_data["energy_deposition"] += E * particle["w"]
        particle["alive"] = False
        particle["E"] = 0.0
        return

    average_A, average_Z, total_stopping_power, total_rho_gcm3 = (
        calculate_total_stopping_power(particle_container, simulation, data)
    )
    energy_loss = total_stopping_power * total_rho_gcm3 * distance

    # Range straggling - modify energy loss to have some slight variations
    # TODO: Insert different thickness regimes to sample from (e.g. Bohr, Landau, Vavilov)
    # TODO: Make this part use rng state instead of np.random.normal?
    energy_straggling_variance = (
        0.1569 * total_rho_gcm3 * average_Z / average_A * distance
    )
    energy_straggling_modifier = np.random.normal(
        loc=0.0, scale=np.sqrt(energy_straggling_variance)
    )
    energy_loss += energy_straggling_modifier
    particle["E"] -= energy_loss
    collision_data["energy_deposition"] += energy_loss * particle["w"]

    if energy_loss * particle["w"] <= 0.0:
        print(f"total density = {total_rho_gcm3}")
        print(f"stopping_power = {total_stopping_power}")
        print(f"distance = {distance}")
        print(f'energy_loss = {energy_loss * particle["w"]}')
        raise ValueError("negative energy loss")

    X0 = material["radiation_length"]

    # Angular scattering according to MCS theory
    phi, theta = sample_mcs_angle(particle["E"], distance, total_rho_gcm3, X0)

    rotate_direction(particle, phi, theta)

    return


@njit
def sample_mcs_angle(E, distance, density, X0):
    sigma = highland_lynch_dahl_sigma(E, distance, density, X0)

    if sigma < 0.0:
        raise ValueError(f"negative sigma = {sigma}")

    # Sample theta from the Highland distribution; phi uniformly from (0, 2pi)
    theta = np.abs(np.random.normal(0, sigma))
    phi = np.random.uniform(0, 2 * np.pi)

    return phi, theta


@njit
def highland_lynch_dahl_sigma(E, distance, density, X0):
    p = np.sqrt(E * (E + 2.0 * PROTON_MASS))
    beta = p / (E + PROTON_MASS)
    z = 1  # Incident particle is a proton, Z=1

    # X0 is measured in g/cm^2
    # Highland formula, modified by Lynch & Dahl
    radiation_distance_fraction = density * distance / X0
    sigma = (
        (13.6e6 / p * beta)
        * z
        * np.sqrt(radiation_distance_fraction)
        * (1 + 0.088 * np.log10(radiation_distance_fraction))
    )
    sigma = np.abs(sigma)

    if sigma < 0.0:
        print(f"radiation_distance_fraction = {radiation_distance_fraction}")
        print(f"p = {p}, beta = {beta}, z = {z}")
        print(f"density = {density}, distance = {distance}")
        raise ValueError(f"negative sigma = {sigma}")

    return sigma


@njit
def rotate_direction(particle, phi, theta):
    """
    Rotate direction vector (ux, uy, uz) by polar angle theta
    and azimuthal angle phi in the local frame.
    Returns new (ux, uy, uz).
    """

    ux = particle["ux"]
    uy = particle["uy"]
    uz = particle["uz"]

    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)

    # Build local perpendicular axes
    d = np.array([ux, uy, uz])
    perp = np.array([1.0, 0.0, 0.0]) if abs(ux) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(d, perp)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)

    d_new = cos_theta * d + sin_theta * cos_phi * u + sin_theta * sin_phi * v
    d_new /= np.linalg.norm(d_new)

    particle["ux"] = d_new[0]
    particle["uy"] = d_new[1]
    particle["uz"] = d_new[2]


@njit
def calculate_total_stopping_power(particle_container, simulation, data):
    particle = particle_container[0]
    material = simulation["materials"][particle["material_ID"]]
    E = particle["E"]

    total_stopping_power = 0.0
    total_rho_gcm3 = 0.0
    total_Z = 0.0
    total_A = 0.0
    # Find the total stopping power by summing over every nuclide in the material
    for i in range(material["N_nuclide"]):
        nuclide_ID = int(mcdc_get.material.nuclide_IDs(i, material, data))
        nuclide = simulation["nuclides"][nuclide_ID]

        # If no stopping power provided, we calculate it ourselves here
        if not material["stopping_power_provided"]:
            dedx_values = mcdc_get.nuclide.stopping_power_all(nuclide, data)
            dedx_energies = mcdc_get.nuclide.stopping_power_energy_grid_all(
                nuclide, data
            )

            # TODO: replace np.interp with a non-numpy function??
            dedx = np.interp(E / 1e6, dedx_energies, dedx_values)
            total_stopping_power += dedx * 1e6

        # Convert atoms/barn-cm to g/cm3:
        atomic_mass = nuclide["atomic_weight_ratio"]  # mass in amu
        nuclide_density = mcdc_get.material.nuclide_densities(i, material, data)
        density_gcm3 = nuclide_density * 1e24 * atomic_mass / (6.022e23)
        total_rho_gcm3 += density_gcm3

        total_Z += nuclide["atomic_number"]
        total_A += nuclide["mass_number"]

    average_Z = total_Z / material["N_nuclide"]
    average_A = total_A / material["N_nuclide"]

    if material["stopping_power_provided"]:
        dedx_values = mcdc_get.material.stopping_power_all(material, data)
        dedx_energies = mcdc_get.material.stopping_power_energy_grid_all(material, data)

        dedx = np.interp(E / 1e6, dedx_energies, dedx_values)
        total_stopping_power = dedx * 1e6

    return average_A, average_Z, total_stopping_power, total_rho_gcm3
