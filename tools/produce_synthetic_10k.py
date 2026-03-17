"""
SafeFlow — Synthetic Transaction Producer
==========================================
Generates and streams 10,000 synthetic transaction events to
the transactions_raw Redpanda topic.

Design principles:
  - Entity-based: each account has a behavioral profile (normal spend range,
    preferred vendors, typical transaction frequency)
  - Risk-realistic: ~70% low-risk, ~20% medium-risk, ~10% high-risk events
  - Velocity patterns: some accounts have burst periods (fraud simulation)
  - Temporal spread: events distributed over the last 90 days

Run from host machine (requires Docker stack running):
    python tools/produce_synthetic_10k.py
    python tools/produce_synthetic_10k.py --count 500 --batch-size 50
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from kafka import KafkaProducer

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BOOTSTRAP_SERVERS = ["localhost:19092"]
TOPIC = "transactions_raw"
DEFAULT_COUNT = 10_000
DEFAULT_BATCH_SIZE = 100   # flush every N messages
DEFAULT_DELAY_MS = 0       # ms between batches (0 = as fast as possible)

CURRENCIES = ["MYR", "USD", "SGD", "EUR"]
CURRENCY_WEIGHTS = [0.70, 0.15, 0.10, 0.05]

CHANNELS = ["ONLINE", "POS", "ATM", "MOBILE", "INTERNAL"]
CHANNEL_WEIGHTS = [0.35, 0.30, 0.15, 0.15, 0.05]

STATUSES = ["BOOKED", "POSTED", "PENDING"]
STATUS_WEIGHTS = [0.70, 0.20, 0.10]

DIRECTIONS = ["DEBIT", "CREDIT"]
DIRECTION_WEIGHTS = [0.65, 0.35]


# ---------------------------------------------------------------------------
# Entity profiles — simulate realistic account behavior
# ---------------------------------------------------------------------------

@dataclass
class EntityProfile:
    account_id: str
    entity_id: str          # links to entities table (ENT-0001 etc)
    risk_tier: str          # LOW, MEDIUM, HIGH
    base_amount_min: float
    base_amount_max: float
    vendor_codes: list[str]
    employee_ids: list[str]
    burst_probability: float   # chance of a velocity spike event


ENTITY_PROFILES: list[EntityProfile] = [
    # Low-risk entities — stable small transactions
    EntityProfile("ACC-ENT-001", "ENT-0001", "LOW",    10,    500,   ["VEND-001", "VEND-002"], [],            0.01),
    EntityProfile("ACC-ENT-002", "ENT-0002", "LOW",    50,    800,   ["VEND-003"],             ["EMP-001"],   0.02),
    EntityProfile("ACC-ENT-003", "ENT-0003", "LOW",    20,    300,   [],                       [],            0.01),
    EntityProfile("ACC-ENT-004", "ENT-0004", "LOW",    100,   1200,  ["VEND-004", "VEND-005"], ["EMP-002"],   0.02),
    EntityProfile("ACC-ENT-005", "ENT-0005", "LOW",    30,    600,   ["VEND-001"],             [],            0.01),

    # Medium-risk entities — moderate amounts, occasional anomalies
    EntityProfile("ACC-ENT-006", "ENT-0006", "MEDIUM", 500,   5000,  ["VEND-010", "VEND-011"], ["EMP-003"],   0.05),
    EntityProfile("ACC-ENT-007", "ENT-0007", "MEDIUM", 300,   4000,  ["VEND-012"],             ["EMP-004"],   0.06),
    EntityProfile("ACC-ENT-008", "ENT-0008", "MEDIUM", 1000,  8000,  ["VEND-013", "VEND-014"], [],            0.07),
    EntityProfile("ACC-ENT-009", "ENT-0009", "MEDIUM", 200,   3500,  [],                       ["EMP-005"],   0.05),
    EntityProfile("ACC-ENT-010", "ENT-0010", "MEDIUM", 800,   6000,  ["VEND-015"],             ["EMP-006"],   0.08),

    # High-risk entities — large amounts, suspicious patterns
    EntityProfile("ACC-ENT-011", "ENT-0011", "HIGH",   5000,  50000, ["VEND-777", "VEND-888"], ["EMP-007"],   0.20),
    EntityProfile("ACC-ENT-012", "ENT-0012", "HIGH",   8000,  80000, ["VEND-999"],             ["EMP-008"],   0.25),
    EntityProfile("ACC-ENT-013", "ENT-0013", "HIGH",   3000,  30000, ["VEND-777"],             [],            0.15),
    EntityProfile("ACC-ENT-014", "ENT-0014", "HIGH",   10000, 95000, [],                       ["EMP-009"],   0.30),
    EntityProfile("ACC-ENT-015", "ENT-0015", "HIGH",   4000,  40000, ["VEND-888", "VEND-999"], ["EMP-010"],   0.20),
]

# Entity weight: skew toward low/medium for realistic distribution
# ~50% low-risk entities, ~33% medium, ~17% high
ENTITY_WEIGHTS = [
    # LOW (5 entities) — higher weight
    8, 8, 7, 7, 7,
    # MEDIUM (5 entities)
    5, 5, 5, 4, 4,
    # HIGH (5 entities) — lower weight
    3, 2, 2, 2, 2,
]


# ---------------------------------------------------------------------------
# Event generation
# ---------------------------------------------------------------------------

def _random_timestamp(days_back: int = 90) -> dt.datetime:
    """Random UTC timestamp within the last N days."""
    now = dt.datetime.utcnow()
    delta = dt.timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (now - delta).replace(microsecond=0)


def _make_event(tx_seq: int, profile: EntityProfile) -> dict:
    """Generate one synthetic transaction event from an entity profile."""

    # Burst mode: if this entity is in a burst, multiply amount by 3-10x
    is_burst = random.random() < profile.burst_probability
    if is_burst:
        amount = round(random.uniform(
            profile.base_amount_max * 3,
            profile.base_amount_max * 10,
        ), 2)
    else:
        amount = round(random.uniform(
            profile.base_amount_min,
            profile.base_amount_max,
        ), 2)

    # Vendor and employee — sometimes None
    vendor = random.choice(profile.vendor_codes) if profile.vendor_codes and random.random() > 0.3 else None
    employee = random.choice(profile.employee_ids) if profile.employee_ids and random.random() > 0.4 else None

    return {
        "event_version": "v1",
        "tenant_id": 1,
        "transaction_id": tx_seq,
        "transaction_reference": f"SYN-{uuid.uuid4().hex[:10].upper()}",
        "account_id": profile.account_id,
        "amount": amount,
        "currency": random.choices(CURRENCIES, CURRENCY_WEIGHTS)[0],
        "direction": random.choices(DIRECTIONS, DIRECTION_WEIGHTS)[0],
        "status": random.choices(STATUSES, STATUS_WEIGHTS)[0],
        "timestamp": _random_timestamp().isoformat(),
        "vendor_code": vendor,
        "employee_id": employee,
    }


# ---------------------------------------------------------------------------
# Producer
# ---------------------------------------------------------------------------

def run(count: int, batch_size: int, delay_ms: float) -> None:
    print(f"SafeFlow Synthetic Producer")
    print(f"  Target:     {count:,} events")
    print(f"  Topic:      {TOPIC}")
    print(f"  Brokers:    {BOOTSTRAP_SERVERS}")
    print(f"  Batch size: {batch_size}")
    print()

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        # Performance tuning for bulk send
        linger_ms=50,
        batch_size=65536,
        compression_type="gzip",
    )

    start = time.time()
    sent = 0
    errors = 0

    # Start tx_id from 10000 to avoid colliding with smoke test events
    tx_seq_start = 10_000

    for i in range(count):
        profile = random.choices(ENTITY_PROFILES, ENTITY_WEIGHTS)[0]
        evt = _make_event(tx_seq_start + i, profile)

        try:
            producer.send(TOPIC, value=evt)
            sent += 1
        except Exception as e:
            errors += 1
            print(f"  [ERROR] Failed to send event {i}: {e}")

        # Batch progress reporting
        if (i + 1) % batch_size == 0:
            producer.flush()
            elapsed = time.time() - start
            rate = sent / elapsed if elapsed > 0 else 0
            print(f"  [{i+1:>6}/{count}] sent={sent:,} errors={errors} "
                  f"rate={rate:.0f} msg/s elapsed={elapsed:.1f}s")

            if delay_ms > 0:
                time.sleep(delay_ms / 1000)

    # Final flush
    producer.flush()
    producer.close()

    elapsed = time.time() - start
    rate = sent / elapsed if elapsed > 0 else 0

    print()
    print(f"Done.")
    print(f"  Sent:    {sent:,} events")
    print(f"  Errors:  {errors}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"  Rate:    {rate:.0f} msg/s")
    print()
    print(f"Check worker: docker logs safeflow-risk-worker -f")
    print(f"Check DB:     docker exec -it safeflow-postgres psql -U safeflow -d safeflow "
          f"-c \"SELECT COUNT(*) FROM transactions;\"")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SafeFlow synthetic transaction producer")
    parser.add_argument("--count",      type=int,   default=DEFAULT_COUNT,      help="Number of events to send")
    parser.add_argument("--batch-size", type=int,   default=DEFAULT_BATCH_SIZE, help="Flush and report every N events")
    parser.add_argument("--delay-ms",   type=float, default=DEFAULT_DELAY_MS,   help="Delay between batches in ms")
    args = parser.parse_args()

    run(args.count, args.batch_size, args.delay_ms)
