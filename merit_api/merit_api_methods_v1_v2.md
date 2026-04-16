# Merit API meetodid (v1 / v2)

Allikas: https://api.merit.ee/connecting-robots/reference-manual/

| Meetod | v1 URL | v2 URL | Tüüp | Dokumentatsioon |
|---|---|---|---|---|
| Get list of sales invoces | `/api/v1/getinvoices` | `/api/v2/getinvoices`<br>`/api/v2/getinvoices2` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/get-list-of-invoices/ |
| Get sales invoice details | `/api/v1/getinvoice` | `/api/v2/getinvoice` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/get-invoice-details/ |
| Delete Invoice | `/api/v1/deleteinvoice` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/delete-invoice/ |
| Create Sales Invoice | `/api/v1/sendinvoice` | `/api/v2/sendinvoice` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/create-sales-invoice/ |
| Create Sales Invoice with multiple payments | `/api/v1/sendinvoice2` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/create-sales-invoice/create-sales-invoice-with-multiple-payments/ |
| Create Sales Invoice of Estonian e-invoice standard 1.2 |  | `/api/v2/sendinvoicexml` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/create-sales-invoice/create-sales-invoice-of-estonian-e-invoice-standard-1-2/ |
| Send Sales Invoice by e-mail |  | `/api/v2/sendinvoicebyemail` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/create-sales-invoice/send-invoice-by-e-mail/ |
| Send Sales Invoice as e-invoice |  | `/api/v2/sendinvoiceaseinv` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/create-sales-invoice/send-sales-invoice-by-einvoice/ |
| Get Sales Invoice PDF |  | `/api/v2/getsalesinvpdf` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/create-sales-invoice/get-sales-invoice-pdf/ |
| Create Credit Invoice | `/api/v1/sendinvoice` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-invoices/create-credit-invoice/ |
| Get List of Sales Offers |  | `/api/v2/getoffers` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/sales-offers/get-list-of-sales-offers/ |
| Create Sales Offer | `/api/v1/sendoffer` | `/api/v2/sendoffer` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-offers/create-sales-offer/ |
| Set Offer status |  | `/api/v2/setofferstatus` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-offers/set-offer-status/ |
| Create Invoice from SalesOffer |  | `/api/v2/offer2inv` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-offers/create-invoice-from-salesoffer/ |
| Get sales offer details |  | `/api/v2/getoffer` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/sales-offers/get-sales-offer-details/ |
| Update sales offer |  | `/api/v2/updateoffer` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-offers/update-sales-offer/ |
| Create Recurring Invoice |  | `/api/v2/sendperinvoice` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/recurring-invoices/create-recurring-invoice/ |
| Get Recurring Invoices clients address list |  | `/api/v2/getpershaddress` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/recurring-invoices/get-recurring-invoices-clients-address-list/ |
| Send Indication Values | `/api/v1/sendindvalues` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/recurring-invoices/send-indication-values/ |
| Get list of Recurring Invoices |  | `/api/v2/getperinvoices` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/recurring-invoices/get-list-of-recurring-invoices/ |
| Get Recurring Invoice details |  | `/api/v2/getperinvoice` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/recurring-invoices/get-recurring-invoice-details/ |
| Get list of purchase invoices | `/api/v1/getpurchorders` | `/api/v2/getpurchorders` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/purchase-invoices/get-list-of-purchase-invoices/ |
| Get purchase invoice details | `/api/v1/getpurchorder` | `/api/v2/getpurchorder` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/purchase-invoices/get-purchase-invoice-details/ |
| Delete Purchase Invoice | `/api/v1/deletepurchinvoice` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/purchase-invoices/delete-purchase-invoice/ |
| Create Purchase Invoice | `/api/v1/sendpurchinvoice` | `/api/v2/sendpurchinvoice` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/purchase-invoices/create-purchase-invoice/ |
| Create Purchase Invoice Waiting Approval | `/api/v1/sendpurchorder` | `/api/v2/sendpurchorder` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/purchase-invoices/create-purchase-order/ |
| Create Purchase Invoice Waiting Approval of Estonian e-invoice standard 1.2 |  | `/api/v2/sendpurchorderxml` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/purchase-invoices/create-purchase-invoice-waiting-approval-of-estonian-e-invoice-standard-1-2/ |
| Get list of Purchase Orders |  | `/api/v2/GetPOrders` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/purchase-invoices/get-list-of-purchase-orders/ |
| Get list of locations |  | `/api/v2/getlocations` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/inventory-movements1/get-list-of-locations/ |
| Send Invenroty Movements | `/api/v1/SendInvMovement` | `/api/v2/SendInvMovement` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/inventory-movements1/send-invenroty-movements/ |
| Get List of Inventory Movements |  | `/api/v2/getinvmovements` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/inventory-movements1/get-list-of-inventory-movements/ |
| List of Payments | `/api/v1/getpayments` | `/api/v2/getpayments` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/payments/list-of-payments/ |
| List of Payment Types |  | `/api/v2/getpaymenttypes` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/payments/list-of-payment-types/ |
| Create Payment of sales invoice | `/api/v1/sendpayment` | `/api/v2/sendpayment` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/create-payment/ |
| Create Payment of purchase invoice | `/api/v1/sendPaymentV` | `/api/v2/sendPaymentV` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/payment-of-purchase-invoice/ |
| Create Payment of sales offer | `/api/v1/sendPaymentO` | `/api/v2/sendPaymentO` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/create-payment-of-sales-offer/ |
| Delete Payment | `/api/v1/deletepayment` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/delete-payment/ |
| Bank statement import |  | `/api/v2/sendcamt53` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/bank-statement-import/ |
| Send Settlement |  | `/api/v2/sendsettlement` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/send-settlement/ |
| Get Payment Imports |  | `/api/v2/PaymentImports` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/payments/get-payment-imports/ |
| List of ExpensePayments |  | `/api/v2/Banks/{bankId}/ExpensePayments` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/payments/list-of-expensepayments/ |
| Send ExpensePayments |  | `/api/v2/Banks/{bankId}/ExpensePayments` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/send-expensepayments/ |
| List of IncomePayments |  | `/api/v2/Banks/{bankId}/IncomePayments` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/payments/list-of-incomepayments/ |
| Send IncomePayments |  | `/api/v2/Banks/{bankId}/IncomePayments` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/send-incomepayments/ |
| Send PrePayments |  | `/api/v2/Banks/{bankId}/PrePayments`<br>`/api/v2/Banks/{bankId}/PrePayments/ForCustomer/{customerId}`<br>`/api/v2/Banks/{bankId}/PrePayments/ForVendor/{vendorId}` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/payments/send-prepayments/ |
| Creating General Ledger Transactions | `/api/v1/sendglbatch` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/general-ledger-transactions/creating-general-ledger-transactions/ |
| Get list of GL Transactions | `/api/v1/getglbatches` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/general-ledger-transactions/get-list-of-gl-transactions/ |
| Getting GL Transaction Details | `/api/v1/getglbatch` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/general-ledger-transactions/getting-gl-transaction-details/ |
| Getting GL Transactions Full Details | `/api/v1/GetGLBatchesFull` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/general-ledger-transactions/getting-gl-transactions-full-details/ |
| List Fixed asset locations |  | `/api/v2/getfalocations` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/fixed-asset/list-fixed-asset-locations/ |
| Responsible employee list |  | `/api/v2/getfaresppersons` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/fixed-asset/responsible-employee-list/ |
| Send Fixed assets |  | `/api/v2/sendfixedassets` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/fixed-asset/send-fixed-assets/ |
| Get Fixed assets |  | `/api/v2/getfixassets` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/fixed-asset/get-fixed-assets/ |
| Tax list | `/api/v1/gettaxes` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/tax-list/ |
| Send Tax |  | `/api/v2/sendtax` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/send-tax/ |
| Get Customer List | `/api/v1/getcustomers` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/customers/get-customer-list/ |
| Create Customer |  | `/api/v2/sendcustomer` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/customers/create-customer/ |
| Update Customer | `/api/v1/updatecustomer` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/customers/update-customer/ |
| Create Customergroup |  | `/api/v2/sendcustomergroup` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/customers/create-customergroup/ |
| Get Customergroups |  | `/api/v2/getcustomergroups` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/customers/get-customergroups/ |
| Get Vendor List | `/api/v1/getvendors` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/vendors/get-vendor-list/ |
| Create Vendor |  | `/api/v2/sendvendor` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/vendors/create-vendor/ |
| Update Vendor | `/api/v1/updatevendor` | `/api/v2/updatevendor` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/vendors/update-vendor/ |
| Create Vendorgroup |  | `/api/v2/sendvendorgroup` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/vendors/create-vendorgroup/ |
| Get Vendorgroup List |  | `/api/v2/getvendorgroups`<br>`/api/v2/getvendorlist` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/vendors/get-vendorgroup-list/ |
| Accounts List | `/api/v1/getaccounts` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/accounts-list/ |
| Project List | `/api/v1/getprojects` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/project-list/ |
| Cost Centers List | `/api/v1/getcostcenters` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/cost-centers-list/ |
| Get Dimensions List |  | `/api/v2/getdimensions` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/dimensions/dimensionslist/ |
| Add Dimensions |  | `/api/v2/senddimensions` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/dimensions/add-dimensions/ |
| Add Dimensions Values |  | `/api/v2/senddimvalues` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/dimensions/add-dimensions-values/ |
| Departments List | `/api/v1/getdepartments` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/departments-list/ |
| Send prices |  | `/api/v2/sendprices` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-prices-and-discounts/send-prices/ |
| Send discounts |  | `/api/v2/senddiscounts` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/sales-prices-and-discounts/send-discounts/ |
| Get prices |  | `/api/v2/getprices` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/sales-prices-and-discounts/get-prices/ |
| Get discounts |  | `/api/v2/getdiscounts` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/sales-prices-and-discounts/get-discounts/ |
| Get Price |  | `/api/v2/getprice` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/sales-prices-and-discounts/get-price/ |
| Units of Measure List | `/api/v1/getunits` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/units-of-measure/units-of-measure-list/ |
| Send units of measure |  | `/api/v2/senduom` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/units-of-measure/send-units-of-measure/ |
| Banks List | `/api/v1/getbanks` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/banks-list/ |
| Financial Years |  | `/api/v2/getaccperiods` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/financial-years/ |
| Items List | `/api/v1/getitems` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/items/items-list/ |
| Item Groups |  | `/api/v2/getitemgroups` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/items/get-item-groups/ |
| Add Items |  | `/api/v2/senditems` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/items/add-items/ |
| Add Item groups |  | `/api/v2/senditemgroups` | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/items/add-item-groups/ |
| Update Item | `/api/v1/updateitem` |  | kirjutamine | https://api.merit.ee/connecting-robots/reference-manual/items/update-item/ |
| Customer Debts Report | `/api/v1/getcustdebtrep` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/reports/customer-debts-report/ |
| Customer Payment Report |  | `/api/v2/getcustpaymrep`<br>`/api/v2/getmoredata` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/reports/customer-payment-report/ |
| Statement of Profit or Loss | `/api/v1/getprofitrep` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/reports/income-statement/ |
| Statement of Financial Position | `/api/v1/getbalancerep` |  | lugemine | https://api.merit.ee/connecting-robots/reference-manual/reports/balance-sheet/ |
| Get Inventory Report |  | `/api/v2/getinventoryreport` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/reports/get-inventory-report/ |
| Sales Report |  | `/api/v2/getsalesrep` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/reports/sales-report/ |
| Purchase Report |  | `/api/v2/getpurchrep` | lugemine | https://api.merit.ee/connecting-robots/reference-manual/reports/purchase-report/ |

