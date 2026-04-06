from unittest.mock import Mock

from merit_api import MeritAPI


def _response(payload=None):
    response = Mock()
    response.status_code = 200
    response.json.return_value = payload if payload is not None else {"ok": True}
    return response


def _assert_last_request(session: Mock, expected_path: str):
    url = session.post.call_args.kwargs["url"]
    assert url.endswith(expected_path)


def test_sales_offer_and_recurring_read_operations_use_expected_endpoints():
    session = Mock()
    session.post.return_value = _response()
    client = MeritAPI("id", "key", session=session)

    client.sales.get_offer("SO-1")
    _assert_last_request(session, "/v1/getsalesoffer")

    client.sales.get_recurring_invoice("RC-1")
    _assert_last_request(session, "/v1/getrecurringinvoice")

    client.sales.get_recurring_invoice_addresses(CustomerId=123)
    _assert_last_request(session, "/v1/getrecurringinvoiceaddresses")


def test_purchase_and_inventory_read_operations_use_expected_endpoints():
    session = Mock()
    session.post.return_value = _response()
    client = MeritAPI("id", "key", session=session)

    client.purchases.get_invoice("PI-1")
    _assert_last_request(session, "/v1/getpurchaseinvoice")

    client.purchases.get_orders(Status="Open")
    _assert_last_request(session, "/v1/getpurchaseorders")

    client.inventory.get_locations()
    _assert_last_request(session, "/v1/getlocations")


def test_financial_read_operations_use_expected_endpoints():
    session = Mock()
    session.post.return_value = _response()
    client = MeritAPI("id", "key", session=session)

    client.financial.get_payment_types()
    _assert_last_request(session, "/v1/getpaymenttypes")

    client.financial.get_payment_imports()
    _assert_last_request(session, "/v1/getpaymentimports")

    client.financial.get_expense_payments()
    _assert_last_request(session, "/v1/getexpensepayments")

    client.financial.get_income_payments()
    _assert_last_request(session, "/v1/getincomepayments")

    client.financial.get_gl_batch("GL-1")
    _assert_last_request(session, "/v1/getglbatch")

    client.financial.get_gl_batch_full_details("GL-1")
    _assert_last_request(session, "/v1/getglbatchfulldetails")


def test_assets_read_operations_use_expected_v2_endpoints():
    session = Mock()
    session.post.return_value = _response()
    client = MeritAPI("id", "key", session=session)

    client.assets.get_locations()
    _assert_last_request(session, "/v2/getfixedassetlocations")

    client.assets.get_responsible_employees()
    _assert_last_request(session, "/v2/getfixedassetresponsibleemployees")


def test_master_data_and_reports_read_operations_use_expected_endpoints():
    session = Mock()
    session.post.return_value = _response()
    client = MeritAPI("id", "key", session=session)

    client.master_data.get_customer_groups()
    _assert_last_request(session, "/v1/getcustomergroups")

    client.master_data.get_vendor_groups()
    _assert_last_request(session, "/v1/getvendorgroups")

    client.master_data.get_accounts()
    _assert_last_request(session, "/v1/getaccounts")

    client.master_data.get_departments()
    _assert_last_request(session, "/v1/getdepartments")

    client.master_data.get_financial_years()
    _assert_last_request(session, "/v1/getfinancialyears")

    client.master_data.get_units_of_measure()
    _assert_last_request(session, "/v1/getunitsofmeasure")

    client.reports.get_customer_debts()
    _assert_last_request(session, "/v1/getcustomerdebtsreport")

    client.reports.get_customer_payments()
    _assert_last_request(session, "/v1/getcustomerpaymentreport")

    client.reports.get_profit_or_loss()
    _assert_last_request(session, "/v1/getprofitandlossreport")

    client.reports.get_financial_position()
    _assert_last_request(session, "/v1/getfinancialpositionreport")

    client.reports.get_inventory_report()
    _assert_last_request(session, "/v1/getinventoryreport")

    client.reports.get_sales_report()
    _assert_last_request(session, "/v1/getsalesreport")

    client.reports.get_purchase_report()
    _assert_last_request(session, "/v1/getpurchasereport")
