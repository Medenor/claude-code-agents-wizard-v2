#!/usr/bin/env python3
"""
Compare two normalized workflow JSON records (baseline vs. live run) and report
differences across agent payloads, state transitions, and validation outcomes.

Usage
-----
    python3 scripts/compare_workflows.py \
        --baseline audit_logs/workflow-baseline.json \
        --actual audit_logs/live-workflow.json

The script highlights:
  * Missing or extra payload types / TODO IDs
  * Mismatched agent order or sender/recipient pairs
  * Validation failures in the live run
  * Divergent state machine phases or todo statuses
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class EventKey:
    payload_type: str
    todo_id: str
    sender: str
    recipient: str


def load_workflow(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def extract_event_key(event: Dict) -> EventKey:
    todo_id = "unknown"
    for line in event["content"].splitlines():
        if line.strip().lower().startswith("todo id:"):
            todo_id = line.split(":", 1)[1].strip()
            break
    return EventKey(
        payload_type=event["payload_type"],
        todo_id=todo_id,
        sender=event["sender"],
        recipient=event["recipient"],
    )


def compare_events(baseline_events: List[Dict], actual_events: List[Dict]) -> Tuple[List[str], List[str]]:
    baseline_keys = [extract_event_key(evt) for evt in baseline_events]
    actual_keys = [extract_event_key(evt) for evt in actual_events]

    missing: List[str] = []
    extra: List[str] = []

    actual_consumed = [False] * len(actual_keys)

    for base_key in baseline_keys:
        try:
            idx = next(
                i for i, key in enumerate(actual_keys)
                if not actual_consumed[i]
                and key.payload_type == base_key.payload_type
                and key.todo_id == base_key.todo_id
            )
            actual_consumed[idx] = True
            actual_key = actual_keys[idx]
            if actual_key.sender != base_key.sender or actual_key.recipient != base_key.recipient:
                missing.append(
                    f"Routing mismatch for {base_key.payload_type} {base_key.todo_id}: "
                    f"baseline {base_key.sender}->{base_key.recipient}, "
                    f"actual {actual_key.sender}->{actual_key.recipient}"
                )
        except StopIteration:
            missing.append(f"Missing event {base_key.payload_type} for {base_key.todo_id}")

    for idx, consumed in enumerate(actual_consumed):
        if not consumed:
            key = actual_keys[idx]
            extra.append(f"Unexpected event {key.payload_type} for {key.todo_id} ({key.sender}->{key.recipient})")

    return missing, extra


def collect_validation_failures(validations: List[Dict]) -> List[str]:
    return [
        f"{entry['name']} missing sections {', '.join(entry['missing_sections'])}"
        for entry in validations
        if entry.get("status") != "pass"
    ]


def compare_state_snapshots(baseline: List[Dict], actual: List[Dict]) -> List[str]:
    issues: List[str] = []
    for idx, base_snapshot in enumerate(baseline):
        if idx >= len(actual):
            issues.append(f"Missing state snapshot #{idx + 1} (phase {base_snapshot['phase']}) in actual run.")
            continue
        actual_snapshot = actual[idx]
        if base_snapshot["phase"] != actual_snapshot["phase"]:
            issues.append(
                f"Snapshot #{idx + 1} phase mismatch: baseline {base_snapshot['phase']} vs actual {actual_snapshot['phase']}"
            )
        base_todos = base_snapshot["todo_statuses"]
        actual_todos = actual_snapshot["todo_statuses"]
        if base_todos != actual_todos:
            issues.append(
                f"Snapshot #{idx + 1} todo statuses differ: baseline {base_todos} vs actual {actual_todos}"
            )
    if len(actual) > len(baseline):
        issues.append(f"Actual run contains {len(actual) - len(baseline)} extra state snapshots.")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare baseline vs live Codex workflows.")
    parser.add_argument("--baseline", required=True, help="Path to baseline workflow JSON.")
    parser.add_argument("--actual", required=True, help="Path to live workflow JSON.")
    args = parser.parse_args()

    baseline = load_workflow(args.baseline)
    actual = load_workflow(args.actual)

    missing_events, extra_events = compare_events(baseline["events"], actual["events"])
    validation_failures = collect_validation_failures(actual.get("validations", []))
    state_diffs = compare_state_snapshots(baseline.get("state_snapshots", []), actual.get("state_snapshots", []))

    if not missing_events and not extra_events and not validation_failures and not state_diffs:
        print("✅ Live run matches baseline workflow structure.")
        return

    if missing_events:
        print("⚠️ Missing / mismatched events:")
        for item in missing_events:
            print(f"  - {item}")
    if extra_events:
        print("\n⚠️ Extra events detected:")
        for item in extra_events:
            print(f"  - {item}")
    if validation_failures:
        print("\n❌ Validation issues:")
        for item in validation_failures:
            print(f"  - {item}")
    if state_diffs:
        print("\n⚠️ State snapshot differences:")
        for item in state_diffs:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
