"""Double cone parallel to the z-axis.

The surface equation is

``f(x, y, z) = x**2 + y**2 + C*z**2 + G*x + H*y + I*z + J = 0``.
"""

import math

from numba import njit

from mcdc.constant import COINCIDENCE_TOLERANCE, INF


@njit
def evaluate(particle_container, surface):
    particle = particle_container[0]
    x = particle["x"]
    y = particle["y"]
    z = particle["z"]
    return (
        x * x
        + y * y
        + surface["C"] * z * z
        + surface["G"] * x
        + surface["H"] * y
        + surface["I"] * z
        + surface["J"]
    )


@njit
def reflect(particle_container, surface):
    particle = particle_container[0]
    gx, gy, gz = _get_gradient(particle, surface)
    norm = math.sqrt(gx * gx + gy * gy + gz * gz)
    if norm == 0.0:
        return

    nx = gx / norm
    ny = gy / norm
    nz = gz / norm
    projection = 2.0 * (nx * particle["ux"] + ny * particle["uy"] + nz * particle["uz"])
    particle["ux"] -= projection * nx
    particle["uy"] -= projection * ny
    particle["uz"] -= projection * nz


@njit
def get_normal_component(particle_container, surface):
    particle = particle_container[0]
    gx, gy, gz = _get_gradient(particle, surface)
    norm = math.sqrt(gx * gx + gy * gy + gz * gz)
    if norm == 0.0:
        return 0.0

    return (gx * particle["ux"] + gy * particle["uy"] + gz * particle["uz"]) / norm


@njit
def get_distance(particle_container, surface):
    particle = particle_container[0]
    x = particle["x"]
    y = particle["y"]
    z = particle["z"]
    ux = particle["ux"]
    uy = particle["uy"]
    uz = particle["uz"]
    C = surface["C"]

    a = ux * ux + uy * uy + C * uz * uz
    b = (
        2.0 * (x * ux + y * uy + C * z * uz)
        + surface["G"] * ux
        + surface["H"] * uy
        + surface["I"] * uz
    )
    c = evaluate(particle_container, surface)
    return _solve_distance(particle_container, surface, a, b, c)


@njit
def _get_gradient(particle, surface):
    return (
        2.0 * particle["x"] + surface["G"],
        2.0 * particle["y"] + surface["H"],
        2.0 * surface["C"] * particle["z"] + surface["I"],
    )


@njit
def _solve_distance(particle_container, surface, a, b, c):
    if abs(c) < COINCIDENCE_TOLERANCE:
        if get_normal_component(particle_container, surface) >= -COINCIDENCE_TOLERANCE:
            return INF

    if abs(a) <= COINCIDENCE_TOLERANCE:
        if abs(b) <= COINCIDENCE_TOLERANCE:
            return INF
        root = -c / b
        if root <= COINCIDENCE_TOLERANCE:
            return INF
        return root

    determinant = b * b - 4.0 * a * c
    if determinant <= 0.0:
        return INF

    sqrt_determinant = math.sqrt(determinant)
    denominator = 2.0 * a
    root_1 = (-b + sqrt_determinant) / denominator
    root_2 = (-b - sqrt_determinant) / denominator

    if root_1 <= COINCIDENCE_TOLERANCE:
        root_1 = INF
    if root_2 <= COINCIDENCE_TOLERANCE:
        root_2 = INF
    return min(root_1, root_2)
