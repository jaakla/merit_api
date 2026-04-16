from dataclasses import dataclass
from inspect import Parameter, Signature
from typing import Any, Callable, Literal, Sequence


PayloadKind = Literal["dict", "list"]
Invoker = Callable[[Any, dict[str, Any]], Any]


@dataclass(frozen=True)
class ActionSpec:
    name: str
    description: str
    api_method: str
    invoke: Invoker
    required_fields: tuple[str, ...] = ()
    payload_kind: PayloadKind | None = None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    mutating: bool
    actions: tuple[ActionSpec, ...]

    @property
    def title(self) -> str:
        return self.name.replace("_", " ").title()

    @property
    def mcp_description(self) -> str:
        prefix = "Mutating tool." if self.mutating else "Read-only tool."
        return f"{prefix} {self.description}"


def _filters_action(name: str, description: str, api_method: str, getter: Callable[[Any], Callable[..., Any]]) -> ActionSpec:
    return ActionSpec(
        name=name,
        description=description,
        api_method=api_method,
        invoke=lambda client, args: getter(client)(**(args["filters"] or {})),
    )


def _none_action(name: str, description: str, api_method: str, getter: Callable[[Any], Callable[..., Any]]) -> ActionSpec:
    return ActionSpec(
        name=name,
        description=description,
        api_method=api_method,
        invoke=lambda client, _args: getter(client)(),
    )


def _id_action(name: str, description: str, api_method: str, getter: Callable[[Any], Callable[..., Any]]) -> ActionSpec:
    return ActionSpec(
        name=name,
        description=description,
        api_method=api_method,
        invoke=lambda client, args: getter(client)(args["id"]),
        required_fields=("id",),
    )


def _payload_action(
    name: str,
    description: str,
    api_method: str,
    getter: Callable[[Any], Callable[..., Any]],
    *,
    payload_kind: PayloadKind,
) -> ActionSpec:
    return ActionSpec(
        name=name,
        description=description,
        api_method=api_method,
        invoke=lambda client, args: getter(client)(args["payload"]),
        required_fields=("payload",),
        payload_kind=payload_kind,
    )


def _validation_error(
    *,
    tool_name: str,
    action: str | None,
    allowed_actions: Sequence[str],
    missing_fields: Sequence[str] = (),
    payload_kind: PayloadKind | None = None,
) -> dict[str, Any]:
    error = {
        "error": "ValidationError",
        "tool": tool_name,
        "action": action,
        "allowed_actions": list(allowed_actions),
    }
    if missing_fields:
        error["message"] = f"Missing required fields for action {action!r}."
        error["missing_fields"] = list(missing_fields)
    elif payload_kind is not None:
        error["message"] = f"Action {action!r} requires payload to be a {payload_kind}."
        error["payload_kind"] = payload_kind
    else:
        error["message"] = f"Unsupported action {action!r}."
    return error


def _action_map(spec: ToolSpec) -> dict[str, ActionSpec]:
    return {action.name: action for action in spec.actions}