## Python API rakenduse seis

Allolev staatus on kontrollitud failide `merit_api/src/merit_api/namespaces.py` ja `merit_api/tests/*.py` põhjal.

Legend:

- `Unit` = mockitud/lokaalsed pytest-testid
- `Integration` = päris Merit API vastu jooksvad testid, mis vajavad `MERIT_API_INTEGRATION_TEST=true` ja API võtmeid
- `raw _post` = endpointi kasutatakse testis otse `client._post(...)` kaudu, kuid public wrapper puudub

- `✅ Integration` tähendab, et meetod on kaasatud `test_integration_read.py` või vastavasse eraldi integratsioonitesti; konkreetse konto korral võib test siiski andmete või mooduli puudumisel `skip`-i minna.

Kokku on Pythoni kliendis praegu wrapper olemas **62** siin tabelis dokumenteeritud operatsioonile.

- Kõik dokumenteeritud lugemise/get/list/report meetodid on nüüd wrapperiga kaetud: **49/49**
- Unit-kattega wrapperid: **53/62**
- Integration-kattega wrapperid: **52/62**
- Ilma ühegi testita wrapperid: `customers.send`, `vendors.send`, `items.add`, `items.update`, `sales.delete_invoice`, `financial.create_payment`, `taxes.send`, `dimensions.add`
- Kontrollitud lokaalselt: `python3 -m pytest merit_api/tests -q` -> `70 passed, 55 skipped`
- Kontrollitud päris API vastu 2026-04-16: `MERIT_API_INTEGRATION_TEST=true python3 -m pytest merit_api/tests/test_integration_read.py -q -rs` -> `44 passed, 5 skipped`

