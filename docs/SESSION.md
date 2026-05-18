# DebugPilot Session Log

## Session: 2026-05-18

### What was built
- **DebugPilot** — AI-powered error analysis tool
- Paste error trace → get root cause + fix
- Supports: Python, JavaScript, Go, Rust, PHP, Ruby
- Runs locally, no external service needed

### Project location
`~/projects/debug-pilot/`

### GitHub
https://github.com/powds/debug-pilot

### Test results
- Python ImportError: ✓ Detects module issues
- JavaScript TypeError: ✓ Parses stack traces correctly

### Files created
```
debug-pilot/
├── SKILL.md           # Hermes skill integration
├── debug_pilot.py     # Main analysis script (22KB)
├── requirements.txt   # Python dependencies
├── README.md          # Project docs
└── docs/
    ├── ALGORITHM.md   # How analysis works (to be created)
    └── SESSION.md     # This file
```

### How it works
1. Parse error trace → extract language, error type, frames
2. Detect category (import, type, syntax, network, etc.)
3. Match against known patterns for fix templates
4. Generate root cause explanation + actionable fix

### Error categories supported
- import (ImportError, ModuleNotFoundError)
- type (TypeError, type mismatch)
- syntax (SyntaxError, parse error)
- reference (ReferenceError, undefined)
- network (connection refused, timeout)
- permission (access denied)
- memory (OOM, memory error)
- value (ValueError, KeyError, IndexError)

### Next steps
1. Add Go panic parsing
2. Add Rust error handling
3. Support error file reading from paste
4. Add --json output for integration
5. Add confidence scoring

### Key decisions
- Pattern matching + heuristic (no ML needed)
- Focus on actionable fixes, not just explanation
- Support multi-language via detection
- Markdown output for readability, Telegram-friendly