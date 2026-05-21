# STA AI Training Hub

Internal training-document hub for School Technology Associates AI program. Single-file React app that indexes the training kit by audience (Start Here / Support Team / SF Admins / Tanya / Admin), with search and favorites.

Deployed on **Cloudflare Pages** with **Cloudflare Access** as the auth gate (`@k12sta.com` email required).

## What's in here

| Path | Purpose |
|---|---|
| `STA-Training-Hub.html` | Source of truth for the React app. Edit this file when changing audience tabs, doc entries, or the UI. |
| `dist/index.html` | Deployed copy of the app. Must be byte-identical to the source after every edit. |
| `dist/docs/` | All training HTML and markdown files referenced by doc cards. |
| `dist/files/` | All training docx and binary files (policies, intake forms, presentations). |
| `dist/_redirects` | Cloudflare Pages SPA fallback. |
| `dist/_headers` | Cloudflare Pages HTTP headers (cache, security). |
| `dist/manifest.json` | PWA manifest. |
| `MAINTENANCE.md` | How to add docs, rename files, sync source-to-dist. **Required reading before editing.** |
| `DEPLOY.md` | Cloudflare Pages + Cloudflare Access setup (one-time) and update procedures. |

## Deploy

See `DEPLOY.md`. In short: push to this repo and Cloudflare Pages auto-deploys from `dist/`.

## Build

None. The app is React 18 + Babel Standalone loaded from CDN; JSX is compiled in the browser at runtime. No build step. No `node_modules`. The deployed bytes ARE the source bytes.

## Filename convention

All files in `dist/docs/` and `dist/files/` use kebab-case slugs (lowercase, hyphens, no spaces, no special characters). This is required for reliable Cloudflare Pages uploads - the 2026-05-21 deploy attempt confirmed that spaced filenames cause silent upload failures partway through batches.

## Contact

Adam Baker - adamb@k12sta.com
