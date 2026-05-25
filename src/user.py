import datetime
import logging
from typing import Optional
import jwt

from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.config import settings
from src.models import User
from fastapi import HTTPException

_logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)
DEFAULT_TOKEN = {"", "xxx", "undefined", "null"}


def get_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    if not credentials or not credentials.credentials:
        return None

    jwt_token = credentials.credentials.strip()
    if jwt_token.lower() in DEFAULT_TOKEN:
        return None

    try:
        payload = jwt.decode(
            jwt_token, settings.jwt_secret, algorithms=["HS256"])
        jwt_payload = User.parse_obj(payload)
        if jwt_payload.expire_at < datetime.datetime.now().timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        return jwt_payload
    except jwt.ExpiredSignatureError:
        _logger.warning(f"JWT token expired: {jwt_token[:20]}...")
        return None
    except jwt.InvalidTokenError as e:
        _logger.warning(f"JWT invalid token: {e}")
        return None
    except Exception as e:
        _logger.warning(f"JWT verification failed: {e}")
        return None
