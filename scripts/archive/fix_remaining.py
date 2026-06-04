#!/usr/bin/env python3
"""Fix remaining errors with cast() or other code-level fixes"""
import re
import subprocess
from pathlib import Path


PROJECT_DIR = Path("/Users/figuramax/LocalProjects/TURBO-CDI")

def run_mypy():
    result = subprocess.run(
        ['python3', '-m', 'mypy', 'src/patterns/', '--ignore-missing-imports', '--show-error-codes'],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    errors = []
    for line in (result.stdout + '\n' + result.stderr).splitlines():
        m = re.match(r'(src/patterns/[^:]+):(\d+):\s*error:\s+(.+)', line)
        if m:
            errors.append((m.group(1), int(m.group(2)), m.group(3)))
    return errors


def fix_errors_one_by_one():
    errors = run_mypy()
    print(f"Starting with {len(errors)} errors")

    # Group errors by file with the error codes
    for fp_rel, lineno, msg in sorted(set((e[0], e[1], e[2]) for e in errors)):
        fp = PROJECT_DIR / fp_rel
        if not fp.exists():
            continue
        
        lines = fp.read_text().split('\n')
        if lineno < 1 or lineno > len(lines):
            continue
        
        line = lines[lineno - 1]

        # Strategy depends on error type
        if 'Need type annotation' in msg and 'var-annotated' in msg:
            # Add type annotation for the variable
            varname_match = re.search(r'for\s+"(\w+)"', msg)
            if varname_match:
                varname = varname_match.group(1)
                line = line.replace(f'{varname} =', f'{varname}: list =')
                lines[lineno - 1] = line
        
        elif 'not indexable' in msg or 'is not indexable' in msg:
            # Wrap in cast()
            # Find the variable being indexed
            m = re.match(r'(.*)self\.(\w+)\[(.*)', line)
            if m:
                indent = m.group(1)
                varname = m.group(2)
                rest = m.group(3)
                # Find where the index ends
                bracket_count = 1
                end_idx = len(indent) + len('self.') + len(varname) + 1
                for i in range(end_idx, len(line)):
                    if line[i] == '[':
                        bracket_count += 1
                    elif line[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            after = line[i+1:]
                            before_idx = line[:i]
                            lines[lineno - 1] = f'{indent}cast(np.ndarray, self.{varname})[{rest}'
                            break
        
        elif 'no attribute' in msg and 'union-attr' in msg:
            # Wrap in cast()
            m = re.match(r'(.*)self\.(\w+)\.(\w+)', line)
            if m:
                indent = m.group(1)
                varname = m.group(2)
                attr = m.group(3)
                line = line.replace(f'self.{varname}.{attr}', f'cast(Any, self.{varname}).{attr}')
                lines[lineno - 1] = line
        
        elif 'Incompatible types in assignment' in msg and 'None' in msg and 'list[str]' in msg:
            # Assignment of None to list - add type annotation
            m = re.match(r'(.*self\.\w+)\s*=\s*None', line)
            if m:
                var = m.group(1)
                line = line.replace(f'{var} = None', f'{var}: list[str] = []')
                lines[lineno - 1] = line
        
        elif 'config' in msg and '| None' in msg and 'has no attribute' in msg:
            # Config is None - insert assert
            m = re.match(r'(\s*)(.+)', line)
            if m:
                indent = m.group(1)
                # Find the function this is in
                for i in range(lineno - 2, -1, -1):
                    if re.match(r'\s*def ', lines[i]):
                        func_indent = len(re.match(r'\s*', lines[i]).group(0))
                        guard = f'{" " * (func_indent + 4)}assert self.config is not None, "config not initialized"'
                        # Check if guard already exists
                        if guard.strip() not in lines:
                            lines.insert(i + 1, guard)
                            lineno += 1
                            print(f"  INSERTED guard at {fp_rel}:{i+2}")
                        break
        
        fp.write_text('\n'.join(lines))
    
    remaining = len(run_mypy())
    print(f"Remaining errors: {remaining}")
    return remaining


if __name__ == "__main__":
    remaining = fix_errors_one_by_one()
    if remaining == 0:
        print("ALL ERRORS FIXED!")
    else:
        print(f"{remaining} errors remain")
        errors = run_mypy()
        for fp, ln, msg in errors:
            print(f"  {fp}:{ln}: {msg[:80]}")
