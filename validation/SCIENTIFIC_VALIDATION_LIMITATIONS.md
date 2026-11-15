# Scientific Validation Limitations — Seebeck Prime

**Version:** 1.0
**Date:** 2026-11-12

This document states, in one place, everything that the validation
programme of `validation/` **cannot** establish, and what a reader of the
results must therefore not conclude.

It is deliberately written as a list of *negative* findings. A validation
report that lists only what passed is not usable for a scientific software
publication.

---

## 1. Epistemic status of the evidence

The programme produced three kinds of evidence. They are not
interchangeable, and the strongest one applies to the fewest calculations.

| Evidence class | What it shows | How many calculations |
|---|---|---|
| **Analytical** — a closed-form identity or a physical limit | the *formula* is right | most of the engine |
| **Independent numerical** — a separately written implementation of the same equation | the software *computes* what the formula says | all implemented equations |
| **Experimental** — an independently published measurement of the same specimen | the software reproduces *a real measurement* | 4 specimens (PF, ZT, κ_L, κₑ, n, μ) |

**Limitation 1.1 — Independent numerical validation cannot validate a
model.** Every reference implementation in
`validation/independent_calculations/` implements the *same* governing
equation as the application. If the equation is wrong for the material, both
the application and the reference are wrong together, and the comparison
passes. The independence is independence **of code**, not **of physics**.
The only way to test the physics is the experimental class, which is
available for four specimens.

**Limitation 1.2 — The reference implementation inherits the same
convention choices.** Where the application and the reference must agree
on a convention (e.g. that the scattering exponent satisfies λ = r + ½),
the agreement is not evidence for the convention — it is evidence that the
two were derived consistently. The convention itself was checked
*analytically* (against the Sommerfeld and Boltzmann limits), and that is
the strongest statement available.

---

## 2. No certified reference material

**Limitation 2.1 — Nothing was measured against a certified reference
material.** A full metrological traceability chain (CRMs, calibrated
instruments, a recognised calibration laboratory) was **not** available and
was **not** attempted. The application's validation is therefore against:

- published literature values (digitised from figures), and
- independent re-implementations of the same equations.

**Consequence.** The validation demonstrates *internal and analytical
correctness* and *agreement with published values*. It does **not**
demonstrate *metrological traceability* of the software's outputs. For a
SoftwareX submission this must be stated explicitly; a reader must not
infer that a Seebeck coefficient computed by Seebeck Prime is traceable to
a national standard.

**Limitation 2.2 — The published reference values carry an unknown
digitisation uncertainty.** The benchmark curves are digitised from the
publications' figures (tracing precision ≈1 % of the axis range), and the
publications' own measurement uncertainties are not available in the
aggregated source. The experimental comparisons therefore carry a floor of
roughly 1–2 % that no software improvement can go below. This is why the
tolerances are 5 % (PF) and 10 % (ZT) rather than machine precision.

---

## 3. Model limitations — the most important section

### 3.1 The single parabolic band

**Limitation 3.1.1 — SPB is implemented correctly but is not a universal
model.** The implementation is verified against an independent reference to
≤1e-6 relative error for every scattering exponent tested (λ = 0, 1, 2) and
against the classical and degenerate limits. That says nothing about
whether a given material is a single parabolic band.

The following are **known** to violate the single-band assumption and are
**not** handled by the application:

- **Bipolar transport** (Mg₂Sn, Mg₂Si₀.₄Sn₀.₆ and other Mg₂Si–Sn alloys
  above their bipolar onset): both carriers contribute, the measured
  Seebeck coefficient is not a single-band quantity, and the SPB inversion
  is not physically applicable.
- **Multiband conduction** (Bi₂Te₃ with Cu, PbTe with Sb/Se alloying):
  the band structure is not parabolic and not single.
- **Strong anisotropy** (SnSe): the in-plane and c-axis transport
  properties differ by one to two orders of magnitude; the application's
  transport model is isotropic and the data model carries no direction
  label.
- **Kane/band-narrowing** (degenerate PbTe): the high-degeneracy limit
  invalidates the parabolic-band dispersion.

