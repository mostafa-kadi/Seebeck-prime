"""Tests for scientific dataset validation rules (``seebeck_prime.domain.validation``)."""

from __future__ import annotations

import numpy as np

from seebeck_prime.domain.validation import (
    Severity,
    ValidationMessage,
    validate_conductivity_array,
    validate_dataset,
    validate_kappa_array,
    validate_kappa_l_array,
    validate_seebeck_array,
    validate_temperature_array,
)


def test_empty_temperature_array_is_an_error():
    messages = validate_temperature_array(np.array([]))

    assert messages[0].severity is Severity.ERROR
    assert messages[0].field == "T"


def test_non_positive_temperature_is_an_error():
    messages = validate_temperature_array(np.array([300.0, 0.0, -5.0]))

    assert any(m.severity is Severity.ERROR for m in messages)


def test_extreme_temperatures_warn_about_units():
    messages = validate_temperature_array(np.array([0.5, 9000.0]))

    assert any(m.severity is Severity.WARNING and "low" in m.message for m in messages)
    assert any(m.severity is Severity.WARNING and "high" in m.message for m in messages)


def test_duplicate_temperatures_warn():
    messages = validate_temperature_array(np.array([300.0, 300.0, 400.0]))

    assert any("Duplicate" in m.message for m in messages)


def test_clean_temperature_array_produces_no_messages():
    assert validate_temperature_array(np.array([300.0, 400.0, 500.0])) == []


def test_negative_conductivity_is_an_error_and_huge_warns():
    negative = validate_conductivity_array(np.array([-1.0]))
    huge = validate_conductivity_array(np.array([2e8]))

    assert negative[0].severity is Severity.ERROR
    assert huge[0].severity is Severity.WARNING


def test_seebeck_above_2000_uv_per_k_warns_about_units():
    messages = validate_seebeck_array(np.array([3e-3]))  # 3000 uV/K in SI V/K

    assert messages[0].severity is Severity.WARNING
    assert messages[0].field == "S"


def test_negative_kappa_is_error_and_negative_kappa_l_warns():
    kappa_messages = validate_kappa_array(np.array([-1.0]))
    kappa_l_messages = validate_kappa_l_array(np.array([-0.1]))

    assert kappa_messages[0].severity is Severity.ERROR
    assert kappa_l_messages[0].severity is Severity.WARNING
    assert kappa_l_messages[0].field == "kappa_L"


def test_validate_dataset_combines_all_applicable_checks():
    messages = validate_dataset(
        np.array([300.0, -1.0]),           # T error
        sigma=np.array([1e5, 1e5]),
        S=np.array([1e-4, 1e-4]),
        kappa=np.array([-2.0, 2.0]),        # kappa error
        kappa_L=np.array([-0.5, 0.5]),      # kappa_L warning
    )

    fields = [m.field for m in messages]
    assert "T" in fields
    assert "kappa" in fields
    assert "kappa_L" in fields


def test_validation_message_str_format():
    message = ValidationMessage(Severity.ERROR, "T", "bad value")

    assert str(message) == "[ERROR] T: bad value"
