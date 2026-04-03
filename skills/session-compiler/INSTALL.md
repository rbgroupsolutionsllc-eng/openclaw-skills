# Session Compiler — Installation

## Requirements

- Python 3.10+
- OpenClaw (any version with JSONL session format v3+)
- No additional Python packages needed

## Install

Clone this repo to a temporary location. Copy the files from `skills/session-compiler/` into your setup:

```bash
# 1. Clone
git clone https://github.com/rbgroupsolutionsllc-eng/openclaw-skills.git /tmp/openclaw-skills

# 2. Copy SKILL.md to your agent workspace
mkdir -p ~/.openclaw/workspace/skills/session-compiler
cp /tmp/openclaw-skills/skills/session-compiler/SKILL.md \
   ~/.openclaw/workspace/skills/session-compiler/

# 3. Copy script to your OpenClaw bin/skills
cp /tmp/openclaw-skills/skills/session-compiler/scripts/session_compiler.py \
   ~/.openclaw/bin/skills/
chmod +x ~/.openclaw/bin/skills/session_compiler.py

# 4. Add to PATH (choose your PATH directory)
ln -sfn ~/.openclaw/bin/skills/session_compiler.py \
   /home/linuxbrew/.linuxbrew/bin/session_compiler
# or: ~/.local/bin/session_compiler
# or: /usr/local/bin/session_compiler

# 5. Clean up
rm -rf /tmp/openclaw-skills
```

## Update

```bash
git clone https://github.com/rbgroupsolutionsllc-eng/openclaw-skills.git /tmp/openclaw-skills

cp /tmp/openclaw-skills/skills/session-compiler/scripts/session_compiler.py \
   ~/.openclaw/bin/skills/
cp /tmp/openclaw-skills/skills/session-compiler/SKILL.md \
   ~/.openclaw/workspace/skills/session-compiler/

rm -rf /tmp/openclaw-skills
```

## Verify

After installing, restart your OpenClaw agent session, then run:

```bash
session_compiler --list
```

Or ask your agent:

```
/recall
```

## Uninstall

```bash
rm ~/.openclaw/bin/skills/session_compiler.py
rm -rf ~/.openclaw/workspace/skills/session-compiler
rm /home/linuxbrew/.linuxbrew/bin/session_compiler  # or wherever you linked it
```
