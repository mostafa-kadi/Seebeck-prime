# Audit — the weighted-mobility model

**Phase:** 3 (critical scientific corrections)
**Date:** 2026-11-12
**Reproduce:** `python tools/audit_weighted_mobility.py`
**Outcome:** the implementation is **numerically reproducible and
dimensionally consistent**, but it **does not implement the equation printed
in the project's own scientific model register**, and its shape factor
**diverges for small \|S\|**. Neither problem can be settled against a
measurement, because no experimental reference for μ_w exists. The
implementation was **not changed**; the documentation was corrected and the
divergence is recorded as an open finding.

---

## 1. What is implemented

`src/domain/transport.py::calculate_weighted_mobility`

μ_w = 331 · (1/ρ) · (T/300)^{−1.5} · shape( |S| / (k_B/e) )

shape(s) = exp(s−2)/(1+exp(−5(s−1))) + 3π² / ( s·(1+exp(5(s−1))) )

with

| Symbol | Unit |
|---|---|
| ρ | mΩ·cm |
| \|S\| | µV/K |
| T | K |
| μ_w | cm²/(V·s) |
| s = \|S\|/(k_B/e) | dimensionless |

## 2. What the model register documents

`docs/SCIENTIFIC_MODEL_REGISTER.md` §3.4 prints

μ_W = [3 h³ σ / (8 π e (2 m_e k_B T)^{3/2})] · [ B(s) ]^{−1}

B(s) = exp(s−2)/(1+exp(−5(s−1))) + (3/π²)·s

with σ in S/m and μ_W in m²/(V·s).

## 3. The two are not the same equation

### 3.1 The shape functions differ

| s | register bracket B(s) | implemented shape(s) | ratio |
|---|---|---|---|
| 0.5 | 0.168908 | 54.742411 | 324.10 |
| 1.0 | 0.487903 | 14.988346 | 30.72 |
| 1.5 | 1.016466 | 2.057901 | 2.02 |
| 1.7405 | 1.281919 | 1.162311 | 0.91 |
| 2.0 | 1.601234 | 1.092391 | 0.68 |
| 3.0 | 3.630049 | 2.718606 | 0.75 |
| 5.0 | 21.605355 | 20.085537 | 0.93 |

The first term of the two is identical
(exp(s−2)/(1+exp(−5(s−1))) = exp(6s−7)/(1+exp(5(s−1)))); the **second term
is different**: (3/π²)·s versus 3π²/(s·(1+exp(5(s−1)))). The bracket also
appears **inverted** in one form and **multiplied** in the other.

### 3.2 The prefactors differ

Expressed per (mΩ·cm)⁻¹ with (T/300)^{−1.5}, the register's prefactor
corresponds to **1 718 050 cm²/(V·s)**; the implementation uses **331.0**.
They are not related by the m²→cm² factor alone.

### 3.3 The resulting mobilities differ by 1.49 to 8.25

Over a representative grid (T = 300/600/900 K, ρ = 0.5/1/2 mΩ·cm,
|S| = 80/150/250 µV/K) the ratio implemented ÷ register runs from
**1.4915** to **8.2452** — and it is a function of |S| alone, not of T or ρ.

## 4. A separate, physical problem: the divergence at small |S|

The implemented second term contains `3π²/(s + 1e-9)`, so the shape factor
diverges as s → 0 and so does μ_w:

| s | \|S\| [µV/K] | μ_w [cm²/(V·s)], ρ = 1 mΩ·cm, T = 300 K |
|---|---|---|
| 0 | 0 | **9.735e+12** |
| 1e-6 | 8.6e-5 | 9.725e+09 |
| 0.01 | 0.86 | 9.732e+05 |
| 0.1 | 8.6 | 9.693e+04 |
| 0.5 | 43.1 | 1.812e+04 |
| 1.0 | 86.2 | 4.961e+03 |
| 1.74 | 149.9 | 3.850e+02 |
| 3.0 | 258.5 | 8.999e+02 |

Real thermoelectric mobilities are 1–1000 cm²/(V·s). The implementation
therefore returns values **four to ten orders of magnitude too large** for
small Seebeck coefficients, which is the regime of a good degenerate
conductor. The `+ 1e-9` guard in the denominator is clearly a
divide-by-zero guard, so the divergence is a known-effect of the expression
rather than a deliberate feature.

The register's bracket does **not** diverge: B(s) → 9.06e-4 as s → 0, so its
form stays finite.

## 5. Why the implementation was not changed

Three facts block a correction:

1. **No primary source is available in the repository.** The register cites
   Snyder et al. (2020), *Advanced Materials* **32**, 2001537, but the full
   text is not present, and the validation brief forbids fabricating or
   inferring a literature equation.
2. **No experimental reference exists.** The only published carrier-mobility
   curve in the benchmark set (Bi₂Te₂.₄Se₀.₆Cu₀.₀₀₆) is **negative** and
   therefore unusable. There is nothing to validate a change against.
3. **The change would be a physics change, not a bug fix.** The
   implementation is *self-consistent*: it agrees with the independently
   written reference in `validation/independent_calculations/references.py`
   to ≤1e-9 relative, it is pinned by the golden regression snapshot, and
   it satisfies the unit convention the application documents.

Adopting the register's equation on the strength of the register alone would
be **fitting the software to an internal document**, which is exactly the
error the previous validation programme was created to eliminate.

## 6. What was done instead

| Action | Detail |
|---|---|
| **The register was corrected** | `docs/SCIENTIFIC_MODEL_REGISTER.md` §3.4 now prints the equation the code actually implements, and states the divergence from the previously-printed form as an open item. |
| **The model's docstring was extended** | `src/domain/transport.py::calculate_weighted_mobility` now states the unit convention, the acoustic-scattering assumption, the small-\|S\| divergence and the absence of an experimental reference. |
| **A characterisation test was added** | `tests/scientific/test_weighted_mobility_audit.py` pins the unit convention, the scaling laws, the divergence, and the difference from the previously-documented form — so that any future change to the physics is a *deliberate, visible* act rather than a silent drift. |
| **The finding was recorded** | As an open item (D-12) in the limitations report and in the equation-status mapping. |

## 7. What would settle it

1. **The primary source.** Snyder et al. (2020), *Advanced Materials* **32**,
   2001537 — the published weighted-mobility expression, including the shape
   function's exact form. This single document decides which of the two
   expressions the implementation should follow.
2. **An experimental μ_w reference** for a specimen whose S, ρ and T are
   also published. Without one, even a corrected expression could not be
   validated — the same argument that blocks the Kane/Dingle model in
   `DEGENERATE_LORENZ_ASSESSMENT.md`.
3. **The small-\|S\| regime** must be specified by the source: whether μ_w
   should approach the ordinary mobility as S → 0, and how the expression is
   regularised there.

Until (1) and (2) exist, the weighted mobility is a **numerically verified
approximation with no experimental validation**, and the divergence between
the two published-in-project forms must remain visible.

## 8. The three statements that must not be made

| Statement | Status |
|---|---|
| "The weighted mobility is validated." | **False** — there is no usable experimental reference. |
| "The weighted mobility is the Hall mobility." | **False** — μ_w ≠ μ_H; they coincide only in the non-degenerate limit with m\* ≈ m_e. |
| "The weighted mobility implements the Snyder weighted-mobility expression." | **Not established** — it implements the expression described above; whether that is the published Snyder expression is an open item. |
