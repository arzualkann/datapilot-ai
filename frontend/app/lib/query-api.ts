export type QueryCell = string | number | boolean | null;
export type QueryRow = Record<string, QueryCell>;

export type QueryResponse = {
  question: string;
  sql: string;
  rows: QueryRow[];
  explanation: string;
};

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function analyzeQuestion(question: string): Promise<QueryResponse> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
  } catch {
    throw new Error("Backend'e ulaşılamadı. FastAPI sunucusunun çalıştığını kontrol edin.");
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    throw new Error(readErrorDetail(payload?.detail) ?? `İstek başarısız oldu (${response.status}).`);
  }

  const body = (await response.json()) as QueryResponse;

  return {
    question: typeof body.question === "string" ? body.question : question,
    sql: typeof body.sql === "string" ? body.sql : "",
    rows: Array.isArray(body.rows) ? body.rows.filter(isQueryRow) : [],
    explanation: typeof body.explanation === "string" ? body.explanation : "",
  };
}

function isQueryRow(value: unknown): value is QueryRow {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function readErrorDetail(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") {
          return item.msg;
        }
        return null;
      })
      .filter((item): item is string => Boolean(item));

    return messages[0] ?? null;
  }

  return null;
}
