# Codex CLI Orchestrator Limitation Report

## Background
During a Codex CLI session in `/Users/raphael/claude-code-agents-wizard-v2/claude-code-agents-wizard-v2`, the orchestrator agent reviewed `.codex/CODEX.md`, which assigns it sole responsibility for planning and delegation. The environment was configured with sandbox mode `workspace-write`, network access `restricted`, shell `zsh`, and approval policy `on-request`.

## Discussion summary
- User asked for a simple “Hello, world!” HTML file.
- Orchestrator drafted a todo for a coder subagent but could not dispatch it because no subagent interface exists in the current CLI harness.
- Follow-up questions confirmed that having CODER.md or dividing roles within `.codex/agents/` does not instantiate subordinate agents.
- User requested documentation of this limitation and potential remedies.

## Identified limitation
The Codex CLI session exposes only file-system and shell access to the orchestrator. There is no mechanism for the orchestrator to invoke coder, tester, or stuck subagents, nor to assume their roles, even when instructions exist. As a result, orchestration cannot progress beyond planning when implementation or verification tasks are required.

## Impact
- Orchestrator-only mode prevents automated fulfillment of user requests that require code changes or test execution.
- Limits experimentation with the full orchestrated workflow described in `.codex/CODEX.md`.
- Users must manually perform coding/testing steps or override role constraints, undermining the orchestrator abstraction.

## Suggested fixes
1. Provide CLI commands or APIs for the orchestrator to launch coder, tester, and stuck subagents and collect their outputs (diffs, logs, screenshots).
2. Include a local dispatcher stub or plugin that emulates these subagents for offline workflows.
3. Offer an explicit override flag that allows the orchestrator to temporarily assume coder/tester roles with safeguards.
4. Update documentation (README, `.codex/CODEX.md`) to detail current limitations and required infrastructure for full orchestration.

## Recommended next steps
- Determine whether subagent execution will occur locally or via a remote control plane, and implement the necessary connectors.
- Update the CLI and documentation once subagent invocation is supported.
- Add regression tests or simulations to ensure future updates preserve orchestrator-subagent integrations.
