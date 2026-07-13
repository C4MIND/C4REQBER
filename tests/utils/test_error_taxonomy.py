"""Tests for error taxonomy."""

import asyncio
import subprocess

import httpx
import pytest

from src.utils.error_taxonomy import (
    ERR_INTERNAL,
    ERR_NETWORK,
    ERR_RATE_LIMIT,
    ERR_TIMEOUT,
    ERR_VALIDATION,
    classify_exception,
)


def test_classify_timeout():
    assert classify_exception(TimeoutError()) == ERR_TIMEOUT


def test_classify_httpx_timeout():
    exc = httpx.TimeoutException("timed out")
    assert classify_exception(exc) == ERR_TIMEOUT


def test_classify_httpx_429():
    req = httpx.Request("GET", "http://example.com")
    resp = httpx.Response(429, request=req)
    exc = httpx.HTTPStatusError("429", request=req, response=resp)
    result = classify_exception(exc)
    assert result.code == "RATE_LIMIT"


def test_classify_subprocess_timeout():
    exc = subprocess.TimeoutExpired(cmd=["sleep"], timeout=1)
    assert classify_exception(exc) == ERR_TIMEOUT


def test_classify_value_error():
    assert classify_exception(ValueError("bad")) == ERR_VALIDATION


def test_classify_generic():
    assert classify_exception(RuntimeError("oops")) == ERR_INTERNAL
