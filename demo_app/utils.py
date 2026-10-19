# demo_app/utils.py
"""Utility helpers – contains a few more issues for PR‑Agent to notice."""

import os
import hashlib
import base64

# ❌ Insecure use of MD5 for cryptographic purposes
def hash_password(password: str) -> str:
    """Return an MD5 hash of the password – **INSECURE** for real use."""
    # ❌ MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()

# ❌ Potential path traversal if `filename` comes from user input
def read_file_safely(filename: str) -> str:
    """Read a file and return its contents as a string.
    
    Note: No validation on `filename` – could allow directory traversal.
    """
    with open(filename, "r") as f:
        return f.read()

# ❌ Hardcoded AWS‑style credential (another secret)
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def dummy_s3_upload(data: bytes) -> None:
    """Pretend to upload data to S3 – uses hardcoded credentials."""
    # In a real app you would never embed keys like this.
    print(f"Uploading {len(data)} bytes to S3 using key {AWS_ACCESS_KEY}")

# ❌ Unused import (style)
import json  # noqa: F401  – we keep it to show an unused import warning

# ❌ Line longer than 88 characters (style)
def long_running_task() -> None:
    """Simulate a long running task by sleeping a lot – just for demo."""
    import time
    # This comment makes the line intentionally long to exceed the style limit.
    time.sleep(5)  # pragma: allowlist secret