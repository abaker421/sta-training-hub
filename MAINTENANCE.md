# STA Training Kit Hub - Maintenance Notes

Pattern modeled on the HC Index App (`Claude/Projects/Help Center Assistant/article-index-app/`). Same source-and-dist convention. Originally React + Babel Standalone (no build step); rewritten to plain vanilla JS on 2026-06-01 (still no build step, and now no framework or CDN scripts loaded at startup).

---

## File Structure

| File / Folder | Purpose |
|---|---|
| `STA-Training-Hub.html` | **Source of truth - edit this file** |
| `dist/index.html` | Deployed/hosted version - must be synced after every edit |
| `dist/docs/` | All training HTML and markdown files referenced by cards. Includes styled HTML versions auto-generated from `dist/files/*.docx`. |
| `dist/files/` | Source `.docx` and `.pptx` files. The .docx files are converted to styled HTML in `dist/docs/` by `convert-docx-to-html.py` and served from there. |
| `dist/_headers` | Cloudflare Pages HTTP headers (cache control, security) |
| `dist/manifest.json` | PWA manifest for "Add to Home Screen" support |
| `convert-docx-to-html.py` | Utility to (re)build `dist/docs/*.html` from `dist/files/*.docx`. Run after any source docx edit. |
| `MAINTENANCE.md` | This file |
| `DEPLOY.md` | Cloudflare Pages + Cloudflare Access setup steps |

**Always edit `STA-Training-Hub.html` first. Always sync `dist/index.html` after.**

---

## How to Sync dist After Editing

After editing `STA-Training-Hub.html`, the dist copy must be updated or changes will not appear in the hosted app:

```bash
cp "STA-Training-Hub.html" "dist/index.html"
```

