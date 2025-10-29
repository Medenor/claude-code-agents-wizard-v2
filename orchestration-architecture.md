## Codex Orchestration Architecture

> **Current status:** The Codex CLI does not yet expose automated subagent invocation. The orchestrator therefore emits Manual Delegation Packets, and humans execute CODER, TESTER, and STUCK tasks while preserving the deterministic state machine described below.

### Top-level components
- **Node launcher (`codex-cli/bin/codex.js`)** — Detects platform, resolves vendored binary, forwards signals, and injects PATH overlays before spawning the Rust runtime.
- **Rust runtime (`vendor/*/codex`)** — Hosts both the interactive TUI and non-interactive `exec` flows, exposes Model Context Protocol (MCP) client/server integrations, and persists logs to `~/.codex/log`.
- **Configuration home (`$CODEX_HOME`)** — Supplies persistent state (profiles, MCP launchers, cached instructions) and user overrides consumed at startup.
- **Workspace adapters** — Git repository guard, sandbox policy enforcer, and filesystem abstraction used to protect project worktrees during tool execution.

### Instruction ingestion
1. Load global instructions from `.codex/CODEX.md` alongside the per-role prompts in [`.codex/agents/`](.codex/agents/)).
2. Walk repository ancestry to merge per-directory instructions, honoring overrides and configured fallbacks.
3. Emit the merged document to the orchestrator context before the first model turn.

### Session lifecycle
| Phase | Trigger | Primary modules | Outputs |
| --- | --- | --- | --- |
| `bootstrap` | CLI invocation | Node launcher, Rust runtime | Resolved binary, configured env, initial telemetry span |
| `planning` | First user turn | Orchestrator loop, plan tool | Todo list (`todo_list` items), reasoning trace |
| `execution` | Active todo | Manual CODER role (per delegation packet); local tooling | Human-supplied diffs, command logs |
| `verification` | Todo completion | Manual TESTER role; optional Playwright MCP | Screenshots, pass/fail report |
| `escalation` | Error/test failure | Manual STUCK role; AskUserQuestion envelope | Human decision packet |
| `finalize` | All todos complete | Summarizer, git status collector | Final assistant message, optional structured output |

### Event streams
- **Interactive TUI** — Logs to `~/.codex/log/codex-tui.log` with `RUST_LOG=codex_core=info,codex_tui=info,codex_rmcp_client=info`.
- **`codex exec --json`** — Emits JSONL events described in the Codex CLI documentation, enabling downstream queue processors.
- **MCP server mode** — Surfaces `thread`, `turn`, and `item` events to connected clients; supports long-running operations with configurable timeouts.

### Data & control flow
```text
User prompt
    ↓
Orchestrator planner
    ↓
Todo queue
    ↓
Manual Delegation Packet → Human CODER → Completion template → Orchestrator
    ↓
Manual Delegation Packet → Human TESTER → Verification template → Orchestrator
    ↓ (on error)
Manual Delegation Packet → Human STUCK → Decision → Orchestrator
```
- Todo queue is processed sequentially; each item carries `id`, `status`, `deadline`, and retry metadata.
- Command executions respect sandbox policy; failure raises structured errors into the orchestration layer.
- Test artifacts (screenshots, logs) are stored alongside run metadata for traceability.

### Manual delegation workflow
- Orchestrator transitions are unchanged; only the actor executing `execution`, `verification`, and `escalation` phases differs.
- Manual packets mirror the automated payload formats so future subagent integrations can drop in with minimal change.
- Humans executing packets must store artifacts in predictable locations and paste structured reports back into the session for auditability.

### Resilience features
- **Retries** — Transient command failures are retried up to `MAX_RETRIES` (default 2) with exponential backoff; persistent errors escalate to `stuck`.
- **Timeouts** — Long-running todos enforce default 8-minute execution and 4-minute verification timeouts; overridable per item.
- **Isolation** — Every todo executes in a clean MCP task context, preventing cross-contamination of state.
- **Observability** — All phases emit structured events, enabling dashboards to track todo progress, error rates, and throughput.

### Extension points
- Configure MCP tools via `config.toml` profiles for language-specific tooling.
- Register additional telemetry sinks by setting `RUST_LOG` and enabling JSON streaming for machine consumption.
- Customize sandbox defaults with `codex exec --sandbox` or profile presets to balance safety and capability.

### Migration checklist
1. Regenerate orchestration instructions (`.codex/CODEX.md`) to align with the state machine defined here.
2. Update agent guides in `.codex/agents/` to follow deterministic templates.
3. Enable JSONL streaming for automation and wire up monitoring to `codex-tui.log`.
4. Roll out per-todo timeout and retry metadata; persist queue state between turns if required.