**Limitation 3.1.2 — The SPB effective mass could not be cross-checked.**
The inversion for P-doped SiGe yields m\* = 1.49–2.23 mₑ (median
1.70 mₑ), which is physically reasonable. It was **not** validated against
a published m\*: the abstract of `10.1021/acsami.9b20090` states no
effective mass and the full text is not openly available. The claim is
therefore *plausibility*, not validation.

**Limitation 3.1.3 — The SPB effective mass inherits the scattering
assumption.** The inverted m\* depends on the assumed scattering exponent
(λ = 0 by default). A different λ gives a different m\* for the same
(S, n, T). The dependency is documented in the registry (E-27) but is not
surfaced as a warning in the UI.

### 3.2 The Lorenz number

**Limitation 3.2.1 — The Lorenz number is the dominant source of model
error in this software.** κₑ = LσT and therefore κ_L and ZT all inherit
the error in L. The measured spread, comparing the rigorous SPB value with
the value implied by each specimen's own published data:

| Specimen | L implied by the published data | pair spread | **κ_L sensitivity** to L = 2.44e-8 | **SPB deviation** (acoustic, λ = 0) |
|---|---|---|---|---|
| Si₈₀Ge₂₀P₁ | 2.4579e-8 W·Ω/K² | 3.0 % | 0.7 % | **−37.7 % … −25.2 %** (median −35 %) |
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 1.6525e-8 W·Ω/K² | 3.4 % | 26.5 % | **−3.6 % … −1.5 %** |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | 1.2765e-8 W·Ω/K² | 24.9 % | 130.6 % | **+10.0 % … +46.0 %** |

The two right-hand columns are **different quantities** and were previously
conflated under a single "SPB deviation" header: the *κ_L sensitivity* is
how much the computed lattice conductivity changes when the constant is used
instead of the implied value, whereas the *SPB deviation* is the gap between
the rigorous acoustic-scattering value and the implied value. Reproduce with
`python tools/lorenz_diagnostics.py`.

The PbTe figure is the extreme case for the **κ_L sensitivity**: the
published κ/κ_L pair there implies a Lorenz number with a **24.9 % spread**,
so it is not internally consistent and the implied value cannot be used to
judge any model. (The specimen is in the *transitional* degeneracy regime —
η from −0.04 to +1.32, F₁⁄₂ from 0.66 to 1.71 — rather than strongly
degenerate; the Phase 3 assessment found that a Kane or Dingle correction
could not be evaluated because the required inputs — Hall carrier
concentration, mobility, effective mass and band gap — are **not available**
in the benchmark data and no independent reference exists against which such
a model could be validated. See
`validation/remediation/DEGENERATE_LORENZ_ASSESSMENT.md`.) Any κ_L or ZT
computed for such a material with the SPB mode carries that error.

**Limitation 3.2.2 — The published data contradict the embedded SPB
acoustic-phonon model for the one specimen that can decide the question.**
For Si₈₀Ge₂₀P₁, the published κ, κ_L and σ imply
L = 2.4579e-8 W·Ω/K², which agrees with the Sommerfeld value (0.6 %) and
**disagrees with the rigorous SPB acoustic value (1.592e-8) by ≈35 %**.

This is *not* a code defect — it is a finding. The application offers the
SPB-derived ("auto") Lorenz number, and that mode therefore carries the
SPB model's −35 % bias for this material. The application's **default**
constant (2.44e-8 W·Ω/K²) is the one that agrees with the published data
(≤0.7 % on κ_L). The auto mode must not be described as physically
validated; its own documentation states the approximation's range.

**The cause was identified in Phase 3**
(`validation/remediation/SIGE_LORENZ_INVESTIGATION.md`): the **scattering
assumption**, not the implementation and not a failure of the
single-parabolic-band model. The published κ/κ_L pair is internally
consistent (3.0 % spread, at the 1.7 % digitisation noise floor — unlike the
PbTe pair, whose 25 % spread is why *that* comparison is UNVERIFIED), and a
scattering exponent **λ ≈ 1.41** — between alloy/optical (1) and
ionised-impurity (2) scattering, as expected for a P-doped alloy — reproduces
the published value **exactly**. The specimen crosses the
classical-to-degenerate transition (F₁⁄₂ from 0.29 to 2.24), where the Lorenz
number is strongly scattering-dependent. **The model was not refitted**; the
negative result is preserved and locked in by
`tests/scientific/test_sige_lorenz_finding.py`, which fails if the acoustic
value is ever made to agree with the measurement.

