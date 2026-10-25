from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from fastapi import HTTPException, status
from app.models.author import Author, AuthorCreate, AuthorUpdate


def create_author(session: Session, author_data: AuthorCreate) -> Author:
    """Create a new author in the database."""
    # Normalize the validated name before checking for duplicates.
    name = author_data.name.strip()

    existing_author = session.exec(
        select(Author).where(func.lower(Author.name) == name.lower())
    ).first()

    if existing_author:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An author with this name already exists",
        )

    # The database supplies timestamps, so construct the table model from
    # fields already validated by the request schema.
    author = Author(
        name=author_data.name,
        bio=author_data.bio,
    )

    try:
        # Commit persists the row and refresh loads generated database fields.
        session.add(author)
        session.commit()
        session.refresh(author)
        return author
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create author because of a database conflict",
        ) from exc
    except Exception:
        session.rollback()
        raise


def list_authors(
    session: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Author]:
    """List all authors in the database."""
    # Offset and limit keep list responses bounded for API clients.
    statement = select(Author).offset(offset).limit(limit)
    return list(session.exec(statement).all())


def get_author(session: Session, author_id: int) -> Author:
    """Return one author or raise 404."""
    author = session.get(Author, author_id)

    if author is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    return author


def update_author(
    session: Session,
    author_id: int,
    author_data: AuthorUpdate,
) -> Author:
    """Update only fields provided by the client."""
    author = get_author(session, author_id)

    # PATCH behavior: update only fields included in the request body.
    update_data = author_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        new_name = update_data["name"]

        if new_name is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Author name cannot be null",
            )

        duplicate = session.exec(
            select(Author).where(
                func.lower(Author.name) == new_name.lower(),
                Author.id != author_id,
            )
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An author with this name already exists",
            )

    # Apply validated values before committing the transaction.
    for field, value in update_data.items():
        setattr(author, field, value)

    try:
        session.add(author)
        session.commit()
        session.refresh(author)
        return author
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not update author because of a database conflict",
        ) from exc
    except Exception:
        session.rollback()
        raise


def delete_author(session: Session, author_id: int) -> None:
    """Delete an author only when no books reference that author."""
    author = get_author(session, author_id)

    # Foreign-key relationships prevent safe deletion while books exist.
    if author.books:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete an author who has books",
        )

    try:
        session.delete(author)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete this author because related records exist",
        ) from exc
    except Exception:
        session.rollback()
        raise
"""Legacy author service implementation kept for compatibility."""
