import hmac
import hashlib
import base64
import requests
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class MeritAPIError(Exception):
    """Base exception for Merit API errors."""
    pass

class MeritAPI:
    """ Python client for Merit Aktiva API. """
    
    BASE_URLS = {
        'EE': 'https://aktiva.merit.ee/api/',
        'PL': 'https://program.360ksiegowosc.pl/api/'
    }

    def __init__(self, api_id: str, api_key: str, country: str = 'EE'):
        self.api_id = api_id
        self.api_key = api_key
        self.base_url = self.BASE_URLS.get(country.upper(), self.BASE_URLS['EE'])
        
        # Namespaces
        self.customers = Customers(self)
        self.vendors = Vendors(self)
        self.items = Items(self)
        self.sales = Sales(self)
        self.purchases = Purchases(self)
        self.financial = Financial(self)
        self.inventory = Inventory(self)
        self.assets = Assets(self)
        self.taxes = Taxes(self)
        self.dimensions = Dimensions(self)

    def _authenticate(self, body: Dict[str, Any]) -> Dict[str, str]:
        """ Generate authentication parameters for a request. """
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        body_str = json.dumps(body)
        
        # Message = apiId + timestamp + body
        data_to_sign = f"{self.api_id}{timestamp}{body_str}"
        
        # Compute HMAC-SHA256
        signature_bin = hmac.new(
            self.api_key.encode('utf-8'),
            data_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        signature_b64 = base64.b64encode(signature_bin).decode('utf-8')
        
        return {
            "apiId": self.api_id,
            "timestamp": timestamp,
            "signature": signature_b64
        }

    def _post(self, endpoint: str, body: Optional[Dict[str, Any]] = None, version: str = 'v1') -> Any:
        """ Make a POST request to the API. """
        body = body or {}
        auth_params = self._authenticate(body)
        url = f"{self.base_url}{version}/{endpoint.lstrip('/')}"
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(
                url, 
                params=auth_params, 
                json=body, 
                headers=headers
            )
            
            if response.status_code != 200:
                raise MeritAPIError(f"API Error ({response.status_code}) at {url}: {response.text}")
                
            return response.json()
        except requests.exceptions.RequestException as e:
            raise MeritAPIError(f"Request failed: {e}")

class Namespace:
    """ Base class for API namespaces. """
    def __init__(self, client: MeritAPI):
        self._client = client

class Customers(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """ Get customer list. Optional filters: Name, RegNo. """
        return self._client._post('getcustomers', kwargs)
    
    def send(self, customer: Dict[str, Any]) -> Dict:
        """ Create or update a customer. """
        return self._client._post('sendcustomer', customer)

class Vendors(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """ Get vendor list. Optional filters: Name, RegNo. """
        return self._client._post('getvendors', kwargs)
    
    def send(self, vendor: Dict[str, Any]) -> Dict:
        """ Create or update a vendor. """
        return self._client._post('sendvendor', vendor)

class Items(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """ Get items list. Optional filters: Code, Name. """
        return self._client._post('getitems', kwargs)
    
    def add(self, items: List[Dict[str, Any]]) -> List[Dict]:
        """ Add new items. """
        return self._client._post('additems', items)
    
    def update(self, item: Dict[str, Any]) -> Dict:
        """ Update an item. """
        return self._client._post('updateitem', item)

class Sales(Namespace):
    def get_invoices(self, **kwargs) -> List[Dict]:
        """ Get list of invoices. Required filters: PeriodStart, PeriodEnd. """
        return self._client._post('getinvoices', kwargs, version='v2')
    
    def get_invoice(self, id: str, add_attachment: bool = False) -> Dict:
        """ Get single invoice details. """
        return self._client._post('getinvoice', {"Id": id, "AddAttachment": add_attachment})
    
    def send_invoice(self, invoice: Dict[str, Any]) -> Dict:
        """ Create a sales invoice. """
        return self._client._post('sendinvoice', invoice)
    
    def delete_invoice(self, id: str) -> Dict:
        """ Delete an invoice. """
        return self._client._post('deleteinvoice', {"Id": id})
    
    def send_credit_invoice(self, credit_data: Dict[str, Any]) -> Dict:
        """ Create a credit invoice. """
        return self._client._post('sendcreditinvoice', credit_data)
    
    def get_offers(self, **kwargs) -> List[Dict]:
        """ Get list of sales offers. """
        return self._client._post('getsalesoffers', kwargs)
    
    def get_recurring_invoices(self, **kwargs) -> List[Dict]:
        """ Get recurring invoices. """
        return self._client._post('getrecurringinvoices', kwargs)

class Purchases(Namespace):
    def get_invoices(self, **kwargs) -> List[Dict]:
        """ Get list of purchase invoices. Required filters: PeriodStart, PeriodEnd. """
        return self._client._post('getpurchaseinvoices', kwargs)
    
    def send_invoice(self, invoice: Dict[str, Any]) -> Dict:
        """ Create a purchase invoice. """
        return self._client._post('sendpurchaseinvoice', invoice)

class Financial(Namespace):
    def get_payments(self, **kwargs) -> List[Dict]:
        """ Get payments. Required: PeriodStart, PeriodEnd. """
        return self._client._post('getpayments', kwargs)
    
    def create_payment(self, payment: Dict[str, Any]) -> Dict:
        """ Create a payment. """
        return self._client._post('createpayment', payment)
    
    def get_gl_batches(self, **kwargs) -> List[Dict]:
        """ Get GL transactions. Required: PeriodStart, PeriodEnd. """
        return self._client._post('getglbatches', kwargs)
    
    def get_banks(self) -> List[Dict]:
        """ Get list of banks. """
        return self._client._post('getbanks')
    
    def get_costs(self) -> List[Dict]:
        """ Get cost centers. """
        return self._client._post('getcosts')
    
    def get_projects(self) -> List[Dict]:
        """ Get projects. """
        return self._client._post('getprojects')

class Inventory(Namespace):
    def get_movements(self, **kwargs) -> List[Dict]:
        """ Get inventory movements. """
        return self._client._post('getinventorymovements', kwargs)

class Assets(Namespace):
    def get_fixed_assets(self, **kwargs) -> List[Dict]:
        """ Get fixed assets. """
        return self._client._post('getfixedassets', kwargs, version='v2')

class Taxes(Namespace):
    def get_list(self) -> List[Dict]:
        """ Get tax rates list. """
        return self._client._post('gettaxes')
    
    def send(self, tax: Dict[str, Any]) -> Dict:
        """ Create or update a tax rate. """
        return self._client._post('sendtax', tax, version='v2')

class Dimensions(Namespace):
    def get_list(self) -> List[Dict]:
        """ Get dimensions list. """
        return self._client._post('dimensionslist', version='v2')
    
    def add(self, dimensions: List[Dict[str, Any]]) -> List[Dict]:
        """ Add dimensions. """
        return self._client._post('adddimensions', dimensions, version='v2')

# Example Usage
if __name__ == "__main__":
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_id = os.getenv("MERIT_API_ID")
    api_key = os.getenv("MERIT_API_KEY")

    if not api_id or not api_key:
        print("Please set MERIT_API_ID and MERIT_API_KEY environment variables (or create a .env file).")
        exit(1)

    # For testing, we use credentials from the environment
    client = MeritAPI(api_id=api_id, api_key=api_key)
    
    print("Fetching customer list...")
    try:
        customers = client.customers.get_list()
        print(f"Items found: {len(customers)}")
        if customers:
            print(json.dumps(customers[0], indent=2))
    except Exception as e:
        print(f"Error: {e}")
        
    print("Fetching tax rates...")
    try:
        taxes = client.taxes.get_list()
        print(f"Successfully fetched {len(taxes)} tax rates.")
        if taxes:
            print("First tax rate:")
            print(json.dumps(taxes[0], indent=2))
    except Exception as e:
        print(f"Error fetching taxes: {e}")