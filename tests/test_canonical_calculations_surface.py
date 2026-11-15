"""Canonical calculation surface: domain defaults and constants.

Created during the architecture migration (Phase 3) to replace
``tests/test_legacy_calculations_compatibility.py`` when the compatibility
shim ``seebeck_prime.legacy.core`` was retired (Phase 4). Every numerical
assertion of the replaced file is preserved unchanged; the former
shim-vs-domain identity assertions lose their subject with the shim and are
intentionally not carried over.
"""

import pytest

from seebeck_prime.domain import calculations as domain
from seebeck_prime.domain.physical_constants import (
    LEGACY_ATOMIC_WEIGHTS,
    LEGACY_DEFAULT_LORENZ,
    LEGACY_GAS_CONSTANT,
    SILICON_DEFAULT_DEBYE_T,
    SILICON_DEFAULT_SOUND_VELOCITY,
)


def test_transport_default_lorenz_is_the_rounded_sommerfeld_value():
    """The historical default 2.44e-8 W·Ω·K⁻² must keep being used."""
    assert domain.calculate_kappa_e(1e5, 300.0) == pytest.approx(
        2.44e-8 * 1e5 * 300.0
    )


def test_molecular_weight_keeps_full_element_support():
    mass, atom_count = domain.calculate_legacy_molecular_weight("NaCl")
    assert mass == pytest.approx(58.44)
    assert atom_count == 2


def test_domain_constants_keep_the_legacy_defaults():
    assert LEGACY_DEFAULT_LORENZ == 2.44e-8
    assert LEGACY_GAS_CONSTANT == 8.314462618
    assert SILICON_DEFAULT_DEBYE_T == 645.0
    assert SILICON_DEFAULT_SOUND_VELOCITY == 5880.0
    assert len(LEGACY_ATOMIC_WEIGHTS) == 118
