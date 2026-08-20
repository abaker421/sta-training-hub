# Write Verification Protocol

**Origin:** 2026-05-02 truncation crisis - three production `instructions.md` files were found mid-word truncated with no backups available.
**Encoded in:** The Architect v4.17 introduced the rule in BEHAVIOR GUIDELINES > "At save time and confirmation gates" > "Post-write verification gate." Since The Architect v6.0 (2026-05-21), the rule lives in `project-blueprints/the-architect/behavior-patterns.md` > "At save time and confirmation gates" - the inline BEHAVIOR GUIDELINES section is now a quick-reference table + Pattern A pointer to the patterns file. v6.0 also split the rule into two distinct named rules: "Post-write verification gate" (the standard verification flow) and "Shortening Edit null-byte check" (the binary null-byte sweep for shortening Edits).
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
| Bash Mount Staleness | The 2026-05-02 finding, SUPERSEDED 2026-06-07 - staleness is conditional, not absolute |
| Edit Tool Null-Byte Padding | Why shortening Edits silently corrupt files - 2026-05-21 empirical finding |
| 2026-06-07 Protocol Upgrade | **Current operative rules** - verification-channel rule, Write-size cap, `verify-write.py`, EOF sentinel |
| References | Related rules in The Architect, related skills, related documents |

---

## The Crisis

On 2026-05-02 morning, Adam discovered three project `instructions.md` files in the workspace had silently lost content during prior session saves. The most diagnostically clear case was `project-blueprints/work-personal-assistant/instructions.md`, which ended mid-word at the string `"I just wanted to share s` - cutting the word "share" in two and leaving the entire EXAMPLES section incomplete (only Example 1 plus the start of Example 2, instead of the v1.1-designed five examples) and the entire NEVER section absent. Two other files were suspected truncated and required investigation:

- `project-blueprints/_Claude-Projects/ai-advisor-proj/instructions.md` - Adam believed the file content matched v1.10 even though the version comment said v1.14. On verification, the file turned out to be intact at v1.14 - the chat-client autolink corruption in the form Adam was viewing it through had created the false impression of mismatch.
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

**Step 1 - Verify through the channel that wrote the file.** *(Revised 2026-06-07 - see the 2026-06-07 Protocol Upgrade section, which supersedes the original blanket "never use bash" wording below.)* For a bash-written or newly-Written file, `verify-write.py` via bash is authoritative. For a file-tool Edit on a large pre-existing file, read the last 30-50 lines via the Read tool - the bash mount can still serve a stale partial view there. When the two channels disagree, the Read tool wins.

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

> **SUPERSEDED 2026-06-07.** This section is retained as the original diagnostic record. The blanket prohibition on bash below is no longer the operative rule - staleness was retested on 2026-06-07 and found to be *conditional*, and bash is now the authoritative channel for script-based verification of bash-written and newly-Written files. See the **2026-06-07 Protocol Upgrade** section for the rule in force.

Empirical observation from 2026-05-02: the bash mount under `/sessions/[session-id]/mnt/` provides a stale view of files that have been modified in the current session via the file tools (Write, Edit). The staleness manifests as:
- `ls -la` shows the pre-edit file size
- `tail -c N` shows pre-edit content
- `grep` on the file does not find newly added markers
- `wc -l` shows the pre-edit line count
- `md5sum` shows the pre-edit checksum

This was tested and confirmed during the diagnostic session: an Edit confirmed via Read tool to have appended 1.5KB of content with two unique markers (CHARLIE-EDIT-START, CHARLIE-EDIT-END) showed the original 10195-byte size and zero matches for the markers when checked through bash, both immediately after the Edit and after a 3-second wait.

Files that were NOT modified during the session (e.g., previously-fixed training documents) show consistent state via both bash and Read - so bash is reliable as a static reference, just not as a verification mechanism for in-session writes.

**Rule as originally written (2026-05-02, no longer operative):** for any verification of a Write or Edit performed during the current session, use the Read tool. Bash may be used for static checks but never to confirm a write's success. **Superseded 2026-06-07** by the verification-channel rule: verify through the channel that wrote the file, and where that channel is bash, `verify-write.py` via bash *is* the authoritative confirmation of a write's success.

---

## Edit Tool Null-Byte Padding

