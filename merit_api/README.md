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
- configurable timeout and retry handling — retries apply only to idempotent requests;
  mutating writes (create invoice, create payment, …) are **not** retried, because Merit
  does not deduplicate a POST that timed out after the server already committed it, so a
  replay would create a duplicate. Such writes are retried only when an `Idempotency-Key`
  is supplied.
- request and response logging hooks with secret redaction
- optional idempotency header generation. **Note:** Merit's API does not deduplicate on
  this header, so it is not a duplicate-prevention guarantee — it only prepares for servers
  that honor it. Real protection comes from the duplicate guards below.
- duplicate-write guards for purchase invoices and payments: by default
  `purchases.send_invoice` refuses a second invoice with the same vendor + `BillNo`, and
  `financial.create_payment` refuses a second payment referencing the same `BillNo` and
  amount. Pass `allow_duplicate=True` to override.
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
