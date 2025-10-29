#!/usr/bin/env python3
"""
Simulate a Codex orchestrator run and capture agent payloads/responses.

The script produces two artifacts in audit_logs/:
  1. workflow-<timestamp>.json  (structured event log + validation results)
  2. workflow-<timestamp>.md    (human-readable transcript)

Each payload or response is validated against the required template
sections described in .codex/CODEX.md and the agent contracts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "audit_logs"
LOG_DIR.mkdir(exist_ok=True)


@dataclass
class Event:
    sequence: int
    timestamp: str
    sender: str
    recipient: str
    role: str
    payload_type: str
    content: str


@dataclass
class StateSnapshot:
    timestamp: str
    phase: str
    active_todo: str | None
    todo_statuses: Dict[str, str]
    note: str


@dataclass
class ValidationResult:
    name: str
    status: str
    missing_sections: Sequence[str]


def current_timestamp() -> str:
    """Return ISO-8601 timestamp with UTC suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def require_sections(text: str, sections: Sequence[str], name: str) -> ValidationResult:
    missing = [section for section in sections if section not in text]
    status = "pass" if not missing else "fail"
    return ValidationResult(name=name, status=status, missing_sections=missing)


def build_simulation() -> Dict[str, object]:
    session_id = "demo-session-001"

    base_time = datetime.now(timezone.utc).replace(microsecond=0)

    def ts(offset_seconds: int) -> str:
        return (base_time + timedelta(seconds=offset_seconds)).isoformat()

    events: List[Event] = []
    snapshots: List[StateSnapshot] = []
    validations: List[ValidationResult] = []

    todo_queue = {
        "todo-001": "pending",
        "todo-002": "pending",
    }
    active_todo: str | None = None

    def record_snapshot(offset: int, phase: str, note: str) -> None:
        snapshots.append(
            StateSnapshot(
                timestamp=ts(offset),
                phase=phase,
                active_todo=active_todo,
                todo_statuses=dict(todo_queue),
                note=note,
            )
        )

    # Bootstrap phase
    record_snapshot(0, "bootstrap", "Captured repository, sandbox, and instruction context.")

    # Planning phase
    todo_queue["todo-001"] = "pending"
    todo_queue["todo-002"] = "pending"
    record_snapshot(5, "planning", "Initialized todo queue with two deterministic items.")

    # Dispatch todo-001
    active_todo = "todo-001"
    todo_queue["todo-001"] = "in_progress"
    record_snapshot(10, "dispatch", "Dispatching todo-001 to coder.")

    coder_payload_001 = """TODO ID: todo-001
OBJECTIVE: Implement audit logger utility
REQUIREMENTS:
- Update module `src/audit/logger.py` to emit deterministic log entries.
- Create tests in `tests/test_logger.py` verifying formatted output.
- Ensure CLI command `python -m audit.logger --demo` prints a sample entry.
CONSTRAINTS:
- Follow deterministic templates
- No TODOs or placeholders
OUTPUT FORMAT:
```diff
<apply_patch style diff>
```
POST-CONDITIONS:
- Tests listed above executed
- Summary + verification log returned"""

    validations.append(
        require_sections(
            coder_payload_001,
            [
                "TODO ID:",
                "OBJECTIVE:",
                "REQUIREMENTS:",
                "CONSTRAINTS:",
                "OUTPUT FORMAT:",
                "POST-CONDITIONS:",
                "```diff",
            ],
            "coder_payload_todo-001",
        )
    )

    events.append(
        Event(
            sequence=len(events) + 1,
            timestamp=ts(12),
            sender="orchestrator",
            recipient="coder",
            role="delegation",
            payload_type="coder_payload",
            content=coder_payload_001,
        )
    )

    coder_response_001 = """TODO ID: todo-001
STATUS: success
DIFF:
```diff
*** Begin Patch
*** Add File: src/audit/logger.py
+from datetime import datetime
+
+def emit_event(phase: str, message: str) -> str:
+    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
+    return f"[{timestamp}] {phase.upper()}: {message}"
*** End Patch
*** Begin Patch
*** Add File: tests/test_logger.py
+from audit.logger import emit_event
+
+def test_emit_event_formats_payload(monkeypatch):
+    class _FakeDateTime:
+        @classmethod
+        def utcnow(cls):
+            return type("dt", (), {"strftime": lambda self, fmt: "2024-01-01T00:00:00Z"})()
+
+    monkeypatch.setattr("audit.logger.datetime", _FakeDateTime)
+    result = emit_event("dispatch", "Invoked coder")
+    assert result == "[2024-01-01T00:00:00Z] DISPATCH: Invoked coder"
*** End Patch
```
TESTS:
- command: pytest tests/test_logger.py
  exit_code: 0
  output: |
    ============================= test session starts ==============================
    collected 1 item
    tests/test_logger.py .                                                      [100%]
    ============================== 1 passed in 0.02s ===============================
SUMMARY:
- Added audit logger helper with deterministic timestamp formatting and coverage test.
FOLLOW-UP:
- none"""

    validations.append(
        require_sections(
            coder_response_001,
            [
                "TODO ID:",
                "STATUS:",
                "DIFF:",
                "```diff",
                "TESTS:",
                "SUMMARY:",
                "FOLLOW-UP:",
            ],
            "coder_response_todo-001",
        )
    )

    events.append(
        Event(
            sequence=len(events) + 1,
            timestamp=ts(25),
            sender="coder",
            recipient="orchestrator",
            role="completion",
            payload_type="coder_response",
            content=coder_response_001,
        )
    )

    # Verification phase for todo-001
    todo_queue["todo-001"] = "verifying"
    record_snapshot(26, "verifying", "Awaiting tester validation for todo-001 output.")

    tester_payload_001 = """TODO ID: todo-001
SCOPE:
- Launch CLI demo via `python -m audit.logger --demo`.
- Capture rendered log output exposed at http://localhost:4173/audit.
VIEWPORTS:
- 1280x720
- 390x844
ARTIFACT REQUESTS:
- Screenshot filenames: todo-001-main-1280x720.png, todo-001-main-390x844.png
- Console log capture if failures occur
PASS CRITERIA:
- Visual output contains `[YYYY-MM-DDTHH:MM:SSZ] DISPATCH: Invoked coder`.
- No console errors during navigation.
FAILURE HANDOFF:
- Invoke stuck with screenshot + console summary"""

    validations.append(
        require_sections(
            tester_payload_001,
            [
                "TODO ID:",
                "SCOPE:",
                "ARTIFACT REQUESTS:",
                "PASS CRITERIA:",
                "FAILURE HANDOFF:",
                "VIEWPORTS:",
            ],
            "tester_payload_todo-001",
        )
    )

    events.append(
        Event(
            sequence=len(events) + 1,
            timestamp=ts(28),
            sender="orchestrator",
            recipient="tester",
            role="delegation",
            payload_type="tester_payload",
            content=tester_payload_001,
        )
    )

    tester_response_001 = """TODO ID: todo-001
STATUS: pass
VIEWPORTS:
- size: 1280x720
  screenshot: todo-001-main-1280x720.png
- size: 390x844
  screenshot: todo-001-main-390x844.png
STEPS:
- action: navigate http://localhost:4173/audit
  result: success
  console_errors: []
- action: verify rendered audit log entry
  result: success
  console_errors: []
ISSUES:
- none
RECOMMENDATION:
- ready for release"""

    validations.append(
        require_sections(
            tester_response_001,
            [
                "TODO ID:",
                "STATUS:",
                "VIEWPORTS:",
                "STEPS:",
                "ISSUES:",
                "RECOMMENDATION:",
            ],
            "tester_response_todo-001",
        )
    )

    events.append(
        Event(
            sequence=len(events) + 1,
            timestamp=ts(40),
            sender="tester",
            recipient="orchestrator",
            role="verification",
            payload_type="tester_response",
            content=tester_response_001,
        )
    )

    todo_queue["todo-001"] = "complete"
    active_todo = None
    record_snapshot(41, "dispatch", "Marked todo-001 complete and returning to queue.")

    # Dispatch todo-002
    active_todo = "todo-002"
    todo_queue["todo-002"] = "in_progress"
    record_snapshot(45, "dispatch", "Dispatching todo-002 to coder.")

    coder_payload_002 = """TODO ID: todo-002
OBJECTIVE: Integrate audit logger into CLI entrypoint
REQUIREMENTS:
- Modify `cli/main.py` to call `emit_event` during startup.
- Wire CLI argument `--demo` to print the formatted log message.
- Update documentation in `README.md` to mention the new command.
CONSTRAINTS:
- Follow deterministic templates
- No TODOs or placeholders
OUTPUT FORMAT:
```diff
<apply_patch style diff>
```
POST-CONDITIONS:
- Tests listed above executed
- Summary + verification log returned"""

    validations.append(
        require_sections(
            coder_payload_002,
            [
                "TODO ID:",
                "OBJECTIVE:",
                "REQUIREMENTS:",
                "CONSTRAINTS:",
                "OUTPUT FORMAT:",
                "POST-CONDITIONS:",
                "```diff",
            ],
            "coder_payload_todo-002",
        )
    )

    events.append(
        Event(
            sequence=len(events) + 1,
            timestamp=ts(47),
            sender="orchestrator",
            recipient="coder",
            role="delegation",
            payload_type="coder_payload",
            content=coder_payload_002,
        )
    )

    coder_response_002 = """TODO ID: todo-002
STATUS: failed
DIFF:
```diff
(no changes)
```
TESTS:
- command: python cli/main.py --demo
  exit_code: 1
  output: |
    Traceback (most recent call last):
      File "cli/main.py", line 3, in <module>
        from audit.logger import emit_event
    ModuleNotFoundError: No module named 'audit'
SUMMARY:
- Unable to import `audit.logger` from CLI entrypoint; package is missing.
FOLLOW-UP:
- Request guidance via stuck agent."""

    validations.append(
        require_sections(
            coder_response_002,
            [
                "TODO ID:",
                "STATUS:",
                "DIFF:",
                "```diff",
                "TESTS:",
                "SUMMARY:",
                "FOLLOW-UP:",
            ],
            "coder_response_todo-002",
        )
    )

    events.append(
        Event(
            sequence=len(events) + 1,
            timestamp=ts(60),
            sender="coder",
            recipient="orchestrator",
            role="completion",
            payload_type="coder_response",
            content=coder_response_002,
        )
    )

    # Escalation through stuck agent
    todo_queue["todo-002"] = "blocked"
    record_snapshot(61, "escalating", "Coder reported failure importing audit package.")

    needed_by = (base_time + timedelta(minutes=5)).isoformat()
    stuck_payload = f"""ISSUE: ModuleNotFoundError for `audit.logger`
CONTEXT:
- Todo ID: todo-002
- Last successful step: Planned CLI integration before executing demo command.
- Error output: ModuleNotFoundError: No module named 'audit'
DECISION OPTIONS:
- Option A: Create `src/audit/__init__.py` and retry the command.
- Option B: Update CLI execution environment to include project root on PYTHONPATH.
- Option C: Request different approach.
NEEDED BY: {needed_by}"""

    validations.append(
        require_sections(
            stuck_payload,
            [
                "ISSUE:",
                "CONTEXT:",
                "DECISION OPTIONS:",
                "NEEDED BY:",
                "Option A",
                "Option B",
                "Option C",
            ],
            "stuck_payload_todo-002",
        )
    )

    events.append(
        Event(
            sequence=len(events) + 1,
            timestamp=ts(63),
            sender="orchestrator",
            recipient="stuck",
            role="escalation",
            payload_type="stuck_payload",
            content=stuck_payload,
        )
    )

    stuck_response = """HUMAN DECISION: Option A
ACTION REQUIRED:
- Add `src/audit/__init__.py` so the package resolves.
- Re-run `python cli/main.py --demo` to confirm the logger output.
FOLLOW-UP:
- none"""

    validations.append(
        require_sections(
            stuck_response,
            [
                "HUMAN DECISION:",
                "ACTION REQUIRED:",
                "FOLLOW-UP:",
            ],
            "stuck_response_todo-002",
        )
    )

    events.append(
        Event(
            sequence=len(events) + 1,
            timestamp=ts(75),
            sender="stuck",
            recipient="orchestrator",
            role="resolution",
            payload_type="stuck_response",
            content=stuck_response,
        )
    )

    todo_queue["todo-002"] = "pending"
    active_todo = None
    record_snapshot(76, "planning", "Updated todo-002 with human guidance; ready to redispatch.")

    return {
        "session_id": session_id,
        "generated_at": current_timestamp(),
        "events": [asdict(e) for e in events],
        "state_snapshots": [asdict(s) for s in snapshots],
        "validations": [asdict(v) for v in validations],
    }


