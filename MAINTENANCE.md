# STA Training Kit Hub - Maintenance Notes

Pattern modeled on the HC Index App (`Claude/Projects/Help Center Assistant/article-index-app/`). Same source-and-dist convention; same React + Babel Standalone (no build step) architecture.

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

## Adding a New Doc

1. **Name the file as a URL-safe slug** before adding to dist. Use kebab-case, lowercase, no spaces, no special characters except hyphen and dot. Example: `customer-renewal-workflow.html`, not `Customer Renewal Workflow.html`. **This is mandatory** - Cloudflare Pages drag-and-drop uploads silently fail partway through batches when filenames contain spaces. The 2026-05-21 deploy attempt confirmed this empirically (uploads stopped at 3/4 with spaced filenames; succeeded fully after rename to slugs).
2. Add the file to `dist/docs/` (HTML and markdown) or `dist/files/` (binaries like docx, pptx, xlsx, pdf).
3. Add a new entry to `window.TRAINING_DATA.docs` in `STA-Training-Hub.html`. Use a kebab-case id that matches the filename slug (without extension). The `file:` value should be `'docs/your-slug.html'` or `'files/your-slug.docx'` - no spaces, no capitals.
4. Add the doc id to one or more `audiences[].sections[].docs` arrays.
5. `cp "STA-Training-Hub.html" "dist/index.html"` to sync.
6. Deploy (drag-and-drop `dist/` to Cloudflare Pages or push if git-based).

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
- **No analytics** - no tracking, no telemetry, no third-party scripts beyond the React/Babel CDN scripts loaded for the app itself.
- **No auth** - auth is enforced upstream by Cloudflare Access at the domain level (see `DEPLOY.md`). The app assumes whoever loads it is already authorized to view it.

---

## Origin and Reference Pattern

Built 2026-05-21. Modeled on `Claude/Projects/Help Center Assistant/article-index-app/HC-Index-App.html` which is the proven STA pattern for self-contained React-on-CDN apps. Differences:

- HC Index uses tabs as products (Time Clocks / VirtuaTime / etc.) with deep TOC sidebar. This app uses tabs as audiences with flat card grids - the right shape for a launcher rather than a content browser.
- Both apps use the same brand palette (`#1A1A2E` header, `#006098` blue, `#6bc04b` green).
- Both apps embed all data in `window.HC_DATA` / `window.TRAINING_DATA` for editability without a build step.
