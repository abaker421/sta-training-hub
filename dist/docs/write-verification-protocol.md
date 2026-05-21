# Write Verification Protocol

**Origin:** 2026-05-02 truncation crisis - three production `instructions.md` files were found mid-word truncated with no backups available.
**Encoded in:** The Architect v4.17 BEHAVIOR GUIDELINES > "At save time and confirmation gates" > "Post-write verification gate."
**Audience:** Adam, and any agent operator working in this workspace.

This document is the diagnostic record and the operational reference for preventing silent file truncation in agent-driven file edits. The Architect's instructions.md encodes the protocol as a behavioral rule; this document explains the why.

---

## Section Map

| Section | What it covers |
|---|---|
| The Crisis | What happened 2026-05-02 - three truncated production files, no backups |
| Diagnostic Findings | Phase 1 evidence from controlled experiments - what reproduced, what did not |
| Root Cause Hypothesis | Why files truncate mid-word during agent-driven saves |
| The Verification Protocol | The save-time discipline - Read after every Write, check the closer, retry once, surface on second failure |
| Mitigation Strategies | Chunked Edit-append for large files, surgical Edits for revisions, output-budget awareness |
| Recovery Procedures | What to do when truncation IS detected - reconstruction sources, changelog framing, Adam review |
| Bash Mount Staleness | Why bash cannot be used for write verification - empirical observation |
| References | Related rules in The Architect, related skills, related documents |

---

## The Crisis

On 2026-05-02 morning, Adam discovered three project `instructions.md` files in the workspace had silently lost content during prior session saves. The most diagnostically clear case was `project-blueprints/work-personal-assistant/instructions.md`, which ended mid-word at the string `"I just wanted to share s` - cutting the word "share" in two and leaving the entire EXAMPLES section incomplete (only Example 1 plus the start of Example 2, instead of the v1.1-designed five examples) and the entire NEVER section absent. Two other files were suspected truncated and required investigation:

- `project-blueprints/_Projects/ai-advisor-proj/instructions.md` - Adam believed the file content matched v1.10 even though the version comment said v1.14. On verification, the file turned out to be intact at v1.14 - the chat-client autolink corruption in the form Adam was viewing it through had created the false impression of mismatch.
- `project-blueprints/sta-security-advisor/instructions.md` - Restated hard rules section appeared to end with only two rules where the project's Constraints section had four equivalent items. The file ended cleanly at a sentence boundary (not mid-word) but the two missing rules were a strong signal of section-tail truncation.

Two prior truncation incidents were already documented in the workspace itself: `_run-tracker-deep-research-master-2026-05-01.md` mentions a Prompt-10 truncation that required reconstruction during the Deep Research run; The Architect's own `instructions.md` v4.14 had a SECTION WEIGHT REFERENCE appendix that was truncated mid-line and was repaired in v4.15. So this was the third confirmed-or-suspected occurrence in the workspace, not an isolated event.

**Critical context: no backups existed.** Every file save by the agent was a one-shot opportunity - any silent loss was unrecoverable. Adam's directive at the start of the diagnostic session was unambiguous: "We must fix the further truncation issue before fixing the files themselves. This cannot continue."

That directive shaped the diagnostic order: prove that current write operations are reliable, establish a verification protocol that detects truncation post-save, and only then proceed to reconstruct lost content.

---

## Diagnostic Findings (Phase 1)

Six controlled experiments produced the following evidence:

**1. Bash mount staleness for in-session writes (high confidence).** When a file is modified via the Edit tool during a session, the bash-side view of that file remains frozen at the pre-Edit state for the rest of the session. An Edit confirmed via the Read tool to have appended new content (with unique markers and increased line count) showed the original byte count and missing markers when checked via `ls -la`, `tail -c`, `grep`, and `wc -l` through bash for at least 3 seconds after the edit. This means bash CANNOT be used to verify in-session writes - only the Read tool reflects the current on-disk state. (Observed empirically; the staleness window may extend longer than the brief delay tested.)

