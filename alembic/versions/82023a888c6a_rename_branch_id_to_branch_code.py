"""rename branch_id to branch_code

Revision ID: 82023a888c6a
Revises: 05f2e5c4aef3
Create Date: 2026-08-11 14:32:47.087289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82023a888c6a'
down_revision: Union[str, Sequence[str], None] = '05f2e5c4aef3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Autogenerate wrote this as add_column + drop_column for each table, because
# Alembic cannot tell a rename apart from "one column vanished and a different
# one appeared". Running that version would have set every existing
# branch_code to NULL, silently unlinking every account, customer and staff
# member from its branch.
#
# alter_column with new_column_name issues a real ALTER TABLE ... RENAME
# COLUMN instead, which keeps the values and the foreign key intact.
#
# The foreign keys are renamed too. A rename leaves the old constraint name
# behind, so without this the accounts table would still carry a constraint
# called accounts_branch_id_fkey on a column named branch_code.

TABLES = ["accounts", "customers", "staff"]


def upgrade() -> None:
    """Upgrade schema."""
    for table in TABLES:
        op.alter_column(table, "branch_id", new_column_name="branch_code")
        op.execute(
            f"ALTER TABLE {table} "
            f"RENAME CONSTRAINT {table}_branch_id_fkey TO {table}_branch_code_fkey"
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in TABLES:
        op.alter_column(table, "branch_code", new_column_name="branch_id")
        op.execute(
            f"ALTER TABLE {table} "
            f"RENAME CONSTRAINT {table}_branch_code_fkey TO {table}_branch_id_fkey"
        )
