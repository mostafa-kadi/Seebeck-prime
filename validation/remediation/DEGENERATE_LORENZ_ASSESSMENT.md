# Assessment — the degenerate-semiconductor Lorenz number (PbTe)

**Phase:** 3 (critical scientific corrections)
**Date:** 2026-11-12
**Audit finding:** M-04b / limitation 3.2.1
**Reproduce:** `python tools/assess_degenerate_lorenz.py`
and `python tools/lorenz_diagnostics.py`
**Decision:** **no model is implemented.** The mathematical requirements,
the literature basis, the required inputs and the available validation data
are documented below, and they show that a Kane/Dingle or multiband model
**cannot currently be validated**.

---

## 1. The correction that preceded this assessment

The shipped validation documents tabulated a **"130.6 %"** figure for the
PbTe specimen under the header *SPB deviation*. That number is real but it
measures a **different quantity**: it is the **κ_L sensitivity** — how much
the computed lattice thermal conductivity changes when the application-wide
constant L = 2.44e-8 is used instead of the Lorenz number implied by the
published data. It is large because κ_L is a small difference of two
comparable numbers.

The two quantities, computed for every specimen that publishes κ_L:

| Specimen | L implied | pair spread | **κ_L sensitivity** | **SPB deviation** (acoustic, λ = 0) |
|---|---|---|---|---|
| Si₈₀Ge₂₀P₁ | 2.4579e-8 | 3.0 % | 0.7 % | −37.7 % … −25.2 % (median −35 %) |
| Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆ | 1.6525e-8 | 3.4 % | 26.5 % | **−3.6 % … −1.5 %** |
| (PbTe)₀.₉₅(PbS)₀.₀₅ | 1.2765e-8 | 24.9 % | 130.6 % | +10.0 % … +46.0 % |

**This changes the scientific picture materially.** The SPB acoustic model
performs **well** on the Bi₂Te₃ specimen (≤3.6 % from the implied value);
it is 15–38 % low on P-doped SiGe (whose cause was identified in Phase 3 —
see `SIGE_LORENZ_INVESTIGATION.md`); and it is 10–46 % high on PbTe, where
the implied value is itself unreliable and **no model conclusion can be
drawn**.

## 2. The degeneracy regime of the PbTe specimen

| Quantity | Range over the published grid (299–862 K) |
|---|---|
| η from the measured \|S\| (λ = 0) | −0.04 … +1.32 (median 0.28) |
| F₁⁄₂(η) | 0.659 … 1.706 |
| Degenerate limit / classical limit | 0.765 / 0.443 |

The specimen **straddles** the classical-to-degenerate transition rather than
being strongly degenerate throughout. This matters for the assessment: the
parabolic-band dispersion is *not* obviously the dominant error term here,
so a Kane correction is not obviously the right remedy either.

## 3. What the published data can and cannot support

**The published κ/κ_L pair for this specimen is internally inconsistent:**
the implied Lorenz number has a **24.9 %** spread (1.1457e-8 … 1.4632e-8)
against a 1.7 % digitisation noise floor. A single Lorenz number cannot
reproduce both published curves. This is exactly why the PbTe κ_L benchmark
comparison is reported **UNVERIFIED** — the limit is in the source data, not
in the calculation.

**Consequently no model can be validated against this specimen**: there is
no reliable reference value for L to compare against.

## 4. What a corrected model would require

A Kane (non-parabolic dispersion) or Dingle (band-narrowing) correction
needs, at minimum:

| Requirement | Why | Available in the benchmark data? |
|---|---|---|
| Band-edge effective mass m_d\* | the Kane correction is parameterised by the band-edge mass | **no** |
| Band-edge Seebeck coefficient S₀ | sets the reference point of the non-parabolic transport integrals | **no** |
| Band gap Eg(T) | the dispersion and the carrier concentration both depend on it | **no** |
| A justified band-narrowing constant | the Dingle factor is not universal | **no** |
| An independent reference for the corrected L | without one, the corrected model is unfalsifiable | **no** |

Present in the data: S(T), σ(T), κ(T), κ_L(T). Absent: n_H, μ_H, m\*, E_g.

**Assessment: a Kane/Dingle model cannot be implemented *and validated*
with the available data.** Implementing one would produce a number with no
way to test it, which is worse than the documented limitation. The validation
brief explicitly forbids implementing such a model "merely to improve
agreement", and the requirement analysis independently shows the agreement
could not be demonstrated.

## 5. Decision

| Option | Assessment |
|---|---|
| Implement a Kane/Dingle/multiband model now | **Rejected** — no validation reference exists; the required inputs are absent; the brief forbids it |
| Re-fit the existing SPB model to the published PbTe value | **Rejected** — that is fitting the model to a measurement whose implied reference is internally inconsistent |
| Report the SPB acoustic value with its measured deviation and keep the comparison UNVERIFIED | **Adopted** |
| Document the regime and the required inputs | **Adopted** |

## 6. What would make it possible, in order of cost

1. **A published Hall carrier concentration and mobility** for the specimen,
   which fixes m_d\* empirically rather than by assumption.
2. **An independent measurement of L** for the specimen — not obtained by
   differencing published κ and κ_L, which is what makes the present pair
   inconsistent. A direct Wiedemann–Franz measurement, or a published
   electronic thermal conductivity, would remove the 24.9 % spread.
3. **The material's band gap over the measured range**, from which E_g(T)
   can be fitted.
4. **A second, internally consistent PbTe specimen**, so that the model
   could be tested on data whose reference value is trustworthy.

## 7. What the software states today

- The rigorous SPB Lorenz number is numerically verified against an
  independent transport-integral reference to **1.4e-14** and reproduces the
  analytic Sommerfeld and classical limits.
- Its **physical applicability** is conditional, and the measured deviations
  are now quoted correctly (§1): −3.6 % (Bi₂Te₃), −35 % median (P-doped
  SiGe, cause identified), +10 % … +46 % (PbTe, reference unreliable).
- The **κ_L sensitivity** to the Lorenz-number choice is documented
  separately, because it is the quantity that determines the reported κ_L and
  ZT: up to 26.5 % (Bi₂Te₃) and 130.6 % (PbTe).
- No model was changed, and no published value was re-fitted.