Empirical observation from 2026-05-21: when the Edit tool's `new_string` is shorter than the `old_string`, the freed bytes at the tail of the file are filled with `\x00` (null) characters rather than the file being truncated to the new length. The Read tool's text-based output silently strips or skips the null bytes, and the standard ends-with-`</html>` verification check passes because the closing tag is still present immediately before the null padding. The file is silently corrupt - downstream parsers, deploy tools, and content-management systems will either reject it, render garbage at the end, or fail in subtle ways depending on how they tolerate null bytes.

This was discovered during the STA training kit Phase 0 fix session. Three files (Manual Tasks Checklist.html, New Project Build Guide V2.html, The Architect Case Study.html) had safe closing-tag content appended via Edit on the first verification pass. A subsequent Edit then replaced a longer truncation-notice block with the proper completed footer content, which was shorter than the block it replaced. The byte-level inspection at the FINAL verification gate revealed 663–972 null bytes between the closing `</html>` tag and the actual end-of-file in each affected file. The bytes did not exist in either the `old_string` or the `new_string` of the Edit operation - they appeared as padding. Maintenance SOP.html was unaffected only because its repair had used a direct python `open(path, 'wb')` write, not Edit.

**Why this matters more than bash staleness:** bash staleness causes a verification check to give the wrong answer for a brief window, then self-corrects. Null-byte padding corrupts the file persistently and silently passes every standard verification check (ends-with-marker, structural-element counts, line count). The only reliable detection is grep on `\x00` against the actual file bytes.

**Detection:** after any Edit where `len(new_string) < len(old_string)` (a "shortening Edit"), read the file with `open(path, 'rb').read()` (binary mode) and check `b'\x00' in data`. If present, the file was null-padded by the Edit tool and needs cleanup.

**Remediation:** never use Edit to clean up null padding (a follow-up Edit on the null region will inherit the same issue). Instead, use python:
```python
with open(path, 'rb') as f:
    data = f.read()
# Find last legitimate content end (e.g., the last </html> tag plus its newline)
cut = data.rfind(b'</html>') + len(b'</html>')
if cut < len(data) and data[cut:cut+1] == b'\n':
    cut += 1
# Write back with binary-mode write, which truncates the file to the new length
with open(path, 'wb') as f:
    f.write(data[:cut])
```
The `'wb'` open mode atomically truncates the file at write time. After the write, re-verify with `b'\x00' in data` and the file is clean.

**Prevention:** for any trailing-content fix (removing a footer block, stripping appended notices, shortening the end of a file), do not use Edit. Read the file as bytes, compute the desired final state, write it back with `open(path, 'wb')`. The python approach is verifiable at every step and does not exhibit the null-padding behavior.

**Scope:** the null-padding behavior is a property of the Edit tool implementation, not the file format or filesystem. It applies to any text-or-binary file edited via Edit: HTML, markdown, JSON, JavaScript, CSS, Python source. It applies whether the Edit succeeds or "succeeds with warnings." The verification protocol must add a byte-level null check after every shortening Edit, in addition to the existing structural checks.

**Rule update for the post-write verification gate:**
- Step 1 remains: Read the last 30-50 lines via Read tool.
- Step 2 remains: check the expected closer.
- **Step 2.5 (new):** for any Edit where `new_string` was shorter than `old_string`, also read the file as bytes via python and check `b'\x00' in data`. If null bytes are present, the file is corrupt regardless of what step 2 said.
- Step 3-6 remain unchanged.

**Reference:** this finding extends the original verification protocol. The grader-checkable trigger now includes shortening-Edit detection: any session that performed a shortening Edit without the null-byte check is a violation, even if all other structural checks passed.

---

## References

**Encoded in:**
- The Architect `instructions.md` v4.17 - BEHAVIOR GUIDELINES > "At save time and confirmation gates" > "Post-write verification gate" rule (rule introduction; inline until v6.0)
- The Architect `instructions.md` v5.18 - BEHAVIOR GUIDELINES > "At save time and confirmation gates" - extended with the shortening-Edit null-byte check (2026-05-21)
- The Architect `instructions.md` v6.0 (2026-05-21) - BEHAVIOR GUIDELINES section restructured: inline content replaced with 6-row quick-reference table + Pattern A pointer to `project-blueprints/the-architect/behavior-patterns.md`. The post-write verification gate and the shortening-Edit null-byte check are now two distinct named rules in the patterns file (previously a single compound rule). The quick-reference table's "At save time" row preserves the split in its required-action column.
- The Architect `behavior-patterns.md` (since v6.0) - canonical source-of-truth for both rules, including the full procedural detail, exact phrasings, and grader checks
- The Architect `changelog.md` - v4.17 row documents the protocol's introduction; v5.18 row documents the null-byte extension; v6.0 row documents the BEHAVIOR GUIDELINES extraction and rule split
- Auto-memory file `feedback_edit_null_byte_padding.md` carries the rule across all conversations (not just Architect sessions)

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

