"""add owner_id and account_number to accounts

Revision ID: 76e20500de2e
Revises: 426f100f79f6
Create Date: 2026-08-11 11:29:06.718121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76e20500de2e'
down_revision: Union[str, Sequence[str], None] = '426f100f79f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Two hand edits were made to Alembic's generated output:
#
# 1. Autogenerate wrote a column defaulting to nextval('account_number_seq')
#    but never created that sequence, so the migration failed on the first
#    run. Alembic does not pick up sequences that are not the plain SERIAL
#    kind, so the CREATE and DROP are written out by hand below.
#
# 2. Autogenerate left the constraint names as None. That works when adding
#    one, because PostgreSQL invents a name, but the downgrade then has no
#    name to drop. Both constraints are named explicitly instead.

# The sequence behind account_number. start=1000 matches the Module 1
# counter, which also began at 1000.
account_number_seq = sa.Sequence("account_number_seq", start=1000)


def upgrade() -> None:
    """Upgrade schema."""
    # The sequence has to exist before a column can default to reading it.
    op.execute(sa.schema.CreateSequence(account_number_seq))

    op.add_column('accounts', sa.Column('account_number', sa.Integer(), server_default=account_number_seq.next_value(), nullable=False))
    op.add_column('accounts', sa.Column('owner_id', sa.Integer(), nullable=False))
    op.create_unique_constraint('uq_accounts_account_number', 'accounts', ['account_number'])
    op.drop_constraint(op.f('accounts_customer_id_fkey'), 'accounts', type_='foreignkey')
    op.create_foreign_key('accounts_owner_id_fkey', 'accounts', 'customers', ['owner_id'], ['id'])
    op.drop_column('accounts', 'customer_id')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('accounts', sa.Column('customer_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint('accounts_owner_id_fkey', 'accounts', type_='foreignkey')
    op.create_foreign_key(op.f('accounts_customer_id_fkey'), 'accounts', 'customers', ['customer_id'], ['id'])
    op.drop_constraint('uq_accounts_account_number', 'accounts', type_='unique')
    op.drop_column('accounts', 'owner_id')
    op.drop_column('accounts', 'account_number')

    # Drop the sequence last, once nothing depends on it any more.
    op.execute(sa.schema.DropSequence(account_number_seq))
