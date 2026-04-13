# Merit API Python Client

A Python shared library for interacting with the Merit Aktiva API.

## Installation

```bash
pip install merit-api
```

## Usage

```python
from merit_api import MeritAPI

client = MeritAPI(api_id="YOUR_API_ID", api_key="YOUR_API_KEY")

# Get customers
customers = client.customers.get_list()

# Get invoices
invoices = client.sales.get_invoices(PeriodStart="2024-01-01", PeriodEnd="2024-01-31")
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```
