import os

from merit_api import MeritAPI

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def main():
    api_id = os.getenv("MERIT_API_ID")
    api_key = os.getenv("MERIT_API_KEY")

    if not api_id or not api_key:
        return

    client = MeritAPI(api_id, api_key)
    customers = client.customers.get_list()
    items = client.items.get_list()

    if not customers or not items:
        return

    customer = customers[0]
    item = items[0]
    invoice_data = {
        "Customer": {"Id": customer["Id"]},
        "DocDate": "20260406",
        "TransactionDate": "20260406",
        "DueDate": "20260413",
        "InvoiceNo": "INV-12345",
        "CurrencyCode": "EUR",
        "PriceInclVat": False,
        "InvoiceRow": [
            {
                "Item": {
                    "Code": item["Code"],
                    "Description": item.get("Name", "Consulting"),
                    "UOMName": item.get("UnitofMeasureName", "tk"),
                },
                "Quantity": 1,
                "Price": 100,
                "TaxId": "b9b25735-6a15-4d4e-8720-25b254ae3d21",
                "Account": "30001",
            }
        ],
        "TaxAmount": [
            {"TaxId": "b9b25735-6a15-4d4e-8720-25b254ae3d21", "Amount": 20.00}
        ],
        "TotalAmount": 120,
    }

    client._post("sendinvoice", invoice_data, version="v1")


if __name__ == "__main__":
    main()
