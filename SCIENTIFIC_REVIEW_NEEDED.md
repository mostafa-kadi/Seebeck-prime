# SCIENTIFIC_REVIEW_NEEDED.md
## Scientific Equations and Approximations Flagged for Review

**Date:** 2026-08-25  
**Version:** Seebeck Prime 0.2.0-dev

This document records empirical models, approximations, and domain assumptions currently in use across the codebase. Per the core design principles of Seebeck Prime, model approximations are never presented as experimental measurements and are cataloged here for ongoing scientific validation.

---

### 1. Empirical SPB Carrier Concentration Formula

- **Current Implementation:** `seebeck_prime.domain.models.spb.calculate_carrier_concentration`
- **Formula:** $n \approx A \cdot \exp(-|S| / B)$ with $A = 10^{21}\text{ cm}^{-3}$, $B = 43.4\ \mu\text{V/K}$.
- **Question:** While this provides an intuitive order-of-magnitude estimate for non-degenerate acoustic-phonon transport, it deviates for degenerate or bipolar regimes and cannot substitute for full Fermi–Dirac integral numerical inversion.
- **Reference Required:** 
  - Snyder, G. J. & Toberer, E. S. (2008). *Complex thermoelectric materials*. Nature Materials, 7, 105–114.
  - May, A. F. & Snyder, G. J. (2012). *Introduction to modeling thermoelectric properties of semiconductors*. In Materials, Preparation, and Characterization in Thermoelectrics (CRC Press).
- **Proposed Evolution / Alternatives:**
  - Introduce rigorous Fermi–Dirac integral solver $F_j(\eta) = \int_0^\infty \frac{x^j}{1 + e^{x-\eta}} dx$ with numerical root-finding for reduced Fermi level $\eta$.
  - Clearly label the current function output in the UI and exports as `Estimated (Empirical SPB)`.

---

### 2. Empirical SPB Lorenz Number Approximation

- **Current Implementation:** `seebeck_prime.domain.models.spb.estimate_lorenz`
- **Formula:** $L = \left(1.5 + \exp\left(-\frac{|S|}{116.0}\right)\right) \times 10^{-8}\ \text{W}\cdot\Omega/\text{K}^2$
- **Question:** Accurate to within ~5% for single parabolic band with acoustic phonon scattering ($r = -1/2$), but does not account for non-parabolic bands (Kane model), ionized impurity scattering ($r = 3/2$), or multiband transport.
- **Reference Required:**
  - Kim, H. S. et al. (2015). *Characterization of Lorenz number with Seebeck coefficient measurement*. APL Materials, 3, 041506.
- **Proposed Evolution / Alternatives:**
  - Retain Kim et al. (2015) as the default fast estimate.
  - Add optional full SPB numerical calculation of $L(\eta)$ alongside user-selectable scattering parameter $r$.

---

### 3. Temperature Grid Alignment for Multi-Instrument Merging

- **Current Implementation:** `src/core/error_propagation.py` (`process_four_probe`, `process_laser_flash`, `calculate_transport`)
- **Behavior:** Groups and matches four-probe and laser-flash data based on rounded temperature values (`round(1)` or `T/20` bins).
- **Question:** Experimental temperatures between Seebeck/resistivity systems and laser flash systems (LFA) rarely coincide exactly. Exact-match or binning can discard valid points or introduce binning-induced variance.
- **Proposed Evolution / Alternatives:**
  - Implement continuous polynomial / spline interpolation framework in the domain layer with explicit boundary reporting so users can see interpolated vs measured points.

---

### 4. Bipolar Thermal Conductivity Separation

- **Current Implementation:** `seebeck_prime.domain.calculations.thermal.calculate_kappa_l`
- **Formula:** $\kappa_L = \kappa_{\text{total}} - \kappa_e$
- **Question:** At elevated temperatures, bipolar thermal conductivity $\kappa_{bp}$ often arises ($\kappa_{\text{total}} = \kappa_L + \kappa_e + \kappa_{bp}$). Attributing all non-electronic thermal conductivity to $\kappa_L$ can lead to an apparent upturn in lattice thermal conductivity at high $T$.
- **Proposed Evolution / Alternatives:**
  - Flag high-temperature upturns in $\kappa_L(T)$ as potential bipolar conduction in the quality-control engine.
