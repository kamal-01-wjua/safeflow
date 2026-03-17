from sqlmodel import create_engine

# ---------------------------------------------------------
# SAFEFLOW PHASE 1 – HARD-CODED DOCKER DB URL
# ---------------------------------------------------------
# This MUST match docker-compose service:
#   service name: postgres
#   user:         safeflow
#   password:     safeflow
#   db:           safeflow
# ---------------------------------------------------------

DATABASE_URL = "postgresql+psycopg2://safeflow:safeflow@postgres:5432/safeflow"

print(f"[DB] engine.py using DATABASE_URL = {DATABASE_URL}", flush=True)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
