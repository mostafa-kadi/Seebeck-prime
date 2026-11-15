"""
Application use cases for Seebeck Prime.

Each use case represents one user/application workflow, coordinating
domain calculations and (optionally) infrastructure through the services layer.

Use cases must NOT depend on GUI or plot code.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from seebeck_prime.domain.calculations import (
    calculate_pf,
    calculate_kappa_e,
    calculate_kappa_l,
    calculate_zt,
    estimate_lorenz,
)
from seebeck_prime.domain.uncertainty import (
    propagate_pf_error,
    propagate_kappa_e_error,
    propagate_kappa_l_error,
    propagate_zt_error,
    propagate_kappa_error,
    propagate_relative_uncertainty as _propagate_relative_uncertainty,
)
from seebeck_prime.domain.physical_constants import (
    DEFAULT_LORENZ,
    LEGACY_DEFAULT_LORENZ,
)
from seebeck_prime.domain.calculations import (
    calculate_legacy_molecular_weight as _calculate_legacy_molecular_weight,
    calculate_dulong_petit_limit as _calculate_dulong_petit_limit,
)
from seebeck_prime.domain.validation import validate_dataset
from seebeck_prime.domain.transport import calculate_weighted_mobility as _calculate_weighted_mobility
from seebeck_prime.domain.transport import resistivity_to_mohm_cm as _resistivity_to_mohm_cm
from seebeck_prime.domain.device_efficiency import calculate_efficiencies as _calculate_efficiencies
from seebeck_prime.domain.phonon import kappa_from_diffusivity_si as _kappa_from_diffusivity_si


def validate_multi_sample_properties(processed_samples: dict) -> list[dict]:
    """Validate every processed multi-sample frame and return plain notices.

    The multi-sample workflow computes a lattice thermal conductivity per
    sample, so it needs the same scientific validation as the main table
    (audit finding D-01). The sample name is prefixed to each message so the
    user can tell which specimen a notice refers to.

    Args:
        processed_samples: Mapping of sample name to processed DataFrame, as
            returned by :func:`process_multi_sample_batch`.

    Returns:
        List of ``{"severity", "field", "message"}`` records.
    """
    notices: list[dict] = []
    for name, frame in (processed_samples or {}).items():
        if frame is None or len(frame) == 0:
            continue
        try:
            sample_notices = validate_calculated_properties(
                frame["Temperature"].to_numpy(),
                frame["Sigma"].to_numpy(),
                frame["Seebeck"].to_numpy(),
                frame["Kappa_total"].to_numpy(),
                frame["Lattice TC"].to_numpy(),
            )
        except KeyError:
            # A frame without the expected columns cannot be validated; the
            # processing step itself reports that case.
            continue
        for notice in sample_notices:
            notices.append(
                {
                    "severity": notice["severity"],
                    "field": notice["field"],
                    "message": f"[{name}] {notice['message']}",
                }
            )
    return notices


def calculate_thermoelectric_properties(
    T: np.ndarray,
    sigma: np.ndarray,
    S: np.ndarray,
    kappa: np.ndarray | None = None,
    lorenz: float | str | None = None,
    u_sigma: np.ndarray | None = None,
    u_S: np.ndarray | None = None,
    u_kappa: np.ndarray | None = None,
    u_T: np.ndarray | None = None,
) -> dict:
    """
    Calculate all thermoelectric properties from measured inputs.

    Args:
        T: Temperature [K].
        sigma: Electrical conductivity [S/m].
        S: Seebeck coefficient [V/K].
        kappa: Total thermal conductivity [W/(m·K)]. Optional.
        lorenz: Lorenz number [W·Ω/K²], ``"auto"`` for Seebeck-derived estimate,
            or ``None`` for the established Sommerfeld default.
        u_sigma: Absolute uncertainty in sigma [S/m]. Optional.
        u_S: Absolute uncertainty in S [V/K]. Optional.
        u_kappa: Absolute uncertainty in kappa [W/(m·K)]. Optional.
        u_T: Absolute uncertainty in temperature [K]. Optional; defaults to zero.

    Returns:
        Dict with keys: T, sigma, S, kappa, PF, kappa_e, kappa_L, ZT
        and corresponding u_* uncertainty keys if inputs were provided.
    """
    T = np.asarray(T, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    S = np.asarray(S, dtype=float)

    # Lorenz number
    lorenz_is_auto = isinstance(lorenz, str) and lorenz == "auto"
    u_L_values = None
    if lorenz_is_auto:
        S_uv_k = np.abs(np.asarray(S, dtype=float)) * 1e6
        L = estimate_lorenz(S_uv_k)
        # In "auto" mode the Lorenz number is derived from the measured
        # Seebeck coefficient, so its uncertainty follows from u(S):
        #   L(S) = (1.5 + exp(-|S|/116)) * 1e-8
        #   dL/dS = -(1/116) * exp(-|S|/116) * 1e-8   [per uV/K]
        # (audit issue SE-036)
        u_L_values = (
            np.exp(-S_uv_k / 116.0) / 116.0 * 1e-8
        ) * np.abs(np.asarray(u_S, dtype=float)) * 1e6 if u_S is not None else None
    else:
        L = DEFAULT_LORENZ if lorenz is None else float(lorenz)

    result = {
        "T": T,
        "sigma": sigma,
        "S": S,
        "PF": calculate_pf(S, sigma),
        "kappa_e": calculate_kappa_e(sigma, T, L),
    }

    result["kappa_L"] = None
    result["ZT"] = None

    if kappa is not None:
        kappa = np.asarray(kappa, dtype=float)
        result["kappa"] = kappa
        result["kappa_L"] = calculate_kappa_l(kappa, result["kappa_e"])
        result["ZT"] = calculate_zt(result["PF"], T, kappa)

    # Uncertainties.
    # Each contribution is evaluated as soon as its inputs are available:
    # previously u_kappa (and u_T alone) were silently dropped unless BOTH
    # u_sigma and u_S were supplied (audit issue SE-035).
    u_T_values = np.zeros_like(T) if u_T is None else np.asarray(u_T, dtype=float)
    if u_L_values is None:
        u_L_values = np.zeros(len(T))

    if u_sigma is not None and u_S is not None:
        u_sigma = np.asarray(u_sigma, dtype=float)
        u_S = np.asarray(u_S, dtype=float)
        result["u_PF"] = propagate_pf_error(S, u_S, sigma, u_sigma)

    if u_sigma is not None:
        result["u_kappa_e"] = propagate_kappa_e_error(
            sigma, np.asarray(u_sigma, dtype=float), T, u_T_values, L, u_L_values
        )

    if kappa is not None and u_kappa is not None:
        u_kappa = np.asarray(u_kappa, dtype=float)
        result["u_kappa"] = u_kappa
        if "u_kappa_e" in result:
            result["u_kappa_L"] = propagate_kappa_l_error(u_kappa, result["u_kappa_e"])
        if "u_PF" in result:
            result["u_ZT"] = propagate_zt_error(
                result["PF"], result["u_PF"],
                T, u_T_values,
                kappa, u_kappa,
            )

    return result


def calculate_zt_use_case(
    T: np.ndarray,
    sigma: np.ndarray,
    S: np.ndarray,
    kappa: np.ndarray,
    lorenz: float | str | None = None,
) -> np.ndarray:
    """Calculate ZT only, without full property suite."""
    result = calculate_thermoelectric_properties(T, sigma, S, kappa, lorenz)
    return result["ZT"]


def process_multi_sample_data(df: pd.DataFrame, lorenz=LEGACY_DEFAULT_LORENZ) -> pd.DataFrame:
    """Prepare one Multi-Sample dataset and calculate its established outputs.

    This Application workflow deliberately preserves the legacy DataFrame
    contract while delegating scientific equations to Domain. It remains a
    compatibility seam until the external dataframe contract is resolved.
    """
    processed = df.copy()
    processed = processed.apply(pd.to_numeric, errors="coerce")
    processed = processed.dropna(
        subset=["Temperature", "Seebeck", "Sigma", "Kappa_total"]
    )
    if processed.empty:
        raise ValueError("No valid data rows after cleaning")

    processed["Power Factor"] = calculate_pf(
        processed["Seebeck"], processed["Sigma"]
    )
    processed["PF_mW"] = processed["Power Factor"] * 1000.0
    processed["Sigma_Scm"] = processed["Sigma"] * 0.01
    processed["S_uVK"] = processed["Seebeck"] * 1e6
    processed["Electronic TC"] = calculate_kappa_e(
        processed["Sigma"], processed["Temperature"], lorenz
    )
    processed["Lattice TC"] = calculate_kappa_l(
        processed["Kappa_total"], processed["Electronic TC"]
    )
    processed["ZT"] = calculate_zt(
        processed["Power Factor"], processed["Temperature"], processed["Kappa_total"]
    )
    return processed


def process_multi_sample_batch(
    samples: dict[str, pd.DataFrame], lorenz=LEGACY_DEFAULT_LORENZ
) -> dict[str, pd.DataFrame]:
    """Process a batch of named samples in insertion order.

    A sample error currently aborts the batch, matching the established
    comparison workflow. The mapping preserves names and deterministic order.
    """
    return {
        name: process_multi_sample_data(frame, lorenz=lorenz)
        for name, frame in samples.items()
    }


def validate_measurement_data(T, sigma=None, S=None, kappa=None, kappa_L=None):
    """
    Validate measurement inputs and return a list of validation messages.

    ``kappa_L`` is forwarded so that the negative-lattice-conductivity
    diagnostic (a sign that the Lorenz number or the units are wrong) is
    reachable from the application layer (audit issue SE-038).

    Returns:
        List of ValidationMessage objects.
    """
    return validate_dataset(T, sigma=sigma, S=S, kappa=kappa, kappa_L=kappa_L)


def validate_calculated_properties(T, sigma=None, S=None, kappa=None, kappa_L=None):
    """Validate a *computed* property suite and return presentation-safe notices.

    This is the application-layer entry point used by the GUI to surface
    scientific validation messages. It exists because the domain validators
    were, until audit finding D-01, never called from any production path:
    a physically impossible lattice thermal conductivity (kappa_L < 0) was
    displayed, plotted and exported as an ordinary value.

    The return value is a list of plain dictionaries with the keys
    ``"severity"``, ``"field"`` and ``"message"``. Plain records are used so
    that the presentation layer never has to import the domain types (the
    layer boundary is enforced by ``tests/test_architecture_dependencies.py``).

    Rows without a finite temperature are ignored: they are empty table
    rows, not data, and an empty table must not raise an error.

    Args:
        T: Temperature [K].
        sigma: Electrical conductivity [S/m].
        S: Seebeck coefficient [V/K].
        kappa: Total thermal conductivity [W/(m*K)].
        kappa_L: Lattice thermal conductivity [W/(m*K)].

    Returns:
        List of ``{"severity": str, "field": str, "message": str}`` records.
        An empty list means the data passed every applicable check.
    """
    T = np.asarray(T, dtype=float)
    finite = np.isfinite(T)
    if not finite.any():
        # An empty table is the normal initial state, not a data error.
        return []

    def _subset(values):
        if values is None:
            return None
        array = np.asarray(values, dtype=float)
        if array.shape != T.shape:
            return array
        return array[finite]

    messages = validate_dataset(
        _subset(T),
        sigma=_subset(sigma),
        S=_subset(S),
        kappa=_subset(kappa),
        kappa_L=_subset(kappa_L),
    )
    return [
        {
            "severity": message.severity.value,
            "field": message.field,
            "message": message.message,
        }
        for message in messages
    ]


def calculate_weighted_mobility_use_case(temperature_k, resistivity_mohm_cm, seebeck_uv_k):
    """Application entry point for the independent weighted-mobility model."""
    return _calculate_weighted_mobility(
        temperature_k, resistivity_mohm_cm, seebeck_uv_k
    )


def calculate_efficiencies_use_case(
    temps_k, seebecks_v_k, sigmas_s_m, kappas_w_mk, tc_k, th_k
):
    """Application entry point for the device-efficiency model."""
    return _calculate_efficiencies(
        temps_k, seebecks_v_k, sigmas_s_m, kappas_w_mk, tc_k, th_k
    )


def convert_resistivity_to_mohm_cm(value, unit):
    """Application entry point for the weighted-mobility input conversion."""
    return _resistivity_to_mohm_cm(value, unit)


def calculate_kappa_from_lfa_si_use_case(diffusivity_m2_s, heat_capacity_j_kg_k, density_kg_m3):
    """Calculate thermal conductivity from SI-normalized LFA measurements."""
    return _kappa_from_diffusivity_si(
        diffusivity_m2_s, heat_capacity_j_kg_k, density_kg_m3
    )


def propagate_lfa_kappa_uncertainty_use_case(
    diffusivity_m2_s,
    diffusivity_error_m2_s,
    heat_capacity_j_kg_k,
    heat_capacity_error_j_kg_k,
    density_kg_m3,
    density_error_kg_m3,
):
    """Propagate independent LFA input uncertainties through κ=αCpρ."""
    return propagate_kappa_error(
        diffusivity_m2_s,
        diffusivity_error_m2_s,
        heat_capacity_j_kg_k,
        heat_capacity_error_j_kg_k,
        density_kg_m3,
        density_error_kg_m3,
    )


def combine_relative_uncertainties_use_case(value, *relative_uncertainties):
    """Combine independent relative measurement errors for a derived value."""
    return _propagate_relative_uncertainty(value, *relative_uncertainties)


def calculate_formula_mass_use_case(formula):
    """Calculate formula mass while preserving the legacy 118-element table."""
    return _calculate_legacy_molecular_weight(formula)


def calculate_dulong_petit_limit_use_case(atom_count, molar_mass_g_mol, unit):
    """Application entry point for the Dulong–Petit display calculation."""
    return _calculate_dulong_petit_limit(atom_count, molar_mass_g_mol, unit)
