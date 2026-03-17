# tests/unit/test_auth.py
"""
Unit tests for apps/api/app/auth.py

Tests cover:
- Token creation for valid roles
- Token decoding returns correct payload
- Invalid/expired tokens raise 401
- Invalid roles raise ValueError
- Role enforcement in dependencies

No DB or network dependencies.
"""

import time
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from apps.api.app.auth import (
    create_access_token,
    _decode_token,
    _extract_token,
    TokenPayload,
    TokenResponse,
    JWT_SECRET,
    JWT_ALGORITHM,
)
from apps.api.app.dependencies import require_analyst, require_manager
from jose import jwt


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_creates_analyst_token(self):
        response = create_access_token("alice", "analyst")
        assert isinstance(response, TokenResponse)
        assert response.token_type == "bearer"
        assert response.role == "analyst"
        assert len(response.access_token) > 20
        assert response.expires_in > 0

    def test_creates_manager_token(self):
        response = create_access_token("bob", "manager")
        assert response.role == "manager"

    def test_invalid_role_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid role"):
            create_access_token("alice", "superadmin")

    def test_invalid_role_guest_raises(self):
        with pytest.raises(ValueError):
            create_access_token("alice", "guest")

    def test_token_contains_correct_subject(self):
        response = create_access_token("alice", "analyst")
        payload = jwt.decode(
            response.access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        assert payload["sub"] == "alice"
        assert payload["role"] == "analyst"

    def test_token_has_expiry(self):
        response = create_access_token("alice", "analyst")
        payload = jwt.decode(
            response.access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        assert "exp" in payload
        assert payload["exp"] > time.time()


# ---------------------------------------------------------------------------
# Token decoding
# ---------------------------------------------------------------------------

class TestDecodeToken:
    def test_valid_token_decodes(self):
        response = create_access_token("alice", "analyst")
        payload = _decode_token(response.access_token)
        assert isinstance(payload, TokenPayload)
        assert payload.sub == "alice"
        assert payload.role == "analyst"

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            _decode_token("not.a.real.token")
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises_401(self):
        response = create_access_token("alice", "analyst")
        tampered = response.access_token[:-5] + "XXXXX"
        with pytest.raises(HTTPException) as exc_info:
            _decode_token(tampered)
        assert exc_info.value.status_code == 401

    def test_wrong_secret_raises_401(self):
        # Create token with different secret
        payload = {"sub": "hacker", "role": "manager"}
        bad_token = jwt.encode(payload, "wrong-secret", algorithm=JWT_ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            _decode_token(bad_token)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        # Create token that expired 1 hour ago
        payload = {
            "sub": "alice",
            "role": "analyst",
            "exp": int(time.time()) - 3600,
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            _decode_token(expired_token)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Token extraction from HTTPBearer credentials
# ---------------------------------------------------------------------------

class TestExtractToken:
    def _make_credentials(self, token: str) -> HTTPAuthorizationCredentials:
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    def test_valid_credentials_extracts_payload(self):
        response = create_access_token("alice", "analyst")
        creds = self._make_credentials(response.access_token)
        payload = _extract_token(creds)
        assert payload.sub == "alice"

    def test_none_credentials_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            _extract_token(None)
        assert exc_info.value.status_code == 401

    def test_invalid_token_in_credentials_raises_401(self):
        creds = self._make_credentials("garbage.token.here")
        with pytest.raises(HTTPException) as exc_info:
            _extract_token(creds)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# RBAC dependencies
# ---------------------------------------------------------------------------

class TestRequireAnalyst:
    def _make_credentials(self, role: str) -> HTTPAuthorizationCredentials:
        response = create_access_token("testuser", role)
        return HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=response.access_token
        )

    def test_analyst_role_passes(self):
        creds = self._make_credentials("analyst")
        user = require_analyst(creds)
        assert user.role == "analyst"

    def test_manager_role_passes_analyst_check(self):
        """Managers have all analyst permissions."""
        creds = self._make_credentials("manager")
        user = require_analyst(creds)
        assert user.role == "manager"

    def test_no_credentials_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            require_analyst(None)
        assert exc_info.value.status_code == 401


class TestRequireManager:
    def _make_credentials(self, role: str) -> HTTPAuthorizationCredentials:
        response = create_access_token("testuser", role)
        return HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=response.access_token
        )

    def test_manager_role_passes(self):
        creds = self._make_credentials("manager")
        user = require_manager(creds)
        assert user.role == "manager"

    def test_analyst_role_raises_403(self):
        """Analysts cannot access manager-only endpoints."""
        creds = self._make_credentials("analyst")
        with pytest.raises(HTTPException) as exc_info:
            require_manager(creds)
        assert exc_info.value.status_code == 403

    def test_no_credentials_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            require_manager(None)
        assert exc_info.value.status_code == 401
