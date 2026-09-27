import logging

from fastapi import APIRouter, HTTPException, status
from psycopg import Error, OperationalError
from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.core.result_explainer import explain_rows
from app.core.sql_generator import SqlGenerationError, UnsafeSqlError, generate_sql
from app.db.query_runner import fetch_query_rows


router = APIRouter(tags=["query"])
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        question = value.strip()
        if not question:
            raise ValueError("question cannot be empty")
        return question


class QueryResponse(BaseModel):
    question: str
    sql: str
    rows: list[dict[str, object]]
    explanation: str


@router.post("/query", response_model=QueryResponse)
def query_database(request: QueryRequest) -> QueryResponse:
    """Generate SQL from the question, validate it, then run it read-only."""
    try:
        sql = generate_sql(request.question)
    except UnsafeSqlError:
        logger.warning("Generated SQL failed the read-only safety check.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Üretilen SQL güvenli değil. Yalnızca okuma sorgularına izin verilir.",
        ) from None
    except SqlGenerationError as exc:
        logger.error("SQL could not be generated from the question.")
        detail = (
            "SQL üretilemedi. Gemini kotası yetersiz."
            if "quota" in str(exc).lower()
            else "SQL üretilemedi. Gemini bağlantısını kontrol edin."
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from None

    try:
        rows = fetch_query_rows(get_settings().database_url, sql)
    except UnsafeSqlError:
        logger.warning("Generated SQL failed the read-only safety check before execution.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Üretilen SQL güvenli değil. Yalnızca okuma sorgularına izin verilir.",
        ) from None
    except OperationalError:
        logger.error("PostgreSQL was unreachable while executing generated SQL.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Veritabanına bağlanılamadı. PostgreSQL bağlantısını kontrol edin.",
        ) from None
    except Error:
        logger.error("Generated SQL could not be executed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Üretilen SQL çalıştırılamadı. Sorguyu kontrol edin.",
        ) from None

    return QueryResponse(
        question=request.question,
        sql=sql,
        rows=rows,
        explanation=explain_rows(request.question, rows),
    )
