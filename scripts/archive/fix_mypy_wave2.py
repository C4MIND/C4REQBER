#!/usr/bin/env python3
"""Second wave: fix union access, no-any-return, implicit optional, unreachable code"""
import os
import re
import sys
from pathlib import Path


PATTERNS_DIR = Path("/Users/figuramax/LocalProjects/TURBO-CDI/src/patterns")


def get_lines(content):
    """Split content into list of lines"""
    return content.split('\n')


def join_lines(lines):
    return '\n'.join(lines)


def fix_implicit_optional_dict(lines):
    """hypothesis: dict[str, Any] = None -> hypothesis: dict[str, Any] | None = None"""
    changed = False
    for i, line in enumerate(lines):
        if re.search(r'def \w+\(.*\)', line):
            continue  # skip function defs, we handle parameters separately
        # hypothesis: dict[str, Any] = None (not already | None)
        new_line = re.sub(
            r'(hypothesis|config)\s*:\s*dict\[str,\s*Any\]\s*=\s*None\b(?!\s*\|\s*None)',
            r'\1: dict[str, Any] | None = None',
            line
        )
        if new_line != line:
            lines[i] = new_line
            changed = True
    return changed


def fix_no_any_return_ndarray(lines):
    """Functions declared to return ndarray[Any, Any] that return Any"""
    changed = False
    for i, line in enumerate(lines):
        if 'return np.' in line or 'return self.' in line:
            if 'def ' not in line and 'return' in line and 'np.' in line:
                # Check if we're inside a function that returns ndarray
                # Add cast
                match = re.match(r'(\s+)return (.+)', line)
                if match:
                    indent = match.group(1)
                    expr = match.group(2).rstrip()
                    lines[i] = f'{indent}return cast(NDArray, {expr})'
                    changed = True
    return changed


def fix_no_any_return_float(lines):
    """Functions declared to return float that return numpy scalar"""
    changed = False
    for i, line in enumerate(lines):
        if 'return np.' in line or 'return float(' in line:
            match = re.match(r'(\s+)return (.+)', line)
            if match:
                indent = match.group(1)
                expr = match.group(2).rstrip()
                if 'np.' in expr and not expr.startswith('float('):
                    lines[i] = f'{indent}return float({expr})'
                    changed = True
    return changed


def fix_unreachable_code(lines):
    """Remove unreachable statements (after return/raise/break/continue)"""
    changed = False
    new_lines = []
    skip_until_indent = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        indent = len(re.match(r'^\s*', line).group(0)) if line.strip() else -1

        if skip_until_indent is not None:
            if indent <= skip_until_indent and stripped:
                skip_until_indent = None
                new_lines.append(line)
            else:
                changed = True
                continue
        else:
            if any(stripped.startswith(kw) for kw in ['return ', 'return\n', 'break', 'continue', 'raise ']):
                # Check next lines - if same or lower indent (more nested), they're unreachable
                # If next line is at the SAME indent, it might just be a different path
                # We need to find the matching indent that's LESS than this line
                current_indent = indent
                # Look ahead for the matching outdent level
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped:
                        continue
                    next_indent = len(re.match(r'^\s*', next_line).group(0))
                    if next_indent <= current_indent and next_stripped:
                        break  # found a line at matching or lower indent
                    if 0 < next_indent <= current_indent:
                        break
                else:
                    new_lines.append(line)
                    continue
                new_lines.append(line)
            else:
                new_lines.append(line)

    return join_lines(new_lines) != join_lines(lines), new_lines


def fix_unreachable_simple(lines):
    """Remove statements immediately after a return that are at the same indent"""
    changed = False
    i = 0
    result = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        result.append(line)

        if stripped in ('return', 'break', 'continue', 'raise') or \
           stripped.startswith('return ') or stripped.startswith('break ') or \
           stripped.startswith('continue ') or stripped.startswith('raise '):
            current_indent = len(re.match(r'^\s*', line).group(0))
            # Skip unreachable lines that follow at the same indent
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.strip()
                if not next_stripped:
                    j += 1
                    continue
                next_indent = len(re.match(r'^\s*', next_line).group(0))
                if next_indent < current_indent:
                    # dedented - new code block, stop skipping
                    break
                if next_indent == current_indent:
                    # Same indent - unreachable
                    changed = True
                    print(f"  SKIPPING unreachable line {j+1}: {next_stripped[:60]}")
                else:
                    # More indented (inside a sub-block) - unreachable too
                    pass
                j += 1
        i += 1

    return changed


def fix_ndarray_union_smart(lines):
    """
    For ndarray fields initialized in __init__ to None, then set to actual arrays,
    change the type to non-optional after init.
    
    Strategy: After the __init__ method ends (when we see a different method at class indent),
    keep the type annotations as ndarray (not Optional) since they're always set in __init__.
    
    But this is the reverse of what we need - the type annotations are already Optional
    and we need to handle runtime checks. The SIMPLEST fix is to change the __init__
    to NOT use None as initial value, but instead initialize arrays directly in one step.
    
    That's too complex. Instead, for patterns where arrays are initialized in __init__,
    we'll change the field annotations to use `ndarray` (not Optional) and use type:ignore for
    the None initialization, OR we add assertions after init.
    
    Actually - the simplest approach: keep the Optional annotation, but after the initialization
    block in __init__, add `assert self.field is not None` for each Optional field.
    Or add `TypedDict` class approach.
    
    Let me just skip this automated fix - it's too context-dependent.
    """
    return False


def main():
    py_files = sorted(PATTERNS_DIR.rglob("*.py"))
    changed_count = 0

    for fp in py_files:
        try:
            content = fp.read_text()
            original = content
            lines = content.split('\n')

            modified = fix_implicit_optional_dict(lines)

            if modified:
                fp.write_text('\n'.join(lines))
                print(f"  FIXED implicit optional: {fp.relative_to(PATTERNS_DIR)}")
                changed_count += 1

        except Exception as e:
            print(f"  ERROR: {fp.relative_to(PATTERNS_DIR)}: {e}")

    print(f"\nPhase 2 changed {changed_count} files")


if __name__ == "__main__":
    main()
