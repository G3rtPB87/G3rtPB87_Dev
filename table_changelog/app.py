"""
app.py — Table Change Log — Streamlit UI

Run:
    streamlit run app.py
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

import demo_db

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Table Change Log",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
/* Operation badges */
.badge {
    display: inline-block;
    border-radius: 5px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
}
.badge-INSERT { background:#d1fae5; color:#065f46; }
.badge-UPDATE { background:#fef3c7; color:#92400e; }
.badge-DELETE { background:#fee2e2; color:#991b1b; }

/* Diff table */
.diff-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    margin: 6px 0 12px 0;
}
.diff-table th {
    background: #f9fafb;
    padding: 6px 10px;
    text-align: left;
    font-size: 11px;
    color: #6b7280;
    border-bottom: 2px solid #e5e7eb;
}
.diff-table td {
    padding: 6px 10px;
    border-bottom: 1px solid #f3f4f6;
    vertical-align: top;
}
.diff-field  { font-weight: 600; color: #374151; }
.diff-before { color: #ef4444; text-decoration: line-through; font-family: monospace; }
.diff-after  { color: #10b981; font-weight: 600; font-family: monospace; }
.diff-arrow  { color: #9ca3af; }

/* Subtle JSON caption */
.json-label {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

/* Feed item */
.feed-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 7px 0;
    border-bottom: 1px solid #f3f4f6;
    font-size: 13px;
}
.feed-meta { color: #6b7280; font-size: 12px; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def badge(op: str) -> str:
    return f'<span class="badge badge-{op}">{op}</span>'


def parse_json(s: Optional[str]) -> dict:
    if not s:
        return {}
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return {}


def diff_html(before: dict, after: dict) -> str:
    rows = []
    for k in sorted(set(before) | set(after)):
        bv = before.get(k)
        av = after.get(k)
        if bv != av:
            rows.append(
                f"<tr>"
                f"<td class='diff-field'>{k}</td>"
                f"<td class='diff-before'>{bv}</td>"
                f"<td class='diff-arrow'>→</td>"
                f"<td class='diff-after'>{av}</td>"
                f"</tr>"
            )
    if not rows:
        return ""
    return (
        "<table class='diff-table'>"
        "<tr><th>Field</th><th>Before</th><th></th><th>After</th></tr>"
        + "".join(rows)
        + "</table>"
    )


# ---------------------------------------------------------------------------
# Boot: init DB once per session
# ---------------------------------------------------------------------------

@st.cache_resource
def _boot():
    demo_db.init_database()
    demo_db.seed_demo_data()
    return True

_boot()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 📋 Change Log")
    st.caption("Table Audit System")
    st.divider()

    page = st.radio(
        "nav",
        ["📊 Dashboard", "🔍 Audit Log", "📦 Inventory", "⚡ Operations", "⚙️ Configuration"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Running in **Demo Mode** (SQLite)")
    if st.button("↺ Reset demo data", use_container_width=True):
        demo_db.reset_database()
        demo_db.init_database()
        demo_db.seed_demo_data()
        st.cache_resource.clear()
        st.rerun()


# ===========================================================================
# PAGE: Dashboard
# ===========================================================================

def page_dashboard() -> None:
    st.title("📊 Dashboard")
    st.caption("Real-time summary of all tracked table changes")

    stats = demo_db.get_audit_stats()
    by_op = stats["by_operation"]

    # --- Metric row 1: audit counts ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Changes",    stats["total_audit_entries"])
    c2.metric("INSERTs",          by_op.get("INSERT", 0))
    c3.metric("UPDATEs",          by_op.get("UPDATE", 0))
    c4.metric("DELETEs",          by_op.get("DELETE", 0))

    # --- Metric row 2: inventory health ---
    c5, c6, _, _ = st.columns(4)
    c5.metric("Active SKUs",      stats["active_items"])
    c6.metric("Stock Value",      f"${stats['total_inventory_value']:,.2f}")

    st.divider()

    col_main, col_side = st.columns([3, 2])

    # Stacked bar — changes over last 7 days
    with col_main:
        timeline = stats["timeline"]
        if timeline:
            df_tl = pd.DataFrame(timeline)
            fig = px.bar(
                df_tl,
                x="day", y="count", color="operation",
                barmode="stack",
                color_discrete_map={
                    "INSERT": "#10b981",
                    "UPDATE": "#f59e0b",
                    "DELETE": "#ef4444",
                },
                labels={"day": "Date", "count": "Changes", "operation": "Operation"},
                title="Changes over the last 7 days",
            )
            fig.update_layout(
                height=310, margin=dict(l=0, r=0, t=48, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor="#f3f4f6", zeroline=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data yet.")

    # Donut — operation mix
    with col_side:
        if by_op:
            df_op = pd.DataFrame(
                [{"Operation": k, "Count": v} for k, v in by_op.items()]
            )
            fig2 = px.pie(
                df_op, values="Count", names="Operation",
                hole=0.5,
                color="Operation",
                color_discrete_map={
                    "INSERT": "#10b981",
                    "UPDATE": "#f59e0b",
                    "DELETE": "#ef4444",
                },
                title="Operation mix",
            )
            fig2.update_traces(textposition="outside", textinfo="percent+label")
            fig2.update_layout(
                height=310, showlegend=False,
                margin=dict(l=0, r=0, t=48, b=0),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Top users
    if stats["by_user"]:
        df_u = pd.DataFrame(stats["by_user"])
        fig3 = px.bar(
            df_u, x="count", y="user", orientation="h",
            color_discrete_sequence=["#6366f1"],
            labels={"count": "Changes", "user": ""},
            title="Top users by change count",
        )
        fig3.update_layout(
            height=230, margin=dict(l=0, r=0, t=48, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(categoryorder="total ascending"),
        )
        fig3.update_xaxes(showgrid=True, gridcolor="#f3f4f6")
        fig3.update_yaxes(showgrid=False)
        st.plotly_chart(fig3, use_container_width=True)

    # Recent activity feed
    st.subheader("Recent activity")
    recent = demo_db.get_audit_logs(limit=10)
    for row in recent:
        data = parse_json(row["AfterData"]) or parse_json(row["BeforeData"])
        sku  = data.get("SKU", "")
        name = data.get("ProductName", "")
        st.markdown(
            f"<div class='feed-row'>"
            f"  {badge(row['Operation'])}"
            f"  <span><strong>{sku}</strong> {name}</span>"
            f"  <span class='feed-meta'>ID {row['RecordID']} &nbsp;·&nbsp; "
            f"{row['ChangedAt']} &nbsp;·&nbsp; {row['ChangedBy']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ===========================================================================
# PAGE: Audit Log
# ===========================================================================

def page_audit_log() -> None:
    st.title("🔍 Audit Log")
    st.caption("Complete history of every tracked change — expandable Before/After snapshots and field-level diffs")

    # Filters
    with st.container():
        fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
        op_filter  = fc1.selectbox("Operation", ["All", "INSERT", "UPDATE", "DELETE"])
        search     = fc2.text_input("Search", placeholder="SKU, user, keyword…")
        rec_id_raw = fc3.text_input("Record ID", placeholder="Leave blank for all")
        limit      = fc4.slider("Max rows", 10, 200, 60, step=10)

    op     = None if op_filter == "All" else op_filter
    rec_id = int(rec_id_raw) if rec_id_raw.strip().isdigit() else None
    rows   = demo_db.get_audit_logs(
        limit=limit, operation=op,
        record_id=rec_id, search=search or None,
    )

    if not rows:
        st.info("No records match the current filters.")
        return

    # Summary row
    counts = {"INSERT": 0, "UPDATE": 0, "DELETE": 0}
    for r in rows:
        counts[r["Operation"]] += 1

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Showing",  len(rows))
    m2.metric("INSERTs",  counts["INSERT"])
    m3.metric("UPDATEs",  counts["UPDATE"])
    m4.metric("DELETEs",  counts["DELETE"])

    # CSV export
    csv = pd.DataFrame(rows).to_csv(index=False)
    m5.download_button("⬇ Export CSV", csv, "audit_log.csv", "text/csv")

    st.divider()

    # Rows
    for row in rows:
        before = parse_json(row["BeforeData"])
        after  = parse_json(row["AfterData"])
        data   = after or before
        sku    = data.get("SKU", "")
        name   = data.get("ProductName", "")

        label = (
            f"#{row['AuditID']}  ·  {row['Operation']}  ·  "
            f"{sku}  {name}  ·  {row['ChangedAt']}  ·  {row['ChangedBy']}"
        )

        with st.expander(label, expanded=False):
            st.markdown(
                f"{badge(row['Operation'])} &nbsp; "
                f"<strong>#{row['AuditID']}</strong> &nbsp; "
                f"<code>{sku}</code> {name} &nbsp; "
                f"<span style='color:#6b7280;font-size:12px'>"
                f"RecordID&nbsp;{row['RecordID']} &nbsp;·&nbsp; "
                f"{row['ChangedAt']} &nbsp;·&nbsp; {row['ChangedBy']}"
                f"</span>",
                unsafe_allow_html=True,
            )

            # Field-level diff for UPDATE
            if row["Operation"] == "UPDATE" and before and after:
                html = diff_html(before, after)
                if html:
                    st.markdown("**Field-level diff**")
                    st.markdown(html, unsafe_allow_html=True)

            # Before / After JSON
            col_b, col_a = st.columns(2)
            with col_b:
                st.markdown("<div class='json-label'>Before</div>", unsafe_allow_html=True)
                if before:
                    st.json(before, expanded=False)
                else:
                    st.markdown(
                        "<span style='color:#9ca3af;font-style:italic;font-size:13px'>— none —</span>",
                        unsafe_allow_html=True,
                    )
            with col_a:
                st.markdown("<div class='json-label'>After</div>", unsafe_allow_html=True)
                if after:
                    st.json(after, expanded=False)
                else:
                    st.markdown(
                        "<span style='color:#9ca3af;font-style:italic;font-size:13px'>— none —</span>",
                        unsafe_allow_html=True,
                    )


# ===========================================================================
# PAGE: Inventory
# ===========================================================================

def page_inventory() -> None:
    st.title("📦 Inventory")
    st.caption("Current live state of the Inventory table")

    items = demo_db.get_inventory()
    if not items:
        st.info("No inventory records found.")
        return

    df      = pd.DataFrame(items)
    active  = df[df["IsActive"] == 1]
    total_v = (active["Quantity"] * active["UnitPrice"]).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total SKUs",   len(df))
    c2.metric("Active",       len(active))
    c3.metric("Total Units",  int(active["Quantity"].sum()))
    c4.metric("Stock Value",  f"${total_v:,.2f}")

    st.divider()

    search = st.text_input(
        "Search", placeholder="Name, SKU, category, location…",
        label_visibility="collapsed",
    )
    if search:
        mask = df.apply(lambda r: search.lower() in str(r.values).lower(), axis=1)
        df   = df[mask]

    display = df[[
        "InventoryID", "SKU", "ProductName", "Category",
        "Quantity", "UnitPrice", "Location", "IsActive", "UpdatedAt",
    ]].copy()
    display["UnitPrice"] = display["UnitPrice"].map("${:.2f}".format)
    display["IsActive"]  = display["IsActive"].map({1: "✅", 0: "❌"})
    display.columns = [
        "ID", "SKU", "Product Name", "Category",
        "Qty", "Unit Price", "Location", "Active", "Updated At",
    ]
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.divider()
    if len(active) >= 2:
        cat = (
            active.assign(value=active["Quantity"] * active["UnitPrice"])
            .groupby("Category")["value"].sum()
            .reset_index()
            .rename(columns={"value": "Stock Value ($)"})
        )
        fig = px.bar(
            cat, x="Category", y="Stock Value ($)",
            color="Category",
            title="Stock value by category",
        )
        fig.update_layout(
            height=270, showlegend=False,
            margin=dict(l=0, r=0, t=48, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_yaxes(gridcolor="#f3f4f6")
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)


# ===========================================================================
# PAGE: Operations
# ===========================================================================

def page_operations() -> None:
    st.title("⚡ Operations")
    st.caption("INSERT, UPDATE, and DELETE records — every action is captured in the audit log")

    items        = demo_db.get_inventory()
    item_options = {
        f"#{r['InventoryID']}  {r['SKU']}  —  {r['ProductName']}": r["InventoryID"]
        for r in items
    }

    tab_ins, tab_upd, tab_del = st.tabs(["➕ Insert", "✏️ Update", "🗑️ Delete"])

    # ---- INSERT ----
    with tab_ins:
        st.subheader("Insert a new product")
        with st.form("form_insert"):
            c1, c2 = st.columns(2)
            sku          = c1.text_input("SKU *",          placeholder="SKU-099")
            product_name = c2.text_input("Product Name *", placeholder="My Product")
            category     = c1.selectbox(
                "Category",
                ["Electronics", "Office", "Hardware", "Clothing", "Food", "Other"],
            )
            location = c2.selectbox(
                "Location",
                ["Warehouse A", "Warehouse B", "Store Front", "Cold Storage"],
            )
            quantity   = c1.number_input("Quantity",      min_value=0, value=50, step=1)
            unit_price = c2.number_input("Unit Price ($)", min_value=0.0, value=19.99,
                                         step=0.01, format="%.2f")
            ins_user   = st.text_input("User", value="app_user")
            go         = st.form_submit_button("Insert record", type="primary")

        if go:
            if not sku.strip() or not product_name.strip():
                st.error("SKU and Product Name are required.")
            else:
                try:
                    inv_id = demo_db.insert_record(
                        sku.strip(), product_name.strip(), category,
                        int(quantity), float(unit_price), location, user=ins_user,
                    )
                    st.success(f"Inserted InventoryID = {inv_id}")
                    log = demo_db.get_audit_logs(limit=1, operation="INSERT", record_id=inv_id)
                    if log:
                        with st.expander("Audit log entry", expanded=True):
                            st.json(parse_json(log[0]["AfterData"]))
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")

    # ---- UPDATE ----
    with tab_upd:
        st.subheader("Update an existing product")
        if not item_options:
            st.info("No records available.")
        else:
            sel_label = st.selectbox("Select record", list(item_options.keys()), key="upd_sel")
            inv_id    = item_options[sel_label]
            current   = next((r for r in items if r["InventoryID"] == inv_id), None)

            if current:
                with st.expander("Current values", expanded=True):
                    st.json({
                        k: current[k]
                        for k in ["SKU", "ProductName", "Category",
                                  "Quantity", "UnitPrice", "Location", "IsActive"]
                    })

            with st.form("form_update"):
                st.caption("Tick the fields you want to change:")
                c1, c2 = st.columns(2)

                chk_qty    = c1.checkbox("Quantity")
                new_qty    = c1.number_input(
                    "New Quantity", min_value=0,
                    value=int(current["Quantity"]) if current else 0,
                )
                chk_price  = c2.checkbox("Unit Price")
                new_price  = c2.number_input(
                    "New Unit Price ($)", min_value=0.0,
                    value=float(current["UnitPrice"]) if current else 0.0,
                    format="%.2f",
                )
                chk_loc    = c1.checkbox("Location")
                new_loc    = c1.selectbox(
                    "New Location",
                    ["Warehouse A", "Warehouse B", "Store Front", "Cold Storage"],
                )
                chk_active = c2.checkbox("Is Active")
                new_active = c2.radio(
                    "Is Active", [1, 0],
                    format_func=lambda x: "Active" if x else "Inactive",
                    horizontal=True,
                )
                upd_user = st.text_input("User", value="admin", key="upd_user")
                go_upd   = st.form_submit_button("Apply update", type="primary")

            if go_upd:
                kwargs: dict[str, Any] = {}
                if chk_qty:    kwargs["Quantity"]  = int(new_qty)
                if chk_price:  kwargs["UnitPrice"]  = float(new_price)
                if chk_loc:    kwargs["Location"]   = new_loc
                if chk_active: kwargs["IsActive"]   = int(new_active)

                if not kwargs:
                    st.warning("Tick at least one field to update.")
                else:
                    try:
                        demo_db.update_record(inv_id, user=upd_user, **kwargs)
                        st.success(f"Updated InventoryID = {inv_id}")
                        log = demo_db.get_audit_logs(limit=1, operation="UPDATE", record_id=inv_id)
                        if log:
                            with st.expander("Audit log entry — field diff", expanded=True):
                                b = parse_json(log[0]["BeforeData"])
                                a = parse_json(log[0]["AfterData"])
                                html = diff_html(b, a)
                                if html:
                                    st.markdown(html, unsafe_allow_html=True)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error: {exc}")

    # ---- DELETE ----
    with tab_del:
        st.subheader("Delete a product")
        if not item_options:
            st.info("No records available.")
        else:
            del_label = st.selectbox("Select record", list(item_options.keys()), key="del_sel")
            del_id    = item_options[del_label]
            target    = next((r for r in items if r["InventoryID"] == del_id), None)

            if target:
                st.warning("This row will be permanently removed:")
                st.json({
                    k: target[k]
                    for k in ["SKU", "ProductName", "Category", "Quantity", "UnitPrice"]
                })

            del_user = st.text_input("User", value="admin", key="del_user")
            confirm  = st.checkbox(f"I confirm deletion of record #{del_id}")
            go_del   = st.button("Delete record", type="primary", disabled=not confirm)

            if go_del:
                try:
                    demo_db.delete_record(del_id, user=del_user)
                    st.success(f"Deleted InventoryID = {del_id}")
                    log = demo_db.get_audit_logs(limit=1, operation="DELETE", record_id=del_id)
                    if log:
                        with st.expander("Audit log entry — deleted snapshot", expanded=True):
                            st.json(parse_json(log[0]["BeforeData"]))
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error: {exc}")


# ===========================================================================
# PAGE: Configuration
# ===========================================================================

def page_configuration() -> None:
    st.title("⚙️ Configuration")
    st.caption("Manage database connection settings and demo data")

    tab_live, tab_demo, tab_schema = st.tabs(
        ["🔴 Live SQL Server", "🟢 Demo Mode (SQLite)", "📄 Schema"]
    )

    # ---- Live SQL Server ----
    with tab_live:
        st.subheader("SQL Server connection")
        st.info(
            "Settings are persisted to a `.env` file. "
            "**Never commit `.env` to source control.**",
            icon="ℹ️",
        )

        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        env: dict[str, str] = {}
        if os.path.exists(env_path):
            with open(env_path) as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        env[k.strip()] = v.strip()

        DRIVERS = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server",
        ]
        driver_default = env.get("DB_DRIVER", DRIVERS[1])
        driver_idx     = DRIVERS.index(driver_default) if driver_default in DRIVERS else 1

        with st.form("form_config"):
            c1, c2 = st.columns(2)
            server   = c1.text_input("DB_SERVER",   value=env.get("DB_SERVER",   r"localhost\SQLEXPRESS"))
            database = c2.text_input("DB_DATABASE", value=env.get("DB_DATABASE", "InventoryDB"))
            uid      = c1.text_input("DB_UID",      value=env.get("DB_UID",      "sa"))
            pwd      = c2.text_input("DB_PWD",      value=env.get("DB_PWD",      ""), type="password")
            driver   = st.selectbox("DB_DRIVER", DRIVERS, index=driver_idx)
            azure    = st.checkbox(
                "Azure SQL  (enables Encrypt=yes; TrustServerCertificate=no)",
                value=env.get("DB_AZURE", "0") == "1",
            )
            save = st.form_submit_button("💾 Save to .env", type="primary")

        if save:
            content = "\n".join([
                "# Auto-generated by Table Change Log app",
                f"DB_SERVER={server}",
                f"DB_DATABASE={database}",
                f"DB_UID={uid}",
                f"DB_PWD={pwd}",
                f"DB_DRIVER={driver}",
                f"DB_AZURE={'1' if azure else '0'}",
            ]) + "\n"
            with open(env_path, "w") as fh:
                fh.write(content)
            st.success(f"Saved to `{env_path}`")

        st.divider()
        st.subheader("Test connection")
        if st.button("🔌 Test connection"):
            try:
                import pyodbc               # noqa: F401
                from db_connect import get_connection
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute("SELECT @@VERSION AS v")
                ver = cur.fetchone()[0]
                conn.close()
                st.success(f"Connected!\n```\n{ver[:160]}\n```")
            except ImportError:
                st.warning("**pyodbc not installed.**  Run: `pip3 install pyodbc`")
            except Exception as exc:
                st.error(f"Connection failed: {exc}")

    # ---- Demo mode ----
    with tab_demo:
        st.subheader("Demo Mode (SQLite)")
        st.success("Currently active — all data uses a local SQLite file.", icon="✅")

        conn = demo_db.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Inventory")
        n_inv = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM Inventory_AuditLog")
        n_log = cur.fetchone()[0]
        cur.execute("SELECT MIN(ChangedAt), MAX(ChangedAt) FROM Inventory_AuditLog")
        rng = cur.fetchone()
        conn.close()

        c1, c2 = st.columns(2)
        c1.metric("Inventory records",    n_inv)
        c2.metric("Audit log entries",    n_log)
        if rng and rng[0]:
            st.caption(f"Date range: `{rng[0]}` → `{rng[1]}`")

        st.divider()
        st.markdown("**SQLite database path**")
        st.code(demo_db.DB_PATH)

        if st.button("🔄 Reset & re-seed demo data", type="secondary"):
            demo_db.reset_database()
            demo_db.init_database()
            demo_db.seed_demo_data()
            st.cache_resource.clear()
            st.success("Demo data has been reset and re-seeded.")
            st.rerun()

    # ---- Schema viewer ----
    with tab_schema:
        st.subheader("T-SQL Schema")
        st.markdown(
            "Run [schema.sql](schema.sql) against your SQL Server instance to create "
            "the `Inventory` table, `Inventory_AuditLog` shadow table, and the audit trigger."
        )
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path) as fh:
                sql = fh.read()
            st.code(sql, language="sql")
        else:
            st.warning("`schema.sql` not found.")


# ===========================================================================
# Router
# ===========================================================================

if page == "📊 Dashboard":
    page_dashboard()
elif page == "🔍 Audit Log":
    page_audit_log()
elif page == "📦 Inventory":
    page_inventory()
elif page == "⚡ Operations":
    page_operations()
elif page == "⚙️ Configuration":
    page_configuration()
