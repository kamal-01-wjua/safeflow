# packages/db/seed_entities.py
from __future__ import annotations

from sqlmodel import Session, select

from packages.db.models import Entity, EntityType, Transaction


def seed_entities_from_transactions(session: Session, max_per_type: int = 300) -> None:
    """
    Create Entity rows from Transaction.account_id and Transaction.customer_id.

    Safe to run multiple times (won't duplicate).
    """

    # Existing entity_ids by type
    existing_accounts = set(
        session.exec(select(Entity.entity_id).where(Entity.type == EntityType.ACCOUNT)).all()
    )
    existing_people = set(
        session.exec(select(Entity.entity_id).where(Entity.type == EntityType.PERSON)).all()
    )

    # --- ACCOUNTS ---
    created = 0
    account_ids = session.exec(select(Transaction.account_id).distinct()).all()
    for acc in account_ids:
        if not acc:
            continue
        ent_id = f"ACC:{acc}"
        if ent_id in existing_accounts:
            continue

        session.add(
            Entity(
                entity_id=ent_id,
                name=f"Account {acc}",
                type=EntityType.ACCOUNT,
                risk_score=0,
            )
        )
        created += 1
        if created >= max_per_type:
            break

    # --- PEOPLE (CUSTOMERS) ---
    created = 0
    customer_ids = session.exec(select(Transaction.customer_id).distinct()).all()
    for cid in customer_ids:
        if not cid:
            continue
        ent_id = f"CUST:{cid}"
        if ent_id in existing_people:
            continue

        session.add(
            Entity(
                entity_id=ent_id,
                name=f"Customer {cid}",
                type=EntityType.PERSON,
                risk_score=0,
            )
        )
        created += 1
        if created >= max_per_type:
            break
