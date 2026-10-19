# demo_app/__init__.py
"""Top‑level package for Demo App.

This package intentionally contains a few issues for PR‑Agent to detect:
* hard‑coded secret
* SQL injection vulnerability
* O(N^2) loop
* missing type hints
* long line (> 88 chars) to trigger style warnings
"""

__all__ = ["core", "utils"]