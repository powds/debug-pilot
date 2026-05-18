#!/usr/bin/env python3
"""
DebugPilot - AI-powered Error Analysis

Paste error trace → get root cause + fix.
Supports: Python, JavaScript, Go, Rust, PHP, Ruby
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# === ERROR PATTERNS ===

ERROR_PATTERNS = {
    'python': {
        'traceback_header': 'Traceback (most recent call last):',
        'file_line': r'  File "([^"]+)", line (\d+)',
        'error_line': r'(\w+Error): (.+)',
        'cause_pattern': r'^\s*(.+Error): (.+?)(?:\n|$)',
    },
    'javascript': {
        'stack_trace': r'at (.+) \((.+):(\d+):(\d+)\)',
        'simple_trace': r'    at (.+):(\d+):(\d+)',
        'error_types': ['ReferenceError', 'TypeError', 'SyntaxError', 'RangeError', 'Error'],
    },
    'go': {
        'panic': r'^panic: (.+)',
        'goroutine': r'^goroutine \d+ \[',
        'file_line': r'^(\S+\.go):(\d+)',
    },
    'rust': {
        'thread_panic': r'thread \'[^\']+\' panicked at',
        'panicked_at': r'panicked at "([^"]+)":(.+)',
        'file_line': r'---> (.+):(\d+)',
    },
    'php': {
        'fatal_error': r'^(Fatal error|FParse error|Warning|Notice): (.+)',
        'stack': r'#\d+ (.+) in (.+) on line (\d+)',
    },
    'ruby': {
        'traceback': r'from (.+\.rb):(\d+)',
        'error': r'^(\w+Error): (.+)',
    }
}

COMMON_FIXES = {
    'ImportError': """# Install the missing package
pip install <package-name>

# Or check requirements.txt is installed
pip install -r requirements.txt""",

    'ModuleNotFoundError': """# Install the missing module
pip install <module-name>

# If using virtual environment, make sure it's activated
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate    # Windows""",

    'SyntaxError': """# Fix the syntax error - check for:
# - Missing colons, parentheses, brackets
# - Incorrect indentation
# - Mismatched quotes or strings
# - Missing 'def' or 'class' keywords

# Common Python syntax errors:
# - IndentationError: inconsistent use of tabs/spaces
# - EOLError: unclosed string, parenthesis, bracket""",

    'TypeError': """# Common causes and fixes:
# 1. Wrong type passed to function
# 2. None value used where expected type required
# 3. Mixing types (str + int)

# Check the line number in traceback
# Verify all variables have expected types
# Add type checking: isinstance(x, str)""",

    'ReferenceError': """# JavaScript ReferenceError - variable not defined
# Possible causes:
# 1. Variable spelled incorrectly
# 2. Variable used before declaration
# 3. let/const temporal dead zone
# 4. Scope issue (inside function vs global)

# Fix:
# - Declare variable before use
# - Check spelling matches declaration
# - Use 'typeof' to check if variable exists""",

    'undefined is not a function': """# JavaScript: calling non-function
# Check:
# 1. Function exists: typeof myFunc === 'function'
# 2. Correct object: obj.method() not obj.method
# 3. This binding: use arrow function or .bind()
# 4. Method name spelled correctly""",

    'connection refused': """# Connection refused - can't reach server
# Possible causes:
# 1. Server not running
# 2. Wrong port number
# 3. Firewall blocking
# 4. Service name incorrect

# Fix:
# - Check server is running: ps aux | grep <service>
# - Verify port: curl localhost:<port>
# - Check firewall: sudo ufw status""",

    'permission denied': """# Permission denied - access issues
# Possible causes:
# 1. File/directory permissions
# 2. User lacks required privileges
# 3. SELinux/AppArmor blocking

# Fix:
# - Check permissions: ls -la <path>
# - Fix permissions: chmod 644 <file>
# - For directories: chmod 755 <dir>
# - Check owner: chown user:group <path>""",
}

# === PARSING ===

