from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from packages.db.session import get_session
from packages.db.models import Invoice
from packages.shared_types import (
    InvoiceResponse,
    CreateInvoiceRequest,
)

router = APIRouter()


# ---------------------------------------------------------
# 🟦 Create Invoice
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=InvoiceResponse,
    summary="Create a new invoice",
)
def create_invoice(
    payload: CreateInvoiceRequest,
    session: Session = Depends(get_session),
):
    invoice = Invoice(**payload.model_dump())
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


# ---------------------------------------------------------
# 🟦 Get Invoice by ID (DB primary key)
# ---------------------------------------------------------
@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get an invoice by internal ID",
)
def get_invoice(
    invoice_id: int,
    session: Session = Depends(get_session),
):
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


# ---------------------------------------------------------
# 🟦 List Invoices (with filters)
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=List[InvoiceResponse],
    summary="List invoices with optional filters",
)
def list_invoices(
    session: Session = Depends(get_session),
    vendor_id: Optional[str] = Query(
        default=None, description="Filter by vendor_id"
    ),
    employee_id: Optional[str] = Query(
        default=None, description="Filter by employee_id"
    ),
    from_date: Optional[date] = Query(
        default=None, description="Filter: invoice_date >= from_date"
    ),
    to_date: Optional[date] = Query(
        default=None, description="Filter: invoice_date <= to_date"
    ),
    limit: int = Query(
        default=100, ge=1, le=500, description="Max number of invoices to return"
    ),
    offset: int = Query(
        default=0, ge=0, description="Offset for pagination"
    ),
):
    query = select(Invoice)

    if vendor_id:
        query = query.where(Invoice.vendor_id == vendor_id)
    if employee_id:
        query = query.where(Invoice.employee_id == employee_id)
    if from_date:
        query = query.where(Invoice.invoice_date >= from_date)
    if to_date:
        query = query.where(Invoice.invoice_date <= to_date)

    query = query.order_by(Invoice.invoice_date.desc()).offset(offset).limit(limit)

    results = session.exec(query).all()
    return results
