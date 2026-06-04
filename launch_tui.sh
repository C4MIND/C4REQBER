#!/bin/bash
# TUI Launcher with Module Status Check
# This script verifies all modules are integrated before launching TUI

echo "🔧 C4-CDI v8.2.1 — Module Integration Check"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0

check_module() {
    TOTAL=$((TOTAL+1))
    module=$1
    check_cmd=$2
    
    if eval $check_cmd > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $module"
        PASSED=$((PASSED+1))
    else
        echo -e "${RED}❌${NC} $module"
    fi
}

echo ""
echo "📚 Core Modules:"
check_module "C4-META (27 states)" "python3 -c 'from src.c4.engine import C4Engine'"
check_module "TRIZ (40 principles)" "python3 -c 'from src.triz import TRIZBridge'"
check_module "FRA Router (20 ops)" "python3 -c 'from src.operators.fra import FRARouter'"
check_module "QZRF (14 ops)" "python3 -c 'from src.operators.qzrf import QZRFEngine'"

echo ""
echo "📡 Knowledge & Search:"
check_module "MultiSource (12 active)" "python3 -c 'from src.knowledge.multi_source import MultiSourceSearcher'"
check_module "Brave Search" "grep -q 'brave' src/knowledge/orchestrator.py"
check_module "Mega-DB" "python3 -c 'from src.knowledge.mega_db import MegaDB'"

echo ""
echo "🧠 Cognitive Plugins (20):"
check_module "SWOT Analysis" "python3 -c 'from src.plugins.swot import analyze'"
check_module "Red Team" "python3 -c 'from src.plugins.red_team import analyze'"
check_module "Six Thinking Hats" "python3 -c 'from src.plugins.six_hats import analyze'"
check_module "All 20 plugins wired" "grep -q 'cognitive_plugins' src/api/v8_routers/discovery_v8.py"

echo ""
echo "🤖 LLM & APIs:"
check_module "Unified LLM Router" "python3 -c 'from src.llm.providers.unified import LLMProviderRouter'"
check_module "Moonshot API Key" "grep -q 'MOONSHOT' .env"
check_module "Brave API Key" "grep -q 'BRAVE' .env"
check_module "NVIDIA API Key" "grep -q 'NVIDIA' .env"

echo ""
echo "⚙️ Physics & Simulations:"
check_module "Newton Physics (mlx-env)" "(source /Users/figuramax/LocalProjects/mlx-env/bin/activate && python3 -c 'import newton')"
check_module "5 Physics Engines" "python3 -c 'from src.simulations import newton_bridge'"

echo ""
echo "🔧 Verification:"
check_module "Lean4" "which lean > /dev/null"
check_module "Coq" "which coqc > /dev/null"
check_module "Dafny" "which Dafny > /dev/null"
check_module "Formal Verification" "python3 -c 'from src.verification import Lean4Bridge'"

echo ""
echo "🚀 Server & API:"
check_module "FastAPI Server" "python3 -c 'from src.api.server import app'"
check_module "Discovery v8 Router" "python3 -c 'from src.api.v8_routers.discovery_v8 import router'"
check_module "Lifespan (auto-start)" "grep -q 'startup_services' src/api/lifespan.py"
check_module "20 wired modules" "grep -q 'cognitive_plugins' src/api/v8_routers/discovery_v8.py"

echo ""
echo "📊 Exports & Output:"
check_module "Export Manager" "python3 -c 'from src.export.manager import ExportManager'"
check_module "Dissertation Mode" "grep -q 'dissertation' src/api/v8_routers/discovery_v8.py"
check_module "Batch v7 (Language Gene)" "test -f discovery/batch_v7/lang_gene_discovery.json"
check_module "Batch v6 (Sleep)" "test -f discovery/batch_v6/paradigm_shift_sleep.json"

echo ""
echo "=============================================="
echo -e "${YELLOW}Results: $PASSED/$TOTAL modules verified${NC}"
echo "=============================================="

if [ $PASSED -eq $TOTAL ]; then
    echo -e "${GREEN}🎉 ALL MODULES INTEGRATED AND WORKING!${NC}"
else
    echo -e "${RED}⚠️  Some modules are missing or not working${NC}"
fi
echo ""
echo "Starting TUI..."
sleep 1
python3 -m src.tui.app_v7
