# DebugPilot

**AI-powered error analysis. Paste error trace → get root cause + fix.**

DebugPilot analyzes error traces from any framework, identifies the root cause, and provides actionable fix suggestions. Runs locally via Hermes skill — no server needed.

## Features

- **Multi-framework support** — Python, JavaScript/Node.js, Go, Rust, PHP, Ruby
- **Root cause analysis** — not just what happened, but why
- **Actionable fixes** — code snippets you can copy-paste
- **Context-aware** — understands framework patterns and common mistakes
- **Self-hosted** — runs on your Mac, no external service

## Quick Start

```bash
# Install skill
hermes skills install https://raw.githubusercontent.com/powds/debug-pilot/main/SKILL.md

# Analyze error
hermes debug-pilot --error "Traceback (most recent call last):\n  File 'test.py'..."

# From file
hermes debug-pilot --file ./error.log

# Interactive mode
hermes debug-pilot
```

## Usage

### Command Line

```bash
# Single error trace
python debug_pilot.py --error "Error: connection refused at line 42"

# From file
python debug_pilot.py --file /path/to/error.log

# With context (code snippet)
python debug_pilot.py --error "ImportError: No module named 'requests'" --context "import requests"

# Language specific
python debug_pilot.py --error "TypeError: undefined" --lang javascript

# Include full traceback
python debug_pilot.py --error "$(cat traceback.txt)" --include-stack
```

### Hermes Integration

```bash
# Direct analysis
hermes debug-pilot --error "Your error message here"

# Via skill
/hermes debug-pilot
/paste error trace
```

## Supported Frameworks

| Framework | File Patterns | Common Errors |
|-----------|--------------|---------------|
| Python | .py | ImportError, TypeError, IndexError, KeyError |
| JavaScript/Node | .js, .ts, .jsx, .tsx | ReferenceError, TypeError, SyntaxError |
| Go | .go | nil pointer, type assert, goroutine panic |
| Rust | .rs | Result/Option unwrap, borrow checker |
| PHP | .php | Fatal error, exception, undefined index |
| Ruby | .rb | NoMethodError, NameError, RuntimeError |

## How It Works

1. **Parse error** — Extract error type, message, file, line number
2. **Identify framework** — Detect language and framework from trace
3. **Analyze pattern** — Match against known error patterns
4. **Generate diagnosis** — Root cause + explanation + fix

## Documentation

See [docs/](docs/) for full documentation.