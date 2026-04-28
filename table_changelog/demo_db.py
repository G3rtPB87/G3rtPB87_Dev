"""
demo_db.py — SQLite-backed demo database that mirrors the SQL Server schema.

The T-SQL trigger logic is implemented in Python so the full INSERT / UPDATE /
DELETE → audit-log pipeline works locally without SQL Server installed.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_changelog.db")

PRODUCTS = [
    ("SKU-001", "Wireless Keyboard Pro",    "Electronics", 150,  49.99, "Warehouse A"),
    ("SKU-002", "USB-C Hub 7-Port",          "Electronics",  80,  34.95, "Warehouse B"),
    ("SKU-003", "Standing Desk Mat",         "Office",        60,  29.00, "Store Front"),
    ("SKU-004", "Noise Cancelling Buds",     "Electronics",  40,  89.99, "Warehouse A"),
    ("SKU-005", "Bamboo Notebook A5",        "Office",       200,  12.50, "Store Front"),
    ("SKU-006", "Blue Light Glasses",        "Clothing",      75,  24.95, "Warehouse B"),
    ("SKU-007", "Mechanical Pencil Set",     "Office",       300,   8.75, "Store Front"),
    ("SKU-008", "Portable Charger 20K",      "Electronics",   55,  59.99, "Warehouse A"),
    ("SKU-009", "Cable Organiser Kit",       "Hardware",     120,  14.00, "Warehouse B"),
    ("SKU-010", "Screen Cleaning Spray",     "Hardware",     500,   6.50, "Store Front"),
    ("SKU-011", "Ergonomic Mouse",           "Electronics",   90,  44.99, "Warehouse A"),
    ("SKU-012", "Laptop Stand Aluminium",    "Office",        45,  69.99, "Warehouse B"),
    ("SKU-013", "Monitor Arm Dual",          "Office",        25, 129.00, "Warehouse A"),
    ("SKU-014", "Webcam HD 1080p",           "Electronics",   60,  79.99, "Warehouse B"),
    ("SKU-015", "Desk Lamp LED Adjustable",  "Office",        80,  39.99, "Store Front"),
]

USERS = ["app_user", "admin", "batch_job", "api_gateway", "migration_script"]

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_database() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS Inventory (
            InventoryID INTEGER PRIMARY KEY AUTOINCREMENT,
            SKU         TEXT    NOT NULL UNIQUE,
            ProductName TEXT    NOT NULL,
            Category    TEXT,
            Quantity    INTEGER NOT NULL DEFAULT 0,
            UnitPrice   REAL    NOT NULL DEFAULT 0.0,
            Location    TEXT,
            IsActive    INTEGER NOT NULL DEFAULT 1,
            CreatedAt   TEXT    NOT NULL,
            UpdatedAt   TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Inventory_AuditLog (
            AuditID    INTEGER PRIMARY KEY AUTOINCREMENT,
            Operation  TEXT    NOT NULL,
            ChangedAt  TEXT    NOT NULL,
            ChangedBy  TEXT    NOT NULL,
            RecordID   INTEGER,
            BeforeData TEXT,
            AfterData  TEXT
        );

        CREATE INDEX IF NOT EXISTS IX_AuditLog_RecordID
            ON Inventory_AuditLog (RecordID, ChangedAt);
    """)
    conn.commit()
    conn.close()


def reset_database() -> None:
    conn = get_connection()
    conn.executescript("""
        DROP TABLE IF EXISTS Inventory_AuditLog;
        DROP TABLE IF EXISTS Inventory;
    """)
    conn.commit()
    conn.close()
    init_database()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.utcnow().isoformat(sep=" ", timespec="seconds")


