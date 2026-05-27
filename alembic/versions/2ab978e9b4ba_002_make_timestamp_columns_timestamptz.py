"""002_make_timestamp_columns_timestamptz

Revision ID: 2ab978e9b4ba
Revises: 001
Create Date: 2026-05-28 00:40:25.206089
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ab978e9b4ba'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "feed_items",
        "published_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
    )
    op.alter_column(
        "feed_items",
        "fetched_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
    )
    op.alter_column(
        "feeds",
        "created_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
    )
    op.alter_column(
        "feeds",
        "updated_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
    )


def downgrade() -> None:
    op.alter_column(
        "feed_items",
        "fetched_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "feed_items",
        "published_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "feeds",
        "updated_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "feeds",
        "created_at",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
    )
