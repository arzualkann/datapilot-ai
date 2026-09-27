"""Read-only database queries used by the HTTP API."""

from datetime import date, datetime
from decimal import Decimal

from psycopg import connect
from psycopg.rows import dict_row

from app.core.sql_generator import assert_readonly_sql


def fetch_query_rows(database_url: str, sql: str) -> list[dict[str, object]]:
    """Execute a validated read-only SELECT and return JSON-safe rows."""
    assert_readonly_sql(sql)

    with connect(database_url, row_factory=dict_row, connect_timeout=5) as connection:
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

    return [serialize_row(row) for row in rows]


def serialize_row(row: dict[str, object]) -> dict[str, object]:
    return {as_text(key): serialize_value(value) for key, value in row.items()}


def serialize_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8")
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return as_text(value)


def as_text(value: object) -> str:
    """Decode PostgreSQL SQL_ASCII/unknown text values that arrive as bytes."""
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8")
    return str(value)
