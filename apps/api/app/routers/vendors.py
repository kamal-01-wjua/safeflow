from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from packages.db.session import get_session
from packages.db.models import Vendor
from packages.shared_types import VendorResponse, CreateVendorRequest

router = APIRouter()


# ---------------------------------------------------------
# 🟦 Create Vendor
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=VendorResponse,
    summary="Create a new vendor",
)
def create_vendor(
    payload: CreateVendorRequest,
    session: Session = Depends(get_session),
):
    vendor = Vendor(**payload.model_dump())
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    return vendor


# ---------------------------------------------------------
# 🟦 Get Vendor by ID (DB primary key)
# ---------------------------------------------------------
@router.get(
    "/{vendor_id}",
    response_model=VendorResponse,
    summary="Get a vendor by internal ID",
)
def get_vendor(
    vendor_id: int,
    session: Session = Depends(get_session),
):
    vendor = session.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


# ---------------------------------------------------------
# 🟦 List Vendors (with filters)
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=List[VendorResponse],
    summary="List vendors with optional filters",
)
def list_vendors(
    session: Session = Depends(get_session),
    vendor_code: Optional[str] = Query(
        default=None, description="Filter by vendor_code"
    ),
    country_code: Optional[str] = Query(
        default=None, description="Filter by country_code"
    ),
    risk_level: Optional[str] = Query(
        default=None, description="Filter by risk_level"
    ),
    onboarding_from: Optional[date] = Query(
        default=None, description="Filter: onboarding_date >= onboarding_from"
    ),
    onboarding_to: Optional[date] = Query(
        default=None, description="Filter: onboarding_date <= onboarding_to"
    ),
    limit: int = Query(
        default=100, ge=1, le=500, description="Max number of vendors to return"
    ),
    offset: int = Query(
        default=0, ge=0, description="Offset for pagination"
    ),
):
    query = select(Vendor)

    if vendor_code:
        query = query.where(Vendor.vendor_code == vendor_code)
    if country_code:
        query = query.where(Vendor.country_code == country_code)
    if risk_level:
        # risk_level is an Enum; cast from string if provided
        query = query.where(Vendor.risk_level == risk_level)
    if onboarding_from:
        query = query.where(Vendor.onboarding_date >= onboarding_from)
    if onboarding_to:
        query = query.where(Vendor.onboarding_date <= onboarding_to)

    query = query.order_by(Vendor.name).offset(offset).limit(limit)
    results = session.exec(query).all()
    return results
