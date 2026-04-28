"""
log_viewer.py — Inventory_AuditLog viewer.

Two modes:
  1. CLI  : python3 log_viewer.py
  2. Web  : streamlit run log_viewer.py

Streamlit is detected automatically; if unavailable the script falls back
to a rich terminal table (or plain print).
"""
from __future__ import annotations

import json
import sys
from typing import Optional

from db_connect import get_connection

# ---------------------------------------------------------------------------
# Shared data fetch
# ---------------------------------------------------------------------------

def fetch_audit_logs(
    limit: int = 200,
    operation: Optional[str] = None,
    record_id: Optional[int] = None,
) -> list[dict]:
    """Return audit log rows as a list of dicts."""
    conn = get_connection()
    cur  = conn.cursor()

    where_clauses = []
    params: list = []

    if operation and operation != "ALL":
        where_clauses.append("Operation = ?")
        params.append(operation)
    if record_id is not None:
        where_clauses.append("RecordID = ?")
        params.append(record_id)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    cur.execute(f"""
        SELECT TOP {limit}
            AuditID,
            Operation,
            FORMAT(ChangedAt, 'yyyy-MM-dd HH:mm:ss') AS ChangedAt,
            ChangedBy,
            RecordID,
            BeforeData,
            AfterData
        FROM dbo.Inventory_AuditLog
        {where_sql}
        ORDER BY AuditID DESC
    """, *params)

    columns = [col[0] for col in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def _format_json(raw: Optional[str]) -> str:
    """Pretty-print a JSON string, or return '—' if empty."""
    if not raw:
        return "—"
    try:
        return json.dumps(json.loads(raw), indent=2)
    except (json.JSONDecodeError, TypeError):
        return raw or "—"


# ---------------------------------------------------------------------------
# Mode 1: Streamlit web UI
# ---------------------------------------------------------------------------

def run_streamlit() -> None:
    import streamlit as st

    st.set_page_config(page_title="Inventory Audit Log", layout="wide")
    st.title("Inventory Change Log")
    st.caption("Live view of dbo.Inventory_AuditLog")

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        op_filter = st.selectbox(
            "Operation", ["ALL", "INSERT", "UPDATE", "DELETE"]
        )
        record_id_filter = st.number_input(
            "RecordID (0 = all)", min_value=0, step=1, value=0
        )
        limit = st.slider("Max rows", 10, 500, 100)
        refresh = st.button("Refresh")

    rid = int(record_id_filter) if record_id_filter > 0 else None

    try:
        rows = fetch_audit_logs(
            limit=limit,
            operation=op_filter if op_filter != "ALL" else None,
            record_id=rid,
        )
    except Exception as exc:
        st.error(f"Connection error: {exc}")
        st.stop()

    if not rows:
        st.info("No audit records found for the current filter.")
        st.stop()

    # Metric row
    col1, col2, col3, col4 = st.columns(4)
    counts = {"INSERT": 0, "UPDATE": 0, "DELETE": 0}
    for r in rows:
        counts[r["Operation"]] = counts.get(r["Operation"], 0) + 1
    col1.metric("Total rows shown", len(rows))
    col2.metric("INSERTs", counts["INSERT"])
    col3.metric("UPDATEs", counts["UPDATE"])
    col4.metric("DELETEs", counts["DELETE"])

    st.divider()

    # Main table — expandable rows for JSON blobs
    for row in rows:
        op_color = {"INSERT": "green", "UPDATE": "orange", "DELETE": "red"}.get(
            row["Operation"], "gray"
        )
        with st.expander(
            f"#{row['AuditID']}  :{op_color}[{row['Operation']}]  "
            f"RecordID={row['RecordID']}  {row['ChangedAt']}  by {row['ChangedBy']}"
        ):
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Before")
                st.code(_format_json(row["BeforeData"]), language="json")
            with c2:
                st.subheader("After")
                st.code(_format_json(row["AfterData"]), language="json")


# ---------------------------------------------------------------------------
# Mode 2: CLI output
# ---------------------------------------------------------------------------

def run_cli() -> None:
    rows = fetch_audit_logs(limit=50)

    if not rows:
        print("No audit records found.")
        return

    # Try rich for a pretty table
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.text import Text

        console = Console()
        table = Table(
            title="Inventory_AuditLog (latest 50)",
            show_lines=True,
        )
        table.add_column("AuditID", style="dim", justify="right")
        table.add_column("Op",      style="bold")
        table.add_column("ChangedAt")
        table.add_column("ChangedBy")
        table.add_column("RecordID", justify="right")
        table.add_column("BeforeData (truncated)")
        table.add_column("AfterData (truncated)")

        op_styles = {"INSERT": "green", "UPDATE": "yellow", "DELETE": "red"}

        for r in rows:
            op_text = Text(r["Operation"], style=op_styles.get(r["Operation"], "white"))
            before = (r["BeforeData"] or "—")[:120]
            after  = (r["AfterData"]  or "—")[:120]
            table.add_row(
                str(r["AuditID"]),
                op_text,
                r["ChangedAt"],
                r["ChangedBy"],
                str(r["RecordID"] or ""),
                before,
                after,
            )

        console.print(table)

    except ImportError:
        # Plain fallback
        print(f"\n{'AuditID':<8} {'Op':<8} {'ChangedAt':<20} {'By':<20} {'RecordID':<10}")
        print("-" * 80)
        for r in rows:
            print(
                f"{r['AuditID']:<8} {r['Operation']:<8} "
                f"{r['ChangedAt']:<20} {r['ChangedBy']:<20} "
                f"{str(r['RecordID'] or ''):<10}"
            )
            if r["BeforeData"]:
                print(f"  BEFORE: {r['BeforeData'][:200]}")
            if r["AfterData"]:
                print(f"  AFTER : {r['AfterData'][:200]}")
            print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # When Streamlit runs this file it injects its own __streamlit__ marker
    try:
        import streamlit.runtime.scriptrunner  # noqa: F401
        run_streamlit()
    except ImportError:
        # Streamlit not installed — use CLI mode
        run_cli()
