# demo_app/core.py
"""
Core business logic for the demo app.

This file contains several deliberate issues:
- Hard‑coded API key (security)
- Plain‑string SQL concatenation (SQL injection)
- Inefficient nested loops (performance)
- Missing docstring on a public function
- Line longer than 88 characters (style)
"""

import sqlite3
from typing import List, Tuple  # imported but not used everywhere – intentional

# ❌ Hard‑coded secret – should be loaded from env/vault
API_KEY = "sk_test_000000000000000000000000000000000000"  # pragma: allowlist secret

def get_user_data(user_id: int) -> List[Tuple]:
    """Fetch all rows for a given user from the local SQLite demo DB.
    
    Note: This function is vulnerable to SQL injection because the user_id
    is directly concatenated into the query string.
    """
    conn = sqlite3.connect("demo.db")
    cursor = conn.cursor()
    
    # ❌ SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def process_all_users() -> None:
    """Demo of an O(N^2) algorithm – intentionally slow for large data."""
    # Pretend we have a list of user IDs we need to process
    user_ids = list(range(1, 101))  # 1..100
    
    # ❌ Nested loops → O(N^2)
    for i in user_ids:
        for j in user_ids:
            # Do nothing useful – just waste CPU cycles
            _ = i * j

    # Another long line that exceeds the typical 88‑char limit
    # This line is deliberately long to trigger a style warning from formatters/linters.
    print("Processing completed for all user IDs: " + ", ".join(str(uid) for uid in user_ids))

# ❌ Missing docstring for a public helper (style / documentation issue)
def helper(x, y):
    return x + y