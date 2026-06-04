#!/usr/bin/env python3
"""Intelligently replace 'except Exception' with specific exception types."""
import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


PROJECT_DIR = Path("/Users/figuramax/LocalProjects/TURBO-CDI")
SRC_DIR = PROJECT_DIR / "src"

# Known patterns for specific exception types
PATTERNS = {
    "ImportError": [
        r"\bimport\s+\w+",
        r"\bfrom\s+\w+\s+import\b",
    ],
    "json.JSONDecodeError": [
        r"\.json\(\)",
        r"json\.loads?\b",
        r"json\.load\b",
    ],
    "KeyError": [
        r"\[['\"][\w\-]+['\"]\]",
        r"\.pop\(",
    ],
    "IndexError": [
        r"\[\d+\]",
        r"\[\w+\]",
    ],
    "ValueError": [
        r"\bint\(",
        r"\bfloat\(",
        r"\bbool\(",
        r"\.split\(",
        r"\.strip\(",
        r"datetime\.strptime",
        r"datetime\.fromisoformat",
    ],
    "TypeError": [
        r"\bawait\s+",
        r"\basyncio\.",
        r"\.is_available\(\)",
    ],
    "FileNotFoundError": [
        r"\bopen\(",
        r"shutil\.",
        r"pathlib\.",
        r"os\.path\.",
    ],
    "OSError": [
        r"os\.",
        r"subprocess\.",
    ],
    "subprocess.TimeoutExpired": [
        r"subprocess\.run\b",
        r"subprocess\.call\b",
    ],
    "httpx.HTTPError": [
        r"httpx\.",
        r"\bclient\.",
    ],
    "requests.RequestException": [
        r"requests\.",
    ],
    "asyncio.TimeoutError": [
        r"asyncio\.wait_for",
        r"asyncio\.timeout",
    ],
    "AttributeError": [
        r"hasattr\(",
        r"getattr\(",
        r"\.\w+\b",
    ],
}

def find_except_blocks(filepath: Path) -> List[Tuple[int, str, List[str]]]:
    """Find all 'except Exception' blocks and their try-body context."""
    content = filepath.read_text()
    lines = content.split('\n')
    blocks = []
    
    for i, line in enumerate(lines):
        if 'except Exception' in line:
            # Find the matching try block
            indent = len(line) - len(line.lstrip())
            try_indent = indent - 4
            
            # Go back to find try:
            try_line = -1
            for j in range(i - 1, -1, -1):
                l = lines[j]
                if l.strip() == 'try:' and len(l) - len(l.lstrip()) == try_indent:
                    try_line = j
                    break
            
            if try_line == -1:
                continue
            
            # Collect try body lines
            body_lines = []
            for j in range(try_line + 1, i):
                l = lines[j]
                if l.strip():
                    l_indent = len(l) - len(l.lstrip())
                    if l_indent > try_indent:
                        body_lines.append(l.strip())
                    elif l_indent == try_indent and not l.strip().startswith('#'):
                        break
            
            blocks.append((i, line, body_lines))
    
    return blocks

def infer_exceptions(body_lines: List[str]) -> Optional[str]:
    """Infer specific exception types from try body."""
    body = '\n'.join(body_lines)
    candidates = set()
    
    for exc_type, patterns in PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, body):
                candidates.add(exc_type)
    
    # Remove overly broad ones if more specific exist
    if "httpx.HTTPError" in candidates and "requests.RequestException" in candidates:
        # Check which library is actually imported
        if "httpx" in body and "requests" not in body:
            candidates.discard("requests.RequestException")
        elif "requests" in body and "httpx" not in body:
            candidates.discard("httpx.HTTPError")
    
    if not candidates:
        return None
    
    # Sort for consistency
    sorted_candidates = sorted(candidates)
    
    if len(sorted_candidates) == 1:
        return sorted_candidates[0]
    return "(" + ", ".join(sorted_candidates) + ")"

def fix_file(filepath: Path) -> Tuple[int, int]:
    """Fix a single file. Returns (fixed, skipped)."""
    content = filepath.read_text()
    lines = content.split('\n')
    blocks = find_except_blocks(filepath)
    
    fixed = 0
    skipped = 0
    
    for line_idx, original_line, body_lines in blocks:
        inferred = infer_exceptions(body_lines)
        
        if inferred:
            # Replace except Exception with specific exception
            if 'except Exception as e:' in original_line:
                new_line = original_line.replace('except Exception as e:', f'except {inferred} as e:')
            elif 'except Exception:' in original_line:
                new_line = original_line.replace('except Exception:', f'except {inferred} as e:')
            else:
                skipped += 1
                continue
            
            lines[line_idx] = new_line
            fixed += 1
        else:
            # Can't infer - ensure it at least has 'as e'
            if 'except Exception:' in original_line and 'as e' not in original_line:
                lines[line_idx] = original_line.replace('except Exception:', 'except Exception as e:')
                fixed += 1
            else:
                skipped += 1
    
    if fixed > 0:
        filepath.write_text('\n'.join(lines))
    
    return fixed, skipped

def main():
    total_fixed = 0
    total_skipped = 0
    modified_files = []
    
    # Find all Python files in src/ excluding tests
    for filepath in sorted(SRC_DIR.rglob("*.py")):
        rel_path = filepath.relative_to(PROJECT_DIR)
        path_str = str(rel_path)
        
        # Skip tests and pycache
        if '/test' in path_str or '__pycache__' in path_str or path_str.startswith('tests/'):
            continue
        
        # Check if file has any except Exception
        content = filepath.read_text()
        if 'except Exception' not in content:
            continue
        
        fixed, skipped = fix_file(filepath)
        
        if fixed > 0:
            print(f"Fixed {fixed} in {rel_path} (skipped {skipped})")
            total_fixed += fixed
            total_skipped += skipped
            modified_files.append(filepath)
        elif skipped > 0:
            total_skipped += skipped
    
    print(f"\nTotal: {total_fixed} fixed, {total_skipped} skipped")
    
    # Verify syntax
    print("\nVerifying syntax...")
    errors = []
    for filepath in modified_files:
        rel = filepath.relative_to(PROJECT_DIR)
        result = os.system(f"cd {PROJECT_DIR} && python3 -m py_compile {rel} 2>&1")
        if result != 0:
            errors.append(str(rel))
    
    if errors:
        print(f"Syntax errors in: {', '.join(errors)}")
    else:
        print("All modified files compile successfully.")

if __name__ == "__main__":
    main()
