#!/usr/bin/env python3
"""Comprehensively replace 'except Exception' with specific exception types."""
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple


PROJECT_DIR = Path("/Users/figuramax/LocalProjects/TURBO-CDI")
SRC_DIR = PROJECT_DIR / "src"

LINE_PATTERNS = [
    (r"\brequests\.(get|post|put|delete|patch|head|options)", "requests.RequestException"),
    (r"\bhttpx\.(get|post|put|delete|patch|head|options|AsyncClient|Client)", "httpx.HTTPError"),
    (r"\bclient\.(get|post|put|delete|patch|head|options)", "httpx.HTTPError"),
    (r"\bself\._client\.(get|post|put|delete|patch|head|options)", "httpx.HTTPError"),
    (r"\bself\.client\.(get|post|put|delete|patch|head|options)", "httpx.HTTPError"),
    (r"\baiohttp\.", "Exception"),
    (r"\burllib\.", "Exception"),
    (r"\bjson\.loads?\b", "json.JSONDecodeError"),
    (r"\bjson\.load\b", "json.JSONDecodeError"),
    (r"\.json\(\)", "json.JSONDecodeError"),
    (r"\bujson\.loads?\b", "ValueError"),
    (r"\byaml\.(safe_load|load)\b", "yaml.YAMLError"),
    (r"^\s*import\s+\w+", "ImportError"),
    (r"^\s*from\s+\w+\s+import\b", "ImportError"),
    (r"^\s*from\s+\w+\.\w+\s+import\b", "ImportError"),
    (r"__import__\(", "ImportError"),
    (r"\bsubprocess\.(run|Popen|call|check_output|check_call)\b", "subprocess.SubprocessError"),
    (r"\bsubprocess\.TimeoutExpired\b", "subprocess.TimeoutExpired"),
    (r"\bopen\(", "OSError"),
    (r"\bshutil\.", "OSError"),
    (r"\bos\.mkdir\b", "OSError"),
    (r"\bos\.makedirs\b", "OSError"),
    (r"\bos\.remove\b", "OSError"),
    (r"\bos\.rename\b", "OSError"),
    (r"\bpathlib\.", "OSError"),
    (r"\.write_text\(", "OSError"),
    (r"\.read_text\(", "OSError"),
    (r"\.write_bytes\(", "OSError"),
    (r"\.read_bytes\(", "OSError"),
    (r"\[['\"]\w+['\"]\]", "KeyError"),
    (r"\[\w+\]", "(KeyError, IndexError)"),
    (r"\.pop\(", "KeyError"),
    (r"\bint\(", "ValueError"),
    (r"\bfloat\(", "ValueError"),
    (r"\bbool\(", "ValueError"),
    (r"\bstr\(", "ValueError"),
    (r"\bdict\(", "ValueError"),
    (r"\blist\(", "ValueError"),
    (r"datetime\.strptime", "ValueError"),
    (r"datetime\.fromisoformat", "ValueError"),
    (r"\.split\(", "AttributeError"),
    (r"\.strip\(", "AttributeError"),
    (r"\bawait\s+", "(TypeError, asyncio.TimeoutError)"),
    (r"\basyncio\.(sleep|wait_for|timeout|gather)\b", "asyncio.TimeoutError"),
    (r"\bsocket\.", "OSError"),
    (r"\bsocket\.timeout\b", "socket.timeout"),
    (r"\bsqlalchemy\.", "sqlalchemy.exc.SQLAlchemyError"),
    (r"\bsession\.(query|add|commit|rollback|execute|close)\b", "sqlalchemy.exc.SQLAlchemyError"),
    (r"\bconn\.(execute|commit|rollback|close)\b", "sqlalchemy.exc.SQLAlchemyError"),
    (r"\bconnection\.(execute|commit|rollback|close)\b", "sqlalchemy.exc.SQLAlchemyError"),
    (r"\bcursor\.(execute|fetchall|fetchone)\b", "Exception"),
    (r"\bpool\.(acquire|release)\b", "Exception"),
    (r"hasattr\(", "AttributeError"),
    (r"getattr\(", "AttributeError"),
    (r"setattr\(", "AttributeError"),
    (r"\.is_available\(\)", "AttributeError"),
    (r"\.isinstance\(", "TypeError"),
    (r"\bmath\.", "ValueError"),
    (r"\bnumpy\.", "Exception"),
    (r"\bnp\.", "Exception"),
    (r"\bBaseModel\b", "ValueError"),
    (r"\bValidationError\b", "ValueError"),
    (r"\.model_validate\(", "ValueError"),
    (r"\.parse_obj\(", "ValueError"),
    (r"\blogger\.", "Exception"),
    (r"\bfunc\(", "Exception"),
    (r"\bfunc\b", "Exception"),
    (r"\bself\._\w+\(", "Exception"),
    (r"\bself\.\w+\(", "Exception"),
    (r"\b\w+\(\w+\)", "Exception"),
]