def _read_master_data_actions() -> tuple[ActionSpec, ...]:
    return (
        _filters_action("customers_list", "List customers with optional filters.", "customers.get_list", lambda c: c.customers.get_list),
        _filters_action("customer_groups_list", "List customer groups.", "customers.get_groups", lambda c: c.customers.get_groups),
        _filters_action("vendors_list", "List vendors with optional filters.", "vendors.get_list", lambda c: c.vendors.get_list),
        _filters_action("vendor_groups_list", "List vendor groups.", "vendors.get_groups", lambda c: c.vendors.get_groups),
        _filters_action("items_list", "List items with optional filters.", "items.get_list", lambda c: c.items.get_list),
        _filters_action("item_groups_list", "List item groups.", "items.get_groups", lambda c: c.items.get_groups),
        _none_action("taxes_list", "List tax rates.", "taxes.get_list", lambda c: c.taxes.get_list),
        ActionSpec(
            name="dimensions_list",
            description="List dimensions.",
            api_method="dimensions.get_list",
            invoke=lambda client, args: client.dimensions.get_list(all_values=bool((args["filters"] or {}).get("AllValues", False))),
        ),
        _none_action("banks_list", "List banks.", "financial.get_banks", lambda c: c.financial.get_banks),
        _filters_action("accounts_list", "List accounts.", "financial.get_accounts", lambda c: c.financial.get_accounts),
        _none_action("projects_list", "List projects.", "financial.get_projects", lambda c: c.financial.get_projects),
        _none_action("cost_centers_list", "List cost centers.", "financial.get_costs", lambda c: c.financial.get_costs),
        _filters_action("departments_list", "List departments.", "financial.get_departments", lambda c: c.financial.get_departments),
        _filters_action("units_list", "List units of measure.", "reference.get_units", lambda c: c.reference.get_units),
        _filters_action("financial_years_list", "List financial years.", "financial.get_financial_years", lambda c: c.financial.get_financial_years),
    )


def _read_sales_actions() -> tuple[ActionSpec, ...]:
    return (
        _filters_action("invoices_list", "List sales invoices.", "sales.get_invoices", lambda c: c.sales.get_invoices),
        ActionSpec(
            name="invoice_get",
            description="Fetch one sales invoice by id.",
            api_method="sales.get_invoice",
            invoke=lambda client, args: client.sales.get_invoice(args["id"], add_attachment=args["add_attachment"]),
            required_fields=("id",),
        ),
        _id_action("invoice_pdf_get", "Fetch one sales invoice PDF by id.", "sales.get_invoice_pdf", lambda c: c.sales.get_invoice_pdf),
        _filters_action("offers_list", "List sales offers.", "sales.get_offers", lambda c: c.sales.get_offers),
        _id_action("offer_get", "Fetch one sales offer by id.", "sales.get_offer", lambda c: c.sales.get_offer),
        _filters_action(
            "recurring_invoices_list",
            "List recurring invoices.",
            "sales.get_recurring_invoices",
            lambda c: c.sales.get_recurring_invoices,
        ),
        _id_action(
            "recurring_invoice_get",
            "Fetch one recurring invoice by id.",
            "sales.get_recurring_invoice",
            lambda c: c.sales.get_recurring_invoice,
        ),
        _filters_action(
            "recurring_invoice_addresses_list",
            "List recurring invoice addresses.",
            "sales.get_recurring_invoice_addresses",
            lambda c: c.sales.get_recurring_invoice_addresses,
        ),
    )


def _read_purchase_actions() -> tuple[ActionSpec, ...]:
    return (
        _filters_action("invoices_list", "List purchase invoices.", "purchases.get_invoices", lambda c: c.purchases.get_invoices),
        _id_action("invoice_get", "Fetch one purchase invoice by id.", "purchases.get_invoice", lambda c: c.purchases.get_invoice),
        _filters_action("orders_list", "List purchase orders.", "purchases.get_orders", lambda c: c.purchases.get_orders),
    )


