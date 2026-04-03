---
name: session-compiler
description: "Compile OpenClaw JSONL session logs into readable and searchable transcripts. Use when the user says /recall, /readchat, /searchchat, or wants to recover context from previous conversations."
---

# Session Compiler — OpenClaw

Compiles OpenClaw JSONL session files into adaptive views for reading, searching, and context recovery across conversations.

## Basic Usage

```bash
session_compiler <file.jsonl>                   # generates .txt + .min.txt
session_compiler <file.jsonl> --grep "pattern"  # search within session
session_compiler --list                          # list available sessions
session_compiler --current                       # compile active session
```

## Output Files

| File | Description |
|------|-------------|
| `.txt`     | Full lossless transcript |
| `.min.txt` | Scannable outline: truncated text, tool calls as one-liners, tool results omitted |

Files are written **next to the input JSONL** by default. Do NOT clean them up after use unless the user explicitly asks.

## Rules

- **Always use `--grep`, never system grep.** This script's `--grep` returns block-level line ranges with role tags that system grep cannot provide.
- Sessions live at `~/.openclaw/agents/main/sessions/` (main agent) or `~/.openclaw/agents/<name>/sessions/`.
- Use `--current` to auto-detect the active session from `sessions.json`.
- **Always `cd` into the sessions directory before multi-file glob searches** — keeps output paths short and saves tokens.

## Workflow

**1. Compile**

```bash
session_compiler ~/.openclaw/agents/main/sessions/<uuid>.jsonl
```

The console output shows line and word counts for each generated file — use this to gauge size before reading.

**2. Read `.min.txt`**

The `.min.txt` is a scannable outline:
- User and assistant text, truncated to ~200 words per block
- Tool calls summarized as `* toolname(main_argument)`
- Tool results omitted (read `.txt` for full output)
- Thinking blocks omitted

```
[user]
check the config file

[assistant]
* read(/home/user/.openclaw/openclaw.json)
The config looks correct. The model is set to gemini-2.5-flash…

[compaction]
## Goal: User wanted to fix the gateway restart issue…
```

**3. Search with `--grep`**

```bash
session_compiler <file.jsonl> --grep "pattern"
```

Returns block-level ranges like `(uuid:L67-L81)` with matching lines marked `►`. Read those ranges in `.txt` for full context — always read a few extra lines before and after.

**4. Multi-file search**

```bash
cd ~/.openclaw/agents/main/sessions && session_compiler *.jsonl --grep "keyword"
```

Always `cd` first so output paths are short relative paths.

---

## SKILLS

### /recall — Recover context from a previous conversation

**Trigger**: User says `/recall`, or wants to resume where a previous session left off.

**Action**:

1. List sessions to find the previous one:
   ```bash
   session_compiler --list
   ```
   Most recent session (excluding current) is usually the one to recover.

2. Compile it:
   ```bash
   session_compiler ~/.openclaw/agents/main/sessions/<prev-uuid>.jsonl
   ```

3. Read `.min.txt` to understand the flow, decisions made, and final state.

4. Use `--grep` for specific details:
   ```bash
   session_compiler <file.jsonl> --grep "error|fail|config"
   ```

5. **Verify against current state** — Read any files referenced in the recovered session. Prior conversation content may be stale. Issue fresh reads for every relevant file.

---

### /readchat — Read a specific session

**Trigger**: User wants to read or review a specific session by ID or date.

**Action**:

1. If no ID given: `session_compiler --list` to find it.
2. Compile: `session_compiler ~/.openclaw/agents/main/sessions/<uuid>.jsonl`
3. Read `.min.txt` for overview, use `--grep` + `.txt` ranges for details.

---

### /searchchat — Search across sessions

**Trigger**: User wants to search the conversation history.

**Action**:

1. Browse available sessions: `session_compiler --list`
2. Search across all sessions:
   ```bash
   cd ~/.openclaw/agents/main/sessions && session_compiler *.jsonl --grep "keyword"
   ```
3. For subagent sessions, check subdirectories or other agent folders.

---

### /current — View the current session

**Trigger**: User wants to see the transcript of the ongoing session.

**Action**:
```bash
session_compiler --current
```
Auto-detects the active session from `sessions.json`.
