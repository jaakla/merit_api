import hmac
import hashlib
import base64
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

import requests

from .exceptions import MeritAPIError
from .namespaces import (
    Customers,
    Vendors,
    Items,
    Sales,
    Purchases,
    Financial,
    Inventory,
    Assets,
    Taxes,
    Dimensions,
)


JsonDict = Dict[str, Any]
LoggerCallback = Callable[[JsonDict], None]
IdempotencyKeyFactory = Callable[[str, Any], Optional[str]]


class MeritAPI:
    """Python client for Merit Aktiva API."""

    BASE_URLS = {
        "EE": "https://aktiva.merit.ee/api/",
        "PL": "https://program.360ksiegowosc.pl/api/",
    }
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        api_id: str,
        api_key: str,
        country: str = "EE",
        *,
        session: Optional[requests.Session] = None,
        timeout: float = 30.0,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
        idempotency_key_factory: Optional[IdempotencyKeyFactory] = None,
        request_logger: Optional[LoggerCallback] = None,
        response_logger: Optional[LoggerCallback] = None,
    ):
        self.api_id = api_id
        self.api_key = api_key
        self.base_url = self.BASE_URLS.get(country.upper(), self.BASE_URLS['EE'])
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.idempotency_key_factory = idempotency_key_factory
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

    def _serialize_body(self, body: Any) -> str:
        """Serialize request bodies deterministically for signing and transport."""
        return json.dumps(body, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

    def _authenticate(self, serialized_body: str) -> Dict[str, str]:
        """Generate authentication parameters for a request."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

        # Message = apiId + timestamp + body
        data_to_sign = f"{self.api_id}{timestamp}{serialized_body}"

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

    def _resolve_idempotency_key(self, endpoint: str, body: Any, idempotency_key: Optional[str]) -> Optional[str]:
        if idempotency_key is not None:
            return idempotency_key
        if self.idempotency_key_factory is None:
            return None
        return self.idempotency_key_factory(endpoint, body)

    def _build_headers(self, serialized_body: str, endpoint: str, body: Any, idempotency_key: Optional[str]) -> JsonDict:
        headers: JsonDict = {"Content-Type": "application/json"}
        resolved_idempotency_key = self._resolve_idempotency_key(endpoint, body, idempotency_key)
        if resolved_idempotency_key:
            headers["Idempotency-Key"] = resolved_idempotency_key
        headers["Content-Length"] = str(len(serialized_body.encode("utf-8")))
        return headers

    def _sanitize_for_log(self, value: Any, *, path: str = "") -> Any:
        secret_keys = {"signature", "idempotency-key", "authorization", "api_key", "api-key"}

        if isinstance(value, dict):
            sanitized: JsonDict = {}
            for key, nested_value in value.items():
                normalized_key = str(key).lower()
                nested_path = f"{path}.{key}" if path else str(key)
                if normalized_key in secret_keys:
                    sanitized[key] = "***"
                else:
                    sanitized[key] = self._sanitize_for_log(nested_value, path=nested_path)
            return sanitized

        if isinstance(value, list):
            return [self._sanitize_for_log(item, path=path) for item in value]

        return value

    def _log_request(
        self,
        *,
        url: str,
        endpoint: str,
        version: str,
        body: Any,
        headers: JsonDict,
        auth_params: JsonDict,
        attempt: int,
    ) -> None:
        if self.request_logger is None:
            return
        self.request_logger(
            {
                "url": url,
                "endpoint": endpoint,
                "version": version,
                "body": self._sanitize_for_log(body),
                "headers": self._sanitize_for_log(headers),
                "auth_params": self._sanitize_for_log(auth_params),
                "attempt": attempt,
            }
        )

    def _log_response(self, *, url: str, endpoint: str, response: requests.Response, payload: Any = None) -> None:
        if self.response_logger is None:
            return
        event: JsonDict = {
            "url": url,
            "endpoint": endpoint,
            "status_code": response.status_code,
            "text": response.text,
        }
        if payload is not None:
            event["payload"] = self._sanitize_for_log(payload)
        self.response_logger(event)

    def _raise_for_business_error(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        if payload.get("Success", True) is not False:
            return

        error_code = payload.get("ErrorCode")
        message = payload.get("Error") or payload.get("Message") or "Merit API business error"
        raise MeritAPIError(
            str(message),
            status_code=200,
            error_code=str(error_code) if error_code is not None else None,
            response_body=payload,
        )

    def _post(
        self,
        endpoint: str,
        body: Optional[Any] = None,
        version: str = "v1",
        *,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        """Make a POST request to the API."""
        body = body or {}
        serialized_body = self._serialize_body(body)
        auth_params = self._authenticate(serialized_body)
        url = f"{self.base_url}{version}/{endpoint.lstrip('/')}"
        headers = self._build_headers(serialized_body, endpoint, body, idempotency_key)

        for attempt in range(self.max_retries + 1):
            self._log_request(
                url=url,
                endpoint=endpoint,
                version=version,
                body=body,
                headers=headers,
                auth_params=auth_params,
                attempt=attempt + 1,
            )
            try:
                response = self.session.post(
                    url,
                    params=auth_params,
                    data=serialized_body.encode("utf-8"),
                    headers=headers,
                    timeout=self.timeout,
                )
            except requests.exceptions.RequestException as exc:
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff * (attempt + 1))
                    continue
                raise MeritAPIError(f"Request failed: {exc}") from exc

            try:
                payload = response.json()
            except ValueError:
                payload = None

            self._log_response(url=url, endpoint=endpoint, response=response, payload=payload)

            if response.status_code != 200:
                if response.status_code in self.RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                    time.sleep(self.retry_backoff * (attempt + 1))
                    continue
                raise MeritAPIError(
                    f"API Error ({response.status_code}) at {url}: {response.text}",
                    status_code=response.status_code,
                    response_body=payload if payload is not None else response.text,
                )

            if payload is None:
                raise MeritAPIError(
                    f"Invalid JSON response from {url}: {response.text}",
                    status_code=response.status_code,
                    response_body=response.text,
                )

            self._raise_for_business_error(payload)
            return payload

        raise MeritAPIError(f"Request failed after retries for {url}")
