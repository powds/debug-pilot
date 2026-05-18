# DebugPilot Algorithm

This document explains how DebugPilot analyzes error traces.

## Overview

DebugPilot uses a three-stage analysis pipeline:
1. **Parse** — Extract structure from raw error text
2. **Categorize** — Match against known error patterns
3. **Diagnose** — Generate root cause and fix

## Stage 1: Parsing

### Language Detection

```python
def detect_language(error_text: str) -> str:
    # Python: "Traceback (most recent call last):"
    # JavaScript: "at functionName (file.js:line:col)"
    # Go: "panic: message"
    # Rust: "thread 'main' panicked at"
```

### Python Traceback Format

```
Traceback (most recent call last):
  File "path/to/file.py", line 42, in function_name
    code_line()
ErrorType: Error message
```

Regex patterns:
- File/line: `r'  File "([^"]+)", line (\d+)'`
- Error: `r'(\w+Error): (.+)'`

### JavaScript Stack Trace

```
ErrorType: message
    at functionName (file.js:42:15)
    at anotherFunction (file.js:15:3)
```

Regex patterns:
- Full: `r'at (.+) \((.+):(\d+):(\d+)\)'`
- Simple: `r'at (.+):(\d+):(\d+)'`

## Stage 2: Categorization

Errors are categorized by matching against known patterns:

| Category | Patterns | Example Fix |
|----------|----------|-------------|
| import | ImportError, ModuleNotFoundError | pip install |
| type | TypeError, type mismatch | type checking |
| syntax | SyntaxError, parse error | linter |
| reference | ReferenceError, undefined | variable check |
| network | connection refused, timeout | server check |
| permission | access denied, forbidden | chmod/chown |
| memory | OOM, memory error | batch processing |
| value | ValueError, KeyError, IndexError | input validation |

## Stage 3: Diagnosis

### Root Cause Generation

Each category has a base explanation template. For example:

```python
'import': "ModuleNotFoundError occurs when Python cannot find 
           or load the required module. This usually means the 
           package is not installed in the current environment."
```

Frame analysis adds file-specific context from the traceback.

### Fix Template Matching

Common fixes are stored as templates, matched by error type/message:

```python
COMMON_FIXES = {
    'ImportError': "pip install <package>",
    'undefined is not a function': "Check object.method vs object.method()",
    'connection refused': "Check server running, port, firewall",
}
```

### Suggestions

Each category has a suggestion list:

```python
'import': [
    "1. Check package installed: pip list",
    "2. Install missing: pip install <name>",
    "3. Verify correct environment activated"
]
```

## Confidence Scoring

Analysis includes confidence level:

- **High (0.8+)**: Exact pattern match, clear error type
- **Medium (0.5-0.8)**: Partial match, known category
- **Low (<0.5)**: Unknown error, generic analysis

## Limitations

DebugPilot uses pattern matching, not true static analysis:
- Cannot detect logical errors (wrong algorithm)
- Cannot fix all edge cases
- Cannot analyze compiled languages deeply

Best for: common errors, framework issues, quick fixes
Not for: complex business logic bugs, race conditions