"""
SafeFlow — Bad Event Producer
Tests the Phase 4 validation layer by sending deliberately invalid events.
Each event should be rejected and appear in the rejected_events table.
"""
import json
import datetime as dt
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=["localhost:19092"],
    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
)

now = dt.datetime.utcnow().replace(microsecond=0).isoformat()

BAD_EVENTS = [
    # 1. Missing account_id
    {
        "label": "MISSING_FIELD — no account_id",
        "event": {
            "event_version": "v1", "tenant_id": 1,
            "transaction_id": 99001, "transaction_reference": "BAD-001",
            "amount": 500.00, "currency": "MYR", "direction": "DEBIT",
            "status": "BOOKED", "timestamp": now,
        },
    },
    # 2. Zero amount
    {
        "label": "INVALID_AMOUNT — zero",
        "event": {
            "event_version": "v1", "tenant_id": 1,
            "transaction_id": 99002, "transaction_reference": "BAD-002",
            "account_id": "ACC-001", "amount": 0.00,
            "currency": "MYR", "direction": "DEBIT",
            "status": "BOOKED", "timestamp": now,
        },
    },
    # 3. Negative amount
    {
        "label": "INVALID_AMOUNT — negative",
        "event": {
            "event_version": "v1", "tenant_id": 1,
            "transaction_id": 99003, "transaction_reference": "BAD-003",
            "account_id": "ACC-001", "amount": -150.00,
            "currency": "MYR", "direction": "DEBIT",
            "status": "BOOKED", "timestamp": now,
        },
    },
    # 4. Amount above ceiling
    {
        "label": "INVALID_AMOUNT — above ceiling",
        "event": {
            "event_version": "v1", "tenant_id": 1,
            "transaction_id": 99004, "transaction_reference": "BAD-004",
            "account_id": "ACC-001", "amount": 99_999_999.99,
            "currency": "MYR", "direction": "DEBIT",
            "status": "BOOKED", "timestamp": now,
        },
    },
    # 5. Invalid currency
    {
        "label": "INVALID_CURRENCY — XYZ",
        "event": {
            "event_version": "v1", "tenant_id": 1,
            "transaction_id": 99005, "transaction_reference": "BAD-005",
            "account_id": "ACC-001", "amount": 500.00,
            "currency": "XYZ", "direction": "DEBIT",
            "status": "BOOKED", "timestamp": now,
        },
    },
    # 6. Invalid direction
    {
        "label": "INVALID_DIRECTION — SIDEWAYS",
        "event": {
            "event_version": "v1", "tenant_id": 1,
            "transaction_id": 99006, "transaction_reference": "BAD-006",
            "account_id": "ACC-001", "amount": 500.00,
            "currency": "MYR", "direction": "SIDEWAYS",
            "status": "BOOKED", "timestamp": now,
        },
    },
    # 7. Missing tenant_id
    {
        "label": "INVALID_TENANT — missing",
        "event": {
            "event_version": "v1",
            "transaction_id": 99007, "transaction_reference": "BAD-007",
            "account_id": "ACC-001", "amount": 500.00,
            "currency": "MYR", "direction": "DEBIT",
            "status": "BOOKED", "timestamp": now,
        },
    },
    # 8. Stale timestamp — 2 years ago
    {
        "label": "STALE_EVENT — 2 years old",
        "event": {
            "event_version": "v1", "tenant_id": 1,
            "transaction_id": 99008, "transaction_reference": "BAD-008",
            "account_id": "ACC-001", "amount": 500.00,
            "currency": "MYR", "direction": "DEBIT",
            "status": "BOOKED",
            "timestamp": "2022-01-01T00:00:00",
        },
    },
]

if __name__ == "__main__":
    print(f"Sending {len(BAD_EVENTS)} bad events to transactions_raw...")
    print("All should be REJECTED by the validation layer.\n")

    for item in BAD_EVENTS:
        producer.send("transactions_raw", value=item["event"])
        print(f"  Sent: {item['label']}")

    producer.flush()
    print("\nDone. Check rejected_events table:")
    print('  docker exec -it safeflow-postgres psql -U safeflow -d safeflow -c "SELECT rejection_code, event_id, rejection_reason FROM rejected_events ORDER BY rejected_at DESC LIMIT 10;"')
