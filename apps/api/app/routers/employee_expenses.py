from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from packages.db.session import get_session
from packages.db.models import EmployeeExpense
from packages.shared_types import (
    EmployeeExpenseResponse,
    CreateEmployeeExpenseRequest,
)

router = APIRouter()


# ---------------------------------------------------------
# 🟦 Create Employee Expense
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=EmployeeExpenseResponse,
    summary="Create a new employee expense",
)
def create_employee_expense(
    payload: CreateEmployeeExpenseRequest,
    session: Session = Depends(get_session),
):
    expense = EmployeeExpense(**payload.model_dump())
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


# ---------------------------------------------------------
# 🟦 Get Employee Expense by ID
# ---------------------------------------------------------
@router.get(
    "/{expense_id}",
    response_model=EmployeeExpenseResponse,
    summary="Get an employee expense by internal ID",
)
def get_employee_expense(
    expense_id: int,
    session: Session = Depends(get_session),
):
    expense = session.get(EmployeeExpense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Employee expense not found")
    return expense


# ---------------------------------------------------------
# 🟦 List Employee Expenses (with filters)
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=List[EmployeeExpenseResponse],
    summary="List employee expenses with optional filters",
)
def list_employee_expenses(
    session: Session = Depends(get_session),
    employee_id: Optional[str] = Query(
        default=None, description="Filter by employee_id"
    ),
    category: Optional[str] = Query(
        default=None, description="Filter by category"
    ),
    status: Optional[str] = Query(
        default=None, description="Filter by status"
    ),
    from_date: Optional[date] = Query(
        default=None, description="Filter: expense_date >= from_date"
    ),
    to_date: Optional[date] = Query(
        default=None, description="Filter: expense_date <= to_date"
    ),
    min_amount: Optional[float] = Query(
        default=None, description="Filter: amount >= min_amount"
    ),
    max_amount: Optional[float] = Query(
        default=None, description="Filter: amount <= max_amount"
    ),
    limit: int = Query(
        default=100, ge=1, le=500, description="Max number of expenses to return"
    ),
    offset: int = Query(
        default=0, ge=0, description="Offset for pagination"
    ),
):
    query = select(EmployeeExpense)

    if employee_id:
        query = query.where(EmployeeExpense.employee_id == employee_id)
    if category:
        query = query.where(EmployeeExpense.category == category)
    if status:
        query = query.where(EmployeeExpense.status == status)
    if from_date:
        query = query.where(EmployeeExpense.expense_date >= from_date)
    if to_date:
        query = query.where(EmployeeExpense.expense_date <= to_date)
    if min_amount is not None:
        query = query.where(EmployeeExpense.amount >= min_amount)
    if max_amount is not None:
        query = query.where(EmployeeExpense.amount <= max_amount)

    query = query.order_by(EmployeeExpense.expense_date.desc()).offset(offset).limit(
        limit
    )
    results = session.exec(query).all()
    return results
