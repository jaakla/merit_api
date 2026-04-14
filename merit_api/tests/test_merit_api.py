import os

import pytest

from merit_api import MeritAPI

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


def test_connection():
    client = MeritAPI(API_ID, API_KEY)

    customers = client.customers.get_list()
    items = client.items.get_list()
    banks = client.financial.get_banks()
    projects = client.financial.get_projects()

    assert customers is not None
    assert items is not None
    assert banks is not None
    assert projects is not None