def detect_language(error_text: str) -> str:
    """Detect programming language from error trace."""
    error_lower = error_text.lower()

    if 'traceback (most recent call last)' in error_lower:
        return 'python'
    elif any(x in error_lower for x in ['referenceerror', 'typeerror', 'syntaxerror',
                                         'at ', '.js:', '.ts:', 'node:', 'javascript']):
        return 'javascript'
    elif 'panic:' in error_lower or 'goroutine' in error_lower or 'go: ' in error_lower:
        return 'go'
    elif 'panicked' in error_lower or 'rust' in error_lower:
        return 'rust'
    elif 'fatal error' in error_lower or 'php' in error_lower:
        return 'php'
    elif 'ruby' in error_lower or '.rb:' in error_lower:
        return 'ruby'

    # Default to Python (most common for error traces)
    return 'python'

def parse_python_traceback(text: str) -> Dict:
    """Parse Python traceback."""
    lines = text.split('\n')
    frames = []
    error_type = None
    error_message = None

    for i, line in enumerate(lines):
        match = re.match(r'  File "([^"]+)", line (\d+)', line)
        if match:
            file_path = match.group(1)
            line_num = match.group(2)
            # Try to get the code line
            code_line = ''
            if i + 1 < len(lines) and lines[i + 1].strip():
                code_line = lines[i + 1].strip()
            frames.append({
                'file': file_path,
                'line': int(line_num),
                'code': code_line
            })

        # Find error
        match = re.match(r'(\w+Error): (.+)', line)
        if match:
            error_type = match.group(1)
            error_message = match.group(2)

    return {
        'language': 'python',
        'frames': frames,
        'error_type': error_type or 'UnknownError',
        'error_message': error_message or text.strip().split('\n')[-1],
        'frames_count': len(frames)
    }

def parse_javascript_trace(text: str) -> Dict:
    """Parse JavaScript error trace."""
    lines = text.split('\n')
    frames = []
    error_type = None
    error_message = None

    for line in lines:
        line = line.strip()
        # Match patterns like: at functionName (file.js:10:5)
        match = re.match(r'at (.+) \((.+):(\d+):(\d+)\)', line)
        if match:
            func_name = match.group(1)
            file_path = match.group(2)
            line_num = match.group(3)
            frames.append({
                'function': func_name,
                'file': file_path,
                'line': int(line_num)
            })
        else:
            # Simple stack line: at file.js:10:5
            match = re.match(r'at (.+):(\d+):(\d+)', line)
            if match:
                file_path = match.group(1)
                line_num = match.group(2)
                frames.append({
                    'file': file_path,
                    'line': int(line_num)
                })

        # Detect error type/message
        if 'ReferenceError' in line:
            error_type = 'ReferenceError'
            error_message = line
        elif 'TypeError' in line:
            error_type = 'TypeError'
            error_message = line
        elif 'SyntaxError' in line:
            error_type = 'SyntaxError'
            error_message = line

    # If no error type found, get from last line
    if not error_type:
        for pattern in ERROR_PATTERNS['javascript']['error_types']:
            if pattern in text:
                error_type = pattern
                break
        error_message = text.strip().split('\n')[-1] if text.strip() else 'Unknown error'

    return {
        'language': 'javascript',
        'frames': frames,
        'error_type': error_type or 'Error',
        'error_message': error_message or 'Unknown error',
        'frames_count': len(frames)
    }

def parse_go_trace(text: str) -> Dict:
    """Parse Go panic trace."""
    lines = text.split('\n')
    frames = []
    error_type = 'panic'
    error_message = None

    for line in lines:
        line = line.strip()
        if line.startswith('panic:'):
            error_message = line[6:].strip()
        match = re.match(r'^(\S+\.go):(\d+)', line)
        if match:
            file_path = match.group(1)
            line_num = match.group(2)
            frames.append({
                'file': file_path,
                'line': int(line_num)
            })

    return {
        'language': 'go',
        'frames': frames,
        'error_type': error_type,
        'error_message': error_message or text.strip().split('\n')[-1],
        'frames_count': len(frames)
    }

