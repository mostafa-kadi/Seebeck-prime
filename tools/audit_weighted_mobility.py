"""Reproduce the weighted-mobility parity check against Snyder et al. (2020).

Run with: python tools/audit_weighted_mobility.py
This is an equation-level numerical check, not experimental validation.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from seebeck_prime.domain.transport import calculate_weighted_mobility  # noqa: E402


def published_expression(temperature_k, resistivity_mohm_cm, seebeck_uv_k):
    """Independent transcription of Snyder et al., Adv. Mater. 32 (2020) 2001537."""
    k_b_over_e_uv_k = 1.380649e-23 / 1.602176634e-19 * 1e6
    s = abs(seebeck_uv_k) / k_b_over_e_uv_k
    first = np.exp(s - 2.0) / (1.0 + np.exp(-5.0 * (s - 1.0)))
    second = ((3.0 / np.pi**2) * s) / (1.0 + np.exp(5.0 * (s - 1.0)))
    return 331.0 / resistivity_mohm_cm * (temperature_k / 300.0) ** (-1.5) * (first + second)


def main():
    print("Snyder et al. (2020) weighted-mobility equation parity")
    print("DOI: 10.1002/adma.202001537")
    maximum_relative_error = 0.0
    for temperature in (300.0, 600.0, 900.0):
        for rho in (0.5, 1.0, 2.0):
            for seebeck in (50.0, 80.0, 100.0, 150.0, 200.0, 250.0):
                actual = float(calculate_weighted_mobility(temperature, rho, seebeck))
                expected = float(published_expression(temperature, rho, seebeck))
                relative_error = abs(actual - expected) / max(abs(expected), 1e-300)
                maximum_relative_error = max(maximum_relative_error, relative_error)
    print(f"Maximum relative error: {maximum_relative_error:.3e}")
    if maximum_relative_error > 2e-12:
        raise SystemExit("FAIL: implementation differs from published expression")
    zero_seebeck = float(calculate_weighted_mobility(300.0, 1.0, 0.0))
    print(f"Finite zero-Seebeck limit: {zero_seebeck:.9g} cm^2/(V s)")
    print("PASS: equation-level parity; experimental validation remains unavailable.")


if __name__ == "__main__":
    main()
