#!/bin/bash
# Test Discovery Module

set -e

echo "🚀 Testing TURBO-CDI v8.3 Discovery (Day 1)"
echo "============================================"

# Activate venv
source .venv/bin/activate

cd v8

# Test 1: Imports
echo "1. Testing discovery imports..."
python3 -c "
import sys
sys.path.insert(0, '.')
from discovery import DiscoveryLab, SourceDiscoveryService, DiscoveryResult
from discovery.operators import apply_transformation, find_shortest_path
from discovery.llm_adapter import llm_call
print('   ✅ All imports successful')
"

# Test 2: C4 Operators & Theorem 11
echo "2. Testing C4 operators..."
python3 -c "
import sys
sys.path.insert(0, '.')
from discovery.operators import C4State, U_T_plus, U_D_plus, find_shortest_path

# Test Theorem 11 (path length in operators <= 6)
start = C4State(t=0, d=0, a=0)
end = C4State(t=2, d=2, a=2)
path = find_shortest_path(start, end)

# cost = number of operators, must be <= 6 per Theorem 11
assert path.cost <= 6, f'Theorem 11 violated: {path.cost} steps'
print(f'   ✅ Path found: {path.cost} operators, {len(path.path)} states (Theorem 11 satisfied)')
"

# Test 3: DiscoveryLab initialization
echo "3. Testing DiscoveryLab..."
python3 -c "
import sys
sys.path.insert(0, '.')
from discovery import DiscoveryLab

lab = DiscoveryLab()
print(f'   ✅ DiscoveryLab initialized')
print(f'      Database: ~/.turbo-cdi/discovery.db')
"

echo ""
echo "============================================"
echo "🎉 DAY 1 COMPLETE! Discovery module ready!"
echo ""
echo "Next: Day 2 - RAG Core + Document Ingestion"
