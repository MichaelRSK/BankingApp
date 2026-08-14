"""widen users email and username columns

Widens users.email and users.username so real values fit.

Both columns were created at VARCHAR(20) by 426f100f79f6, and neither length
was ever revisited. 20 characters is far too small for an email address:
"michaelrsk2004@gmail.com" is 24, and PostgreSQL rejects an over-length value
outright rather than truncating it, so registration failed with

    ERROR: value too long for type character varying(20)

for any address over 20 characters. The longest address stored before this
migration was exactly 20, sitting right on the boundary.

The same 20-character ceiling applied to usernames, which is tight enough to
turn away ordinary names, so it is widened here too.

email goes to 255, matching customers.email, which registration already
writes the same address into. Having the two disagree is what let a value be
accepted in one table and refused in the other halfway through signup.
username goes to 120, matching customers.name.

This is the mirror of what 528f100fabcd did for users.password, which was
created at the same 20 characters and could not hold a 60-character bcrypt
hash.

Widening a varchar does not rewrite the table in PostgreSQL, so this is a
quick metadata change even on a populated database. The primary key index on
username and the unique index on email are rebuilt, which is not free but is
trivial at this size.

Revision ID: ae9e35893c3e
Revises: 95dd0676a507
Create Date: 2026-08-14 09:35:46.308069

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae9e35893c3e'
down_revision: Union[str, Sequence[str], None] = '95dd0676a507'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Widen email to 255, the same length customers.email already uses.
    #
    # existing_nullable is passed on both columns so the alter only changes
    # the type. Left out, alembic has no record of the current setting and
    # can emit a DROP NOT NULL alongside the type change, which would quietly
    # let a NULL email or username through afterwards.
    op.alter_column(
        'users',
        'email',
        existing_type=sa.String(length=20),
        type_=sa.String(length=255),
        existing_nullable=False,
    )

    # Widen username to 120, matching customers.name.
    #
    # This column is the table's primary key. Widening it is still safe:
    # nothing references it with a foreign key, so there is no dependent
    # column that would have to change with it.
    op.alter_column(
        'users',
        'username',
        existing_type=sa.String(length=20),
        type_=sa.String(length=120),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Narrows both columns back to the original 20 characters.
    #
    # Unlike the upgrade, this one can fail, and that is deliberate. Shrinking
    # a varchar means PostgreSQL has to check every existing value fits, and
    # it aborts the migration if any row is too long rather than truncating
    # it. Anyone who registered with a normal email address after the upgrade
    # would trip this.
    #
    # Deleting or truncating those rows to force the downgrade through is not
    # something a migration should decide on its own, since it would silently
    # destroy a login. If this needs to run, shorten the offending values
    # first and then downgrade.
    op.alter_column(
        'users',
        'username',
        existing_type=sa.String(length=120),
        type_=sa.String(length=20),
        existing_nullable=False,
    )

    op.alter_column(
        'users',
        'email',
        existing_type=sa.String(length=255),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