def parse_generic(text: str, language: str) -> Dict:
    """Generic error parser."""
    lines = [l for l in text.split('\n') if l.strip()]

    return {
        'language': language,
        'frames': [],
        'error_type': 'Error',
        'error_message': text.strip().split('\n')[-1] if lines else 'Unknown error',
        'frames_count': 0
    }

def parse_error(text: str) -> Dict:
    """Parse error trace into structured format."""
    language = detect_language(text)

    if language == 'python':
        return parse_python_traceback(text)
    elif language == 'javascript':
        return parse_javascript_trace(text)
    elif language == 'go':
        return parse_go_trace(text)
    else:
        return parse_generic(text, language)

# === ANALYSIS ===

def get_error_category(error_type: str, error_message: str) -> str:
    """Categorize error type."""
    error_lower = (error_type + error_message).lower()

    categories = {
        'import': ['importerror', 'modulenotfounderror', 'no module'],
        'type': ['typeerror', 'type mismatch', 'not a function'],
        'syntax': ['syntaxerror', 'parse error', 'unexpected token'],
        'reference': ['referenceerror', "not defined", 'undefined'],
        'network': ['connection refused', 'timeout', 'network', 'econnrefused'],
        'permission': ['permission denied', 'access denied', 'forbidden'],
        'memory': ['memoryerror', 'out of memory', 'oom'],
        'value': ['valueerror', 'invalid value', 'key error', 'indexerror'],
    }

    for category, patterns in categories.items():
        if any(p in error_lower for p in patterns):
            return category

    return 'general'

def find_fix_template(error_type: str, error_message: str) -> Optional[str]:
    """Find common fix template for known errors."""
    error_combined = f"{error_type} {error_message}".lower()

    for error_name, fix in COMMON_FIXES.items():
        if error_name.lower() in error_combined:
            return fix

    return None

def analyze_frame(frame: Dict, context_lines: List[str] = None) -> Dict:
    """Analyze a single stack frame."""
    analysis = {
        'file': frame.get('file', 'unknown'),
        'line': frame.get('line', 0),
        'likely_cause': None,
        'suggestion': None
    }

    file_path = frame.get('file', '')

    # Detect common issues by file pattern
    if 'venv' in file_path or '.venv' in file_path or 'site-packages' in file_path:
        analysis['likely_cause'] = 'virtual environment issue'
        analysis['suggestion'] = 'Check virtual environment is activated and package installed in correct env'

    elif '/node_modules/' in file_path:
        analysis['likely_cause'] = 'npm package issue'
        analysis['suggestion'] = 'Check package installed: npm list <package-name>'

    elif any(x in file_path for x in ['__pycache__', '.pyc']):
        analysis['likely_cause'] = 'Python cache conflict'
        analysis['suggestion'] = 'Clear cache: find . -type d -name __pycache__ -exec rm -rf {} +'

    return analysis

# === FORMATTING ===

def format_markdown(analysis: Dict, context: str = None) -> str:
    """Format analysis as Markdown."""
    lines = [
        "# 🔍 DebugPilot Analysis",
        "",
        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Language:** {analysis['parsed']['language'].upper()}",
        "",
        "---",
        "",
        f"## ❌ {analysis['parsed']['error_type']}",
        f"**Message:** {analysis['parsed']['error_message']}",
        "",
    ]

    if analysis['parsed']['frames']:
        lines.append("## 📍 Stack Trace")
        lines.append("")
        for i, frame in enumerate(analysis['parsed']['frames'][:5], 1):
            file_path = frame.get('file', 'unknown')
            line_num = frame.get('line', 0)
            func_name = frame.get('function', '')
            func_part = f" in {func_name}" if func_name else ""
            lines.append(f"{i}. `{file_path}:{line_num}`{func_part}")

        lines.append("")

    lines.append("## 💡 Root Cause")
    lines.append("")
    lines.append(f"**Category:** {analysis['category']}")
    lines.append("")
    lines.append(analysis['root_cause'])

    lines.append("")
    lines.append("## 🔧 Fix")

    if analysis['fix_template']:
        lines.append("```")
        lines.append(analysis['fix_template'])
        lines.append("```")

    lines.append("")
    lines.append(analysis['fix_suggestion'])

    if context:
        lines.append("")
        lines.append("## 📄 Context")
        lines.append("```")
        lines.append(context[:500] if len(context) > 500 else context)
        lines.append("```")

    lines.append("")
    lines.append(f"_DebugPilot v1.0 — {analysis['parsed']['language'].upper()}_")

    return '\n'.join(lines)

