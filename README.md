# Bookstore Inventory API

A production-oriented REST API for managing bookstore authors, books, and
inventory stock. The API is built with FastAPI and SQLModel and uses PostgreSQL
for persistent storage.

## Features

- Author CRUD operations
- Book CRUD operations
- Author and ISBN uniqueness checks
- Input validation for names, titles, ISBNs, prices, stock, and IDs
- Dedicated stock adjustment endpoint
- PostgreSQL row locking for stock adjustments
- Consistent JSON error responses
- Liveness and database readiness endpoints
- Alembic database migrations
- Pytest API integration tests
- Docker image with a non-root runtime user

## Technology Stack

- Python 3.12+
- FastAPI
- SQLModel
- SQLAlchemy
- PostgreSQL
- Psycopg 3
- Alembic
- Pydantic Settings
- Pytest and HTTPX
- Docker

## Project Structure

```text
app/
├── api/routes/       # FastAPI route handlers
├── core/             # Settings, logging, and exception handling
├── db/               # Database engine and session dependency
├── models/           # SQLModel tables and API schemas
├── services/         # Business logic and database operations
└── main.py           # FastAPI application entry point
alembic/              # Database migration environment and revisions
tests/                # API integration tests
Dockerfile            # Production container image
pytest.ini            # Pytest configuration
```

## Requirements

- Python 3.12 or newer
- PostgreSQL database
- Git
- Docker Desktop (optional, for containerized execution)

## Configuration

The application reads configuration from environment variables and a local
`.env` file. `.env` is ignored by Git and must never be committed.

Minimum configuration:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

Optional configuration:

```dotenv
APP_NAME=Bookstore Inventory API
ENVIRONMENT=development
LOG_LEVEL=INFO
API_KEY=replace-with-a-long-random-api-key
MIGRATION_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@DIRECT_HOST/DATABASE?sslmode=require
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=300
DB_CONNECT_TIMEOUT=10
```

`DATABASE_URL` is used by normal API requests. If
`MIGRATION_DATABASE_URL` is set, Alembic uses it for migrations; otherwise
Alembic falls back to `DATABASE_URL`.

Author and book routes require the `X-API-Key` request header. Set `API_KEY`
to a long random value before starting the application. Health endpoints
remain public so deployment platforms can check liveness and readiness.

Do not paste database credentials into source code, commit them, or include
them in bug reports and screenshots.

## Local Setup

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `.env` in the project root and configure a valid PostgreSQL
`DATABASE_URL`. Then apply the migrations:

```powershell
alembic upgrade head
```

Start the development server:

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

Interactive API documentation:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## API Endpoints

### Health

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health/live` | Confirms that the API process is running |
| `GET` | `/health/ready` | Checks API availability and database connectivity |

Example:

```powershell
curl.exe http://127.0.0.1:8000/health/live
```

Expected response:

```json
{"status":"ok"}
```

Protected endpoint example:

```powershell
curl.exe -H "X-API-Key: $env:API_KEY" `
  http://127.0.0.1:8000/authors
```

### Authors

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/authors` | Create an author |
| `GET` | `/authors` | List authors |
| `GET` | `/authors/{author_id}` | Get one author |
| `PATCH` | `/authors/{author_id}` | Partially update an author |
| `DELETE` | `/authors/{author_id}` | Delete an author |

List endpoints support pagination:

```text
GET /authors?offset=0&limit=20
```

Create request:

```json
{
  "name": "Jane Austen",
  "bio": "English novelist"
}
```

### Books

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/books` | Create a book |
| `GET` | `/books` | List books |
| `GET` | `/books/{book_id}` | Get one book |
| `PATCH` | `/books/{book_id}` | Partially update editable book fields |
| `POST` | `/books/{book_id}/stock` | Increase or decrease stock |
| `DELETE` | `/books/{book_id}` | Delete a book |

List endpoints support pagination:

```text
GET /books?offset=0&limit=20
```

