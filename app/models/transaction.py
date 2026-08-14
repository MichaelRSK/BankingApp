# datetime is used to stamp each transaction with the moment it happened.
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey

from app.db.base import Base


# Transaction represents a single movement of money in the bank.
class Transaction(Base):
    __tablename__ = "transactions"

    # ENCAPSULATION: same pattern as Customer. The column is "id", the Python
    # attribute is _transaction_id, and outside code reads it through the
    # transaction_id property so it can never be reassigned.
    #
    # Module 1's _id_counter class attribute is gone. It restarted at 1 every
    # time the server did, which would have collided with transactions
    # already saved. PostgreSQL hands out the ids now.
    _transaction_id = Column("id", Integer, primary_key=True)

    # A label such as "TRANSFER", "DEPOSIT", "WITHDRAWAL".
    transaction_type = Column(String(20), nullable=False)

    # Exact, not a float, for the same reason as Account._balance.
    amount = Column(Numeric(12, 2), nullable=False)

    # Both are optional: a deposit has no source and a withdrawal has no
    # destination. The foreign keys mean a transaction can only ever name
    # accounts that actually exist.
    from_account_id = Column(Integer, ForeignKey("accounts.account_number"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.account_number"), nullable=True)

    # Record when this happened. default=datetime.now means the caller does
    # not have to remember to set it, matching the Module 1 behaviour.
    timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # Keeps the Module 1 constructor working, including the positional order
    # Transaction("TRANSFER", 50.0, from_account_id=1, to_account_id=2).
    def __init__(
        self,
        transaction_type: str,
        amount: float,
        from_account_id: int = None,
        to_account_id: int = None,
        timestamp: datetime = None,
        **kwargs,
    ):
        super().__init__(
            transaction_type=transaction_type,
            # Same float-to-Decimal conversion as Account, for the same reason.
            amount=Decimal(str(amount)),
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            # Stamp the time here instead of leaving it to the column default,
            # so the object knows when it happened before it is ever saved.
            timestamp=timestamp if timestamp is not None else datetime.now(),
            **kwargs,
        )

    # A read-only way to access the transaction's ID from outside the class.
    @property
    def transaction_id(self):
        return self._transaction_id

    # Returns just the calendar date of this transaction, without the time.
    # Filtering by date is easier when the time of day is ignored.
    def get_date(self):
        return self.timestamp.date()