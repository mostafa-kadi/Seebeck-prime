# Seebeck-Prime — Reference Verification Audit (Stage 6b, final)

**Document type:** SoftwareX manuscript-preparation deliverable.
**Date:** 2026-11-12 (verification performed live today)
**Status:** All listed references verified against **Crossref** and/or
**OpenAlex** on 2026-11-12. No DOI, title, author name, journal, volume or page
number in the final reference list is invented.

---

## 1. Outcome of the verification pass

The Stage-4 draft bibliography contained **three wrong DOIs and several
unverifiable entries**. The verification pass caught and corrected or removed
them:

| Draft entry (Stage 4) | Verification result | Disposition |
|---|---|---|
| `kim2015` DOI `10.1063/1.4915862` | **WRONG** — resolves to an unrelated AIP Conference Proceedings paper ("Distributed search engine architecture…") | Corrected to `10.1063/1.4908244` (verified) |
| `snyder2008` DOI `10.1038/nmat2160` | **WRONG** — resolves to a different Nature Materials paper ("Electrostatic electrochemistry at insulators", Liu & Bard) | Corrected to `10.1038/nmat2090` (verified) |
| `snyder2020` DOI `10.1002/adma.201901537` | **WRONG** — DOI does not resolve (404) | Corrected to `10.1002/adma.202001537` (verified) |
| `snyder2022` PRX Energy `10.1103/PhysRevResearch.4.034021` | DOI does not resolve; intended paper not locatable | **REMOVED** |
| `putley1960` (book) | Title/author confirmed via three 1962 book reviews; publisher/edition unverifiable locally | **REMOVED** (Hall background stands without citation rather than with an unverified reference) |
| Historical Wiedemann/Franz/Sommerfeld/Lorenz entries | Details not verifiable locally | **REMOVED** (context covered by verified kim2015/snyder2008/goldsmid2016) |
| `capriogarcia2020` (PbTe benchmark) | Journal wrongly drafted as J. Mater. Chem. A | Corrected from repository registry + Crossref: **Current Applied Physics**, authors Zhang/Zhao/Gu/Peng (verified) |
| `wilkins2015` (SiGe:Sb benchmark) | Journal wrongly drafted as Int. J. Heat Mass Transfer; authors unknown | Corrected from repository registry + Crossref: **Energy Conversion and Management**, authors Wang et al. (verified) |
| Benchmark DOI for SiGe:P | Draft used the Bi₂Te₃ DOI pattern by mistake | Corrected from repository registry + Crossref: `10.1021/acsami.9b20090` (verified) |

## 2. Final verified reference list (as in `references.bib`)

