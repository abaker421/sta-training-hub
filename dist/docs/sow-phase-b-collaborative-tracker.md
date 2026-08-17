# STA Project Tracker - Phase B (Shared Collaborative Version) - Statement of Work

**Status:** Draft for review. Created 2026-06-05.
**Owner:** Adam Baker.
**Builds on:** Phase A (shipped 2026-06-05) - read-only Projects tab in the gated STA Support Hub, fed by a static `data/project-data.json` generated from the Work PA's `agenda-state.md`.
**Planning doc, not a build prompt.** Build prompts come after Adam approves scope and the open decisions (Section 11) are resolved. A Deep Research commission (Section 3 / B0) is a recommended prerequisite - the KB has no module on Cloudflare D1/Workers or multi-agent write contracts.

---

## 1. Purpose

Turn the read-only Projects tab into a **shared, writable project tracker** that STA staff (Adam, Chris, Tyler, Andy, and any `@k12sta.com` user) edit directly, and that **multiple AI agents** read from and write to through a single defined interface. The tracker becomes the **source of truth** for STA project status: the Work PA's meeting-ingest writes into it, and the hub tab + daily report read from it.

A successful end state: Chris updates a SchoolTRAK item's status in the tab; it persists and the others see it on refresh. The Work PA, after the Friday Cruxlab call, writes the week's changes into the same store through the MCP - attributed, without clobbering Chris's manual edits. A future agent (or another employee's agent) does the same through the identical contract.

## 2. Architecture decision (recommended, pending approval)

**Backend = Cloudflare D1 (serverless SQLite) + Cloudflare Pages Functions, with identity from Cloudflare Access.** The agent interface = a thin **MCP server** over that API, plus a written **AI Interaction SOP**.

Why D1 + Pages Functions over the alternatives:

