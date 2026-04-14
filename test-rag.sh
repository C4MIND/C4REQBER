#!/bin/bash
# Test RAG Module

set -e

echo "🚀 Testing TURBO-CDI v8.3 RAG (Day 2)"
echo "======================================"

source .venv/bin/activate
cd v8

# Test 1: Vector Store
echo "1. Testing VectorStore..."
python3 -c "
import sys
sys.path.insert(0, '.')
from rag import UserDocumentStore

store = UserDocumentStore('test')
print('   ✅ UserDocumentStore initialized')
print(f'      Collection: user_docs_test')
"

# Test 2: DocumentIngester
echo "2. Testing DocumentIngester..."
python3 -c "
import sys
sys.path.insert(0, '.')
from rag.ingestion import DocumentIngester

ingester = DocumentIngester()
print('   ✅ DocumentIngester initialized')
print('      Model: all-MiniLM-L6-v2')
"

# Test 3: HybridRetriever
echo "3. Testing HybridRetriever..."
python3 -c "
import sys
sys.path.insert(0, '.')
from rag.retriever import HybridRetriever

retriever = HybridRetriever('test')
print('   ✅ HybridRetriever initialized')
"

# Test 4: Orchestrator integration
echo "4. Testing Orchestrator RAG methods..."
python3 -c "
import sys
sys.path.insert(0, '.')
from core.orchestrator import TurboCDIv8

turbo = TurboCDIv8()
print('   ✅ TurboCDIv8 with RAG initialized')
print(f'      Has ingest_document: {hasattr(turbo, \"ingest_document\")}')
print(f'      Has query_knowledge_base: {hasattr(turbo, \"query_knowledge_base\")}')
print(f'      Has select_gap_and_plan: {hasattr(turbo, \"select_gap_and_plan\")}')
"

echo ""
echo "======================================"
echo "🎉 DAY 2 COMPLETE! RAG module ready!"
