"""The SDK exposes a programmatic version string (single source of truth)."""

import re

import merit_api


def test_version_is_exposed():
    assert isinstance(merit_api.__version__, str)
    assert merit_api.__version__
    assert "__version__" in merit_api.__all__


def test_version_looks_like_a_version():
    # Either a real PEP 440-ish version, or the documented source-checkout fallback.
    assert re.match(r"^\d+\.\d+\.\d+", merit_api.__version__) or merit_api.__version__ == "0.0.0+unknown"
