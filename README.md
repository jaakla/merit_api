# Merit API MCP Server

MCP server ja Pythoni SDK Merit Aktiva REST API jaoks. MCP server eksponeerib praegu 29 tööriista, 3 töövoo prompti ja 2 ressurssi. See on mõeldud töötama MCP klientidega nagu Claude Code, Codex CLI, Cursor, Windsurf, Cline, Gemini CLI ja sarnased tööriistad.

> **Aktiivne arendus.** See projekt areneb endiselt. MCP kiht on kasutatav, kuid see ei ole veel täisfunktsionaalne raamatupidamise töövoosüsteem. Kontrolli iga kirjutava operatsiooni tulemust live-raamatupidamisandmete vastu enne selle usaldamist.

## Vastutusest loobumine

**See on eksperimentaalne ja mitteametlik projekt.** See ei ole seotud Merit Aktivaga, selle poolt toetatud ega ametlikult kinnitatud.

**Kasutad seda täielikult omal vastutusel.** See tarkvara saab lugeda ja muuta live-raamatupidamisandmeid, sh kliente, hankijaid, artikleid, arveid, makseid, makse ja dimensioone. Autorid ei vastuta vigaste kannete, kustutatud kirjete ega muu kaudse kahju eest.

Seda tarkvara kasutades nõustud, et:

- vastutad ise kõigi loodud või muudetud raamatupidamisandmete kontrollimise eest
- peaksid enne tähtsate live-andmete vastu kasutamist põhjalikult testima
- tegemist on eksperimentaalse tarkvaraga ilma igasuguse garantiita

## Nõuded

- Node.js 18+ `npx` wrapperi jaoks
- Python 3.10+ peab olema masinas olemas

npm-pakett eemaldab vajaduse Pythoni sõltuvusi käsitsi paigaldada, kuid server ise on kirjutatud Pythonis, seega on lokaalne Python interpreter siiski vajalik.

## API mandaadid

Server kasutab järgmisi keskkonnamuutujaid:

- `MERIT_API_ID`
- `MERIT_API_KEY`
- `MERIT_API_COUNTRY` on valikuline, `EE` või `PL`, vaikimisi `EE`

Näide:

```bash
export MERIT_API_ID=your-api-id
export MERIT_API_KEY=your-api-key
export MERIT_API_COUNTRY=EE
```

Kui `MERIT_API_ID` või `MERIT_API_KEY` puudub, käivitub server seadistusrežiimis (aga mitte igas kliendis). Seadistusrežiimis:

- `get_setup_instructions` jääb kättesaadavaks
- avastusressursid jäävad kättesaadavaks
- promptid jäävad kättesaadavaks
- API-põhised tööriistad tagastavad seadistusjuhise ega kutsu Merit API-t

## Seadistus

### 1. Lisa MCP server

Enamik AI assistente oskab selle sinu eest seadistada. Mõeldud paketikäsk on:

```bash
npx -y merit-api-mcp
```

Kui eelistad käsitsi seadistada:

**Claude Code:**

```bash
claude mcp add merit-api -- npx -y merit-api-mcp
```

**Teised tööriistad** JSON-konfiguratsiooniga:

```json
{
  "mcpServers": {
    "merit-api": {
      "command": "npx",
      "args": ["-y", "merit-api-mcp"],
      "env": {
        "MERIT_API_ID": "your-api-id-here",
        "MERIT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Codex CLI** TOML-konfiguratsiooniga:

```toml
[mcp_servers.merit-api]
command = "npx"
args = ["-y", "merit-api-mcp"]
```

npm wrapper loob automaatselt privaatse virtualenv-i, paigaldab sinna kaasasolevad Pythoni alamprojektid ja käivitab MCP serveri. Tavakasutuse korral ei pea kasutaja `pip install` käske käsitsi jooksutama.

<details>
<summary>Tööriistade konfiguratsioonifailide asukohad</summary>

| Tööriist | Konfiguratsioonifail |
|---|---|
| **Claude Code** | `~/.claude/settings.json` või projekti `.claude/settings.json` |
| **Codex CLI** | `~/.codex/config.toml` |
| **Gemini CLI** | `~/.gemini/settings.json` |
| **Cursor** | projekti `.cursor/mcp.json` |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` |
| **Cline** | VS Code seadetes `cline.mcpServers` all |

</details>

### 2. Käsitsi Pythonist käivitamine

Kui töötad otse Pythoni keskkonnast ega kasuta `npx`, saab MCP serveri käivitada ka nii:

```bash
python3 -m merit_api_mcp
```

### 3. Käivitamine lähtekoodist

```bash
git clone https://github.com/jaakla/merit_api.git
cd merit_api
pip install -e ./merit_api
pip install -e ./mcp
python3 -m merit_api_mcp
```

## Töövood (MCP promptid)

Server sisaldab praegu 3 sisseehitatud prompti:

| Prompt | Kirjeldus |
|---|---|
| `setup-merit-api` | Selgitab, kuidas seadistada vajalikud keskkonnamuutujad ja server käivitada |
| `create-sales-invoice` | Juhendab assistenti kliendi leidmisel ja müügiarve loomisel |
| `find-or-create-customer` | Juhendab assistenti kliendi otsimisel ja loomisel |

## Ressursid

