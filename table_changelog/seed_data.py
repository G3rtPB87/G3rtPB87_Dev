"""
seed_data.py — Mock data generator.

Inserts 10 dummy Inventory records, updates 3 of them,
and deletes 1.  After each batch, prints a summary of
the resulting AuditLog rows so you can verify triggers fired.
"""
from __future__ import annotations

import random
from datetime import datetime

from db_connect import get_connection

# ---------------------------------------------------------------------------
# Dummy data
# ---------------------------------------------------------------------------

CATEGORIES = ["Electronics", "Clothing", "Food", "Hardware", "Office"]
LOCATIONS  = ["Warehouse A", "Warehouse B", "Store Front", "Cold Storage"]

PRODUCTS = [
    ("SKU-001", "Wireless Keyboard",     "Electronics", 150, 49.99),
    ("SKU-002", "USB-C Hub 7-Port",      "Electronics",  80, 34.95),
    ("SKU-003", "Standing Desk Mat",     "Office",        60, 29.00),
    ("SKU-004", "Noise Cancelling Buds", "Electronics",  40, 89.99),
    ("SKU-005", "Bamboo Notebook",       "Office",       200, 12.50),
    ("SKU-006", "Blue Light Glasses",    "Clothing",      75, 24.95),
    ("SKU-007", "Mechanical Pencil Set", "Office",       300,  8.75),
    ("SKU-008", "Portable Charger 20K",  "Electronics",  55, 59.99),
    ("SKU-009", "Cable Organiser Kit",   "Hardware",     120, 14.00),
    ("SKU-010", "Screen Cleaning Spray", "Hardware",     500,  6.50),
]


def _print_separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# INSERT 10 records
# ---------------------------------------------------------------------------

def insert_records(cursor) -> list[int]:
    """Insert 10 products and return their generated InventoryIDs."""
    inserted_ids: list[int] = []

    sql = """
        INSERT INTO dbo.Inventory
            (SKU, ProductName, Category, Quantity, UnitPrice, Location)
        OUTPUT INSERTED.InventoryID
        VALUES (?, ?, ?, ?, ?, ?)
    """

    for sku, name, cat, qty, price in PRODUCTS:
        loc = random.choice(LOCATIONS)
        cursor.execute(sql, sku, name, cat, qty, price, loc)
        row = cursor.fetchone()
        inserted_ids.append(row[0])
        print(f"  [INSERT] InventoryID={row[0]}  {sku}  '{name}'")

    return inserted_ids


# ---------------------------------------------------------------------------
# UPDATE 3 records
# ---------------------------------------------------------------------------

def update_records(cursor, ids: list[int]) -> None:
    """Apply price / quantity bumps to the first three inserted records."""
    updates = [
        (ids[0], 175, 54.99),
        (ids[2], 45,  27.50),
        (ids[5], 90,  22.00),
    ]
    sql = """
        UPDATE dbo.Inventory
        SET Quantity = ?, UnitPrice = ?, UpdatedAt = SYSUTCDATETIME()
        WHERE InventoryID = ?
    """
    for inv_id, new_qty, new_price in updates:
        cursor.execute(sql, new_qty, new_price, inv_id)
        print(f"  [UPDATE] InventoryID={inv_id}  Qty→{new_qty}  Price→{new_price}")


# ---------------------------------------------------------------------------
# DELETE 1 record
# ---------------------------------------------------------------------------

def delete_record(cursor, ids: list[int]) -> None:
    """Delete the last inserted record."""
    inv_id = ids[-1]
    cursor.execute("DELETE FROM dbo.Inventory WHERE InventoryID = ?", inv_id)
    print(f"  [DELETE] InventoryID={inv_id}")


# ---------------------------------------------------------------------------
# Verify: dump audit log counts
# ---------------------------------------------------------------------------

def show_audit_summary(cursor) -> None:
    cursor.execute("""
        SELECT Operation, COUNT(*) AS Cnt
        FROM dbo.Inventory_AuditLog
        GROUP BY Operation
        ORDER BY Operation
    """)
    rows = cursor.fetchall()
    print("\nAudit log summary:")
    for row in rows:
        print(f"  {row.Operation:<10} {row.Cnt} row(s)")

    cursor.execute("""
        SELECT TOP 5
            AuditID, Operation, ChangedBy,
            FORMAT(ChangedAt, 'yyyy-MM-dd HH:mm:ss') AS ChangedAt,
            RecordID
        FROM dbo.Inventory_AuditLog
        ORDER BY AuditID DESC
    """)
    rows = cursor.fetchall()
    print("\nMost recent 5 audit entries:")
    for r in rows:
        print(
            f"  #{r.AuditID:<5} {r.Operation:<8} "
            f"RecordID={r.RecordID}  at {r.ChangedAt}  by {r.ChangedBy}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    conn = get_connection()
    cur  = conn.cursor()

    try:
        _print_separator("Step 1 — Inserting 10 records")
        ids = insert_records(cur)

        _print_separator("Step 2 — Updating 3 records")
        update_records(cur, ids)

        _print_separator("Step 3 — Deleting 1 record")
        delete_record(cur, ids)

        conn.commit()
        _print_separator("Step 4 — Audit log verification")
        show_audit_summary(cur)

    except Exception as exc:
        conn.rollback()
        raise exc
    finally:
        cur.close()
        conn.close()

    print("\nDone. Run log_viewer.py (or streamlit run log_viewer.py) to inspect the full log.\n")


if __name__ == "__main__":
    run()
