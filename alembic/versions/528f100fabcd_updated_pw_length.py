"""initial schema

Revision ID: 426f100f79f6
Revises: 
Create Date: 2026-08-11 11:20:33.756874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '528f100fabcd'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Change length from old size to 255
    op.alter_column(
        'users',
        'password',
        existing_type=sa.String(length=20),  # The current size in DB
        type_=sa.String(length=255)           # The new desired size
    )

def downgrade() -> None:
    # Revert back to the original length if needed
    op.alter_column(
        'users',
        'password',
        existing_type=sa.String(length=255),
        type_=sa.String(length=20)
    )