"""Generate the Stage 7 golden-output baseline (``tests/golden/baseline_outputs.json``).

Run from the repository root:

    python scripts/generate_golden_baseline.py

The baseline is a self-generated characterization snapshot of the current
Domain/Application scientific outputs. It is NOT scientific validation: the
expected values were produced by this very codebase on 2026-11-11 and are used
only to detect unintended changes in calculations during refactoring.

Determinism notes:
- All inputs are hard-coded literals or deterministic library behavior;
- No random data, no filesystem-dependent inputs, no GUI state;
- If the baseline must be regenerated deliberately (e.g. after an approved
  scientific change), re-run this script and review the diff in git.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (REPO_ROOT, REPO_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from seebeck_prime.domain.calculations import (  # noqa: E402
    calculate_dulong_petit_limit,
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_legacy_molecular_weight,
    calculate_molecular_weight,
    calculate_pf,
    calculate_zt,
    estimate_lorenz,
)
from seebeck_prime.domain.physical_constants import (  # noqa: E402
    ATOMIC_WEIGHTS,
    DEFAULT_LORENZ,
    LEGACY_DEFAULT_LORENZ,
)
from seebeck_prime.domain.uncertainty import (  # noqa: E402
    propagate_density_error,
    propagate_kappa_e_error,
    propagate_kappa_error,
    propagate_kappa_l_error,
    propagate_pf_error,
    propagate_relative_uncertainty,
    propagate_sigma_error,
    propagate_zt_error,
)
from seebeck_prime.domain.transport import (  # noqa: E402
    calculate_weighted_mobility,
    resistivity_to_mohm_cm,
)
from seebeck_prime.domain.spb import (  # noqa: E402
    calculate_effective_mass,
    calculate_carrier_concentration,
    rigorous_lorenz_number,
    seebeck_from_reduced_fermi_level,
)
from seebeck_prime.domain.hall import (  # noqa: E402
    calculate_hall_carrier_density,
    calculate_hall_coefficient_from_raw,
    calculate_hall_mobility,
    determine_carrier_type,
)
from seebeck_prime.domain.device_efficiency import (  # noqa: E402
    calculate_efficiencies,
)
from seebeck_prime.domain.phonon import (  # noqa: E402
    dulong_petit_specific,
    kappa_from_diffusivity,
)
from seebeck_prime.application.use_cases import (  # noqa: E402
    calculate_thermoelectric_properties,
    process_multi_sample_batch,
)


def to_jsonable(value):
    """Recursively convert NumPy/pandas results to JSON-serializable data."""
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, pd.DataFrame):
        return {str(col): to_jsonable(series) for col, series in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (pd.Series, np.ndarray)):
        return [to_jsonable(v) for v in np.asarray(value).ravel().tolist()]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)):
            return "NaN"
        return float(value)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise TypeError(f"Unsupported baseline type: {type(value)!r}")


def build_baseline() -> dict:
    # Representative measurement values used across the whole baseline.
    seebeck = 100e-6          # V/K
    conductivity = 1e5        # S/m
    temperature = 300.0       # K
    kappa_total = 2.0         # W/(m K)
    array = {
        "seebeck": np.array([100e-6, 50e-6]),
        "conductivity": np.array([1e5, 0.5e5]),
        "temperature": np.array([300.0, 400.0]),
        "kappa_total": np.array([2.0, 1.5]),
    }

    baseline: dict = {}

    baseline["constants"] = {
        "DEFAULT_LORENZ": float(DEFAULT_LORENZ),
        "LEGACY_DEFAULT_LORENZ": float(LEGACY_DEFAULT_LORENZ),
        "ATOMIC_WEIGHTS_sample": {
            key: float(ATOMIC_WEIGHTS[key]) for key in ("Bi", "Te", "Pb")
        },
    }

    baseline["core_properties"] = {
        "pf_scalar": to_jsonable(calculate_pf(seebeck, conductivity)),
        "pf_array": to_jsonable(calculate_pf(array["seebeck"], array["conductivity"])),
        "kappa_e_scalar": to_jsonable(calculate_kappa_e(conductivity, temperature)),
        "kappa_e_array": to_jsonable(
            calculate_kappa_e(array["conductivity"], array["temperature"])
        ),
        "kappa_l_scalar": to_jsonable(
            calculate_kappa_l(kappa_total, calculate_kappa_e(conductivity, temperature))
        ),
        "kappa_l_array": to_jsonable(
            calculate_kappa_l(
                array["kappa_total"],
                calculate_kappa_e(array["conductivity"], array["temperature"]),
            )
        ),
        "zt_scalar": to_jsonable(
            calculate_zt(
                calculate_pf(seebeck, conductivity), temperature, kappa_total
            )
        ),
        "zt_array": to_jsonable(
            calculate_zt(
                calculate_pf(array["seebeck"], array["conductivity"]),
                array["temperature"],
                array["kappa_total"],
            )
        ),
        "lorenz_estimate_100uVK": to_jsonable(estimate_lorenz(100.0)),
        "lorenz_estimate_250uVK": to_jsonable(estimate_lorenz(250.0)),
    }

    baseline["uncertainty"] = {
        "pf_error": to_jsonable(
            propagate_pf_error(seebeck, 5e-6, conductivity, 0.05e5)
        ),
        "kappa_e_error": to_jsonable(
            propagate_kappa_e_error(
                conductivity, 0.05e5, temperature, 5.0, DEFAULT_LORENZ, 0.0
            )
        ),
        "kappa_l_error": to_jsonable(
            propagate_kappa_l_error(0.02, 0.01)
        ),
        "zt_error": to_jsonable(
            propagate_zt_error(1e-3, 5e-5, temperature, 5.0, kappa_total, 0.02)
        ),
        "sigma_error": to_jsonable(propagate_sigma_error(1.0, 0.02, 1.0, 0.01, 0.1, 0.001)),
        "kappa_error": to_jsonable(
            propagate_kappa_error(2.0, 0.05, 0.25, 0.01, 7.0, 0.1)
        ),
        "density_error": to_jsonable(
            propagate_density_error(1.0, 0.01, 1.0, 0.02, 1.0, 0.01)
        ),
        "relative_combined": to_jsonable(
            propagate_relative_uncertainty(1e-3, 0.05, 0.02, 0.01)
        ),
    }

    baseline["materials"] = {
        "molecular_weight_Bi2Te3": to_jsonable(calculate_molecular_weight("Bi2Te3")),
        "legacy_molecular_weight_Bi2Te3": to_jsonable(
            calculate_legacy_molecular_weight("Bi2Te3")
        ),
        "dulong_petit_per_atom": to_jsonable(calculate_dulong_petit_limit(1, 1.0)),
        "dulong_petit_Bi2Te3_JgK": to_jsonable(calculate_dulong_petit_limit(3, 489.68)),
        "phonon_dulong_petit_specific_Bi2Te3": to_jsonable(
            dulong_petit_specific(3, 489.68)
        ),
        "phonon_kappa_from_diffusivity": to_jsonable(
            kappa_from_diffusivity(1.5, 0.20, 7.8)
        ),
    }

    baseline["transport_models"] = {
        "weighted_mobility_reference": to_jsonable(
            calculate_weighted_mobility(300.0, 10.0, 200.0)
        ),
        "resistivity_conversions": {
            str(unit): to_jsonable(resistivity_to_mohm_cm(1.0, unit))
            for unit in ("Ω·cm", "Ω·m", "S/cm", "S/m")
        },
        "spb_effective_mass_150uVK_1e19_300K": to_jsonable(
            calculate_effective_mass(150.0, 1e19, 300.0)
        ),
        "spb_seebeck_roundtrip": to_jsonable(
            seebeck_from_reduced_fermi_level(1.0, 0.5)
        ),
        "spb_rigorous_lorenz_eta1_l05": to_jsonable(rigorous_lorenz_number(1.0, 0.5)),
        "spb_carrier_concentration_150uVK": to_jsonable(
            calculate_carrier_concentration(150.0)
        ),
    }

    baseline["hall"] = {
        "hall_coefficient_from_raw": to_jsonable(
            calculate_hall_coefficient_from_raw(1e-3, 1e-3, 1e-2, 0.5)
        ),
        "hall_carrier_density": to_jsonable(
            calculate_hall_carrier_density(0.001, 1.0)
        ),
        "hall_mobility": to_jsonable(calculate_hall_mobility(0.001, 1e5)),
        "carrier_type_positive": to_jsonable(determine_carrier_type(1e-4)),
        "carrier_type_negative": to_jsonable(determine_carrier_type(-1e-4)),
    }

    baseline["device_efficiency"] = {
        "constant_properties_Tc300_Th500": to_jsonable(
            calculate_efficiencies(
                np.array([300.0, 400.0]),
                np.array([200e-6, 200e-6]),
                np.array([1e5, 1e5]),
                np.array([2.0, 2.0]),
                300.0,
                500.0,
            )
        ),
    }

    baseline["application"] = {
        "thermoelectric_properties_with_uncertainties": to_jsonable(
            calculate_thermoelectric_properties(
                array["temperature"],
                array["conductivity"],
                array["seebeck"],
                array["kappa_total"],
                u_sigma=np.array([1e3, 500.0]),
                u_S=np.array([2e-6, 1e-6]),
                u_kappa=np.array([0.02, 0.015]),
                u_T=np.array([0.5, 0.5]),
            )
        ),
        "multi_sample_batch": to_jsonable(
            process_multi_sample_batch(
                {
                    "SampleA": pd.DataFrame(
                        {
                            "Temperature": [300.0, 400.0],
                            "Seebeck": [100e-6, -200e-6],
                            "Sigma": [1e5, 8e4],
                            "Kappa_total": [2.0, 1.5],
                        }
                    )
                }
            )
        ),
    }

    return baseline


def main() -> None:
    baseline = build_baseline()
    target = REPO_ROOT / "tests" / "golden" / "baseline_outputs.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(baseline, indent=2, sort_keys=True, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