def format_telegram(analysis: Dict, context: str = None) -> str:
    """Format analysis for Telegram."""
    lines = [
        "🔍 *DebugPilot Analysis*",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"*Error:* `{analysis['parsed']['error_type']}`",
        f"*Message:* {analysis['parsed']['error_message'][:100]}...",
        "",
        f"*Language:* `{analysis['parsed']['language'].upper()}`",
        f"*Category:* {analysis['category']}",
        "",
    ]

    if analysis['parsed']['frames']:
        lines.append("*Stack Trace:*")
        for frame in analysis['parsed']['frames'][:3]:
            file_path = frame.get('file', 'unknown')
            line_num = frame.get('line', 0)
            lines.append("  > {}:{}".format(file_path, line_num))
        lines.append("")

    lines.append("*💡 Root Cause:*")
    lines.append(analysis['root_cause'][:200] + "..." if len(analysis['root_cause']) > 200 else analysis['root_cause'])
    lines.append("")
    lines.append("*🔧 Fix:*")
    if analysis['fix_template']:
        lines.append("```")
        fix_clean = analysis['fix_template'][:150].strip()
        lines.append(fix_clean + "..." if len(analysis['fix_template']) > 150 else fix_clean)
        lines.append("```")

    lines.append(analysis['fix_suggestion'][:200] + "..." if len(analysis['fix_suggestion']) > 200 else analysis['fix_suggestion'])

    return '\n'.join(lines)

# === MAIN ANALYSIS ===

def analyze_error(error_text: str, context: str = None, language: str = None) -> Dict:
    """Main analysis function."""
    if not error_text or not error_text.strip():
        return {'error': 'No error text provided'}

    # Detect language if not specified
    if not language:
        language = detect_language(error_text)

    # Parse error trace
    parsed = parse_error(error_text)

    # Override language if specified
    if language:
        parsed['language'] = language

    # Get error category
    category = get_error_category(parsed['error_type'], parsed['error_message'])

    # Find fix template
    fix_template = find_fix_template(parsed['error_type'], parsed['error_message'])

    # Analyze frames
    frame_analysis = []
    for frame in parsed['frames'][:5]:
        frame_analysis.append(analyze_frame(frame))

    # Generate root cause
    root_cause = generate_root_cause(parsed, category, frame_analysis)

    # Generate fix suggestion
    fix_suggestion = generate_fix_suggestion(parsed, category, fix_template, frame_analysis)

    return {
        'parsed': parsed,
        'category': category,
        'root_cause': root_cause,
        'fix_template': fix_template or '',
        'fix_suggestion': fix_suggestion,
        'frame_analysis': frame_analysis
    }

def generate_root_cause(parsed: Dict, category: str, frames: List[Dict]) -> str:
    """Generate root cause explanation."""
    error_type = parsed['error_type']
    error_message = parsed['error_message']
    language = parsed['language']

    causes = {
        'import': f"{error_type} occurs when Python cannot find or load the required module. This usually means the package is not installed in the current environment, or there's a path configuration issue.",
        'type': f"{error_type} occurs when an operation receives a value of unexpected type. Common causes: passing wrong type to function, using None where expected type, or mixing incompatible types.",
        'syntax': f"{error_type} occurs when the code structure is invalid. The parser cannot understand the syntax. Common causes: missing punctuation, incorrect indentation, or typos in keywords.",
        'reference': f"{error_type} occurs when code references a variable that doesn't exist in current scope. Common causes: typo in name, using before declaration, or scope issues.",
        'network': f"Connection error indicates the application cannot reach the target server. Possible causes: server down, wrong host/port, firewall blocking, or network connectivity issues.",
        'permission': f"Permission error indicates the process cannot access the requested resource. Possible causes: file permissions, user privileges, or security policies.",
        'memory': f"Memory error indicates system resource exhaustion. Possible causes: memory leak, processing too much data, or insufficient system resources.",
        'value': f"Value error occurs when data doesn't match expected format or range. Common causes: invalid input, boundary violations, or data transformation issues.",
    }

    base_cause = causes.get(category, f"{error_type} indicates an unexpected error condition. Review the traceback to identify the source.")

    # Add file-specific context
    if frames:
        first_frame = frames[0]
        base_cause += f"\n\n*Most likely source:* `{first_frame['file']}:{first_frame['line']}`"

    return base_cause

