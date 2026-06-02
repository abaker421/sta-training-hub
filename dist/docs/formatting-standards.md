# Formatting Standards - Training Materials

A reference checklist for every document type produced in this project. Apply these before saving any new file.

---

## HTML Documents (case studies, reference pages, reports)

Reference file: `The Architect/system-assessment-2026-04-27.html` - this is the canonical style.

- **Font:** Roboto via Google Fonts (`wght@400;500;600;700;800`). Include preconnect tags.
- **CSS variables:** Define via `:root` - `--blue: #006098`, `--green: #6bc04b`, `--gray: #8a8d8e`, `--red: #c0392b`, `--light: #f4f6f8`, `--dark: #1e2a35`, `--white: #ffffff`, `--border: #dde3e8`.
- **Header:** Dark navy bg (`--dark`), white text, `border-bottom: 5px solid var(--blue)`. Include badge pills for meta.
- **Page bg:** `--light` (`#f4f6f8`). Body font-size 14px.
- **Section titles:** `font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--gray); border-bottom: 2px solid var(--border);` - NOT large h2 headings.
- **Item cards:** `.item` - white, `border: 1px solid var(--border)`, `border-radius: 10px`. Type indicated by colored top border: `border-top: 3px solid var(--green)` (strong/positive), `border-top: 3px solid var(--blue)` (informational), `border-top: 3px solid var(--red)` (warning/issue), `border-top: 3px solid var(--gray)` (neutral/reference).
- **Item header:** flex row with emoji icon + title (15px 700) + subtitle (11px uppercase, colored by type).
- **Item body:** `font-size: 13px; color: #444;`
- **Callouts:** Left-border style - blue `#e8f2f8 / --blue`, green `#edf7e6 / --green`, red `#fdf0ef / --red`, amber `#fef4e0 / #f4a300`.
- **Score/stat grid:** `display: grid; grid-template-columns: repeat(N, 1fr);` with `.score-card` - white card, centered large number.
- **Multi-item comparison cards (3+ items):** Always stack vertically (`display: flex; flex-direction: column; gap: 14px;`). Do NOT use `grid-template-columns: repeat(auto-fit, ...)` for 3 or more comparable option cards - horizontal square cards feel cramped and visually uneven. Two-item layouts can be horizontal. Three or more always vertical rectangles.
- **Flow steps:** Numbered blue circles (30px) + `h4` title + `p` body. No old timeline/connector style.
- **Final verdict block:** Dark navy bg (`--dark`), white text, green heading, `border-radius: 10px`.
- **Footer:** Dark navy, centered, `rgba(255,255,255,0.4)` text.
- **Code syntax:** hl-key `#006098`, hl-val `#5a6577` (muted), hl-str `#7a6040` (muted), hl-comment `var(--gray) italic`.
- **Company name:** Never "STA" or "STAi" - use "School Technology Associates", "School Technology", or "School Tech".

---

## Case Studies

Every project and course gets a case study HTML file. This is a standing deliverable, not optional.

**Canonical examples:**
- `Training Materials/Training - Admin/The Architect Case Study.html`
- `Training Materials/Training - Admin/Deep Research Case Study.html`

**Standard section structure (adapt as needed per subject):**
1. 01 - The Big Picture (what it is, with/without comparison)
2. 02 - System Architecture (how it's structured)
3. 03 - Modes / Input Types (if applicable)
4. 04 - Guardrails / Quality Gates
5. 05 - Live Case Study (step-by-step walkthrough)
6. 06 - The Output (stats + produced artifacts)
7. 07 - The File Format (if output files exist)
8. 08 - What Happens Next (downstream connections)
9. 09 - The Gravity of It (why it's harder than it looks + honest caveat)

**Required before generation - case confirmation gate:**
Before writing any case study, confirm with Adam which specific real session, example, or build will be used as the live case study (Section 05). Ask in one message - include 1-3 candidate examples drawn from known sessions, builds, or existing KB content, so Adam can pick or redirect rather than having to think from scratch:

> "Which specific session/build/example do you want to use for the live walkthrough in Section 05? Based on what I know, a few options that could work: [1] [candidate with one-line reason], [2] [candidate with one-line reason], [3] [candidate with one-line reason]. Pick one of these or name something else."

Rules:
- Only suggest real, known sessions - nothing fabricated or generic.
- If fewer than 3 good candidates are known, suggest what exists and note the gap.
- Do not proceed until Adam confirms a specific case. Do not start drafting, outlining, or creating any file before the case is named.

**Naming convention:** `[project-slug]-case-study.html` saved to `Training Materials/Training - Admin/`.

---

## PowerPoint (.pptx)

- **Font:** Roboto (primary). Fallback: Calibri or Effra per STA style guide.
- **Primary accent / headings:** `#006098` (STA Blue).
- **Secondary accent / highlights:** `#6bc04b` (STA Green).
- **Neutral / muted:** `#8a8d8e` (STA Gray).
- **Dark slide backgrounds:** `#1a2540` (use sparingly - section dividers only).
- **Light slide backgrounds:** `#f5f5f5` or `#ffffff`.
- **Body text on light:** `#1a1a1a`.
- **Text on dark:** `#ffffff`. Subtext/captions: `#b0c8d8`.
- **Never:** Generic palettes (orange, violet, default PowerPoint themes).

---

## Word Documents (.docx)

- **Font:** Roboto (primary). Fallback: Calibri.
- **Heading 1:** STA Blue `#006098`, bold.
- **Heading 2:** STA Blue `#006098`, slightly lighter weight than H1.
- **Accent color:** STA Green `#6bc04b` for callouts, highlights, or pull quotes.
- **Table headers:** `#006098` fill, white text.
- **Body text:** `#1a1a1a` on white background.
- **Company name:** Same rule as HTML - no "STA" abbreviation.

---

## Spreadsheets (.xlsx)

- **Header rows:** `#006098` fill, `#ffffff` text.
- **Alternating rows:** White / `#f5f6f8`.
- **Accent cells:** `#e8f0f8` (light blue tint) for highlights.
- **Chart colors:** Primary `#006098`, Secondary `#6bc04b`, Tertiary `#8a8d8e`.

---

## Outstanding Tasks

- [ ] Delete original case study files at project root level (manual step for Adam - sandbox cannot delete mounted files):
  - `Claude/Projects/Deep Research/Deep Research Case Study.html`
  - `The Architect/The Architect Case Study.html` (root level copy)

---

*Last updated: 2026-04-29*
