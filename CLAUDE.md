# CLAUDE.md - training-kit-hub

See @README.md for what this project is and @MAINTENANCE.md for the source/dist
sync and deploy procedure.

## Deploy (push to main)
`main` is the deploy branch - Cloudflare Pages auto-deploys from `origin/main`
within ~60s of a push. Direct pushes to `main` are the normal workflow (no
branch protection and no CI are configured on this repo). After editing, sync
`dist/index.html`, commit, and `git push origin main`. See @MAINTENANCE.md for
the full source/dist sync + deploy procedure.
