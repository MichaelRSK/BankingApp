# Decimal is Python's exact decimal type. Money is stored as Numeric in
# PostgreSQL, which comes back as a Decimal, so the maths below uses it too.
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Sequence
from sqlalchemy.orm import relationship

from app.db.base import Base


# Account is the base class every specific account type builds on.
#
# ABSTRACTION: in Module 1 this inherited from ABC and marked account_type()
# with @abstractmethod. That is not possible now, because ABC's metaclass and
# SQLAlchemy's declarative metaclass cannot be combined on one class. The
# intent is kept by raising NotImplementedError instead: a subclass that
# forgets to implement account_type() still fails loudly, just when the
# method is called rather than when the object is created.
#
# INHERITANCE: SavingsAccount and CheckingAccount below share this one table.
# SQLAlchemy calls that single table inheritance. The "type" column records
# which class each row is, and SQLAlchemy uses it to rebuild the right
# subclass when loading a row back out.
class User(Base):
    __tablename__ = "users"

    # id = Column(Integer, primary_key=True)
    username = Column(
        String,
        unique=True,
        nullable=False,
        primary_key=True
    )

    password = Column(
        String,
        unique=True,
        nullable=False,
        primary_key=False
    )

    sub = Column(
        String,
        unique=True,
        nullable=False,
        primary_key=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        primary_key=False
    )

    roles = Column(
        String,
        unique=True,
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