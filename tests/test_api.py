"""Integration tests for the Bookstore API using a disposable test database."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.models import Author, Book  # noqa: F401


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide an isolated API client backed by TEST_DATABASE_URL."""
    database_url = os.environ.get("TEST_DATABASE_URL")
    api_key = os.environ.get("API_KEY")
    if not database_url or "YOUR-" in database_url or "******" in database_url:
        pytest.skip(
            "Set TEST_DATABASE_URL to a dedicated disposable test database."
        )
    if not api_key:
        pytest.skip("Set API_KEY to authenticate API integration tests.")

    test_engine: Engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    # This fixture drops and recreates tables; never point it at a real
    # development or production database.
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)

    def override_get_session() -> Generator[Session, None, None]:
        """Yield sessions connected to the isolated test database."""
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    test_client = TestClient(app)
    test_client.headers.update({"X-API-Key": api_key})

    try:
        # A plain TestClient avoids running the application's production
        # startup lifespan and its normal database health check.
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
        SQLModel.metadata.drop_all(test_engine)
        test_engine.dispose()


def create_author(client: TestClient) -> int:
    """Create a test author and return its generated ID."""
    response = client.post(
        "/authors",
        json={
            "name": "Test Author",
            "bio": "An author created for automated tests",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_book(client: TestClient, author_id: int) -> int:
    """Create a test book and return its generated ID."""
    response = client.post(
        "/books",
        json={
            "title": "Test Book",
            "isbn": "9781234567890",
            "price": "1500.00",
            "stock": 5,
            "author_id": author_id,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_health_live(client: TestClient) -> None:
    """The liveness endpoint confirms the API process is running."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_authors(client: TestClient) -> None:
    """Created authors appear in the paginated author list."""
    author_id = create_author(client)
    response = client.get("/authors")
    assert response.status_code == 200
    assert any(author["id"] == author_id for author in response.json())


def test_duplicate_author_returns_conflict(client: TestClient) -> None:
    """Creating the same author name twice returns a conflict."""
    create_author(client)
    response = client.post("/authors", json={"name": "Test Author"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_create_book(client: TestClient) -> None:
    """A created book can be retrieved with its author's public name."""
    author_id = create_author(client)
    book_id = create_book(client, author_id)
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Book"
    assert response.json()["author_name"] == "Test Author"


def test_duplicate_isbn_returns_conflict(client: TestClient) -> None:
    """A duplicate ISBN is rejected with a conflict response."""
    author_id = create_author(client)
    create_book(client, author_id)
    response = client.post(
        "/books",
        json={
            "title": "Another Book",
            "isbn": "9781234567890",
            "price": "100.00",
            "stock": 2,
            "author_id": author_id,
        },
    )
    assert response.status_code == 409


def test_negative_price_is_rejected(client: TestClient) -> None:
    """Pydantic validation rejects a negative book price."""
    author_id = create_author(client)
    response = client.post(
        "/books",
        json={
            "title": "Invalid Book",
            "isbn": "9781234567891",
            "price": "-10.00",
            "stock": 1,
            "author_id": author_id,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_book_returns_not_found(client: TestClient) -> None:
    """Unknown book IDs return the standard not-found envelope."""
    response = client.get("/books/999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_stock_adjustment(client: TestClient) -> None:
    """A valid stock increase updates the public stock value."""
    author_id = create_author(client)
    book_id = create_book(client, author_id)
    response = client.post(
        f"/books/{book_id}/stock",
        json={"action": "increase", "quantity": 3},
    )
    assert response.status_code == 200
    assert response.json()["stock"] == 8


def test_insufficient_stock_returns_conflict(client: TestClient) -> None:
    """A decrease larger than available stock leaves stock unchanged."""
    author_id = create_author(client)
    book_id = create_book(client, author_id)
    response = client.post(
        f"/books/{book_id}/stock",
        json={"action": "decrease", "quantity": 6},
    )
    assert response.status_code == 409
    book_response = client.get(f"/books/{book_id}")
    assert book_response.json()["stock"] == 5
