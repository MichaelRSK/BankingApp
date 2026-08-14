"""add transfer limits

Creates the transfer_limits table behind the user-defined spending caps.

user_id points at customers.id rather than users.username, because that is
what CurrentUser.user_id holds and what every other ownership check in the
app compares against.

Autogenerate also offered two unnamed unique constraints on
accounts.account_number and branches.branch_code. Both are already primary
keys, so the constraints add nothing, and passing None as a constraint name
to op.create_unique_constraint fails outright. They come from unique=True
sitting alongside primary_key=True in those two models, the same drift the
comment on User.username describes, and they are unrelated to this change,
so they have been removed from the file rather than applied here.

Revision ID: 95dd0676a507
Revises: 528f100fabcd
Create Date: 2026-08-12 21:03:20.219833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95dd0676a507'
down_revision: Union[str, Sequence[str], None] = '528f100fabcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('transfer_limits',
    sa.Column('id', sa.Integer(), nullable=False),
    # Named user_id to match the model. It holds a customers.id, and the
    # foreign key below is what makes sure that customer actually exists.
    sa.Column('user_id', sa.Integer(), nullable=False),
    # String rather than a PostgreSQL enum type, matching how
    # transactions.transaction_type and accounts.type already store their
    # upper-cased constants. Adding a fourth limit kind later then needs no
    # migration at all.
    sa.Column('limit_type', sa.String(length=20), nullable=False),
    # Numeric, not float, for the same reason as accounts.balance. Comparing
    # money against a ceiling is exactly where a float's rounding error would
    # decide a transfer wrongly.
    sa.Column('max_amount', sa.Numeric(precision=12, scale=2), nullable=False),
    # nullable=False so the limit check never has to add to a NULL.
    sa.Column('current_period_used', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('period_start', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # Every transfer looks these rows up by user_id before the money moves,
    # so this one is on the hot path. PostgreSQL does not index a foreign key
    # column on its own. The model declares index=True to match, otherwise
    # the next autogenerate would see an index the models do not know about
    # and offer to drop it.
    op.create_index(
        op.f('ix_transfer_limits_user_id'), 'transfer_limits', ['user_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_transfer_limits_user_id'), table_name='transfer_limits')
    op.drop_table('transfer_limits')