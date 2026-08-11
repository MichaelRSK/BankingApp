"""updated primary key for branch table

Revision ID: 05f2e5c4aef3
Revises: 76e20500de2e
Create Date: 2026-08-11 14:16:35.167423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05f2e5c4aef3'
down_revision: Union[str, Sequence[str], None] = '76e20500de2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Autogenerate only produced the three create_foreign_key calls at the end of
# upgrade(). That failed with:
#
#   foreign key constraint "accounts_branch_id_fkey1" cannot be implemented
#   DETAIL: Key columns "branch_id" and "branch_code" are of incompatible
#           types: integer and character varying.
#
# because it does not detect primary key changes or column type changes. Every
# step before the create_foreign_key calls was written by hand.
#
# This migration replaces the surrogate branches.id primary key with
# branch_code, and changes branch_code from varchar(20) to integer.
#
# NOTE: the varchar -> integer cast only succeeds if every existing
# branch_code is made up of digits. A code like 'BR-001' will fail. The
# branches table was empty when this was written, so there was nothing to
# convert.


def upgrade() -> None:
    """Upgrade schema."""
    # The old foreign keys point at branches.id, which is about to disappear.
    # They have to go first or the column cannot be dropped.
    op.drop_constraint('accounts_branch_id_fkey', 'accounts', type_='foreignkey')
    op.drop_constraint('customers_branch_id_fkey', 'customers', type_='foreignkey')
    op.drop_constraint('staff_branch_id_fkey', 'staff', type_='foreignkey')

    # Drop the old primary key, then the column it was built on.
    op.drop_constraint('branches_pkey', 'branches', type_='primary')
    op.drop_column('branches', 'id')

    # Convert branch_code to integer. postgresql_using supplies the USING
    # clause PostgreSQL needs to cast the existing values across.
    op.alter_column(
        'branches',
        'branch_code',
        existing_type=sa.String(length=20),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using='branch_code::integer',
    )

    # branch_code becomes the primary key.
    op.create_primary_key('branches_pkey', 'branches', ['branch_code'])

    # Now that both sides are integers, the new foreign keys can be built.
    # They are named explicitly so downgrade() has something to drop.
    op.create_foreign_key('accounts_branch_id_fkey', 'accounts', 'branches', ['branch_id'], ['branch_code'])
    op.create_foreign_key('customers_branch_id_fkey', 'customers', 'branches', ['branch_id'], ['branch_code'])
    op.create_foreign_key('staff_branch_id_fkey', 'staff', 'branches', ['branch_id'], ['branch_code'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('accounts_branch_id_fkey', 'accounts', type_='foreignkey')
    op.drop_constraint('customers_branch_id_fkey', 'customers', type_='foreignkey')
    op.drop_constraint('staff_branch_id_fkey', 'staff', type_='foreignkey')

    op.drop_constraint('branches_pkey', 'branches', type_='primary')

    op.alter_column(
        'branches',
        'branch_code',
        existing_type=sa.Integer(),
        type_=sa.String(length=20),
        existing_nullable=False,
        postgresql_using='branch_code::varchar',
    )

    # Put the surrogate id back, as a SERIAL so it generates its own values
    # again, and restore it as the primary key.
    op.add_column('branches', sa.Column('id', sa.Integer(), nullable=False, autoincrement=True))
    op.execute('CREATE SEQUENCE IF NOT EXISTS branches_id_seq OWNED BY branches.id')
    op.execute("ALTER TABLE branches ALTER COLUMN id SET DEFAULT nextval('branches_id_seq')")
    op.create_primary_key('branches_pkey', 'branches', ['id'])

    op.create_foreign_key('accounts_branch_id_fkey', 'accounts', 'branches', ['branch_id'], ['id'])
    op.create_foreign_key('customers_branch_id_fkey', 'customers', 'branches', ['branch_id'], ['id'])
    op.create_foreign_key('staff_branch_id_fkey', 'staff', 'branches', ['branch_id'], ['id'])
