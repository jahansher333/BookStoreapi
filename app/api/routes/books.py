"""HTTP routes for book CRUD operations."""

from fastapi import APIRouter, Depends, Query, Response, status

from app.core.security import require_api_key
from app.db.session import SessionDep
from app.models import BookCreate, BookPublic, BookUpdate, StockAdjustment
from app.services import books as book_service


# All book endpoints share the /books prefix and OpenAPI tag.
router = APIRouter(
    prefix="/books",
    tags=["books"],
    dependencies=[Depends(require_api_key)],
)


@router.post(
    "",
    response_model=BookPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_book(
    book_data: BookCreate,
    session: SessionDep,
) -> BookPublic:
    """Validate and create a book."""
    return book_service.create_book(session, book_data)


@router.get("", response_model=list[BookPublic])
def list_books(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[BookPublic]:
    """Return a paginated list of books."""
    return book_service.list_books(session, offset=offset, limit=limit)


@router.get("/{book_id}", response_model=BookPublic)
def get_book(
    book_id: int,
    session: SessionDep,
) -> BookPublic:
    """Return one book by ID."""
    return book_service.get_book(session, book_id)


@router.patch("/{book_id}", response_model=BookPublic)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    session: SessionDep,
) -> BookPublic:
    """Update editable book fields without changing stock."""
    return book_service.update_book(session, book_id, book_data)


@router.post("/{book_id}/stock", response_model=BookPublic)
def adjust_book_stock(
    book_id: int,
    adjustment: StockAdjustment,
    session: SessionDep,
) -> BookPublic:
    """Apply a validated increase or decrease to a book's stock."""
    return book_service.adjust_book_stock(session, book_id, adjustment)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    session: SessionDep,
) -> Response:
    """Delete a book and return an empty successful response."""
    book_service.delete_book(session, book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
