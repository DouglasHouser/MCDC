"""Double cone with an arbitrary axis.

For a point ``p``, apex ``c``, unit axis vector ``d``, and
``t_sq = tan(theta)**2``, where ``theta`` is the half-angle between the axis
and the cone surface, define ``q = p - c``, ``q_axial = dot(q, d)``, and
``q_perp = q - q_axial d``. The surface equation is

``f(p) = dot(q_perp, q_perp) - t_sq*q_axial**2 = 0``.
"""

import math

from numba import njit

from mcdc.constant import COINCIDENCE_TOLERANCE, INF


@njit
def evaluate(particle_container, surface):
    particle = particle_container[0]
    axial, rx, ry, rz = _get_components(particle, surface)
    t_sq = surface["R"]
    return rx * rx + ry * ry + rz * rz - t_sq * axial * axial


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
    axial, rx, ry, rz = _get_components(particle, surface)

    dx = surface["nx"]
    dy = surface["ny"]
    dz = surface["nz"]
    ux = particle["ux"]
    uy = particle["uy"]
    uz = particle["uz"]
    t_sq = surface["R"]

    u_axial = ux * dx + uy * dy + uz * dz
    vx = ux - u_axial * dx
    vy = uy - u_axial * dy
    vz = uz - u_axial * dz

    a = vx * vx + vy * vy + vz * vz - t_sq * u_axial * u_axial
    b = 2.0 * (rx * vx + ry * vy + rz * vz - t_sq * axial * u_axial)
    c = evaluate(particle_container, surface)

    if abs(c) < COINCIDENCE_TOLERANCE:
        if get_normal_component(particle_container, surface) >= (
            -COINCIDENCE_TOLERANCE
        ):
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


@njit
def _get_components(particle, surface):
    x = particle["x"] - surface["A"]
    y = particle["y"] - surface["B"]
    z = particle["z"] - surface["C"]
    dx = surface["nx"]
    dy = surface["ny"]
    dz = surface["nz"]

    axial = x * dx + y * dy + z * dz
    return axial, x - axial * dx, y - axial * dy, z - axial * dz


@njit
def _get_gradient(particle, surface):
    axial, rx, ry, rz = _get_components(particle, surface)
    scale = surface["R"] * axial
    return (
        rx - scale * surface["nx"],
        ry - scale * surface["ny"],
        rz - scale * surface["nz"],
    )
