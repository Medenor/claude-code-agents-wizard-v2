# OpenAI Codex Agent Orchestration System v2 🚀

A simple yet powerful orchestration system purpose-built for the **OpenAI Codex CLI**. It uses specialized Codex agents to manage complex projects from start to finish, with mandatory human oversight and visual testing.

Original orchestrator by [Income Stream Surfer](https://github.com/IncomeStreamSurfer/claude-code-agents-wizard-v2) for Claude Code CLI.

## 🎯 What Is This?

This is a **custom orchestration system** that transforms how you build software projects with the OpenAI Codex CLI. The master Codex orchestrator manages the big picture and emits structured instructions so humans (or future automation) can act as specialized subagents:

- **🧠 Codex Orchestrator (You)** - The large-context master coordinator managing todos and the big picture
- **✍️ Coder Subagent** - Implements one todo at a time following manual delegation packets
- **👁️ Tester Subagent** - Verifies implementations using Playwright or a browser, guided by manual packets
- **🆘 Stuck Subagent** - Human escalation point when ANY problem occurs

## ⚡ Key Features

- **No Fallbacks**: When ANY agent hits a problem, you get asked - no assumptions, no workarounds
- **Visual Testing**: Playwright MCP integration for screenshot-based verification
- **Todo Tracking**: Always see exactly where your project stands
- **Manual Friendly Flow**: The orchestrator creates todos → emits Manual Delegation Packets → humans execute coder/tester/stuck instructions → repeat
- **Human Control**: The stuck agent ensures you're always in the loop

## 🚀 Quick Start

### Prerequisites

1. **OpenAI Codex CLI** installed ([instructions](https://platform.openai.com/docs/guides/devtools))
2. **Node.js** (for Playwright MCP)

### Installation

```bash
# Clone this repository
git clone https://github.com/IncomeStreamSurfer/claude-code-agents-wizard-v2.git
cd claude-code-agents-wizard-v2

# Start the agent system in this directory using the Codex CLI
codex
```

That's it! The Codex CLI automatically loads the orchestration instructions from the `.codex/` directory.

## 📖 How to Use

### Starting a Project

When you want to build something, just tell the Codex orchestrator your requirements:

```
You: "Build a todo app with React and TypeScript"
```

The orchestrator will:
1. Create a detailed todo list using TodoWrite.
2. Emit a **Manual Delegation Packet** for the first todo targeting the CODER role.
3. You (or another human) open `.codex/agents/coder.md`, follow the instructions, and return the completion template.
4. Paste the coder’s response back into the orchestrator turn.
5. The orchestrator records the evidence and emits the next packet—usually for the TESTER role.
6. Repeat the manual handoff cycle until the todo is closed, then advance to the next item.
7. Invoke the STUCK agent via manual packet whenever clarification or human decisions are required.

### The Workflow

```
USER: "Build X"
    ↓
ORCHESTRATOR: Creates detailed todos with TodoWrite
    ↓
ORCHESTRATOR: Emits Manual Delegation Packet → CODER
    ↓
HUMAN CODER: Follows `.codex/agents/coder.md`, implements feature, returns report
    ↓
    ├─→ Problem? → Orchestrator emits STUCK packet → Human decision → Continue
    ↓
ORCHESTRATOR: Logs coder report, updates evidence
    ↓
ORCHESTRATOR: Emits Manual Delegation Packet → TESTER
    ↓
HUMAN TESTER: Performs verification, captures screenshots/logs, returns report
    ↓
    ├─→ Test fails? → Orchestrator emits STUCK packet → Human decision → Continue
    ↓
ORCHESTRATOR: Marks todo complete, moves to next
    ↓
Repeat until all todos done ✅
```

### Manual Delegation Packets

Every packet you copy from the orchestrator should remain SMART so the acting agent has the right amount of context without overflowing their prompt:

- **Specific** — include the objective, relevant background, and file paths the agent cannot infer.
- **Measurable** — list acceptance criteria, commands to run, or artifacts (diffs, screenshots, logs) required for completion.
- **Achievable** — scope each packet to a single todo that can be finished in one focused turn.
- **Relevant** — tie the work back to the current project milestone and mention upstream dependencies or decisions.
- **Time-bound** — reference the todo deadline or add a short note when urgency matters.

Keep packets concise but complete; link to prior evidence or decisions via filenames rather than repeating long transcripts.

## 🛠️ How It Works

### Codex Orchestrator
**Your expansive context window (gpt-5-codex-high)**

- Creates and maintains comprehensive todo lists
- Sees the complete project from A-Z
- Produces Manual Delegation Packets for specialized roles
- Tracks overall progress across all tasks
- Maintains project state and context

**How it works**: The Codex orchestrator uses its large context window to manage everything, then shares manual packets so humans (or future automated subagents) can perform coding, testing, and escalation steps in smaller contexts.

### Coder Subagent
**Fresh Context Per Task**

- **Manual mode today**: A human follows the packet plus `.codex/agents/coder.md`.
- Gets invoked with ONE specific todo item
- Works in its own clean context window
- Writes clean, functional code
- **Never uses fallbacks** - invokes stuck agent immediately
- Reports completion back to the orchestrator

**When it's used**: The orchestrator delegates each coding todo to this subagent

### Tester Subagent
**Fresh Context Per Verification**

- **Manual mode today**: A human runs the verification and captures evidence.
- Gets invoked after each coder completion
- Works in its own clean context window
- Uses **Playwright MCP** to see rendered output
- Takes screenshots to verify layouts
- Tests interactions (clicks, forms, navigation)
- **Never marks failing tests as passing**
- Reports pass/fail back to the orchestrator

**When it's used**: The orchestrator delegates testing after every implementation

### Stuck Subagent
**Fresh Context Per Problem**

- **Manual mode today**: A human relays questions and decisions using the packet template.
- Gets invoked when coder or tester hits a problem
- Works in its own clean context window
- **ONLY subagent** that can ask you questions
- Presents clear options for you to choose
- Blocks progress until you respond
- Returns your decision to the calling agent
- Ensures no blind fallbacks or workarounds

**When it's used**: Whenever ANY subagent encounters ANY problem

## 🚨 The "No Fallbacks" Rule

**This is the key differentiator:**

Traditional AI: Hits error → tries workaround → might fail silently
**This system**: Hits error → asks you → you decide → proceeds correctly

Every agent is **hardwired** to invoke the stuck agent rather than use fallbacks. You stay in control.

## 💡 Example Session

```
You: "Build a landing page with a contact form"

The orchestrator creates todos:
  [ ] Set up HTML structure
  [ ] Create hero section
  [ ] Add contact form with validation
  [ ] Style with CSS
  [ ] Test form submission

The orchestrator emits Manual Delegation Packet → CODER(todo #1: "Set up HTML structure")

You copy the packet, open `.codex/agents/coder.md`, create `index.html`, and return the completion template.

The orchestrator logs the report, then emits Manual Delegation Packet → TESTER("Verify HTML structure loads")

You (or a teammate) follow `.codex/agents/tester.md`, capture screenshots, and return the verification template.

The orchestrator marks todo #1 complete ✓

Next, the orchestrator emits Manual Delegation Packet → CODER(todo #2: "Create hero section")

While implementing, you notice `hero.jpg` is missing. Report `STATUS: failed` and request a STUCK packet.

The orchestrator emits Manual Delegation Packet → STUCK describing the missing asset.

You choose "Download from Unsplash" in the stuck template, return the decision, and resume coding.

... repeat the manual loop until every todo is done.
```

## 📁 Repository Structure

```
.
├── .codex/
│   ├── CODEX.md               # Master orchestrator instructions for the Codex CLI
│   └── agents/
│       ├── coder.md          # Codex coder subagent definition
│       ├── tester.md         # Codex tester subagent definition
│       └── stuck.md          # Codex stuck subagent definition
├── codex-cli-orchestrator-limitations.md  # Notes on current CLI constraints
├── docs/
│   ├── dry-run-smart-todo.md             # SMART todo dry-run walkthrough
│   └── manual-delegation-sample.md       # End-to-end manual delegation example
├── .mcp.json                  # Playwright MCP configuration
├── .gitignore
├── orchestration-architecture.md         # High-level architecture reference
├── scripts/
│   ├── compare_workflows.py              # Baseline vs. live workflow diff
│   ├── ingest_codex_jsonl.py             # Normalize Codex JSONL traces
│   └── run_workflow_simulation.py        # Generate simulated workflow logs
└── README.md
```
## 🤝 Contributing

This is an open system! Feel free to:
- Add new specialized agents
- Improve existing agent prompts
- Share your agent configurations
- Submit PRs with enhancements

## 📝 How It Works Under the Hood

This system is architected for automated subagents but currently operates in **manual delegation mode** inside the OpenAI Codex CLI:

1. **CODEX.md** instructs the Codex CLI orchestrator (running `gpt-5-codex-high`) and defines the Manual Delegation Packet format.
2. **Subagent guides** in `.codex/agents/*.md` describe how humans should execute CODER, TESTER, and STUCK responsibilities.
3. **Manual Delegation Packets** are copied into the session so humans can perform each role deterministically and return structured reports.
4. **Main orchestrator** maintains the large-context workspace with todos and project state, updating evidence as packets are fulfilled.
5. **Playwright MCP** (optional) remains available in `.mcp.json` for testers who want automated browser support.

The magic happens because:
- **Codex orchestrator (large context)** = Maintains big picture, manages todos, issues packets
- **Coder role** = Implements one task per packet with clear acceptance criteria
- **Tester role** = Verifies one implementation at a time and supplies artifacts
- **Stuck role** = Handles one problem at a time with human decisions
- **Each role** adheres to deterministic templates, ensuring the orchestrator can stitch results back together

## 🎯 Best Practices

1. **Trust the Codex orchestrator** - Let it create and manage the todo list
2. **Review screenshots** - The tester provides visual proof of every implementation
3. **Make decisions when asked** - The stuck agent needs your guidance
4. **Don't interrupt the flow** - Let subagents complete their work
5. **Check the todo list** - Always visible, tracks real progress

## 🔥 Pro Tips

- Use `agents` in the Codex CLI to see all available subagents
- The orchestrator maintains the todo list in its large context - check anytime
- Screenshots from tester are saved and can be reviewed
- Each subagent has specific tools - check their `.md` files
- Subagents get fresh contexts - no context pollution!

## 📜 License

MIT - Use it, modify it, share it!

## 🙏 Credits

Original orchestrator by [Income Stream Surfer](https://github.com/IncomeStreamSurfer/claude-code-agents-wizard-v2)

Powered by the OpenAI Codex CLI and Playwright MCP.

---
