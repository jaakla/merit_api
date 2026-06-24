import json
import os
import sys
from pathlib import Path

import pytest

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# --- Verbose integration logging -------------------------------------------
# When MERIT_API_VERBOSE is truthy, integration clients print every request and
# response exchanged with Merit. The SDK sanitizes secrets (signature, tokens)
# before invoking these hooks, so the printed output is safe to share. Use
# pytest's -s flag to see it:
#   MERIT_API_INTEGRATION_TEST=true MERIT_API_VERBOSE=true \
#       pytest tests/test_integration_read.py -v -s

_VERBOSE_VALUES = {"1", "true", "yes", "on"}
_MAX_STR = 500


def _truncate(value, limit=_MAX_STR):
    """Shorten long strings (e.g. base64 PDFs) so logs stay readable."""
    if isinstance(value, str) and len(value) > limit:
        return f"{value[:limit]}… <+{len(value) - limit} chars>"
    if isinstance(value, dict):
        return {key: _truncate(item, limit) for key, item in value.items()}
    if isinstance(value, list):
        return [_truncate(item, limit) for item in value]
    return value


def _dump(value):
    try:
        return json.dumps(_truncate(value), indent=2, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return repr(_truncate(value))


def _verbose_request_logger(event):
    print(
        f"\n>>> MERIT REQUEST  [{event.get('endpoint')}] {event.get('url')}"
        f"  (attempt {event.get('attempt')})"
        f"\n    body: {_dump(event.get('body'))}",
        file=sys.stderr,
        flush=True,
    )


def _verbose_response_logger(event):
    body = event.get("payload")
    if body is None:
        body = event.get("text")
    print(
        f"\n<<< MERIT RESPONSE [{event.get('endpoint')}] status={event.get('status_code')}"
        f"\n    body: {_dump(body)}",
        file=sys.stderr,
        flush=True,
    )


def verbose_enabled() -> bool:
    return os.getenv("MERIT_API_VERBOSE", "").strip().lower() in _VERBOSE_VALUES


@pytest.fixture(scope="session")
def merit_logging_kwargs() -> dict:
    """MeritAPI kwargs that enable request/response logging when MERIT_API_VERBOSE is set.

    Returns an empty dict otherwise, so non-verbose runs build a plain client.
    """
    if verbose_enabled():
        return {
            "request_logger": _verbose_request_logger,
            "response_logger": _verbose_response_logger,
        }
    return {}