**Limitation 3.2.3 — The Kim empirical relation is an acoustic-scattering
fit, not a universal law.** L(S) = (1.5 + exp(−|S|/116))·10⁻⁸ tracks the
rigorous SPB value with the following deviations (at |S| = 150 µV/K; the
deviation grows with |S| for λ ≥ 1):

| Scattering | Deviation of the Kim value from the SPB value at \|S\| = 150 µV/K | Range over \|S\| = 50 … 250 µV/K |
|---|---|---|
| λ = 0 (acoustic) | **+2.8 %** | −3.2 % … +3.6 % |
| λ = 1 (optical/alloy) | **−21.7 %** | −10.4 % … −27.6 % |
| λ = 2 (ionised impurity) | **−31.8 %** | −12.6 % … −41.9 % |

The relation is therefore only appropriate where acoustic-phonon transport
dominates.

**Limitation 3.2.4 — The application's default Lorenz constant is a
rounded value.** The default is 2.44e-8 W·Ω/K²; the exact Sommerfeld value
is 2.443004509e-8 (a 0.13 % difference). This is a deliberate, documented
author decision — a unified default across all Lorenz modes — and is not a
defect, but it means the default is not the Sommerfeld value *exactly*.

### 3.3 The Wiedemann–Franz decomposition

**Limitation 3.3.1 — κ_L = κ_total − κₑ is valid only below the bipolar
onset.** Above it, the minority-carrier contribution inflates κ_total and
the subtraction mis-attributes it to the lattice. The application flags a
*negative* κ_L but has **no** bipolar-onset detection.

**Limitation 3.3.2 — The negative-κ_L warning does not reach the user.**
The validator (`domain/validation.py::validate_kappa_l_array`) correctly
produces a `WARNING` for κ_L < 0, and
`application/use_cases.py::validate_measurement_data` forwards it — but
**no production code path calls either function**, so the diagnostic is
never shown (audit finding D-01). A physically impossible lattice thermal
conductivity is currently displayed, plotted and exported as an ordinary
value. Even once the warning is wired through, the application does not
compare a small negative value against the propagated uncertainty to
decide whether it is significant.

---

## 4. Scope limitations — what is not implemented

**Limitation 4.1 — The raw measurement chain is not implemented.** The
application does **not** implement V/I → R → ρ → σ. It assumes the
instrument file already contains the electrical conductivity. There is
therefore **no** validation of a raw-measurement chain, and none is
claimed. The instrument files used in the importer tests are
*reconstructions* in the instrument **format**, derived from published
curves — they are **format/parsing** validation, not a
measurement-chain validation.

**Limitation 4.2 — There is no uncertainty propagation for the weighted
mobility or for the SPB outputs.** Those calculations have no implemented
uncertainty, so none is validated. The SPB outputs in particular compound
the uncertainty of S, n and T *and* the uncertainty of the assumed
scattering exponent, which is not quantifiable from the input data.

**Limitation 4.3 — No covariance is modelled.** Every uncertainty
propagator assumes the inputs are **statistically independent**. For a
real measurement this is rarely true: the Seebeck coefficient and the
electrical conductivity are frequently measured with a shared
thermocouple, a shared geometry or a shared temperature scan, and the
thermal conductivity and the electrical conductivity are often derived
from the same specimen under the same conditions. The application offers
no way to enter a covariance, so a user cannot correct for this. This is a
modelling limitation, not a bug.

**Limitation 4.4 — The uncertainty model is first-order only.** The
propagators are linearised. For a quantity with a strongly non-linear
dependence on a poorly known input (e.g. m\* from a Seebeck coefficient
near the metallic limit), the first-order estimate is not adequate. The
Monte-Carlo reference used in the tests quantifies the discrepancy only for
the two quantities where it was applied (PF and laser-flash κ), where it is
below 5e-3.

