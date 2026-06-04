import asyncio

import pytest


# Skip if optional dependency not available
try:
    import textual
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False

pytestmark = pytest.mark.skipif(not HAS_TEXTUAL, reason="textual not installed")


def test_asyncio_run():
    print("Running loop:", asyncio._get_running_loop())
    try:
        result = asyncio.run(async_fn())
        print("Result:", result)
    except Exception as e:
        print("Exception:", type(e).__name__, e)

async def async_fn():
    return "hello"