**Backups (gap closed):**
The 2026-05-02 truncation crisis was unrecoverable specifically because no backups existed. That gap is closed: the workspace is backed up to a Git repo on a **weekly** schedule, and the backup is shipped rather than queued. Backups are therefore no longer the open item this section originally described - but a weekly cadence means an unverified write can still cost up to a week of work, so the save-time verification discipline above remains the primary defence, not a stopgap.

---

## 2026-06-07 Protocol Upgrade - Prevention Cap + Script Verification

Root-cause diagnosis session (2026-06-07) re-tested the two platform behaviors this protocol was built around. Results:

**1. Bash-mount staleness is CONDITIONAL, not gone.** The 2026-05-02 finding was retested twice on 2026-06-07 with a split result. Fresh: files newly created via the Write tool, files written via bash itself, and small-file Edits - all immediately byte-identical when read via bash, on both mounts. Still stale: file-tool Edits on large pre-existing files - bash served a mid-word PARTIAL view of instructions.md, behavior-patterns.md, and this very document for minutes after each Edit, while the Read tool showed every file complete. Consequence - the **verification channel rule**: verify through the channel that wrote the file. Bash-written or newly-Written file -> `verify-write.py` via bash is authoritative. File-tool Edit on a large existing file -> Read-tool tail check is authoritative. When the two disagree, the Read tool wins. A script WARN/FAIL on a freshly-Edited large file is most likely a stale mount view, not a real truncation - confirm with Read before repairing anything.

**2. Shortening-Edit null-byte padding is STILL LIVE.** A 60-byte test file Edit-shortened on 2026-06-07 kept its 60-byte length with 35 trailing `\x00` bytes. The bug even null-padded the new verification script itself minutes after its creation. Treat every shortening Edit as suspect.

**Protocol changes (enforced in instructions.md rule 19 + behavior-patterns.md as of v6.22):**

- **Write-size cap (new, prevention):** no single Write tool call over ~150 lines / ~8KB on a meaningful file. Larger files are built as a Write stub + chunked Edit-appends. This targets the root cause - output-token clipping on oversized single Writes - rather than detecting it after the fact.
- **Script-based verification (replaces manual Read-tail checks):** `verify-write.py` at the workspace root. One bash call per task, covering every touched file: `python3 verify-write.py FILE [FILE ...]`. Checks type-correct closer (`</html>`, changelog pointer, `<!-- EOF -->`, code fence, table row), mid-word tail heuristic, and `\x00` presence; The flag set:
  - `--fix-nulls FILE [...]` strips trailing null runs in place via the sanctioned `r+b` truncate, then re-checks.
  - `--scan DIR [--fix-nulls]` walks `DIR` recursively and checks every text file, printing only FAIL/WARN plus a summary - clean files stay silent, which is what makes it token-minimal. It skips `_Archived/`, `Backups/`, `.git/`, `node_modules/` and `__pycache__/` so legitimate binary NULs never false-positive. This is the mode the recurring sweep uses.
  - `--assert-fresh FILE "marker"` exits 0 if the file *as bash currently sees it* contains the marker, and exits 2 with STALE if not. This is the guard on the file-tool-to-bash boundary: it is how you tell a stale mount view apart from real corruption, instead of guessing. Use it before repairing anything a scan flagged on a freshly-Edited file.

  Exit 1 = do not declare done.
- **EOF sentinel convention (new):** meaningful `.md` files with no natural closer end with `<!-- EOF -->` so the script check is deterministic.
- **Unattended sweep is detection-only.** The recurring workspace-wide truncation sweep runs as **Check 15 of the Monday health check (System Monitor v1.23), and it is READ-ONLY.** It reports clipped and null-padded files; it never repairs them. There is no unattended `--fix-nulls` pass. Every repair is a deliberate, operator-initiated follow-up on a named file - which is why a Check 15 finding is a work item, not a resolved issue.

The 2026-05-02 sections above are retained as the historical diagnostic record; where they conflict with this section, this section wins.

---

*This document is the diagnostic record for the Write Verification Protocol. The protocol itself is enforced via The Architect's instructions.md. If you change the protocol in either location, update both for consistency - The Architect's TRAINING DOC DRIFT CHECK should catch divergence at the next per-change scan.*

<!-- EOF -->
