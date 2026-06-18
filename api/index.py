"""Vercel serverless entrypoint.

Exposes the FastAPI ASGI ``app`` that Vercel's Python runtime serves. The
package lives under ``src/`` (src layout), so we add it to ``sys.path`` here
rather than relying on a build step. The catalog is fetched from S3 at runtime,
so nothing data-related needs bundling.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ersilia_search.api.app import app  # noqa: E402

__all__ = ["app"]
