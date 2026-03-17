# apps/api/app/dependencies.py
"""
SafeFlow FastAPI Dependencies
==============================
Inject these into route functions to enforce authentication and RBAC.

Examples:
    # Any authenticated user (analyst or manager)
    @router.get("/")
    def list_items(user: TokenPayload = Depends(require_analyst)):
        ...

    # Manager only
    @router.delete("/{id}")
    def delete_item(id: int, user: TokenPayload = Depends(require_manager)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from .auth import TokenPayload, bearer_scheme, _extract_token


def require_analyst(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenPayload:
    """
    Require a valid JWT with role 'analyst' OR 'manager'.
    (Managers have all analyst permissions.)
    """
    user = _extract_token(credentials)
    if user.role not in {"analyst", "manager"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role}' does not have analyst access",
        )
    return user


def require_manager(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenPayload:
    """
    Require a valid JWT with role 'manager' only.
    Used for write operations and admin endpoints.
    """
    user = _extract_token(credentials)
    if user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires manager role",
        )
    return user
