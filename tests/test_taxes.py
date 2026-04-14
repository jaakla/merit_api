from merit_api import MeritAPI
import os
import json
import pytest

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_ID = os.getenv("MERIT_API_ID")
API_KEY = os.getenv("MERIT_API_KEY")
RUN_INTEGRATION = os.getenv("MERIT_API_INTEGRATION_TEST") == "true"

pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION or not API_ID or not API_KEY,
    reason="Set MERIT_API_INTEGRATION_TEST=true with credentials to run integration tests.",
)


def test_fetch_taxes_smoke():
    client = MeritAPI(API_ID, API_KEY)
    taxes = client.taxes.get_list()
    assert isinstance(taxes, list)
    if taxes:
        json.dumps(taxes[0], indent=2)
