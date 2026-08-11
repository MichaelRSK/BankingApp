# datetime is used to stamp each transaction with the moment it happened.
from datetime import datetime


# Transaction represents a single movement of money in the bank.
# This is a plain data-holding class, similar in style to Customer.
class Transaction:

    # A class attribute (shared by ALL Transaction objects, not one per
    # object). We use it as a counter so every new transaction gets a
    # unique ID automatically: 1, 2, 3, and so on.
    _id_counter = 0

    # Constructor method that runs when a Transaction object is created.
    # transaction_type is a label such as "TRANSFER", "DEPOSIT", "WITHDRAWAL".
    # amount is how much money moved.
    # from_account_id and to_account_id are optional, a deposit has no
    # source and a withdrawal has no destination.
    # timestamp defaults to right now, but can be passed in for testing.
    def __init__(
        self,
        transaction_type: str,
        amount: float,
        from_account_id: int = None,
        to_account_id: int = None,
        timestamp: datetime = None,
    ):
        # Increase the shared counter, then use it as this transaction's ID.
        Transaction._id_counter += 1

        # ENCAPSULATION: the leading underscore marks this as protected.
        # It's accessed through the transaction_id property below, since an
        # ID should never change once it has been assigned.
        self._transaction_id = Transaction._id_counter

        self.transaction_type = transaction_type
        self.amount = amount
        self.from_account_id = from_account_id
        self.to_account_id = to_account_id

        # Record when this happened. Using datetime.now() by default means
        # the caller does not have to remember to set it.
        self.timestamp = timestamp if timestamp is not None else datetime.now()

    # A read-only way to access the transaction's ID from outside the class.
    @property
    def transaction_id(self):
        return self._transaction_id

    # Returns just the calendar date of this transaction, without the time.
    # Filtering by date is easier when the time of day is ignored.
    def get_date(self):
        return self.timestamp.date()