"""
Tests for optional JWT authentication behavior.
"""

import datetime
import os
import sys

import jwt
from fastapi.security import HTTPAuthorizationCredentials

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.user import get_user


def bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def make_token(expire_at: float) -> str:
    return jwt.encode(
        {
            "login_type": "github",
            "user_name": "octocat",
            "expire_at": expire_at,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def test_missing_credentials_are_anonymous():
    assert get_user(None) is None


def test_placeholder_credentials_are_anonymous():
    assert get_user(bearer("")) is None
    assert get_user(bearer("xxx")) is None
    assert get_user(bearer("undefined")) is None
    assert get_user(bearer("null")) is None


def test_invalid_token_falls_back_to_anonymous():
    assert get_user(bearer("not-a-jwt")) is None


def test_expired_token_falls_back_to_anonymous():
    expired_at = datetime.datetime.now().timestamp() - 60
    assert get_user(bearer(make_token(expired_at))) is None


def test_valid_token_returns_user():
    expire_at = datetime.datetime.now().timestamp() + 3600
    user = get_user(bearer(make_token(expire_at)))

    assert user is not None
    assert user.login_type == "github"
    assert user.user_name == "octocat"
    assert user.expire_at == expire_at