DIR_DEFAULTS = {
    "knowledge": "(httpx.HTTPError, requests.RequestException, json.JSONDecodeError, KeyError, ValueError)",
    "adapters": "(requests.RequestException, json.JSONDecodeError, KeyError, ValueError)",
    "simulations": "(ImportError, AttributeError, RuntimeError, OSError, TypeError)",
    "api": "(ValueError, KeyError, TypeError, httpx.HTTPError)",
    "verification": "(subprocess.SubprocessError, FileNotFoundError, OSError, ValueError)",
    "tui": "(ImportError, AttributeError, OSError, ValueError)",
    "data": "(sqlalchemy.exc.SQLAlchemyError, OSError, ValueError)",
    "integrations": "(requests.RequestException, json.JSONDecodeError, OSError, ValueError)",
    "agents": "(ValueError, KeyError, TypeError, ImportError)",
    "plugins": "(ImportError, AttributeError, ValueError, KeyError)",
    "infrastructure": "(OSError, ValueError, KeyError)",
    "compute": "(OSError, ImportError, ValueError)",
    "cli": "(ValueError, KeyError, OSError)",
    "observability": "(ValueError, KeyError, Exception)",
    "news": "(requests.RequestException, json.JSONDecodeError, KeyError, ValueError)",
    "solver": "(ValueError, TypeError, KeyError, RuntimeError)",
    "skills": "(ValueError, TypeError, KeyError, ImportError)",
    "mcp_server": "(ValueError, TypeError, KeyError, Exception)",
    "c4": "(ValueError, TypeError, KeyError, Exception)",
    "graph": "(ValueError, KeyError, TypeError, Exception)",
    "discovery": "(ValueError, KeyError, TypeError, Exception)",
    "novelty": "(ValueError, KeyError, TypeError, Exception)",
    "validation": "(ValueError, KeyError, TypeError, Exception)",
    "architecture": "(ValueError, KeyError, TypeError, Exception)",
    "utils": "(ValueError, TypeError, KeyError, Exception)",
    "llm": "(ImportError, ValueError, KeyError, TypeError)",
    "analogy": "(ValueError, KeyError, TypeError, Exception)",
    "metamodels": "(ValueError, KeyError, TypeError, Exception)",
    "extractors": "(ValueError, KeyError, TypeError, Exception)",
    "litintel": "(ValueError, KeyError, TypeError, Exception)",
    "r1": "(ValueError, KeyError, TypeError, Exception)",
    "system_dynamics": "(ValueError, KeyError, TypeError, Exception)",
    "publishing": "(ValueError, KeyError, TypeError, Exception)",
    "voice": "(ValueError, KeyError, TypeError, Exception)",
    "patents": "(ValueError, KeyError, TypeError, Exception)",
    "bots": "(ValueError, KeyError, TypeError, Exception)",
    "collaboration": "(ValueError, KeyError, TypeError, Exception)",
    "core": "(ValueError, KeyError, TypeError, Exception)",
    "dashboard": "(ValueError, KeyError, TypeError, Exception)",
    "memory": "(ValueError, KeyError, TypeError, Exception)",
}

def get_dir_default(filepath: Path) -> str:
    rel = filepath.relative_to(SRC_DIR)
    parts = rel.parts
    if len(parts) > 0:
        first_dir = parts[0]
        return DIR_DEFAULTS.get(first_dir, "Exception")
    return "Exception"

def infer_from_body(body_lines: List[str]) -> Optional[str]:
    body = '\n'.join(body_lines)
    candidates = set()
    
    for pattern, exc_type in LINE_PATTERNS:
        if re.search(pattern, body, re.MULTILINE):
            if exc_type != "Exception":
                candidates.add(exc_type)
    
    if not candidates:
        return None
    
    flat = set()
    for c in candidates:
        if c.startswith("(") and c.endswith(")"):
            for part in c[1:-1].split(", "):
                flat.add(part)
        else:
            flat.add(c)
    
    sorted_candidates = sorted(flat)
    
    if len(sorted_candidates) == 1:
        return sorted_candidates[0]
    return "(" + ", ".join(sorted_candidates) + ")"

def find_prev_exceptions(lines: List[str], except_idx: int, except_indent: int) -> set:
    """Find exceptions already caught in earlier except blocks at same indent level."""
    prev_exceptions = set()
    for j in range(except_idx - 1, -1, -1):
        line = lines[j]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        if indent < except_indent and (stripped.startswith('try:') or stripped.startswith('def ') or stripped.startswith('async def ') or stripped.startswith('class ')):
            break
        
        if indent == except_indent and stripped.startswith('except '):
            match = re.match(r'\s*except\s+([^(]+?)(?:\s+as\s+\w+)?\s*:', line)
            if match:
                exc_str = match.group(1).strip()
                if exc_str.startswith('(') and exc_str.endswith(')'):
                    exc_str = exc_str[1:-1]
                for e in exc_str.split(','):
                    prev_exceptions.add(e.strip())
        elif indent == except_indent and not stripped.startswith('except '):
            break
    
    return prev_exceptions

