from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import field_validator
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    func,
)
from sqlmodel import Field, Relationship, SQLModel

from app.models.author import Author


class BookBase(SQLModel):
    """Shared validated fields for book create and table models."""
    # Request validation prevents invalid values reaching the database.
    title: str = Field(min_length=1, max_length=250)
    isbn: str = Field(min_length=10, max_length=20)
    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )
    stock: int = Field(ge=0)
    author_id: int = Field(gt=0)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        # Remove accidental spaces before storing or comparing titles.
        value = value.strip()

        if not value:
            raise ValueError("Book title cannot be empty or whitespace")

        return value

    @field_validator("isbn")
    @classmethod
    def normalize_isbn(cls, value: str) -> str:
        # Keep ISBN values consistent when clients include outer spaces.
        value = value.strip()

        if not value:
            raise ValueError("ISBN cannot be empty")

        return value


class Book(BookBase, table=True):
    """Database table representing a book."""
    __tablename__ = "books"

    # Database-level checks protect data even if code validation is bypassed.
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_books_price_positive"),
        CheckConstraint("stock >= 0", name="ck_books_stock_nonnegative"),
    )

    id: int | None = Field(default=None, primary_key=True)

    isbn: str = Field(
        min_length=10,
        max_length=20,
        unique=True,
    )

    price: Decimal = Field(
        sa_column=Column(
            Numeric(10, 2),
            nullable=False,
        )
    )

    author_id: int = Field(
        foreign_key="authors.id",
        index=True,
    )

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    )

    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )

    # Each book belongs to one author through author_id.
    author: Author = Relationship(back_populates="books")


class BookCreate(BookBase):
    """Request schema for creating a book."""

    pass


class BookUpdate(SQLModel):
    """Partial request schema for updating a book."""
    # Optional fields allow PATCH requests to update only supplied values.
    title: str | None = Field(default=None, min_length=1, max_length=250)
    isbn: str | None = Field(default=None, min_length=10, max_length=20)
    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )
    author_id: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Book title cannot be empty or whitespace")

        return value

    @field_validator("isbn")
    @classmethod
    def normalize_isbn(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("ISBN cannot be empty")

        return value


class StockAdjustment(SQLModel):
    """Validated request body for a dedicated stock adjustment."""

    # Literal keeps the inventory operation limited to two business actions.
    action: Literal["increase", "decrease"]
    # Zero and negative quantities do not represent a valid stock movement.
    quantity: int = Field(gt=0)


class BookPublic(SQLModel):
    """Response schema exposing a book and its author to clients."""
    id: int
    title: str
    isbn: str
    price: Decimal
    stock: int
    author_id: int
    author_name: str
    created_at: datetime
    updated_at: datetime
"""Book database model and API validation schemas."""
