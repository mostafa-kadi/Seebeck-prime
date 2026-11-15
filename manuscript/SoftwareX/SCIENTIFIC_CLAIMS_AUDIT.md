# Seebeck-Prime — Scientific Claims Audit (Stage 5 input)

**Document type:** Stage 5 deliverable of the SoftwareX manuscript preparation.
**Date:** 2026-11-12
**Status:** Audit draft.

---

## 1. Purpose

Audit every important scientific claim that may appear in the manuscript, and
record whether the local evidence supports it.

## 2. Claim register and evidence status

| # | Claim | Level | Evidence | Status |
|---|---|---|---|---|
| C1 | Power factor is computed as \(PF = S^2\sigma\). | Mathematical | Independent reference; 1e-12 rel. | **Supported** |
| C2 | Electronic thermal conductivity is \(\kappa_e = L\sigma T\). | Mathematical | Independent reference; 1e-12; Wiedemann–Franz context. | **Supported** |
| C3 | Lattice thermal conductivity is \(\kappa_L = \kappa - \kappa_e\). | Mathematical | Independent reference; 1e-12. | **Supported** |
| C4 | Figure of merit is \(ZT = PF\,T/\kappa\). | Mathematical | Independent reference; 1e-12; benchmarks. | **Supported** |
| C5 | Sommerfeld Lorenz number is \(L_0 = (\pi^2/3)(k_B/e)^2 = 2.443004509e-8\). | Mathematical | Independent; 3e-11. | **Supported** |
| C6 | Kim empirical Lorenz number is \(L(S) = (1.5+e^{-|S|/116})10^{-8}\). | Mathematical | Independent; 1e-12; conditional. | **Conditional** (acoustic approximation) |
| C7 | Rigorous SPB Lorenz number is implemented via Fermi-Dirac transport integrals. | Mathematical | Independent; 2e-14; limits. | **Supported** (single parabolic band) |
| C8 | SiGe:P published Lorenz number is ≈\(2.46e-8\), consistent with app constant \(2.44e-8\). | Experimental | Published data; median \(2.4579e-8\); 0.7% vs constant. | **Supported** (implied) |
| C9 | SPB acoustic Lorenz number is \(1.59e-8\), −35% from published SiGe:P value. | Experimental | Investigation; published data; −35%. | **Supported** (explained as scattering) |
| C10 | The −35% gap is a scattering-assumption matter, resolved via λ ≈ 1.41; model not refitted. | Interpretive | Investigation; 5 regression tests. | **Supported** (negative result preserved) |
| C11 | PbTe Lorenz comparison is **unverified** (source-data inconsistency, spread >20%). | Experimental | Benchmark; spread 24.9%. | **Supported** (unverified) |
| C12 | Weighted mobility is not experimentally validated; divergence from earlier internal formulation documented. | Scientific | Audit; tests; divergence. | **Supported** (documented) |
| C13 | Raw V/I → R → ρ → σ chain is **not implemented**. | Fact | Audit; registry E-58. | **Supported** |
| C14 | First-order uncertainty propagation assumes independent inputs; covariance propagation not implemented. | Fact | Audit; registry. | **Supported** |
| C15 | Full suite: 680 passed, 10 skipped (primary). | Empirical | Test run. | **Supported** |
| C16 | GUI automated coverage incomplete. | Fact | Audit; Phase 5 backlog. | **Supported** |

## 3. Claims that must NOT be made (per audit)

- "The software is fully validated." — **No** (models conditional; benchmarks scoped).
- "The weighted mobility is validated." — **No**.
- "The Lorenz number was measured experimentally." — **No** (implied from published κ/κL).
- "All models are physically valid." — **No**.
- "The V/I chain is implemented." — **No**.

## 4. Critical review summary (Stage 5)

Reviewer-style findings:

- **Major concerns:** none outstanding in the *science*; manuscript-level concerns
  remain (3000-word limit verification, software availability, licence).
- **Minor concerns:** figure captions/wording precision; benchmark error bars.
- **Missing evidence:** GUI screenshot; author identity; licence; distribution; full
  reference verification.
- **Unsupported claims:** none yet drafted, but must be re-checked at final assembly.
- **Required author decisions:** version, licence, distribution, author info,
  references, title, keywords, figure 2.
- **Recommended revisions:** tighten wording on conditional validation; add
  placeholders.

## 5. Conclusion of audit

All substantive scientific claims carry traceable evidence; the honest-boundary
claims (C11, C12, C13, C14) are correctly negative and must be preserved.

---

*End of scientific-claims audit draft.*
