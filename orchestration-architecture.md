## Codex Orchestration Architecture

### Top-level components
- **Node launcher (`codex-cli/bin/codex.js`)** — Detects platform, resolves vendored binary, forwards signals, and injects PATH overlays before spawning the Rust runtime.
- **Rust runtime (`vendor/*/codex`)** — Hosts both the interactive TUI and non-interactive `exec` flows, exposes Model Context Protocol (MCP) client/server integrations, and persists logs to `~/.codex/log`.
- **Configuration home (`$CODEX_HOME`)** — Supplies persistent state (profiles, MCP launchers, cached instructions) and user overrides consumed at startup.
- **Workspace adapters** — Git repository guard, sandbox policy enforcer, and filesystem abstraction used to protect project worktrees during tool execution.

### Instruction ingestion
1. Load global guidance from `$CODEX_HOME/AGENTS.override.md` → `AGENTS.md` (see [`docs/agents_md.md`](./agents_md.md)).
2. Walk repository ancestry to merge per-directory instructions, honoring overrides and configured fallbacks.
3. Emit the merged document to the orchestrator context before the first model turn.

### Session lifecycle
| Phase | Trigger | Primary modules | Outputs |
| --- | --- | --- | --- |
| `bootstrap` | CLI invocation | Node launcher, Rust runtime | Resolved binary, configured env, initial telemetry span |
| `planning` | First user turn | Orchestrator loop, plan tool | Todo list (`todo_list` items), reasoning trace |
| `execution` | Active todo | MCP task runner, sandbox manager | Command/file deltas (`command_execution`, `file_change` items) |
| `verification` | Todo completion | Tester agent, Playwright MCP | Screenshots, test verdicts |
| `escalation` | Error/test failure | Stuck agent | AskUserQuestion payload, human decision |
| `finalize` | All todos complete | Summarizer, git status collector | Final assistant message, optional structured output |

### Event streams
- **Interactive TUI** — Logs to `~/.codex/log/codex-tui.log` with `RUST_LOG=codex_core=info,codex_tui=info,codex_rmcp_client=info`.
- **`codex exec --json`** — Emits JSONL events described in [`docs/exec.md`](./exec.md#json-output-mode), enabling downstream queue processors.
- **MCP server mode** — Surfaces `thread`, `turn`, and `item` events to connected clients; supports long-running operations with configurable timeouts.

### Data & control flow
```text
User prompt → Orchestrator planner → Todo queue → {coder → tester} loops
                                          ↓ (on error)
                                         stuck agent → AskUserQuestion → human
```
- Todo queue is processed sequentially; each item carries `id`, `status`, `deadline`, and retry metadata.
- Command executions respect sandbox policy; failure raises structured errors into the orchestration layer.
- Test artifacts (screenshots, logs) are stored alongside run metadata for traceability.

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
