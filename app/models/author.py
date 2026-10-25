from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from pydantic import field_validator
from sqlalchemy import Column, func
from sqlmodel import  DateTime, Field , Relationship, SQLModel




if TYPE_CHECKING:
    from app.models.book import Book



class AuthorBase(SQLModel):
    """Shared validated fields for author create and table models."""
    # These constraints run before service/database work begins.
    name: str = Field(
        min_length=1,
        max_length=150,
        index=True,
        nullable=False,
    )
    bio: str | None = Field(default=None, max_length=2000, nullable=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        # Normalize user input so duplicate checks are more consistent.
        value = value.strip()

        if not value:
            raise ValueError("Author name cannot be empty or whitespace")

        return value

class Author(AuthorBase, table=True):
    """Database table representing an author."""
    __tablename__ = "authors"
    # SQLModel maps these fields to columns in the authors table.
    id : int| None = Field(default=None, primary_key=True)
    created_at : datetime = Field(
         sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )
    updated_at : datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )
    # One author can be related to many books.
    books : List["Book"] = Relationship(back_populates="author")

class AuthorCreate(AuthorBase):
    """Request schema for creating an author."""

    pass

class AuthorRead(AuthorBase):
    """Internal/read schema containing author persistence fields."""

    id : int
    created_at : datetime
    updated_at : datetime



class AuthorUpdate(SQLModel):
    """Partial request schema for updating an author."""
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
        nullable=True,
    )
    bio: str | None = Field(default=None, max_length=2000, nullable=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value

        # PATCH requests may omit name, but supplied values still normalize.
        value = value.strip()

        if not value:
            raise ValueError("Author name cannot be empty or whitespace")

        return value

class AuthorPublic(SQLModel):
    """Response schema exposing an author to API clients."""
    id: int
    name: str
    bio: str | None
    created_at: datetime
"""Author database model and API validation schemas."""
