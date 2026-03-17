from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GraphNodeType(str, Enum):
    ACCOUNT = "ACCOUNT"
    VENDOR = "VENDOR"
    EMPLOYEE = "EMPLOYEE"
    TRANSACTION = "TRANSACTION"
    INVOICE = "INVOICE"
    TENANT = "TENANT"


@dataclass
class TransactionGraphContext:
    """
    Minimal graph-relevant context for a transaction.

    This is what the graph engine needs to know in order to
    compute relational risk. Later we can extend this.
    """
    tenant_id: Optional[int]
    transaction_id: Optional[int]
    transaction_reference: str

    account_id: Optional[str]
    vendor_code: Optional[str]
    employee_id: Optional[str]  # from linked employee expense, if any


@dataclass
class GraphMetrics:
    """
    Raw graph metrics used to derive a graph risk score.
    These are examples; we can expand in Phase 3.
    """
    degree: Optional[int] = None
    community_size: Optional[int] = None
    pagerank: Optional[float] = None
    avg_neighbor_risk: Optional[float] = None  # 0–1