def _read_financial_actions() -> tuple[ActionSpec, ...]:
    return (
        _filters_action("payments_list", "List payments.", "financial.get_payments", lambda c: c.financial.get_payments),
        _filters_action(
            "payment_types_list",
            "List payment types.",
            "financial.get_payment_types",
            lambda c: c.financial.get_payment_types,
        ),
        ActionSpec(
            name="payment_imports_list",
            description="List payment imports for a bank.",
            api_method="financial.get_payment_imports",
            invoke=lambda client, args: client.financial.get_payment_imports(bankId=args["bank_id"], **(args["filters"] or {})),
            required_fields=("bank_id", "filters"),
        ),
        ActionSpec(
            name="expense_payments_list",
            description="List expense payments for a bank.",
            api_method="financial.get_expense_payments",
            invoke=lambda client, args: client.financial.get_expense_payments(args["bank_id"], **(args["filters"] or {})),
            required_fields=("bank_id", "filters"),
        ),
        ActionSpec(
            name="income_payments_list",
            description="List income payments for a bank.",
            api_method="financial.get_income_payments",
            invoke=lambda client, args: client.financial.get_income_payments(args["bank_id"], **(args["filters"] or {})),
            required_fields=("bank_id", "filters"),
        ),
        _filters_action("gl_batches_list", "List GL batches.", "financial.get_gl_batches", lambda c: c.financial.get_gl_batches),
        _id_action("gl_batch_get", "Fetch one GL batch by id.", "financial.get_gl_batch", lambda c: c.financial.get_gl_batch),
        _filters_action(
            "gl_batches_full_list",
            "List GL batches with full details.",
            "financial.get_gl_batches_full",
            lambda c: c.financial.get_gl_batches_full,
        ),
    )


