# Seebeck Prime — Documentation Archive

This directory contains superseded historical planning documents, audits, and architectural transition maps.

---

## 1. Archival Notice & Purpose

As part of the documentation consolidation milestone (October 2026), all disparate and overlapping markdown planning files in the repository root were audited, reconciled against actual source code evidence, and synthesized into a clean, authoritative documentation suite under `docs/`.

These historical documents are preserved here for historical context and traceability. **They are no longer active sources of truth and should not be used for implementation decisions.**

---

## 2. Superseded Documents & Authoritative Mapping

| Archived Document | Original Purpose | Why Superseded | Authoritative Replacement |
|---|---|---|---|
| `ARCHITECTURE_AUDIT.md` | Initial Phase 0 audit of legacy code (Aug 2026) | Contained outdated directory descriptions and superseded coupling analysis. | [`docs/ARCHITECTURE.md`](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/ARCHITECTURE.md) |
| `ARCHITECTURE_MIGRATION_MAP.md` | File-by-file refactoring map (Aug 2026) | Superseded by verified issue tracker and prioritized phase roadmap. | [`docs/MIGRATION_PLAN.md`](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/MIGRATION_PLAN.md) |
| `SCIENTIFIC_FUNCTION_MAP.md` | Initial inventory of scientific functions | Lacked rigorous equations, unit specifications, and domain assumptions. | [`docs/SCIENTIFIC_MODEL_REGISTER.md`](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/SCIENTIFIC_MODEL_REGISTER.md) |
| `SCIENTIFIC_REVIEW_NEEDED.md` | Flagged approximations (SPB, Kim Lorenz, binning) | Consolidated into unified model register with equations, limitations, and plans. | [`docs/SCIENTIFIC_MODEL_REGISTER.md`](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/SCIENTIFIC_MODEL_REGISTER.md) |
| `SOFTWAREX_VALIDATION_REPORT.md` (legacy) | Draft validation report (Aug 2026) | Contained unverified claim of 135 passing tests while test files were absent from disk. | [`docs/SOFTWAREX_VALIDATION_REPORT.md`](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/SOFTWAREX_VALIDATION_REPORT.md) |
| `plan.md` | AI Agent Master Plan (Aug 2026) | Long 1500-line historical prompt plan; core architectural guidance and scope constraints incorporated into authoritative docs. | [`docs/ARCHITECTURE.md`](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/ARCHITECTURE.md) & [`docs/MIGRATION_PLAN.md`](file:///c:/Users/Elkady/Documents/seebeck_new/Seebeck-Prime/docs/MIGRATION_PLAN.md) |

---

## 3. Preserved Historical Context

Key historical decisions and findings preserved from these documents:
1. **Scope Boundary:** Strict commitment that Seebeck Prime is an experimental transport analysis platform, explicitly excluding DFT, literature web-scraping, and heavy distributed infrastructure.
2. **Phase 1-2 Domain Extraction:** The initial strategy of creating a pure, GUI-independent domain layer (`seebeck_prime.domain`) was recorded in `ARCHITECTURE_MIGRATION_MAP.md` and remains the foundation of the target architecture.
3. **Scientific Flags:** The approximations identified in `SCIENTIFIC_REVIEW_NEEDED.md` (Kim empirical Lorenz formula, empirical carrier concentration, and lattice thermal conductivity without bipolar conduction) have been formally incorporated into the model register with explicit warnings and improvement tasks.
