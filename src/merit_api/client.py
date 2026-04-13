import hmac
import hashlib
import base64
import requests
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .exceptions import MeritAPIError
from .namespaces import (
    Customers, Vendors, Items, Sales, Purchases, 
    Financial, Inventory, Assets, Taxes, Dimensions
)

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