### Implemented Read Wrappers

| Namespace | Wrapperid | Unit | Integration | Märkused |
|---|---|---|---|---|
| `customers` | `get_list()`, `get_groups()` | ✅ `test_read_methods.py` | ✅ `test_integration_read.py` | Katab `getcustomers`, `getcustomergroups`. |
| `vendors` | `get_list()`, `get_groups()` | ✅ | ✅ | Katab `getvendors`, `getvendorgroups`. |
| `items` | `get_list()`, `get_groups()` | ✅ | ✅ | Katab `getitems`, `getitemgroups`. |
| `sales` | `get_invoices()`, `get_invoice()`, `get_invoice_pdf()`, `get_offers()`, `get_offer()`, `get_recurring_invoices()`, `get_recurring_invoice()`, `get_recurring_invoice_addresses()` | ✅ | ✅ | Katab kõik dokumenteeritud sales-read meetodid. `get_invoice()` kasutab praegu `v1/getinvoice`; `get_invoice_pdf()` kasutab `_get_pdf(...)`. |
| `purchases` | `get_invoices()`, `get_invoice()`, `get_orders()` | ✅ | ✅ | Katab `getpurchorders`, `getpurchorder`, `GetPOrders`. |
| `financial` | `get_payments()`, `get_payment_types()`, `get_payment_imports()`, `get_expense_payments()`, `get_income_payments()`, `get_gl_batches()`, `get_gl_batch()`, `get_gl_batches_full()`, `get_banks()`, `get_accounts()`, `get_costs()`, `get_projects()`, `get_departments()`, `get_financial_years()` | ✅ | ✅ | `get_payment_imports()`, `get_expense_payments()` ja `get_income_payments()` kasutavad query-string GET transporti (`client._get(...)`), sest live API käitus nii korrektselt. |
| `inventory` | `get_locations()`, `get_movements()` | ✅ | ✅ | Katab `getlocations`, `getinvmovements`. |
| `assets` | `get_locations()`, `get_responsible_persons()`, `get_fixed_assets()` | ✅ | ✅ | Katab `getfalocations`, `getfaresppersons`, `getfixassets`. |
| `taxes` | `get_list()` | ✅ | ✅ | Katab `gettaxes`. |
| `dimensions` | `get_list()` | ✅ | ✅ | Katab `getdimensions`. |
| `pricing` | `get_prices()`, `get_discounts()`, `get_price()` | ✅ | ✅ | Katab `getprices`, `getdiscounts`, `getprice`; `get_price()` vajab live API-s `DocDate`. |
| `reports` | `get_customer_debts()`, `get_customer_payments()`, `get_more_data()`, `get_profit()`, `get_balance()`, `get_inventory()`, `get_sales()`, `get_purchases()` | ✅ | ✅ | Katab kõik dokumenteeritud report-read meetodid; live API nõuab mitmel juhul teistsugust payloadi kui lihtne `PeriodStart/PeriodEnd`. |
| `reference` | `get_units()` | ✅ | ✅ | Katab `getunits`. |

