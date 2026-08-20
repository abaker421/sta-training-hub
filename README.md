# STA AI Training Hub

Internal training-document hub for School Technology Associates' AI program. A
self-contained single-file app that indexes the training kit by audience, with search
and favorites.

Deployed on **Cloudflare Pages** (project `sta-training-hub`) with **Cloudflare Access**
as the auth gate (`@k12sta.com` email required).

## What's in here

| Path | Purpose |
|---|---|
| `STA-Training-Hub.html` | Source of truth for the app. Edit this file when changing audience tabs, doc entries, or the UI. |
| `dist/index.html` | Deployed copy of the app. Must be byte-identical to the source after every edit. |
| `dist/docs/` | Training HTML and Markdown files referenced by doc cards. Includes styled HTML generated from `dist/files/*.docx`. |
| `dist/files/` | Binary training files served for download (`.docx`, `.pptx`, `.pdf`). |
| `dist/_headers` | Cloudflare Pages HTTP headers (cache control, content disposition). |
| `dist/manifest.json` | PWA manifest ("STA AI Training Hub"). |
| `dist/sw.js` | Service worker. Navigation is network-first by design, so a new deploy always wins and a bad cache cannot trap users on a stale page. |
| `dist/icons/`, `dist/img/` | Favicons, touch icons, and brand images. |
| `dist/serve.ps1` | Local static server for previewing `dist/` (`.\serve.ps1 -Port 8000`). |
| `convert-docx-to-html.py` | Rebuilds `dist/docs/*.html` from `dist/files/*.docx`. Run after any source docx edit. |
| `MAINTENANCE.md` | How to add docs, sync source to dist, and the definition of done for a doc edit. **Required reading before editing.** |
| `DEPLOY.md` | Cloudflare Pages + Cloudflare Access setup and update procedures. |
| `CLAUDE.md` | Branching and deploy rules for agents working in this repo. |

## Build

**None.** The app is plain vanilla JavaScript in one HTML file — no framework, no build
step, no `node_modules`, and **no external scripts loaded at startup**. The deployed bytes
are the source bytes.

Two libraries load lazily, only when a doc of that type is first opened: `marked`
(Markdown rendering) and `mammoth` (`.docx` rendering). Both are pinned with Subresource
Integrity hashes. If a CDN is unreachable, only `.md` and `.docx` viewing degrades — HTML
and PDF docs are unaffected.

## Data structure

All content lives in `window.TRAINING_DATA` inside the source file: an `audiences` array
(the tabs, each with sections of doc ids) and a `docs` object (one entry per card). There
are currently **8 audience tabs** — Start Here, Sales, Support, Marketing, Operations,
Renewals, Salesforce Admins, AI Admin — plus a **Saved** tab that appears only once the
user stars something. A ninth view, search, returns a flat grid across all audiences.

A card's `desc` is rendered through an HTML-escaping helper, so it is **plain text only** —
markup there renders as literal tag text rather than formatting. The optional `check` field
has no render path today; it is card metadata only. Keep it plain text as well, so it stays
safe if it is ever surfaced.

## Deploy

Cloudflare Pages deploys from the GitHub remote `origin/main`, **not** from your local
filesystem. A local `dist/` sync alone does not update the hosted hub.

`main` is branch-protected, so the change ships through a pull request:

1. Branch, edit `STA-Training-Hub.html`, then `cp "STA-Training-Hub.html" "dist/index.html"`.
2. Stage explicit paths (`git add -- <paths>`), commit, push, open a PR.
3. Wait for checks, then squash-merge.

Pages picks up the change within about 60 seconds of the **merge**. See `DEPLOY.md` for the
full procedure and `CLAUDE.md` for the branching rules.

## Filename convention

Files in `dist/docs/` and `dist/files/` use kebab-case slugs — lowercase, hyphens, no
spaces or special characters. This is required: the 2026-05-21 deploy confirmed that
spaced filenames cause silent upload failures partway through a batch.

## Do not add a `_redirects` file

There is deliberately no `dist/_redirects`. The wildcard SPA fallback
(`/* /index.html 200`) is rejected at deploy time with `[code: 10021] Infinite loop
detected`, and the hub does not need it — there is no client-side routing, every card
opens a real static file, and `/` serves `index.html` naturally. See `DEPLOY.md` for the
detail and for the exact-match redirect form to use if a URL ever has to move.

## Contact

Adam Baker — adamb@k12sta.com
