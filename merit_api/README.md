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
