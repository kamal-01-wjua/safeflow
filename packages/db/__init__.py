from sqlmodel import SQLModel

# Use the engine defined in session.py
from .session import engine


def init_db() -> None:
    """
    Initialize the database and create all SQLModel tables.

    Why this matters:
    - SQLModel only creates tables for models that are imported.
    - Importing `packages.db.models` ensures all models (transactions,
      invoices, vendors, employee_expenses, etc.) are registered.
    """
    # Import ALL models so they are registered in SQLModel.metadata
    # This is safe because `packages.db.models.__init__` imports everything cleanly.
    from . import models  # noqa: F401

    # Create any missing tables
    SQLModel.metadata.create_all(bind=engine)


__all__ = ["init_db", "engine"]
