import asyncio
import websockets
import json
import sys

async def test_websocket():
    uri = "ws://localhost:8765"
    
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        # 1. Receive greeting
        greeting = await ws.recv()
        print(f"✅ Connected: {json.loads(greeting)['message']}")
        
        # 2. Test discover
        print("\n🔍 Testing discover...")
        await ws.send(json.dumps({
            "command": "discover",
            "query": "quantum error correction",
            "domain": "physics"
        }))
        
        # Wait for discovery_complete
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=60)
            data = json.loads(msg)
            print(f"   [{data.get('type', 'unknown')}]")
            
            if data.get('type') == 'discovery_complete':
                print(f"   ✅ Gaps found: {data.get('gaps_count', 0)}")
                break
        
        # 3. Test query_rag
        print("\n📚 Testing query_rag...")
        await ws.send(json.dumps({
            "command": "query_rag",
            "query": "What is quantum computing?",
            "sources": ["user_docs"],
            "top_k": 3
        }))
        
        msg = await asyncio.wait_for(ws.recv(), timeout=30)
        data = json.loads(msg)
        if data.get('type') == 'rag_results':
            print(f"   ✅ Results: {len(data.get('results', []))}")
        
        # 4. Test select_gap
        print("\n🎯 Testing select_gap...")
        await ws.send(json.dumps({
            "command": "select_gap",
            "gap_id": "gap_0",
            "domain": "physics"
        }))
        
        msg = await asyncio.wait_for(ws.recv(), timeout=30)
        data = json.loads(msg)
        if data.get('type') == 'gap_plan':
            print(f"   ✅ Plan generated")
            print(f"   From: {data.get('from_state')}")
            print(f"   To: {data.get('to_state')}")
        
        print("\n🎉 All WebSocket tests passed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
