from merit_api import MeritAPI
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def main():
    API_ID = os.getenv("MERIT_API_ID")
    API_KEY = os.getenv("MERIT_API_KEY")
    
    if not API_ID or not API_KEY:
        print("Please set MERIT_API_ID and MERIT_API_KEY environment variables (or create a .env file).")
        return
        
    client = MeritAPI(API_ID, API_KEY)
    
    # Try with "InvoiceRow" instead of "InvoiceLines" or "InvoiceRows"
    # Fetch existing data to ensure valid identifiers
    customers = client.customers.get_list()
    items = client.items.get_list()
    
    if not customers or not items:
        print("Need at least one customer and one item in the system to test.")
        return
        
    customer = customers[0]
    item = items[0]
    
    # Using existing customer ID and existing Item Code
    invoice_data = {
        "Customer": customer,
        "DocDate": "20260406120000",
        "DueDate": "20260413120000",
        "InvoiceNo": "INV-12345",
        "TotalAmount": 100,
        "InvoiceRow": [
            {
                "Item": {
                    "Code": item['Code'],
                    "Description": item.get('Name', 'Consulting'),
                    "UOMName": item.get('UnitofMeasureName', 'tk')
                },
                "Quantity": 1, 
                "Price": 100,
                "TaxId": "b9b25735-6a15-4d4e-8720-25b254ae3d21"  # 20% Tax
            }
        ],
        "TaxAmount": [
            {"TaxId": "b9b25735-6a15-4d4e-8720-25b254ae3d21", "Amount": 20.00}
        ]
    }
    
    try:
        # V1 is sufficient for this check
        res = client._post('sendinvoice', invoice_data, version='v1')
        print("Success! Invoice Created.", res)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
