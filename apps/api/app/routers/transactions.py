from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from packages.db.session import get_session
from packages.db.models import Transaction
from packages.shared_types import TransactionResponse, CreateTransactionRequest

router = APIRouter()


# -----------------------------
# Helpers (response shaping)
# -----------------------------
def _derive_transaction_reference(t: Transaction) -> str:
    """
    Your seed data uses description like: 'ref=TXN-RAW-HIGH'
    If present, extract that. Otherwise fall back to tx_id or id.
    """
    desc = (getattr(t, "description", None) or "").strip()
    if "ref=" in desc:
        ref = desc.split("ref=", 1)[1].strip()
        if ref:
            return ref
    return str(getattr(t, "tx_id", None) or getattr(t, "id", ""))


def _to_transaction_response(t: Transaction) -> dict:
    """
    Convert SQLModel object -> dict and add fields required by TransactionResponse:
      - transaction_reference
      - timestamp
    """
    data = t.model_dump() if hasattr(t, "model_dump") else t.dict()

    # Ensure these fields exist for the response model
    data["transaction_reference"] = _derive_transaction_reference(t)
    data["timestamp"] = data.get("tx_time")  # timestamp = tx_time
    return data


# ---------------------------------------------------------
# 🟦 Create Transaction
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=TransactionResponse,
    summary="Create a new transaction",
)
def create_transaction(
    payload: CreateTransactionRequest,
    session: Session = Depends(get_session),
):
    tx = Transaction(**payload.model_dump())
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return _to_transaction_response(tx)


# ---------------------------------------------------------
# 🟦 Get Transaction by ID (DB primary key)
# ---------------------------------------------------------
@router.get(
    "/{tx_id}",
    response_model=TransactionResponse,
    summary="Get a transaction by internal ID",
)
def get_transaction(
    tx_id: int,
    session: Session = Depends(get_session),
):
    tx = session.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_transaction_response(tx)


# ---------------------------------------------------------
# 🟦 List Transactions (with filters)
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=List[TransactionResponse],
    summary="List transactions with optional filters",
)
def list_transactions(
    session: Session = Depends(get_session),
    account_id: Optional[str] = Query(default=None, description="Filter by account_id"),
    customer_id: Optional[str] = Query(default=None, description="Filter by customer_id"),
    min_time: Optional[datetime] = Query(default=None, description="Filter: tx_time >= min_time (UTC)"),
    max_time: Optional[datetime] = Query(default=None, description="Filter: tx_time <= max_time (UTC)"),
    limit: int = Query(default=100, ge=1, le=500, description="Max number of transactions to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
):
    query = select(Transaction)

    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if customer_id:
        query = query.where(Transaction.customer_id == customer_id)
    if min_time:
        query = query.where(Transaction.tx_time >= min_time)
    if max_time:
        query = query.where(Transaction.tx_time <= max_time)

    query = query.order_by(Transaction.tx_time.desc()).offset(offset).limit(limit)
    results = session.exec(query).all()

    # IMPORTANT: shape to match TransactionResponse schema
    return [_to_transaction_response(t) for t in results]
