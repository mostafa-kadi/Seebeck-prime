# Seebeck-Prime — SoftwareX Compliance Checklist (Stage 5 draft)

**Document type:** Stage 5 deliverable of the SoftwareX manuscript preparation.
**Date:** 2026-11-12
**Status:** Draft — pending verification against the current official guide.

---

## 1. Checklist items

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Maximum manuscript length | **Verified against official guide (2026):** the descriptive paper has a **4000-word limit** (the commonly quoted 3000 was outdated). Draft body ≈2,300 words → **within limit**. | Verify against the final submission version |
| 2 | Required article structure | **Drafted** | Title/abstract/motivation/software/functionality/validation/impact/limitations/conclusions (+metadata, refs, figs) |
| 3 | Required software metadata table | **Substantially filled (2026-11-13)** | C1 (0.1.0, released), C3 (MIT), C4 (git), C5 (languages/tools), C6 (deps) filled; C2 (public repo), C7 (docs URL), C8 (support email) remain `[AUTHOR TO CONFIRM]` → `SOFTWARE_METADATA.md` |
| 4 | Software availability | **Open (author-side)** | Local release preparation complete (licence, version, `CITATION.cff`, wheel build + clean-venv install verified 2026-11-13); the public GitHub repository and tagged `v0.1.0` release + DOI remain to be created |
| 5 | Licensing information | **RESOLVED (2026-11-13): MIT** | `LICENSE` + `Licence.txt` in the repository (SoftwareX-required filename); `setup.py` `license="MIT"` + classifier aligned; `CITATION.cff` license field set |
| 6 | Reference formatting | **Draft** | `references.bib` + `REFERENCE_VERIFICATION.md`; DOIs to verify |
| 7 | Submission-specific declarations | **Not drafted** | To be added at final assembly |
| 8 | Generative-AI disclosure | **Not drafted** | Required at submission: statement before reference list (see `AI_USAGE_RECORD.md`) |
| 9 | Title-page content | **Draft** | Title/authors/affiliations/corresponding author/email/address — author input pending |
| 10 | Abstract | **Draft** | Must be ≤250 words, standalone, no references, minimal abbreviations → `MANUSCRIPT_DRAFT.md` currently ~150 words draft — to be finalised |
| 11 | Keywords | **Draft** | 1–7 keywords, English, avoid multi-word keywords → draft proposes 5 |
| 12 | Highlights | **Pending** | Encouraged; 3–5 bullets, ≤85 chars each — planned (`FIGURE_PLAN.md`/`MANUSCRIPT_OUTLINE.md`) |
| 13 | Graphical abstract | **Pending** | Encouraged; ≥1328 px wide, 13 cm readable, no AI-generated primary-data images → planned |
| 14 | Math formulae | **Draft** | Editable text, solidus, italics, exp, display eqns numbered consecutively |
| 15 | Tables | **Draft** | Editable text, captions/notes, avoid vertical rules |
| 16 | Figures/artwork | **Draft** | Separate files, captions, logical naming; Fig. 2 pending author input |
| 17 | Ethics | **Draft** | Authorship (substantial contributions, corresponding author), competing interests (declarations tool), funding (standard; none → state), GenAI (disclosure required) |
| 18 | File format | **Verified:** Word single-column (.doc/.docx) or LaTeX (.tex); PDF not acceptable source; remove strikethrough/underline unless scientific |
| 19 | Templates | **RESOLVED (2026-11-12):** official OSP template downloaded unmodified to `templates/softwarex-osp-template.tex` (+ `.docx`) from `legacyfileshare.elsevier.com/promis_misc/softwarex-osp-template.tex`; structure inspected; `MANUSCRIPT.tex` produced from it (instruction block deleted per template's own instruction) | Template-enforced requirements recorded below |

## 1b. Requirements enforced by the official OSP template (verified 2026-11-12)

| # | Template requirement | Status in `MANUSCRIPT.tex` |
|---|---|---|
| T1 | Five mandatory templated sections: *Motivation and significance*, *Software description*, *Illustrative examples*, *Impact*, *Conclusions* | **Met** (all five present with exact names; extra *Limitations and future work* section retained for honesty) |
| T2 | Mandatory "Required Metadata" + "Current code version" code-metadata table (C1–C8) | **Present**; C1 = "0.1.0 (released 2026-11-13)", C3 = MIT, C4–C6 filled; C2/C7/C8 = `[AUTHOR TO CONFIRM]` |
| T3 | **GitHub-only repository** in metadata tables (other hosts not accepted) | **Open** — author must create/public release |
| T4 | Repository must contain a well-documented `README.md` and a `Licence.txt` (paper returned if missing) | **Met locally (2026-11-13):** `README.md` refreshed (architecture, scientific status, licence, citation, support sections) and `Licence.txt` + `LICENSE` present with the MIT text; the files must be pushed to the public repository |
| T5 | Word limit 4,000; max 6 figures; max 6 pages of main text | Body within limit (word count checked at assembly; figures: 2 placeholder figures declared) |
| T6 | Abstract "ca. 100 words" (guide max 250) | Draft abstract ≈145 words — within guide max, above template hint; author may trim at proof stage |
| T7 | Mandatory "Current executable software version" end section | **Present** with placeholders |
| T8 | We will only consider software articles submitted using this template | `MANUSCRIPT.tex` follows the template verbatim in structure and class options |
| T9 | Compile verification of `MANUSCRIPT.tex` (elsarticle + bibtex run) | **Open** — no LaTeX toolchain available locally; verify on Overleaf (upload `MANUSCRIPT.tex` + `references.bib`) or the author's TeX installation before submission |

## 2. Compliance conclusion (updated)

Verified against the live SoftwareX author guide (accessed 2026-11-12):
- Descriptive paper limit: **4000 words** (updated from the commonly quoted 3000).
- Abstract limit: **250 words**.
- Keywords: **1–7**.
- GenAI disclosure: **required** at submission (statement before references; AI tools must not be authors).
- Software: open-source distribution + support material; GitHub hosting; journal-archived accepted copy.
- File formats: .docx/.tex; Word single-column; PDF not acceptable source.

Compliance is contingent on (a) completing author-input items, (b) finalising references, (c) completing metadata, (d) finalising compliance checklist items 9–19.

## 3. Open compliance items

- Finalise author inputs (items 9, 3, 4, 5).
- Finalise references (item 6).
- Finalise compliance items 7, 8, 12–19.
- Inspect official templates (item 19) and produce `MANUSCRIPT.tex` / `MANUSCRIPT.docx`.
- Complete final polish.

---

*End of compliance-checklist draft (updated).*
