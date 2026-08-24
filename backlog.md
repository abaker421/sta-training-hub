# Backlog - STA Training Hub

## Active

- 2026-08-24 - Assign a per-doc accent to the 77 dist/docs files that declare none. Design decision, Adam's call - accents map to audience and topic, not to a script. This is the actual prerequisite for the title gradient being a per-doc feature rather than a uniform blue wash. Effort: unknown until the grouping is decided.

## Parked

- 2026-06-01 - PARKED 2026-08-24 - Screenshots: the 11 items from the AI Admin tab gather list, for the skill briefs and the onboarding spots. Parked because each capture is of Adam's own logged-in account and cannot be automated. Revisit only if a specific doc is blocked on one.

## Implemented

- 2026-05-22 - Add Cloudflare Access SSO gating so only @k12sta.com emails can access the hub. DONE - verified in Cloudflare Zero Trust 2026-08-24. Access application `sta-training-hub - Cloudflare Workers` covers sta-training-hub.adamb-1a4.workers.dev; policy `sta-training-hub - Production` allows Emails ending in @k12sta.com; login methods are One-time PIN plus a Google Workspace IdP named K12sta.
- 2026-06-12 - Opened-doc title gradient. DONE 2026-08-24, scoped to the 9 docs that declare --doc-accent. The original note assumed per-doc accents existed library-wide; a survey found 9 of 86. The other 77 fall through to the default blue and were deliberately left unchanged. The two generated pages are excluded: they have no doc-title h1, only numbered section headings. Readable-shade values corrected to green #37811c (4.72) and admin orange #a56400 (4.77) - the note's original #3a8a1e (4.34) and #b06a00 (4.28) both fail AA normal text and must not be used.
