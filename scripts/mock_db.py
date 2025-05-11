# scripts/mock_db.py

"""
Simulated in-memory issue database for autonomous workflow.
Shared across routers and agents during runtime.
"""

db = {}  # ✅ Can be seeded via /workflow/seed
