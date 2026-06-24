# Merit Unofficial MCP Server

[![CI](https://github.com/jaakla/merit_api/actions/workflows/ci.yml/badge.svg)](https://github.com/jaakla/merit_api/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/merit-unofficial-mcp-server.svg)](https://pypi.org/project/merit-unofficial-mcp-server/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-purple.svg)](https://modelcontextprotocol.io)
<a href="https://glama.ai/mcp/servers/jaakla/merit_api/score"><img src="https://glama.ai/mcp/servers/jaakla/merit_api/badge" alt="Glama score" width="140" /></a>

> **English summary:** Unofficial MCP server and Python SDK for the [Merit Aktiva](https://aktiva.merit.ee) accounting REST API. Exposes 32 tools, 3 workflow prompts, and 2 resources to AI coding assistants (Claude Code, Cursor, Windsurf, Gemini CLI, etc.), letting you read and write accounting data — customers, invoices, payments, taxes, and more — through natural-language prompts. Write operations use a two-step preview/confirm flow to prevent accidental changes. Requires a Merit Aktiva Premium account and API credentials (`MERIT_API_ID`, `MERIT_API_KEY`). Run/install instantly via `uvx`. **Experimental and unofficial — use at your own risk.**

---

MCP server ja Pythoni SDK Merit Aktiva REST API jaoks. MCP server eksponeerib praegu 32 tööriista, 3 töövoo prompti ja 2 ressurssi. See on mõeldud töötama MCP klientidega nagu Claude Code, Codex CLI, Cursor, Windsurf, Cline, Gemini CLI ja sarnased tööriistad.

> **Aktiivne arendus.** See projekt areneb endiselt. MCP kiht on kasutatav, kuid see ei ole veel täisfunktsionaalne raamatupidamise töövoosüsteem. Kontrolli iga kirjutava operatsiooni tulemust live-raamatupidamisandmete vastu enne selle usaldamist.

## Vastutusest loobumine

**See on eksperimentaalne ja mitteametlik projekt.** See ei ole seotud AS Merit Tarkvaraga, ei ole nende poolt toetatud ega ametlikult kinnitatud.

**Kasutad seda täielikult omal vastutusel.** See tarkvara saab lugeda ja muuta live-raamatupidamisandmeid, sh kliente, hankijaid, artikleid, arveid, makseid, makse ja dimensioone. Autorid ei vastuta vigaste kannete, kustutatud kirjete ega muu kaudse kahju eest.

Seda tarkvara kasutades nõustud, et:

- vastutad ise kõigi loodud või muudetud raamatupidamisandmete kontrollimise eest
- peaksid enne tähtsate live-andmete vastu kasutamist põhjalikult testima
- tegemist on eksperimentaalse tarkvaraga ilma igasuguse garantiita

## Kasutaja API võtmed

Server vajab järgmisi võtmeid, mille saab Meriti Aktivast Ettevõtte andmete > API Seadistustes, vajalik **piisav kasutaja õiguste tase (haldaja) ja pakett (Premium või parem)**:

- `MERIT_API_ID`
- `MERIT_API_KEY`
- `MERIT_API_COUNTRY` on valikuline, `EE` või `PL`, vaikimisi `EE`

Käsurea-vahendites saab need panna keskkonda (environment variables):

```bash
export MERIT_API_ID=your-api-id
export MERIT_API_KEY=your-api-key
export MERIT_API_COUNTRY=EE
```

Kui `MERIT_API_ID` või `MERIT_API_KEY` puudub, võib käivituda server seadistusrežiimis, aga kindlam on need seadistada json failis nagu kirjas allpool. Seadistusrežiimis:

- `get_setup_instructions` jääb kättesaadavaks
- ressursid jäävad kättesaadavaks
- promptid jäävad kättesaadavaks
- API-põhised tööriistad tagastavad seadistusjuhise ega kutsu Merit API-t

## Paigaldus ja seadistus

### Eeltingimused

* Arvutisse peab olema paigaldatud [uv](https://docs.astral.sh/uv/) — kaasaegne ja kiire Pythoni pakihaldur.

### 1. Lisa MCP server

Server käivitatakse lokaalselt taustal ja ühendub otse Meriti pilveteenusega. Kolmandaid osapooli ei kaasata.

**Claude Code:** (käsurealt)

```bash
claude mcp add merit-api -- uvx merit-unofficial-mcp-server
```

**Teised tööriistad** JSON-konfiguratsiooniga (nt. Claude Desktop, Cursor, Cline):

```json
{
  "mcpServers": {
    "merit-api": {
      "command": "uvx",
      "args": ["merit-unofficial-mcp-server"],
      "env": {
        "MERIT_API_ID": "your-api-id-here",
        "MERIT_API_KEY": "your-api-key-here",
        "MERIT_API_COUNTRY": "EE"
      }
    }
  }
}
```

Seadistusfail Claude Desktop-is:

* macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
* Windows: `%APPDATA%\Claude\claude_desktop_config.json`
* Linux: `~/.config/Claude/claude_desktop_config.json`

**Codex CLI** TOML-konfiguratsiooniga:

```toml
[mcp_servers.merit-api]
command = "uvx"
args = ["merit-unofficial-mcp-server"]
```

`uvx` tõmbab ja käivitab serveri otse PyPI registrist, tagades et alati on olemas vajalikud Pythoni moodulid ilma masinat risustamata.

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

### 2. Käivitamine lähtekoodist (arenduseks)

Kui soovite serverit lokaalselt muuta või testida, kloonige repositoorium ja käivitage see uv workspace toel:

```bash
git clone https://github.com/jaakla/merit_api.git
cd merit_api
# Paigalda lokaalsed sõltuvused (sh pytest arendustestide jaoks)
uv sync --all-extras
# Käivita MCP server otse lokaalsest koodist
uv run --package merit-unofficial-mcp-server merit-unofficial-mcp
```

## MCP promptid

Server sisaldab kolme lihtsat näidisprompti, kuid kasutada saab ka mistahes teistsuguseid, keerukamaid käske:

| Prompt | Kirjeldus |
|---|---|
| `setup-merit-api` | Selgitab, kuidas seadistada vajalikud keskkonnamuutujad ja server käivitada |
| `create-sales-invoice` | Juhendab assistenti kliendi leidmisel ja müügiarve loomisel |
| `find-or-create-customer` | Juhendab assistenti kliendi andmete otsimisel ja loomisel |

## Ressursid

| Ressurss | Kirjeldus |
|---|---|
| `merit://server/info` | Serveri metaandmed, seadistusrežiimi staatus, toetatud env muutujad ja hoiatus |
| `merit://tools/catalog` | Tööriistade kataloog koos konsolideeritud tööriistade, nende action'ite ja nõutud väljadega |

## Tööriistad (tools)

Merit võimaldab kümneid erinevaid käske, see MCP server koondab need üldistatud tööriistadeks, et vältida liiga pikka nimekirja käskudest. Üldine tööriist kasutab `action` välja, et valida konkreetne Merit'i workflow.

Lugemise, Read-only tööriistad:

- `merit_read_master_data`
- `merit_read_sales`
- `merit_read_purchases`
- `merit_read_financial`
- `merit_read_inventory`
- `merit_read_reports`

Muutmise/kirjutamise tööriistad toimivad kahe käsuna, et vältida vigaste andmete sisestust:

- `merit_write_customers` (eelvaade) ja `merit_write_customers_confirm` (kinnitatud muutmine)
- `merit_write_sales` (eelvaade) ja `merit_write_sales_confirm` (kinnitatud muutmine)
- `merit_write_purchases` (eelvaade) ja `merit_write_purchases_confirm` (kinnitatud muutmine)
- `merit_write_financial` (eelvaade) ja `merit_write_financial_confirm` (kinnitatud muutmine)

Kirjutavad tööriistad on kahe sammuga. Esimene `merit_write_*` kutse ei tee Merit'is muudatusi: see tagastab eelvaate, `confirmation_tool` nime ja unikaalse `confirmation_code` väärtuse. Pärast eelvaate ülevaatamist tuleb sama action'i ja samade argumentidega kutsuda vastavat `*_confirm` tööriista ning anda kaasa `confirmation_code` ja `confirmed=true`. Kood on seotud konkreetsete argumentidega ja seda ei saa kasutada teise muudatuse kinnitamiseks.

**NB! mõned AI mudelid püüavad olla "abivalmid" ja proovivad teha *_confirm* käsku automaatselt ise. Ole tähelepanelik, enne kui vajutad "Allow".**

Kõigi tööriistade täielik action-kataloog on ressursis `merit://tools/catalog`.

## Kasutusnäited

Kui MCP server on ühendatud, saad AI assistendiga suhelda eesti, inglise (tegelikult enamvähem mistahes) keeles.

### Uuri põhiandmeid

> "Näita kliente, mis vastavad nimele Acme"

Töövahend peaks kasutama `merit_read_master_data` tööriista action'iga `customers_list` ja `filters={"Name": "Acme"}`.

### Loo või uuenda kliendi andmeid

> "Loo uus klient Example OÜ"

Töövahend peaks koostama kliendi andmete faili ja kutsuma `merit_write_customers` tööriista action'iga `customer_upsert`.

**Merit nõuab teatud (ja kahjuks mitte dokumenteeritud) minimaalset komplekti andmeid, seega esimene katse võib ebaõnnestuda. Siiski paremad AI mudelid oskavad neid automaatselt juurde otsida veebist, küsida kasutajalt ja ka mitu korda erinevalt andmeid proovida, kuni toimib.**

### Loo müügiarve

> "Loo kliendile Acme müügiarve aprilli konsultatsiooniteenuse eest"

Töövahend saab kasutada `merit_read_master_data` action'iga `customers_list`, vajadusel `find-or-create-customer`, ja seejärel `merit_write_sales` action'iga `sales_invoice_create`.
`merit_write_sales` tagastab eelvaate; arve luuakse alles `merit_write_sales_confirm` kutsega, kui kasutaja on eelvaate üle vaadanud.

### Uuri sisestatud andmeid

> "Mis pangad, kulukohad, projektid ja maksud Merit'is olemas on?"

Assistant saab kasutada `merit_read_master_data` tööriista action'eid `banks_list`, `cost_centers_list`, `projects_list` ja `taxes_list`.

### Kontrolli seadistuse seisu

> "Kontrolli, kas Merit MCP server on õigesti seadistatud ja saan Meritiga ühenduda"

Assistant saab kasutada `get_setup_instructions` ja `merit://server/info`.

## SDK kasutamine

See repository sisaldab ka eraldi avatud koodiga Pythoni SDK projekti kataloogis [merit_api/](/Users/jaak/mygit/merit_api/merit_api). Siit saad kontrollida, mida täpselt tarkvara teeb, ja arendusoskuse korral pakkuda välja koodiparandusi ja -täiendusi.

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
- seadistatavat timeouti ja retry käitumist (kordusi tehakse ainult idempotentsetele päringutele; muteerivaid kirjutusi nagu arve või makse loomine ei korrata, sest aegunud, kuid serveris juba kinnitatud päringu kordamine looks duplikaadi)
- request/response logger hooke koos saladuste redaktsiooniga
- valikulist idempotency headeri genereerimist (tähelepanu: Merit API ei dedubleeri selle headeri põhjal — see ei ole duplikaadivastane garantii, vaid valmidus juhuks, kui server seda kunagi toetab)
- ostuarvete ja maksete duplikaadikaitset: vaikimisi ei looda sama tarnija + `BillNo` ostuarvet ega sama `BillNo` + summaga makset teist korda; möödaminekuks anna `allow_duplicate=True`
- API taseme vigade haldust, eristust HTTP 200 vastustest

## Uuendamine

Uuendamise viis sõltub sellest, kuidas serverit käivitad.

### Kui kasutad `uvx`

Kuna server on avaldatud PyPI-s, laadib `uvx` automaatselt alla uusima versiooni. Kui soovite olemasolevat paigaldust käsitsi viimasele versioonile uuendada, käivitage:

```bash
uvx --upgrade merit-unofficial-mcp-server
```

Seejärel taaskäivita oma AI töövahend.

### Kui jooksutad algkoodist, lokaalsest GIT checkout'ist

```bash
git pull
# Kuna kasutusel on uv workspace, siis uv sync teeb kõik automaatselt korda:
uv sync
```

Seejärel taaskäivita oma AI töövahend.

## Arendus

Repositoorium on jaotatud ühisesse `uv` workspace'i kuuluvateks alamprojektideks:

- [merit_api/](merit_api/merit_api) SDK jaoks (pakett: `merit-api`)
- [mcp/](merit_api/mcp) Pythoni MCP serveri jaoks (pakett: `merit-unofficial-mcp-server`)
- root `pyproject.toml` workspace seadete jaoks

SDK testid:

```bash
uv run --package merit-api pytest
```

MCP testid:

```bash
uv run --package merit-unofficial-mcp-server pytest
```

SDK live integratsioonitestid on opt-in:

```bash
MERIT_API_INTEGRATION_TEST=true uv run --package merit-api pytest
```

Iga Merit päringu ja vastuse väljatrükkimiseks lisa `MERIT_API_VERBOSE=true` ja pytesti `-s` lipp:

```bash
MERIT_API_INTEGRATION_TEST=true MERIT_API_VERBOSE=true uv run --package merit-api pytest -s
```

## Versiooni avaldamine (hooldajale)

Mõlemad paketid — `merit-api` (SDK) ja `merit-unofficial-mcp-server` (MCP server) — avaldatakse PyPI-sse käsitsi; automaatset CI avaldusvoogu ei ole. Versioonid hoitakse lukus, st kõik tõstetakse korraga samale numbrile.

1. **Tõsta versioon** samale numbrile kõigis neljas kohas:
   - `package.json` — väli `version`
   - `mcp/pyproject.toml` — `version` ning sõltuvuse pin `merit-api>=X.Y.Z`
   - `merit_api/pyproject.toml` — `version`

2. **Lisa muudatused** `CHANGELOG.md`-sse uue versiooni pealkirja alla.

3. **Värskenda lukufaili:**

   ```bash
   uv lock
   ```

4. **Jooksuta testid:**

   ```bash
   uv run --package merit-api pytest
   uv run --package merit-unofficial-mcp-server pytest
   ```

5. **Tee commit ja silt:**

   ```bash
   git add -A
   git commit -m "release: vX.Y.Z"
   git tag -a vX.Y.Z -m "vX.Y.Z"
   ```

6. **Lükka GitHubi:**

   ```bash
   git push origin main
   git push origin vX.Y.Z
   ```

7. **Ehita paketid** (tulemused tekivad kausta `dist/`):

   ```bash
   uv build --package merit-api
   uv build --package merit-unofficial-mcp-server
   ```

8. **Avalda PyPI-sse** — kõigepealt SDK (`merit-api`), sest MCP server sõltub sellest, ja alles siis MCP server. Vajab PyPI API tokenit (`UV_PUBLISH_TOKEN` keskkonnamuutuja või lipp `--token`):

   ```bash
   uv publish dist/merit_api-X.Y.Z*
   uv publish dist/merit_unofficial_mcp_server-X.Y.Z*
   ```

Pärast avaldamist laadib `uvx merit-unofficial-mcp-server` automaatselt uue versiooni.

> npm pakett `merit-unofficial-mcp` on aegunud ega vaja enam avaldamist — kasutajad suunatakse `uvx` peale.

## Hea teada

- Kasuta **tipptasemel AI/LLM mudeleid**, kuigi need on pisut kallimad : **Opus**/**Pro** tase, ja **mitte** Light, mini või Haiku tase. 
- Praegune MCP server toetab ainult ühte ühendust korraga, ehk siis ühe ettevõttega tööd. Kui sa oled raamatupidamisfirma, kes soovib selle tasuta ja garaantiita koodi ning AI abil kõikide oma klientide raamatupidamist automaatselt hallata, siis olgu Jumala arm sinuga (loe: ei ole hea mõte). 
- Auditeerimiseks logi püsisalvestust ei ole
- Dry-run kirjutusvooge veel ei ole — aga kirjutus käib läbi kontrolli, see peaks asendama dry-run enamuse juhtudel
- Dokumentide sisestust mis nõuaks OCR töövoogu veel ei ole - nt ostuarvete sisestuseks kasuta muud AI tööriista või -mudelit, mis teeb selle tekstiks. PDF faili saab manusega ostuarvele lisada küll.

## Litsents - tasuta, omal vastutusel

[MIT](LICENSE)
