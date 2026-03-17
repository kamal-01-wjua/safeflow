# apps/api/app/auth.py
"""
SafeFlow JWT Authentication
============================
Simple JWT-based auth with two roles: analyst and manager.

Tokens are signed with HS256. Secret key comes from environment variable
SAFEFLOW_JWT_SECRET (falls back to a dev-only default — never use in prod).

Token payload:
    {
        "sub": "username",
        "role": "analyst" | "manager",
        "exp": <unix timestamp>
    }

Usage:
    # Create a token (e.g. for testing)
    token = create_access_token(subject="alice", role="analyst")

    # Verify in a route via dependency injection:
    user = Depends(require_analyst)
    user = Depends(require_manager)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

JWT_SECRET = os.getenv("SAFEFLOW_JWT_SECRET", "safeflow-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("SAFEFLOW_JWT_EXPIRY_MINUTES", "60"))

ROLES = {"analyst", "manager"}

# HTTPBearer extracts the token from Authorization: Bearer <token>
bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Token model
# ---------------------------------------------------------------------------

class TokenPayload(BaseModel):
    sub: str            # username / user id
    role: str           # analyst | manager
    exp: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_in: int     # seconds


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def create_access_token(subject: str, role: str) -> TokenResponse:
    """
    Create a signed JWT for the given subject and role.
    Used by the /auth/token endpoint and tests.
    """
    if role not in ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of: {ROLES}")

    expires_delta = timedelta(minutes=JWT_EXPIRY_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=role,
        expires_in=int(expires_delta.total_seconds()),
    )


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def _decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT. Raises HTTPException on any failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        role = payload.get("role")
        if not sub or not role:
            raise credentials_exception
        return TokenPayload(sub=sub, role=role, exp=payload.get("exp"))
    except JWTError:
        raise credentials_exception


def _extract_token(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> TokenPayload:
    """
    Extract and verify token from HTTPBearer credentials.
    Raises 401 if missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode_token(credentials.credentials)
