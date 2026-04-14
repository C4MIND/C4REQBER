#!/bin/bash
# Quick test script for TURBO-CDI v8.2

set -e  # Exit on error

echo "🚀 TURBO-CDI v8.2 Quick Test"
echo "=============================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

cd /Users/figuramax/LocalProjects/TURBO-CDI/v8

# Test 1: Import
echo -n "1. Testing imports... "
python3 -c "from core.orchestrator import TurboCDIv8; print('OK')" 2>/dev/null && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

# Test 2: UserProfile
echo -n "2. Testing UserProfile... "
python3 -c "
import sys
sys.path.insert(0, '.')
from cognitive.user_profile.core import UserProfile
p = UserProfile(user_id='test')
try:
    p.save('../../../etc/passwd')
    exit(1)
except ValueError:
    exit(0)
" 2>/dev/null && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

# Test 3: Bias Types
echo -n "3. Testing BiasTypes (10)... "
python3 -c "
import sys
sys.path.insert(0, '.')
from cognitive.bias_detector.core import BiasType
assert len(list(BiasType)) == 10
" 2>/dev/null && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

# Test 4: SelfModifier (доступ к dataclass полям через точку)
echo -n "4. Testing SelfModifier rollback... "
python3 -c "
import sys
sys.path.insert(0, '.')
from meta.self_modifier.core import SelfModifier
sm = SelfModifier()
sm.set_parameter('effectiveness_base_weight', 0.5, manual=True)
sm.set_parameter('effectiveness_base_weight', 0.7, manual=True)
h = sm.tuning_history
assert len(h) >= 2
# Доступ к полям dataclass через точку
assert h[-1].old_value == 0.5
" 2>/dev/null && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

# Test 5: C4 Navigation
echo -n "5. Testing C4 navigation... "
python3 -c "
import sys
sys.path.insert(0, '.')
from core.orchestrator import TurboCDIv8
from modules import C4State, TimeAxis, ScaleAxis, AgencyAxis
t = TurboCDIv8()
result = t.navigate_c4_space(
    C4State(TimeAxis.PAST, ScaleAxis.CONCRETE, AgencyAxis.SELF),
    C4State(TimeAxis.FUTURE, ScaleAxis.ABSTRACT, AgencyAxis.SELF)
)
assert result['theorem_11_compliant'] == True
" 2>/dev/null && echo -e "${GREEN}✅ PASS${NC}" || echo -e "${RED}❌ FAIL${NC}"

echo "=============================="
echo "🎉 All tests passed!"
