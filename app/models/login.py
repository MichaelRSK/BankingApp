from sqlalchemy import Column, String

from app.db.base import Base


# User holds the login credentials and the claims that end up inside a token.
#
# The password column stores a bcrypt hash, never the password itself. bcrypt
# keeps the salt inside the hash string, so there is no separate salt column
# sitting next to it.
#
# sub, email and roles are the three claims app/core/security.py copies into
# every token it signs.
class User(Base):
    __tablename__ = "users"

    # id = Column(Integer, primary_key=True)
    # unique=True is left off deliberately. A primary key is already unique,
    # and declaring both makes Alembic see a constraint in the models that is
    # not in the database and offer to add it on every autogenerate.
    # String(120) rather than a bare String, matching customers.name.
    #
    # A bare String has no length at all, which PostgreSQL reads as unlimited
    # text. The real column has always had a length, set by the migration
    # rather than here, so the model quietly described a wider column than
    # existed. Stating the length means the two cannot drift apart again.
    username = Column(
        String(120),
        nullable=False,
        primary_key=True
    )

    # Not unique. Two users choosing the same password is not an error, and
    # the constraint would have leaked that fact by rejecting the second one.
    # In practice bcrypt's random salt makes two hashes differ anyway, so this
    # never fired and simply described the wrong intent.
    password = Column(
        String,
        nullable=False,
        primary_key=False
    )

    sub = Column(
        String,
        unique=True,
        nullable=False,
        primary_key=False
    )

    # String(255) rather than a bare String, for the same reason as username,
    # and matching customers.email, which registration writes the same address
    # into. This column was VARCHAR(20) until ae9e35893c3e, which rejected any
    # address over 20 characters outright and broke registration.
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        primary_key=False
    )

    # Not unique. Every CUSTOMER shares the same role string, so a unique
    # constraint here would let only one user in the whole system hold a
    # given role.
    roles = Column(
        String,
        nullable=False,
        primary_key=False
    )


    def __init__(self, user: str, pwd: str, sb: str, eml: str, rls: str, **kwargs):
        super().__init__(
            username=user,
            password=pwd,
            sub=sb,
            email=eml,
            roles=rls,
            **kwargs,
        )