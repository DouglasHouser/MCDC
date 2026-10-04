"""
Phase 5 performance benchmark: verify photon physics routines complete within
acceptable time bounds.

Benchmarks cross-section lookups and scattering kernel sampling at a throughput
that is suitable for production Monte Carlo use.  This test ensures the module
does not regress in performance as code changes are made.

Run with::

    pytest test/regression/photon/test_performance_benchmark.py -v -s
"""

import time

import numpy as np
import pytest

from photon_transport_code.transport.physics.photon.cross_sections import (
    klein_nishina_total,
)
from photon_transport_code.transport.physics.photon.distributions import (
    sample_klein_nishina,
    sample_pair_production,
    photoelectric_absorption,
    photoelectric_select_shell,
)
from photon_transport_code.transport.physics.photon.native import (
    build_element_buffer,
    interpolate_xs,
)

# =============================================================================
# Benchmark parameters
# =============================================================================

# Number of iterations for timing benchmarks.
# Large enough for stable timing, small enough for fast CI.
_N_XS = 10_000
_N_SAMPLE = 10_000

# Maximum allowed time (seconds) per benchmark scenario.
# Conservative limits to avoid false CI failures on slow machines.
_MAX_SEC_XS = 5.0  # cross-section lookups
_MAX_SEC_SAMPLE = 10.0  # kernel sampling

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def al_buffer():
    """Pre-built element buffer for Al (Z=13)."""
    return build_element_buffer(Z=13)


@pytest.fixture(scope="module")
def pb_buffer():
    """Pre-built element buffer for Pb (Z=82)."""
    return build_element_buffer(Z=82)


@pytest.fixture(scope="module")
def energy_array():
    """Log-spaced energy array for parametric benchmarks."""
    np.random.seed(99)
    # Random energies in [0.01, 100] MeV to avoid branch-prediction bias
    return np.random.uniform(0.01, 100.0, _N_XS)


# =============================================================================
# Cross-section benchmarks
# =============================================================================


def test_klein_nishina_throughput(energy_array):
    """
    Klein-Nishina cross-section: must evaluate 10k energies in < 5 s.

    The analytical formula should be fast — dominated by math.log and
    floating-point arithmetic rather than memory access.
    """
    start = time.perf_counter()
    for E in energy_array:
        _ = klein_nishina_total(E)
    elapsed = time.perf_counter() - start

    rate = _N_XS / elapsed
    print(f"\n  KN throughput: {rate:,.0f} evals/s  ({elapsed:.3f} s for {_N_XS:,})")
    assert elapsed < _MAX_SEC_XS, (
        f"KN cross-section too slow: {elapsed:.2f} s for {_N_XS:,} evaluations "
        f"(limit {_MAX_SEC_XS} s)"
    )


def test_tabulated_pe_throughput(al_buffer, energy_array):
    """
    Tabulated photoelectric cross-section: 10k interpolations in < 5 s.

    Uses log-log binary search and interpolation on the NIST data buffer.
    """
    al_element, al_data = al_buffer
    N = int(al_element[0]["N_points"])
    eg_off = int(al_element[0]["energy_grid_offset"])
    pe_off = int(al_element[0]["pe_offset"])

    # Clamp energies to NIST table range
    E_min = float(al_data[eg_off])
    E_max = float(al_data[eg_off + N - 1])
    energies = np.clip(energy_array, E_min, E_max)

    start = time.perf_counter()
    for E in energies:
        _ = interpolate_xs(E, eg_off, pe_off, N, al_data)
    elapsed = time.perf_counter() - start

    rate = _N_XS / elapsed
    print(f"\n  PE (Al) throughput: {rate:,.0f} evals/s  ({elapsed:.3f} s)")
    assert elapsed < _MAX_SEC_XS, (
        f"PE interpolation too slow: {elapsed:.2f} s "
        f"for {_N_XS:,} evaluations (limit {_MAX_SEC_XS} s)"
    )


# =============================================================================
# Sampling kernel benchmarks
# =============================================================================


def test_compton_sampling_throughput():
    """
    Kahn (1954) Compton sampling: 10k samples in < 10 s.

    Acceptance rate >= 50 % at all energies, so average ~2 random draws per
    accepted sample.  Test at a representative 1 MeV incident energy.
    """
    np.random.seed(42)
    E_in = 1.0  # MeV

    start = time.perf_counter()
    for _ in range(_N_SAMPLE):
        _ = sample_klein_nishina(E_in)
    elapsed = time.perf_counter() - start

    rate = _N_SAMPLE / elapsed
    print(
        f"\n  Compton sampling: {rate:,.0f} samples/s  ({elapsed:.3f} s for {_N_SAMPLE:,})"
    )
    assert elapsed < _MAX_SEC_SAMPLE, (
        f"Compton sampling too slow: {elapsed:.2f} s for {_N_SAMPLE:,} samples "
        f"(limit {_MAX_SEC_SAMPLE} s)"
    )


def test_pair_production_sampling_throughput():
    """
    Pair production sampling: 10k samples in < 10 s.

    Uniform energy sharing and exponential angle sampling — very fast.
    """
    np.random.seed(42)
    E_gamma = 10.0  # MeV — well above threshold

    start = time.perf_counter()
    for _ in range(_N_SAMPLE):
        _ = sample_pair_production(E_gamma)
    elapsed = time.perf_counter() - start

    rate = _N_SAMPLE / elapsed
    print(
        f"\n  PP sampling: {rate:,.0f} samples/s  ({elapsed:.3f} s for {_N_SAMPLE:,})"
    )
    assert elapsed < _MAX_SEC_SAMPLE, (
        f"PP sampling too slow: {elapsed:.2f} s for {_N_SAMPLE:,} samples "
        f"(limit {_MAX_SEC_SAMPLE} s)"
    )


def test_photoelectric_sampling_throughput():
    """
    Photoelectric absorption + shell selection: 10k samples in < 10 s.

    Shell selection is a single random draw against probability thresholds.
    """
    np.random.seed(42)
    E_photon = 0.1  # MeV

    start = time.perf_counter()
    for _ in range(_N_SAMPLE):
        _ = photoelectric_absorption(E_photon)
        _ = photoelectric_select_shell(E_photon, Z=13)
    elapsed = time.perf_counter() - start

    rate = _N_SAMPLE / elapsed
    print(
        f"\n  PE sampling: {rate:,.0f} samples/s  ({elapsed:.3f} s for {_N_SAMPLE:,})"
    )
    assert elapsed < _MAX_SEC_SAMPLE, (
        f"PE sampling too slow: {elapsed:.2f} s for {_N_SAMPLE:,} samples "
        f"(limit {_MAX_SEC_SAMPLE} s)"
    )


# =============================================================================
# Relative performance: photon vs reference
# =============================================================================


def test_compton_vs_reference_speed():
    """
    Compton sampling throughput must exceed 1000 samples/s.

    This is a conservative lower bound; on modern hardware the module
    typically achieves > 100k samples/s.  The test catches severe
    performance regressions (e.g., accidental Python loop overhead).
    """
    np.random.seed(0)
    E_in = 0.5  # MeV

    start = time.perf_counter()
    for _ in range(1000):
        _ = sample_klein_nishina(E_in)
    elapsed = time.perf_counter() - start

    samples_per_sec = 1000 / elapsed
    print(f"\n  Reference: {samples_per_sec:,.0f} Compton samples/s")
    assert samples_per_sec > 1000, (
        f"Compton sampling below 1000 samples/s: {samples_per_sec:.0f} "
        "— check for accidental Python overhead"
    )
