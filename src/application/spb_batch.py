"""Application workflows for the SPB row-wise batch table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from seebeck_prime.domain import spb as spb_domain


@dataclass(frozen=True)
class SPBBatchRowResult:
    """Calculated values associated with their original editable-table row."""

    row_index: int
    reduced_fermi_level: float
    effective_mass: float
    lorenz_display_value: float


def calculate_spb_batch_rows(
    temperatures_k: Sequence[float],
    seebecks_uv_k: Sequence[float],
    concentrations_cm3: Sequence[float],
    row_indices: Sequence[int],
    scattering_parameter: float,
) -> tuple[list[SPBBatchRowResult], float]:
    """Run the current SPB row calculations and return the legacy mean mass.

    Input screening/unit conversion stays at the dialog boundary. This use
    case preserves row order, Lorenz display scaling (1e8), and NaN exclusion
    for the existing arithmetic mean.
    """
    results = []
    masses = []
    for row, temperature, seebeck, concentration in zip(
        row_indices, temperatures_k, seebecks_uv_k, concentrations_cm3
    ):
        effective_mass, eta = spb_domain.calculate_effective_mass(
            seebeck,
            concentration,
            temperature,
            lambda_scat=scattering_parameter,
        )
        lorenz = spb_domain.rigorous_lorenz_number(
            eta, lambda_scat=scattering_parameter
        )
        results.append(
            SPBBatchRowResult(
                row_index=row,
                reduced_fermi_level=eta,
                effective_mass=effective_mass,
                lorenz_display_value=lorenz * 1e8,
            )
        )
        masses.append(effective_mass)

    valid_masses = [mass for mass in masses if not np.isnan(mass)]
    mean_mass = float(np.mean(valid_masses)) if valid_masses else float("nan")
    return results, mean_mass


def calculate_spb_batch_mean_parameters(
    temperatures_k: Sequence[float],
    seebecks_uv_k: Sequence[float],
    concentrations_cm3: Sequence[float],
    scattering_parameter: float,
) -> tuple[float, float] | None:
    """Return the established valid-mass mean and mean input temperature."""
    masses = [
        spb_domain.calculate_effective_mass(
            seebeck,
            concentration,
            temperature,
            lambda_scat=scattering_parameter,
        )[0]
        for temperature, seebeck, concentration in zip(
            temperatures_k, seebecks_uv_k, concentrations_cm3
        )
    ]
    valid_masses = [mass for mass in masses if not np.isnan(mass)]
    if not valid_masses:
        return None
    # Legacy rule (pinned by
    # tests/test_batch_workflows.py::test_spb_batch_application_mean_parameters_preserve_legacy_mean_rules):
    # the mean effective mass is taken over the valid rows while the mean
    # temperature is the mean of ALL submitted rows. The two numbers therefore
    # describe different populations - documented as audit issue SE-034
    # (MEDIUM, behaviour preserved deliberately).
    return float(np.mean(valid_masses)), float(np.mean(temperatures_k))
