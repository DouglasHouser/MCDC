"""Infinite cylinder with an arbitrary axis.

For a point ``p``, an axis point ``c``, and a unit axis vector ``d``, define
``q = p - c`` and ``q_perp = q - dot(q, d) d``.  The surface equation is

``f(p) = dot(q_perp, q_perp) - radius**2 = 0``.
"""

import math

from numba import njit

from mcdc.constant import COINCIDENCE_TOLERANCE, INF


@njit
def evaluate(particle_container, surface):
    particle = particle_container[0]
    rx, ry, rz = _get_radial_vector(particle, surface)
    radius = surface["R"]
    return rx * rx + ry * ry + rz * rz - radius * radius


@njit
def reflect(particle_container, surface):
    particle = particle_container[0]
    rx, ry, rz = _get_radial_vector(particle, surface)
    norm = math.sqrt(rx * rx + ry * ry + rz * rz)
    if norm == 0.0:
        return

    nx = rx / norm
    ny = ry / norm
    nz = rz / norm
    projection = 2.0 * (nx * particle["ux"] + ny * particle["uy"] + nz * particle["uz"])
    particle["ux"] -= projection * nx
    particle["uy"] -= projection * ny
    particle["uz"] -= projection * nz


@njit
def get_normal_component(particle_container, surface):
    particle = particle_container[0]
    rx, ry, rz = _get_radial_vector(particle, surface)
    norm = math.sqrt(rx * rx + ry * ry + rz * rz)
    if norm == 0.0:
        return 0.0

    return (rx * particle["ux"] + ry * particle["uy"] + rz * particle["uz"]) / norm


@njit
def get_distance(particle_container, surface):
    particle = particle_container[0]
    rx, ry, rz = _get_radial_vector(particle, surface)

    dx = surface["nx"]
    dy = surface["ny"]
    dz = surface["nz"]
    ux = particle["ux"]
    uy = particle["uy"]
    uz = particle["uz"]

    u_dot_d = ux * dx + uy * dy + uz * dz
    vx = ux - u_dot_d * dx
    vy = uy - u_dot_d * dy
    vz = uz - u_dot_d * dz

    a = vx * vx + vy * vy + vz * vz
    if a <= COINCIDENCE_TOLERANCE:
        return INF

    b = 2.0 * (rx * vx + ry * vy + rz * vz)
    c = evaluate(particle_container, surface)

    if abs(c) < COINCIDENCE_TOLERANCE:
        if get_normal_component(particle_container, surface) >= (
            -COINCIDENCE_TOLERANCE
        ):
            return INF

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


@njit
def _get_radial_vector(particle, surface):
    x = particle["x"] - surface["A"]
    y = particle["y"] - surface["B"]
    z = particle["z"] - surface["C"]
    dx = surface["nx"]
    dy = surface["ny"]
    dz = surface["nz"]

    axial = x * dx + y * dy + z * dz
    return x - axial * dx, y - axial * dy, z - axial * dz