### Existing Write Wrappers

| Dokumenteeritud meetod | Python API | Unit | Integration | Märkused |
|---|---|---|---|---|
| Delete Invoice | `client.sales.delete_invoice()` | ❌ | ❌ | Wrapper olemas, aga testid puuduvad. |
| Create Sales Invoice | `client.sales.send_invoice()` | ✅ `test_priority1_invoice_delivery.py` | ❌ | Kasutab vaikimisi `v1/sendinvoice`, kuigi dokumentatsioonis on olemas ka `v2`. |
| Send Sales Invoice by e-mail | `client.sales.send_invoice_by_email()` | ✅ `test_priority1_invoice_delivery.py` | ✅ `test_priority1_integration.py` | Kasutab `v2/sendinvoicebyemail`. |
| Send Sales Invoice as e-invoice | `client.sales.send_invoice_by_einvoice()` | ✅ `test_priority1_invoice_delivery.py` | ✅ `test_priority1_integration.py` | Kasutab `v2/sendinvoiceaseinv`. |
| Create Credit Invoice | `client.sales.send_credit_invoice()` | ✅ `test_priority1_invoice_delivery.py` | ❌ | Eraldi endpointi ei ole; wrapper kasutab sama `sendinvoice` transporti negatiivsete summadega. |
| Create Purchase Invoice | `client.purchases.send_invoice()` | ❌ | ✅ `test_purchase_invoice_integration.py` | Kasutab vaikimisi `v1/sendpurchinvoice`; olemas reaalne integratsioonitest PDF-manusega. |
| Create Payment of purchase invoice | `client.financial.create_payment()` | ❌ | ❌ | Katab ainult `sendPaymentV` purchase-invoice makse flow'd. Kui payloadis on `CurrencyCode`, lülitab `v2` peale, muidu kasutab `v1`. |
| Send Tax | `client.taxes.send()` | ❌ | ❌ | Kasutab `v2/sendtax`, aga testid puuduvad. |
| Create Customer | `client.customers.send()` | ❌ | ❌ | Wrapper olemas, kuid praegu kutsub vaikimisi `v1/sendcustomer`; dokumentatsioonis on see `v2` endpoint. |
| Create Vendor | `client.vendors.send()` | ❌ | ❌ | Wrapper olemas, kuid praegu kutsub vaikimisi `v1/sendvendor`; dokumentatsioonis on see `v2` endpoint. |
| Add Dimensions | `client.dimensions.add()` | ❌ | ❌ | Kasutab `v2/senddimensions`, aga testid puuduvad. |
| Add Items | `client.items.add()` | ❌ | ❌ | Kasutab `v2/senditems`, aga testid puuduvad. |
| Update Item | `client.items.update()` | ❌ | ❌ | Kasutab `v1/updateitem`, aga testid puuduvad. |

