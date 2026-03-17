from sqlmodel import Session, select
from packages.db.core import engine
from packages.db.models.transactions import Transaction
from packages.db.models.invoices import Invoice
from packages.db.models.alerts import Alert
from datetime import datetime

def fix_table(model):
    with Session(engine) as session:
        rows = session.exec(select(model)).all()
        for row in rows:
            if row.created_at is None:
                row.created_at = datetime.utcnow()
            if row.updated_at is None:
                row.updated_at = datetime.utcnow()
            session.add(row)
        session.commit()

print("Fixing NULL timestamps for transactions...")
fix_table(Transaction)

print("Fixing NULL timestamps for invoices...")
fix_table(Invoice)

print("Fixing NULL timestamps for alerts...")
fix_table(Alert)

print("DONE.")
