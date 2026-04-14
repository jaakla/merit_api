from dataclasses import dataclass
from inspect import Parameter, Signature
from typing import Any, Callable, Literal, Sequence


ParamMode = Literal["filters", "payload", "items", "id", "id_with_attachment", "none"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    namespace: str
    method: str
    description: str
    param_mode: ParamMode
    mutating: bool = False

    @property
    def title(self) -> str:
        return self.name.replace("_", " ").title()

    @property
    def api_method(self) -> str:
        return f"{self.namespace}.{self.method}"

    @property
    def mcp_description(self) -> str:
        prefix = "Mutating tool." if self.mutating else "Read-only tool."
        return f"{prefix} {self.description}"


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec("customers_get_list", "customers", "get_list", "List customers with optional filters.", "filters"),
    ToolSpec("customers_send", "customers", "send", "Create or update a customer.", "payload", True),
    ToolSpec("vendors_get_list", "vendors", "get_list", "List vendors with optional filters.", "filters"),
    ToolSpec("vendors_send", "vendors", "send", "Create or update a vendor.", "payload", True),
    ToolSpec("items_get_list", "items", "get_list", "List items with optional filters.", "filters"),
    ToolSpec("items_add", "items", "add", "Add new items.", "items", True),
    ToolSpec("items_update", "items", "update", "Update an item.", "payload", True),
    ToolSpec("sales_get_invoices", "sales", "get_invoices", "List sales invoices for a date range or filters.", "filters"),
    ToolSpec("sales_get_invoice", "sales", "get_invoice", "Fetch one sales invoice by id.", "id_with_attachment"),
    ToolSpec("sales_send_invoice", "sales", "send_invoice", "Create a sales invoice.", "payload", True),
    ToolSpec("sales_delete_invoice", "sales", "delete_invoice", "Delete a sales invoice by id.", "id", True),
    ToolSpec("sales_send_credit_invoice", "sales", "send_credit_invoice", "Create a credit invoice.", "payload", True),
    ToolSpec("sales_get_offers", "sales", "get_offers", "List sales offers.", "filters"),
    ToolSpec("sales_get_recurring_invoices", "sales", "get_recurring_invoices", "List recurring invoices.", "filters"),
    ToolSpec("purchases_get_invoices", "purchases", "get_invoices", "List purchase invoices for a date range or filters.", "filters"),
    ToolSpec("purchases_send_invoice", "purchases", "send_invoice", "Create a purchase invoice.", "payload", True),
    ToolSpec("financial_get_payments", "financial", "get_payments", "List payments for a date range or filters.", "filters"),
    ToolSpec("financial_create_payment", "financial", "create_payment", "Create a payment.", "payload", True),
    ToolSpec("financial_get_gl_batches", "financial", "get_gl_batches", "List GL batches for a date range or filters.", "filters"),
    ToolSpec("financial_get_banks", "financial", "get_banks", "List banks.", "none"),
    ToolSpec("financial_get_costs", "financial", "get_costs", "List cost centers.", "none"),
    ToolSpec("financial_get_projects", "financial", "get_projects", "List projects.", "none"),
    ToolSpec("inventory_get_movements", "inventory", "get_movements", "List inventory movements.", "filters"),
    ToolSpec("assets_get_fixed_assets", "assets", "get_fixed_assets", "List fixed assets.", "filters"),
    ToolSpec("taxes_get_list", "taxes", "get_list", "List tax rates.", "none"),
    ToolSpec("taxes_send", "taxes", "send", "Create or update a tax rate.", "payload", True),
    ToolSpec("dimensions_get_list", "dimensions", "get_list", "List dimensions.", "none"),
    ToolSpec("dimensions_add", "dimensions", "add", "Add dimensions.", "items", True),
)


def get_tool_specs() -> Sequence[ToolSpec]:
    return TOOL_SPECS


def _build_signature(spec: ToolSpec) -> Signature:
    dict_type = dict[str, Any]
    list_type = list[dict[str, Any]]

    if spec.param_mode == "filters":
        parameters = [
            Parameter("filters", kind=Parameter.POSITIONAL_OR_KEYWORD, default=None, annotation=dict_type | None)
        ]
    elif spec.param_mode == "payload":
        parameters = [Parameter("payload", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=dict_type)]
    elif spec.param_mode == "items":
        parameters = [Parameter("items", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=list_type)]
    elif spec.param_mode == "id":
        parameters = [Parameter("id", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str)]
    elif spec.param_mode == "id_with_attachment":
        parameters = [
            Parameter("id", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=str),
            Parameter("add_attachment", kind=Parameter.POSITIONAL_OR_KEYWORD, default=False, annotation=bool),
        ]
    else:
        parameters = []

    return Signature(parameters=parameters, return_annotation=Any)


def _build_annotations(spec: ToolSpec) -> dict[str, Any]:
    annotations: dict[str, Any] = {"return": Any}
    if spec.param_mode == "filters":
        annotations["filters"] = dict[str, Any] | None
    elif spec.param_mode == "payload":
        annotations["payload"] = dict[str, Any]
    elif spec.param_mode == "items":
        annotations["items"] = list[dict[str, Any]]
    elif spec.param_mode == "id":
        annotations["id"] = str
    elif spec.param_mode == "id_with_attachment":
        annotations["id"] = str
        annotations["add_attachment"] = bool
    return annotations


def build_tool_handler(
    spec: ToolSpec,
    *,
    client_getter: Callable[[], Any],
    setup_payload_builder: Callable[..., dict],
) -> Callable[..., Any]:
    def handler(*args: Any, **kwargs: Any) -> Any:
        client = client_getter()
        if client is None:
            return setup_payload_builder(blocked_tool=spec.name, blocked_api_method=spec.api_method)

        namespace = getattr(client, spec.namespace)
        method = getattr(namespace, spec.method)

        if spec.param_mode == "filters":
            return method(**(kwargs.get("filters") or {}))
        if spec.param_mode == "payload":
            return method(kwargs["payload"])
        if spec.param_mode == "items":
            return method(kwargs["items"])
        if spec.param_mode == "id":
            return method(kwargs["id"])
        if spec.param_mode == "id_with_attachment":
            return method(kwargs["id"], add_attachment=kwargs.get("add_attachment", False))
        return method()

    handler.__name__ = spec.name
    handler.__doc__ = spec.mcp_description
    handler.__signature__ = _build_signature(spec)
    handler.__annotations__ = _build_annotations(spec)
    return handler


def tool_catalog_entry(spec: ToolSpec) -> dict:
    return {
        "name": spec.name,
        "title": spec.title,
        "namespace": spec.namespace,
        "method": spec.method,
        "api_method": spec.api_method,
        "description": spec.description,
        "mutating": spec.mutating,
        "read_only": not spec.mutating,
        "param_mode": spec.param_mode,
    }
