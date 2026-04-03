---
name: backpressure
description: "Self-verification checks for OpenClaw agents. Read BACKPRESSURE.md and run the relevant checks after every code or config change. Use when writing scripts, modifying openclaw.json, cron jobs, or any file in bin/skills/."
---

# BACKPRESSURE — OpenClaw Self-Verification

After every code or config change, run the checks defined in `BACKPRESSURE.md` before reporting the task as done.

## When to Run

| Change made | Checks to run |
|-------------|---------------|
| Created or edited a `.py` script | Syntax, Executable, Help, Path |
| Modified `openclaw.json` | Config (openclaw.json) |
| Modified `models.json` | Config (models.json) |
| Modified `cron/jobs.json` | Cron |
| New script uses non-stdlib imports | Imports |
| Changed any plugin/model config | Config + Gateway (on-demand) |

## How to Run the Checks

**Syntax check** (replace `<file>` with actual path):
```bash
python3 -m py_compile ~/.openclaw/bin/skills/<script>.py && echo PASS || echo FAIL
```

**Executable check**:
```bash
test -x ~/.openclaw/bin/skills/<script>.py && echo PASS || echo FAIL
```

**Config check**:
```bash
python3 -m json.tool /home/$USER/.openclaw/openclaw.json > /dev/null && echo PASS || echo FAIL
```

**Help check**:
```bash
python3 ~/.openclaw/bin/skills/<script>.py --help && echo PASS || echo FAIL
```

**Path / symlink check**:
```bash
test -L $(which <name> 2>/dev/null) && echo PASS || echo FAIL
```

**Imports check** (run for each non-stdlib package the script uses):
```bash
python3 -c "import <package>" && echo PASS || echo FAIL
```

**Gateway check** (only after plugin or provider config changes):
```bash
pm2 jlist | python3 -c "import sys,json; p=json.load(sys.stdin); g=[x for x in p if x['name']=='kairo-gateway']; sys.exit(0 if g and g[0]['pm2_env']['status']=='online' else 1)" && echo ONLINE || echo OFFLINE
```

**Cron check**:
```bash
python3 -m json.tool /home/$USER/.openclaw/cron/jobs.json > /dev/null && echo PASS || echo FAIL
```

## Rules

- **Blocking checks must pass before reporting done.** Do not skip them.
- **Warning checks** (Path, Gateway) — report the result but do not block.
- **Never fabricate a passing result.** If a check fails, fix the issue and re-run.
- For scripts with multiple dependencies, run the Imports check for each one.

## Template: New Skill Checklist

When you create a new skill script at `~/.openclaw/bin/skills/<name>.py`:

```bash
# 1. Syntax
python3 -m py_compile ~/.openclaw/bin/skills/<name>.py

# 2. Executable
chmod +x ~/.openclaw/bin/skills/<name>.py
test -x ~/.openclaw/bin/skills/<name>.py

# 3. Help works
python3 ~/.openclaw/bin/skills/<name>.py --help

# 4. Symlink to PATH (adjust directory to your PATH)
ln -sfn ~/.openclaw/bin/skills/<name>.py /home/linuxbrew/.linuxbrew/bin/<name>

# 5. Imports (for each non-stdlib package)
python3 -c "import <package>"
```

All 5 must pass before the skill is considered deployed.

## BACKPRESSURE.md Template

Place this at the root of your OpenClaw workspace (`~/.openclaw/workspace/BACKPRESSURE.md`):

```markdown
# BACKPRESSURE.md

> Deterministic verification checks for OpenClaw workspace.
> Agents: run these checks after every code or config change. Do not proceed if blocking checks fail.

## Syntax

- `python3 -m py_compile <file>` — exit 0, no syntax errors
  - severity: blocking
  - when: after-every-change

## Executable

- `test -x ~/.openclaw/bin/skills/<script>.py && echo OK` — prints OK
  - severity: blocking
  - when: after-every-change

## Config

- `python3 -m json.tool ~/.openclaw/openclaw.json > /dev/null` — exit 0
  - severity: blocking
  - when: after-every-change

## Help

- `python3 ~/.openclaw/bin/skills/<script>.py --help` — exit 0
  - severity: blocking
  - when: after-every-change

## Path

- `test -L $(which <name>) && echo OK` — prints OK
  - severity: warning
  - when: after-every-change

## Imports

- `python3 -c "import <package>"` — exit 0
  - severity: blocking
  - when: on-demand

## Gateway

- `pm2 jlist | python3 -c "..."` — prints ONLINE
  - severity: warning
  - when: on-demand
```