| # | Key | Reference (verified) | DOI | Verified via |
|---|---|---|---|---|
| 1 | `kim2015` | H.-S. Kim, Z. M. Gibbs, Y. Tang, H. Wang, G. J. Snyder, "Characterization of Lorenz number with Seebeck coefficient measurement", **APL Materials** 3 (2015) | 10.1063/1.4908244 | OpenAlex + Crossref |
| 2 | `snyder2008` | G. J. Snyder, E. S. Toberer, "Complex thermoelectric materials", **Nature Materials** 7, 105–114 (2008) | 10.1038/nmat2090 | OpenAlex + Crossref |
| 3 | `snyder2020` | G. J. Snyder, A. H. Snyder, M. Wood, R. Gurunathan, B. H. Snyder, C. Niu, "Weighted Mobility", **Advanced Materials** 32, e2001537 (2020) | 10.1002/adma.202001537 | OpenAlex + Crossref |
| 4 | `maysnyder2012` | A. F. May, G. J. Snyder, "Introduction to Modeling Thermoelectric Transport at High Temperatures", in *Materials, Preparation, and Characterization in Thermoelectrics*, CRC Press, 207–224 (print ed. 2012) | 10.1201/b11891-11 | OpenAlex + Crossref |
| 5 | `goldsmid2016` | H. J. Goldsmid, *Introduction to Thermoelectricity*, Springer Series in Materials Science (2016) | 10.1007/978-3-662-49256-7 | OpenAlex + Crossref |
| 6 | `huang2019` | Z.-y. Huang, H.-q. Li, X.-y. Wang, W. Jiang, F.-q. Zu, "Effect of Cu electroless plating on thermoelectric properties of n-type Bi2Te2.4Se0.6 alloy", **J. Mater. Sci.: Mater. Electron.** 30, 15018–15023 (2019) | 10.1007/s10854-019-01874-0 | Crossref (and registry) |
| 7 | `zhang2020` | C. C. Zhang, Y. Zhao, P. Gu, L. M. Peng, "Thermoelectric performance in pseudo-ternary (PbTe)0.95-x(Sb2Se3)x(PbS)0.05 system with ultra-low thermal conductivity via multi-scale phonon scattering", **Current Applied Physics** 20, 1008–1012 (2020) | 10.1016/j.cap.2020.06.028 | OpenAlex (and registry) |
| 8 | `wang2015` | C. Wang, S. Lin, H. Chen, Y. Zhao, L. Zhao, H. Wang, D. Huo, X. Chen, "Thermoelectric performance of Si80Ge20−xSbx based multiphase alloys with inhomogeneous dopant distribution", **Energy Conversion and Management** 94, 331–336 (2015) | 10.1016/j.enconman.2015.01.082 | Crossref (and registry) |
| 9 | `wang2020srtio3` | J. Wang, J.-B. Li, H.-Y. Yu, J. Li, H. Yang, X. Yaer, X.-H. Wang, H.-M. Liu, "Enhanced Thermoelectric Performance in n-Type SrTiO3/SiGe Composite", **ACS Appl. Mater. Interfaces** 12, 2687–2694 (2020) | 10.1021/acsami.9b20090 | Crossref (and registry) |
| 10 | `katsura2025` | Y. Katsura, M. Kumagai, T. Mato, Y. Takada, Y. Ando, E. Fujita, F. Hosono, E. Koyama, F. Mudasar, T. N. T. Phuong, "Starrydata: from published plots to shared materials data", **Sci. Technol. Adv. Mater.: Methods** 5 (2025) | 10.1080/27660400.2025.2506976 | OpenAlex + Crossref |

### Residual minor flags (do not block submission, but confirm at proof stage)

- `kim2015`: Crossref records volume 3, issue 4 but no page/article number;
  the APL Materials article number should be added from the publisher PDF at
  proof stage.
- `wang2020srtio3`: journal issue is 2020 (vol. 12); Crossref records the
  online publication as December 2019. Cited here as 2020.
- `maysnyder2012`: print book is 2012; the DOI record is the 2017 e-book
  edition. Cited here as 2012.
- Author-name spellings follow Crossref records (e.g. "Alemayouh H. Snyder"
  exactly as Crossref lists it); confirm against the publisher PDF at proof
  stage.

## 3. Citation-support mapping (manuscript statements → references)

| Manuscript statement | Supporting verified reference(s) |
|---|---|
| PF, κe (Wiedemann–Franz), κL, ZT conventions | `snyder2008`, `goldsmid2016` |
| Empirical Lorenz number L(S) | `kim2015` |
| Rigorous SPB transport-integral modelling | `maysnyder2012` |
| Weighted mobility context | `snyder2020` |
| Benchmark data provenance | `katsura2025` |
| Bi₂Te₃ benchmark specimen | `huang2019` |
| PbTe benchmark specimen | `zhang2020` |
| SiGe:Sb benchmark specimen | `wang2015` |
| SiGe:P (SrTiO₃/SiGe reference) benchmark specimen | `wang2020srtio3` |

## 4. Rule for the final manuscript (unchanged, now satisfied)

- Every citation in `MANUSCRIPT.tex` resolves to an entry in §2 above.
- No unverified bibliographic detail appears in the manuscript bibliography.
- Any future citation must be verified the same way before it is added.

---

*End of reference-verification audit (final).* 
