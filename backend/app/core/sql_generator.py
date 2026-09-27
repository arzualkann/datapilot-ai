"""Generate read-only SQL from a natural-language question via Gemini."""

import re

from google.genai import errors as genai_errors
from google.genai import types

from app.core.gemini_client import GEMINI_MODEL, get_gemini_client


SCHEMA_DESCRIPTION = """
customers(id, name, email, city)
products(id, name, category, price)
orders(id, customer_id, order_date, total_amount)
order_items(id, order_id, product_id, quantity, unit_price)
"""

SYSTEM_PROMPT = f"""You write PostgreSQL for a read-only analytics database.

Tables:
{SCHEMA_DESCRIPTION.strip()}

Rules:
- Reply with a single SQL statement only.
- Do not use markdown or code fences.
- Do not add explanations, comments, or extra text.
- Use only a single SELECT or WITH ... SELECT statement.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, REVOKE, or other write/DDL statements.
"""

FORBIDDEN_SQL_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
)
SQL_FENCE_PATTERN = re.compile(
    r"^```(?:sql)?\s*(.*?)\s*```$",
    re.IGNORECASE | re.DOTALL,
)


class SqlGenerationError(Exception):
    """Raised when the model cannot produce SQL."""


class UnsafeSqlError(Exception):
    """Raised when generated SQL is not a single read-only statement."""


def generate_sql(question: str) -> str:
    """Ask the model for SQL, strip fences, and reject write/DDL statements."""
    try:
        response = get_gemini_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0,
            ),
        )
    except genai_errors.APIError as exc:
        raise SqlGenerationError(_generation_error_message(exc)) from exc
    except RuntimeError as exc:
        raise SqlGenerationError("Gemini client is not configured.") from exc

    content = (getattr(response, "text", None) or "").strip()
    if not content:
        raise SqlGenerationError("The model returned an empty SQL response.")

    sql = strip_sql_fences(content)
    assert_readonly_sql(sql)
    return sql


def _generation_error_message(exc: Exception) -> str:
    details = str(exc).lower()
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 429 or "resource_exhausted" in details or "quota" in details:
        return "Gemini quota is exhausted."
    return "Gemini SQL generation failed."


def strip_sql_fences(text: str) -> str:
    sql = text.strip()
    fenced = SQL_FENCE_PATTERN.match(sql)
    if fenced:
        return fenced.group(1).strip()
    if sql.startswith("```"):
        lines = sql.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return sql


def assert_readonly_sql(sql: str) -> None:
    compact = sql.strip()
    if not compact:
        raise UnsafeSqlError("Generated SQL is empty.")

    normalized = strip_sql_comments(compact)
    body = normalized.rstrip().rstrip(";").strip()
    if not body:
        raise UnsafeSqlError("Generated SQL is empty.")
    if ";" in body:
        raise UnsafeSqlError("Only a single SQL statement is allowed.")

    upper = body.upper()
    for keyword in FORBIDDEN_SQL_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            raise UnsafeSqlError("Write or schema-changing SQL is not allowed.")

    if re.search(r"\bINTO\b", upper):
        raise UnsafeSqlError("SELECT INTO and other write targets are not allowed.")

    if not re.match(r"^(SELECT|WITH)\b", upper):
        raise UnsafeSqlError("Only read-only SELECT statements are allowed.")


def strip_sql_comments(sql: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", " ", without_blocks)
