# Drift Check Procedure - Training Doc Per-Change Drift Check (Mechanism 1)

**Purpose:** When The Architect's own `instructions.md` changes, when any flagship project's `instructions.md` named in training docs changes, or when `context-agent-registry.md` gets an add/deprecate/rename, this procedure runs as the lightweight per-change drift check (Mechanism 1 of The Architect's TRAINING DOC DRIFT CHECK).

**Source:** Extracted from The Architect's `instructions.md` in v5.0 compaction (2026-05-03). The Architect references this file from its own TRAINING DOC DRIFT CHECK section via Pattern A framing.

---

## When this fires

The Architect itself runs this procedure. Triggers:

- Any change to The Architect's own `instructions.md`.
- Any change to a flagship project's `instructions.md` named in training docs.
- Any add/deprecate/rename in `context-agent-registry.md`.

**Skip exemption:** Pure-internal changes (typo fix, formatting tweak, comment update) skip this procedure.

---

## Scan root (read this before running any grep)

The authoritative scan root is the **served** hub content, not an upstream authoring folder:

```
C:\Users\Adam\source\repos\training-kit-hub\dist\docs\
```

plus the hub source file itself for card titles, descriptions, and check questions:

```
C:\Users\Adam\source\repos\training-kit-hub\STA-Training-Hub.html
```

**Why this matters.** Until 2026-08-19 this procedure scanned an authoring folder that held 19 files, while `dist\docs\` serves 92. The codebase guide, the scheduled-tasks reference, every `skill-*.html` and every tool brief exist **only** in dist. Scanning the smaller folder returned "no drift found" on documents it had never opened - a false clean. Always scan the served set.

Card text lives in `window.TRAINING_DATA` inside `STA-Training-Hub.html` and is served to users as card titles, `desc` strings, and check questions. A doc can be correct while its card is stale, so the card fields are part of the scan, not an afterthought.

`dist/index.html` is a byte-identical copy of `STA-Training-Hub.html`. Scan the source; do not treat the copy as a second finding.

---

## Procedure

1. Identify the changed concept(s). For an `instructions.md` edit, this is the section name, rule name, or behavioral phrase that was modified.

2. Search the served set for references to the changed concept:

   ```
   grep -rln "[changed-concept]" "dist/docs/" "STA-Training-Hub.html"
   ```

   This finds references in the served HTML and `.md` files and in the card data.

3. For `.docx` files, grep cannot read directly. Extract text first:

   ```
   docx2txt [file] - | grep [pattern]
   ```

   or:

   ```
   python3 -c "import docx; print('\n'.join([p.text for p in docx.Document('[file]').paragraphs]))" | grep [pattern]
   ```

   Apply to the `.docx` files actually served from `dist\files\`:

   - `ai-acceptable-use-policy.docx`
   - `ai-restricted-data-reference-guide.docx` - **in scope for mechanical drift, exempt for content.** Scan it; see the rule below.
   - `ai-rollout-plan.docx`
   - `sta-salesforce-org-intake.docx`

   Each of these is also pre-converted to a styled HTML copy in `dist\docs\` by
   `convert-docx-to-html.py`. The HTML copy is what users read, so a `.docx` fix is not
   shipped until the matching `dist\docs\[slug].html` has been regenerated.

4. Categorize findings:

   - **Mechanical fixes** (auto-apply): renames, version numbers, path corrections, additions to "what's new" lists.
   - **Judgment calls** (surface to Adam with Options a/b/c): structural rewrites, contested changes, substantial new sections.

5. Auto-apply mechanical fixes directly via Edit. Surface judgment calls to Adam in chat with three options.

6. When a doc changes, bump the matching card's `updated:` field in the same pass. A doc edit that leaves the card date stale is an incomplete fix, not a completed one.

7. Defer log: any items deferred for Adam's review later are written to `The Architect/training-drift-log.md`.

---

## Out of scope

**The restricted-data guide is a split case, not an exemption.** Earlier passes read its entry here as "skip this file entirely." That is wrong, and it let mechanical drift accumulate in a document staff are required to read. The rule is:

| | Status | Examples |
|---|---|---|
| **Mechanical drift** | **IN SCOPE - scan it** | Tool and agent names, version numbers, links, file paths, references to retired tools, section cross-references, dates |
| **Content** | **EXEMPT - do not audit** | The policy substance, the data classifications, the decision rules, the worked examples |

So: if the guide names a tool that has been renamed or retired, fix it. If it points at a moved path, fix it. If you disagree with how it classifies a data type, that is not yours to change - raise it with Adam as a policy question, never as a drift fix.

Genuinely out of scope:

- `project-blueprints/` folders - working files, not training materials.
- `_Evaluations and Assessments/` - historical artifacts.

---

## Relationship to Mechanism 2 (Final-Version Audit)

Mechanism 1 (this procedure) runs on every change. Mechanism 2 invokes the `training-doc-auditor` skill when a final version of any prompt or agent has been decided (project transitions Draft to Active). The two are complementary: this procedure is fast and catches obvious drift; the audit is thorough and catches drift keyword-grep misses.

---

**Last updated:** 2026-08-19 (scan root repointed to the served `dist\docs\` set + card data; `.docx` apply-to list corrected to the files actually served; card-date bump added as step 6).

<!-- EOF -->
