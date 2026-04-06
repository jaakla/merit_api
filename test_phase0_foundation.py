from unittest.mock import Mock

import pytest
import requests

from merit_api import MeritAPI, MeritAPIError


def _mock_response(status_code=200, payload=None, text=""):
    response = Mock()
    response.status_code = status_code
    response.text = text
    if payload is None:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = payload
    return response


def test_signature_serialization_uses_stable_key_order_for_logically_equal_payloads():
    client = MeritAPI("test_id", "test_key")
    payload_a = {"b": 2, "a": 1}
    payload_b = {"a": 1, "b": 2}

    assert client._serialize_body(payload_a) == client._serialize_body(payload_b)


def test_retries_on_transient_http_status_then_succeeds():
    session = Mock()
    session.post.side_effect = [
        _mock_response(status_code=503, payload={"Message": "retry"}),
        _mock_response(status_code=200, payload={"Result": "ok"}),
    ]

    client = MeritAPI("test_id", "test_key", session=session, max_retries=1, retry_backoff=0)
    result = client._post("getcustomers", {})

    assert result == {"Result": "ok"}
    assert session.post.call_count == 2


def test_retries_on_request_exception_then_succeeds():
    session = Mock()
    session.post.side_effect = [
        requests.exceptions.Timeout("timeout"),
        _mock_response(status_code=200, payload={"Result": "ok"}),
    ]

    client = MeritAPI("test_id", "test_key", session=session, max_retries=1, retry_backoff=0)
    result = client._post("getcustomers", {})

    assert result == {"Result": "ok"}
    assert session.post.call_count == 2


def test_raises_api_error_when_payload_contains_business_error():
    session = Mock()
    session.post.return_value = _mock_response(
        status_code=200,
        payload={"Success": False, "ErrorCode": "E-100", "Error": "Business rule failed"},
    )
    client = MeritAPI("test_id", "test_key", session=session)

    with pytest.raises(MeritAPIError) as exc:
        client._post("sendinvoice", {"InvoiceNo": "INV-1"})

    assert exc.value.error_code == "E-100"
    assert exc.value.status_code == 200


def test_idempotency_key_from_factory_is_included_in_request_headers():
    session = Mock()
    session.post.return_value = _mock_response(status_code=200, payload={"ok": True})

    client = MeritAPI(
        "test_id",
        "test_key",
        session=session,
        idempotency_key_factory=lambda endpoint, body: f"{endpoint}:{body.get('InvoiceNo')}",
    )

    client._post("sendinvoice", {"InvoiceNo": "INV-5"})

    call_kwargs = session.post.call_args.kwargs
    assert call_kwargs["headers"]["Idempotency-Key"] == "sendinvoice:INV-5"


def test_request_and_response_loggers_are_called_with_redacted_secret_fields():
    session = Mock()
    session.post.return_value = _mock_response(status_code=200, payload={"ok": True})
    request_events = []
    response_events = []

    client = MeritAPI(
        "my_api_id",
        "test_key",
        session=session,
        request_logger=request_events.append,
        response_logger=response_events.append,
    )

    client._post("getcustomers", {"Name": "Acme"}, idempotency_key="idem-secret")

    assert request_events
    assert response_events
    assert request_events[0]["auth_params"]["signature"] == "***"
    assert request_events[0]["headers"]["Idempotency-Key"] == "***"
    assert response_events[0]["status_code"] == 200
