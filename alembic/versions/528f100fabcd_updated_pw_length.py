"""updated pw length

Widens users.password so a bcrypt hash fits. A hash is 60 characters and the
column started at 20, which truncated every hash on the way in.

On a database built from 426f100f79f6 this is already the case and the alter
does nothing, but a database created before that fix still needs it.

Revision ID: 528f100fabcd
Revises: 426f100f79f6
Create Date: 2026-08-12 10:14:02.113509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '528f100fabcd'
# Chains onto the initial schema. This was None, which made alembic treat the
# file as a second starting point, and "upgrade head" then failed because two
# separate heads existed with no way to tell which one was meant.
down_revision: Union[str, Sequence[str], None] = '426f100f79f6'
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