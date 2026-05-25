"""
Tests for production security hardening.
"""

import asyncio
import json
import os
import sys

import pytest
from starlette.requests import Request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import exception_handler
from src.config import Settings


def test_production_rejects_default_jwt_secret():
    with pytest.raises(Exception) as exc_info:
        Settings(app_env="production", jwt_secret="secret")
    assert "jwt_secret" in str(exc_info.value)


def test_production_accepts_strong_jwt_secret():
    settings = Settings(
        app_env="production",
        jwt_secret="use-a-long-random-secret-for-production",
    )

    assert settings.app_env == "production"
    assert settings.jwt_secret != "secret"


def test_global_exception_handler_does_not_leak_exception_text():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/boom",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )

    response = asyncio.run(
        exception_handler(request, RuntimeError("database password leaked"))
    )
    body = json.loads(response.body)

    assert response.status_code == 500
    assert body == {
        "error": "internal_server_error",
        "message": "服务暂时不可用，请稍后重试",
    }
    assert "database password leaked" not in response.body.decode()