| Ressurss | Kirjeldus |
|---|---|
| `merit://server/info` | Serveri metaandmed, seadistusrežiimi staatus, toetatud env muutujad ja hoiatus |
| `merit://tools/catalog` | Tööriistade kataloog koos namespace'i, meetodi, read-only/mutating staatuse ja parameetrirežiimiga |

## Tööriistade pind

MCP server eksponeerib praegu otse olemasoleva SDK pinna.

Kliendid:

- `customers_get_list`
- `customers_send`

Hankijad:

- `vendors_get_list`
- `vendors_send`

Artiklid:

- `items_get_list`
- `items_add`
- `items_update`

Müük:

- `sales_get_invoices`
- `sales_get_invoice`
- `sales_send_invoice`
- `sales_delete_invoice`
- `sales_send_credit_invoice`
- `sales_get_offers`
- `sales_get_recurring_invoices`

Ostud:

- `purchases_get_invoices`
- `purchases_send_invoice`

Finants:

- `financial_get_payments`
- `financial_create_payment`
- `financial_get_gl_batches`
- `financial_get_banks`
- `financial_get_costs`
- `financial_get_projects`

Ladu:

- `inventory_get_movements`

Põhivara:

- `assets_get_fixed_assets`

Maksud:

- `taxes_get_list`
- `taxes_send`

Dimensioonid:

- `dimensions_get_list`
- `dimensions_add`

Kirjutavad tööriistad on selgelt märgistatud mutating-tööriistadena nii kirjeldustes kui ka tööriistakataloogi ressursis.

## Kasutusnäited

Kui MCP server on ühendatud, saad AI assistendiga suhelda loomulikus keeles.

### Uuri põhiandmeid

> "Näita kliente, mis vastavad nimele Acme"

Assistant peaks kasutama `customers_get_list` tööriista koos `Name` filtriga.

### Loo või uuenda klienti

> "Loo uus klient Example OÜ"

Assistant peaks koostama kliendi payloadi ja kutsuma `customers_send`.

### Loo müügiarve

> "Loo kliendile Acme müügiarve aprilli konsultatsiooniteenuse eest"

Assistant saab kasutada `customers_get_list`, vajadusel `find-or-create-customer`, ja seejärel `sales_send_invoice`.

### Uuri viiteandmeid

> "Mis pangad, kulukohad, projektid ja maksud Merit'is olemas on?"

Assistant saab kasutada `financial_get_banks`, `financial_get_costs`, `financial_get_projects` ja `taxes_get_list`.

### Kontrolli seadistuse seisu

> "Kontrolli, kas Merit MCP server on õigesti seadistatud"

Assistant saab kasutada `get_setup_instructions` ja `merit://server/info`.

## SDK kasutamine

See repository sisaldab ka eraldi Pythoni SDK projekti kataloogis [merit_api/](/Users/jaak/mygit/merit_api/merit_api).

Näide:

```python
from merit_api import MeritAPI

client = MeritAPI(api_id="YOUR_API_ID", api_key="YOUR_API_KEY")

customers = client.customers.get_list()
invoices = client.sales.get_invoices(
    PeriodStart="2024-01-01",
    PeriodEnd="2024-01-31",
)
```

SDK sisaldab praegu:

- deterministlikku request body serialiseerimist signeerimiseks
- seadistatavat timeouti ja retry käitumist
- request/response logger hooke koos saladuste redaktsiooniga
- valikulist idempotency headeri genereerimist
- API taseme ärivea parsimist HTTP 200 vastustest

## Uuendamine

Uuendamise viis sõltub sellest, kuidas serverit käivitad.

### Kui kasutad `npx`

Kui sinu MCP konfiguratsioon kasutab `npx -y merit-api-mcp`, piisab tavaliselt MCP serveri taaskäivitamisest või uuesti laadimisest. Järgmisel käivitamisel tõmbab `npx` viimase avaldatud versiooni.

Kui klient jääb kasutama vanemat cache'itud versiooni, sunni ühe korra värskendus:

```bash
npx -y merit-api-mcp@latest
```

Seejärel taaskäivita MCP server oma kliendis.

### Kui jooksutad lokaalsest checkout'ist

```bash
git pull
pip install -e ./merit_api
pip install -e ./mcp
```

Seejärel taaskäivita MCP server oma kliendis.

## Arendus

See repository on jaotatud eraldi alamprojektideks:

- [merit_api/](/Users/jaak/mygit/merit_api/merit_api) SDK jaoks
- [mcp/](/Users/jaak/mygit/merit_api/mcp) Pythoni MCP serveri jaoks
- juure `package.json` npm wrapperi jaoks

SDK testid:

```bash
cd merit_api
python3 -m pytest -q
```

MCP testid:

```bash
cd mcp
python3 -m pytest -q
```

Kontrolli npm wrapperi tarballi:

```bash
npm pack --dry-run
```

SDK live integratsioonitestid on opt-in:

```bash
cd merit_api
MERIT_API_INTEGRATION_TEST=true python3 -m pytest -q
```

## Hea teada

- Praegune MCP server toetab ainult ühte ühendust korraga
- Audit logi püsisalvestust veel ei ole
- Dry-run kirjutusvooge veel ei ole
- Dokumentide ingest'i või OCR töövookihti veel ei ole
- MCP skeemid jäävad üldiseks seal, kus aluseks olev SDK on üldine
- Juure npm-pakett on launcher-wrapper; päris Pythoni projektid asuvad `merit_api/` ja `mcp/`

## Litsents

[MIT](LICENSE)
