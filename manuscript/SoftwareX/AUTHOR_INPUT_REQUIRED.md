# Seebeck-Prime Author Input Required — SoftwareX Stage 1

**Document type:** Stage 1 deliverable of the SoftwareX manuscript preparation.
**Date:** 2026-11-12
**Companion documents:** `manuscript/SoftwareX/SOFTWARE_CAPABILITY_MATRIX.md`,
`manuscript/SoftwareX/RESEARCH_POSITIONING.md`,
`manuscript/SoftwareX/MANUSCRIPT_OUTLINE.md`.

---

## 1. Purpose

This document lists, in author-facing terms, every item that is **not yet
resolved** and therefore must be supplied or confirmed by the project author
before the corresponding manuscript content may be finalised.

No placeholder value has been invented here.

## 2. Author-input items

### 2.1 Author identity and affiliation
- Full author list for the SoftwareX submission: **[TO BE CONFIRMED BY AUTHOR]**.
- Affiliation(s) for each author: **[TO BE CONFIRMED BY AUTHOR]**.
- Corresponding author and corresponding-author email: **[TO BE CONFIRMED BY AUTHOR]**.
- ORCID iDs: **[TO BE CONFIRMED BY AUTHOR]**.
- Funding sources / grant numbers: **[TO BE CONFIRMED BY AUTHOR]**.
- Competing interests: **[TO BE CONFIRMED BY AUTHOR]**.
- Acknowledgements: **[TO BE CONFIRMED BY AUTHOR]**.
- Author contributions (CRediT): **[TO BE CONFIRMED BY AUTHOR]**.
- Confirm whether the publication name should be **Mostafa M. Elkady**.

### 2.2 Software metadata
- Current software version: reconcile between `pyproject.toml`, `CHANGELOG.md`,
  and the validation reports — **[version discrepancy to be resolved: audit D-03]** .
- Public repository URL / distribution: **[TO BE CONFIRMED BY AUTHOR]** (local-only
  files must not be claimed as a compliant distribution).
- License: **[TO BE CONFIRMED BY AUTHOR]** (audit D-04 open).
- Release / archiving step required before submission: **[TO BE CONFIRMED BY AUTHOR]**.

### 2.3 Code and evidence
- Confirm the authoritative module paths for the capability matrix (the author
  may have newer paths than those recorded here).
- Confirm the exact set of literature references to be cited, and their verified
  bibliographic details (title, authors, journal, year, DOI).

### 2.4 Clinical / ethical / accessibility disclosures
- None identified in the local project at Stage 1.

## 3. Required confirmations before Stage 2 (manuscript drafting)

The following must be author-confirmed before Stage 2 begins:

1. Approval to proceed from **Stage 1 to Stage 2** (manuscript outline).
2. Confirmation of the author identity and affiliation set.
3. Resolution of the version, license, and distribution items above.
4. Any additional literature references the author intends to cite (the
   Stage-1 positioning draft used repository-recorded anchors only).
5. Confirmation of which proposed titles to take forward.

## 4. Items already resolved during the validation programme (no author input
required at this stage)

- The full-suite result at the end of Phase 3: **680 passed, 10 skipped, 1 warning**
  (conda primary environment); Qt-capable venv: 629 passed, 4 skipped.
- The negative-κL diagnostic fix (D-01) is implemented and tested; GUI tests for it
  run in the Qt-capable environment.
- The benchmark carrier-unit defect (D-02) is fixed and guarded.
- The SiGe:P Lorenz finding (D-13) is resolved and locked in.
- The weighted-mobility divergence (D-12) is documented, not changed.

These resolved items are recorded here so that the author does not have to
re-derive them during drafting.
