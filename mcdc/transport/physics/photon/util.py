import math

from numba import njit

# ======================================================================================
# Physical constants (MeV, cm)
# ======================================================================================

ELECTRON_REST_MASS_ENERGY = 0.51099895
CLASSICAL_ELECTRON_RADIUS = 2.8179403e-13
THOMSON_CROSS_SECTION = (8.0 / 3.0) * math.pi * CLASSICAL_ELECTRON_RADIUS**2
PAIR_PRODUCTION_THRESHOLD = 2.0 * ELECTRON_REST_MASS_ENERGY
FINE_STRUCTURE_CONSTANT = 7.2973526e-3
AVOGADRO = 6.02214076e23
BARN_PER_CM2 = 1.0e24


# ======================================================================================
# Compton kinematics
# ======================================================================================


@njit
def compton_scattered_energy(E_in, mu):
    kappa = E_in / 0.51099895
    return E_in / (1.0 + kappa * (1.0 - mu))


@njit
def compton_scattering_cosine(E_in, E_out):
    kappa = E_in / 0.51099895
    return 1.0 - (1.0 / kappa) * (E_in / E_out - 1.0)


# ======================================================================================
# Threshold helpers
# ======================================================================================


@njit
def pair_production_threshold():
    return 2.0 * 0.51099895


@njit
def electron_rest_mass_energy():
    return 0.51099895


# ======================================================================================
# Numerical utilities
# ======================================================================================


@njit
def log_log_interpolation(x, x0, x1, y0, y1):
    if y0 <= 0.0 or y1 <= 0.0:
        t = (x - x0) / (x1 - x0)
        return y0 + t * (y1 - y0)
    log_x0 = math.log(x0)
    log_x1 = math.log(x1)
    log_y0 = math.log(y0)
    log_y1 = math.log(y1)
    alpha = (log_y1 - log_y0) / (log_x1 - log_x0)
    return math.exp(log_y0 + alpha * (math.log(x) - log_x0))


@njit
def scatter_direction(ux, uy, uz, mu, azi):
    sin_theta = math.sqrt(max(0.0, 1.0 - mu * mu))
    cos_azi = math.cos(azi)
    sin_azi = math.sin(azi)

    if abs(uz) < 1.0 - 1e-10:
        sin_polar = math.sqrt(max(0.0, 1.0 - uz * uz))
        ux_new = mu * ux + sin_theta * (ux * uz * cos_azi - uy * sin_azi) / sin_polar
        uy_new = mu * uy + sin_theta * (uy * uz * cos_azi + ux * sin_azi) / sin_polar
        uz_new = mu * uz - sin_theta * sin_polar * cos_azi
    else:
        ux_new = sin_theta * cos_azi
        uy_new = sin_theta * sin_azi
        uz_new = mu * (1.0 if uz > 0.0 else -1.0)

    return ux_new, uy_new, uz_new
