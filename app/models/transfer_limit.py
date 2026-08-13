# enum gives the three limit kinds a single definition, so the service and
# the controller compare against LimitType.DAILY rather than a bare string
# that a typo could silently break.
import enum

# datetime stamps the moment the current period began, the same way
# Transaction stamps when a transaction happened.
from datetime import datetime

# Decimal is Python's exact decimal type. Money is stored as Numeric in
# PostgreSQL, which comes back as a Decimal, so the maths below uses it too.
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey

from app.db.base import Base


# The kinds of limit a customer can set on themselves.
#
# Inheriting from str as well as Enum means LimitType.DAILY == "DAILY" is
# true, so a value read back out of the database compares equal to the enum
# member without converting it first.
#
# The values are stored in a plain String(20) column rather than a PostgreSQL
# enum type, matching Transaction.transaction_type and Account.type, which
# already hold upper-cased constants the same way. A native enum type would
# validate at the database level, but adding a fourth limit kind later would
# then need an ALTER TYPE migration instead of nothing at all.
class LimitType(str, enum.Enum):
    # Caps a single transfer. Nothing accumulates, the amount is simply
    # compared against max_amount every time.
    PER_TRANSACTION = "PER_TRANSACTION"

    # Caps the total moved in one calendar day.
    DAILY = "DAILY"

    # Caps the total moved in one calendar month.
    MONTHLY = "MONTHLY"


# TransferLimit is a cap a customer sets on their own outgoing transfers.
#
# A customer can hold several of these at once, for example a $500
# per-transaction limit alongside a $2000 daily limit. Every one of them has
# to pass before a transfer is allowed through.
class TransferLimit(Base):
    __tablename__ = "transfer_limits"

    # ENCAPSULATION: same pattern as Customer and Transaction. The column is
    # "id", the Python attribute is _limit_id, and outside code reads it
    # through the limit_id property below so it can never be reassigned.
    _limit_id = Column("id", Integer, primary_key=True)

    # The customer this limit belongs to.
    #
    # This points at customers.id, not users.username, even though the limit
    # is set by a logged-in user. The users table is keyed by username, and
    # its sub column is the string that ends up in the token's subject claim,
    # which get_current_user turns back into an int as CurrentUser.user_id.
    # Every ownership check already in the app compares that int against
    # customers.id, so that is the value stored here.
    #
    # nullable=False because a limit with no owner would apply to nobody and
    # could never be listed or updated.
    #
    # index=True because every transfer looks these rows up by user_id before
    # the money moves. PostgreSQL does not index a foreign key column on its
    # own, and this is the one query on the hot path.
    user_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)

    # Which of the three kinds above this row is. Held as text for the reason
    # described on LimitType.
    limit_type = Column(String(20), nullable=False)

    # The ceiling itself. Numeric(12, 2) for the same reason as
    # Account._balance: a float cannot represent a value like 0.10 exactly,
    # and comparing money against a limit is exactly where that would bite.
    max_amount = Column(Numeric(12, 2), nullable=False)

    # How much of the ceiling has been spent in the period that is currently
    # running. Only meaningful for DAILY and MONTHLY, a PER_TRANSACTION limit
    # never accumulates and leaves this at zero.
    #
    # nullable=False plus a default means this can never end up as NULL, which
    # would break the addition in the limit check.
    current_period_used = Column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # When the period that current_period_used refers to began.
    #
    # This is what makes the rollover check possible without a background job:
    # comparing this against now tells us whether a new day or month has
    # started since the usage was last touched.
    #
    # Naive local time, matching Transaction.timestamp, so the two columns can
    # be compared against each other without a timezone conversion.
    period_start = Column(DateTime, nullable=False, default=datetime.now)

    # Keeps the constructor readable at the call site:
    # TransferLimit(user_id, "DAILY", 500).
    #
    # There is deliberately no relationship() back to Customer. Nothing in the
    # app needs to walk from a customer to their limits through the ORM, the
    # service queries by user_id directly, and adding one would mean editing
    # customer.py to declare the other half of it.
    #
    # SQLAlchemy only calls __init__ when we build a NEW object in Python. It
    # restores rows loaded from the database by a different route, so this
    # does not interfere with queries.
    def __init__(
        self,
        user_id: int,
        limit_type: str,
        max_amount: float,
        period_start: datetime = None,
        **kwargs,
    ):
        super().__init__(
            user_id=user_id,
            # LimitType(...) raises ValueError on anything that is not one of
            # the three members, so a bad value can never reach the database.
            # The service checks first and returns None, so in practice this
            # is a last line of defence rather than the error path.
            # .value stores a plain str, not the enum member itself.
            limit_type=LimitType(limit_type).value,
            # Same float-to-Decimal conversion as Account, for the same
            # reason: going through str() avoids inheriting the float's
            # rounding error.
            max_amount=Decimal(str(max_amount)),
            # A brand new limit has spent nothing yet.
            current_period_used=Decimal("0.00"),
            # Stamped here rather than left to the column default, so the
            # object knows when its period started before it is ever saved.
            period_start=period_start if period_start is not None else datetime.now(),
            **kwargs,
        )

    # A read-only way to access the limit's ID from outside the class.
    @property
    def limit_id(self):
        return self._limit_id

    # True when this limit accumulates usage over a period, false for
    # PER_TRANSACTION which is checked against a single amount instead.
    #
    # Lives here rather than in the service because it is a fact about what
    # a limit kind means, and both the check and the record path need it.
    def accumulates(self):
        return self.limit_type in (LimitType.DAILY.value, LimitType.MONTHLY.value)