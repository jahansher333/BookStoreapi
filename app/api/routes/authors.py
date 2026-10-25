from fastapi import APIRouter, Depends, Query, Response, status

from app.core.security import require_api_key
from app.db.session import SessionDep
from app.models import AuthorCreate, AuthorPublic, AuthorUpdate
from app.services import authors as author_service


# Keep the resource prefix in one place for consistent API paths and docs.
router = APIRouter(
    prefix="/authors",
    tags=["authors"],
    dependencies=[Depends(require_api_key)],
)

# FastAPI validates the request body as AuthorCreate before calling the service.
@router.post(
    "",
    response_model=AuthorPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_author(
    author_data: AuthorCreate,
    session: SessionDep,
) -> AuthorPublic:
    """Create and return a validated author."""
    return author_service.create_author(session, author_data)


@router.get("", response_model=list[AuthorPublic])
def list_authors(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[AuthorPublic]:
    """Return a paginated list of authors."""
    # Query limits protect the endpoint from unbounded result sets.
    return author_service.list_authors(
        session,
        offset=offset,
        limit=limit,
    )


@router.get("/{author_id}", response_model=AuthorPublic)
def get_author(
    author_id: int,
    session: SessionDep,
) -> AuthorPublic:
    """Return one author by ID."""
    return author_service.get_author(session, author_id)


@router.patch("/{author_id}", response_model=AuthorPublic)
def update_author(
    author_id: int,
    author_data: AuthorUpdate,
    session: SessionDep,
) -> AuthorPublic:
    """Apply a partial update and return the updated author."""
    # AuthorUpdate supports PATCH semantics: only supplied fields are changed.
    return author_service.update_author(
        session,
        author_id,
        author_data,
    )


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(
    author_id: int,
    session: SessionDep,
) -> Response:
    """Delete an author when no books reference it."""
    author_service.delete_author(session, author_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
"""HTTP routes for author CRUD operations."""
