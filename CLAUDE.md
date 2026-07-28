# CLAUDE.md - training-kit-hub

See @README.md for what this project is and @MAINTENANCE.md for the source/dist
sync procedure and @DEPLOY.md for the Cloudflare setup.

## Deploy
- Cloudflare Pages deploys from the GitHub remote `origin/main` (repo:
  `abaker421/sta-training-hub`), not from the local filesystem. A local `dist/` sync
  alone does NOT update the hosted hub - the change has to reach `main` on GitHub,
  and Pages picks it up within ~60s of the merge.
- Always edit `STA-Training-Hub.html` first, then sync `dist/index.html`. Never edit
  `dist/index.html` as the source of truth.
- After any source `.docx` edit, re-run `convert-docx-to-html.py` to rebuild
  `dist/docs/*.html`.

## Branching (main is protected - PR only)

`main` is protected: direct pushes are rejected. **Never run `git push origin main`.**

1. `git checkout main && git pull origin main` - start from an up-to-date main
2. `git checkout -b <type>/<slug>` - branch BEFORE staging, so local `main` never diverges
3. edit, then `git add -- <explicit paths>` - never `git add -A`
4. `git commit -m "<message>"`
5. `git push -u origin <branch>`
6. `gh pr create --base main --fill`
7. `gh pr checks <branch> --watch` - wait for the required checks
8. `gh pr merge <branch> --squash --delete-branch`
9. `git checkout main && git pull origin main`

Never merge while a required check is failing or pending, and never disable a check to
force a merge through - stop and report instead.

Both the edited source and the synced `dist/` file go in the same PR - a merge that
ships one without the other publishes a hub that disagrees with its source.
