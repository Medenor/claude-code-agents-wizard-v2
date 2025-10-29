#!/usr/bin/env python3
"""
Convert a real Codex CLI JSONL trace into the normalized workflow schema used
by the orchestration audit tools.

Usage
-----
    python3 scripts/ingest_codex_jsonl.py \
        --input ~/.codex/log/latest-session.jsonl \
        --output audit_logs/live-workflow.json

The script expects Codex `--json` / telemetry events that contain text content
for orchestrator <-> agent exchanges. It applies heuristic classification based
on the payload templates defined in `.codex/CODEX.md` and produces:
  * Normalized event list (matching scripts/run_workflow_simulation.py output)
  * Derived state snapshots that follow the orchestrator state machine
  * Template validation checks for each detected payload/response

If new agent templates are introduced, extend the `CLASSIFIERS` definitions
below so the ingestion step recognizes them.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class EventRecord:
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
    active_todo: Optional[str]
    todo_statuses: Dict[str, str]
    note: str


@dataclass
class ValidationResult:
    name: str
    status: str
    missing_sections: Sequence[str]


TODO_ID_PATTERN = re.compile(r"TODO ID:\s*(todo-\d+)", re.IGNORECASE)


def current_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_list(value: object) -> List:
    if isinstance(value, list):
        return value
    return [value]


def flatten_text(event: Dict) -> str:
    """
    Extract human-readable text from Codex JSON events. Supports multiple shapes:
      - {"content": [{"type": "text", "text": "..."}]}
      - {"content": "raw text"}
      - {"message": {"content": ...}}
      - {"payload": {"content": ...}}
    """
    content_candidates: Iterable = []
    if "content" in event:
        content_candidates = ensure_list(event["content"])
    elif "message" in event and "content" in event["message"]:
        content_candidates = ensure_list(event["message"]["content"])
    elif "payload" in event and "content" in event["payload"]:
        content_candidates = ensure_list(event["payload"]["content"])
    else:
        return ""

    extracted: List[str] = []
    for candidate in content_candidates:
        if isinstance(candidate, str):
            extracted.append(candidate)
        elif isinstance(candidate, dict):
            if candidate.get("type") == "text" and "text" in candidate:
                extracted.append(candidate["text"])
            elif "value" in candidate and isinstance(candidate["value"], str):
                extracted.append(candidate["value"])
    return "\n".join(extracted).strip()


def guess_actor(event: Dict) -> Tuple[str, str]:
    """
    Best-effort inference of sender/recipient based on event metadata.
    Fallback to payload type classification when metadata is missing.
    """
    actor = (
        event.get("participant")
        or event.get("actor")
        or event.get("source")
        or {}
    )
    if isinstance(actor, dict):
        name = actor.get("name") or actor.get("role") or "unknown"
    else:
        name = str(actor)

    target = (
        event.get("target")
        or event.get("recipient")
        or {}
    )
    if isinstance(target, dict):
        target_name = target.get("name") or target.get("role") or "unknown"
    elif target:
        target_name = str(target)
    else:
        target_name = "unknown"

    return name, target_name


ClassifierResult = Tuple[str, str]  # payload_type, inferred direction (sender, recipient)


def classifier_orchestrator_payload(text: str) -> Optional[ClassifierResult]:
    if "OBJECTIVE:" in text and "REQUIREMENTS:" in text and "CONSTRAINTS:" in text:
        return ("coder_payload", ("orchestrator", "coder"))
    if "SCOPE:" in text and "PASS CRITERIA:" in text and "ARTIFACT REQUESTS:" in text:
        return ("tester_payload", ("orchestrator", "tester"))
    if text.startswith("ISSUE:") and "DECISION OPTIONS:" in text:
        return ("stuck_payload", ("orchestrator", "stuck"))
    return None


def classifier_agent_response(text: str) -> Optional[ClassifierResult]:
    if "STATUS:" in text and "DIFF:" in text and "TESTS:" in text:
        status_line = re.search(r"STATUS:\s*(\w+)", text)
        status = status_line.group(1).lower() if status_line else "unknown"
        payload_type = "coder_response"
        role = "completion"
        direction = ("coder", "orchestrator")
        return (payload_type, direction)
    if "STATUS:" in text and "VIEWPORTS:" in text and "RECOMMENDATION:" in text:
        return ("tester_response", ("tester", "orchestrator"))
    if text.startswith("HUMAN DECISION:") and "ACTION REQUIRED:" in text:
        return ("stuck_response", ("stuck", "orchestrator"))
    return None


CLASSIFIERS = [
    classifier_orchestrator_payload,
    classifier_agent_response,
]


def classify_event(text: str) -> Optional[Tuple[str, Tuple[str, str]]]:
    for classifier in CLASSIFIERS:
        result = classifier(text)
        if result:
            return result
    return None


def require_sections(text: str, sections: Sequence[str], name: str) -> ValidationResult:
    missing = [section for section in sections if section not in text]
    return ValidationResult(
        name=name,
        status="pass" if not missing else "fail",
        missing_sections=missing,
    )


VALIDATION_RULES: Dict[str, Sequence[str]] = {
    "coder_payload": ("TODO ID:", "OBJECTIVE:", "REQUIREMENTS:", "CONSTRAINTS:", "OUTPUT FORMAT:", "POST-CONDITIONS:", "```diff"),
    "coder_response": ("TODO ID:", "STATUS:", "DIFF:", "TESTS:", "SUMMARY:", "FOLLOW-UP:"),
    "tester_payload": ("TODO ID:", "SCOPE:", "VIEWPORTS:", "ARTIFACT REQUESTS:", "PASS CRITERIA:", "FAILURE HANDOFF:"),
    "tester_response": ("TODO ID:", "STATUS:", "VIEWPORTS:", "STEPS:", "ISSUES:", "RECOMMENDATION:"),
    "stuck_payload": ("ISSUE:", "CONTEXT:", "DECISION OPTIONS:", "NEEDED BY:"),
    "stuck_response": ("HUMAN DECISION:", "ACTION REQUIRED:", "FOLLOW-UP:"),
}


def parse_timestamp(event: Dict) -> str:
    for key in ("timestamp", "created", "time"):
        value = event.get(key)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).replace(microsecond=0).isoformat()
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.rstrip("Z")).replace(tzinfo=timezone.utc).replace(microsecond=0).isoformat()
            except ValueError:
                continue
    return current_timestamp()


def extract_events(events: Iterable[Dict]) -> Tuple[List[EventRecord], List[ValidationResult]]:
    results: List[EventRecord] = []
    validations: List[ValidationResult] = []

    sequence = 0

    for raw_event in events:
        text = flatten_text(raw_event)
        if not text:
            continue
        classification = classify_event(text)
        if not classification:
            continue

        payload_type, inferred_direction = classification

        sender_guess, recipient_guess = guess_actor(raw_event)
        sender, recipient = inferred_direction

        if sender_guess != "unknown" and sender_guess not in ("assistant", "system"):
            sender = sender_guess
        if recipient_guess != "unknown":
            recipient = recipient_guess

        sequence += 1
        timestamp = parse_timestamp(raw_event)

        results.append(
            EventRecord(
                sequence=sequence,
                timestamp=timestamp,
                sender=sender,
                recipient=recipient,
                role="delegation" if payload_type.endswith("payload") else "completion",
                payload_type=payload_type,
                content=text,
            )
        )

        sections = VALIDATION_RULES.get(payload_type, [])
        if sections:
            todo_id_match = TODO_ID_PATTERN.search(text)
            todo_fragment = todo_id_match.group(1) if todo_id_match else payload_type
            validations.append(
                require_sections(text, sections, f"{payload_type}_{todo_fragment}")
            )

    return results, validations


def build_state_snapshots(events: List[EventRecord]) -> List[StateSnapshot]:
    todo_status: Dict[str, str] = defaultdict(lambda: "pending")
    snapshots: List[StateSnapshot] = []
    active_todo: Optional[str] = None
    phase = "bootstrap"

    def append_snapshot(note: str, timestamp: str) -> None:
        snapshots.append(
            StateSnapshot(
                timestamp=timestamp,
                phase=phase,
                active_todo=active_todo,
                todo_statuses=dict(todo_status),
                note=note,
            )
        )

    if events:
        append_snapshot("Captured session metadata from raw log.", events[0].timestamp)

    for event in events:
        todo_match = TODO_ID_PATTERN.search(event.content)
        todo_id = todo_match.group(1) if todo_match else None

        if event.payload_type == "coder_payload" and todo_id:
            phase = "dispatch"
            active_todo = todo_id
            todo_status[todo_id] = "in_progress"
            append_snapshot(f"Dispatching {todo_id} to coder.", event.timestamp)
        elif event.payload_type == "coder_response" and todo_id:
            status_match = re.search(r"STATUS:\s*(\w+)", event.content, re.IGNORECASE)
            status_token = status_match.group(1).lower() if status_match else ""
            if status_token == "success":
                phase = "verifying"
                todo_status[todo_id] = "verifying"
                append_snapshot(f"Awaiting tester results for {todo_id}.", event.timestamp)
            else:
                phase = "escalating"
                todo_status[todo_id] = "blocked"
                append_snapshot(f"Coder reported failure for {todo_id}.", event.timestamp)
        elif event.payload_type == "tester_payload" and todo_id:
            phase = "verifying"
            append_snapshot(f"Tester engaged for {todo_id}.", event.timestamp)
        elif event.payload_type == "tester_response" and todo_id:
            status_match = re.search(r"STATUS:\s*(\w+)", event.content, re.IGNORECASE)
            status_token = status_match.group(1).lower() if status_match else ""
            if status_token == "pass":
                todo_status[todo_id] = "complete"
                phase = "dispatch"
                append_snapshot(f"Tester passed {todo_id}; returning to queue.", event.timestamp)
            else:
                todo_status[todo_id] = "blocked"
                phase = "escalating"
                append_snapshot(f"Tester failed {todo_id}; escalating.", event.timestamp)
        elif event.payload_type == "stuck_payload" and todo_id:
            phase = "escalating"
            append_snapshot(f"Escalating {todo_id} to stuck agent.", event.timestamp)
        elif event.payload_type == "stuck_response" and todo_id:
            phase = "planning"
            todo_status[todo_id] = "pending"
            append_snapshot(f"Human guidance received for {todo_id}.", event.timestamp)

    return snapshots


def load_events_from_jsonl(path: Path) -> List[Dict]:
    events: List[Dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Codex JSONL traces.")
    parser.add_argument("--input", required=True, type=Path, help="Path to Codex JSONL trace (from `codex exec --json`).")
    parser.add_argument("--output", required=True, type=Path, help="Destination workflow JSON file.")
    parser.add_argument("--session-id", default=None, help="Override session ID (defaults to basename of input).")
    args = parser.parse_args()

    raw_events = load_events_from_jsonl(args.input)
    if not raw_events:
        raise SystemExit(f"No events parsed from {args.input}")

    events, validations = extract_events(raw_events)
    if not events:
        raise SystemExit("Unable to detect any orchestrator/agent payloads in the provided log; update classifier rules.")

    snapshots = build_state_snapshots(events)
    record = {
        "session_id": args.session_id or args.input.stem,
        "generated_at": current_timestamp(),
        "events": [asdict(evt) for evt in events],
        "state_snapshots": [asdict(snapshot) for snapshot in snapshots],
        "validations": [asdict(validation) for validation in validations],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
        fh.write("\n")

    print(f"Wrote normalized workflow record to {args.output}")


if __name__ == "__main__":
    main()