- **Same platform as the hub.** The hub is already a Cloudflare Pages app gated by Cloudflare Access. Pages Functions (Workers under the hood) bind to D1 natively - no new vendor, no second auth system, no connection pooling. ([D1 overview](https://developers.cloudflare.com/d1/), [Pages + D1](https://www.stackcompat.dev/cloudflare-pages-with-sqlite/))
- **Identity is already solved.** Access injects a signed `Cf-Access-Jwt-Assertion` JWT on every request; a Pages Function reads the user's email (and group claims) from it to enforce roles and attribute writes - no separate login. The JWT must be validated server-side. ([Access on Pages Functions](https://developers.cloudflare.com/pages/functions/plugins/cloudflare-access/), [Validate JWTs](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/))
- **Production-ready and right-sized.** D1 went GA in late 2024; SQLite semantics, edge reads, single-primary writes, built-in backups. The free tier (enforced since Feb 2025) comfortably covers a handful of internal users; monitor write limits only. ([D1 limits](https://developers.cloudflare.com/d1/platform/limits/), [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/))

Alternatives considered and why not (for the canonical build):

- **Google Sheet as the store** - fastest bridge, but the team would edit in Sheets (not the tab), write-back needs a separate Google API integration, and concurrency is weak. Good throwaway MVP, wrong long-term home.
- **Trello-backed** - reuses an existing tool but surrenders custom UI/fields and is really just "use Trello," which Adam already rejected as the home.
- **Supabase / Firebase** - capable, but a new platform off Cloudflare with its own auth - more surface than 4 users need when D1 + Access is already under the hub.

## 3. Prerequisite - Deep Research commission (Phase B0)

**Status: COMPLETE (2026-06-05).** The 6 modules landed at `knowledge-base/sta/ai-platform/cloudflare-d1-multi-agent-backend/` (+ `_summary.md`) and the KB index entry is in (STA scope, update-sensitive, monthly). B1/B2/B3 build prompts can now be grounded in these modules, and the Section 16 open decisions should be resolved against them.

This commission was needed because the KB had **no module** on Cloudflare D1/Workers or on multi-agent write contracts (confirmed in the Phase A drift/KB check). Before B2/B3 build, commission a Deep Research module covering: D1 schema design + migrations for a small multi-writer app; Pages Functions binding patterns; Cloudflare Access JWT validation and group-to-role mapping; optimistic-concurrency / conflict handling for 3-4 simultaneous writers (human + agents); and MCP-server-over-HTTP-API patterns with per-operator auth. The Architect recommends the topic; Deep Research runs it; this SOW's build prompts get grounded in the result. (Mirrors how the Wren MCP SOW was grounded in the `wren-mcp-server` commission.)

## 4. Scope

### In scope (Phase B)

- A **D1 schema** for projects, groups, open items, stage history, and timeline (Section 6).
- A **Pages Functions REST API** (read + guarded write) bound to D1 (Section 7).
- **Access-based auth + two roles** (admin / member), enforced server-side from the Access JWT (Section 8).
- **In-tab editing** for members: status, stage transitions, open-item add/complete, notes, timeline append. The existing Refresh button + periodic re-fetch stay (no realtime needed).
- An **MCP server** over the API so any Claude agent interacts through typed tools (Section 9).
- An **AI Interaction SOP / contract** doc every agent loads (Section 10).
- **Source-of-truth inversion:** D1 becomes canonical; the Work PA's ingest writes via the MCP; the hub tab and daily report read from the API (Section 9/12).

### Out of scope (Phase B - defer to a later SOW / backlog)

- Assignees, due dates, comments, change-history-as-a-feature - these come from **Salesforce** (case owner, comments) via a later integration, not rebuilt here.
- A "suggest-then-approve after meetings" agent-edit workflow (backlog) - B3 ships direct attributed writes; the approval gate is a fast-follow.
- Realtime/live multi-cursor updates (periodic + manual refresh is the confirmed requirement).
- The full "Support Hub" rebrand (separate, deferred).
- Non-`@k12sta.com` external access (the gate stays org-only; expandable later).

## 5. Tech stack

| Layer | Choice | Note |
|---|---|---|
| Datastore | Cloudflare D1 (serverless SQLite) | Native Worker binding; edge reads, single-primary writes |
| API | Cloudflare Pages Functions (Workers) | Same Pages project as the hub; `/api/*` routes |
| Auth / identity | Cloudflare Access (`@k12sta.com` SSO) | `Cf-Access-Jwt-Assertion` JWT -> email + groups; validate server-side |
| Frontend | Existing React-in-HTML Projects tab | Switch from static `data/project-data.json` fetch to the live `/api/projects` endpoint; Refresh button reused |
| Agent interface | MCP server over the REST API | Per-operator auth; typed tools (Section 9) |
| Repo | `sta-help-center-index` (hub) for the Pages Functions; MCP server in its own repo | Pages Functions live beside the app they serve |

## 6. Data model (D1, first cut)

Tables (refine during B1 against the DR):

- `projects` - `id`, `name`, `group` (`dev`|`ops`), `status`, `status_class`, `stage`, `stage_class` (nullable for ops), `statusline`, `what_it_is`, `sort`, `updated_at`, `updated_by`, `version` (for optimistic concurrency).
- `open_items` - `id`, `project_id`, `text`, `stage`, `stage_class`, `meta`, `done` (bool), `done_at`, `created_by`, `updated_at`, `version`.
- `stage_history` - `id`, `project_id`, `when_label`, `note`, `created_at`.
- `timeline` - `id`, `project_id`, `when_label`, `note`, `created_at`, `created_by`.
- `stage_legend` - static reference (Prelim/Dev/Post/Meetings) or kept in code.
- `audit` - `id`, `actor` (email), `actor_kind` (`human`|`agent`), `agent_name`, `action`, `entity`, `entity_id`, `before`, `after`, `at`. (Every write appends here - this is attribution + the human-edit-protection trail, not a user-facing comments feature.)

The Phase A `project-data.json` schema maps 1:1, so seeding D1 from the current feed is straightforward.

## 7. API surface (Pages Functions, first cut)

| Method + route | Auth | Purpose |
|---|---|---|
| `GET /api/projects` | member+ | Full tracker payload (groups, projects, items, timeline, legend) - what the tab renders |
| `GET /api/projects/:id` | member+ | One project |
| `PATCH /api/projects/:id` | member+ (content) / admin (structure) | Update status/stage/statusline; create/reorder is admin-only |
| `POST /api/projects/:id/items` | member+ | Add an open item |
| `PATCH /api/items/:id` | member+ | Edit/complete an item |
| `POST /api/projects/:id/timeline` | member+ | Append a timeline entry |
| `POST /api/projects/:id/stage` | member+ | Record a stage transition (writes stage + stage_history) |
| `GET /api/audit?project=:id` | admin | Read the attribution/audit trail |

All writes: validate the Access JWT, resolve email -> role, enforce, append to `audit`, bump `version` (reject on stale `version` -> optimistic-concurrency conflict). The tab can keep using the Refresh button to re-`GET /api/projects`.

## 8. Auth & roles

- **Gate:** Cloudflare Access, `@k12sta.com` only (already in place for the hub). Expandable later.
- **Identity:** server reads the validated Access JWT (`Cf-Access-Jwt-Assertion`) -> user email + group claims.
- **Roles (two tiers, confirmed 2026-06-05):**
  - **Admin (Adam):** everything, including project create/delete/reorder, schema, and system/agent config.
  - **Member (everyone else with a k12sta email; Chris as project lead):** edit project *content* - status, stage transitions, open items, notes, timeline - but not structure/schema/system. Chris has near-full content access by role, not a special case.
- Mapping email/group -> role lives server-side (a small allowlist or an Access group), never trusted from the client.

## 9. Agent interaction layer - MCP server (the new requirement)

The portal will be used by **multiple agents** (the Work PA now; other agents and other employees' agents later). They must all go through **one defined interface**, not ad-hoc edits. That interface is an **MCP server** over the REST API.

**MCP tools (model-controlled, read + guarded write):**

| Tool | Purpose |
|---|---|
| `tracker_get_projects` | Full current tracker (read) |
| `tracker_get_project` | One project (read) |
| `tracker_update_status` | Set a project's status / statusline |
| `tracker_set_stage` | Record a stage transition (Prelim/Dev/Post/Meetings) |
| `tracker_add_item` | Add an open item (with stage tag) |
| `tracker_complete_item` | Mark an item done |
| `tracker_append_timeline` | Append a dated timeline note |
| `tracker_get_audit` | Read recent changes (so an agent can see what humans changed before writing) |

**Hard contract for every tool call:** authenticate as the **operating user** (the agent acts with its operator's `@k12sta.com` identity, not a god account), so role enforcement + attribution work per-operator; every write carries `actor_kind=agent`, `agent_name`, and the operator email into `audit`; writes use the project's `version` for optimistic concurrency and **reject rather than clobber** on conflict.

**Build routing:** per The Architect's boundaries, the MCP server is built via the `mcp-builder` skill (and packaged appropriately - HTTP server beside the Pages app, or a thin client of the API), not authored inline here. This SOW defines the tool surface and contract; mcp-builder implements.

## 10. AI Interaction SOP (the "instructions" for agents)

A short, mandatory contract doc - a context file every agent that touches the tracker loads (and the spec the MCP enforces). It is the answer to "there needs to be a standard operating procedure for how AI interacts with it."

Rules:

1. **Write only through the MCP / API.** Never hand-edit the D1 store, the deployed HTML, or `agenda-state.md` as a backdoor. The MCP is the only write path.
2. **Authenticate as your operator.** Act with the human operator's `@k12sta.com` identity; respect that operator's role (members edit content; only Adam changes structure/schema/system).
3. **Attribute every write.** `actor_kind=agent`, agent name, operator email, timestamp - all land in `audit`.
4. **Never clobber a human edit.** Read current state (and recent `audit`) before writing; use optimistic concurrency (`version`); on conflict, re-read and reconcile or surface, never blind-overwrite.
5. **Stay in the field set.** Status, stage, items, notes, timeline only. No inventing assignees/due-dates/comments (that's Salesforce, later).
6. **Tag stages by the standard.** Use `stage-classification-standard.md` (Prelim/Dev/Post/Meetings); the three recurring dev meetings are always Stage 4.
7. **Cadence, not chatter.** Batch a meeting's changes into a coherent set of writes; don't thrash the store.
8. **The tracker is the source of truth.** After B3, ingest writes here, and the daily report/hub read from here - don't maintain a divergent copy.

**Build routing:** packaged as an uploadable/loadable context file via the appropriate context packager; referenced by a routing rule in every agent that touches the tracker (Work PA first).

## 11. Implementation phasing

| Phase | What | Rough effort |
|---|---|---|
| **B0** | Deep Research commission (Section 3) - de-risk D1/Workers/Access + multi-agent contract | DONE 2026-06-05 (6 modules in KB) |
| **B1** | D1 schema + read API (`GET /api/projects`); Projects tab reads the live endpoint instead of the static feed; seed D1 from current `project-data.json`. Read path proven first. | DONE 2026-06-06 end-to-end. Backend: PR #8, deploy `ecc15454`. Tab cutover: PR #9, deploy `e7146573` - tab now fetches live D1 with baked fallback. Signed-in prod verified (8 projects). |
| **B2** | Write API + Access-identity roles; in-tab editing for members; `audit` + optimistic concurrency | Backend DONE + PROD-VERIFIED 2026-06-06 - PR #10 merged (`8ed6596`). Live prod round-trip passed: compare-and-set bumps version, 409 on stale write, soft-delete, role + host gates, and 2 audit rows attributed to a genuine Access JWT identity (`adamb@k12sta.com`, human). Only remaining B2 piece: front-end cutover PR to ship the edit UI (the generator already has it). |
| **B3** | MCP server + AI Interaction SOP; migrate the Work PA ingest to write via the MCP; flip source-of-truth (daily report reads D1) | SCOPED 2026-06-06 -> `future-enhancements/b3-build-prompt.md`. **B3a DONE + PROD-VERIFIED 2026-06-06** (PR #12, deploy `f55ce3a0`): single-project GET + service-token operator delegation live; live token test passed (delegated read/write 200s, non-allowlisted operator 403, audit rows `actor_kind=agent` / `agent_name=work-pa` / `actor_email=adamb@k12sta.com`). Cloudflare prep done: `work-pa-tracker` token (1yr), Service Auth policy, secret in `%USERPROFILE%\.sta-tracker\service-token.env`. B3b SCOPED 2026-06-06 -> `b3b-build-prompt.md` (TypeScript stdio server in NEW repo `source/repos/sta-tracker-mcp`, 7 `tracker_*` tools, service-token auth from the secrets file, 409 as structured conflict result, no delete tools, mcp-builder standards; cloudflared interactive path deferred to backlog). **B3c DONE 2026-06-06:** `ai-interaction-sop.md` written (blueprint root) - the seven-rule agent contract keyed to the `tracker_*` tools, with the write-loop quick reference and the routing-trigger line for wiring agents. **B3b DONE + PROD-VERIFIED 2026-06-06:** `sta-tracker-mcp` built (own repo, local commit `07e1e7e`, no remote; SDK pinned 1.29.0). All 7 `tracker_*` tools verified via Inspector + live stdio client: 8-project read, single-project read, write round-trip (item 1 v5->v7, restored), stale write -> structured `{conflict:true, current}` (no exception, no audit row), audit attribution `agent`/`work-pa`/`adamb@k12sta.com`. stderr-only logging, secret never in repo/logs/results. Registration command produced, not yet run. **B3d INSTRUCTIONS SHIPPED 2026-06-06:** reconciliation verified (no drift; D1 == agenda-state at the 2026-06-05 generation). Work PA bumped to **v2.0** (major): D1 canonical for project state via `tracker_*` tools + SOP routing; agenda-state.md split (briefing-state stored there; Active Projects = generated mirror, Step 5a/5b/5c); Daily Agenda reads `tracker_list_projects` with mirror fallback; hub-feed regeneration RETIRED; NEVER ACT sanctioned-exception carve-out; scheduled-run write fallback (pending-tracker-updates, never a side door); truncation-check backfill. **B3d DONE + VERIFIED 2026-06-07 - PHASE B COMPLETE.** Wiring done: desktop-config MCP registration (machine-level; tools confirmed visible in Cowork sessions), scheduled briefing task + morning-briefing-prompt.md updated to v2.0 by the Work PA itself, live verification green in a fresh Work PA session (all 7 tools, live D1 read, SOP write-loop confirmed, Active Projects mirror regenerated with briefing-state untouched). End-to-end write also proven from a Cowork session (item 1 v7->v9 toggle/restore, attributed). v2.1 path fix from the verification finding (full `The Architect/...` paths). Backlog: B4 candidates (briefing-state in D1, Salesforce, suggest-then-approve), multi-machine MCP setup, token rotation ~2027-06. |
| **B4 (later/backlog)** | Salesforce integration (owner/comments); suggest-then-approve agent-edit flow | separate SOW |

Read-before-write discipline (B1 before B2) mirrors the Wren MCP SOW: prove the read path against real data before any tool can mutate state.

## 12. Source-of-truth migration

Today: `agenda-state.md` (Work PA) -> static `project-data.json` -> hub reads it. After B3: **D1 is canonical.** The Work PA's dev-call ingestion writes structured changes into D1 via the MCP; the hub tab and the daily report both read the D1-backed API. `agenda-state.md` either becomes a generated human-readable mirror or is retired. Migrate in B3, not before - B1/B2 can run with D1 seeded from the static feed while `agenda-state.md` still leads, so nothing breaks mid-build.

## 13. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Multi-agent / human write conflicts (clobbering) | Medium | High | Optimistic concurrency (`version`); read-before-write; `audit` trail; agents reject-on-conflict, never blind-overwrite (SOP rule 4) |
| Prompt-injection via agent inputs into the store | Medium | Medium | Narrow tool surface; server-side validation; role limits; audit trail |
| Access JWT not validated -> spoofable identity | Low | High | Always validate `Cf-Access-Jwt-Assertion` server-side; never trust client headers |
| Scope creep into a full PM tool | Medium | Medium | Hold the minimal-field line; assignees/comments are Salesforce's job |
| D1 free-tier write limits | Low | Low | 4 users is well under; monitor; paid tier is cheap if needed |
| Source-of-truth inversion breaks the daily briefing | Medium | High | Migrate in B3 only; keep `agenda-state.md` leading through B1/B2; cut over behind a verified read path |
| KB gap on D1/Workers/multi-agent contracts | High (now) | Medium | B0 Deep Research commission before B2/B3 build |

## 14. Acceptance criteria (Phase B)

- A member edits a project's status/item in the tab; it persists to D1 and shows to others on Refresh.
- Role enforcement holds: a member cannot create/delete projects or change schema; Adam can.
- The Work PA writes a meeting's changes via the MCP; the tab and the daily report both reflect them; every write is attributed in `audit`.
- No agent (or human) write silently overwrites a conflicting edit - conflicts are rejected/surfaced.
- Identity is real: writes are attributed to the actual `@k12sta.com` operator from a validated Access JWT.
- The AI Interaction SOP exists, is loaded by every tracker-touching agent, and the MCP enforces its hard rules.

## 15. Dependencies

- Phase A shipped (done) - the tab, the gate, the Cloudflare Pages project.
- Cloudflare Access already gating the hub (confirmed).
- B0 Deep Research commission grounding the D1/Workers/Access + multi-agent build.
- `mcp-builder` skill for the MCP server; a context packager for the SOP doc.
- `stage-classification-standard.md` (exists) - the stage vocabulary the API/MCP enforce.

## 16. Decisions

**Confirmed (2026-06-05):**
1. Backend = **Cloudflare D1 + Pages Functions + Access identity** (this SOW's recommendation, pending Adam's sign-off).
2. Two roles: **Adam admin / everyone-else member (content)**; gate stays `@k12sta.com`.
3. **Minimal fields**; assignees/comments/owner/history come from **Salesforce later**.
4. **Periodic + manual refresh** (no realtime) - simpler API, reuse the existing Refresh button.
5. **Tracker becomes the source of truth** (inversion in B3).
6. **Multi-agent access goes through one MCP + a written SOP** - no ad-hoc agent edits (the new requirement, 2026-06-05).

**Resolved against the B0 modules (2026-06-05):**
1. **Role mapping = server-side allowlist** (Module 3). A tiny `ADMINS` set in the Function assigns admin (Adam) vs member from the validated email - simplest at 4 users / 1 admin, no extra network call. Promote to Cloudflare Access groups only if membership management outgrows a one-line code change. (Reverses the earlier "Access group" lean, per the research.)
2. **Headless Work PA auth = Cloudflare Access service token + bounded operator delegation** (Modules 3 + 5). The scheduled job authenticates with a service token (Client ID/Secret + a Service Auth policy) and sends `X-Operator-Email` + `X-Agent-Name`; the API trusts the service token only for authentication, then checks the claimed operator against a server-side allowlist of operators that token may act for, looks up that operator's role, and audits the write as `actor_kind=agent`. Never let a header alone set the operator.
3. **`agenda-state.md` survives as a generated human-readable mirror** after B3 (for the Cowork artifact + continuity); D1 is canonical.
4. **MCP hosting = local stdio server first** (Module 5). A stdio MCP server on Adam's machine holds the operator credentials locally and calls the gated API over TLS - no public deploy, no second Access app. Move to a remote Streamable HTTP MCP only when other employees' agents need the tools without each running a local process, and defer that until the MCP auth spec settles after the 2026-07-28 RC.

## 17. Changelog

- 2026-06-05 - Drafted. DB choice (Cloudflare D1 + Pages Functions + Access) recommended and grounded in current Cloudflare docs; agent-interaction layer (MCP server + AI Interaction SOP) added as a first-class component per Adam's multi-agent requirement; B0 Deep Research commission flagged as a prerequisite (KB gap).
- 2026-06-05 - B0 Deep Research commission COMPLETE: 6 modules + `_summary.md` landed at `knowledge-base/sta/ai-platform/cloudflare-d1-multi-agent-backend/`, KB index entry added. Cleared for B1.
- 2026-06-05 - Section 16 open decisions RESOLVED against the B0 modules (allowlist roles; service-token + bounded-operator-delegation for the headless Work PA; agenda-state.md as a generated mirror; local stdio MCP first). B1 build prompt written: `future-enhancements/b1-build-prompt.md` (D1 schema reconciled to the live project-data.json shape, read API, Access read-gate, seed, tab swap - read path only, no writes).
- 2026-06-06 - B2 scoping STARTED. `future-enhancements/b2-build-prompt.md` written (paste-ready CC prompt), grounded in module-04 (write contract), module-03 (roles), module-02 (API) and the shipped B1 backend (native Web Crypto identity object, `audit`/`version`/`deleted_at`/`done` already in schema -> no migration needed for B2). Four decisions locked: (1) preview-DB isolation = host-gate writes to `CANONICAL_WRITE_HOSTS` (resolves the B1-surfaced prerequisite); (2) capability matrix (member edits content, admin edits structure); (3) the module-04 write contract (compare-and-set on `expected_version`, 409 with current row, audit per mutation, soft-delete); (4) required B1-payload extension to emit `id` + `version` per row so the client can send `expected_version`. Scope = human writes + in-tab member editing; agent/MCP path deferred to B3. **[CONFIRM]** the canonical write host(s) before build.
- 2026-06-06 - B1 backend SHIPPED and live in production (PR #8 squash-merged to `main`, deploy `ecc15454`). Both remote D1s migrated + seeded (8 projects / 20 open items). **Auth-approach change vs this SOW's assumption:** Sections 8/10 assumed the `@cloudflare/pages-plugin-cloudflare-access` plugin + `Cf-Access-Jwt-Assertion` header. The Pages project has **no build command** (no `npm install` at deploy), so the plugin could not resolve at the edge. B1 instead validates the Access JWT with **native Web Crypto** (`functions/_lib/access.js`): same four checks (RS256/JWKS, `aud`, `iss`, `exp`), zero external imports, preserves the repo's no-build deploy, and gates `/api/*` in our own code as defense-in-depth on top of the edge Access gate. **B2/B3 build on the plugin-free verifier, not the plugin.** Verified: signed-out -> 302 SSO (canonical prod) / 403 (deploy alias). Two B1-surfaced items added to `backlog.md`: preview-DB isolation under the flat binding namespace (a B2 write-path prerequisite) and Access fail-open -> consider fail-closed.
- 2026-06-06 - B2 COMPLETE end-to-end. Write backend merged (PR #10, `8ed6596`) and PROD-VERIFIED via a live signed-in round-trip: compare-and-set bumped version 1->2->3, `done` toggled + restored, a stale `expected_version` returned `409` with the current row, and 2 audit rows landed attributed to a genuine Access JWT identity (`adamb@k12sta.com`, `actor_kind=human`). Payload extended to emit `id`/`version`/`done` per item. Edit-UI cutover shipped (PR #11, `29867e3`, deploy `bbe19fee`): in-tab editing live for signed-in `@k12sta.com` users (inline project/item edit, done checkbox, add-item/timeline, admin-only create/delete, 409 reconcile banner), `GET /api/me` returns the identity for UI role tailoring. Canonical write host confirmed = `sta-help-center-index.pages.dev` (no custom domain yet; follow-up logged in backlog).
- 2026-06-06 - B3 SCOPED. `future-enhancements/b3-build-prompt.md` written, grounded in module-05 (MCP over API + per-operator auth) + module-04 (write contract). Decisions: local stdio MCP first (remote HTTP deferred past the 2026-07-28 MCP spec RC - the fastest-staling area); MCP wraps the B2 REST API (no DB access); per-operator auth via cloudflared (interactive) + service token with bounded operator delegation (headless); D1 becomes canonical with `agenda-state.md` as a generated mirror; MCP server build routed to `mcp-builder` (not inline) per the skill boundary; the AI Interaction SOP written as a context doc. Sub-phases B3a (API additions: single-project GET + service-token operator delegation in middleware), B3b (MCP stdio server), B3c (SOP), B3d (Work PA migration + source-of-truth inversion). Manual Cloudflare steps flagged (service token + Service Auth policy + `SERVICE_TOKEN_OPERATORS` allowlist).
- 2026-06-07 - **PHASE B COMPLETE.** All sub-phases shipped and verified live: B3a (PR #12), B3b (`sta-tracker-mcp`, 7 tools), B3c (`ai-interaction-sop.md`), B3d (Work PA v2.0/v2.1 - D1 canonical, mirror flip, hub-feed retired, scheduled-task prompts updated). Final state: one shared D1 store; humans edit via the gated hub tab, agents write via audited per-operator MCP tools under the SOP; conflicts rejected (409/compare-and-set), every write attributed (`audit`); daily briefing + hub tab read the same source. Drift fix applied to the system map (Projects tab note: read-only -> editable/D1-backed) - dist sync + PR via the hub push prompt.
