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
        title="Create Unsent Accounting Invoice",
        description="Create an unsent accounting invoice (not an unposted draft); review before confirmation.",
    )
    def create_sales_invoice(invoice_summary: str = "Create a new sales invoice") -> str:
        return (
            f"{invoice_summary}\n"
            "1. Use merit_read_master_data with action='customers_list' to find the customer.\n"
            "2. If needed, call merit_write_customers with action='customer_upsert' to preview the customer create/update.\n"
            "3. After the user reviews that preview, call merit_write_customers_confirm with the same arguments, "
            "the returned confirmation_code, and confirmed=true.\n"
            "4. Confirm the company's InvoiceNo convention; read invoices_list for context, but do not "
            "assume the next integer is reserved or appropriate for every series.\n"
            "5. Read items_list to choose existing non-stock items and taxes_list for TaxId GUIDs. "
            "Do not create articles implicitly; missing or unknown items are refused.\n"
            "6. Build the restricted payload: Customer={Id}; DocDate, TransactionDate, DueDate as YYYYMMDD; "
            "InvoiceNo; CurrencyCode='EUR'; PriceInclVat=false; InvoiceRow; TaxAmount; TotalAmount. "
            "Each row has Item={Code, Description, UOMName}, Quantity>0, Price>=0, TaxId, Account. "
            "TotalAmount is the positive VAT-exclusive sum of per-row rounded amounts. "
            "No Payment, AccountingDoc, DelivNote, negative rows, discounts, or item-creation fields.\n"
            "7. Call merit_write_sales action='sales_invoice_create' for a non-writing preview.\n"
            "8. Warn the user: confirmation creates a real, unsent accounting invoice that can affect "
            "the ledger/reports BEFORE delivery. It is NOT an unposted draft; review before confirming.\n"
            "9. After review, call merit_write_sales_confirm with the same arguments, returned "
            "confirmation_code, and confirmed=true. Both calls are agent-accessible, not proof of human consent.\n"
            "10. Check the resulting invoice in Merit. Delivery is manual and not exposed by this server."

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
            "3. Otherwise construct a customer payload and call merit_write_customers with action='customer_upsert' "
            "to preview the write.\n"
            "4. After the user reviews the preview, call merit_write_customers_confirm with the same arguments, "
            "the returned confirmation_code, and confirmed=true.\n"
            "5. Confirm the resulting customer id before using it in downstream invoice flows."
        )