def write_artifacts(record: Dict[str, object]) -> Path:
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = LOG_DIR / f"workflow-{timestamp_str}.json"
    md_path = LOG_DIR / f"workflow-{timestamp_str}.md"

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
        fh.write("\n")

    lines: List[str] = []
    lines.append(f"# Workflow Simulation Transcript ({record['session_id']})")
    lines.append(f"Generated at: {record['generated_at']}")
    lines.append("")
    lines.append("## Validation Summary")
    for validation in record["validations"]:
        missing = validation["missing_sections"]
        status = validation["status"]
        name = validation["name"]
        if missing:
            lines.append(f"- {name}: {status.upper()} (missing {', '.join(missing)})")
        else:
            lines.append(f"- {name}: {status.upper()}")
    lines.append("")
    lines.append("## State Snapshots")
    for snapshot in record["state_snapshots"]:
        todo_states = ", ".join(f"{k}:{v}" for k, v in snapshot["todo_statuses"].items())
        lines.append(
            f"- {snapshot['timestamp']} — phase={snapshot['phase']} — active_todo={snapshot['active_todo']} — {todo_states} — {snapshot['note']}"
        )
    lines.append("")
    lines.append("## Event Log")
    for event in record["events"]:
        lines.append(
            f"### {event['sequence']}. {event['timestamp']} — {event['sender']} → {event['recipient']} ({event['payload_type']})"
        )
        lines.append("```")
        lines.append(event["content"])
        lines.append("```")
        lines.append("")

    with md_path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    return md_path


def main() -> None:
    record = build_simulation()
    transcript_path = write_artifacts(record)
    print(f"Wrote workflow transcript to {transcript_path}")


if __name__ == "__main__":
    main()