def _get_row(cur: sqlite3.Cursor, inventory_id: int) -> Optional[dict]:
    cur.execute("SELECT * FROM Inventory WHERE InventoryID = ?", (inventory_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def _write_audit(
    cur: sqlite3.Cursor,
    operation: str,
    record_id: int,
    before: Optional[dict],
    after: Optional[dict],
    user: str,
    ts: str,
) -> None:
    cur.execute(
        """
        INSERT INTO Inventory_AuditLog
            (Operation, ChangedAt, ChangedBy, RecordID, BeforeData, AfterData)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            operation, ts, user, record_id,
            json.dumps(before) if before else None,
            json.dumps(after)  if after  else None,
        ),
    )


# ---------------------------------------------------------------------------
# CRUD  (each call opens + closes its own connection)
# ---------------------------------------------------------------------------

def insert_record(
    sku: str,
    product_name: str,
    category: str,
    quantity: int,
    unit_price: float,
    location: str,
    user: str = "demo_user",
    ts: Optional[str] = None,
) -> int:
    now  = ts or _now()
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO Inventory
                (SKU, ProductName, Category, Quantity, UnitPrice,
                 Location, IsActive, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (sku, product_name, category, quantity, unit_price, location, now, now),
        )
        inv_id = cur.lastrowid
        after  = _get_row(cur, inv_id)
        _write_audit(cur, "INSERT", inv_id, None, after, user, now)
        conn.commit()
        return inv_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_record(
    inventory_id: int,
    user: str = "demo_user",
    ts: Optional[str] = None,
    **kwargs: Any,
) -> None:
    now  = ts or _now()
    conn = get_connection()
    cur  = conn.cursor()
    try:
        before = _get_row(cur, inventory_id)
        if before is None:
            raise ValueError(f"InventoryID {inventory_id} not found")

        if kwargs:
            # Column names come from internal callers — values are parameterised
            set_sql = ", ".join(f"{k} = ?" for k in kwargs)
            cur.execute(
                f"UPDATE Inventory SET {set_sql}, UpdatedAt = ? WHERE InventoryID = ?",
                [*kwargs.values(), now, inventory_id],
            )

        after = _get_row(cur, inventory_id)
        _write_audit(cur, "UPDATE", inventory_id, before, after, user, now)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_record(
    inventory_id: int,
    user: str = "demo_user",
    ts: Optional[str] = None,
) -> None:
    now  = ts or _now()
    conn = get_connection()
    cur  = conn.cursor()
    try:
        before = _get_row(cur, inventory_id)
        if before is None:
            raise ValueError(f"InventoryID {inventory_id} not found")
        cur.execute("DELETE FROM Inventory WHERE InventoryID = ?", (inventory_id,))
        _write_audit(cur, "DELETE", inventory_id, before, None, user, now)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_audit_logs(
    limit: int = 200,
    operation: Optional[str] = None,
    record_id: Optional[int] = None,
    search: Optional[str] = None,
) -> list[dict]:
    conn    = get_connection()
    cur     = conn.cursor()
    clauses: list[str] = []
    params:  list[Any] = []

    if operation:
        clauses.append("Operation = ?")
        params.append(operation)
    if record_id is not None:
        clauses.append("RecordID = ?")
        params.append(record_id)
    if search:
        clauses.append("(BeforeData LIKE ? OR AfterData LIKE ? OR ChangedBy LIKE ?)")
        s = f"%{search}%"
        params += [s, s, s]

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    cur.execute(
        f"""
        SELECT AuditID, Operation, ChangedAt, ChangedBy,
               RecordID, BeforeData, AfterData
        FROM Inventory_AuditLog
        {where}
        ORDER BY AuditID DESC
        LIMIT ?
        """,
        params + [limit],
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_inventory() -> list[dict]:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM Inventory ORDER BY InventoryID")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_audit_stats() -> dict:
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Inventory_AuditLog")
    total = cur.fetchone()[0]

    cur.execute("SELECT Operation, COUNT(*) FROM Inventory_AuditLog GROUP BY Operation")
    by_op = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("""
        SELECT date(ChangedAt) AS day, Operation, COUNT(*) AS cnt
        FROM   Inventory_AuditLog
        WHERE  ChangedAt >= date('now', '-7 days')
        GROUP  BY day, Operation
        ORDER  BY day
    """)
    timeline = [{"day": r[0], "operation": r[1], "count": r[2]} for r in cur.fetchall()]

    cur.execute("""
        SELECT ChangedBy, COUNT(*) AS cnt
        FROM   Inventory_AuditLog
        GROUP  BY ChangedBy
        ORDER  BY cnt DESC
        LIMIT  5
    """)
    by_user = [{"user": r[0], "count": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT COUNT(*) FROM Inventory WHERE IsActive = 1")
    active_items = cur.fetchone()[0]

    cur.execute(
        "SELECT COALESCE(SUM(CAST(Quantity AS REAL) * UnitPrice), 0) "
        "FROM Inventory WHERE IsActive = 1"
    )
    total_value = cur.fetchone()[0]

    conn.close()
    return {
        "total_audit_entries": total,
        "by_operation": by_op,
        "timeline": timeline,
        "by_user": by_user,
        "active_items": active_items,
        "total_inventory_value": total_value,
    }


def is_seeded() -> bool:
    conn  = get_connection()
    cur   = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Inventory_AuditLog")
    count = cur.fetchone()[0]
    conn.close()
    return count > 0


# ---------------------------------------------------------------------------
# Demo seed  (historical data spread over last 7 days)
# ---------------------------------------------------------------------------

def seed_demo_data() -> None:
    if is_seeded():
        return

    now = datetime.utcnow()

    def ts(days_ago: float, hours: int = 0, minutes: int = 0) -> str:
        return (now - timedelta(days=days_ago, hours=hours, minutes=minutes)).isoformat(
            sep=" ", timespec="seconds"
        )

    ids: list[int] = []
    for i, (sku, name, cat, qty, price, loc) in enumerate(PRODUCTS):
        inv_id = insert_record(
            sku, name, cat, qty, price, loc,
            user=USERS[i % len(USERS)],
            ts=ts(7 - i * 0.4, hours=8 + (i * 3) % 9),
        )
        ids.append(inv_id)

    update_scenarios = [
        (ids[0],  {"Quantity": 175, "UnitPrice": 54.99},                6,  14, "admin"),
        (ids[1],  {"Quantity": 65,  "Location": "Warehouse A"},         5,  10, "batch_job"),
        (ids[2],  {"Quantity": 45,  "UnitPrice": 27.50},                5,   9, "app_user"),
        (ids[3],  {"Quantity": 30,  "UnitPrice": 94.99},                4,  11, "api_gateway"),
        (ids[4],  {"Quantity": 220},                                     4,   8, "batch_job"),
        (ids[5],  {"Quantity": 90,  "UnitPrice": 22.00},                3,  15, "admin"),
        (ids[7],  {"Quantity": 42,  "UnitPrice": 64.99},                3,  16, "app_user"),
        (ids[9],  {"Quantity": 480},                                     2,  14, "batch_job"),
        (ids[10], {"Quantity": 85,  "Location": "Warehouse B"},         2,   9, "api_gateway"),
        (ids[11], {"Quantity": 50,  "UnitPrice": 74.99},                1,  11, "admin"),
        (ids[0],  {"Quantity": 160},                                     1,  14, "batch_job"),
        (ids[3],  {"IsActive": 0},                                       1,   8, "admin"),
    ]
    for inv_id, fields, days, hours, user in update_scenarios:
        update_record(inv_id, user=user, ts=ts(days, hours=hours), **fields)

    for inv_id, days, hours, user in [
        (ids[12], 2, 16, "admin"),
        (ids[13], 1,  9, "migration_script"),
    ]:
        delete_record(inv_id, user=user, ts=ts(days, hours=hours))