(That's the entire sync step. Both files are byte-identical when the app is correctly maintained.)

If you also updated any of the source training docs in `Training Materials/Training - Staff/` or `Training Materials/Training - Admin/`, sync those too:

```bash
# Single doc example
cp "../Training - Staff/Getting Started Guide.html" "dist/docs/Getting Started Guide.html"

# Full re-sync
# (see the deploy guide for the full one-liner)
```

---

## Ship to Deploy (mandatory after every sync)

**Cloudflare Pages deploys from the GitHub remote `origin/main`, not from the local filesystem.** Local dist syncs alone do NOT update the hosted hub - the change must reach `main` on GitHub before Cloudflare picks it up. Every sync must be followed by a merged PR, or the hub silently serves stale content even though dist/ on disk is up to date.

**Never `git push origin main`.** The change ships through a pull request. Cloudflare deploys on the merge, not on the push.

> **NOTE: nothing at the remote enforces this.** Verified 2026-08-20: this repo reports
> `protected=false` with no rulesets. It is a **public** repo, so branch protection is
> available on this GitHub plan and simply is not switched on. (On the private
> `school-tech-ai-system` repo it is not available at all - the API answers
> "Upgrade to GitHub Pro or make this repository public to enable this feature.")
> **The discipline IS the control.** An agent that checks, finds no protection, and
> concludes the rule was mistaken has misread this note.

**The Architect provides a paste-ready prompt at the end of every hub-modifying session** per RESTATED HARD RULES rule 13. Paste it into Claude Code to execute. The prompt template:

```bash
cd "C:\Users\Adam\source\repos\training-kit-hub"
git checkout main && git pull origin main
git checkout -b hub/[short-slug]
git status
git add -- STA-Training-Hub.html dist/index.html   # name the files; never git add -A
git commit -m "[concrete descriptive message of what changed]"
git push -u origin hub/[short-slug]
gh pr create --base main --fill
gh pr checks hub/[short-slug] --watch
gh pr merge hub/[short-slug] --squash --delete-branch
git checkout main && git pull origin main
```

If running manually (no Architect session):

1. `cd` to the hub folder above.
2. `git checkout main && git pull origin main`, then `git checkout -b hub/<slug>`.
3. `git status` to confirm what changed.
4. `git add -- <explicit paths>` (source + the synced dist file). Do not `git add -A`.
5. `git commit -m "..."` with a concrete commit message (name the files or behaviors that changed, not "updates").
6. `git push -u origin hub/<slug>`, then `gh pr create --base main --fill`.
7. Wait for checks, then `gh pr merge <branch> --squash --delete-branch`.

Cloudflare Pages auto-deploys within ~60 seconds of the **merge** completing. Confirm by loading the hosted hub URL in a new private window (to bypass browser cache).

**No merged PR = no deploy.** Edits to source files alone, or a pushed branch that never merges, will silently fail to reach users. This is the dominant operational failure mode for the hub - the dist sync rule (immediate, within-session) catches the local mirror issue; this ship rule (immediate, before declaring complete) catches the remote deploy issue.

Origin: 2026-05-21, The Architect's RESTATED HARD RULES rule 13 added after Adam observed the push step was being missed at the end of hub-modifying sessions. Revised 2026-07-28 on the belief that `main` had become protected across all repos. **That belief was wrong, or has since lapsed:** measured 2026-08-20, neither repo has any protection or ruleset, and on the private repo the feature is unavailable on this plan, so it could never have applied there. The PR workflow this note describes is still correct - keep it - but it rests on discipline, not on the remote rejecting anything.
---

## Re-converting .docx Files After Source Edits

The hub does NOT render `.docx` files directly - they are pre-converted to styled HTML at `dist/docs/[slug].html` so the app can display them inline with full STA branding, preserved colors, and inlined images. The original `.docx` files stay in `dist/files/` only as editable downloads (for intake forms that need filling out).

**Whenever a source `.docx` is updated, the matching `dist/docs/*.html` must be regenerated.** Run the conversion utility:

```bash
# Convert all .docx files in dist/files/
python3 convert-docx-to-html.py

# Convert a single file
python3 convert-docx-to-html.py ai-acceptable-use-policy.docx
```

The script uses LibreOffice headless mode (preserves colors and tables) and inlines all images as base64 so each output HTML is fully self-contained. Output lands in `dist/docs/` with the same kebab-case slug as the source.

**Standard update workflow:**

1. Edit the source `.docx` in Word / LibreOffice / Google Docs.
2. Save the edited file as `dist/files/[slug].docx` (overwrite the existing one).
3. Run `python3 convert-docx-to-html.py [slug].docx` (or run with no arg to rebuild all).
4. The matching `dist/docs/[slug].html` is regenerated with the latest content.
5. Commit and push (or drag-and-drop the updated `dist/` to Cloudflare Pages).

**Requirements:** LibreOffice must be installed and on PATH. On the sandboxed workspace shell it is preinstalled (`/usr/bin/libreoffice`). On a fresh local machine, install it from libreoffice.org or via package manager (`apt install libreoffice` / `brew install --cask libreoffice`).

**If you ADD a new .docx file to the hub:**

1. Drop the `.docx` into `dist/files/` using a kebab-case slug (no spaces).
2. Run `python3 convert-docx-to-html.py new-file-name.docx`.
3. Add an entry to `window.TRAINING_DATA.docs` in `STA-Training-Hub.html` pointing at `'docs/new-file-name.html'` with `type: 'html'`.
4. Add the doc id to the relevant `audiences[].sections[].docs` arrays.
5. Sync source to `dist/index.html` and deploy.

---

## Data Structure

`window.TRAINING_DATA` is a JSON-style object with two top-level keys:

```js
window.TRAINING_DATA = {
  audiences: [
    {
      id: 'unique-slug',
      title: 'Tab Name',
      icon: 'emoji',
      sub: 'Audience description shown under the tab title',
      sections: [
        {
          heading: 'Section heading',
          docs: ['doc-id-1', 'doc-id-2']
        }
      ]
    }
  ],
  docs: {
    'doc-id': {
      title: 'Doc Title',
      icon: 'emoji',
      desc: 'One-paragraph description shown on the card',
      file: 'docs/path/to/file.html', // or 'files/path/to/file.docx'
      type: 'html' | 'docx' | 'md' | 'pptx',
      priority: 'required' | 'recommended' | 'optional' | 'admin',
      tags: ['Tag1', 'Tag2']  // optional - first 2 shown on card
    }
  }
};
```

**Two patterns to remember:**

1. **Doc IDs are referenced from multiple audiences.** The same doc id (e.g., `aup`, `getting-started`) appears in multiple `audiences[].sections[].docs` arrays. This is intentional - one source of truth for each doc, multiple audience contexts that point to it.
2. **Priority drives the card top-border color.** Required = blue, Recommended = green, Optional = gray, Admin = orange. Pick the priority for the highest-tier audience that needs the doc; the card looks the same in every audience tab.

---

## Card Standards (locked 2026-06-09)

**Fixed card size + 5-line descriptions.** Every card renders at one fixed height (`.card { height: 212px; overflow: hidden }`) with its description clamped to a 5-line maximum (`-webkit-line-clamp: 5`). All cards are the same size whether or not they fill five lines. When adding or editing a doc, keep `desc` to roughly 200 characters / 5 lines - text past the clamp is truncated with an ellipsis, so rewrite the description rather than rely on the clamp.

**Deployment bubbles (Project vs Cowork).** Agent docs carry a `deployment: 'project' | 'cowork'` field. A `project` doc renders an indigo (`#3f51b5`) outline (full border + 3px top accent) on a white card body, plus a "Project" pill; a `cowork` doc renders a bronze (`#795548`) outline plus a "Cowork" pill. Card body stays white in both light and dark themes - only the outline and pill carry the deployment color. The in-doc header band matches the card via `DEPLOY_ACCENT`. Built web apps (e.g. the Project Tracker) get NO deployment field - they live under System reference, not the agent buckets.

**Redundant-tag dedup.** The card renderer auto-hides any tag that merely duplicates the priority (e.g. a `priority: 'admin'` card no longer shows a second "Admin" tag). List real, informative tags only.

## Definition of Done for Any Doc Edit (added 2026-08-19)

**Editing a doc is not finished until that doc'"'"'s card date moves.** Every entry in
`window.TRAINING_DATA.docs` carries an `updated:` field. When you change a file in
`dist/docs/`, set the matching card'"'"'s `updated:` to the edit date in the same pass.

Why this is a written rule: in the 2026-08-17 sweep **43 docs changed and exactly one card
date moved.** The hub then advertised months-old dates on freshly-corrected documents, which
is worse than no date at all - a stale date reads as "checked recently, still right" and
actively suppresses the next review. The drift check cannot catch it either, because the doc
and the card disagree without either one being internally inconsistent.

So the checklist for any doc edit is:

1. Edit the file in `dist/docs/`.
2. Bump that doc'"'"'s card `updated:` to today in `STA-Training-Hub.html`.
3. If the change alters what the card promises, fix `desc` (and `check`) too - a corrected
   doc behind a wrong description is still wrong to the reader who only reads cards.
4. `cp "STA-Training-Hub.html" "dist/index.html"` to sync.
5. Ship via PR (see above). No merged PR = no deploy.

A doc edit that ships without step 2 should be treated as an incomplete change, not a
completed one.

---

## Adding a New Doc

1. **Name the file as a URL-safe slug** before adding to dist. Use kebab-case, lowercase, no spaces, no special characters except hyphen and dot. Example: `customer-renewal-workflow.html`, not `Customer Renewal Workflow.html`. **This is mandatory** - Cloudflare Pages drag-and-drop uploads silently fail partway through batches when filenames contain spaces. The 2026-05-21 deploy attempt confirmed this empirically (uploads stopped at 3/4 with spaced filenames; succeeded fully after rename to slugs).
2. Add the file to `dist/docs/` (HTML and markdown) or `dist/files/` (binaries like docx, pptx, xlsx, pdf).
3. Add a new entry to `window.TRAINING_DATA.docs` in `STA-Training-Hub.html`. Use a kebab-case id that matches the filename slug (without extension). The `file:` value should be `'docs/your-slug.html'` or `'files/your-slug.docx'` - no spaces, no capitals.
4. Add the doc id to one or more `audiences[].sections[].docs` arrays. **For an agent or tool card in the AI Admin tab, file it by deployment type per the next section - never drop it into a single mixed bucket.**
5. `cp "STA-Training-Hub.html" "dist/index.html"` to sync.
6. Deploy (drag-and-drop `dist/` to Cloudflare Pages or push if git-based).

---

## Agent / Tool Card Placement in AI Admin (MANDATORY)

This rule exists because agent cards were repeatedly dropped into one undifferentiated "Internal agents & tools" list, which kept mixing Claude.ai Projects in with Coworks (e.g. the Internal R&D Tracker landed in the Cowork pile) and forced manual re-sorting. Do not recreate a single mixed bucket.

The AI Admin tab has exactly two internal-tool sections, in this fixed order:

1. **`Internal tools - Claude.ai Projects`** (TOP) - every agent whose registry **Deployment Target** is `Claude.ai Project` or `Both`.
2. **`Internal tools - Coworks`** (BOTTOM) - every agent whose Deployment Target is `Cowork`.

Built **web apps** (e.g. the STA Project Tracker hub tab - "a web app, not a chat agent") are neither: they belong under **`System reference`**, not the agent buckets.

**Procedure before adding any agent/tool card:** open `context-agent-registry.md`, find the agent's row, read its **Deployment Target** column, and place the card in the matching bucket above. Projects on top, Coworks on bottom, web apps in System reference. If the deployment type is unclear, resolve it against the registry first - never guess and never use a catch-all "agents & tools" heading.

---

## Removing a Doc

1. Delete the entry from `window.TRAINING_DATA.docs`.
2. Remove the doc id from every `audiences[].sections[].docs` array it appears in.
3. Delete the asset file from `dist/docs/` or `dist/files/`.
4. Sync and deploy.

The app silently ignores doc ids that don't exist in `docs`, so a missed reference won't crash - it just won't render a card. Search will also skip missing docs.

---

## Adding a New Audience Tab

Add a new entry to `window.TRAINING_DATA.audiences`. The order in the array is the order tabs appear. Use a kebab-case `id`. Tab icons are emoji - paste directly or use the `\u{XXXX}` escape format.

---

## Updating an Audience's Doc List

Edit the `sections` array of that audience. Each section has a `heading` and a `docs` array of doc ids. Headings appear as section dividers above each card grid.

---

## Current Audience Tabs (as of 2026-05-21)

1. **Start Here** - default tab, what everyone reads first
2. **Support Team** - Chris and Tyler
3. **SF Admins** - Tanya, Joanie, Kelsey, Adam
4. **Tanya** - SF Admins kit + brand tone capture
5. **Admin (Adam)** - full admin kit

Also auto-rendered when the user stars any doc: **Saved** tab with all favorited docs.

---

## Features Built In

- **Search** - across all doc titles, descriptions, and tags. Returns a flat card grid regardless of audience.
- **Favorites** - star icon on each card; saved per browser via `localStorage`. Saved tab only appears when the user has at least one favorite.
- **Active tab persistence** - last viewed audience tab persists across sessions via `localStorage`.
- **Mobile-responsive** - card grid collapses to single column under 700px width; header restacks.

---

## What This App Does NOT Do

- **No content rendering** - the app is a launcher. Clicking a card opens the source file (HTML/docx/md) in a new tab. Each doc renders in the browser's native viewer for that type.
- **No editing** - the app is read-only. To update content, edit the source files in `Training Materials/Training - Staff/` or `Training Materials/Training - Admin/`, then re-sync `dist/docs/` and `dist/files/`.
- **No analytics** - no tracking, no telemetry. The app loads no framework scripts at startup; the only external requests are the Roboto web font and, loaded lazily on first open of a `.md` or `.docx` doc, the SRI-pinned `marked` / `mammoth` libraries.
- **No auth** - auth is enforced upstream by Cloudflare Access at the domain level (see `DEPLOY.md`). The app assumes whoever loads it is already authorized to view it.

---

## Origin and Reference Pattern

Built 2026-05-21. Modeled on `Claude/Projects/Help Center Assistant/article-index-app/HC-Index-App.html`, the proven STA pattern for self-contained single-file apps. (This hub was originally React-on-CDN like HC Index; it was rewritten to plain vanilla JS on 2026-06-01 - no framework, no build step, no CDN scripts at load.) Differences:

- HC Index uses tabs as products (Time Clocks / VirtuaTime / etc.) with deep TOC sidebar. This app uses tabs as audiences with flat card grids - the right shape for a launcher rather than a content browser.
- Both apps use the same brand palette (`#1A1A2E` header, `#006098` blue, `#6bc04b` green).
- Both apps embed all data in `window.HC_DATA` / `window.TRAINING_DATA` for editability without a build step.
