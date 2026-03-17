import json
import datetime as dt
from kafka import KafkaProducer

# ---------------------------------------------------------
# Kafka producer using internal Docker hostname for Redpanda
# ---------------------------------------------------------
producer = KafkaProducer(
    bootstrap_servers=["redpanda:9092"],  # 🔥 key fix here
    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
)

def send_raw_event(evt: dict):
    """Send a single raw transaction event to the transactions_raw topic."""
    producer.send("transactions_raw", value=evt)


if __name__ == "__main__":
    now = dt.datetime.utcnow().replace(microsecond=0)

    # LOW-RISK RAW TRANSACTION
    low_event = {
        "event_version": "v1",
        "tenant_id": 1,
        "transaction_id": 1,
        "transaction_reference": "TXN-RAW-LOW",
        "account_id": "ACC-001",
        "amount": 50,
        "currency": "MYR",
        "direction": "DEBIT",
        "status": "BOOKED",
        "timestamp": now.isoformat(),
        "vendor_code": None,
        "employee_id": None,
    }

    # HIGH-RISK RAW TRANSACTION
    high_event = {
        "event_version": "v1",
        "tenant_id": 1,
        "transaction_id": 2,
        "transaction_reference": "TXN-RAW-HIGH",
        "account_id": "ACC-002",
        "amount": 20000,
        "currency": "MYR",
        "direction": "DEBIT",
        "status": "BOOKED",
        "timestamp": (now + dt.timedelta(minutes=5)).isoformat(),
        "vendor_code": "VEND-777",
        "employee_id": "EMP-007",
    }

    print("Sending LOW-RISK RAW event...")
    send_raw_event(low_event)

    print("Sending HIGH-RISK RAW event...")
    send_raw_event(high_event)

    producer.flush()
    print("DONE — messages sent.")
