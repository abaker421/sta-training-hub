# Backlog - STA Training Hub

## Active

- 2026-08-24 - Assign a per-doc accent to the 77 dist/docs files that declare none. Design decision, Adam's call - accents map to audience and topic, not to a script. This is the actual prerequisite for the title gradient being a per-doc feature rather than a uniform blue wash. Effort: unknown until the grouping is decided.

- 2026-08-27 - **html-checklist gained a third output mode (SURVEY) - the card and the brief both still say two.** The skill now emits a Likert/rating matrix as `survey-[slug].html`: one statement per row, radio columns on a scale the requester defines, a separate scale allowed per section, one-section-per-page pagination with Back/Next and a clickable step bar, an all-rows-answered gate before Next, N/A excluded from scoring, per-section and overall scores (a percentage of points-possible when the sections use different scales), and the same Generate .md export. Two surfaces to fix, both hand-edited (`skill-html-checklist.html` is NOT in `GENERATED_PAIRS`, so edit the HTML directly, do not look for a .docx):
  1. `STA-Training-Hub.html` - the `HTML Checklist` card. `desc` opens "Two kinds:" and describes only checkbox and intake; add survey. Bump `updated` from `2026-06-01`. The `check` question ("What three visual features...show your progress") was written against checkbox mode only and now has a second right answer in the survey step bar - reword it or scope it to checkbox mode.
  2. `dist/docs/skill-html-checklist.html` - the brief. Its `Two modes` heading and the `When to use it` section both enumerate exactly two; needs a third `Survey mode` block and a third when-to-use line.
  Suggested when-to-use wording, since the distinction is the thing staff will get wrong: checkbox = things you complete; form/intake = things you collect; survey = things you rate. Staff-facing examples that fit STA: a district readiness self-assessment, a post-training feedback form, an internal tool-satisfaction pulse.
  Effort: small - two text edits, no script run, no new asset. Source of the change: html-checklist v3, 2026-08-27, backed up and packaged; see `Backups\skills\html-checklist\CHANGELOG.md`.

## Parked

- 2026-06-01 - PARKED 2026-08-24 - Screenshots: the 11 items from the AI Admin tab gather list, for the skill briefs and the onboarding spots. Parked because each capture is of Adam's own logged-in account and cannot be automated. Revisit only if a specific doc is blocked on one.

## Implemented

- 2026-05-22 - Add Cloudflare Access SSO gating so only @k12sta.com emails can access the hub. DONE - verified in Cloudflare Zero Trust 2026-08-24. Access application `sta-training-hub - Cloudflare Workers` covers sta-training-hub.adamb-1a4.workers.dev; policy `sta-training-hub - Production` allows Emails ending in @k12sta.com; login methods are One-time PIN plus a Google Workspace IdP named K12sta.
- 2026-06-12 - Opened-doc title gradient. DONE 2026-08-24, scoped to the 9 docs that declare --doc-accent. The original note assumed per-doc accents existed library-wide; a survey found 9 of 86. The other 77 fall through to the default blue and were deliberately left unchanged. The two generated pages are excluded: they have no doc-title h1, only numbered section headings. Readable-shade values corrected to green #37811c (4.72) and admin orange #a56400 (4.77) - the note's original #3a8a1e (4.34) and #b06a00 (4.28) both fail AA normal text and must not be used.