**Limitation 4.5 — The interactive GUI is not covered.** Six calculation
dialogs (error bar, Kappa, SPB, Hall, weighted mobility, multi-sample),
the clipboard paste, the menus and the plot export have **no** automated
coverage. The reason is structural: each dialog is opened with a modal
`dialog.exec()`, which blocks the event loop and cannot be driven by
`QTest` without refactoring the dialogs to a non-modal form. No such
refactoring was performed, because it would change production code for
testability alone. The headless GUI stack (spreadsheet recalculation,
display-unit rendering, plot-data preparation, the subprocess end-to-end
driver) **is** covered.

**Limitation 4.6 — Some unit systems are not supported.** Only
W/(m·K) is available for thermal conductivity (no W/(cm·K)); the
application's conductivity display covers S/m, S/cm and Ω·cm. These are
choices, not defects, but they limit the import surface. The converter now
*rejects* an unsupported thermal-conductivity unit instead of silently
treating it as W/(m·K) (defect SE-042, fixed), and the application layer
preserves its documented pass-through for an unrecognised unit.

**Limitation 4.7 — The chemical formula parser is deliberately narrow.** It
accepts the subset of syntax used by the intended workflows and rejects
anything else with a message (audit issue SE-002). It is not a general
chemical-formula parser.

**Limitation 4.8 — Legacy behaviour was preserved, not corrected.** The
SPB batch's mean mass/temperature pairing rule (E-51) is a legacy
behaviour that is *documented* rather than changed, because changing it
would alter results for existing users without scientific justification
from the available data.

---

## 5. Data limitations

**Limitation 5.1 — The published carrier concentration is in m⁻³; the
application's API expects cm⁻³.** The unit interpretation was *confirmed*
rather than assumed, using the independent relation μ = σ/(n·e) on the
published data (median ratio 1.08). A unit error would have produced a
factor of 10⁶ or 10⁻⁶. The confirmation is strong but it is a
*consistency* argument, not a metrological one.

**Limitation 5.2 — The published carrier-mobility curve for the Bi₂Te₃
benchmark is negative.** It is physically impossible and therefore cannot
serve as a reference. The consequence is concrete: **weighted mobility has no experimental validation in this repository.** The implementation equation has since been corrected against Snyder et al. (2020), DOI: 10.1002/adma.202001537, and independently regression-tested; this does not replace a matched experimental reference dataset. The comparison is skipped with the reason recorded, not replaced by a substitute value.

**Limitation 5.3 — The published κ and κ_L of the PbTe benchmark are not
consistent with a single Lorenz number** (implied L = 1.276e-8, spread
25 %). The lattice-κ comparison for that specimen is therefore limited by
the source data, not by the calculation, and is reported UNVERIFIED.

**Limitation 5.4 — The published data are not all from the same specimen
or the same conditions.** Only comparisons of the *same* specimen under
*compatible* conditions are performed. Where a publication reports a
composite and a reference sample, the reference sample is used and the
relationship is documented (e.g. the SiGe:P reference versus the
SrTiO₃/SiGe composite in `10.1021/acsami.9b20090`).