**2. Write tool itself does not truncate at small or moderate sizes.** A 2KB synthetic file (`test-02kb.txt`, 2204 bytes) and a 10KB synthetic file (`test-10kb.txt`, 10195 bytes) were each written via Write and verified intact via Read - exact byte count match, both header and footer end markers present. This rules out a tool-level character cap below 10KB.

**3. Edit tool does not truncate when adding moderate deltas.** A 1.5KB block was appended to the 10KB test file via Edit. Read tool confirmed all expected content present with the unique CHARLIE markers intact. This rules out a tool-level cap on Edit deltas at this scale.

**4. No simple file-size threshold for production truncation.** Truncated production files clustered at 13.9KB (work-personal-assistant), 13.8KB (sta-security-advisor), and 18.9KB (ai-advisor-proj, suspected). Intact production files exist at adjacent and larger sizes: personal-assistant at 13.5KB, task-scheduler at 16.7KB, deep-research at 58KB, the-architect itself at 90KB. A simple file-size threshold (e.g., "files over 14KB get truncated") cannot account for this distribution.

**5. Single-shot Write at 26KB is reliable in this session.** A synthetic stress test (`test-20kb.md`, 26015 bytes when written, 200 numbered lines plus headers, ECHO-20KB-START and ECHO-20KB-END markers) was written via Write and verified intact via Read - all 200 numbered lines present, both end markers present, file ends cleanly at the END MARKER. This is empirical proof that output budget can carry ~6,500 tokens of content into a single tool call without truncation in a normally-loaded session.

**6. Files built up through many Edit deltas remain intact at large sizes.** The Architect's own `instructions.md` is 90,234 bytes and intact - it was built up through dozens of small Edit operations over months, never as a single 90KB Write. This is the strongest pattern signal: the difference between intact and truncated production files maps onto the difference between "built via many Edits" and "saved via one large Write."

---

## Root Cause Hypothesis

The diagnostic evidence supports a high-confidence hypothesis: **truncation happens at model output time during single-shot Writes, not at the tool layer or filesystem layer.**

The mechanism: when an agent generates a Write tool call with a long content payload, the entire content has to fit into one response turn's output token budget. If the model's output budget is exhausted mid-content - because the session has already produced significant output, because of an unusually long preamble, or because the content itself is near the budget ceiling - the tool call's `content` field gets clipped at whatever was emitted before the budget ran out. The tool then receives the truncated `content` string as its input and successfully writes that (partial) content to disk. The "success" the tool reports is technically accurate: the bytes that arrived were written. But the bytes that arrived were less than what the model was trying to send, and there is no error signal at the tool layer to flag the discrepancy.

The mid-word ending pattern is the signature of this mechanism. Filesystem-level truncations and tool-level character caps tend to truncate at clean boundaries (chunk sizes, character limits aligned to whitespace). Output-budget exhaustion mid-token-stream cuts wherever the budget happens to expire, which is usually mid-word in English prose because tokens often span word boundaries. The work-personal-assistant cut at "share s" is a textbook example.

The "intact at 90KB via many Edits" finding is the corroborating evidence. If output-budget exhaustion is the cause, then the protective factor is splitting content across multiple response turns - exactly what chunked Edits do. Each Edit's `new_string` parameter only carries the delta, not the whole file, so each individual Edit fits comfortably within budget regardless of total file size.

This hypothesis cannot be proven definitively from the agent's side - the model's output budget is set externally and cannot be inspected at runtime. But every observable signature matches it, and no alternative hypothesis fits the data without invoking specific session-state effects that would themselves be a form of budget exhaustion.

---

## The Verification Protocol

This is the operational discipline that fires after every Write or Edit on a meaningful file. It is encoded as a rule in The Architect's instructions.md v4.17 and reproduced here with rationale.

**Step 1 - Read the last 30-50 lines of the file via the Read tool.** Never use bash for this; bash is stale (see Bash Mount Staleness section). The Read tool returns the current on-disk state.