def _read_inventory_actions() -> tuple[ActionSpec, ...]:
    return (
        _filters_action("locations_list", "List inventory locations.", "inventory.get_locations", lambda c: c.inventory.get_locations),
        _filters_action("movements_list", "List inventory movements.", "inventory.get_movements", lambda c: c.inventory.get_movements),
        _filters_action(
            "fixed_asset_locations_list",
            "List fixed asset locations.",
            "assets.get_locations",
            lambda c: c.assets.get_locations,
        ),
        _filters_action(
            "fixed_asset_responsible_persons_list",
            "List fixed asset responsible persons.",
            "assets.get_responsible_persons",
            lambda c: c.assets.get_responsible_persons,
        ),
        _filters_action("fixed_assets_list", "List fixed assets.", "assets.get_fixed_assets", lambda c: c.assets.get_fixed_assets),
        _filters_action("prices_list", "List prices.", "pricing.get_prices", lambda c: c.pricing.get_prices),
        _filters_action("discounts_list", "List discounts.", "pricing.get_discounts", lambda c: c.pricing.get_discounts),
        ActionSpec(
            name="price_get",
            description="Fetch an effective price.",
            api_method="pricing.get_price",
            invoke=lambda client, args: client.pricing.get_price(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
    )


def _read_report_actions() -> tuple[ActionSpec, ...]:
    return (
        ActionSpec(
            name="customer_debts_get",
            description="Get customer debts report.",
            api_method="reports.get_customer_debts",
            invoke=lambda client, args: client.reports.get_customer_debts(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
        ActionSpec(
            name="customer_payments_get",
            description="Get customer payment report.",
            api_method="reports.get_customer_payments",
            invoke=lambda client, args: client.reports.get_customer_payments(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
        ActionSpec(
            name="more_data_get",
            description="Get continuation page for a report.",
            api_method="reports.get_more_data",
            invoke=lambda client, args: client.reports.get_more_data(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
        ActionSpec(
            name="profit_report_get",
            description="Get statement of profit or loss.",
            api_method="reports.get_profit",
            invoke=lambda client, args: client.reports.get_profit(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
        ActionSpec(
            name="balance_report_get",
            description="Get statement of financial position.",
            api_method="reports.get_balance",
            invoke=lambda client, args: client.reports.get_balance(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
        ActionSpec(
            name="inventory_report_get",
            description="Get inventory report.",
            api_method="reports.get_inventory",
            invoke=lambda client, args: client.reports.get_inventory(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
        ActionSpec(
            name="sales_report_get",
            description="Get sales report.",
            api_method="reports.get_sales",
            invoke=lambda client, args: client.reports.get_sales(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
        ActionSpec(
            name="purchase_report_get",
            description="Get purchase report.",
            api_method="reports.get_purchases",
            invoke=lambda client, args: client.reports.get_purchases(**(args["filters"] or {})),
            required_fields=("filters",),
        ),
    )


def _write_customer_actions() -> tuple[ActionSpec, ...]:
    return (
        _payload_action("customer_upsert", "Create or update a customer.", "customers.send", lambda c: c.customers.send, payload_kind="dict"),
        _payload_action("vendor_upsert", "Create or update a vendor.", "vendors.send", lambda c: c.vendors.send, payload_kind="dict"),
    )


def _write_sales_actions() -> tuple[ActionSpec, ...]:
    return (
        _payload_action("sales_invoice_create", "Create a sales invoice.", "sales.send_invoice", lambda c: c.sales.send_invoice, payload_kind="dict"),
        _id_action("sales_invoice_delete", "Delete a sales invoice by id.", "sales.delete_invoice", lambda c: c.sales.delete_invoice),
        _payload_action(
            "credit_invoice_create",
            "Create a credit invoice.",
            "sales.send_credit_invoice",
            lambda c: c.sales.send_credit_invoice,
            payload_kind="dict",
        ),
        ActionSpec(
            name="sales_invoice_send_email",
            description="Send a sales invoice by email.",
            api_method="sales.send_invoice_by_email",
            invoke=lambda client, args: client.sales.send_invoice_by_email(args["id"], delivnote=args["delivnote"]),
            required_fields=("id",),
        ),
        ActionSpec(
            name="sales_invoice_send_einvoice",
            description="Send a sales invoice as e-invoice.",
            api_method="sales.send_invoice_by_einvoice",
            invoke=lambda client, args: client.sales.send_invoice_by_einvoice(args["id"], delivnote=args["delivnote"]),
            required_fields=("id",),
        ),
    )


def _write_purchase_actions() -> tuple[ActionSpec, ...]:
    return (
        _payload_action(
            "purchase_invoice_create",
            "Create a purchase invoice.",
            "purchases.send_invoice",
            lambda c: c.purchases.send_invoice,
            payload_kind="dict",
        ),
    )


def _write_financial_actions() -> tuple[ActionSpec, ...]:
    return (
        _payload_action(
            "purchase_invoice_payment_create",
            "Create a purchase invoice payment.",
            "financial.create_payment",
            lambda c: c.financial.create_payment,
            payload_kind="dict",
        ),
        _payload_action("tax_upsert", "Create or update a tax rate.", "taxes.send", lambda c: c.taxes.send, payload_kind="dict"),
        _payload_action("dimensions_add", "Add dimensions.", "dimensions.add", lambda c: c.dimensions.add, payload_kind="list"),
        _payload_action("items_add", "Add items.", "items.add", lambda c: c.items.add, payload_kind="list"),
        _payload_action("item_update", "Update an item.", "items.update", lambda c: c.items.update, payload_kind="dict"),
    )


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec("merit_read_master_data", "Read common master and reference data from Merit.", False, _read_master_data_actions()),
    ToolSpec("merit_read_sales", "Read sales invoices, offers, and recurring invoice data.", False, _read_sales_actions()),
    ToolSpec("merit_read_purchases", "Read purchase invoices and purchase orders.", False, _read_purchase_actions()),
    ToolSpec("merit_read_financial", "Read payments, banks, and GL information.", False, _read_financial_actions()),
    ToolSpec("merit_read_inventory", "Read inventory, fixed asset, and pricing data.", False, _read_inventory_actions()),
    ToolSpec("merit_read_reports", "Read Merit reports and report continuations.", False, _read_report_actions()),
    ToolSpec("merit_write_customers", "Create or update customers and vendors.", True, _write_customer_actions()),
    ToolSpec("merit_write_sales", "Create, delete, and deliver sales invoices.", True, _write_sales_actions()),
    ToolSpec("merit_write_purchases", "Create purchase invoices.", True, _write_purchase_actions()),
    ToolSpec("merit_write_financial", "Create purchase payments and update related financial master data.", True, _write_financial_actions()),
)


def get_tool_specs() -> Sequence[ToolSpec]:
    return TOOL_SPECS


def _build_signature(_spec: ToolSpec) -> Signature:
    dict_type = dict[str, Any]
    payload_type = dict[str, Any] | list[dict[str, Any]]
    parameters = [
        Parameter("action", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
        Parameter("id", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None, annotation=str | None),
        Parameter("filters", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None, annotation=dict_type | None),
        Parameter("payload", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None, annotation=payload_type | None),
        Parameter("add_attachment", kind=Parameter.POSITIONAL_OR_KEYWORD, default=False, annotation=bool),
        Parameter("delivnote", kind=Parameter.POSITIONAL_OR_KEYWORD, default=False, annotation=bool),
        Parameter("bank_id", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None, annotation=str | None),
    ]
    return Signature(parameters=parameters, return_annotation=Any)


def _build_annotations(_spec: ToolSpec) -> dict[str, Any]:
    return {
        "return": Any,
        "action": str,
        "id": str | None,
        "filters": dict[str, Any] | None,
        "payload": dict[str, Any] | list[dict[str, Any]] | None,
        "add_attachment": bool,
        "delivnote": bool,
        "bank_id": str | None,
    }


def build_tool_handler(
    spec: ToolSpec,
    *,
    client_getter: Callable[[], Any],
    setup_payload_builder: Callable[..., dict],
) -> Callable[..., Any]:
    actions = _action_map(spec)
    allowed_actions = tuple(actions)

    def handler(
        action: str,
        id: str | None = None,
        filters: dict[str, Any] | None = None,
        payload: dict[str, Any] | list[dict[str, Any]] | None = None,
        add_attachment: bool = False,
        delivnote: bool = False,
        bank_id: str | None = None,
    ) -> Any:
        args = {
            "action": action,
            "id": id,
            "filters": filters,
            "payload": payload,
            "add_attachment": add_attachment,
            "delivnote": delivnote,
            "bank_id": bank_id,
        }
        selected = actions.get(action)

        client = client_getter()
        if client is None:
            return setup_payload_builder(
                blocked_tool=spec.name,
                blocked_api_method=selected.api_method if selected is not None else None,
            )

        if selected is None:
            return _validation_error(tool_name=spec.name, action=action, allowed_actions=allowed_actions)

        missing_fields = tuple(
            field_name for field_name in selected.required_fields if args[field_name] in (None, "", [])
        )
        if missing_fields:
            return _validation_error(
                tool_name=spec.name,
                action=action,
                allowed_actions=allowed_actions,
                missing_fields=missing_fields,
            )

        if selected.payload_kind == "dict" and not isinstance(payload, dict):
            return _validation_error(
                tool_name=spec.name,
                action=action,
                allowed_actions=allowed_actions,
                payload_kind="dict",
            )
        if selected.payload_kind == "list" and not isinstance(payload, list):
            return _validation_error(
                tool_name=spec.name,
                action=action,
                allowed_actions=allowed_actions,
                payload_kind="list",
            )

        return selected.invoke(client, args)

    handler.__name__ = spec.name
    handler.__doc__ = spec.mcp_description
    handler.__signature__ = _build_signature(spec)
    handler.__annotations__ = _build_annotations(spec)
    return handler


def action_catalog_entry(action: ActionSpec) -> dict[str, Any]:
    return {
        "name": action.name,
        "description": action.description,
        "api_method": action.api_method,
        "required_fields": list(action.required_fields),
        "payload_kind": action.payload_kind,
    }


def tool_catalog_entry(spec: ToolSpec) -> dict[str, Any]:
    return {
        "name": spec.name,
        "title": spec.title,
        "description": spec.description,
        "mutating": spec.mutating,
        "read_only": not spec.mutating,
        "when_to_use": spec.description,
        "actions": [action_catalog_entry(action) for action in spec.actions],
    }
