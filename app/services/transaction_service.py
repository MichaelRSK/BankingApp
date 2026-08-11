# datetime is used to turn the start_date string into something we can
# actually compare against a transaction's timestamp.
from datetime import datetime

# Import the Transaction class from its location in app/models.
from app.models.transaction import Transaction

# In-memory list acting as our transactions "database" for now.
# Each entry is a Transaction object, which already assigns its own id.
transactions_db = []


# Records a completed transfer so it shows up in the transaction history.
# The transfer endpoint calls this after the money has actually moved.
def record_transfer(from_account_id: int, to_account_id: int, amount: float):
    new_transaction = Transaction(
        transaction_type="TRANSFER",
        amount=amount,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
    )

    transactions_db.append(new_transaction)

    return new_transaction


# Returns every transaction that happened on or after start_date AND matches
# the given type. Both conditions have to be true for a transaction to be
# included.
# start_date is a string in YYYY-MM-DD form, for example "2026-01-01".
# type is a label such as "TRANSFER", matched without caring about casing.
# Returns None if start_date is not a real date, so the controller can
# answer with its own 400 instead of letting the error escape.
def filter_transactions(start_date: str, type: str):
    # Turn the incoming string into a date we can compare with. If the
    # string is malformed, strptime raises and we report that back.
    try:
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return None

    matching_transactions = []

    for transaction in transactions_db:
        # Skip anything that happened before the requested start date.
        if transaction.get_date() < parsed_start_date:
            continue

        # Skip anything of a different type. Comparing in upper case means
        # "transfer" and "TRANSFER" both work.
        if transaction.transaction_type.upper() != type.upper():
            continue

        matching_transactions.append(transaction)

    return matching_transactions