**Step 2 - Check the expected closer for the file's type.** Each file type has a specific structural endpoint:
- `instructions.md` ends with `*Full version history in [changelog.md](changelog.md).*` or its handoff-routed equivalent (`*Full version history in [handoff.md](handoff.md).*` for projects that keep the changelog inline in handoff.md instead of a dedicated changelog.md file).
- `.html` files end with `</html>`.
- Tracker `.md` files (handoff, blueprint-summary, test-cases, backlog) end with a complete final list item or table row - whatever the file's last meaningful structural element is.
- `project-launch.md` ends with the closing fence of Block 3's initialization-prompt code block.
- `changelog.md` ends with the oldest version row complete (no trailing partial row).

**Step 3 - Confirm the last content line ends at a sentence or structure boundary, never mid-word.** The mid-word signature is the most reliable indicator of output-budget truncation. If the last visible line ends with a partial word or a partial markdown token, the save failed regardless of what step 2 says.

**Step 4 - For files with declared element counts, grep-verify the count.** If a section header reads "5 examples" and the file has 4 example sub-headers, the file is incomplete. If a checklist promises 10 test cases and 7 are present, the file is incomplete. Grep on the structural marker (e.g., `^### Example`) and count.

**Step 5 - On failure, retry once via Edit with only the missing portion.** Do not re-Write the whole file. A failed Write usually means output budget was tight; a fresh Edit with a smaller delta has a fresh budget on a new response turn. Targeted Edits are also less risky in case the failure has a different cause.

**Step 6 - On second failure, STOP and surface to Adam in chat.** Do not declare the save complete. Do not try a third time silently. Tell Adam exactly what was written, what is missing, and what the verification check showed. The user's call on next steps - they may want to investigate before further writes.

**The grader-checkable trigger:** every Write or Edit on a meaningful file in a session must have a paired Read-verify call before "done" is asserted in chat. Meaningful files include `instructions.md`, context files, tracker `.md` files (handoff, blueprint-summary, test-cases, backlog, project-launch), training-materials `.html` and `.md` files, and `changelog.md` updates - basically anything outside the `outputs/` scratch folder.

---

## Mitigation Strategies

The verification protocol catches truncation after it happens. Mitigation strategies prevent it from happening in the first place.

**Strategy 1 - Chunked Edit-append for files larger than ~12KB.** For new large files, write a stub with header and section skeleton (small enough to land safely in one Write) then Edit-append each section individually. Each Edit carries only the delta, so each individual call has plenty of output budget. This is the pattern that produced The Architect's 90KB instructions.md intact - many small Edits over many sessions.

**Strategy 2 - Surgical Edits for revisions, never full re-Writes.** When updating an existing large file, change only the specific section that needs updating. Use Edit with a tightly scoped `old_string`/`new_string` pair. Do not re-emit the entire file via Write. Even a small content change inside a Write call of a 50KB file puts the entire 50KB through one output budget.

**Strategy 3 - Watch context window load.** Output budget is shared with reasoning, narration, and any other content the model emits in a response turn. A long preamble in chat before a Write tool call consumes budget that could otherwise have gone to the file content. For production fixes of large files, minimize narration before the tool call. Or just split the work across multiple response turns.

**Strategy 4 - Empirical validation matters more than theoretical limits.** A 26KB single-shot Write was validated empirically in the diagnostic session - if the next file you need to save is 18KB, that's well within proven safe territory. But the validation is per-session: a new session has its own output budget state. Use the verification protocol as the safety net regardless.

**Strategy 5 - Avoid unnecessary regeneration.** If a file is already at the right state, do not re-Write it just to "freshen" it. Each save event is a chance for silent loss. The lowest-risk file is the file you don't have to save.

---

## Recovery Procedures

When the verification protocol catches truncation, or when an old truncation is discovered after the fact:

**Step 1 - Read the full file to assess what's missing.** Do not rely on the closing-line check alone. Some content may be present but elements may still be incomplete.

**Step 2 - Check the changelog row for the version that introduced the missing content.** Project changelogs in this workspace tend to be detailed - often the v[X.X] row that added a section enumerates exactly what was added. The work-personal-assistant v1.4 reconstruction was guided directly by the v1.1 changelog row's description ("Added 5th example for formal vendor/leadership register" and "Restructured NEVER section into Hard Rules sub-section (FABRICATE, ACT EXTERNALLY) and Format Absolutes sub-section (em dash, School Tech naming) with stated reasons"). If the changelog row is detailed enough, reconstruction is well-grounded.

