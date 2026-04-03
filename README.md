# openclaw-skills

**Specialized skills for [OpenClaw](https://openclaw.dev) agents.**

Each skill is a self-contained folder with a `SKILL.md` (the agent instruction file) and an optional `scripts/` directory. Drop a skill into your agent's workspace skills folder and it's immediately available.

> **OpenClaw-native.** These skills are built for the OpenClaw session format and tool system, not Claude Code or other runtimes.

---

## Skills

| Skill | Description |
|-------|-------------|
| [`session-compiler`](skills/session-compiler/) | Compile OpenClaw JSONL session logs into readable, searchable transcripts. Enables `/recall`, `/readchat`, `/searchchat`. |
| [`backpressure`](skills/backpressure/) | Deterministic self-verification checks for agents. Run after every code or config change to catch errors before they propagate. |

### Recommended companion: Agent-Skills for Context Engineering

The following skills from [muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) work well alongside these OpenClaw-native skills. Install them directly from that repo:

```bash
BASE="https://raw.githubusercontent.com/muratcankoylan/Agent-Skills-for-Context-Engineering/main/skills"
DEST="~/.openclaw/workspace/skills"

for skill in context-fundamentals context-degradation context-compression context-optimization filesystem-context memory-systems tool-design multi-agent-patterns; do
  mkdir -p "$DEST/$skill"
  curl -sS "$BASE/$skill/SKILL.md" -o "$DEST/$skill/SKILL.md"
done
```

| Skill | When Kairo uses it |
|-------|-------------------|
| `context-fundamentals` | Design/debug agent architecture, explain context windows |
| `context-degradation` | Agent fails on long sessions, lost-in-middle symptoms, context poisoning |
| `context-compression` | Handle compaction events, summarize session history |
| `context-optimization` | Token costs too high, need masking/caching/partitioning |
| `filesystem-context` | Offload large tool outputs, plan persistence, multi-agent workspaces |
| `memory-systems` | Choose memory framework, design knowledge graph, cross-session persistence |
| `tool-design` | Create or audit agent tools/scripts |
| `multi-agent-patterns` | Design subagent handoffs, orchestration, context isolation |

---

## Installation

### Single skill (manual)

```bash
# 1. Clone to a temp location
git clone https://github.com/rbgroupsolutionsllc-eng/openclaw-skills.git /tmp/openclaw-skills

# 2. Copy the skill folder into your agent workspace
cp -r /tmp/openclaw-skills/skills/session-compiler ~/.openclaw/workspace/skills/

# 3. Copy the script to your OpenClaw bin
cp /tmp/openclaw-skills/skills/session-compiler/scripts/session_compiler.py ~/.openclaw/bin/skills/
chmod +x ~/.openclaw/bin/skills/session_compiler.py

# 4. Symlink to PATH (adjust to your PATH)
ln -sfn ~/.openclaw/bin/skills/session_compiler.py /home/linuxbrew/.linuxbrew/bin/session_compiler

# 5. Remove temp clone
rm -rf /tmp/openclaw-skills
```

### Update

```bash
git clone https://github.com/rbgroupsolutionsllc-eng/openclaw-skills.git /tmp/openclaw-skills
cp /tmp/openclaw-skills/skills/session-compiler/scripts/session_compiler.py ~/.openclaw/bin/skills/
cp -r /tmp/openclaw-skills/skills/session-compiler/SKILL.md ~/.openclaw/workspace/skills/session-compiler/
rm -rf /tmp/openclaw-skills
```

### Verify

After installing, ask your OpenClaw agent:

```
/recall
```

or:

```
session_compiler --list
```

---

## Requirements

- Python 3.10+
- OpenClaw (any recent version)
- No additional Python packages required

---

## Contributing

Skills accepted via PR. Each skill must include:
- `SKILL.md` — agent instruction file with frontmatter (`name`, `description`)
- Tested on OpenClaw ≥ 2026.x
- `scripts/` folder for any companion executables

---

## License

MIT