### Dokumenteeritud endpointid, millele public wrapper puudub

Need endpointid on dokumentatsioonis olemas, kuid `merit_api/src/merit_api/namespaces.py` ei paku neile praegu avalikku namespace-meetodit. Pärast read-wrapperite lisamist on puudu jäänud ainult kirjutamise/mutating poole meetodid.

| Dokumenteeritud meetod | Endpoint(id) | Märkused |
|---|---|---|
| Create Sales Invoice with multiple payments | `/api/v1/sendinvoice2` | Puudub wrapper. |
| Create Sales Invoice of Estonian e-invoice standard 1.2 | `/api/v2/sendinvoicexml` | Puudub wrapper. |
| Create Sales Offer | `/api/v1/sendoffer`, `/api/v2/sendoffer` | Puudub wrapper. |
| Set Offer status | `/api/v2/setofferstatus` | Puudub wrapper. |
| Create Invoice from SalesOffer | `/api/v2/offer2inv` | Puudub wrapper. |
| Update sales offer | `/api/v2/updateoffer` | Puudub wrapper. |
| Create Recurring Invoice | `/api/v2/sendperinvoice` | Puudub wrapper. |
| Send Indication Values | `/api/v1/sendindvalues` | Puudub wrapper. |
| Delete Purchase Invoice | `/api/v1/deletepurchinvoice` | Puudub public wrapper; kasutatakse ainult `raw _post` kujul integratsioonitestis cleanup'iks. |
| Create Purchase Invoice Waiting Approval | `/api/v1/sendpurchorder`, `/api/v2/sendpurchorder` | Puudub wrapper. |
| Create Purchase Invoice Waiting Approval of Estonian e-invoice standard 1.2 | `/api/v2/sendpurchorderxml` | Puudub wrapper. |
| Send Invenroty Movements | `/api/v1/SendInvMovement`, `/api/v2/SendInvMovement` | Puudub wrapper. |
| Create Payment of sales invoice | `/api/v1/sendpayment`, `/api/v2/sendpayment` | Puudub wrapper. |
| Create Payment of sales offer | `/api/v1/sendPaymentO`, `/api/v2/sendPaymentO` | Puudub wrapper. |
| Delete Payment | `/api/v1/deletepayment` | Puudub wrapper. |
| Bank statement import | `/api/v2/sendcamt53` | Puudub wrapper. |
| Send Settlement | `/api/v2/sendsettlement` | Puudub wrapper. |
| Send ExpensePayments | `/api/v2/Banks/{bankId}/ExpensePayments` | Puudub wrapper. |
| Send IncomePayments | `/api/v2/Banks/{bankId}/IncomePayments` | Puudub wrapper. |
| Send PrePayments | `/api/v2/Banks/{bankId}/PrePayments`, `/api/v2/Banks/{bankId}/PrePayments/ForCustomer/{customerId}`, `/api/v2/Banks/{bankId}/PrePayments/ForVendor/{vendorId}` | Puudub wrapper. |
| Creating General Ledger Transactions | `/api/v1/sendglbatch` | Puudub wrapper. |
| Send Fixed assets | `/api/v2/sendfixedassets` | Puudub wrapper. |
| Update Customer | `/api/v1/updatecustomer` | Puudub wrapper. |
| Create Customergroup | `/api/v2/sendcustomergroup` | Puudub wrapper. |
| Update Vendor | `/api/v1/updatevendor`, `/api/v2/updatevendor` | Puudub wrapper. |
| Create Vendorgroup | `/api/v2/sendvendorgroup` | Puudub wrapper. |
| Add Dimensions Values | `/api/v2/senddimvalues` | Puudub wrapper. |
| Send prices | `/api/v2/sendprices` | Puudub wrapper. |
| Send discounts | `/api/v2/senddiscounts` | Puudub wrapper. |
| Send units of measure | `/api/v2/senduom` | Puudub wrapper. |
| Add Item groups | `/api/v2/senditemgroups` | Puudub wrapper. |
