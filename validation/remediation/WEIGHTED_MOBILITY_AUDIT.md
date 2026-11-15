# Audit and remediation — weighted mobility

**Status:** Corrected against the primary publication  
**Date:** 2026-11-15  
**Primary source:** Snyder et al., *Weighted Mobility*, Advanced Materials 32 (2020), 2001537. DOI: [10.1002/adma.202001537](https://doi.org/10.1002/adma.202001537).

## 1. Finding

The implementation in `src/domain/transport.py` did not match the published Snyder et al. expression. The second term had been implemented as

```python
(3 * pi**2 / s) / (1 + exp(5 * (s - 1)))
```

instead of

```python
((3 / pi**2) * s) / (1 + exp(5 * (s - 1)))
```

The incorrect term diverged as $s\to0$ and produced non-physical values at low Seebeck coefficients. The primary publisher page explicitly provides the correct equation and units; the previous claim that the primary source was unavailable is superseded.

## 2. Published expression

\[
\mu_w=331\frac{\mathrm{cm}^2}{\mathrm{V s}}
\left(\frac{\mathrm{m\Omega cm}}{\rho}\right)
\left(\frac{T}{300\,\mathrm K}\right)^{-3/2}
\left[
\frac{\exp(s-2)}{1+\exp[-5(s-1)]}
+
\frac{(3/\pi^2)s}{1+\exp[5(s-1)]}
\right]
\]

where $s=|S|/(k_B/e)$, $\rho$ is in mΩ·cm, $T$ is in K, and $S$ is in µV/K. Snyder et al. report $k_B/e=86.3$ µV/K; the application uses the CODATA-derived value (86.1733… µV/K), which is a documented precision choice.

## 3. Correction applied

- Replaced the incorrect second term with the published $(3/\pi^2)s$ term.
- Removed the artificial $+10^{-9}$ denominator regularisation; the published expression is finite at $S=0$.
- Evaluated logistic factors using `numpy.logaddexp` to avoid overflow for large reduced Seebeck values.
- Added broadcasting support and explicit NaN output for non-finite inputs, non-positive temperature, or non-positive resistivity.
- Preserved the established public function name and units.

## 4. Regression coverage

`tests/scientific/test_weighted_mobility_audit.py` independently transcribes the publisher equation and checks:
- Seebeck magnitudes of 50, 100, 150, 200 and 250 µV/K;
- invariance under the sign of Seebeck coefficient;
- inverse resistivity scaling and $T^{-3/2}$ scaling;
- finite behaviour at zero Seebeck coefficient;
- array broadcasting;
- NaN handling for invalid and non-finite inputs;
- distinction from Hall mobility.

These tests establish implementation parity with the published equation. They do **not** establish experimental validity for a material dataset.

## 5. Remaining limitation

The current benchmark collection does not contain a usable, physically valid published mobility curve for a specimen with matching $S$, $\rho$, and $T$. Therefore weighted mobility remains **experimentally unvalidated** in this repository. Do not describe it as Hall mobility or claim material-specific experimental validation.

## 6. Superseded conclusions

The following previous findings are withdrawn:
- that the primary Snyder source was unavailable;
- that the published expression diverged at low $|S|$;
- that the implemented second term should be preserved pending source confirmation;
- that the alternative expression in the earlier model register was a competing Snyder form.

The alternative expression with $3h^3\sigma/[8\pi e(2m_ek_BT)^{3/2}]$ and an inverted bracket is not the empirical equation published in Snyder et al. (2020) and must not be represented as such.
