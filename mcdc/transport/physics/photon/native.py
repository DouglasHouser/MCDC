import math

from numba import njit

from mcdc.transport.physics.photon import util

# ======================================================================================
# @njit cross-section interpolation (operates on pre-extracted flat numpy arrays)
# ======================================================================================


@njit
def interpolate_xs(E, energy_grid_offset, xs_offset, N_points, data):
    idx = find_energy_bin(E, energy_grid_offset, N_points, data)
    x0 = data[energy_grid_offset + idx]
    x1 = data[energy_grid_offset + idx + 1]
    y0 = data[xs_offset + idx]
    y1 = data[xs_offset + idx + 1]
    return util.log_log_interpolation(E, x0, x1, y0, y1)


@njit
def find_energy_bin(E, energy_grid_offset, N_points, data):
    if E <= data[energy_grid_offset]:
        return 0
    if E >= data[energy_grid_offset + N_points - 1]:
        return N_points - 2

    lo = 0
    hi = N_points - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if data[energy_grid_offset + mid] <= E:
            lo = mid
        else:
            hi = mid
    return lo