def generate_fix_suggestion(parsed: Dict, category: str, fix_template: str, frames: List[Dict]) -> str:
    """Generate fix suggestion."""
    suggestions = {
        'import': "1. Check package installed: `pip list` or `npm list`\n2. Install missing: `pip install <name>` or `npm install <name>`\n3. Verify correct environment activated",
        'type': "1. Check variable types with `type()` or `typeof()`\n2. Add type validation before operation\n3. Ensure all variables initialized before use",
        'syntax': "1. Review the line mentioned in traceback\n2. Check for matching brackets, quotes, parentheses\n3. Verify indentation is consistent\n4. Run linter: `python -m py_compile` or `eslint`",
        'reference': "1. Verify variable name spelling matches declaration\n2. Check variable is declared before use\n3. Ensure correct scope (global vs local)\n4. For JS: use `typeof` to check existence",
        'network': "1. Check server is running: `ps aux | grep <server>`\n2. Verify host/port configuration\n3. Test connectivity: `curl localhost:<port>`\n4. Check firewall rules",
        'permission': "1. Check file permissions: `ls -la <path>`\n2. Fix permissions: `chmod 644 <file>` or `chmod 755 <dir>`\n3. Check ownership: `chown user:group <path>`\n4. Verify user has required privileges",
        'memory': "1. Check memory usage: `top` or `htop`\n2. Look for memory leaks in code\n3. Process data in smaller batches\n4. Consider increasing system memory",
        'value': "1. Validate input data before processing\n2. Add bounds checking\n3. Use try/except for data transformation\n4. Log input values for debugging",
    }

    suggestion = suggestions.get(category, "Review the error traceback and fix the indicated issue.")

    return suggestion

# === OUTPUT ===

def send_telegram(message: str) -> bool:
    """Send message to Telegram."""
    try:
        import requests
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

        if not bot_token or not chat_id:
            print("WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='DebugPilot - AI-powered error analysis')
    parser.add_argument('--error', '-e', help='Error trace to analyze')
    parser.add_argument('--file', '-f', help='Read error from file')
    parser.add_argument('--context', '-c', help='Additional context code')
    parser.add_argument('--lang', '-l', choices=['python', 'javascript', 'go', 'rust', 'php', 'ruby'],
                       help='Force language detection')
    parser.add_argument('--output', '-o', default='stdout',
                       choices=['stdout', 'telegram', 'json', 'markdown'])
    parser.add_argument('--include-stack', action='store_true', help='Include full stack trace')

    args = parser.parse_args()

    # Get error text
    error_text = args.error
    if args.file:
        try:
            with open(args.file, 'r') as f:
                error_text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)

    if not error_text:
        print("No error text provided. Use --error or --file")
        print("Example: debug_pilot.py --error 'ImportError: No module named requests'")
        sys.exit(1)

    # Analyze
    print("Analyzing error...", file=sys.stderr)
    result = analyze_error(error_text, args.context, args.lang)

    if 'error' in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    # Format output
    if args.output == 'json':
        print(json.dumps(result, indent=2))
    elif args.output == 'telegram':
        output = format_telegram(result, args.context)
        success = send_telegram(output)
        if success:
            print("Analysis sent to Telegram")
        else:
            print(output)
    elif args.output == 'markdown':
        print(format_markdown(result, args.context))
    else:
        print(format_markdown(result, args.context))

if __name__ == '__main__':
    main()