# Backlog - STA Training Hub

## Active

- 2026-06-12 - Opened-doc title gradient: render the doc h1 as a gradient from the dark title color (#1e2a35) to the doc's accent (Gradient A, dark->accent). Use the readable darker accent shade for light colors (green ->#3a8a1e, admin orange ->#b06a00) so the title stays legible; stripe/footer keep the bright card color. Context: approved direction during the 2026-06-12 header overhaul but deferred to ship the Option 3 footer-strip first. Effort: one pass over the ~65 converted doc headers (or a shared rule), about an hour.

## Parked

- 2026-06-01 - PARKED 2026-08-24 - Screenshots: the 11 items from the AI Admin tab gather list, for the skill briefs and the onboarding spots. Parked because each capture is of Adam's own logged-in account and cannot be automated. Revisit only if a specific doc is blocked on one.

## Implemented

- 2026-05-22 - Add Cloudflare Access SSO gating so only @k12sta.com emails can access the hub. DONE - verified in Cloudflare Zero Trust 2026-08-24. Access application `sta-training-hub - Cloudflare Workers` covers sta-training-hub.adamb-1a4.workers.dev; policy `sta-training-hub - Production` allows Emails ending in @k12sta.com; login methods are One-time PIN plus a Google Workspace IdP named K12sta.
