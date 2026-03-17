# conftest.py
"""
Pytest configuration and shared fixtures for SafeFlow test suite.
Located at repo root so all test modules can import it.
"""

import sys
import os

# Ensure the repo root is on the Python path so all packages resolve correctly
# This is needed because we run pytest from the repo root, not from inside apps/api
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
