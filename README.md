# DataPilot AI
<img width="2054" height="1604" alt="image" src="https://github.com/user-attachments/assets/4c1b4169-7c69-4949-a81c-556b87f3bc6c" />

DataPilot AI is a small local MVP that turns a natural-language question into read-only SQL, runs that SQL against PostgreSQL, and returns both the result rows and a short Turkish explanation.

This repository is a portfolio project for a Junior AI-Native Product Engineer role. It focuses on a working path from question to trusted database result, not on a full production platform.

## What it does

- Accepts a question in the Next.js workspace
- Sends the question to `POST /api/query`
- Uses Gemini to generate a single PostgreSQL `SELECT`
- Rejects write or schema-changing SQL before it reaches the database
- Executes only validated SQL against a local demo e-commerce schema
- Asks Gemini to explain the returned rows in 2–4 Turkish sentences
- Renders the generated SQL, a dynamic result table, and the explanation in the UI

The frontend never receives `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `DATABASE_URL`. It only calls the public API URL.

## Tech stack

| Area | Choice |
|---|---|
| API | FastAPI, Uvicorn, Pydantic Settings |
| Database | PostgreSQL, psycopg |
| SQL generation / explanation | Gemini (`gemini-3.5-flash-lite`) via the official `google-genai` SDK |
| Frontend | Next.js 15, React 19, TypeScript |
| Local demo data | Faker-based seeder |

An OpenAI client helper is still in the backend for comparison, but the live query path uses Gemini.

## Architecture

```text
User question
    → Next.js (http://127.0.0.1:3001)
    → POST /api/query
    → Gemini generates SQL
    → SQL security checks
    → PostgreSQL (read-only connection)
    → real rows
    → Gemini writes a short explanation from those rows
    → { question, sql, rows, explanation }
```

If explanation generation fails, the endpoint still returns the SQL and rows.

## SQL safety

Generated SQL is cleaned of markdown fences, then checked before execution. The runner also re-checks the same rules and opens a read-only connection.

Allowed:

- a single `SELECT` or `WITH ... SELECT`

Rejected:

- `INSERT`, `UPDATE`, `DELETE`
- `DROP`, `ALTER`, `CREATE`, `TRUNCATE`
- `GRANT`, `REVOKE`
- `SELECT INTO`
- multiple statements

Unsafe SQL is never sent to PostgreSQL.

## Database tables

The demo schema lives in `backend/app/db/schema.sql`:

| Table | Columns |
|---|---|
| `customers` | `id`, `name`, `email`, `city` |
| `products` | `id`, `name`, `category`, `price` |
| `orders` | `id`, `customer_id`, `order_date`, `total_amount` |
| `order_items` | `id`, `order_id`, `product_id`, `quantity`, `unit_price` |

Seed data is dummy e-commerce records (customers in several cities, a small catalog, and dated orders).

## Project layout

```text
datapilot-ai/
├── backend/
│   ├── app/
│   │   ├── api/query.py              # POST /api/query
│   │   ├── core/config.py            # settings from backend/.env
│   │   ├── core/gemini_client.py     # Gemini client + model name
│   │   ├── core/sql_generator.py     # NL → SQL + safety checks
│   │   ├── core/result_explainer.py  # rows → Turkish explanation
│   │   ├── db/schema.sql             # tables and indexes
│   │   ├── db/seed.py                # dummy data generator
│   │   ├── db/query_runner.py        # read-only SQL execution
│   │   └── main.py                   # FastAPI app, CORS, /health
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/                          # Next.js workspace UI
│   ├── .env.local.example
│   └── package.json
└── README.md
```

## Local setup

You need Python 3.11+, Node.js 20+, and a running local PostgreSQL instance.

### 1. Database

```powershell
psql -U postgres -c "CREATE USER datapilot WITH PASSWORD 'datapilot';"
psql -U postgres -c "CREATE DATABASE datapilot OWNER datapilot;"
```

From the `backend` folder:

```powershell
psql -U datapilot -d datapilot -f app/db/schema.sql
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and set real values for `DATABASE_URL` and `GEMINI_API_KEY`. Do not commit that file.

Seed the demo tables:

```powershell
python -m app.db.seed --reset
```

Start the API from the `backend` folder:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: `http://127.0.0.1:8000/health`

```json
{"status":"ok","service":"datapilot-ai-api"}
```

Swagger: `http://127.0.0.1:8000/docs`

### 3. Frontend

In a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

The dev script binds to `http://127.0.0.1:3001`. The API CORS allowlist matches that origin, so open that URL rather than `localhost:3000`.

## Environment variables

Copy the example files. Put secrets only in local ignored files.

`backend/.env.example`

```env
APP_NAME=DataPilot AI API
ENVIRONMENT=development
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
OPENAI_API_KEY=your_api_key_here
GEMINI_API_KEY=your_api_key_here
```

`frontend/.env.local.example`

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

`GEMINI_API_KEY` is required for SQL generation and explanations. `OPENAI_API_KEY` is reserved for the unused OpenAI helper. `NEXT_PUBLIC_API_BASE_URL` is the only frontend variable and is not a secret.

## Example questions

```text
Son 30 günde en çok satan 5 ürünü göster.
En pahalı 10 ürünü listele.
Şehir bazında kaç müşterimiz var?
```

Each request should return generated SQL, real PostgreSQL rows, and a short data-based explanation.

## API

`POST /api/query`

```json
{
  "question": "Son 30 günde en çok satan 5 ürünü göster."
}
```

```json
{
  "question": "...",
  "sql": "SELECT ...",
  "rows": [{ "...": "..." }],
  "explanation": "..."
}
```