Create request:

```json
{
  "title": "Pride and Prejudice",
  "isbn": "9780141439518",
  "price": "12.99",
  "stock": 10,
  "author_id": 1
}
```

Stock adjustment request:

```json
{
  "action": "decrease",
  "quantity": 2
}
```

Valid actions are `increase` and `decrease`. Quantity must be greater than
zero. A decrease greater than the available stock returns `409 Conflict`, and
stock is not changed. Stock is intentionally changed through the dedicated
stock endpoint rather than the regular book update endpoint.

## Error Responses

HTTP errors, validation errors, and unexpected server errors use a consistent
response envelope:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Book not found"
  }
}
```

Validation errors include a `details` array:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "price",
        "message": "Input should be greater than 0",
        "type": "greater_than"
      }
    ]
  }
}
```

Common status codes:

- `201 Created` - resource created
- `200 OK` - successful read or update
- `204 No Content` - successful deletion
- `404 Not Found` - resource does not exist
- `409 Conflict` - duplicate data or insufficient stock
- `422 Unprocessable Entity` - request validation failed
- `503 Service Unavailable` - readiness check cannot reach the database
- `500 Internal Server Error` - unexpected server-side failure

Unexpected exception details are logged on the server and are not exposed to
the client.

## Database Migrations

Show the current migration:

```powershell
alembic current
```

Apply all migrations:

```powershell
alembic upgrade head
```

Create a new migration after changing SQLModel table definitions:

```powershell
alembic revision --autogenerate -m "describe the schema change"
```

Check whether model changes require a migration:

```powershell
alembic check
```

Review autogenerated migrations before applying them to a shared database.

## Automated Tests

The test suite uses `TEST_DATABASE_URL` and drops/recreates tables for each
test fixture. Always use a separate disposable PostgreSQL database. Never use
your development or production database. Set `API_KEY` as well so the test
client can authenticate its requests.

Set the URL without printing it:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST/TEST_DATABASE?sslmode=require"
if ($env:TEST_DATABASE_URL) {
    Write-Host "Test database URL configured"
}
```

Run the tests:

```powershell
python -m pytest -v
```

If `TEST_DATABASE_URL` is missing or still a placeholder, the tests
intentionally skip instead of touching an unsafe database.

Run the Python compilation check:

```powershell
python -m compileall app
```

Verify that the application imports:

```powershell
python -c "from app.main import app; print('Application import successful')"
```

## Docker

Build the image:

```powershell
docker build -t bookstore-api:1.0 .
```

Run the container using values from `.env`:

```powershell
docker run --rm --name bookstore-api `
  -p 8000:8000 `
  --env-file .env `
  -e ENVIRONMENT=production `
  -e LOG_LEVEL=INFO `
  bookstore-api:1.0
```

Alternatively, forward database variables from the current PowerShell
environment:

```powershell
docker run --rm --name bookstore-api `
  -p 8000:8000 `
  -e DATABASE_URL `
  -e MIGRATION_DATABASE_URL `
  -e ENVIRONMENT=production `
  -e LOG_LEVEL=INFO `
  bookstore-api:1.0
```

Check the running container from another terminal:

```powershell
curl.exe http://127.0.0.1:8000/health/live
curl.exe http://127.0.0.1:8000/health/ready
```

The image runs as the non-root `appuser`. Database migrations are intentionally
run separately with Alembic; starting the API container does not automatically
change the database schema.

## Production Notes

- Use a managed PostgreSQL database and a separate direct connection for
  migrations when required by the provider.
- Keep secrets in the deployment platform's secret manager.
- Run `alembic upgrade head` as a controlled deployment step.
- Configure health checks against `/health/live` and `/health/ready`.
- Review connection pool settings for the deployment size.
- Add authentication and authorization before exposing business endpoints
  publicly.
- Add rate limiting, monitoring, backups, and a deployment rollback strategy
  before production launch.

## License

No license has been selected for this project yet.
