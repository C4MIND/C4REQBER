#!/usr/bin/env python3
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load keys
if os.path.exists(".env.development"):
    with open(".env.development") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)

import asyncio

from src.pipeline.hil_pipeline import HILDiscoveryPipeline


async def test():
    p = HILDiscoveryPipeline()
    record = await p.discover('Self-healing concrete with bacterial additives')
    print('Hypotheses:')
    for i, h in enumerate(record.hypotheses):
        t = h.get('title', '')[:80]
        d = h.get('description', '')[:120]
        print(str(i) + ': ' + t)
        print('   desc: ' + d)
    print('\nVerification:', record.verification.status)
    print('Claim:', record.verification.claim[:200] if record.verification else 'N/A')

asyncio.run(test())
