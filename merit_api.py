import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence

import requests


class MeritAPIError(Exception):
    """Base exception for Merit API errors with parsed API context."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
        response_body: Optional[Any] = None,
        url: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        self.response_body = response_body
        self.url = url


class MeritAPI:
    """Python client for Merit Aktiva API."""

    BASE_URLS = {
        "EE": "https://aktiva.merit.ee/api/",
        "PL": "https://program.360ksiegowosc.pl/api/",
    }

    def __init__(
        self,
        api_id: str,
        api_key: str,
        country: str = "EE",
        *,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_backoff: float = 0.5,
        retry_statuses: Sequence[int] = (408, 425, 429, 500, 502, 503, 504),
        sort_keys_for_signature: bool = True,
        idempotency_key_factory: Optional[Callable[[str, Dict[str, Any]], Optional[str]]] = None,
        session: Optional[requests.Session] = None,
        request_logger: Optional[Callable[[Dict[str, Any]], None]] = None,
        response_logger: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.api_id = api_id
        self.api_key = api_key
        self.base_url = self.BASE_URLS.get(country.upper(), self.BASE_URLS["EE"])

        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.retry_statuses = set(retry_statuses)
        self.sort_keys_for_signature = sort_keys_for_signature
        self.idempotency_key_factory = idempotency_key_factory
        self.session = session or requests.Session()
        self.request_logger = request_logger
        self.response_logger = response_logger

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

    def _serialize_body(self, body: Dict[str, Any]) -> str:
        """Serialize request body in a deterministic way for signing."""
        return json.dumps(
            body,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=self.sort_keys_for_signature,
        )

    def _authenticate(self, body: Dict[str, Any]) -> Dict[str, str]:
        """Generate authentication parameters for a request."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        body_str = self._serialize_body(body)

        # Message = apiId + timestamp + body
        data_to_sign = f"{self.api_id}{timestamp}{body_str}"

        # Compute HMAC-SHA256
        signature_bin = hmac.new(
            self.api_key.encode("utf-8"),
            data_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        signature_b64 = base64.b64encode(signature_bin).decode("utf-8")

        return {
            "apiId": self.api_id,
            "timestamp": timestamp,
            "signature": signature_b64,
        }

    def _build_headers(
        self,
        endpoint: str,
        body: Dict[str, Any],
        idempotency_key: Optional[str],
    ) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        key = idempotency_key
        if key is None and self.idempotency_key_factory is not None:
            key = self.idempotency_key_factory(endpoint, body)

        if key:
            headers["Idempotency-Key"] = key

        return headers

    def _extract_json_safely(self, response: requests.Response) -> Optional[Any]:
        try:
            return response.json()
        except ValueError:
            return None

    def _parse_error_payload(self, payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}

        error_code = payload.get("ErrorCode") or payload.get("Code") or payload.get("errorCode")
        error_message = (
            payload.get("Error")
            or payload.get("Message")
            or payload.get("error")
            or payload.get("message")
        )

        details = payload.get("Details") or payload.get("errors") or payload.get("ValidationErrors")

        success_flag = payload.get("Success")
        has_error_flag = payload.get("HasError")

        return {
            "error_code": error_code,
            "error_message": error_message,
            "details": details,
            "success_flag": success_flag,
            "has_error_flag": has_error_flag,
        }

    def _maybe_raise_api_error(self, payload: Any, *, url: str, status_code: int = 200) -> None:
        parsed = self._parse_error_payload(payload)
        success_flag = parsed.get("success_flag")
        has_error_flag = parsed.get("has_error_flag")
        error_message = parsed.get("error_message")

        should_raise = bool(error_message)
        if success_flag is False:
            should_raise = True
        if has_error_flag is True:
            should_raise = True

        if should_raise:
            raise MeritAPIError(
                error_message or "Merit API reported an error",
                status_code=status_code,
                error_code=parsed.get("error_code"),
                details=parsed.get("details"),
                response_body=payload,
                url=url,
            )

    def _redact_auth_params(self, auth_params: Dict[str, str]) -> Dict[str, str]:
        redacted = dict(auth_params)
        if "apiId" in redacted:
            value = redacted["apiId"]
            if len(value) > 4:
                redacted["apiId"] = f"{value[:2]}...{value[-2:]}"
            else:
                redacted["apiId"] = "***"
        if "signature" in redacted:
            redacted["signature"] = "***"
        return redacted

    def _emit_request_log(
        self,
        *,
        method: str,
        url: str,
        body: Dict[str, Any],
        auth_params: Dict[str, str],
        headers: Dict[str, str],
        attempt: int,
    ) -> None:
        if self.request_logger is None:
            return

        log_payload = {
            "method": method,
            "url": url,
            "body": body,
            "auth_params": self._redact_auth_params(auth_params),
            "headers": {k: ("***" if k.lower() == "idempotency-key" else v) for k, v in headers.items()},
            "attempt": attempt,
        }
        self.request_logger(log_payload)

    def _emit_response_log(
        self,
        *,
        method: str,
        url: str,
        status_code: int,
        elapsed_seconds: float,
        response_json: Optional[Any],
        attempt: int,
    ) -> None:
        if self.response_logger is None:
            return

        self.response_logger(
            {
                "method": method,
                "url": url,
                "status_code": status_code,
                "elapsed_seconds": round(elapsed_seconds, 6),
                "response_json": response_json,
                "attempt": attempt,
            }
        )

    def _post(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        version: str = "v1",
        *,
        timeout: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        """Make a POST request to the API with retries and centralized error handling."""
        body = body or {}
        auth_params = self._authenticate(body)
        url = f"{self.base_url}{version}/{endpoint.lstrip('/')}"
        headers = self._build_headers(endpoint, body, idempotency_key)
        timeout_to_use = timeout if timeout is not None else self.timeout

        attempts = self.max_retries + 1
        for attempt in range(1, attempts + 1):
            started = time.monotonic()
            self._emit_request_log(
                method="POST",
                url=url,
                body=body,
                auth_params=auth_params,
                headers=headers,
                attempt=attempt,
            )

            try:
                response = self.session.post(
                    url,
                    params=auth_params,
                    json=body,
                    headers=headers,
                    timeout=timeout_to_use,
                )
            except requests.exceptions.RequestException as exc:
                if attempt < attempts:
                    time.sleep(self.retry_backoff * (2 ** (attempt - 1)))
                    continue
                raise MeritAPIError(f"Request failed: {exc}", url=url) from exc

            elapsed = time.monotonic() - started
            payload = self._extract_json_safely(response)
            self._emit_response_log(
                method="POST",
                url=url,
                status_code=response.status_code,
                elapsed_seconds=elapsed,
                response_json=payload,
                attempt=attempt,
            )

            if response.status_code == 200:
                if payload is None:
                    raise MeritAPIError(
                        "Response was not valid JSON",
                        status_code=response.status_code,
                        response_body=response.text,
                        url=url,
                    )
                self._maybe_raise_api_error(payload, url=url, status_code=response.status_code)
                return payload

            if response.status_code in self.retry_statuses and attempt < attempts:
                time.sleep(self.retry_backoff * (2 ** (attempt - 1)))
                continue

            parsed = self._parse_error_payload(payload)
            message = parsed.get("error_message") or f"API Error ({response.status_code})"
            raise MeritAPIError(
                message,
                status_code=response.status_code,
                error_code=parsed.get("error_code"),
                details=parsed.get("details"),
                response_body=payload if payload is not None else response.text,
                url=url,
            )

        raise MeritAPIError("Unexpected retry loop termination", url=url)


class Namespace:
    """Base class for API namespaces."""

    def __init__(self, client: MeritAPI):
        self._client = client


class Customers(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """Get customer list. Optional filters: Name, RegNo."""
        return self._client._post("getcustomers", kwargs)

    def send(self, customer: Dict[str, Any]) -> Dict:
        """Create or update a customer."""
        return self._client._post("sendcustomer", customer)


class Vendors(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """Get vendor list. Optional filters: Name, RegNo."""
        return self._client._post("getvendors", kwargs)

    def send(self, vendor: Dict[str, Any]) -> Dict:
        """Create or update a vendor."""
        return self._client._post("sendvendor", vendor)


class Items(Namespace):
    def get_list(self, **kwargs) -> List[Dict]:
        """Get items list. Optional filters: Code, Name."""
        return self._client._post("getitems", kwargs)

    def add(self, items: List[Dict[str, Any]]) -> List[Dict]:
        """Add new items."""
        return self._client._post("additems", items)

    def update(self, item: Dict[str, Any]) -> Dict:
        """Update an item."""
        return self._client._post("updateitem", item)


class Sales(Namespace):
    def get_invoices(self, **kwargs) -> List[Dict]:
        """Get list of invoices. Required filters: PeriodStart, PeriodEnd."""
        return self._client._post("getinvoices", kwargs, version="v2")

    def get_invoice(self, id: str, add_attachment: bool = False) -> Dict:
        """Get single invoice details."""
        return self._client._post("getinvoice", {"Id": id, "AddAttachment": add_attachment})

    def send_invoice(self, invoice: Dict[str, Any]) -> Dict:
        """Create a sales invoice."""
        return self._client._post("sendinvoice", invoice)

    def delete_invoice(self, id: str) -> Dict:
        """Delete an invoice."""
        return self._client._post("deleteinvoice", {"Id": id})

    def send_credit_invoice(self, credit_data: Dict[str, Any]) -> Dict:
        """Create a credit invoice."""
        return self._client._post("sendcreditinvoice", credit_data)

    def get_offers(self, **kwargs) -> List[Dict]:
        """Get list of sales offers."""
        return self._client._post("getsalesoffers", kwargs)

    def get_recurring_invoices(self, **kwargs) -> List[Dict]:
        """Get recurring invoices."""
        return self._client._post("getrecurringinvoices", kwargs)


class Purchases(Namespace):
    def get_invoices(self, **kwargs) -> List[Dict]:
        """Get list of purchase invoices. Required filters: PeriodStart, PeriodEnd."""
        return self._client._post("getpurchaseinvoices", kwargs)

    def send_invoice(self, invoice: Dict[str, Any]) -> Dict:
        """Create a purchase invoice."""
        return self._client._post("sendpurchaseinvoice", invoice)


class Financial(Namespace):
    def get_payments(self, **kwargs) -> List[Dict]:
        """Get payments. Required: PeriodStart, PeriodEnd."""
        return self._client._post("getpayments", kwargs)

    def create_payment(self, payment: Dict[str, Any]) -> Dict:
        """Create a payment."""
        return self._client._post("createpayment", payment)

    def get_gl_batches(self, **kwargs) -> List[Dict]:
        """Get GL transactions. Required: PeriodStart, PeriodEnd."""
        return self._client._post("getglbatches", kwargs)

    def get_banks(self) -> List[Dict]:
        """Get list of banks."""
        return self._client._post("getbanks")

    def get_costs(self) -> List[Dict]:
        """Get cost centers."""
        return self._client._post("getcosts")

    def get_projects(self) -> List[Dict]:
        """Get projects."""
        return self._client._post("getprojects")


class Inventory(Namespace):
    def get_movements(self, **kwargs) -> List[Dict]:
        """Get inventory movements."""
        return self._client._post("getinventorymovements", kwargs)


class Assets(Namespace):
    def get_fixed_assets(self, **kwargs) -> List[Dict]:
        """Get fixed assets."""
        return self._client._post("getfixedassets", kwargs, version="v2")


class Taxes(Namespace):
    def get_list(self) -> List[Dict]:
        """Get tax rates list."""
        return self._client._post("gettaxes")

    def send(self, tax: Dict[str, Any]) -> Dict:
        """Create or update a tax rate."""
        return self._client._post("sendtax", tax, version="v2")


class Dimensions(Namespace):
    def get_list(self) -> List[Dict]:
        """Get dimensions list."""
        return self._client._post("dimensionslist", version="v2")

    def add(self, dimensions: List[Dict[str, Any]]) -> List[Dict]:
        """Add dimensions."""
        return self._client._post("adddimensions", dimensions, version="v2")


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
