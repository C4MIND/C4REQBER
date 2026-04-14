#!/usr/bin/env python3
"""
TURBO-CDI v6.0 Server
Run: python -m v6.engine.server
"""

import uvicorn
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def main():
    """Start the API server"""
    print("=" * 50)
    print("TURBO-CDI v6.0 - Prometheus Meta-Simulation Engine")
    print("=" * 50)
    print()
    print("Starting API server...")
    print("  - HTTP API: http://localhost:8000")
    print("  - WebSocket: ws://localhost:8000/ws")
    print("  - Docs: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "v6.engine.src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

if __name__ == "__main__":
    main()
