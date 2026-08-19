# STA Training Kit Hub - Deployment Guide

Step-by-step for deploying the hub on Cloudflare Pages with Cloudflare Access (Zero Trust) gating by `@k12sta.com` email. Both are free tier.

---

## Why this stack

| | Cloudflare Pages + Access | Static-host free tier |
|---|---|---|
| Bandwidth | Unlimited | 100 GB/mo |
| Builds | 500/mo | 300/mo |
| Custom domains | 100 | 1 |
| Auth gate | Cloudflare Access (50 users free) | Separate vendor needed |
| Vendor relationship | Single vendor for hosting + auth | Multiple vendors |

Cloudflare Access free tier covers up to 50 users via the Zero Trust dashboard. STA Phase 1 cohort is 5 users; staff at full org is 11. Plenty of headroom on the free tier.

---

## One-Time Setup (Adam, ~20 min)

### Part 1: Create the Cloudflare account (skip if you already have one)

1. Go to https://dash.cloudflare.com/sign-up
2. Sign up with your work email (`adamb@k12sta.com`).
3. Verify the email.

### Part 2: Deploy the hub to Cloudflare Pages

**Option A - Drag-and-drop (fastest, recommended for v1):**

1. In the Cloudflare dashboard, go to **Workers & Pages** → **Create** → **Pages** → **Upload assets**.
2. Project name: `sta-training-hub` (this becomes part of the URL: `sta-training-hub.adamb-1a4.workers.dev`).
3. Drag the entire `dist/` folder from `C:\Users\Adam\source\repos\training-kit-hub\dist\` into the upload area.
4. Click **Deploy site**.
5. Wait ~30 seconds. You'll get a URL like `https://sta-training-hub.adamb-1a4.workers.dev`.

**Option B - Git integration (recommended once stable):**

1. Push the `training-kit-hub/` folder to a git repo (use the existing `abaker421/school-tech-ai-system` private repo, or a dedicated repo if you want public-ish hosting).
2. In Cloudflare Pages → **Connect to Git** → select the repo.
3. Build settings:
   - Build command: (leave empty - no build needed)
   - Build output directory: `C:\Users\Adam\source\repos\training-kit-hub\dist`
   - Root directory: `/`
4. Save and deploy. Future pushes auto-deploy.

### Part 3: Set up Cloudflare Access (the auth gate)

This is the step that locks the site to `@k12sta.com` emails only. Without it, anyone with the URL can read everything.

