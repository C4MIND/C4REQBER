#!/usr/bin/env python3
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from src.knowledge.multi_source import MultiSourceSearcher


async def test():
    s = MultiSourceSearcher()
    result = await s.search_all('Self-healing concrete with bacterial additives')
    print('Total papers:', result.get('total_papers', 0))
    print('Sources used:', result.get('sources_used', 0))
    print('Source names:', result.get('source_names', []))
    for i, p in enumerate(result.get('papers', [])[:3]):
        print(i, ':', p.get('title', '')[:50], '|', p.get('url', '')[:50])

asyncio.run(test())
