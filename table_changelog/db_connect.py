"""
db_connect.py — SQL Server connection helpers.

Reads connection parameters exclusively from environment variables
(or a .env file via python-dotenv if present).

Supports both pyodbc (direct) and SQLAlchemy (ORM / pandas).
"""
from __future__ import annotations

import os
import urllib.parse

# Load .env file if present (python-dotenv is optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pyodbc
from typing import Optional


# ---------------------------------------------------------------------------
# Build connection string from environment variables
# ---------------------------------------------------------------------------

def _get_env(key: str, default: Optional[str] = None) -> str:
    value = os.environ.get(key, default)
    if value is None:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Copy .env.example to .env and fill in your credentials."
        )
    return value


def build_connection_string() -> str:
    """Return an ODBC connection string built from env vars."""
    server   = _get_env("DB_SERVER")
    database = _get_env("DB_DATABASE")
    uid      = _get_env("DB_UID")
    pwd      = _get_env("DB_PWD")
    driver   = _get_env("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    azure    = _get_env("DB_AZURE", "0") == "1"

    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        f"UID={uid}",
        f"PWD={pwd}",
    ]

    if azure:
        parts += ["Encrypt=yes", "TrustServerCertificate=no"]
    else:
        # Local / Express — trust the cert or use no encryption
        parts += ["TrustServerCertificate=yes"]

    return ";".join(parts)


# ---------------------------------------------------------------------------
# pyodbc connection
# ---------------------------------------------------------------------------

def get_connection() -> pyodbc.Connection:
    """Return a live pyodbc connection. Caller is responsible for closing."""
    conn_str = build_connection_string()
    conn = pyodbc.connect(conn_str, autocommit=False)
    conn.setdecoding(pyodbc.SQL_CHAR, encoding="utf-8")
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding="utf-8")
    conn.setencoding(encoding="utf-8")
    return conn


# ---------------------------------------------------------------------------
# SQLAlchemy engine (optional — only used if sqlalchemy is installed)
# ---------------------------------------------------------------------------

def get_sqlalchemy_engine():
    """Return a SQLAlchemy Engine. Requires sqlalchemy + pyodbc."""
    try:
        from sqlalchemy import create_engine
    except ImportError:
        raise ImportError("Install sqlalchemy: pip3 install sqlalchemy")

    server   = _get_env("DB_SERVER")
    database = _get_env("DB_DATABASE")
    uid      = _get_env("DB_UID")
    pwd      = _get_env("DB_PWD")
    driver   = _get_env("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    azure    = _get_env("DB_AZURE", "0") == "1"

    extra = "Encrypt=yes&TrustServerCertificate=no" if azure else "TrustServerCertificate=yes"
    odbc_str = (
        f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
        f"UID={uid};PWD={pwd};{extra}"
    )
    encoded = urllib.parse.quote_plus(odbc_str)
    url = f"mssql+pyodbc:///?odbc_connect={encoded}"
    return create_engine(url, fast_executemany=True)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Testing connection …")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION AS version")
        row = cursor.fetchone()
        print(f"Connected!\nSQL Server version:\n{row.version}")
