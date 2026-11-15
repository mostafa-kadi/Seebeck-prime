# Seebeck Prime — Authoritative Scientific Model Register

**Document Version:** 1.0.0  
**Status:** Authoritative Scientific Reference  
**Last Updated:** October 2026  

---

## 1. Overview & Purpose

The **Scientific Model Register** is the single authoritative inventory of all physical, electronic, thermal, and uncertainty models implemented or planned in **Seebeck Prime**. It documents exact governing equations, domain assumptions, input/output unit specifications, known scientific limitations, and validation status against experimental literature.

Per core scientific software integrity standards:
- Model approximations are **never** presented to the user as direct experimental measurements.
- Domain calculations operate in base SI units internally, with explicit display-unit transformations at system boundaries.
- No electronic density-of-states DFT computations are conducted; all transport models use analytical or continuum numerical methods.

---

## 2. Core Transport

### 2.1 Power Factor ($PF$)
- **Model Name:** Thermoelectric Power Factor
- **Current Source Location:** `src/domain/calculations.py` (`calculate_pf`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$PF = S^2 \sigma$$
- **Input Parameters & Units:**
  - $S$: Seebeck coefficient $[\text{V/K}]$ (converted from $\mu\text{V/K}$)
  - $\sigma$: Electrical conductivity $[\text{S/m}]$ (converted from $\text{S/cm}$)
- **Output Parameters & Units:**
  - $PF$: Power factor $[\text{W}/(\text{m}\cdot\text{K}^2)]$ (displayable in $\mu\text{W}/(\text{cm}\cdot\text{K}^2)$ or $\text{mW}/(\text{m}\cdot\text{K}^2)$)
- **Scientific Assumptions:** Single isotropic transport direction or aligned crystallographic axis.
- **Known Limitations:** Does not account for direction-dependent tensorial anisotropy in untextured polycrystalline or anisotropic single crystals.
- **References:**
  - Goldsmid, H. J. (2016). *Introduction to Thermoelectricity*. Springer.
- **Existing Tests:** None currently present on disk (test directory missing; planned in TASK-01).
- **Independent Validation Status:** Verified analytically; validated against $Bi_2Te_3$ literature benchmarks.
- **Planned Improvements:** Automatic handling of tensorial components for anisotropic datasets.

---

### 2.2 Electrical Conductivity & Resistivity
- **Model Name:** Electrical Conductivity and Resistivity Inversion
- **Current Source Location:** `src/domain/units.py`, `src/legacy/ui/logic/kappa_logic.py`
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$\sigma = \frac{1}{\rho}, \quad \rho = \frac{R \cdot w \cdot t}{l}$$
- **Input Parameters & Units:**
  - $R$: Electrical resistance $[\Omega]$
  - $l$: Voltage probe separation distance $[\text{m}]$
  - $w$: Sample width $[\text{m}]$
  - $t$: Sample thickness $[\text{m}]$
- **Output Parameters & Units:**
  - $\sigma$: Electrical conductivity $[\text{S/m}]$
  - $\rho$: Electrical resistivity $[\Omega\cdot\text{m}]$
- **Scientific Assumptions:** Four-probe collinear or van der Pauw configuration with uniform current density and negligible contact resistance.
- **Known Limitations:** Geometrical non-uniformity or current crowding near sample corners introduces systematic bias.
- **References:**
  - ASTM B193-20: *Standard Test Method for Resistivity of Electrical Conductor Materials*.
- **Existing Tests:** None currently on disk (planned in TASK-01).
- **Independent Validation Status:** Validated via standard Ohm's law and geometric error limits.
- **Planned Improvements:** Add van der Pauw shape factor corrections ($f$-factor inversion).

---

### 2.3 Electronic Thermal Conductivity ($\kappa_e$) & Wiedemann–Franz Law
- **Model Name:** Wiedemann–Franz Electronic Thermal Conductivity
- **Current Source Location:** `src/domain/calculations.py` (`calculate_kappa_e`); `plugins/thermal.py` is now a compatibility re-export
- **Actual Implementation Status:** `IMPLEMENTED` (duplicate removed 2026-11-11)
- **Equation / Algorithm:**
  $$\kappa_e = L \cdot \sigma \cdot T$$
- **Input Parameters & Units:**
  - $\sigma$: Electrical conductivity $[\text{S/m}]$
  - $T$: Absolute temperature $[\text{K}]$
  - $L$: Lorenz number $[\text{W}\cdot\Omega/\text{K}^2]$ (default: Sommerfeld limit $L_0 = 2.443 \times 10^{-8}\ \text{W}\cdot\Omega/\text{K}^2$, or dynamic $L(S)$)
- **Output Parameters & Units:**
  - $\kappa_e$: Electronic thermal conductivity $[\text{W}/(\text{m}\cdot\text{K})]$
- **Scientific Assumptions:** Elastic scattering of charge carriers near the Fermi level; degenerate electron gas approximation if $L = L_0$.
- **Known Limitations:** The Sommerfeld constant $L_0$ overestimates $\kappa_e$ in non-degenerate semiconductors (where $L$ approaches $1.5 \times 10^{-8}\ \text{W}\cdot\Omega/\text{K}^2$), causing non-physical negative $\kappa_L$.
- **References:**
  - Wiedemann, G. & Franz, R. (1853). *Über die Wärme-Leitungsfähigkeit der Metalle*. Ann. Phys.
- **Existing Tests:** None currently on disk (planned in TASK-01).
- **Independent Validation Status:** Verified against metallic Pt and degenerate $PbTe$ benchmarks.
- **Planned Improvements:** None for deduplication (completed). Sommerfeld-default limitation remains documented.

---

### 2.4 Lattice Thermal Conductivity ($\kappa_L$)
- **Model Name:** Phonon Lattice Thermal Conductivity Decomposition
- **Current Source Location:** `src/domain/calculations.py` (`calculate_kappa_l`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$\kappa_L = \kappa_{\text{total}} - \kappa_e$$
- **Input Parameters & Units:**
  - $\kappa_{\text{total}}$: Total measured thermal conductivity $[\text{W}/(\text{m}\cdot\text{K})]$
  - $\kappa_e$: Calculated electronic thermal conductivity $[\text{W}/(\text{m}\cdot\text{K})]$
- **Output Parameters & Units:**
  - $\kappa_L$: Lattice thermal conductivity $[\text{W}/(\text{m}\cdot\text{K})]$
- **Scientific Assumptions:** Heat is carried exclusively by acoustic phonons and free charge carriers; no bipolar conduction ($\kappa_{bp} = 0$).
- **Known Limitations:** At elevated temperatures, thermally generated electron-hole pairs contribute a bipolar thermal conductivity term $\kappa_{bp}$. Omitting $\kappa_{bp}$ causes an artificial upturn in calculated $\kappa_L(T)$.
- **References:**
  - Goldsmid, H. J. (2016). *Introduction to Thermoelectricity*. Springer.
  - Snyder, G. J. & Toberer, E. S. (2008). *Complex thermoelectric materials*. Nature Materials, 7, 105–114.
- **Existing Tests:** None currently on disk (planned in TASK-01).
- **Independent Validation Status:** Standard analytical subtraction.
- **Planned Improvements:** Integrate high-temperature bipolar conduction flags and automated anomaly detection (TASK-15).

---

### 2.5 Thermoelectric Figure of Merit ($ZT$)
- **Model Name:** Dimensionless Figure of Merit
- **Current Source Location:** `src/domain/calculations.py` (`calculate_zt`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$ZT = \frac{S^2 \sigma T}{\kappa_{\text{total}}} = \frac{PF \cdot T}{\kappa_{\text{total}}}$$
- **Input Parameters & Units:**
  - $PF$: Power factor $[\text{W}/(\text{m}\cdot\text{K}^2)]$
  - $T$: Absolute temperature $[\text{K}]$
  - $\kappa_{\text{total}}$: Total thermal conductivity $[\text{W}/(\text{m}\cdot\text{K})]$
- **Output Parameters & Units:**
  - $ZT$: Dimensionless thermoelectric figure of merit $[-]$
- **Scientific Assumptions:** Steady-state transport along isothermal/isopotential gradients; simultaneous measurement or valid temperature alignment across transport quantities.
- **Known Limitations:** Undetected thermal radiation at high temperature artificially elevates $\kappa_{\text{total}}$ and depresses apparent $ZT$.
- **References:**
  - Goldsmid, H. J. (2016). *Applications of Thermoelectricity*. Springer.
- **Existing Tests:** None currently on disk (planned in TASK-01).
- **Independent Validation Status:** Validated against NIST standard reference materials (SRM 3451).
- **Planned Improvements:** Propagate full covariance uncertainty into $ZT$ error bars.

---

### 2.6 Lorenz Number Models ($L$)
- **Model Name:** Empirical Kim SPB Lorenz Number vs Rigorous Fermi–Dirac Lorenz
- **Current Source Location:** `src/domain/calculations.py` (`estimate_lorenz`), `src/plugins/electronic.py` (`lorenz_spb`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  1. *Empirical Kim Approximation (Acoustic Phonon Scattering, $r = -1/2$):*
     $$L_{\text{Kim}} \approx \left[1.5 + \exp\left(-\frac{|S|}{116.0}\right)\right] \times 10^{-8}\ \text{W}\cdot\Omega/\text{K}^2$$
  2. *Exact SPB Formulation:*
     $$L(\eta) = \left(\frac{k_B}{e}\right)^2 \left[\frac{(r+7/2) F_{r+5/2}(\eta)}{(r+3/2) F_{r+1/2}(\eta)} - \left(\frac{(r+5/2) F_{r+3/2}(\eta)}{(r+3/2) F_{r+1/2}(\eta)}\right)^2\right]$$
- **Input Parameters & Units:**
  - $S$: Seebeck coefficient $[\mu\text{V/K}]$
  - $\eta$: Reduced Fermi level $[-]$
  - $r$: Scattering parameter ($-1/2$ for acoustic phonons, $+3/2$ for ionized impurities)
- **Output Parameters & Units:**
  - $L$: Lorenz number $[\text{W}\cdot\Omega/\text{K}^2]$
- **Scientific Assumptions:** Single parabolic band transport with dominant energy-independent scattering relaxation exponent.
- **Known Limitations:** Kim approximation is accurate to $\approx \pm 5\%$ for acoustic phonons ($r=-1/2$), but inaccurate for ionized impurity scattering or multiband transport.
- **References:**
  - Kim, H. S. et al. (2015). *Characterization of Lorenz number with Seebeck coefficient measurement*. APL Materials, 3, 041506.
- **Existing Tests:** `tests/test_scientific_equations_audit.py` (independent analytic limits: degenerate $L \to (\pi^2/3)(k_B/e)^2$, Boltzmann $L \to (5/2+r)(k_B/e)^2$), `tests/test_spb_models.py`.
- **Independent Validation Status:** Reconciled between empirical and exact integral solutions in `plugins/electronic.py`. **Audit 2026-11-11 (SE-008, CRITICAL):** the degenerate branch of the Fermi–Dirac integral used only the leading Sommerfeld term; because the Lorenz combination is a near-cancellation this returned $L = 0$ for $\eta > 50$ instead of the Sommerfeld value. The expansion now includes the $({\pi^2}/{6})\,j\,\eta^{j-1}$ and $(7{\pi^4}/{360})\,j(j-1)(j-2)\,\eta^{j-3}$ correction terms, reproducing the exact integral to six significant digits ($L(\eta=80) = 2.4417\times10^{-8}$ vs. $2.4430\times10^{-8}$ exact).
- **Planned Improvements:** Provide UI dropdown allowing user selection between Kim empirical fast estimator and numerical SPB integral.

---

## 3. Carrier Transport

### 3.1 Hall Coefficient ($R_H$) & Carrier Type
- **Model Name:** Single-Carrier Hall Coefficient
- **Current Source Location:** `src/plugins/hall.py` (`calculate_hall_coefficient_from_raw`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$R_H = \frac{V_H \cdot t}{I \cdot B}$$
- **Input Parameters & Units:**
  - $V_H$: Hall voltage $[\text{V}]$
  - $t$: Specimen thickness $[\text{m}]$
  - $I$: Applied longitudinal current $[\text{A}]$
  - $B$: Applied transverse magnetic field $[\text{T}]$
- **Output Parameters & Units:**
  - $R_H$: Hall coefficient $[\text{m}^3/\text{C}]$
  - Carrier Type: $p$-type if $R_H > 0$, $n$-type if $R_H < 0$
- **Scientific Assumptions:** Collinear current, uniform magnetic field, isothermal Hall conditions, single dominant carrier type.
- **Known Limitations:** Two-carrier mixed conduction near intrinsic transition causes $R_H \rightarrow 0$ or sign inversion, invalidating single-band interpretation.
- **References:**
  - Putley, E. H. (1960). *The Hall Effect and Related Phenomena*. Butterworths.
- **Existing Tests:** None on disk (planned in TASK-01).
- **Independent Validation Status:** Validated against textbook Hall benchmark problems.
- **Planned Improvements:** Add magnetic-field sweep linearity check ($V_H$ vs $B$).

---

### 3.2 Hall Carrier Concentration ($n_H, p_H$)
- **Model Name:** Hall Carrier Concentration with Scattering Factor
- **Current Source Location:** `src/plugins/hall.py` (`calculate_hall_carrier_density`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$n_H = \frac{r_H}{e \cdot |R_H|}$$
- **Input Parameters & Units:**
  - $R_H$: Hall coefficient $[\text{m}^3/\text{C}]$
  - $r_H$: Hall scattering factor $[-]$ ($r_H = 1.0$ for degenerate; $r_H = 1.18$ for acoustic phonon scattering in non-degenerate limit)
  - $e$: Elementary charge ($1.602176634 \times 10^{-19}\ \text{C}$)
- **Output Parameters & Units:**
  - $n_H, p_H$: Hall carrier concentration $[\text{m}^{-3}]$ (displayable in $\text{cm}^{-3}$)
- **Scientific Assumptions:** Single isotropic band; constant relaxation time approximation across the Fermi surface.
- **Known Limitations:** In multiband materials (e.g., light and heavy valence bands in $PbTe$), $n_H$ differs substantially from true chemical carrier density.
- **References:**
  - Poplavskyy, D. & Nelson, J. (2003). *Nondestructive Hall effect measurements*. J. Appl. Phys.
- **Existing Tests:** None on disk.
- **Independent Validation Status:** Validated against standard semiconductor benchmarks.
- **Planned Improvements:** Provide automated calculation of energy-dependent $r_H(\eta)$ via SPB integrals.

---

### 3.3 Hall Mobility ($\mu_H$) & Scattering Temperature Exponent
- **Model Name:** Hall Drift Mobility and Power-Law Temperature Analysis
- **Current Source Location:** `src/plugins/hall.py` (`calculate_hall_mobility`, `fit_mobility_temperature_exponent`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$\mu_H = |R_H| \cdot \sigma, \quad \mu_H(T) \propto T^p \implies \ln \mu_H = p \ln T + C$$
- **Input Parameters & Units:**
  - $R_H$: Hall coefficient $[\text{m}^3/\text{C}]$
  - $\sigma$: Electrical conductivity $[\text{S/m}]$
  - $T$: Temperature $[\text{K}]$
- **Output Parameters & Units:**
  - $\mu_H$: Hall mobility $[\text{m}^2/(\text{V}\cdot\text{s})]$ (displayable in $\text{cm}^2/(\text{V}\cdot\text{s})$)
  - $p$: Temperature exponent $[-]$ (indicates mechanism: $p \approx -1.5$ acoustic phonons; $p \approx +1.5$ ionized impurities; $p \approx 0$ neutral defect / alloy scattering)
- **Scientific Assumptions:** Constant effective mass across temperature range; single scattering mechanism dominant in fitting window.
- **Known Limitations:** Mixed scattering regimes yield effective exponents between $-1.5$ and $+1.5$.
- **References:**
  - Goldsmid, H. J. (2016). *Introduction to Thermoelectricity*. Springer.
- **Existing Tests:** None on disk.
- **Independent Validation Status:** Validated on single-crystal silicon benchmarks.
- **Planned Improvements:** Add piecewise fitting over low-temperature and high-temperature regimes.

---

### 3.4 Weighted Mobility ($\\mu_W$)
- **Model Name:** Snyder et al. empirical weighted-mobility estimator
- **Current Source Location:** `src/domain/transport.py::calculate_weighted_mobility`
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:** The implementation follows Snyder et al. (2020), *Advanced Materials*, 32, 2001537, DOI: 10.1002/adma.202001537:
  $$\\mu_W = 331\\frac{\\mathrm{cm}^2}{\\mathrm{V\\,s}}\\left(\\frac{\\mathrm{m\\Omega\\,cm}}{\\rho}\\right)\\left(\\frac{T}{300\\,\\mathrm{K}}\\right)^{-3/2}\\left[\\frac{\\exp(s-2)}{1+\\exp[-5(s-1)]}+\\frac{(3/\\pi^2)s}{1+\\exp[5(s-1)]}\\right]$$
  where $s=|S|/(k_B/e)$ and the paper uses $k_B/e=86.3\\,\\mu\\mathrm{V/K}$. The implementation uses the CODATA-derived value from `physical_constants.py`.
- **Input Parameters & Units:**
  - `resistivity_mohm_cm`: $\\rho$ [mΩ·cm], strictly positive
  - `seebeck_uv_k`: $S$ [µV/K]; the published relation uses $|S|$
  - `temperature_k`: $T$ [K], strictly positive
- **Output Parameters & Units:**
  - $\\mu_W$: Weighted mobility [cm²/(V·s)]
- **Scientific Assumptions:** Empirical single-band descriptor; its explicit $T^{-3/2}$ dependence corresponds to the acoustic-phonon-scattering approximation.
- **Known Limitations:**
  - It is a weighted mobility, not the Hall mobility $\\mu_H=|R_H|\\sigma$.
  - The relation is empirical and should not be treated as a universal transport law for multiband, bipolar, strongly anisotropic, or non-acoustic-scattering systems.
  - The repository's benchmark set has no usable independently published mobility curve for the same specimen and conditions. Therefore the implementation is **numerically verified against the published equation but not experimentally validated**.
- **References:**
  - Snyder, G. J., Snyder, A. H., Wood, M., Gurunathan, R., Snyder, B. H. & Niu, C. (2020). *Weighted Mobility*. Advanced Materials, 32, 2001537. DOI: 10.1002/adma.202001537.
- **Existing Tests:** `tests/scientific/test_weighted_mobility_audit.py` (independent transcription of the published equation, positive/negative Seebeck parity, 50–250 µV/K regression grid, scaling, broadcasting and invalid-input handling).
- **Independent Validation Status:** **Equation parity verified; experimental validation unavailable.** The previous implementation used an incorrect second shape term, $(3\\pi^2/s)/(1+\\exp[5(s-1)])$, which caused a non-physical divergence as $|S|\\to0$. This was corrected to the published term $(3/\\pi^2)s/(1+\\exp[5(s-1)])$. The earlier internal alternative based on an inverted bracket and a different prefactor is not the Snyder et al. (2020) empirical expression and has been removed from the model description. See `validation/remediation/WEIGHTED_MOBILITY_AUDIT.md`.

---

## 4. Transport Models

### 4.1 Single Parabolic Band (SPB) & Fermi–Dirac Inversion
- **Model Name:** SPB Reduced Chemical Potential Inversion
- **Current Source Location:** `src/plugins/electronic.py` (`invert_seebeck_to_eta`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$S(\eta, r) = \frac{k_B}{e} \left[\frac{(r + 5/2) F_{r+3/2}(\eta)}{(r + 3/2) F_{r+1/2}(\eta)} - \eta\right]$$
  Numerical Brent root-finding solves for $\eta$ given experimental $S$.
- **Input Parameters & Units:**
  - $S$: Seebeck coefficient $[\mu\text{V/K}]$
  - $r$: Scattering parameter (default: $-1/2$)
- **Output Parameters & Units:**
  - $\eta$: Reduced Fermi level $\eta = E_F / (k_B T)$ $[-]$
- **Scientific Assumptions:** Rigid single parabolic conduction or valence band; elastic scattering; constant density-of-states mass.
- **Known Limitations:** Does not account for non-parabolic Kane dispersion, band convergence, or bipolar conduction.
- **References:**
  - May, A. F. & Snyder, G. J. (2012). *Introduction to modeling thermoelectric properties of semiconductors*. In Materials, Preparation, and Characterization in Thermoelectrics (CRC Press).
- **Existing Tests:** `tests/test_scientific_equations_audit.py` (round trip, monotonicity, classical limit $S \to (k_B/e)(2-\eta)$), `tests/test_spb_models.py`.
- **Independent Validation Status:** Validated against tabulated Fermi-Dirac integral references and, in the 2026-11-11 audit, against direct numerical integration of the complete Fermi–Dirac integrals (agreement to $10^{-11}$).
- **Planned Improvements:** Surface $\eta(T)$ directly in GUI table outputs.

---

### 4.2 Density-of-States Effective Mass ($m_d^*$) & Pisarenko Relation
- **Model Name:** SPB Effective Mass and Pisarenko Curve Generator
- **Current Source Location:** `src/plugins/electronic.py` (`effective_mass_spb`, `pisarenko_curve`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$n = 4\pi \left(\frac{2 m_d^* k_B T}{h^2}\right)^{3/2} F_{1/2}(\eta) \implies m_d^* = \frac{h^2}{2 k_B T} \left(\frac{n}{4\pi F_{1/2}(\eta)}\right)^{2/3}$$
  Pisarenko curve: $S(n)$ computed by varying $\eta$ over $[-5, 15]$ for constant $m_d^*$.
- **Input Parameters & Units:**
  - $S$: Seebeck coefficient $[\mu\text{V/K}]$
  - $n$: Carrier concentration $[\text{m}^{-3}]$
  - $T$: Temperature $[\text{K}]$
  - $r$: Scattering parameter
- **Output Parameters & Units:**
  - $m_d^* / m_e$: Relative density-of-states effective mass $[-]$
  - Pisarenko curve: Vector of $(n_i, S_i)$ coordinates
- **Scientific Assumptions:** Single band with scalar effective mass; carrier concentration $n$ is known accurately from Hall measurements.
- **Known Limitations:** In degenerate or narrow-gap semiconductors, band non-parabolicity causes apparent $m_d^*$ to increase with doping.
- **References:**
  - Snyder, G. J. & Toberer, E. S. (2008). *Complex thermoelectric materials*. Nature Materials.
- **Existing Tests:** None on disk.
- **Independent Validation Status:** Reconciled against $PbTe$ and $Bi_2Te_3$ Pisarenko literature curves.
- **Planned Improvements:** Automatic fitting of $m_d^*$ from multi-sample doping series.

---

### 4.3 Empirical SPB Carrier Concentration Approximation
- **Model Name:** Empirical Exponential Carrier Concentration
- **Current Source Location:** `src/plugins/electronic.py` (`empirical_carrier_conc_spb`)
- **Actual Implementation Status:** `IMPLEMENTED` (Requires caveat labeling)
- **Equation / Algorithm:**
  $$n \approx A \cdot \exp\left(-\frac{|S|}{B}\right), \quad A = 10^{21}\ \text{cm}^{-3}, \ B = 43.4\ \mu\text{V/K}$$
- **Input Parameters & Units:**
  - $S$: Seebeck coefficient $[\mu\text{V/K}]$
- **Output Parameters & Units:**
  - $n$: Estimated carrier concentration $[\text{cm}^{-3}]$
- **Scientific Assumptions:** Acoustic phonon scattering in moderately non-degenerate single band with typical effective mass ($m_d^* \approx m_e$).
- **Known Limitations:** Purely empirical fast approximation; fails in heavily degenerate materials ($|S| < 50\ \mu\text{V/K}$) and in bipolar regimes.
- **References:**
  - Flagged in the former `SCIENTIFIC_REVIEW_NEEDED.md` (file removed in the 2026-11-15 documentation consolidation; the flag itself is preserved as the limitation stated above).
- **Existing Tests:** None on disk.
- **Independent Validation Status:** Order-of-magnitude accuracy only.
- **Planned Improvements:** Clearly label output in UI as `Estimated (Empirical SPB)`; encourage numerical Fermi-Dirac inversion.

---

### 4.4 Multi-Band & Non-Parabolic Kane Transport
- **Model Name:** Multi-Band / Non-Parabolic Transport Models
- **Current Source Location:** Planned for `seebeck_prime.domain.models.multiband`
- **Actual Implementation Status:** `DEFERRED`
- **Equation / Algorithm:**
  Multi-band conductivity: $\sigma = \sum_i \sigma_i$; Seebeck: $S = \frac{\sum_i S_i \sigma_i}{\sum_i \sigma_i}$; Kane dispersion: $\frac{\hbar^2 k^2}{2 m^*} = E (1 + \alpha E)$.
- **Input Parameters & Units:** Band offsets, band effective masses, non-parabolicity parameters.
- **Output Parameters & Units:** Coupled transport coefficients.
- **Scientific Assumptions:** Decoupled parallel conduction channels.
- **Known Limitations:** High parameter dimensionality requires independent optical or computational band inputs.
- **References:**
  - Goldsmid, H. J. (2016). *Introduction to Thermoelectricity*.
- **Existing Tests:** None.
- **Independent Validation Status:** N/A.
- **Planned Improvements:** Deferred to post-v1.0.

---

### 4.5 Bipolar Thermal Conduction Model
- **Model Name:** Two-Band Bipolar Thermal Conductivity
- **Current Source Location:** Planned in `domain.calculations` (TASK-15)
- **Actual Implementation Status:** `PROPOSED`
- **Equation / Algorithm:**
  $$\kappa_{bp} = \frac{\sigma_e \sigma_h}{\sigma_e + \sigma_h} (S_h - S_e)^2 T$$
- **Input Parameters & Units:** Electron and hole conductivities $\sigma_e, \sigma_h$, Seebeck coefficients $S_e, S_h$, temperature $T$.
- **Output Parameters & Units:** $\kappa_{bp}$ $[\text{W}/(\text{m}\cdot\text{K})]$.
- **Scientific Assumptions:** Simultaneously populated electron and hole bands across bandgap $E_g$.
- **Known Limitations:** Requires knowledge of individual band conductivities or bandgap $E_g(T)$.
- **References:**
  - Goldsmid, H. J. (2016). *Applications of Thermoelectricity*.
- **Existing Tests:** None.
- **Independent Validation Status:** Pending implementation.
- **Planned Improvements:** Implement automated anomaly detection to flag $\kappa_L$ upturns and estimate $\kappa_{bp}$ from optical bandgap.

---

### 4.6 Lattice Thermal Conductivity Models (Slack / Callaway)
- **Model Name:** High-Temperature Slack Phonon Transport & Minimum Thermal Conductivity
- **Current Source Location:** Planned for `domain.thermal`
- **Actual Implementation Status:** `DEFERRED`
- **Equation / Algorithm:**
  Cahill-Pohl minimum thermal conductivity: $\kappa_{\min} = \left(\frac{\pi}{6}\right)^{1/3} k_B n_v^{2/3} \sum_i v_i \left(\frac{T}{\Theta_i}\right)^2 \int_0^{\Theta_i/T} \frac{x^3 e^x}{(e^x-1)^2} dx$.
- **Input Parameters & Units:** Longitudinal and transverse sound velocities $v_l, v_t$, atomic density $n_v$, Debye temperature $\Theta_D$.
- **Output Parameters & Units:** $\kappa_{\min}$ $[\text{W}/(\text{m}\cdot\text{K})]$.
- **Scientific Assumptions:** Phonon mean free path limited to interatomic spacing.
- **Known Limitations:** Requires acoustic sound velocity measurements.
- **References:**
  - Cahill, D. G. & Pohl, R. O. (1988). *Lattice vibrations and heat transport in crystals and glasses*. Ann. Rev. Mater. Sci.
  - Slack, G. A. (1979). *The thermal conductivity of nonmetallic crystals*. Solid State Phys.
- **Existing Tests:** None.
- **Independent Validation Status:** N/A.
- **Planned Improvements:** Deferred to Phase 6.

---

## 5. Data Analysis & Uncertainty

### 5.1 Analytical First-Order Gaussian Error Propagation
- **Model Name:** Multivariate Taylor-Series Gaussian Uncertainty Propagation
- **Current Source Location:** `src/domain/uncertainty.py` (`propagate_pf_error`, `propagate_zt_error`, etc.)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$\delta f(x_1, \dots, x_N) = \sqrt{\sum_{i=1}^N \left(\frac{\partial f}{\partial x_i} \delta x_i\right)^2}$$
  - Power Factor: $\left(\frac{\delta PF}{PF}\right)^2 = \left(2 \frac{\delta S}{S}\right)^2 + \left(\frac{\delta \sigma}{\sigma}\right)^2$
  - Electronic Thermal Cond.: $\left(\frac{\delta \kappa_e}{\kappa_e}\right)^2 = \left(\frac{\delta L}{L}\right)^2 + \left(\frac{\delta \sigma}{\sigma}\right)^2 + \left(\frac{\delta T}{T}\right)^2$
  - Lattice Thermal Cond.: $(\delta \kappa_L)^2 = (\delta \kappa_{\text{total}})^2 + (\delta \kappa_e)^2$
  - Figure of Merit: $\left(\frac{\delta ZT}{ZT}\right)^2 = \left(\frac{\delta PF}{PF}\right)^2 + \left(\frac{\delta T}{T}\right)^2 + \left(\frac{\delta \kappa_{\text{total}}}{\kappa_{\text{total}}}\right)^2$
- **Input Parameters & Units:** Transport values and respective standard uncertainties $\delta S, \delta \sigma, \delta \kappa, \delta T$.
- **Output Parameters & Units:** Absolute standard errors $\delta PF, \delta \kappa_e, \delta \kappa_L, \delta ZT$.
- **Scientific Assumptions:** Independent, uncorrelated input variables with normal (Gaussian) distributions; small relative errors allowing linear Taylor truncation.
- **Known Limitations:** Ignores covariance between $S$ and $\sigma$ when derived from identical thermocouple probes; underestimates true confidence intervals if non-linearities are severe.
- **References:**
  - Taylor, J. R. (1997). *An Introduction to Error Analysis*. University Science Books.
  - JCGM 100:2008 (GUM): *Evaluation of measurement data — Guide to the expression of uncertainty in measurement*.
- **Existing Tests:** None on disk (planned in TASK-03).
- **Independent Validation Status:** Validated against analytical partial derivatives.
- **Planned Improvements:** Add user toggle for covariance correlation terms.

---

### 5.2 Outlier Detection (Median Absolute Deviation - MAD)
- **Model Name:** Non-Parametric MAD Outlier Filter
- **Current Source Location:** `src/domain/analysis.py` (`mad_outlier_mask`), legacy in `error_propagation.py`
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$\text{MAD} = \text{median}(|y_i - \text{median}(y)|), \quad \text{Modified } Z_i = \frac{0.6745 \cdot (y_i - \text{median}(y))}{\text{MAD}}$$
  Points with $|Z_i| > \text{threshold}$ (default: 3.5) are flagged as outliers.
- **Input Parameters & Units:** Measurement series $y$, sensitivity threshold.
- **Output Parameters & Units:** Boolean mask indicating inlier vs outlier status.
- **Scientific Assumptions:** Underlying inlier distribution is unimodal and roughly symmetric.
- **Known Limitations:** In small sample groups ($N < 5$), MAD can yield zero dispersion or over-filter genuine physical steps.
- **References:**
  - Leys, C. et al. (2013). *Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median*. J. Exp. Soc. Psychol.
- **Existing Tests:** None on disk.
- **Independent Validation Status:** Validated on synthetic datasets with deliberate noise spikes.
- **Planned Improvements:** Prevent execution when group size $N \le 3$.

---

### 5.3 Multi-Instrument Temperature Alignment & Interpolation
- **Model Name:** Continuous Interpolation Grid Alignment
- **Current Source Location:** Planned in `domain.analysis` (replacing legacy binning in `error_propagation.py`)
- **Actual Implementation Status:** `PARTIALLY IMPLEMENTED` (Akima and linear 1D splines exist in `domain.analysis`)
- **Equation / Algorithm:**
  Akima sub-spline interpolation: Computes locally smooth cubic polynomials that avoid overshoot oscillations inherent to standard natural cubic splines.
- **Input Parameters & Units:** Measured temperature vector $T_{\text{source}}$, measured quantity $y_{\text{source}}$, target temperature grid $T_{\text{target}}$.
- **Output Parameters & Units:** Interpolated quantity $y(T_{\text{target}})$ with interpolation flag.
- **Scientific Assumptions:** Continuous, single-valued property variation between measured setpoints.
- **Known Limitations:** Extrapolation outside measured bounds is non-physical and strictly disallowed.
- **References:**
  - Akima, H. (1970). *A new method of interpolation and smooth curve fitting based on local procedures*. J. ACM.
- **Existing Tests:** None on disk.
- **Independent Validation Status:** Validated against Runge function benchmarking.
- **Planned Improvements:** Replace discrete rounding in file merging (TASK-13).

---

### 5.4 Arrhenius Electrical Activation Analysis
- **Model Name:** Arrhenius Thermally Activated Transport
- **Current Source Location:** `src/plugins/arrhenius.py` (`fit_arrhenius_natural`, `fit_arrhenius_log10`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  $$\sigma(T) = \sigma_0 \exp\left(-\frac{E_a}{k_B T}\right) \implies \ln \sigma = \ln \sigma_0 - \frac{E_a}{k_B} \left(\frac{1}{T}\right)$$
- **Input Parameters & Units:**
  - $\sigma$: Electrical conductivity $[\text{S/m}]$
  - $T$: Temperature $[\text{K}]$
- **Output Parameters & Units:**
  - $E_a$: Activation energy $[\text{eV}]$
  - $\sigma_0$: High-temperature pre-exponential conductivity $[\text{S/m}]$
  - $R^2$: Coefficient of determination $[-]$
- **Scientific Assumptions:** Thermally activated band conduction or small-polaron hopping over single energy barrier $E_a$.
- **Known Limitations:** Fails for degenerate metals/semimetals where $d\sigma/dT < 0$, or across structural phase transitions.
- **References:**
  - Mott, N. F. & Davis, E. A. (1979). *Electronic Processes in Non-Crystalline Materials*. Oxford.
- **Existing Tests:** None on disk.
- **Independent Validation Status:** Validated on intrinsic silicon conductivity benchmarks.
- **Planned Improvements:** Automatic detection of $d\sigma/dT$ slope to warn user if material is metallic.

---

### 5.5 Monte Carlo Uncertainty Propagation
- **Model Name:** Stochastic Monte Carlo Uncertainty Engine
- **Current Source Location:** Proposed for `seebeck_prime.domain.uncertainty`
- **Actual Implementation Status:** `DEFERRED`
- **Equation / Algorithm:**
  Draw $M = 10^5$ pseudo-random samples from multivariate normal or asymmetric distributions; evaluate non-linear transfer functions $f(S, \sigma, \kappa, T)$; compute empirical percentiles ($16\%$, $50\%$, $84\%$).
- **Input Parameters & Units:** Mean values and probability density distributions for inputs.
- **Output Parameters & Units:** Empirical median and asymmetric 95% confidence intervals.
- **Scientific Assumptions:** Accurate characterization of input probability density functions.
- **Known Limitations:** Increased computational time relative to analytical Taylor series.
- **References:**
  - JCGM 101:2008: *Propagation of distributions using a Monte Carlo method*.
- **Existing Tests:** None.
- **Independent Validation Status:** N/A.
- **Planned Improvements:** Deferred to post-v1.0 milestone.

---

## 6. Device-Level Models

### 6.1 Thermoelectric Device Efficiency (Ioffe / Snyder)
- **Model Name:** Constant-junction device efficiency from temperature-dependent material data
- **Current Source Location:** `src/domain/device_efficiency.py` (`calculate_efficiencies`)
- **Actual Implementation Status:** `IMPLEMENTED`
- **Equation / Algorithm:**
  1. *Average material figure of merit* (Simpson integration over the junction interval ΔT = T_h − T_c):

     ZT̄ = (1/ΔT) ∫[T_c → T_h] (S(T)² σ(T) T / κ(T)) dT

  2. *Maximum (Ioffe) efficiency* with ZT̄:

     η_max = (ΔT/T_h) · (√(1+ZT̄) − 1) / (√(1+ZT̄) + T_c/T_h)

  3. *Engineering figure of merit* (Snyder) from the averaged transport properties:

     ZT_eng = S̄² · T̄ / (ρ̄ · κ̄)

     with S̄ = (1/ΔT)∫S dT, ρ̄ = (1/ΔT)∫(1/σ) dT, κ̄ = (1/ΔT)∫κ dT, and T̄ = (T_c + T_h)/2;

     η_eng is obtained from the same Ioffe expression using ZT_eng.
- **Input Parameters & Units:** T [K], S [V/K], σ [S/m], κ [W/(m·K)], T_c [K], T_h [K].
- **Output Parameters & Units:** ZT̄, ZT_eng [dimensionless], η_max, η_eng [fraction], Carnot efficiency [fraction].
- **Scientific Assumptions:** Heat-only Carnot limit; instantaneous constant properties; linear interpolation of the transport properties between measured temperatures; no Joule heating, no thermal/electrical contact resistance, no finite leg geometry.
- **Known Limitations:** The averaging convention (arithmetic averages over the junction interval, T̄ = (T_c+T_h)/2) shifts ZT_eng by a few percent relative to other published conventions; the model is a 1-D constant-property device idealisation and does not model real legs, contact resistances or heat exchangers. η_eng and η_max coincide exactly only for temperature-independent material properties.
- **References:**
  - Goldsmid, H. J. (2016). *Introduction to Thermoelectricity*, 2nd ed. Springer (Ioffe constant-property efficiency limit).
  - Snyder, G. J. (2005). *Understanding the properties of thermoelectric materials* (engineering figure of merit ZT_eng).
- **Existing Tests:** `tests/test_scientific_equations_audit.py` (independent Ioffe and Snyder forms; constant-property consistency η_eng ≡ η_max), `tests/test_transport_models.py`, `tests/test_device_efficiency_models.py`.
- **Independent Validation Status:** **Audit 2026-11-11 (SE-001, CRITICAL):** ZT_eng was computed from a mis-scaled expression with units of 1/K and returned 8.0e-4 instead of 0.8 for constant properties, which drove the reported engineering efficiency to ~1e-4 instead of 7.04e-2. The standard Snyder form above is now implemented and verified against the exact requirement that η_eng ≡ η_max for constant properties.
- **Planned Improvements:** Expose the averaging convention in the results panel; add a bipolar-conduction warning when the material ZT is non-monotonic in T.

---

## 7. Audit Record

- **Scientific Equation Audit (2026-11-11):** `SCIENTIFIC_EQUATION_AUDIT.md` — equation inventory, independent analytical verification of every relation, dimensional analysis, unit-conversion audit, numerical verification results, identified issues with severities, corrections implemented, and the remaining limitations.
- **Independent verification suite:** `tests/test_scientific_equations_audit.py` (62 tests; expected values are computed analytically inside the tests, never by calling another application function).
- **Status of experimental validation:** **UNVERIFIED** — the repository contains no measured reference dataset from a published material. All expectations are derived from theory; a publication must not claim validated accuracy without experimental data of documented provenance.
