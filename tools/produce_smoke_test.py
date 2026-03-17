"""
Smoke test producer — runs from HOST machine (not inside Docker).
Sends 5 synthetic transactions to transactions_raw topic.
Uses localhost:19092 (Redpanda external listener port).
"""
import json
import datetime as dt
import random
import uuid

from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=["localhost:19092"],
    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
)

ACCOUNTS = ["ACC-001", "ACC-002", "ACC-003", "ACC-004", "ACC-005"]
VENDORS = ["VEND-100", "VEND-200", None, None, None]
EMPLOYEES = ["EMP-001", None, "EMP-003", None, None]


def make_event(i: int) -> dict:
    now = dt.datetime.utcnow().replace(microsecond=0)
    return {
        "event_version": "v1",
        "tenant_id": 1,
        "transaction_id": 9000 + i,
        "transaction_reference": f"SMOKE-{uuid.uuid4().hex[:8].upper()}",
        "account_id": random.choice(ACCOUNTS),
        "amount": round(random.uniform(10, 25000), 2),
        "currency": "MYR",
        "direction": random.choice(["DEBIT", "CREDIT"]),
        "status": "BOOKED",
        "timestamp": now.isoformat(),
        "vendor_code": random.choice(VENDORS),
        "employee_id": random.choice(EMPLOYEES),
    }


if __name__ == "__main__":
    print("Sending 5 smoke test events to transactions_raw...")
    for i in range(5):
        evt = make_event(i)
        producer.send("transactions_raw", value=evt)
        print(f"  Sent: {evt['transaction_reference']} amount={evt['amount']} account={evt['account_id']}")

    producer.flush()
    print("Done. Check worker logs and Postgres.")