**Step 3 - Look for parallel files of the same type for structural template.** Most agents in this workspace follow recurring patterns. If a section is lost in one project's instructions.md, the equivalent section in a peer project's instructions.md is a usable template. The work-personal-assistant NEVER section was reconstructed using personal-assistant/instructions.md NEVER as the structural reference.

**Step 4 - Reconstruct as new authorial content if originals are not recoverable.** Be honest about this in the changelog: "Content restoration, not behavior change" plus an explicit note that the new content is reconstructed (not recovered) and Adam should review for fit. Do not pretend the new content matches the original byte-for-byte unless you can prove it.

**Step 5 - Bump the version with a clear changelog row.** The version bump signals the file changed; the changelog row preserves the diagnostic record for future sessions or audit.

**Step 6 - Adam reviews reconstructed content before relying on it in production.** New authorial content from the agent should not silently propagate into live use. Surface the reconstruction in chat with the link to the file and a request to review.

---

## Bash Mount Staleness

Empirical observation from 2026-05-02: the bash mount under `/sessions/[session-id]/mnt/` provides a stale view of files that have been modified in the current session via the file tools (Write, Edit). The staleness manifests as:
- `ls -la` shows the pre-edit file size
- `tail -c N` shows pre-edit content
- `grep` on the file does not find newly added markers
- `wc -l` shows the pre-edit line count
- `md5sum` shows the pre-edit checksum

This was tested and confirmed during the diagnostic session: an Edit confirmed via Read tool to have appended 1.5KB of content with two unique markers (CHARLIE-EDIT-START, CHARLIE-EDIT-END) showed the original 10195-byte size and zero matches for the markers when checked through bash, both immediately after the Edit and after a 3-second wait.

Files that were NOT modified during the session (e.g., previously-fixed training documents) show consistent state via both bash and Read - so bash is reliable as a static reference, just not as a verification mechanism for in-session writes.

**Rule:** for any verification of a Write or Edit performed during the current session, use the Read tool. Bash may be used for static checks (file existence, listing contents of unmodified directories, searching across files that haven't been touched this session) but never to confirm a write's success.

---

## References

**Encoded in:**
- The Architect `instructions.md` v4.17 - BEHAVIOR GUIDELINES > "At save time and confirmation gates" > "Post-write verification gate" rule
- The Architect `changelog.md` v4.17 row documents the protocol's introduction

**Related rules in The Architect:**
- "Don't produce scaffolded files" - the NEVER SHIP SCAFFOLD rule, complementary save-time discipline
- "Distinguish confirmed / inferred / unknown" - content quality at save time
- "Wait for explicit confirmation before Wave 2 outputs" - timing of saves
- "Backlog version-bump check" - post-save bookkeeping that fires on every version increment

**Related skills:**
- `prompt-evaluator` - scores instructions.md quality but does not check for truncation; the verification protocol is the truncation-specific complement
- `training-doc-auditor` - cross-checks training docs against the live system; should also flag files that end mid-word as truncated rather than as drift

**Related documents:**
- `_run-tracker-deep-research-master-2026-05-01.md` line 22 - records a Prompt-10 truncation that required reconstruction during a Deep Research run
- The Architect `instructions.md` v4.15 changelog row - records the v4.14 SECTION WEIGHT REFERENCE appendix truncation and its repair
- `project-blueprints/work-personal-assistant/changelog.md` v1.4 row - records the EXAMPLES + NEVER section reconstruction
- `project-blueprints/sta-security-advisor/handoff.md` v1.3 changelog row - records the Restated hard rules section restoration

**Backups (the missing piece):**
The 2026-05-02 truncation crisis was unrecoverable specifically because no backups existed. A workspace-level Git repo with daily auto-commit is queued in The Architect's backlog as the durable solution; manual snapshot procedures are the bridge until that lands.

---

*This document is the diagnostic record for the Write Verification Protocol. The protocol itself is enforced via The Architect's instructions.md. If you change the protocol in either location, update both for consistency - The Architect's TRAINING DOC DRIFT CHECK should catch divergence at the next per-change scan.*
