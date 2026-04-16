from fastmcp import FastMCP

from .config import build_setup_payload


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="setup-merit-api",
        title="Setup Merit API",
        description="Explain how to configure Merit API credentials for the MCP server.",
    )
    def setup_merit_api() -> str:
        payload = build_setup_payload()
        return (
            "Configure the Merit API MCP server before using API-backed tools.\n"
            f"Required environment variables: {', '.join(payload['supported_env_vars'][:2])}.\n"
            "Optional environment variable: MERIT_API_COUNTRY (EE or PL, defaults to EE).\n"
            "Once configured, restart the MCP client or reload the server."
        )

    @mcp.prompt(
        name="create-sales-invoice",
        title="Create Sales Invoice",
        description="Guide an assistant through creating a sales invoice with Merit API tools.",
    )
    def create_sales_invoice(invoice_summary: str = "Create a new sales invoice") -> str:
        return (
            f"{invoice_summary}\n"
            "1. Use merit_read_master_data with action='customers_list' to find the customer.\n"
            "2. If needed, use merit_write_customers with action='customer_upsert' to create or update the customer.\n"
            "3. Build the invoice payload.\n"
            "4. Use merit_write_sales with action='sales_invoice_create' to create the invoice.\n"
            "5. Validate the returned invoice identifiers and totals."
        )

    @mcp.prompt(
        name="find-or-create-customer",
        title="Find Or Create Customer",
        description="Guide an assistant through finding or creating a customer.",
    )
    def find_or_create_customer(customer_name: str) -> str:
        return (
            f"Find or create the customer named {customer_name!r}.\n"
            "1. Search with merit_read_master_data using action='customers_list' and a Name filter.\n"
            "2. If a confident match exists, use that record.\n"
            "3. Otherwise construct a customer payload and call merit_write_customers with action='customer_upsert'.\n"
            "4. Confirm the resulting customer id before using it in downstream invoice flows."
        )
