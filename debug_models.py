# debug_models.py
import inspect
import sys

print("\n=== PYTHON PATH INSIDE CONTAINER ===")
for p in sys.path:
    print(" -", p)

print("\n=== IMPORTING MODELS ===")
from packages.db.models import transactions as tm
from packages.db.models import invoices as im

print("\n=== TRANSACTION MODEL FILE ===")
print(tm.__file__)

print("\n=== TRANSACTION SOURCE ===")
print(inspect.getsource(tm.Transaction))

print("\n=== INVOICE MODEL FILE ===")
print(im.__file__)

print("\n=== INVOICE SOURCE ===")
print(inspect.getsource(im.Invoice))
