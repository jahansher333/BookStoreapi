"""Create authors and books tables.

Revision ID: 0001
Revises:
Create Date: 2026-10-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create authors and books tables."""
    # Create the referenced table before books because books has a foreign key.
    op.create_table(
        "authors",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("bio", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_authors_name"), "authors", ["name"], unique=False)

    # Add book constraints and the relationship to its author.
    op.create_table(
        "books",
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=250), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("isbn", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("price > 0", name="ck_books_price_positive"),
        sa.CheckConstraint("stock >= 0", name="ck_books_stock_nonnegative"),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isbn"),
    )
    op.create_index(op.f("ix_books_author_id"), "books", ["author_id"], unique=False)


def downgrade() -> None:
    """Drop books and authors tables."""
    # Drop dependent objects first so the foreign-key relationship is valid.
    op.drop_index(op.f("ix_books_author_id"), table_name="books")
    op.drop_table("books")
    op.drop_index(op.f("ix_authors_name"), table_name="authors")
    op.drop_table("authors")
