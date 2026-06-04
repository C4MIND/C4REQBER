"""API test fixtures"""
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@pytest.fixture
def test_app():
    from src.api.server import app
    return app


@pytest.fixture
def test_client(test_app):
    from fastapi.testclient import TestClient
    return TestClient(test_app)
