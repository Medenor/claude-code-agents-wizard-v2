# OpenAI Codex Agent Orchestration System v2 🚀

A simple yet powerful orchestration system purpose-built for the **OpenAI Codex CLI**. It uses specialized Codex agents to manage complex projects from start to finish, with mandatory human oversight and visual testing.

## 🎯 What Is This?

This is a **custom orchestration system** that transforms how you build software projects with the OpenAI Codex CLI. The master Codex orchestrator manages the big picture while delegating individual tasks to specialized subagents:

- **🧠 Codex Orchestrator (You)** - The large-context master coordinator managing todos and the big picture
- **✍️ Coder Subagent** - Implements one todo at a time in its own clean context
- **👁️ Tester Subagent** - Verifies implementations using Playwright in its own context
- **🆘 Stuck Subagent** - Human escalation point when ANY problem occurs

## ⚡ Key Features

- **No Fallbacks**: When ANY agent hits a problem, you get asked - no assumptions, no workarounds
- **Visual Testing**: Playwright MCP integration for screenshot-based verification
- **Todo Tracking**: Always see exactly where your project stands
- **Simple Flow**: The orchestrator creates todos → delegates to coder → tester verifies → repeat
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

The orchestrator will automatically:
1. Create a detailed todo list using TodoWrite
2. Delegate the first todo to the **coder** subagent
3. The coder implements in its own clean context window
4. Delegate verification to the **tester** subagent (Playwright screenshots)
5. If ANY problem occurs, the **stuck** subagent asks you what to do
6. Mark todo complete and move to the next one
7. Repeat until project complete

### The Workflow

```
USER: "Build X"
    ↓
ORCHESTRATOR: Creates detailed todos with TodoWrite
    ↓
ORCHESTRATOR: Invokes coder subagent for todo #1
    ↓
CODER (own context): Implements feature
    ↓
    ├─→ Problem? → Invokes STUCK → You decide → Continue
    ↓
CODER: Reports completion
    ↓
ORCHESTRATOR: Invokes tester subagent
    ↓
TESTER (own context): Playwright screenshots & verification
    ↓
    ├─→ Test fails? → Invokes STUCK → You decide → Continue
    ↓
TESTER: Reports success
    ↓
ORCHESTRATOR: Marks todo complete, moves to next
    ↓
Repeat until all todos done ✅
```

## 🛠️ How It Works

### Codex Orchestrator
**Your expansive context window (gpt-5-codex-high)**

- Creates and maintains comprehensive todo lists
- Sees the complete project from A-Z
- Delegates individual todos to specialized subagents
- Tracks overall progress across all tasks
- Maintains project state and context

**How it works**: The Codex orchestrator uses its large context window to manage everything and delegates coding and verification to subagents running `gpt-5-codex-medium`.

### Coder Subagent
**Fresh Context Per Task**

- Gets invoked with ONE specific todo item
- Works in its own clean context window
- Writes clean, functional code
- **Never uses fallbacks** - invokes stuck agent immediately
- Reports completion back to the orchestrator

**When it's used**: The orchestrator delegates each coding todo to this subagent

### Tester Subagent
**Fresh Context Per Verification**

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

The orchestrator invokes coder(todo #1: "Set up HTML structure")

Coder (own context): Creates index.html
Coder: Reports completion to the orchestrator

The orchestrator invokes tester("Verify HTML structure loads")

Tester (own context): Uses Playwright to navigate
Tester: Takes screenshot
Tester: Verifies HTML structure visible
Tester: Reports success to the orchestrator

The orchestrator: Marks todo #1 complete ✓

The orchestrator invokes coder(todo #2: "Create hero section")

Coder (own context): Implements hero section
Coder: ERROR - image file not found
Coder: Invokes stuck subagent

Stuck (own context): Asks YOU:
  "Hero image 'hero.jpg' not found. How to proceed?"
  Options:
  - Use placeholder image
  - Download from Unsplash
  - Skip image for now

You choose: "Download from Unsplash"

Stuck: Returns your decision to coder
Coder: Proceeds with Unsplash download
Coder: Reports completion to the orchestrator

... and so on until all todos done
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
├── .mcp.json                  # Playwright MCP configuration
├── .gitignore
└── README.md
```

## 🎓 Learn More

### Resources

- **[SEO Grove](https://seogrove.ai)** - AI-powered SEO automation platform
- **[ISS AI Automation School](https://www.skool.com/iss-ai-automation-school-6342/about)** - Join our community to learn AI automation
- **[Income Stream Surfers YouTube](https://www.youtube.com/incomestreamsurfers)** - Tutorials, breakdowns, and AI automation content

### Support

Have questions or want to share what you built?
- Join the [ISS AI Automation School community](https://www.skool.com/iss-ai-automation-school-6342/about)
- Subscribe to [Income Stream Surfers on YouTube](https://www.youtube.com/incomestreamsurfers)
- Check out [SEO Grove](https://seogrove.ai) for automated SEO solutions

## 🤝 Contributing

This is an open system! Feel free to:
- Add new specialized agents
- Improve existing agent prompts
- Share your agent configurations
- Submit PRs with enhancements

## 📝 How It Works Under the Hood

This system leverages the subagent capabilities available in the OpenAI Codex CLI:

1. **CODEX.md** instructs the Codex CLI orchestrator (running `gpt-5-codex-high`)
2. **Subagents** are defined in `.codex/agents/*.md` and run on `gpt-5-codex-medium`
3. **Each subagent** gets its own fresh context window
4. **Main orchestrator** maintains the large-context workspace with todos and project state
5. **Playwright MCP** is configured in `.mcp.json` for visual testing

The magic happens because:
- **Codex orchestrator (large context)** = Maintains big picture, manages todos
- **Coder (fresh context)** = Implements one task at a time
- **Tester (fresh context)** = Verifies one implementation at a time
- **Stuck (fresh context)** = Handles one problem at a time with human input
- **Each subagent** has specific tools and hardwired escalation rules

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

Built by [Income Stream Surfer](https://www.youtube.com/incomestreamsurfers)

Powered by the OpenAI Codex CLI and Playwright MCP.

---

**Ready to build something amazing?** Run `codex` in this directory and tell it what you want to create! 🚀
