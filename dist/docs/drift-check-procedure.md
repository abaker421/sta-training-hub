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

## Procedure

1. Identify the changed concept(s). For an `instructions.md` edit, this is the section name, rule name, or behavioral phrase that was modified.

2. Search training materials for references to the changed concept:

   ```
   grep -rln "[changed-concept]" "Training Materials/"
   ```

   This finds references in HTML and .md files.

3. For .docx files, grep cannot read directly. Extract text first:

   ```
   docx2txt [file] - | grep [pattern]
   ```

   or:

   ```
   python3 -c "import docx; print('\n'.join([p.text for p in docx.Document('[file]').paragraphs]))" | grep [pattern]
   ```

   Apply to: `AI-System-Operations-Agent-SOW.docx`, `AI Rollout Plan.docx`, `AI Acceptable Use Policy.docx`.

4. Categorize findings:

   - **Mechanical fixes** (auto-apply): renames, version numbers, path corrections, additions to "what's new" lists.
   - **Judgment calls** (surface to Adam with Options a/b/c): structural rewrites, contested changes, substantial new sections.

5. Auto-apply mechanical fixes directly via Edit. Surface judgment calls to Adam in chat with three options.

6. Defer log: any items deferred for Adam's review later are written to `The Architect/training-drift-log.md`.

---

## Out of scope

- `AI Restricted Data Reference Guide.docx` - sensitive content not subject to drift check.
- `project-blueprints/` folders - working files, not training materials.
- `Evaluations/` - historical artifacts.

---

## Relationship to Mechanism 2 (Final-Version Audit)

Mechanism 1 (this procedure) runs on every change. Mechanism 2 invokes the `training-doc-audit` skill when a final version of any prompt or agent has been decided (project transitions Draft to Active). The two are complementary: this procedure is fast and catches obvious drift; the audit is thorough and catches drift keyword-grep misses.

---

**Last updated:** 2026-05-03 (v5.0 extraction).