1. In the Cloudflare dashboard, go to **Zero Trust** (it's in the left sidebar; if it's your first time there, you'll be prompted to choose a team name - use `school-tech` or similar).
2. Go to **Settings** → **Authentication** → **Login methods**.
3. Add **One-time PIN** as a login method (this is the simplest - users get a code emailed to them, no Google/Microsoft SSO setup needed).
4. Optionally also add **Google Workspace** if you want to wire up Google SSO. Requires admin console access to Google Workspace.

5. Go to **Access** → **Applications** → **Add an application** → **Self-hosted**.
6. Application name: `STA Training Hub`
7. Session duration: `24 hours` (so users don't re-auth every visit)
8. Application domain: `sta-training-hub.adamb-1a4.workers.dev` (or your custom domain if you've added one)
9. Path: leave blank to protect the entire site
10. Click **Next** → **Add a policy**.
11. Policy name: `STA staff only`
12. Action: **Allow**
13. Include: **Emails ending in** → `@k12sta.com`
14. Save the policy → save the application.

That's it. Anyone hitting the URL now sees a Cloudflare Access login screen. They enter their @k12sta.com email, get a one-time PIN, log in, and the site loads.

### Part 4: Test

1. Open `https://sta-training-hub.adamb-1a4.workers.dev` in an incognito/private window.
2. You should see the Cloudflare Access login.
3. Enter `adamb@k12sta.com`, get the PIN from your inbox, log in.
4. The hub should load.
5. Try a wrong email (e.g., `test@gmail.com`) and confirm it's rejected.

---

## Updating the Hub After Deploy

### Drag-and-drop method (Option A)

After editing `STA-Training-Hub.html`:

```bash
# Sync source to dist
cp "STA-Training-Hub.html" "dist/index.html"

# (If you also updated underlying training docs, re-sync those too)
# See MAINTENANCE.md for the per-doc sync commands
```

Then in Cloudflare Pages → your project → **Create deployment** → drag the updated `dist/` folder in. New deploy goes live in ~30 seconds.

### Git method (Option B)

Just commit and push. Cloudflare auto-deploys on push.

---

## Custom Domain (Optional)

If you want `training.k12sta.com` instead of `sta-training-hub.adamb-1a4.workers.dev`:

1. In Cloudflare Pages → your project → **Custom domains** → **Set up a custom domain**.
2. Enter `training.k12sta.com` (or whatever subdomain you want).
3. Cloudflare gives you a CNAME record to add.
4. Add the CNAME record in your DNS provider (wherever k12sta.com is managed).
5. Wait for propagation (usually under an hour).
6. **Re-check the Cloudflare Access application's Application domain** - update it to match the new custom domain.

If `k12sta.com` is already on Cloudflare DNS, step 4 is automatic.

---

## Adding More Users to Cloudflare Access

The current policy includes all `@k12sta.com` emails automatically - no per-user setup. Anyone in that domain can log in.

If you need to add external users (e.g., a contractor or auditor):

1. Zero Trust → **Access** → **Applications** → STA Training Hub → **Edit**.
2. Add a new policy or edit the existing one.
3. Add their specific email to the **Include** rules.

If you want to *exclude* certain @k12sta.com addresses (rare but possible):

1. Same place; add an **Exclude** rule with the specific email.

---

## Free Tier Limits to Watch

Cloudflare Pages free tier (per https://www.cloudflare.com/plans/developer-platform/):

- **Unlimited** static asset requests (no bandwidth cap)
- **500 builds per month** (only matters if you're on Git-integrated deploys with lots of pushes)
- **100 custom domains**
- **20,000 files per project** (we're at ~30 - lots of headroom)
- **25 MiB max per file** (our biggest is the docx files, all under 200 KB - fine)

Cloudflare Access (Zero Trust free tier):

- **50 users free** (we're using 5-11 - fine)
- **Unlimited applications**

If usage ever becomes a concern, Cloudflare's first paid tier starts at $5/mo. But you're nowhere near the limits.

---

## Rollback

If a deploy breaks the app:

1. Cloudflare Pages → your project → **Deployments**.
2. Find the last good deployment.
3. Click the three-dot menu → **Rollback to this deployment**.

Done. Takes about 10 seconds.

---

## Known deploy gotcha: `_redirects` file

**Do not add a `_redirects` file to `dist/`.** The 2026-05-21 deploy failed with `[code: 10021] Infinite loop detected` because Cloudflare Workers Assets (the architecture CF Pages currently deploys under) interprets the conventional SPA fallback `/* → /index.html 200` as a potential infinite redirect loop and rejects the deploy entirely.

The hub does NOT need SPA fallback - it has no client-side routing. Every doc card link opens a real static file (`/docs/[slug].html` or `/files/[slug].docx`) and the root `/` naturally serves `index.html`. Just leave `_redirects` out of `dist/`.

If you need redirect rules in the future (e.g., to rename a URL while preserving inbound links), use exact-match patterns rather than wildcards:

```
# OK - exact source, different target
/old-path.html  /docs/new-path.html  301

# NOT OK - wildcard that includes the target
/*  /index.html  200
```

## Troubleshooting

**Users see a 404 when clicking a card.** The asset file isn't in `dist/docs/` or `dist/files/`. Check the path in `window.TRAINING_DATA.docs[id].file` matches what's actually in dist.

**Cards load but the search box doesn't work.** Open the browser console. Likely a JavaScript error in the inline `<script type="module">` block in the source HTML. The browser console reports the file and line number directly (there is no Babel transpile step anymore - the app is plain vanilla JS).

**Cloudflare Access loop (users keep getting asked to log in).** Cookie issue - usually third-party cookies blocked in the browser. Have them try a different browser or enable third-party cookies for `cloudflareaccess.com`.

**Whole app blank, no errors.** The app is a single self-contained file with **no external scripts loaded at startup** - React and Babel were removed (2026-06-01 rewrite). If the page is blank, open the console and look for a syntax/runtime error in the module script. Check the Network tab only for the local assets (`index.html`, the Roboto font CSS); there are no app-framework CDN requests to fail.

**A `.md` or `.docx` doc won't open (other docs are fine).** Those two types are the only ones that fetch an external library, and they load it lazily on first open: `marked` (from jsdelivr) for markdown, `mammoth` (from cdnjs) for Word docs. Both are pinned with Subresource Integrity (SRI) hashes. If the CDN is down, or a future version bump changes the file without updating the `integrity=` hash in the source, the browser blocks the script and only `.md`/`.docx` viewing breaks - HTML and PDF docs are unaffected. Re-generate the hash with `curl -sL <url> | openssl dgst -sha384 -binary | openssl base64 -A` and update the `MARKED` / `MAMMOTH` constants in the source.

---

## What Cloudflare Access Logs

Cloudflare's Zero Trust dashboard shows every login attempt with email, IP, country, and timestamp. Useful if you ever need to investigate suspicious access. No conversation content or session data is logged - just the auth event.

---

## Future Considerations

- **Audit trail of what each user opened.** Not built in - Cloudflare logs auth, not asset access. If you want per-doc analytics, options are (a) add a lightweight analytics script like Plausible (privacy-friendly, $9/mo) or (b) instrument the app to log opens to a Cloudflare Worker that writes to KV.
- **Search ranking by recency.** Currently search is exact-match across title/desc/tags. If the doc set grows past ~30, consider adding fuzzy search via Fuse.js (CDN, no build step).
- **Multi-language.** If STA ever adds non-English staff, the labels and audience descriptions in `window.TRAINING_DATA` are the translation points. The HTML doc files would need their own translation pass.
- **Mobile bookmark.** Once users save the URL as a home-screen icon, the `manifest.json` makes it look like a native app. No additional setup needed.
