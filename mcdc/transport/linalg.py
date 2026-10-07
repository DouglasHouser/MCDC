import math
from numba import njit


@njit
def cross(result, a, b):
    x = a[1] * b[2] - a[2] * b[1]
    y = a[2] * b[0] - a[0] * b[2]
    z = a[0] * b[1] - a[1] * b[0]
    result[0] = x
    result[1] = y
    result[2] = z


@njit
def normalize(a):
    magnitude = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    a[0] /= magnitude
    a[1] /= magnitude
    a[2] /= magnitude
