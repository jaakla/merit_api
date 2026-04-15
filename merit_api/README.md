# merit-api

Python SDK for the Merit Aktiva API.

## Installation

```bash
pip install merit-api
```

## Usage

```python
from merit_api import MeritAPI

client = MeritAPI(api_id="YOUR_API_ID", api_key="YOUR_API_KEY")

customers = client.customers.get_list()
invoices = client.sales.get_invoices(
    PeriodStart="2024-01-01",
    PeriodEnd="2024-01-31",
)
```

## Features

- deterministic request-body serialization for signing
- configurable timeout and retry handling
- request and response logging hooks with secret redaction
- optional idempotency header generation
- API-level business error parsing from HTTP 200 responses

## Testing and method coverage report

Run tests:

```bash
pytest -q
```

Regenerate the method-level read/write coverage report:

```bash
python scripts_report_method_test_coverage.py
```

The report is written to `reports/method_test_coverage.md` and CI checks that this file stays up to date.
