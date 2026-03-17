# apps/api/app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from sqlalchemy import text

from .config import get_settings
from .auth import create_access_token, bearer_scheme, TokenResponse, _extract_token
from .dependencies import require_analyst, require_manager
from .error_handlers import register_error_handlers
from .routers import (
    transactions,
    invoices,
    vendors,
    employee_expenses,
    ml,
    risk,
    risk_preview,
    alerts,
)
from apps.api.app.routers import entities

from packages.db import init_db
from packages.db.session import engine

settings = get_settings()

# -------------------------------------------------
# App
# -------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description=(
        "SafeFlow 3.0 — Hybrid streaming + batch risk pipeline API. "
        "Authenticate via POST /auth/token to get a JWT, "
        "then include it as: Authorization: Bearer <token>"
    ),
)

# -------------------------------------------------
# Error handlers (before middleware)
# -------------------------------------------------
register_error_handlers(app)

# -------------------------------------------------
# CORS (dev-safe)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Prometheus
# -------------------------------------------------
instrumentator = Instrumentator()
instrumentator.instrument(app)
instrumentator.expose(app, include_in_schema=False)

# -------------------------------------------------
# System endpoints (no auth required)
# -------------------------------------------------

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "db": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB not ready: {type(e).__name__}")


# -------------------------------------------------
# Auth endpoints (no auth required — these issue tokens)
# -------------------------------------------------

class TokenRequest(BaseModel):
    username: str
    role: str  # "analyst" | "manager"
    # In a real system this would be password + lookup.
    # For portfolio: role is passed directly; add password check in Phase 6.


@app.post(
    "/auth/token",
    response_model=TokenResponse,
    tags=["auth"],
    summary="Issue a JWT token (dev mode — no password required)",
)
def issue_token(payload: TokenRequest):
    """
    Issues a JWT for the given username and role.
    In production this would validate credentials against a user store.
    For portfolio/dev: role is passed directly.

    Roles:
    - analyst: read-only access to all data endpoints
    - manager: analyst access + write/admin endpoints
    """
    try:
        return create_access_token(subject=payload.username, role=payload.role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(
    "/auth/me",
    tags=["auth"],
    summary="Return current token payload",
)
def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    user = _extract_token(credentials)
    return {"username": user.sub, "role": user.role}


# -------------------------------------------------
# Startup
# -------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    init_db()


# -------------------------------------------------
# API v1 router mounts
# All endpoints now available at /api/v1/<resource>
# Legacy flat paths kept for dashboard backward compat
# -------------------------------------------------

# Entities — both paths
app.include_router(entities.router)                                    # /entities (legacy)
app.include_router(entities.router, prefix="/api/v1")                 # /api/v1/entities

# Transactions
app.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"],
)
app.include_router(
    transactions.router,
    prefix="/api/v1/transactions",
    tags=["transactions v1"],
)

# Invoices
app.include_router(
    invoices.router,
    prefix="/invoices",
    tags=["invoices"],
)
app.include_router(
    invoices.router,
    prefix="/api/v1/invoices",
    tags=["invoices v1"],
)

# Vendors
app.include_router(
    vendors.router,
    prefix="/vendors",
    tags=["vendors"],
)
app.include_router(
    vendors.router,
    prefix="/api/v1/vendors",
    tags=["vendors v1"],
)

# Employee Expenses
app.include_router(
    employee_expenses.router,
    prefix="/employee-expenses",
    tags=["employee_expenses"],
)
app.include_router(
    employee_expenses.router,
    prefix="/api/v1/employee-expenses",
    tags=["employee_expenses v1"],
)

# ML
app.include_router(
    ml.router,
    prefix="/ml",
    tags=["ml"],
)

# Risk
app.include_router(
    risk.router,
    prefix="/risk",
    tags=["risk"],
)

app.include_router(
    risk_preview.router,
    prefix="/risk-preview",
    tags=["risk-preview"],
)

# Alerts — already at /api/v1/alerts from before; keep legacy mount too
app.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["alerts"],
)
app.include_router(
    alerts.router,
    prefix="/api/v1/alerts",
    tags=["Alerts v1"],
)
