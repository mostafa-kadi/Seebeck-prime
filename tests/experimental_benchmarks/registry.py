"""Canonical registry of the experimental benchmarks.

Single source of truth for the benchmark set: the extraction scripts, the
tests and the validation reports all refer to this registry, and a test
verifies that the on-disk datasets and the published reports agree with it.

``comparisons`` maps every published grid to the *kind* of comparison that the
grid supports:

``experimental``  the software is compared with an independently published
                  measurement that was not used to derive anything in the
                  comparison;
``consistency``   the comparison is an internal-consistency (arithmetic)
                  check of the published data - e.g. the lattice thermal
                  conductivity recomputed with a Lorenz number *derived from
                  the same published lattice conductivity* - and therefore
                  says nothing about the correctness of the model.

The distinction is the outcome of the final validation audit
(docs/EXTENDED_VALIDATION_REPORT.md, section 2) and is enforced by
``test_report_consistency.py``.
"""

from __future__ import annotations

REGISTRY = {
    "b2te3_bi2te2_4se0_6cu0_006": {
        "family": "Bi2Te3-based",
        "composition": "Bi2Te2.4Se0.6Cu0.006",
        "doi": "10.1007/s10854-019-01874-0",
        "journal": "Journal of Materials Science: Materials in Electronics",
        "year": 2019,
        "title": (
            "Effect of Cu electroless plating on thermoelectric properties of "
            "n-type Bi2Te2.4Se0.6 alloy"
        ),
        "sample_note": "n-type Bi2Te2.4Se0.6 with Cu electroless plating",
        "grids": ["pf", "zt", "kappa_l", "carrier_concentration", "carrier_mobility"],
        "comparisons": {
            "pf": "experimental",
            "zt": "experimental",
            # the Lorenz number is derived from the published kappa_L, so this
            # is an arithmetic consistency check, not an experimental one
            "kappa_l": "consistency",
        },
        "notes": (
            "The published carrier-mobility curve is negative (physically "
            "impossible) and therefore unusable as a reference."
        ),
    },
    "pbte_pbte0_95pbs0_05": {
        "family": "PbTe-based",
        "composition": "(PbTe)0.95(PbS)0.05",
        "doi": "10.1016/j.cap.2020.06.028",
        "journal": "Current Applied Physics",
        "year": 2020,
        "title": (
            "Thermoelectric performance in pseudo-ternary "
            "(PbTe)0.95-x(Sb2Se3)x(PbS)0.05 system with ultra-low thermal "
            "conductivity"
        ),
        "sample_note": "pseudo-ternary PbTe-PbS-Sb2Se3",
        "grids": ["pf", "zt", "kappa_l"],
        "comparisons": {
            "pf": "experimental",
            "zt": "experimental",
            "kappa_l": "consistency",
        },
        "notes": (
            "The published total and lattice thermal conductivities are not "
            "consistent with a single Lorenz number (25 % scatter), so even "
            "the consistency check is noise-limited and is reported UNVERIFIED."
        ),
    },
    "sige_si80ge18sb2": {
        "family": "SiGe-based",
        "composition": "Si80Ge18Sb2",
        "doi": "10.1016/j.enconman.2015.01.082",
        "journal": "Energy Conversion and Management",
        "year": 2015,
        "title": (
            "Thermoelectric performance of Si80Ge20-xSbx based multiphase "
            "alloys with inhomogeneous dopant distribution"
        ),
        "sample_note": "Sb-doped SiGe multiphase alloy",
        "grids": ["pf", "zt"],
        "comparisons": {
            "pf": "experimental",
            "zt": "experimental",
        },
        "notes": "No lattice thermal conductivity is published for this sample.",
    },
    "sige_si80ge20p1": {
        "family": "SiGe-based",
        "composition": "Si80Ge20P1",
        "doi": "10.1021/acsami.9b20090",
        "journal": "ACS Applied Materials & Interfaces",
        "year": 2020,
        "title": (
            "Enhanced Thermoelectric Performance in n-Type SrTiO3/SiGe Composite"
        ),
        "sample_note": (
            "single-phase P-doped SiGe reference of the SrTiO3/SiGe composite "
            "study (Starrydata sample name '0wt% SrTiO3')"
        ),
        "grids": [
            "pf", "zt", "kappa_e", "kappa_l", "carrier_concentration",
            "carrier_mobility",
        ],
        "comparisons": {
            "pf": "experimental",
            "zt": "experimental",
            # computed with the application's own a-priori constant
            # L = 2.44e-8, so this is a genuine experimental comparison
            "kappa_l": "experimental",
            "kappa_e": "experimental",
            "carrier_concentration": "experimental",
            "carrier_mobility": "experimental",
        },
        "notes": (
            "The paper reports ZT = 0.91 at 1000 K for the composite; the "
            "single-phase SiGe:P reference published here reaches ZT = 0.87. "
            "The Lorenz number implied by the published kappa and kappa_L is "
            "the Sommerfeld value, not the single-parabolic-band value."
        ),
    },
}

#: The kinds a comparison may have.
COMPARISON_KINDS = ("experimental", "consistency")
