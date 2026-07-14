"""
C4 Engine tests — conftest and helpers.
"""

import sys
from pathlib import Path


# Add src/ to path so tests can import c4
src_path = Path(__file__).resolve().parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
