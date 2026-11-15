# Investigation — the SiGe:P Lorenz-number discrepancy

**Phase:** 3 (critical scientific corrections)
**Date:** 2026-11-12
**Audit finding:** M-04
**Reproduce:** `python tools/investigate_sige_lorenz.py`
**Outcome:** the discrepancy is a **scattering-assumption** difference. It is
**not** an implementation error and **not** a failure of the single-parabolic-
band model. **The SPB model was not changed.**

---

## 1. The observation

For the benchmark specimen **Si₈₀Ge₂₀P₁** (`10.1021/acsami.9b20090`) the
published thermal conductivity, lattice thermal conductivity and electrical
conductivity imply a Lorenz number

L_implied = (κ − κ_L)/(σ·T) = **2.4579e-8 W·Ω/K²** (median over the grid)

while the application's embedded SPB **acoustic-phonon** model (λ = 0, the
default of the Seebeck-derived "auto" Lorenz mode) gives **1.592e-8** — a
**−35 %** disagreement.

The application's *constant* 2.44e-8 agrees with the published data to
**0.7 %** (on κ_L). The previous validation report recorded this as an
unresolved discrepancy.

## 2. The four candidate causes, and how each was tested

| # | Candidate cause | Test | Result |
|---|---|---|---|
| (a) | **Scattering assumption** | Evaluate the rigorous SPB Lorenz number for λ = 0, 1, 2 at the η implied by the *measured* Seebeck coefficient; then solve for the λ that reproduces the published value | **CONFIRMED — see §3** |
| (b) | Single-parabolic-band assumption fails | Characterise the degeneracy regime the specimen occupies | The specimen is in the **transitional** regime where the single-band model is *most* applicable; the failure is not a band-structure effect |
| (c) | The published κ/κ_L pair is not internally consistent | Spread of the implied L over the published grid | **Rejected** — the spread is 3.0 %, i.e. at the noise floor |
| (d) | The digitisation/reconstruction contributes the offset | Propagate a 1 % digitisation error on κ and κ_L into L | **Rejected** — the noise floor is 1.7 %, below the observed 3.0 % spread, so the pair is not noise-limited |

## 3. The measurement

### 3.1 The published pair is self-consistent (rejects (c) and (d))

| Quantity | Value |
|---|---|
| Implied L, median | 2.4579e-8 W·Ω/K² |
| Implied L, range | 2.4089e-8 … 2.4830e-8 |
| Relative spread | **3.0 %** |
| Digitisation noise floor (1 % on κ and κ_L) | 1.7 % |
| Sommerfeld L₀ = 2.443004509e-8 | differs from the median by **0.6 %** |
| Application default 2.44e-8 | differs from the median by **0.7 %** |

For comparison, the **PbTe** benchmark's published pair implies a Lorenz
number with a **25 %** spread — that one *is* internally inconsistent. The
SiGe:P pair is not.

### 3.2 The scattering exponent reproduces the published value (confirms (a))

Evaluating the rigorous SPB Lorenz number at the η implied by the *measured*
Seebeck coefficient:

| λ | Mechanism | L(η) median | vs the published value |
|---|---|---|---|
| **0.0** | acoustic deformation potential (**the application's default**) | 1.5920e-8 | **−35.2 %** |
| 1.0 | polar optical / alloy | 2.2381e-8 | −8.9 % |
| 2.0 | ionised impurity | 2.7317e-8 | +11.1 % |
| **1.41** | **solved: reproduces the published L exactly** | **2.4579e-8** | **+0.0 %** |
| — | Sommerfeld L₀ | 2.4430e-8 | −0.6 % |

**λ = 1.41 lies between alloy/optical scattering (λ = 1) and ionised-impurity
scattering (λ = 2)** — exactly what is expected for a **P-doped** SiGe alloy
at 300–1000 K, where phonon, alloy and ionised-impurity scattering all
contribute.

### 3.3 Why the scattering exponent matters so much here (rejects (b))

The specimen **crosses the classical-to-degenerate transition**:

| Quantity | Range over the published grid |
|---|---|
| η from the measured \|S\| (λ = 0) | −0.99 … +1.79 |
| F₁⁄₂(η) | 0.293 … 2.238 |
| Degenerate limit / classical limit | 0.765 / 0.443 |

In this regime the Lorenz number is strongly temperature- and
scattering-dependent, which is why a 35 % difference between the acoustic
model and the measurement is entirely plausible — and why the constant
Sommerfeld value happens to sit close to the published data.

## 4. Conclusion

> The published SiGe:P data are reproduced by the application's SPB model
> **with a scattering exponent of λ ≈ 1.41** instead of the acoustic default
> λ = 0. The SPB implementation is correct; the **default scattering
> assumption** is what does not hold for this specimen.

**No scientific model was changed.** Fitting λ to a single dataset would be
re-fitting the model to the measurement, which the validation brief forbids
and which would not generalise to other materials.

**What did change** is the *documentation*: the Seebeck-derived ("auto")
Lorenz mode, the rigorous SPB Lorenz number and the Kim empirical relation
now state that they are **acoustic-scattering approximations** and that they
can underestimate the Lorenz number by tens of per cent for alloys with
significant alloy or ionised-impurity scattering.

## 5. Consequence for the software's claims

| Claim | Before | After |
|---|---|---|
| The auto-Lorenz mode | "conditional on acoustic-phonon transport" | **conditional on acoustic-phonon transport; measured to underestimate the published Lorenz number by 35 % for a P-doped SiGe alloy, because that alloy's effective scattering exponent is ≈1.41** |
| The SPB acoustic model | "model-dependent" | **model-dependent; the acoustic default (λ = 0) is not appropriate for alloys whose scattering is dominated by alloy or ionised-impurity mechanisms** |
| The constant 2.44e-8 | "a rounded value" | unchanged; it agrees with the published SiGe:P data to 0.7 % |

## 6. The negative result that is preserved

The published data **contradict the acoustic-scattering assumption** that the
default Lorenz modes carry. That contradiction is retained, quantified, and
**not** removed by changing the model. The benchmark comparison in
`tests/experimental_benchmarks/test_auto_lorenz.py` continues to assert that
the SPB acoustic value disagrees with the published data by more than 25 %, so
a future change that quietly "fixed" the model would fail the suite.

## 7. What would settle the question further

- An independent measurement of the scattering exponent for the specimen
  (a mobility-vs-temperature fit with a stated mechanism), which would make
  λ a *measured* input rather than an assumption.
- The same analysis on the other three benchmark specimens (Bi₂Te₃, PbTe,
  SiGe:Sb), which would show whether the acoustic default is reasonable for
  the degenerate binary alloys.
- A published Lorenz number obtained independently (for example by a direct
  Wiedemann–Franz measurement rather than by differencing published κ and
  κ_L), which would remove the 3 % digitisation floor.