**Limitation 5.5 — Only three families have active experimental
comparisons, and only two quantities (PF, ZT) are compared for all of
them.** Mg₂Sn, SnSe and CaMnO₃ have no active comparison in this cycle;
the reasons are scientific and are given in
`SCIENTIFIC_BENCHMARK_MATERIAL_FAMILIES.md` §5 (two-band transport,
anisotropy, and the circularity of deriving a Lorenz number from the same
publication's κ_L). The framework, the extraction procedure and the
provenance discipline are in place for them.

---

## 6. Software-process limitations

**Limitation 6.1 — The CI workflow has never been executed.** The GitHub
Actions workflow (`.github/workflows/tests.yml`) exists but has never run,
because no push has been performed. All results in this programme come
from local runs. A publication claim of "continuously integrated tests"
would be false.

**Limitation 6.2 — The golden baseline is a regression snapshot, not a
scientific reference.** `tests/golden/baseline_outputs.json` was generated
by the application itself. It detects *changes* in behaviour; it provides
**no** evidence of correctness. It is labelled as such wherever it appears.

**Limitation 6.3 — The primary development environment cannot load Qt.**
The conda environment's PyQt6 6.11.0 fails with a DLL error
(`0xc0000139`) when importing QtWidgets. The GUI tests are therefore
skipped there and executed in a documented Qt-capable venv (PyQt6 6.9.1 /
Qt 6.9.0). The two environments differ in the Qt build only; the GUI code
path is identical. An environment in which the application cannot even
start its main window is a **reproducibility risk** for third-party users
and should be fixed by pinning a working Qt build in the dependency
specification.

**Limitation 6.4 — The reference implementation is not independent of the
*input data*.** It re-implements the equations, not the acquisition. It
therefore cannot detect a systematic error in the instrument-file parsing
that affects both the application and the benchmark datasets. The
instrument files are reconstructions from published curves, so this class
of error is only partly covered.

**Limitation 6.5 — The reference module is verified for independence
mechanically, but "independently written" is a human claim.** The test
suite proves that the reference does not import the application, uses a
different numerical method where one exists, and depends only on NumPy,
SciPy and the standard library. It cannot prove that a different person
wrote it, and the two occasions on which the reference (not the
application) was wrong show that independent re-derivation is itself
error-prone — a *desirable* property for validation, but a reminder that
two agreeing implementations are still not ground truth.

---

## 7. What would change these conclusions

| Limitation | What would resolve it |
|---|---|
| 2.1 — no certified reference material | measuring a reference specimen with a CRM-traceable instrument, and documenting the traceability chain |
| 3.2.2 — SPB model contradicted by the SiGe data | an independent determination of the scattering exponent for the specimen; or a multi-band SPB implementation validated against the same data |
| 3.2.1 — Lorenz error: the κ_L sensitivity reaches 130.6 % on the PbTe specimen, and the SPB deviation is 10–46 % there and 15–38 % on P-doped SiGe | a rigorous, degeneracy-aware Lorenz number (Kane/Dingle-corrected) *and* a measured scattering exponent per material family — see the Phase 3 assessment |
| 4.1 — no raw measurement chain | implementing V/I → R → ρ → σ with geometry and its uncertainty; then a full measurement-chain validation |
| 4.3 — no covariance model | adding a covariance input to the uncertainty propagators, or at minimum a documented warning |
| 4.5 — interactive GUI untested | refactoring the dialogs to a non-modal, injectable form so that `QTest` can drive them |
| 5.2 — no weighted-mobility reference | a publication reporting a *physically valid* mobility curve for a specimen whose S, ρ and T are also published |
| 5.5 — three families without comparisons | a two-band transport model, an anisotropic data model, and an independent Lorenz measurement respectively — each is a *model addition*, outside the scope of a validation task |
| 6.1 — CI never run | one push with the workflow enabled |

---

## 8. Summary of the honest overall position

- The **calculation engine is verified** at the level of
  independent re-implementation and analytical limits, with agreement at
  1e-14 – 1e-6 — six to twelve orders of magnitude inside the physical
  uncertainties of the inputs.
- The **software is verified against published measurements** for four
  specimens, for the power factor and the figure of merit, to 1.3–5.9 %.
- The **physical models are not validated in general**; for the single
  specimen where the published data can arbitrate, they are *contradicted*
  by ≈35 % in the Lorenz number.
- **Six interactive GUI paths, the raw measurement chain, experimental
  validation of weighted mobility, and three of the seven material families
  remain outside the evidence.**
- **No metrological traceability** has been established.

A statement of the form *"Seebeck Prime is 100 % validated"* would be
false. The defensible statement is:

> Seebeck Prime's implemented scientific calculations have been
> independently re-derived and verified numerically, its unit handling and
> physical constraints have been systematically tested, and its core
> transport outputs reproduce four published specimens' power factors and
> figures of merit to within 1.3–5.9 %. Its physical models, its
> interactive GUI paths and its raw measurement chain remain outside the
> verified set.
