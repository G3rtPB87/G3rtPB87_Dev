# Table Change Log System

A full audit-trail system for Microsoft SQL Server that captures every INSERT, UPDATE, and DELETE on an `Inventory` table as timestamped JSON snapshots. Includes a Streamlit web UI for browsing, filtering, and replaying changes.

---

## What's included

| File | Purpose |
|---|---|
| `app.py` | Streamlit web UI (Dashboard, Audit Log, Inventory, Operations, Configuration) |
| `demo_db.py` | SQLite-backed demo database — runs locally with no SQL Server required |
| `db_connect.py` | pyodbc / SQLAlchemy connection helper for a live SQL Server instance |
| `schema.sql` | T-SQL script — creates `Inventory`, `Inventory_AuditLog`, and the audit trigger |
| `seed_data.py` | CLI script that inserts 10 rows, updates 3, and deletes 1 against a live SQL Server |
| `log_viewer.py` | Standalone CLI / Streamlit viewer for a live SQL Server audit log |
| `requirements.txt` | All Python dependencies |

---

## Prerequisites

### Python

- **Python 3.9 or later** — check with `python3 --version`
- No virtual environment required, though one is recommended

### For the live SQL Server mode (optional)

- A running **SQL Server** instance — SQL Server Express (free), Developer Edition, or Azure SQL all work
- **ODBC Driver 17 or 18 for SQL Server** installed on your machine
  - macOS: `brew install msodbcsql18`
  - Windows: download from [Microsoft](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
  - Linux (Ubuntu): follow the [Microsoft docs](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

---

## Quick start — Demo Mode (no SQL Server needed)

Demo mode uses a local SQLite file to simulate the full SQL Server schema and trigger behaviour. No credentials or drivers required.

### 1. Install dependencies

```bash
pip3 install streamlit pandas plotly python-dotenv
```

### 2. Run the app

```bash
cd table_changelog
python3 -m streamlit run app.py
```

### 3. Open in browser

```
http://localhost:8501
```

The app seeds itself with 15 products, 12 updates, and 2 deletes spread across the last 7 days on first launch. Use the **↺ Reset demo data** button in the sidebar to wipe and re-seed at any time.

---

## Live SQL Server setup

### 1. Install all dependencies

```bash
pip3 install -r requirements.txt
```

`requirements.txt` includes `pyodbc` in addition to the Streamlit stack.

### 2. Configure your connection

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` and set:

```env
DB_SERVER=localhost\SQLEXPRESS   # or your server name / Azure SQL hostname
DB_DATABASE=InventoryDB
DB_UID=sa
DB_PWD=YourStrong!Passw0rd
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_AZURE=0                       # set to 1 for Azure SQL
```

> **Never commit `.env` to source control.** It is listed in `.gitignore` by convention.

### 3. Deploy the schema

Run `schema.sql` against your target database. You can do this in SSMS, Azure Data Studio, or via `sqlcmd`:

```bash
sqlcmd -S localhost\SQLEXPRESS -d InventoryDB -i schema.sql
```

This creates:
- `dbo.Inventory` — the primary table
- `dbo.Inventory_AuditLog` — the shadow/audit table
- `dbo.trg_Inventory_Audit` — the trigger that fires on INSERT, UPDATE, and DELETE

### 4. Seed mock data (optional)

Inserts 10 products, updates 3, deletes 1, then prints an audit log summary:

```bash
python3 seed_data.py
```

### 5. Run the app

```bash
python3 -m streamlit run app.py
```

Then navigate to **⚙️ Configuration → Live SQL Server** in the sidebar to test your connection and switch from demo mode.

---

## App pages

| Page | Description |
|---|---|
| **📊 Dashboard** | Metrics, change-over-time bar chart, operation mix donut, top users, live activity feed |
| **🔍 Audit Log** | Filterable full history — expandable rows with field-level diff for UPDATEs and Before/After JSON; CSV export |
| **📦 Inventory** | Current table state with search and stock-value-by-category chart |
| **⚡ Operations** | INSERT / UPDATE / DELETE forms — each action immediately shows the audit log entry it created |
| **⚙️ Configuration** | Manage SQL Server credentials, test connection, reset demo data, view raw schema SQL |

---

## How the trigger works

A single `AFTER INSERT, UPDATE, DELETE` trigger on `dbo.Inventory` fires for every data change. It:

1. Detects the operation type from the virtual `INSERTED` / `DELETED` tables
2. Serialises the **before** state (`DELETED`) and **after** state (`INSERTED`) to JSON using `FOR JSON PATH, WITHOUT_ARRAY_WRAPPER`
3. Writes one row to `dbo.Inventory_AuditLog` per affected record, capturing the operation type, UTC timestamp, SQL Server login (`SYSTEM_USER`), and both JSON snapshots

Bulk operations (e.g. `UPDATE … WHERE Category = 'Electronics'`) produce one audit row per affected record.

---

## Project structure

```
table_changelog/
├── app.py                # Streamlit UI
├── demo_db.py            # SQLite demo backend
├── db_connect.py         # Live SQL Server connection helpers
├── schema.sql            # T-SQL schema + trigger
├── seed_data.py          # CLI mock data generator
├── log_viewer.py         # Standalone CLI/Streamlit log viewer
├── requirements.txt      # Python dependencies
├── .env.example          # Credentials template
└── README.md             # This file
```

---

## Dependency versions

| Package | Version | Required for |
|---|---|---|
| streamlit | ≥ 1.35 | Web UI |
| pandas | ≥ 2.0 | Data tables and CSV export |
| plotly | ≥ 5.0 | Charts |
| python-dotenv | ≥ 1.0 | Loading `.env` credentials |
| pyodbc | ≥ 4.0 | Live SQL Server connection (optional) |
| rich | ≥ 13.0 | Pretty CLI tables in `log_viewer.py` (optional) |
| sqlalchemy | ≥ 2.0 | SQLAlchemy engine helper in `db_connect.py` (optional) |

Install everything:

```bash
pip3 install -r requirements.txt
```

Install the minimum needed for demo mode only:

```bash
pip3 install streamlit pandas plotly
```
