---
name: debug-pilot
description: "AI-powered error analysis. Paste error trace → get root cause + fix. Supports Python, JavaScript, Go, Rust, PHP, Ruby."
version: 1.0.0
author: powds
license: MIT
metadata:
  debug-pilot:
    tags: [debugging, error-analysis, developer-tools, ai]
    homepage: https://github.com/powds/debug-pilot
---

# DebugPilot Skill

AI-powered error analysis. Paste an error trace → get root cause + actionable fix.

## Usage

### Command Line

```bash
# Analyze error from stdin
echo "Traceback (most recent call last):" | python debug_pilot.py

# From file
python debug_pilot.py --file ./error.log

# With context
python debug_pilot.py --error "ImportError" --context "import requests"

# Language specific
python debug_pilot.py --error "TypeError" --lang python
```

### Hermes Integration

```bash
# Interactive mode
/hermes debug-pilot

# Quick analysis
/hermes paste error trace
```

## Output Format

```
🔍 DebugPilot Analysis
━━━━━━━━━━━━━━━━━━━━━━

Error Type: ImportError
File: app/api/generate.py
Line: 42

💡 Root Cause:
The module 'requests' is not installed in the current environment.

🔧 Fix:
# Install the missing package
pip install requests

# Or add to requirements.txt
echo "requests==2.28.0" >> requirements.txt

📚 Reference:
https://docs.python.org/3/library/exceptions.html#ImportError
```

## Configuration

Create `~/.debug-pilot/config.yaml`:

```yaml
analysis:
  max_context_lines: 50
  include_reference_links: true
  confidence_threshold: 0.7

languages:
  python:
    traceback_pattern: "Traceback \\(most recent call last\\):"
    line_pattern: 'File "(.+)", line (\d+)'
  javascript:
    line_pattern: "at (.+) \((.+):(\d+):(\d+)\)"
  go:
    line_pattern: "panic: (.+)"

output:
  format: markdown
  color: true
```

## Files

```
debug-pilot/
├── SKILL.md           # This file
├── debug_pilot.py     # Main analysis script
├── config.yaml        # Default config
├── requirements.txt   # Python dependencies
├── docs/
│   ├── ALGORITHM.md   # How analysis works
│   └── SESSION.md     # Session log
└── README.md          # Project overview
```