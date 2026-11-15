# Seebeck-Prime Research Positioning — SoftwareX Stage 1

**Document type:** Stage 1 deliverable of the SoftwareX manuscript preparation.
**Date:** 2026-11-12
**Companion documents:** `manuscript/SoftwareX/SOFTWARE_CAPABILITY_MATRIX.md`,
`manuscript/SoftwareX/MANUSCRIPT_OUTLINE.md`,
`manuscript/SoftwareX/AUTHOR_INPUT_REQUIRED.md`.

---

## 1. The practical problem (as evidenced in the repository)

Thermoelectric transport-property work is, in practice, a sequence of
interdependent steps that researchers assemble by hand:

1. measure Seebeck coefficient, electrical conductivity, thermal conductivity;
2. combine them into power factor and figure of merit;
3. derive or estimate the Lorenz number;
4. decompose total thermal conductivity into electronic and lattice parts;
5. invert (Seebeck, conductivity, temperature) for an effective carrier mass;
6. compute device efficiency;
7. propagate uncertainties.

Each step has its own unit convention and its own modelling assumption, and the
steps are easy to mix (e.g. κL as a difference of two close numbers; Lorenz number
choice propagating directly into κL and ZT). The Seebeck-Prime repository was
built to make this sequence reproducible, numerical, and traceable.

## 2. Literature findings (to be cited / confirmed)

The following are the literature anchors already recorded in the repository and
are the ones the manuscript should rely on unless the author supplies more:

- **Wiedemann (1853) / Franz (1854):** κe = L·σ·T. Recorded as the basis of the
  electronic-thermal-conductivity implementation; the Wiedemann–Franz relation is
  listed in the scientific background.
- **Sommerfeld (1928) / Lorenz (1919):** L0 = (π²/3)(kB/e)² = 2.443004509e-8 W·Ω/K².
  The unified constant used throughout the programme.
- **Kim et al. (2015), *APL Materials* 3, 041506:** empirical Lorenz number
  L(S) = (1.5 + e^(−|S|/116))·10⁻⁸. Acoustic-phonon approximation.
- **Snyder & Toberer (2008), *Nature Materials* 7, 105–114:** Pisarenko analysis,
  single parabolic band; F1/2 inversion.
- **Snyder et al. (2020), *Advanced Materials* 32, 2001537:** weighted mobility.
- **May & Snyder (2012), CRC Press:** introduction to modelling thermoelectric
  properties of semiconductors (Fermi–Dirac integrals).
- **Goldsmid (2016):** thermoelectric power factor / ZT conventions.
- **Putley (1960):** Hall effect and related phenomena (Hall mobility).

**SoftwareX-relevant literature to check:** the manuscript should compare against
existing thermoelectric *software* rather than only against equations. At Stage 1
the repository inventory contains **no** third-party thermoelectric-analysis
software comparison that could be cited from the local tree; any such comparison
in the final draft must come from the author or from verified public sources and
must not be fabricated (per the task rules).

## 3. Positioning statement (defensible)

> Seebeck-Prime is an integrated desktop application that turns the standard
> thermoelectric measurement triad (S, σ, κ) into power factor, figure of merit,
> Lorenz-number-conditioned electronic and lattice thermal conductivities, SPB-based
> carrier/Seebeck inversion, and device efficiency — under a single unit convention
> and with traceable uncertainty propagation.

Defensible because:
- the calculation engine was independently re-derived and agrees to ~1e-14…1e-6
  relative error;
- the application-wide Lorenz constant (2.44e-8 W·Ω/K²) reproduces the published
  SiGe:P data to ≤0.7 %;
- the full pipeline (manual or instrument-derived inputs → transport properties →
  plots/exports) is implemented end to end at the headless level.

## 4. Defensible novelty claims (Stage 1 — author to confirm)

1. **Integrated desktop workflow for thermoelectric transport analysis.** The
   defensible claim is *integration of the calculation, modelling, and uncertainty
   chain behind one desktop UI and one unit convention*, not the invention of any
   single equation.
2. **Rigorous SPB Lorenz number with unnormalised Fermi-Dirac integrals and
   explicit Blatt-normalisation reconciliation** (verified to 2.7e-14), plus the
   Seebeck-from-η inversion and carrier-density/effective-mass round trips.
3. **Negative-result transparency:** the programme *quantified* the SiGe:P
   acoustic-scattering contradiction (35 %) and did not silently re-fit the model.

## 5. Claims that should be avoided (author must confirm before drafting)

- "Seebeck-Prime is the first thermoelectric software." → **Avoid** without a
  defensible literature comparison.
- "All thermoelectric models are validated." → **Avoid**; the models are
  conditionally physical.
- "The weighted mobility is validated." → **Avoid**; it is **PARTIALLY VERIFIED**
  (physics UNVERIFIED).
- "The Lorenz number is experimental." → **Avoid**; the SiGe:P value is
  implied-from-published-κ/κL and the Lorenz estimate is model-derived.
- "The software validates all experimental data." → **Avoid**; only four
  specimens were benchmarked, and the PbTe comparison is **UNVERIFIED**.

## 6. Research gap

The gap the software addresses (as evidenced locally): researchers must combine
several programs / spreadsheets / custom scripts to move from measured S, σ, κ to
ZT, and to keep unit conventions and modelling assumptions consistent across
steps. Seebeck-Prime's positioning is that this chain can be provided as one
reproducible, testable, desktop-resident workflow.

---

*Stage 1 decision: the positioning above is **drafted from repository evidence
only**; literature details and novelty claims require author confirmation before
they are cited in the manuscript.*