def find_blocks(filepath: Path) -> List[Tuple[int, str, List[str]]]:
    content = filepath.read_text()
    lines = content.split('\n')
    blocks = []
    
    for i, line in enumerate(lines):
        if 'except Exception' not in line:
            continue
        
        indent = len(line) - len(line.lstrip())
        try_indent = indent
        
        try_line = -1
        for j in range(i - 1, -1, -1):
            l = lines[j]
            if l.strip() == 'try:' and len(l) - len(l.lstrip()) == try_indent:
                try_line = j
                break
        
        if try_line == -1:
            continue
        
        body_lines = []
        for j in range(try_line + 1, i):
            l = lines[j]
            if l.strip() and not l.strip().startswith('#'):
                l_indent = len(l) - len(l.lstrip())
                if l_indent > try_indent:
                    body_lines.append(l)
                elif l_indent == try_indent:
                    break
        
        blocks.append((i, line, body_lines))
    
    return blocks

def fix_file(filepath: Path) -> Tuple[int, int, int]:
    content = filepath.read_text()
    lines = content.split('\n')
    blocks = find_blocks(filepath)
    
    inferred_fixed = 0
    default_fixed = 0
    skipped = 0
    
    for line_idx, original_line, body_lines in blocks:
        inferred = infer_from_body(body_lines)
        
        if inferred:
            new_exc = inferred
        else:
            new_exc = get_dir_default(filepath)
        
        # Remove exceptions already caught in previous blocks
        indent = len(original_line) - len(original_line.lstrip())
        prev_exceptions = find_prev_exceptions(lines, line_idx, indent)
        
        if new_exc != "Exception" and prev_exceptions:
            if new_exc.startswith('(') and new_exc.endswith(')'):
                current = [e.strip() for e in new_exc[1:-1].split(',')]
            else:
                current = [new_exc]
            
            filtered = [e for e in current if e not in prev_exceptions]
            
            if len(filtered) == 0:
                new_exc = "Exception"
            elif len(filtered) == 1:
                new_exc = filtered[0]
            else:
                new_exc = "(" + ", ".join(filtered) + ")"
        
        if new_exc == "Exception":
            if 'except Exception:' in original_line and 'as e' not in original_line:
                lines[line_idx] = original_line.replace('except Exception:', 'except Exception as e:')
                default_fixed += 1
            else:
                skipped += 1
            continue
        
        # Make replacement
        if 'except Exception as e:' in original_line:
            lines[line_idx] = original_line.replace('except Exception as e:', f'except {new_exc} as e:')
        elif 'except Exception:' in original_line:
            lines[line_idx] = original_line.replace('except Exception:', f'except {new_exc} as e:')
        else:
            match = re.match(r'(\s*)except Exception(\s+as\s+\w+)\s*:', original_line)
            if match:
                indent_str, alias = match.groups()
                lines[line_idx] = f"{indent_str}except {new_exc}{alias}:"
            else:
                skipped += 1
                continue
        
        if inferred:
            inferred_fixed += 1
        else:
            default_fixed += 1
    
    if inferred_fixed + default_fixed > 0:
        filepath.write_text('\n'.join(lines))
    
    return inferred_fixed, default_fixed, skipped

def main():
    total_inferred = 0
    total_default = 0
    total_skipped = 0
    modified_files = []
    
    for filepath in sorted(SRC_DIR.rglob("*.py")):
        rel_path = filepath.relative_to(PROJECT_DIR)
        path_str = str(rel_path)
        
        if '/test' in path_str or '__pycache__' in path_str or path_str.startswith('tests/'):
            continue
        
        content = filepath.read_text()
        if 'except Exception' not in content:
            continue
        
        inferred, default, skipped = fix_file(filepath)
        
        if inferred + default > 0:
            print(f"Fixed {inferred+default} ({inferred} inferred, {default} default) in {rel_path} (skipped {skipped})")
            total_inferred += inferred
            total_default += default
            total_skipped += skipped
            modified_files.append(filepath)
        elif skipped > 0:
            total_skipped += skipped
    
    print(f"\nTotal: {total_inferred} inferred, {total_default} default, {total_skipped} skipped")
    print(f"Files modified: {len(modified_files)}")
    
    print("\nVerifying syntax...")
    errors = []
    for filepath in modified_files:
        rel = filepath.relative_to(PROJECT_DIR)
        result = os.system(f"cd {PROJECT_DIR} && python3 -m py_compile {rel} > /dev/null 2>&1")
        if result != 0:
            errors.append(str(rel))
    
    if errors:
        print(f"Syntax errors in: {', '.join(errors)}")
    else:
        print("All modified files compile successfully.")

if __name__ == "__main__":
    main()
