"""Explain PostgreSQL result rows in Turkish via Gemini."""

import json
import logging

from google.genai import errors as genai_errors
from google.genai import types

from app.core.gemini_client import GEMINI_MODEL, get_gemini_client


logger = logging.getLogger(__name__)

EMPTY_RESULT_EXPLANATION = "Bu soruya uygun kayıt bulunamadı."
FALLBACK_EXPLANATION = "Sorgu çalıştırıldı ve sonuçlar listelenmiştir."

SYSTEM_PROMPT = """Sen bir veri analisti asistanısın.

Kurallar:
- Yalnızca Türkçe yaz.
- 2 ile 4 cümle arasında, kısa ve kullanıcı dostu bir açıklama üret.
- Yalnızca verilen soruya, kolonlara ve satırlara dayan.
- Veride olmayan sayı, ürün, şehir veya yorum uydurma.
- Markdown, başlık veya madde işareti kullanma.
"""


def explain_rows(question: str, rows: list[dict[str, object]]) -> str:
    """Return a short Turkish explanation of the result rows."""
    if not rows:
        return EMPTY_RESULT_EXPLANATION

    try:
        response = get_gemini_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=_user_prompt(question, rows),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0,
            ),
        )
    except (genai_errors.APIError, RuntimeError):
        logger.error("Gemini could not explain the query result.")
        return FALLBACK_EXPLANATION

    explanation = (getattr(response, "text", None) or "").strip()
    if not explanation:
        return FALLBACK_EXPLANATION
    return explanation


def _user_prompt(question: str, rows: list[dict[str, object]]) -> str:
    columns = list(rows[0].keys())
    payload = {
        "question": question,
        "columns": columns,
        "row_count": len(rows),
        "rows": rows,
    }
    return (
        "Kullanıcının sorusu ve PostgreSQL sonucu aşağıdadır. "
        "Yalnızca bu JSON içindeki verilere dayanarak kısa bir Türkçe açıklama yaz.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, default=str)}"
    )
