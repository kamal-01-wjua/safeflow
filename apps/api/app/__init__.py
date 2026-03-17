"""
App package initializer for SafeFlow API.

This makes sure our monorepo folders (like `packages`, `services`, etc.)
are on PYTHONPATH when running inside Docker, so imports like
`from packages.db.session import get_session` work.
"""

import sys
from pathlib import Path

# This file is: /app/apps/api/app/__init__.py
# So BASE_DIR is: /app/apps/api
BASE_DIR = Path(__file__).resolve().parent.parent

# Monorepo root: /app  (because /app/apps/api -> parent -> /app/apps -> parent -> /app)
MONOREPO_ROOT = BASE_DIR.parent.parent

# Candidate paths that may contain our internal code
candidate_paths = {
    BASE_DIR,                  # /app/apps/api
    BASE_DIR.parent,           # /app/apps
    MONOREPO_ROOT,             # /app
    MONOREPO_ROOT / "safeflow" # /app/safeflow  (where the monorepo code often lives)
}

for path in candidate_paths:
    p_str = str(path)
    if p_str not in sys.path:
        sys.path.append(p_str)
