# SMART Todo Dry-Run Example

This dry-run illustrates how to structure a single manual delegation cycle for a theoretical task without touching the repository. It demonstrates the SMART pattern and the expected responses from CODER and TESTER roles.

---

## Setup
- **Todo ID**: `todo-010`
- **Goal**: Prepare a project status summary markdown file.
- **Context**: No file currently exists; orchestrator requires a lightweight summary for stakeholders.
- **Deadline**: Complete within the current turn (deadline_ms ≈ 300000).

---

## 1. Manual Delegation Packet → CODER

```
MANUAL DELEGATION PACKET
Act as the coder agent, carefully following .codex/agents/coder.md instructions
TODO ID: todo-010
PHASE: dispatch
TARGET AGENT: CODER
OBJECTIVE: Draft status_summary.md summarizing project progress
DETAILS:
- Scope: Create new file `status_summary.md` at repo root with three sections: Overview, Completed Todos, Next Actions.
- Acceptance: Each section has at least one bullet; include references to evidence files (e.g., diffs, screenshots) by name; keep under 200 words.
- Notes: Base content on latest manual delegation sample (`docs/manual-delegation-sample.md`); no code changes required beyond the markdown file.
- Deadline: Complete within this turn (deadline_ms 300000). Escalate if additional context is required.
REQUESTED ARTIFACTS:
- apply_patch diff showing the new file
- `cat status_summary.md` output verifying content
```

### Expected CODER Response (Dry-Run)

```
TODO ID: todo-010
STATUS: success
DIFF:
*** Begin Patch
*** Add File: status_summary.md
+# Project status summary (dry-run)
+
+## Overview
+- Documented manual orchestration flow for hello-world example.
+
+## Completed Todos
+- todo-001 – Added `hello.html` (see hello.html diff).
+
+## Next Actions
+- Plan automation strategy for invoking subagents.
*** End Patch
TESTS:
- command: cat status_summary.md
  exit_code: 0
  output: |
    # Project status summary (dry-run)
    ...
SUMMARY:
- Created status_summary.md capturing overview, completed work, and next actions under 200 words.
FOLLOW-UP:
- none
```

---

## 2. Manual Delegation Packet → TESTER

```
MANUAL DELEGATION PACKET
Act as the tester agent, carefully following .codex/agents/tester.md instructions
TODO ID: todo-010
PHASE: verifying
TARGET AGENT: TESTER
OBJECTIVE: Verify status_summary.md structure and references
DETAILS:
- Scope: Open `status_summary.md`; ensure sections Overview/Completed Todos/Next Actions exist with bullet content under 200 words total.
- Acceptance: Confirm references to evidence filenames (e.g., `hello.html`) are present; ensure markdown renders without lint warnings (run `markdownlint` if available or a visual preview).
- Notes: No screenshots required; log lint command output or manual inspection notes.
- Deadline: Same turn; escalate if linting tooling unavailable.
REQUESTED ARTIFACTS:
- Verification template with confirmation of section structure
- Lint command output or narrative inspection notes
```

### Expected TESTER Response (Dry-Run)

```
TODO ID: todo-010
STATUS: pass
VIEWPORTS:
- size: n/a
  screenshot: none
STEPS:
- action: cat status_summary.md; verified three sections with bullets and word count below 200
  result: success
  console_errors: []
- action: markdownlint status_summary.md (or manual check); confirmed no structural issues
  result: success
  console_errors: []
ISSUES:
- none
RECOMMENDATION:
- ready for release
```

---

## Takeaways
- The packet clearly communicates **Specific** scope (one markdown file), **Measurable** acceptance (sections, word limit, references), **Achievable** workload (single-file draft), **Relevant** context (ties back to existing evidence), and **Time-bound** expectations.
- CODER and TESTER responses stay concise while capturing the required artifacts/logs, making it easy for the orchestrator to record evidence without overloading the shared context.
